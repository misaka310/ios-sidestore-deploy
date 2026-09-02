import re
from pathlib import Path

import yaml


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "reusable-build-unsigned-ipa.yml"


def load_workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def workflow_trigger(workflow: dict) -> dict:
    return workflow.get("on") or workflow.get(True)


def test_reusable_workflow_has_explicit_unsigned_call_contract() -> None:
    workflow = load_workflow()
    trigger = workflow_trigger(workflow)
    inputs = trigger["workflow_call"]["inputs"]

    for name in (
        "foundation_repository",
        "foundation_ref",
        "scheme",
        "project_path",
        "workspace_path",
        "configuration",
        "app_name",
        "app_version",
        "build_number",
        "minimum_os_version",
    ):
        assert name in inputs
    assert "secrets" not in trigger["workflow_call"]


def test_workflow_uses_standard_macos_and_read_only_permissions() -> None:
    workflow = load_workflow()
    assert workflow["permissions"] == {"contents": "read"}
    job = workflow["jobs"]["build"]
    runner = job["runs-on"]
    assert runner in {"macos-14", "macos-15", "macos-latest"}
    assert not re.search(r"larger|xlarge|metal", runner, re.IGNORECASE)


def test_workflow_separates_app_and_foundation_checkouts() -> None:
    workflow = load_workflow()
    steps = workflow["jobs"]["build"]["steps"]
    checkouts = [step for step in steps if step.get("uses", "").startswith("actions/checkout@")]

    assert len(checkouts) == 2
    assert checkouts[0]["with"]["path"] == "app"
    assert checkouts[1]["with"]["repository"] == "${{ inputs.foundation_repository }}"
    assert checkouts[1]["with"]["ref"] == "${{ inputs.foundation_ref }}"
    assert checkouts[1]["with"]["path"] == "foundation"


def test_workflow_builds_validates_and_uploads_unsigned_outputs() -> None:
    workflow = load_workflow()
    steps = workflow["jobs"]["build"]["steps"]
    run_text = "\n".join(step.get("run", "") for step in steps)

    assert "xcodebuild" in run_text
    assert "-sdk iphoneos" in run_text
    assert "CODE_SIGNING_ALLOWED=NO" in run_text
    assert "CODE_SIGNING_REQUIRED=NO" in run_text
    assert "CODE_SIGN_IDENTITY=\"\"" in run_text
    assert "foundation/scripts/package_ipa.sh" in run_text
    assert "foundation/scripts/validate_ipa.py" in run_text
    assert '"signed": False' in run_text
    assert any(step.get("uses", "").startswith("actions/upload-artifact@") for step in steps)
