"""SC-002: a repository nobody wired up sees the exact behaviour it saw before.

The gate surface this feature touches, enumerated because SC-002 measures
against it and nobody had written it down until now:

- `wfctl status` — the JSON and console payload gain `session_open` and
  `session_holder`, and neither may change what an unwired caller already read.
- `wfctl resume` — gains the holder-relation guard (`test_session_is_open.py`
  covers the guard itself; this covers that an unwired caller never trips it).
- `wfctl end` — the same guard, the same requirement.
- `wfctl start` — gains the takeover; an unwired caller must never trigger one.
- `speckit-orchestrate`'s step-0 gate — reads `session_open` instead of
  `session_started` and is markdown, not code this file can invoke. Its own
  tests are `test_skills_ship.py::test_start_session_names_no_host_variable` and
  `::test_no_skill_reads_the_event_log_for_session_state`; not repeated here.

Every test below presents no identity at all, and is parametrised over how the
branch was left by whoever else touched it — never started, started before this
feature existed, started and held by somebody else, or started and already
ended. An unwired caller must read the same four outcomes it always did,
whichever of those it lands on: `session_open_for` resolves every one of them to
`"none"` or `"unknown"` (`wfctl/_session.py`), never `"other"`, so nothing here
should ever refuse.
"""
from __future__ import annotations

import json
import types

import pytest
from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()


def _leave_the_branch(
    storyctl_dir: types.SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
) -> None:
    """Set up the branch the way somebody else might have left it, then get out
    of the way — every assertion below presents no identity of its own.

    `end` and `resume` carry no `--session-id` flag (`_caller_identity` reads
    only `WFCTL_SESSION_ID`), so "someone else" is set up through the
    environment and cleared before the assertion runs.
    """
    if shape == "never-started":
        return
    if shape == "started-with-no-identity":
        # A branch recorded before this feature: `start` with nobody wired up.
        runner.invoke(app, ["start"])
        return
    if shape == "held-by-another":
        result = runner.invoke(app, ["start", "--session-id", "someone-else"])
        assert result.exit_code == 0, result.output
        return
    if shape == "wrapped-up":
        runner.invoke(app, ["start", "--session-id", "someone-else"])
        monkeypatch.setenv("WFCTL_SESSION_ID", "someone-else")
        result = runner.invoke(app, ["end"])
        assert result.exit_code == 0, result.output
        monkeypatch.delenv("WFCTL_SESSION_ID")
        return
    raise AssertionError(f"unhandled shape: {shape!r}")


BRANCH_SHAPES = [
    "never-started",
    "started-with-no-identity",
    "held-by-another",
    "wrapped-up",
]


@pytest.mark.parametrize("shape", BRANCH_SHAPES)
def test_status_reports_the_released_answer(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, shape: str
) -> None:
    """`session_open` mirrors `session_started`; `session_holder` is never
    `"other"` for a caller who presented nothing, whatever the branch's actual
    holder is."""
    _leave_the_branch(storyctl_dir, monkeypatch, shape)

    payload = json.loads(runner.invoke(app, ["status", "--json"]).output)

    assert payload["session_open"] is payload["session_started"]
    assert payload["session_holder"] != "other"


@pytest.mark.parametrize("shape", BRANCH_SHAPES)
def test_resume_gives_the_released_verdict(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, shape: str
) -> None:
    """Refuses only where the released version already refused: no session ever
    started. Every other shape — including one another conversation is holding
    or already wrapped up — proceeds exactly as before this feature existed."""
    _leave_the_branch(storyctl_dir, monkeypatch, shape)

    result = runner.invoke(app, ["resume"])

    assert result.exit_code == (0 if shape != "never-started" else 1)


@pytest.mark.parametrize("shape", BRANCH_SHAPES)
def test_end_gives_the_released_verdict(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, shape: str
) -> None:
    """The same requirement as `resume`, at `end`'s own guard."""
    _leave_the_branch(storyctl_dir, monkeypatch, shape)

    result = runner.invoke(app, ["end"])

    assert result.exit_code == (0 if shape != "never-started" else 1)


@pytest.mark.parametrize("shape", BRANCH_SHAPES)
def test_start_never_takes_over_for_an_unwired_caller(
    storyctl_dir: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch, shape: str
) -> None:
    """FR-006: presenting no identity must never displace whatever holder is
    already on record — the property a takeover exists to make possible for a
    wired caller, and to never do to an unwired one."""
    _leave_the_branch(storyctl_dir, monkeypatch, shape)

    events_path = storyctl_dir.agent_dir / "events.jsonl"
    events_before = events_path.read_text() if events_path.exists() else ""
    result = runner.invoke(app, ["start"])
    events_after = events_path.read_text()

    assert result.exit_code == 0
    assert "took over" not in result.output
    # Idempotent, or the sitting-boundary append, or the branch's first `start`
    # — never a takeover line carrying a `session_id`, which only a wired caller
    # can produce.
    assert '"session_id"' not in events_after.replace(events_before, "", 1)
