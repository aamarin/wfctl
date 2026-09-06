"""`wfctl end` says which of its two outcomes happened (#239).

It writes `session-summary.md` only when the file is absent — a second `end`
must not destroy prose someone filled in between the two — but it printed
`Summary: <path>` either way. The state dir is per branch, so a worktree branch
only ever sees the write; `main` only ever sees the keep. Twice in two days a
session on `main` followed `end-session` step 4 to a file headed with the
previous day's date and wrote over it by hand.

The report is what changes here. The write rule does not, and neither does what
the line is allowed to claim: a pre-existing summary is as often a handoff
written *for* the branch by `worktree-handoff` as a stale one left behind, and
`end` cannot tell which it is holding.
"""
from __future__ import annotations

import os
import types
from pathlib import Path

from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()

# Every way the kept line could over-claim. `end` observes a file and an mtime;
# it never observes who wrote it, when their session ran, or whether what is in
# there is out of date.
AUTHORSHIP_CLAIMS = ("stale", "earlier session", "previous session", "out of date")


def _run_end() -> str:
    runner.invoke(app, ["start"])
    result = runner.invoke(app, ["end"])
    assert result.exit_code == 0, result.output
    return result.output


def _summary_path(storyctl_dir: types.SimpleNamespace) -> Path:
    return storyctl_dir.agent_dir / "session-summary.md"


def test_a_written_scaffold_is_reported_without_a_caveat(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The arm that always worked, pinned so the fix cannot pay for itself here.

    A warning on every run would be as uninformative as the single line it
    replaces — the caller would learn to skip it.
    """
    output = _run_end()

    assert "Summary: " in output
    assert "kept" not in output
    assert _summary_path(storyctl_dir).exists()


def test_a_second_end_says_it_wrote_nothing_and_when_the_file_last_changed(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The defect: two outcomes, one sentence.

    The mtime is in the line because it is the one thing that lets the reader
    decide whether the file belongs to this session's work without opening it.
    """
    _run_end()
    _summary_path(storyctl_dir).write_text("# hand-written prose\n")
    # 2026-01-02T03:04:05Z, as an epoch. Fixed rather than read back from the
    # file, so the assertion below fails if the rendering drifts by an offset
    # instead of agreeing with whatever it just produced.
    os.utime(_summary_path(storyctl_dir), (1767323045, 1767323045))

    output = _run_end()

    assert "kept" in output
    assert "this session wrote nothing" in output
    assert "last modified 2026-01-02T03:04:05Z" in output
    # The write rule is unchanged — that is #239's premise, not a side effect.
    assert _summary_path(storyctl_dir).read_text() == "# hand-written prose\n"


def test_the_path_line_stays_a_path_and_nothing_else(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The caveat is a second line, not a suffix.

    `Summary: <path>` is the only machine-readable thing `end` prints, and the
    next session opens what follows the colon. An em-dash clause appended there
    is inside the path as far as any reader that splits on it is concerned.
    """
    _run_end()

    output = _run_end()

    summary_line = next(ln for ln in output.splitlines() if "Summary:" in ln)
    assert summary_line.strip().endswith("session-summary.md")


def test_a_handoff_written_before_the_first_session_is_not_called_stale(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The case that rules out the cheap discriminator.

    `worktree-handoff` writes a summary *for* a branch before any session runs
    on it, and `workmux add` runs `wfctl start` in `post_create` — so the file
    lands after the branch's first `start` event. "Older than the session"
    therefore classifies a legitimate handoff as leftover prose, which is the
    reported failure inverted.
    """
    _summary_path(storyctl_dir).write_text("# Handoff — read this first\n")

    output = _run_end()

    assert "kept" in output
    for claim in AUTHORSHIP_CLAIMS:
        assert claim not in output.lower()
    assert _summary_path(storyctl_dir).read_text() == "# Handoff — read this first\n"
