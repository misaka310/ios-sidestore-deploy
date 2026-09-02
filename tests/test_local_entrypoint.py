from pathlib import Path


def test_windows_local_verification_entrypoint_exists() -> None:
    entrypoint = Path(__file__).parents[1] / "run.ps1"

    assert entrypoint.is_file()
    content = entrypoint.read_text(encoding="utf-8")
    assert "python -m pytest -q" in content
