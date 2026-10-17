"""The `store-specs` pass under `implement`, and how a host block on it routes.

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
from wfctl import _evidence, _spec_store
from wfctl._session import record_blocked, standing_blocks
from wfctl.cli import app

runner = CliRunner()
BRANCH = "359-push-specs-to-trunk"


def _finished_spec_dir(root: Path) -> Path:
    """This branch's spec dir under `root`, with every step up to and
    including `implement` reading done."""
    spec_dir = root / BRANCH
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.md").write_text(CLEAN_SPEC)
    (spec_dir / "plan.md").write_text(CLEAN_PLAN)
    write_plan_review(spec_dir)
    (spec_dir / "tasks.md").write_text("- [x] T001 done\n")
    (spec_dir / "checklists").mkdir()
    (spec_dir / "checklists" / "analysis-report.md").write_text("x\n")
    return spec_dir


def _pin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, spec_root: Path, project: Path) -> Path:
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(spec_root))
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(project))
    monkeypatch.setenv("WFCTL_BRANCH", BRANCH)
    monkeypatch.setenv("WFCTL_STATE_DIR", str(state))
    return state


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
    spec_dir = _finished_spec_dir(here)
    state = _pin(monkeypatch, tmp_path, here, project)
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


def _next_step_file(state: Path) -> str:
    result = runner.invoke(app, ["next"])
    assert result.exit_code == 0, result.output
    return (state / "next-step.md").read_text()


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


def test_a_host_block_on_store_specs_routes_to_the_pass_and_not_to_verify(
    finished: types.SimpleNamespace,
) -> None:
    """Research R15. Verification has already passed by the time this pass is
    outstanding, so sending the reader to `wfctl verify` would show a green
    verdict and leave the hold in place. `next-step.md` is read from the copy
    `wfctl next` writes, because `resume` writes its copy from `build_report`
    and would pass whether or not `next` routes the same way."""
    blocked = runner.invoke(
        app, ["report-block", "store-specs", "--reason", "host classifier: git push"],
    )
    assert blocked.exit_code == 0, blocked.output

    payload = _payload()

    assert payload["next_command"] == "/store-specs"
    assert payload["auto"] is False
    assert _next_step_file(finished.state).startswith("Next step: /store-specs\nauto: false\n")


@pytest.mark.parametrize("action", ["push", "issue-close"])
def test_a_block_for_another_action_still_routes_to_verify(
    finished: types.SimpleNamespace, action: str,
) -> None:
    """The exception is for a block filed under the outstanding pass's own
    name. A block for anything else means what it meant before this pass
    existed, whatever the pass underneath happens to read."""
    record_blocked(finished.state, BRANCH, action, "refused", "implement")

    payload = _payload()

    assert _pass(payload)["state"] == "in_progress"
    assert payload["next_command"] == "wfctl verify"
    assert payload["auto"] is False
    assert _next_step_file(finished.state).startswith("Next step: wfctl verify\n")


def test_a_block_for_a_declared_manual_pass_returns_its_qualified_name(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The rule keys on the outstanding pass's name, not on `store-specs`, so
    a repository's own pass gets the same answer. A manual pass has no
    command to route to, so the answer is the name a manual pass already
    gets without a block. `specs/` here is inside the code repository, so
    `store-specs` reads `skipped` and the declared pass is the outstanding one."""
    storyctl_dir.stage_upstream_of("tasks")
    (storyctl_dir.repo_root / "wfctl.json").write_text(json.dumps({"steps": {"implement": [
        {"name": "sign-off", "manual": True, "evidence": "sign-off.md"},
    ]}}))
    record_blocked(storyctl_dir.agent_dir, "418-storyctl", "sign-off", "refused", "implement")

    payload = _payload()

    assert payload["next_command"] == "implement.sign-off"
    assert payload["auto"] is False
    assert _next_step_file(storyctl_dir.agent_dir).startswith(
        "Next step: implement.sign-off\nauto: false\n"
    )


def test_a_store_after_the_block_records_the_action_and_lifts_the_hold(
    finished: types.SimpleNamespace,
) -> None:
    """Research R15. A person who runs `wfctl store specs` in their own shell
    after the host refused it has done what the block asked for, and should
    not need a second command to say so."""
    runner.invoke(app, ["report-block", "store-specs", "--reason", "refused"])

    stored = runner.invoke(app, ["store", "specs"])

    assert stored.exit_code == 0, stored.output
    assert standing_blocks(finished.state, BRANCH) == []
    payload = _payload()
    assert _pass(payload)["state"] == "done"
    assert _implement(payload)["state"] == "done"
    assert payload["next_command"] is None


@pytest.mark.parametrize("kind", ["store_no_upstream", "in_repo", "unmanaged"])
def test_a_layout_with_nowhere_to_push_reads_skipped_with_no_reason_and_no_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str,
) -> None:
    """User Story 5 and research R4. These are layouts a repository chose on
    purpose, so the pipeline has to finish there. A `skipped` reading with a
    reason is listed as a warning on every `status`, which would nag about a
    choice nobody needs to revisit, so the text goes in `display`. The
    no-upstream text says nothing about a commit, because the pipeline never
    ran the store there (PR-009)."""
    project = git_repo(tmp_path / "project")
    root = {
        "store_no_upstream": lambda: git_repo(tmp_path / "store"),
        "in_repo": lambda: project / "specs",
        "unmanaged": lambda: tmp_path / "notes" / "specs",
    }[kind]()
    spec_dir = _finished_spec_dir(root)
    state = _pin(monkeypatch, tmp_path, root, project)
    display = {
        "store_no_upstream": "no upstream branch; not backed up",
        "in_repo": "inside the code repository; not backed up",
        "unmanaged": f"not backed up anywhere: {root}",
    }[kind]

    reading = _evidence.store_specs(_evidence.build_evidence(spec_dir, project, state))
    payload = _payload()

    assert (reading.state, reading.reason, reading.display) == ("skipped", None, display)
    assert (_pass(payload)["state"], _pass(payload)["annotation"]) == ("skipped", display)
    assert [w for w in payload["warnings"] if w["pass"] == "store-specs"] == []
    assert payload["next_command"] is None


@pytest.mark.parametrize("cause", ["detached", "git_fails"])
def test_a_store_git_cannot_use_holds_implement_instead_of_reading_skipped(
    finished: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, cause: str,
) -> None:
    """A detached spec store read as a layout chosen on purpose, and so did one
    git could not read at all. Either way the pass read `skipped`, which does
    not hold `implement`, and an unattended run finished with nothing stored."""
    if cause == "detached":
        _git(finished.here, "checkout", "--detach")
        display = "the spec store has no branch checked out"
    else:
        def refused(*_: object, **__: object) -> str:
            raise subprocess.CalledProcessError(128, ["git"], "", "fatal: detected dubious ownership")

        monkeypatch.setattr(_spec_store, "_checkout_top", refused)
        display = "git could not read the spec store"

    reading = _evidence.store_specs(_evidence_for(finished))
    payload = _payload()

    assert (reading.state, reading.reason, reading.display) == ("in_progress", None, display)
    assert _pass(payload)["state"] == "in_progress"
    assert payload["next_command"] == "/store-specs"
