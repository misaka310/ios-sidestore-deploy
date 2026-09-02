import json
import plistlib
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from scripts.validate_ipa import IpaValidationError, validate_ipa


def write_ipa(tmp_path: Path, entries: dict[str, bytes], name: str = "sample.ipa") -> Path:
    ipa_path = tmp_path / name
    with zipfile.ZipFile(ipa_path, "w") as archive:
        for entry_name, contents in entries.items():
            archive.writestr(entry_name, contents)
    return ipa_path


def plist_bytes(**overrides: object) -> bytes:
    values = {
        "CFBundleIdentifier": "com.example.Test",
        "CFBundleShortVersionString": "1.0",
        "CFBundleVersion": "1",
    }
    values.update(overrides)
    return plistlib.dumps(values, fmt=plistlib.FMT_BINARY)


def valid_entries() -> dict[str, bytes]:
    return {
        "Payload/Test.app/Info.plist": plist_bytes(),
        "Payload/Test.app/Test": b"unsigned executable placeholder",
    }


def test_accepts_valid_ipa_and_returns_app_metadata(tmp_path: Path) -> None:
    ipa_path = write_ipa(tmp_path, valid_entries())

    result = validate_ipa(ipa_path)

    assert result == {
        "appName": "Test.app",
        "bundleIdentifier": "com.example.Test",
        "appVersion": "1.0",
        "buildNumber": "1",
        "signed": False,
    }


@pytest.mark.parametrize(
    ("entries", "message"),
    [
        ({"README.txt": b"missing payload"}, "Payload/ directory is missing"),
        (
            {
                "Payload/First.app/Info.plist": plist_bytes(),
                "Payload/Second.app/Info.plist": plist_bytes(),
            },
            "exactly one .app bundle",
        ),
        ({"Payload/Test.app/Test": b"no plist"}, "Info.plist is missing"),
        ({"Payload/Test.app/Info.plist": b"not a plist"}, "Info.plist is malformed"),
        (
            {"Payload/Test.app/Info.plist": plist_bytes(CFBundleIdentifier="")},
            "CFBundleIdentifier is missing",
        ),
        (
            {"Payload/Test.app/Info.plist": plist_bytes(CFBundleShortVersionString="")},
            "CFBundleShortVersionString is missing",
        ),
        (
            {"Payload/Test.app/Info.plist": plist_bytes(CFBundleVersion="")},
            "CFBundleVersion is missing",
        ),
        ({"../outside.txt": b"path traversal"}, "path traversal"),
        (
            {
                **valid_entries(),
                "Payload/Test.app/embedded.mobileprovision": b"signing material",
            },
            "signing material",
        ),
        (
            {
                **valid_entries(),
                "Payload/Test.app/_CodeSignature/CodeResources": b"signature",
            },
            "signing material",
        ),
    ],
)
def test_rejects_invalid_ipa_layouts(
    tmp_path: Path, entries: dict[str, bytes], message: str
) -> None:
    ipa_path = write_ipa(tmp_path, entries)

    with pytest.raises(IpaValidationError, match=message):
        validate_ipa(ipa_path)


def test_rejects_non_zip_input_with_actionable_error(tmp_path: Path) -> None:
    ipa_path = tmp_path / "not-an-ipa.ipa"
    ipa_path.write_bytes(b"not a zip")

    with pytest.raises(IpaValidationError, match="not a valid ZIP archive"):
        validate_ipa(ipa_path)


def test_cli_returns_nonzero_and_error_text_for_invalid_ipa(tmp_path: Path) -> None:
    ipa_path = write_ipa(tmp_path, {"README.txt": b"missing payload"})
    script_path = Path(__file__).parents[1] / "scripts" / "validate_ipa.py"

    result = subprocess.run(
        [sys.executable, str(script_path), str(ipa_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Payload/ directory is missing" in result.stderr


def test_build_manifest_schema_accepts_unsigned_manifest() -> None:
    schema_path = Path(__file__).parents[1] / "schemas" / "build-manifest.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    manifest = {
        "schemaVersion": 1,
        "repository": "example/sample",
        "commitSha": "a" * 40,
        "workflowRunId": "123",
        "xcodeVersion": "Xcode 16.0",
        "runnerImage": "macos-14",
        "foundationRepository": "example/foundation",
        "foundationRef": "main",
        "scheme": "SideStoreSample",
        "configuration": "Release",
        "bundleIdentifier": "com.example.Test",
        "appVersion": "1.0",
        "buildNumber": "1",
        "minimumOSVersion": "17.0",
        "ipaFileName": "Test-1.0.ipa",
        "ipaSha256": "b" * 64,
        "signed": False,
        "buildTimestampUtc": "2026-09-03T00:00:00Z",
    }

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(manifest)


def test_build_manifest_schema_rejects_signed_manifest() -> None:
    schema_path = Path(__file__).parents[1] / "schemas" / "build-manifest.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    manifest = {
        "schemaVersion": 1,
        "repository": "example/sample",
        "commitSha": "a" * 40,
        "workflowRunId": "123",
        "xcodeVersion": "Xcode 16.0",
        "runnerImage": "macos-14",
        "foundationRepository": "example/foundation",
        "foundationRef": "main",
        "scheme": "SideStoreSample",
        "configuration": "Release",
        "bundleIdentifier": "com.example.Test",
        "appVersion": "1.0",
        "buildNumber": "1",
        "minimumOSVersion": "17.0",
        "ipaFileName": "Test-1.0.ipa",
        "ipaSha256": "b" * 64,
        "signed": True,
        "buildTimestampUtc": "2026-09-03T00:00:00Z",
    }

    with pytest.raises(ValidationError):
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(manifest)
