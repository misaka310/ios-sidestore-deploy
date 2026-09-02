#!/usr/bin/env python3
"""Deterministically add release metadata to a SideStore-compatible AltSource."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from scripts.validate_alt_source import AltSourceValidationError, validate_source, version_sort_key


class AltSourceConflictError(ValueError):
    """Raised when a release would overwrite a different version/build entry."""


RELEASE_KEYS = {
    "name",
    "bundleIdentifier",
    "developerName",
    "localizedDescription",
    "version",
    "buildVersion",
    "date",
    "downloadURL",
    "size",
    "sha256",
    "minOSVersion",
    "maxOSVersion",
    "marketingVersion",
}
REQUIRED_RELEASE_KEYS = RELEASE_KEYS - {"maxOSVersion", "marketingVersion"}


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AltSourceConflictError(f"{label} must be a non-empty string")
    return value.strip()


def _release_version_entry(release: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(REQUIRED_RELEASE_KEYS - set(release))
    if missing:
        raise AltSourceConflictError(f"release metadata is missing: {', '.join(missing)}")
    unknown = sorted(set(release) - RELEASE_KEYS)
    if unknown:
        raise AltSourceConflictError(f"release metadata contains unsupported keys: {', '.join(unknown)}")

    entry = {
        "version": _require_string(release["version"], "version"),
        "buildVersion": _require_string(release["buildVersion"], "buildVersion"),
        "date": _require_string(release["date"], "date"),
        "localizedDescription": _require_string(release["localizedDescription"], "localizedDescription"),
        "downloadURL": _require_string(release["downloadURL"], "downloadURL"),
        "size": release["size"],
        "sha256": _require_string(release["sha256"], "sha256"),
        "minOSVersion": _require_string(release["minOSVersion"], "minOSVersion"),
    }
    for key in ("maxOSVersion", "marketingVersion"):
        if key in release:
            entry[key] = _require_string(release[key], key)
    return entry


def _sort_source(source: dict[str, Any]) -> None:
    source["apps"] = sorted(source.get("apps", []), key=lambda app: app["bundleIdentifier"])
    for app in source["apps"]:
        app["versions"] = sorted(
            app["versions"],
            key=lambda version: version_sort_key(version["version"], version["buildVersion"]),
            reverse=True,
        )


def update_source(source: dict[str, Any], release: dict[str, Any]) -> dict[str, Any]:
    """Return source with one release added, replaced idempotently, and stably ordered."""

    if not isinstance(source, dict):
        raise AltSourceConflictError("source must be an object")
    candidate = copy.deepcopy(source)
    validate_source(candidate) if candidate.get("apps") else None
    if not isinstance(release, dict):
        raise AltSourceConflictError("release metadata must be an object")
    for key in ("name", "bundleIdentifier", "developerName", "localizedDescription"):
        _require_string(release.get(key), key)

    version_entry = _release_version_entry(release)
    apps = candidate.setdefault("apps", [])
    if not isinstance(apps, list):
        raise AltSourceConflictError("source.apps must be an array")

    matching_app = next(
        (app for app in apps if isinstance(app, dict) and app.get("bundleIdentifier") == release["bundleIdentifier"]),
        None,
    )
    if matching_app is None:
        matching_app = {
            "name": release["name"],
            "bundleIdentifier": release["bundleIdentifier"],
            "developerName": release["developerName"],
            "localizedDescription": release["localizedDescription"],
            "versions": [],
            "appPermissions": {},
        }
        apps.append(matching_app)
    else:
        for key in ("name", "developerName", "localizedDescription"):
            matching_app.setdefault(key, release[key])
        matching_app.setdefault("appPermissions", {})
        if not isinstance(matching_app.get("versions"), list):
            raise AltSourceConflictError("matching app versions must be an array")

    pair = (version_entry["version"], version_entry["buildVersion"])
    for index, existing in enumerate(matching_app["versions"]):
        existing_pair = (existing.get("version"), existing.get("buildVersion"))
        if existing_pair != pair:
            continue
        if existing != version_entry:
            raise AltSourceConflictError(
                f"conflicting duplicate version/build: {pair[0]}/{pair[1]}"
            )
        matching_app["versions"][index] = version_entry
        break
    else:
        matching_app["versions"].append(version_entry)

    _sort_source(candidate)
    validate_source(candidate)
    return candidate


def write_updated_source(source_path: str | Path, release_path: str | Path, output_path: str | Path | None = None) -> None:
    source_file = Path(source_path)
    release_file = Path(release_path)
    output_file = Path(output_path) if output_path is not None else source_file
    source = json.loads(source_file.read_text(encoding="utf-8"))
    release = json.loads(release_file.read_text(encoding="utf-8"))
    updated = update_source(source, release)
    output_file.write_text(
        json.dumps(updated, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="source.json to update")
    parser.add_argument("release_metadata", type=Path, help="JSON release metadata")
    parser.add_argument("--output", type=Path, help="optional output source path")
    args = parser.parse_args(argv)
    try:
        write_updated_source(args.source, args.release_metadata, args.output)
    except (OSError, json.JSONDecodeError, AltSourceConflictError, AltSourceValidationError) as error:
        print(f"AltSource generation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
