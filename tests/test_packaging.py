"""The shape file ships with the package (FR-012b).

Marked `builds_wheel`: this shells out to a real `python -m build`, which
costs seconds rather than milliseconds — the same reasoning `runs_mypy`
carries for the tests that shell out to mypy.
"""
from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.builds_wheel
def test_the_shipped_shape_file_is_a_member_of_the_built_wheel(tmp_path: Path) -> None:
    """A missing `graft`/package-data entry ships a wheel whose contract file
    is absent — the command still works and the version it emits is still
    correct (FR-011), but the document `SC-005` promises a reader is gone.
    This is the failure that must be caught before release, not by a
    consumer at runtime (FR-012b)."""
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(tmp_path)],
        cwd=REPO_ROOT, check=True, capture_output=True,
    )
    wheels = list(tmp_path.glob("*.whl"))
    assert len(wheels) == 1, wheels

    with zipfile.ZipFile(wheels[0]) as wheel:
        names = wheel.namelist()
    assert "wfctl/contracts/status-payload.json" in names
