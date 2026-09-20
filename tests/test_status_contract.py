"""The shape check itself (US3) — the comparison, the comparison under test,
the version agreement, and the absent-file case.

`tests/test_packaging.py` proves the shipped file travels with the wheel;
this file proves what it says is true.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from importlib import resources
from pathlib import Path

import pytest

from tests.conftest import CONTRACT_FIXTURE_PAYLOADS, CONTRACT_FIXTURES
from wfctl import _contract
from wfctl._contract import (
    bump,
    build_live_probe_repo,
    diff_message,
    isolated_subprocess_env,
    merge_type_paths,
    type_paths,
    wfctl_binary,
)
from wfctl._pipeline import STATUS_PAYLOAD_VERSION


def _live_payload() -> dict:
    """One real `wfctl status --json` run, against `build_live_probe_repo`'s
    isolated repo with no feature ever resolved — the same repo `wfctl
    contract regenerate` runs its own live check against, for the reason that
    function's docstring gives.

    `payload_of` is a hand transcription of the dict literal `status_cmd`
    builds — a key added there and forgotten in the transcription is a path
    no fixture, built from a `PipelineReport` and `payload_of` together, can
    ever see. Only a real subprocess call proves the two still agree
    (FR-013b, 423-the-promised-shape-is-a-shipped-data-file.md § Decision).
    """
    root = build_live_probe_repo()
    env = isolated_subprocess_env(WFCTL_STATE_DIR=str(root / ".agent-runs"))
    result = subprocess.run(
        [wfctl_binary(), "status", "--json"], cwd=root, env=env, capture_output=True, check=True,
    )
    return json.loads(result.stdout)


def test_isolated_subprocess_env_strips_every_wfctl_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The live probe's env-building used to clear only `WFCTL_STATE_DIR`
    (`aee1167`), leaving `WFCTL_BRANCH`/`WFCTL_SPEC_DIR`/`WFCTL_ARCH_DIR`/
    `WFCTL_REPO_ROOT` to leak straight through from a developer's own shell
    into the throwaway repo's `wfctl status` subprocess — the same defect
    class, three siblings left open. Asserts the fix strips the whole
    `WFCTL_` namespace instead of denylisting one variable at a time."""
    monkeypatch.setenv("WFCTL_BRANCH", "some-other-branch")
    monkeypatch.setenv("WFCTL_SPEC_DIR", "/tmp/should-not-leak")
    monkeypatch.setenv("WFCTL_ARCH_DIR", "/tmp/should-not-leak-either")
    monkeypatch.setenv("WFCTL_REPO_ROOT", "/tmp/should-not-leak-either")
    monkeypatch.setenv("SOME_OTHER_VAR", "keep-me")

    env = isolated_subprocess_env(WFCTL_STATE_DIR="/wanted")

    assert env["WFCTL_STATE_DIR"] == "/wanted"
    assert env["SOME_OTHER_VAR"] == "keep-me"
    for leaked in ("WFCTL_BRANCH", "WFCTL_SPEC_DIR", "WFCTL_ARCH_DIR", "WFCTL_REPO_ROOT"):
        assert leaked not in env


def test_init_throwaway_repo_cleans_up_after_a_failed_git_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A git call failing partway through `_init_throwaway_repo` used to leave
    its `mkdtemp` directory on disk with nothing pointing at it — the same
    leak class `54abeca` fixed for the happy path, left open on the exception
    path until now."""
    real_run = subprocess.run
    calls = {"n": 0}

    def flaky_run(cmd, *args, **kwargs):  # type: ignore[no-untyped-def]
        calls["n"] += 1
        if calls["n"] == 2:  # "git config user.email", mid-init
            raise subprocess.CalledProcessError(1, cmd)
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(_contract.subprocess, "run", flaky_run)

    with pytest.raises(subprocess.CalledProcessError):
        _contract._init_throwaway_repo("contract-fail-test-", "some-branch")

    leaked = list(Path(tempfile.gettempdir()).glob("contract-fail-test-*"))
    assert leaked == [], f"leaked: {leaked}"


def test_fixture_states_cleans_up_already_built_repos_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`fixture_states()` used to build its five repos outside any try block
    it owned itself, and used to track each one in `states` only *after* its
    staging finished — a failure on the third fixture's staging (not just its
    build) left the first two, plus the third's own already-built repo, with
    no reference anywhere to clean them up."""
    real_stage = _contract.stage_upstream_of
    built: list[Path] = []
    calls = {"n": 0}

    def flaky_stage(env, step, tasks="- [x] T001 done\n"):  # type: ignore[no-untyped-def]
        built.append(env.repo_root)
        calls["n"] += 1
        if calls["n"] == 3:  # "manual"'s staging, third fixture built
            raise RuntimeError("simulated staging failure")
        return real_stage(env, step, tasks)

    monkeypatch.setattr(_contract, "stage_upstream_of", flaky_stage)

    with pytest.raises(RuntimeError):
        _contract.fixture_states()

    assert len(built) == 3, "expected the failure on the third fixture staged"
    for root in built:
        assert not root.exists(), f"leaked: {root}"


def _observed_paths() -> dict[str, str]:
    """FR-013a/FR-013b's union: every fixture's payload, plus one live run."""
    maps = [type_paths(p) for p in CONTRACT_FIXTURE_PAYLOADS.values()]
    maps.append(type_paths(_live_payload()))
    return merge_type_paths(*maps)


def _recorded_paths() -> dict[str, str]:
    text = resources.files("wfctl").joinpath("contracts/status-payload.json").read_text()
    return json.loads(text)["paths"]


# --- T004: the five fixtures cover what a clean tree never emits ------------

def test_the_five_fixtures_build_and_cover_the_hidden_paths() -> None:
    assert set(CONTRACT_FIXTURES) == {"quiet", "blocked", "manual", "stalled", "nested"}

    merged = merge_type_paths(*(type_paths(p) for p in CONTRACT_FIXTURE_PAYLOADS.values()))
    for path in (
        "attention", "attention.kind", "attention.step", "attention.detail",
        "stall", "stall.step", "stall.passes", "stall.unchanged", "stall.unchanged[]",
        "steps[].sub_steps[]", "steps[].sub_steps[].name", "steps[].sub_steps[].manual",
        "steps[].sub_steps[].claimed", "steps[].sub_steps[].command",
    ):
        assert path in merged, f"no fixture ever emitted {path!r}"


# --- T029: the walker's vocabulary is JSON names, nullable as a union -------

def test_the_walker_uses_json_type_names_not_python_ones() -> None:
    merged = merge_type_paths(type_paths({
        "a": "x", "b": 1, "c": True, "d": None, "e": {"f": 1}, "g": [1],
    }))
    assert merged == {
        "a": "string", "b": "number", "c": "boolean", "d": "null",
        "e": "object", "e.f": "number", "g": "array", "g[]": "number",
    }


def test_a_nullable_path_renders_as_a_union_with_null_last() -> None:
    merged = merge_type_paths(type_paths({"a": {"x": 1}}), type_paths({"a": None}))
    assert merged["a"] == "object | null"


# --- T021: the comparison itself --------------------------------------------

def test_the_shipped_file_matches_the_union_in_both_directions() -> None:
    """FR-013, FR-013a, FR-013b. Not run in front of anyone — this test *is*
    the check FR-015 says must never run in front of `wfctl status`."""
    recorded = _recorded_paths()
    observed = _observed_paths()
    message = diff_message(recorded, observed)
    assert message is None, message


# --- T022: the file's version and the payload's version agree --------------

def test_the_recorded_version_equals_the_emitted_version() -> None:
    text = resources.files("wfctl").joinpath("contracts/status-payload.json").read_text()
    assert json.loads(text)["version"] == STATUS_PAYLOAD_VERSION


# --- T023: the comparison under test ----------------------------------------

def test_a_renamed_key_fails_naming_the_path_and_owing_major() -> None:
    recorded = {"a": "string", "b.c": "number"}
    observed = {"a": "string", "b.d": "number"}  # b.c -> b.d
    assert bump(recorded, observed) == "major"
    message = diff_message(recorded, observed)
    assert message is not None
    assert "b.c" in message and "major" in message


def test_a_renamed_nested_key_fails_the_same_way() -> None:
    """FR-017: the nested step structure is inside the versioned surface, not
    an implementation detail the check is blind to — confirmed at
    `/speckit.clarify` rather than assumed, so a rename at the top level alone
    would leave this clause unproven."""
    recorded = {"steps[].sub_steps[].manual": "boolean"}
    observed = {"steps[].sub_steps[].is_manual": "boolean"}
    assert bump(recorded, observed) == "major"
    message = diff_message(recorded, observed)
    assert message is not None and "steps[].sub_steps[].manual" in message


def test_an_added_key_fails_naming_the_path_and_owing_minor() -> None:
    recorded = {"a": "string"}
    observed = {"a": "string", "b": "number"}
    assert bump(recorded, observed) == "minor"
    message = diff_message(recorded, observed)
    assert message is not None
    assert "b" in message and "minor" in message


def test_a_recorded_path_dropped_from_the_file_but_still_emitted_fails_too() -> None:
    """FR-013, both directions: the file naming a path that was already
    unemitted before this comparison ran is the case a one-directional check
    would miss."""
    recorded = {"a": "string"}
    observed = {"a": "string", "b": "number", "c": "string"}
    # Neither "b" nor "c" is recorded; both must be named.
    message = diff_message(recorded, observed)
    assert message is not None
    assert "b" in message and "c" in message


def test_agreement_reports_nothing() -> None:
    same = {"a": "string", "b.c": "number | null"}
    assert bump(same, dict(same)) is None
    assert diff_message(same, dict(same)) is None


# --- T026: the command works with the shape file absent --------------------

def test_the_command_emits_the_same_version_with_the_shape_file_absent() -> None:
    """FR-011's second clause: the version comes from a constant `status_cmd`
    reads directly, never from `wfctl/contracts/status-payload.json` — proven
    by removing the real installed file and confirming the command still
    succeeds and still emits `STATUS_PAYLOAD_VERSION`. Without this, nothing
    tells a version read off the file from one produced by the constant; the
    file happening to agree today is not evidence of which one `status_cmd`
    actually reads (FR-011, the Edge Case naming a package built without it).
    """
    target = Path(str(resources.files("wfctl").joinpath("contracts/status-payload.json")))
    original = target.read_bytes()
    target.unlink()
    try:
        from typer.testing import CliRunner

        from wfctl.cli import app

        result = CliRunner().invoke(app, ["status", "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["version"] == STATUS_PAYLOAD_VERSION
    finally:
        target.write_bytes(original)
