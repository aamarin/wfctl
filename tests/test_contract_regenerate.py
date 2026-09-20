"""`wfctl contract regenerate` (T031, T032) — against this repository's own
shipped `wfctl/contracts/status-payload.json`, the one file the command has
any business rewriting.

Every test here corrupts a copy of a real, tracked file and restores it in a
`finally`: this command's whole job is editing files this checkout ships, so
there is no synthetic repo to point it at instead.
"""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()

CONTRACT_PATH = (
    Path(__file__).resolve().parent.parent / "wfctl" / "contracts" / "status-payload.json"
)
PIPELINE_PATH = Path(__file__).resolve().parent.parent / "wfctl" / "_pipeline.py"


def test_regenerate_cleans_up_its_throwaway_repos() -> None:
    """`_init_throwaway_repo` never removes the directory it creates — five
    fixture repos plus the live probe, six per run, with no cleanup short of
    OS temp reaping. This is the one caller invoked repeatedly by a developer
    rather than once per test process, so it removes what it built."""
    import tempfile

    before = {
        p.name for p in Path(tempfile.gettempdir()).glob("contract-*")
    }

    result = runner.invoke(app, ["contract", "regenerate"])
    assert result.exit_code == 0

    after = {
        p.name for p in Path(tempfile.gettempdir()).glob("contract-*")
    }
    assert after == before


def test_a_clean_tree_reports_no_change_and_writes_nothing() -> None:
    before = CONTRACT_PATH.read_bytes()
    result = runner.invoke(app, ["contract", "regenerate"])
    assert result.exit_code == 0
    assert "no change" in result.output
    assert CONTRACT_PATH.read_bytes() == before


def test_hold_version_moves_the_paths_and_leaves_the_version() -> None:
    original = CONTRACT_PATH.read_text()
    try:
        corrupted = json.loads(original)
        corrupted["paths"]["spec_dir"] = "string"  # a fake drift to correct
        CONTRACT_PATH.write_text(json.dumps(corrupted, indent=2))

        result = runner.invoke(app, ["contract", "regenerate", "--hold-version"])

        assert result.exit_code == 0
        assert "version held" in result.output
        assert "commit body" in result.output
        after = json.loads(CONTRACT_PATH.read_text())
        assert after["paths"]["spec_dir"] == "string | null"
        assert after["version"] == corrupted["version"]
    finally:
        CONTRACT_PATH.write_text(original)


def test_a_bump_moves_both_the_file_and_the_pipeline_constant() -> None:
    original_contract = CONTRACT_PATH.read_text()
    original_pipeline = PIPELINE_PATH.read_text()
    try:
        corrupted = json.loads(original_contract)
        corrupted["paths"]["spec_dir"] = "string"
        CONTRACT_PATH.write_text(json.dumps(corrupted, indent=2))

        result = runner.invoke(app, ["contract", "regenerate"])

        assert result.exit_code == 0
        assert "major" in result.output
        after = json.loads(CONTRACT_PATH.read_text())
        assert after["version"] != corrupted["version"]
        assert f'STATUS_PAYLOAD_VERSION = "{after["version"]}"' in PIPELINE_PATH.read_text()
    finally:
        CONTRACT_PATH.write_text(original_contract)
        PIPELINE_PATH.write_text(original_pipeline)
