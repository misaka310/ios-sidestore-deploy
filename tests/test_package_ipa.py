import plistlib
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.validate_ipa import validate_ipa


REPO_ROOT = Path(__file__).parents[1]
SCRIPT = REPO_ROOT / "scripts" / "package_ipa.sh"
HAS_POSIX_ZIP_TOOLCHAIN = all(shutil.which(command) for command in ("bash", "zip"))


def run_packager(app_path: Path, output_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), str(app_path), str(output_path)],
        check=False,
        capture_output=True,
        text=True,
    )


def make_app(tmp_path: Path, name: str = "Test.app") -> Path:
    app_path = tmp_path / name
    app_path.mkdir()
    (app_path / "Info.plist").write_bytes(
        plistlib.dumps(
            {
                "CFBundleIdentifier": "com.example.Test",
                "CFBundleShortVersionString": "1.0",
                "CFBundleVersion": "1",
            },
            fmt=plistlib.FMT_BINARY,
        )
    )
    executable = app_path / "Test"
    executable.write_bytes(b"unsigned executable")
    executable.chmod(executable.stat().st_mode | 0o100)
    return app_path


def test_packager_script_exists() -> None:
    assert SCRIPT.is_file()


@pytest.mark.skipif(
    not HAS_POSIX_ZIP_TOOLCHAIN,
    reason="package_ipa.sh requires the macOS bash and zip toolchain",
)
def test_packages_app_under_single_payload_root(tmp_path: Path) -> None:
    app_path = make_app(tmp_path)
    output_path = tmp_path / "out" / "Test-1.0.ipa"

    result = run_packager(app_path, output_path)

    assert result.returncode == 0, result.stderr
    assert validate_ipa(output_path)["appName"] == "Test.app"


@pytest.mark.skipif(
    not HAS_POSIX_ZIP_TOOLCHAIN,
    reason="package_ipa.sh requires the macOS bash and zip toolchain",
)
@pytest.mark.parametrize(
    ("app_factory", "output_exists", "message"),
    [
        (lambda tmp_path: tmp_path / "Missing.app", False, "does not exist"),
        (lambda tmp_path: make_app(tmp_path), True, "already exists"),
        (lambda tmp_path: tmp_path / "NoInfo.app", False, "Info.plist is missing"),
    ],
)
def test_rejects_packaging_precondition_failures(
    tmp_path: Path, app_factory, output_exists: bool, message: str
) -> None:
    app_path = app_factory(tmp_path)
    if app_path.name == "NoInfo.app":
        app_path.mkdir()
    output_path = tmp_path / "out" / "Test.ipa"
    output_path.parent.mkdir()
    if output_exists:
        output_path.write_bytes(b"existing")

    result = run_packager(app_path, output_path)

    assert result.returncode != 0
    assert message in result.stderr
