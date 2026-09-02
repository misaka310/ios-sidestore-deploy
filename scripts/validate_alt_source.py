#!/usr/bin/env python3
"""Validate the supported, non-marketplace AltSource contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from typing import Any
from urllib.parse import urlparse


class AltSourceValidationError(ValueError):
    """Raised when an AltSource is unsafe or semantically inconsistent."""


ROOT_KEYS = {
    "name",
    "subtitle",
    "description",
    "iconURL",
    "headerURL",
    "website",
    "tintColor",
    "featuredApps",
    "apps",
    "news",
}
APP_KEYS = {
    "name",
    "bundleIdentifier",
    "developerName",
    "subtitle",
    "localizedDescription",
    "iconURL",
    "tintColor",
    "category",
    "screenshots",
    "versions",
    "appPermissions",
}
VERSION_KEYS = {
    "version",
    "buildVersion",
    "marketingVersion",
    "date",
    "localizedDescription",
    "downloadURL",
    "size",
    "sha256",
    "minOSVersion",
    "maxOSVersion",
    "assetURLs",
}


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AltSourceValidationError(f"{label} must be a non-empty string")
    return value.strip()


def _natural_key(value: str) -> tuple[tuple[int, int | str], ...]:
    parts = re.findall(r"\d+|[A-Za-z]+", value)
    return tuple((0, int(part)) if part.isdigit() else (1, part.lower()) for part in parts)


def version_sort_key(version: str, build: str) -> tuple[tuple[tuple[int, int | str], ...], tuple[tuple[int, int | str], ...]]:
    return _natural_key(version), _natural_key(build)


def _check_https_url(value: Any, label: str) -> None:
    url = _require_string(value, label)
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise AltSourceValidationError(f"{label} must be an absolute HTTPS URL")


def _check_allowed_keys(value: dict[str, Any], allowed: set[str], label: str) -> None:
    unsupported = sorted(set(value) - allowed)
    if unsupported:
        raise AltSourceValidationError(f"{label} contains unsupported keys: {', '.join(unsupported)}")


def _validate_version(version: Any, label: str) -> None:
    if not isinstance(version, dict):
        raise AltSourceValidationError(f"{label} must be an object")
    _check_allowed_keys(version, VERSION_KEYS, label)
    for key in ("version", "buildVersion", "date", "downloadURL"):
        _require_string(version.get(key), f"{label}.{key}")
    _check_https_url(version["downloadURL"], f"{label}.downloadURL")

    try:
        datetime.fromisoformat(version["date"].replace("Z", "+00:00"))
    except (TypeError, ValueError) as error:
        raise AltSourceValidationError(f"{label}.date must be ISO 8601") from error

    size = version.get("size")
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise AltSourceValidationError(f"{label}.size must be a non-negative integer")

    if "sha256" in version:
        sha256 = _require_string(version["sha256"], f"{label}.sha256")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", sha256):
            raise AltSourceValidationError(f"{label}.sha256 must be a 64-character hex digest")

    for key in ("minOSVersion", "maxOSVersion", "marketingVersion", "localizedDescription"):
        if key in version:
            _require_string(version[key], f"{label}.{key}")

    if "assetURLs" in version:
        asset_urls = version["assetURLs"]
        if not isinstance(asset_urls, dict) or any(
            not isinstance(key, str) or not isinstance(value, str) for key, value in asset_urls.items()
        ):
            raise AltSourceValidationError(f"{label}.assetURLs must map strings to strings")


def validate_source(source: Any) -> None:
    """Raise AltSourceValidationError unless source satisfies the supported contract."""

    if not isinstance(source, dict):
        raise AltSourceValidationError("source must be an object")
    _check_allowed_keys(source, ROOT_KEYS, "source")
    _require_string(source.get("name"), "source.name")
    apps = source.get("apps")
    if not isinstance(apps, list):
        raise AltSourceValidationError("source.apps must be an array")

    bundle_ids: set[str] = set()
    previous_bundle_id: str | None = None
    for app_index, app in enumerate(apps):
        label = f"source.apps[{app_index}]"
        if not isinstance(app, dict):
            raise AltSourceValidationError(f"{label} must be an object")
        _check_allowed_keys(app, APP_KEYS, label)
        name = _require_string(app.get("name"), f"{label}.name")
        bundle_id = _require_string(app.get("bundleIdentifier"), f"{label}.bundleIdentifier")
        _require_string(app.get("developerName"), f"{label}.developerName")
        _require_string(app.get("localizedDescription"), f"{label}.localizedDescription")
        if bundle_id in bundle_ids:
            raise AltSourceValidationError(f"duplicate bundleIdentifier: {bundle_id}")
        bundle_ids.add(bundle_id)
        if previous_bundle_id is not None and bundle_id < previous_bundle_id:
            raise AltSourceValidationError("apps must use stable ascending bundleIdentifier order")
        previous_bundle_id = bundle_id

        permissions = app.get("appPermissions")
        if not isinstance(permissions, dict):
            raise AltSourceValidationError(f"{label}.appPermissions must be an object")
        versions = app.get("versions")
        if not isinstance(versions, list) or not versions:
            raise AltSourceValidationError(f"{label}.versions must be a non-empty array")

        seen_pairs: set[tuple[str, str]] = set()
        previous_key = None
        for version_index, version in enumerate(versions):
            version_label = f"{label}.versions[{version_index}]"
            _validate_version(version, version_label)
            pair = (version["version"], version["buildVersion"])
            if pair in seen_pairs:
                raise AltSourceValidationError(
                    f"{version_label} duplicates version/build pair {pair[0]}/{pair[1]}"
                )
            seen_pairs.add(pair)
            current_key = version_sort_key(*pair)
            if previous_key is not None and current_key > previous_key:
                raise AltSourceValidationError(
                    f"{label}.versions must use stable descending order"
                )
            previous_key = current_key

        for key in ("subtitle", "iconURL", "tintColor", "category"):
            if key in app:
                _require_string(app[key], f"{label}.{key}")

    if "news" in source and not isinstance(source["news"], list):
        raise AltSourceValidationError("source.news must be an array")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=str, help="path to source.json")
    args = parser.parse_args(argv)
    try:
        source = json.loads(open(args.source, encoding="utf-8").read())
        validate_source(source)
    except (OSError, json.JSONDecodeError, AltSourceValidationError) as error:
        print(f"AltSource validation failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(source, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
