import re
from pathlib import Path

import yaml


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "publish-source.yml"


def load_workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def workflow_trigger(workflow: dict) -> dict:
    return workflow.get("on") or workflow.get(True)


def test_source_workflow_is_reusable_and_has_pages_permissions() -> None:
    workflow = load_workflow()
    trigger = workflow_trigger(workflow)
    inputs = trigger["workflow_call"]["inputs"]

    for name in (
        "app_repository",
        "app_ref",
        "foundation_repository",
        "foundation_ref",
        "release_tag",
        "source_path",
        "source_url",
        "app_name",
        "developer_name",
        "app_description",
    ):
        assert inputs[name]["required"] is True
    assert workflow["permissions"] == {
        "contents": "read",
        "pages": "write",
        "id-token": "write",
    }


def test_source_workflow_uses_standard_runner_and_bounded_runtime() -> None:
    workflow = load_workflow()
    for job in workflow["jobs"].values():
        assert job["runs-on"] in {"ubuntu-24.04", "ubuntu-22.04", "ubuntu-latest"}
        assert not re.search(r"larger|xlarge|metal", job["runs-on"], re.IGNORECASE)
        assert job["timeout-minutes"] == 15


def test_source_workflow_reads_release_metadata_and_validates_ipa() -> None:
    workflow = load_workflow()
    run_text = "\n".join(step.get("run", "") for job in workflow["jobs"].values() for step in job.get("steps", []))

    assert "gh release view" in run_text
    assert "gh release download" in run_text
    assert "foundation/scripts/validate_ipa.py" in run_text
    assert "foundation/scripts/generate_alt_source.py" in run_text
    assert "foundation/scripts/validate_alt_source.py" in run_text
    assert "build-manifest.json" in run_text


def test_source_workflow_deploys_only_validated_json_to_pages() -> None:
    workflow = load_workflow()
    build_steps = workflow["jobs"]["build-source"]["steps"]
    deploy_steps = workflow["jobs"]["deploy-pages"]["steps"]

    assert any(step.get("uses", "").startswith("actions/upload-pages-artifact@") for step in build_steps)
    assert any(step.get("uses", "").startswith("actions/deploy-pages@") for step in deploy_steps)
    assert "source.json" in "\n".join(step.get("run", "") for step in build_steps)
    assert workflow["jobs"]["deploy-pages"]["needs"] == "build-source"


def test_source_workflow_does_not_use_signing_secrets() -> None:
    workflow = load_workflow()
    trigger = workflow_trigger(workflow)
    assert "secrets" not in trigger
    assert all("secrets" not in job for job in workflow["jobs"].values())
