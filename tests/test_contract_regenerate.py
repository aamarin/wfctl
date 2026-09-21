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


def test_a_missing_file_is_created_without_a_spurious_bump() -> None:
    """`bump({}, observed)` reads every observed path as newly added and
    always returns "minor" — a bump this case does not owe, since nothing
    changed shape; there was simply no prior file to diff against."""
    from wfctl._pipeline import STATUS_PAYLOAD_VERSION

    original_contract = CONTRACT_PATH.read_text()
    original_pipeline = PIPELINE_PATH.read_text()
    try:
        CONTRACT_PATH.unlink()

        result = runner.invoke(app, ["contract", "regenerate"])

        assert result.exit_code == 0
        assert "no prior baseline" in result.output
        after = json.loads(CONTRACT_PATH.read_text())
        assert after["version"] == STATUS_PAYLOAD_VERSION
        assert PIPELINE_PATH.read_text() == original_pipeline
    finally:
        CONTRACT_PATH.write_text(original_contract)
        PIPELINE_PATH.write_text(original_pipeline)


def test_a_version_move_that_cannot_find_the_declaration_fails_and_writes_nothing() -> None:
    """`_rewrite_status_payload_version` returns `False` when it cannot find
    exactly one `STATUS_PAYLOAD_VERSION = "..."` line — an innocuous reformat
    upstream, say. Before this test, the command wrote the bumped contract
    file first and only printed a red line about it, exiting 0: a script
    driving this command reads success, and the tree is left with the shipped
    file and the constant disagreeing — exactly what the version-agreement
    test in test_status_contract.py exists to catch, but only once committed."""
    import wfctl.cli as cli_module

    original_contract = CONTRACT_PATH.read_text()
    original_pipeline = PIPELINE_PATH.read_text()
    try:
        corrupted = json.loads(original_contract)
        corrupted["paths"]["spec_dir"] = "string"
        CONTRACT_PATH.write_text(json.dumps(corrupted, indent=2))

        original_rewrite = cli_module._rewrite_status_payload_version
        cli_module._rewrite_status_payload_version = lambda new_version: False
        try:
            result = runner.invoke(app, ["contract", "regenerate"])
        finally:
            cli_module._rewrite_status_payload_version = original_rewrite

        assert result.exit_code != 0
        assert "could not be moved" in result.output
        assert CONTRACT_PATH.read_text() == json.dumps(corrupted, indent=2)
        assert PIPELINE_PATH.read_text() == original_pipeline
    finally:
        CONTRACT_PATH.write_text(original_contract)
        PIPELINE_PATH.write_text(original_pipeline)


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
