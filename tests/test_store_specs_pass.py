"""The `store-specs` pass under `implement`.

Every fixture here builds a real spec store under `tmp_path`: a bare remote,
a clone of it as the spec root, and a code repository beside it. The pass
reads git, so a stub would only repeat back what the test told it.
"""

from __future__ import annotations

import json
import subprocess
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.conftest import CLEAN_PLAN, CLEAN_SPEC, git_repo, write_plan_review
from tests.test_spec_store import _git, _remote_and_clones
from wfctl import _evidence
from wfctl.cli import app

runner = CliRunner()
BRANCH = "359-push-specs-to-trunk"


@pytest.fixture
def finished(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> types.SimpleNamespace:
    """A feature whose `implement` reads done, with its spec dir in a spec
    store that has an upstream, and nothing in it stored yet.

    `tasks.md` has every task ticked and the code repository declares no
    definition of done, so `implement`'s own reading is `done` and the pass
    is the only thing left to read.
    """
    remote, here, there = _remote_and_clones(tmp_path)
    project = git_repo(tmp_path / "project")
    spec_dir = here / BRANCH
    spec_dir.mkdir()
    (spec_dir / "spec.md").write_text(CLEAN_SPEC)
    (spec_dir / "plan.md").write_text(CLEAN_PLAN)
    write_plan_review(spec_dir)
    (spec_dir / "tasks.md").write_text("- [x] T001 done\n")
    (spec_dir / "checklists").mkdir()
    (spec_dir / "checklists" / "analysis-report.md").write_text("x\n")
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(here))
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(project))
    monkeypatch.setenv("WFCTL_BRANCH", BRANCH)
    monkeypatch.setenv("WFCTL_STATE_DIR", str(state))
    return types.SimpleNamespace(
        remote=remote, here=here, there=there, project=project, spec_dir=spec_dir,
        state=state,
    )


def _payload() -> dict:
    result = runner.invoke(app, ["status", "--json"])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def _implement(payload: dict) -> dict:
    return next(s for s in payload["steps"] if s["name"] == "implement")


def _pass(payload: dict) -> dict:
    return next(s for s in _implement(payload)["sub_steps"] if s["name"] == "store-specs")


def _commit_spec_dir(finished: types.SimpleNamespace) -> None:
    _git(finished.here, "add", "-A", "--", BRANCH)
    _git(finished.here, "commit", "-m", "specs(359): by hand", "--", BRANCH)


def _evidence_for(finished: types.SimpleNamespace) -> _evidence.Evidence:
    return _evidence.build_evidence(finished.spec_dir, finished.project, finished.state)


def test_a_finished_implement_with_uncommitted_files_names_store_specs(
    finished: types.SimpleNamespace,
) -> None:
    """FR-017 and `store-specs-implement-pass.md`. An unattended run only runs
    the next command, so the store has to be the next command once the work
    is done, or the run opens a pull request with its specs unstored."""
    payload = _payload()

    assert _pass(payload)["state"] == "in_progress"
    assert _pass(payload)["annotation"] == "uncommitted: 5 files"
    assert _implement(payload)["state"] == "in_progress"
    assert payload["next_command"] == "/store-specs"
    assert payload["auto"] is True


def test_a_committed_and_pushed_spec_dir_reads_done_with_no_fetch(
    finished: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-016. `status` runs on every session start, and a pass that fetched
    would make each one wait on the network. `@{u}` is git's local copy of
    the remote branch, which the push updates, so no fetch is needed."""
    _commit_spec_dir(finished)
    _git(finished.here, "push")
    real = subprocess.run
    verbs: list[str] = []

    def record(args: list[str], *a: object, **kw: object) -> object:
        if args[:1] == ["git"]:
            verbs.extend(args)
        return real(args, *a, **kw)  # type: ignore[call-overload]

    monkeypatch.setattr(subprocess, "run", record)

    payload = _payload()

    assert _pass(payload)["state"] == "done"
    assert payload["next_command"] is None
    assert not {"fetch", "pull", "ls-remote", "push"} & set(verbs)


def test_a_committed_and_unpushed_spec_dir_reads_in_progress(
    finished: types.SimpleNamespace,
) -> None:
    """The state a store that could not push leaves behind. `git status` reads
    clean there, and only the comparison with `@{u}` shows the files are
    still not on the remote."""
    _commit_spec_dir(finished)

    payload = _payload()

    assert _pass(payload)["state"] == "in_progress"
    assert _pass(payload)["annotation"] == "committed, not pushed"
    assert payload["next_command"] == "/store-specs"


def test_the_pass_never_puts_a_reason_on_its_reading(finished: types.SimpleNamespace) -> None:
    """Research R4. The roll-up copies a pass's reason onto its step, and a
    held `implement` with no open task routes to `wfctl verify`, which would
    show a green verdict and never store anything."""
    uncommitted = _evidence.store_specs(_evidence_for(finished))
    _commit_spec_dir(finished)
    unpushed = _evidence.store_specs(_evidence_for(finished))

    assert (uncommitted.state, unpushed.state) == ("in_progress", "in_progress")
    assert uncommitted.reason is None and unpushed.reason is None
    assert _implement(_payload())["reason"] is None
    assert _payload()["next_command"] != "wfctl verify"


def test_a_claim_that_the_pass_does_not_apply_wins_over_the_reader(
    finished: types.SimpleNamespace,
) -> None:
    """A person can decide a branch's specs need no storing, and that judgment
    is not overturned by what git says, as for every other pass."""
    claimed = runner.invoke(
        app, ["step", "none", "implement.store-specs", "--reason", "a throwaway spike"],
    )
    assert claimed.exit_code == 0, claimed.output

    payload = _payload()

    assert _pass(payload)["state"] == "skipped"
    assert _pass(payload)["claimed"] == "a throwaway spike"
    assert payload["next_command"] is None

