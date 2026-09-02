import re
from pathlib import Path

import yaml


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "release.yml"


def load_workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def workflow_trigger(workflow: dict) -> dict:
    return workflow.get("on") or workflow.get(True)


def test_release_is_tag_triggered_and_uses_least_privilege_write_access() -> None:
    workflow = load_workflow()
    trigger = workflow_trigger(workflow)

    assert "workflow_call" in trigger
    assert trigger["workflow_call"]["inputs"]["release_tag"]["required"] is True
    assert trigger["workflow_call"]["inputs"]["app_ref"]["required"] is True
    assert workflow["permissions"] == {"contents": "write"}
    job = workflow["jobs"]["release"]
    assert job["runs-on"] in {"macos-14", "macos-15", "macos-latest"}
    assert not re.search(r"larger|xlarge|metal", job["runs-on"], re.IGNORECASE)
    assert job["timeout-minutes"] == 45


def test_release_checks_tag_and_version_consistency() -> None:
    workflow = load_workflow()
    run_text = "\n".join(step.get("run", "") for step in workflow["jobs"]["release"]["steps"])

    assert "GITHUB_REF" in run_text
    assert "GITHUB_REF_NAME" in run_text
    assert 'v${EXPECTED_VERSION}' in run_text
    assert "Release tag does not match" in run_text


def test_release_rebuilds_from_explicit_tag_and_foundation_ref() -> None:
    workflow = load_workflow()
    steps = workflow["jobs"]["release"]["steps"]
    checkouts = [step for step in steps if step.get("uses", "").startswith("actions/checkout@")]
    assert len(checkouts) == 2
    assert checkouts[0]["with"]["path"] == "app"
    assert checkouts[0]["with"]["ref"] == "${{ github.ref }}"
    assert checkouts[1]["with"]["path"] == "foundation"
    assert checkouts[1]["with"]["ref"] == "${{ inputs.foundation_ref }}"

    run_text = "\n".join(step.get("run", "") for step in steps)
    assert "-sdk iphoneos" in run_text
    assert "CODE_SIGNING_ALLOWED=NO" in run_text
    assert "CODE_SIGNING_REQUIRED=NO" in run_text
    assert 'CODE_SIGN_IDENTITY=""' in run_text
    assert "foundation/scripts/package_ipa.sh" in run_text
    assert "foundation/scripts/validate_ipa.py" in run_text


def test_release_validates_manifest_in_isolated_environment_before_publish() -> None:
    workflow = load_workflow()
    run_text = "\n".join(step.get("run", "") for step in workflow["jobs"]["release"]["steps"])

    assert 'python3 -m venv "$RUNNER_TEMP/manifest-venv"' in run_text
    assert '"$RUNNER_TEMP/manifest-venv/bin/python" -m pip install' in run_text
    assert "build-manifest.schema.json" in run_text
    assert "gh release create" in run_text


def test_release_rechecks_published_asset_hash() -> None:
    workflow = load_workflow()
    run_text = "\n".join(step.get("run", "") for step in workflow["jobs"]["release"]["steps"])

    assert "gh release download" in run_text
    assert "shasum -a 256" in run_text
    assert "Published IPA hash mismatch" in run_text
    publish_steps = [
        step for step in workflow["jobs"]["release"]["steps"] if step.get("name") == "Publish GitHub Release"
    ]
    assert publish_steps[0]["env"]["GH_TOKEN"] == "${{ github.token }}"


def test_release_workflow_does_not_request_signing_secrets() -> None:
    workflow = load_workflow()
    trigger = workflow_trigger(workflow)
    assert "secrets" not in trigger
    assert "secrets" not in workflow["jobs"]["release"]
