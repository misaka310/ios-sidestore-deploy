import copy
import json
from pathlib import Path

import pytest

from scripts.generate_alt_source import AltSourceConflictError, update_source
from scripts.validate_alt_source import AltSourceValidationError, validate_source


SOURCE_TEMPLATE = {
    "name": "SideStore Deployment Foundation",
    "subtitle": "Unsigned iOS app releases for SideStore.",
    "description": "A public AltSource for the proof application.",
    "apps": [],
    "news": [],
}


def release(
    version: str = "1.0",
    build: str = "1",
    *,
    bundle_identifier: str = "com.example.SideStoreSample",
    url: str | None = None,
) -> dict:
    return {
        "name": "SideStore Sample",
        "bundleIdentifier": bundle_identifier,
        "developerName": "SideStore Deployment Foundation",
        "localizedDescription": "A minimal proof app for the SideStore deployment path.",
        "version": version,
        "buildVersion": build,
        "date": "2026-09-03T00:00:00Z",
        "downloadURL": url or f"https://github.com/example/releases/download/v{version}/SideStoreSample-{version}.ipa",
        "size": 12345,
        "sha256": "a" * 64,
        "minOSVersion": "17.0",
    }


def test_first_version_creates_a_supported_alt_source_entry() -> None:
    result = update_source(copy.deepcopy(SOURCE_TEMPLATE), release())

    app = result["apps"][0]
    assert app["bundleIdentifier"] == "com.example.SideStoreSample"
    assert app["versions"][0]["version"] == "1.0"
    assert app["versions"][0]["buildVersion"] == "1"
    assert app["appPermissions"] == {}
    validate_source(result)


def test_newer_version_is_inserted_first() -> None:
    source = update_source(copy.deepcopy(SOURCE_TEMPLATE), release("1.0", "1"))
    source = update_source(source, release("1.1", "2"))

    versions = source["apps"][0]["versions"]
    assert [(item["version"], item["buildVersion"]) for item in versions] == [
        ("1.1", "2"),
        ("1.0", "1"),
    ]
    validate_source(source)


def test_exact_duplicate_is_idempotent() -> None:
    source = update_source(copy.deepcopy(SOURCE_TEMPLATE), release())
    repeated = update_source(copy.deepcopy(source), release())

    assert repeated == source
    assert json.dumps(repeated, indent=2, sort_keys=True) == json.dumps(
        source, indent=2, sort_keys=True
    )


def test_conflicting_duplicate_version_and_build_is_rejected() -> None:
    source = update_source(copy.deepcopy(SOURCE_TEMPLATE), release())
    conflict = release(url="https://github.com/example/releases/download/v1.0/other.ipa")

    with pytest.raises(AltSourceConflictError, match="conflicting duplicate"):
        update_source(source, conflict)


def test_apps_and_versions_have_stable_ordering() -> None:
    source = update_source(copy.deepcopy(SOURCE_TEMPLATE), release("1.0", "1", bundle_identifier="com.example.Z"))
    source = update_source(source, release("1.0", "1", bundle_identifier="com.example.A"))
    source = update_source(source, release("1.0", "1", bundle_identifier="com.example.Z"))

    assert [app["bundleIdentifier"] for app in source["apps"]] == [
        "com.example.A",
        "com.example.Z",
    ]
    validate_source(source)


def test_validator_rejects_an_insecure_download_url() -> None:
    source = update_source(copy.deepcopy(SOURCE_TEMPLATE), release())
    source["apps"][0]["versions"][0]["downloadURL"] = "http://example.invalid/app.ipa"

    with pytest.raises(AltSourceValidationError, match="downloadURL"):
        validate_source(source)


def test_validator_rejects_unsorted_versions() -> None:
    source = update_source(copy.deepcopy(SOURCE_TEMPLATE), release("1.0", "1"))
    source = update_source(source, release("1.1", "2"))
    source["apps"][0]["versions"].reverse()

    with pytest.raises(AltSourceValidationError, match="stable descending order"):
        validate_source(source)


def test_repository_source_template_is_valid() -> None:
    source_path = Path(__file__).parents[1] / "source" / "source.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))

    validate_source(source)
