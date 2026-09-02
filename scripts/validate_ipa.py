#!/usr/bin/env python3
"""Validate the safe, unsigned IPA contract used by the deployment workflow."""

from __future__ import annotations

import argparse
import json
import plistlib
import posixpath
import sys
import zipfile
from pathlib import Path
from typing import Any


class IpaValidationError(ValueError):
    """Raised when an IPA does not satisfy the unsigned archive contract."""


def _validate_zip_member_name(name: str) -> None:
    normalized = name.replace("\\", "/")
    if "\x00" in normalized:
        raise IpaValidationError("archive contains a path traversal or NUL path")
    if normalized.startswith("/") or posixpath.isabs(normalized):
        raise IpaValidationError(f"archive contains path traversal: {name}")

    parts = [part for part in normalized.split("/") if part not in ("", ".")]
    if ".." in parts:
        raise IpaValidationError(f"archive contains path traversal: {name}")


def _required_string(info: dict[str, Any], key: str) -> str:
    value = info.get(key)
    if not isinstance(value, str) or not value.strip():
        raise IpaValidationError(f"{key} is missing or empty in Info.plist")
    return value.strip()


def validate_ipa(ipa_path: str | Path) -> dict[str, Any]:
    """Validate an IPA and return metadata extracted from its app bundle."""

    path = Path(ipa_path)
    if not path.is_file():
        raise IpaValidationError(f"IPA file does not exist: {path}")

    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as error:
        raise IpaValidationError(f"{path} is not a valid ZIP archive") from error

    with archive:
        names = archive.namelist()
        for name in names:
            _validate_zip_member_name(name)

        payload_names = [name for name in names if name == "Payload/" or name.startswith("Payload/")]
        if not payload_names:
            raise IpaValidationError("Payload/ directory is missing")

        app_roots: set[str] = set()
        for name in names:
            parts = name.rstrip("/").split("/")
            if len(parts) >= 2 and parts[0] == "Payload" and parts[1].endswith(".app"):
                app_roots.add(parts[1])

        if len(app_roots) != 1:
            raise IpaValidationError(
                "IPA must contain exactly one .app bundle directly under Payload/"
            )

        app_name = next(iter(app_roots))
        app_prefix = f"Payload/{app_name}/"
        signing_entries = [
            name
            for name in names
            if name.startswith(app_prefix)
            and (
                name.endswith(".mobileprovision")
                or "_CodeSignature/" in name
                or name.endswith("/_CodeSignature")
            )
        ]
        if signing_entries:
            raise IpaValidationError(
                "IPA contains signing material: " + ", ".join(sorted(signing_entries))
            )

        info_name = f"{app_prefix}Info.plist"
        if info_name not in names:
            raise IpaValidationError(f"{info_name} Info.plist is missing")

        try:
            info = plistlib.loads(archive.read(info_name))
        except (plistlib.InvalidFileException, ValueError, TypeError) as error:
            raise IpaValidationError(f"{info_name} Info.plist is malformed") from error
        if not isinstance(info, dict):
            raise IpaValidationError(f"{info_name} Info.plist is malformed")

        bundle_identifier = _required_string(info, "CFBundleIdentifier")
        app_version = _required_string(info, "CFBundleShortVersionString")
        build_number = _required_string(info, "CFBundleVersion")

    return {
        "appName": app_name,
        "bundleIdentifier": bundle_identifier,
        "appVersion": app_version,
        "buildNumber": build_number,
        "signed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ipa", type=Path, help="path to the IPA/ZIP to validate")
    args = parser.parse_args(argv)

    try:
        metadata = validate_ipa(args.ipa)
    except IpaValidationError as error:
        print(f"IPA validation failed: {error}", file=sys.stderr)
        return 1

    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
