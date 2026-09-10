"""Tests for `wfctl arch accept` — the command surface of the promotion transition.

`_arch.accept` is covered in `test_arch_records.py`; what these cover is the part
that only exists at the console. Three of the refusals differ from each other
*only* in what they say, so a test that checked exit codes alone would pass over
a command that gave one message for all three — and the message is the whole
remedy a reader gets.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()


def _record(root: Path, slug: str, status: str, log: str = "- 2026-03-14  proposed    — x") -> Path:
    """A record with a `## Log`, unlike `test_remaining_commands._record`.

    The transition under test appends to that section and raises without one, so
    a helper that omitted it would make every test here fail for a reason none of
    them is about.
    """
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{slug}.md"
    path.write_text(
        f"---\nstatus: {status}\n---\n\n# {slug}\n\n## Decision\n\nx\n\n## Log\n\n{log}\n"
    )
    return path


def _arch_root(agent_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = agent_dir.parent / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    return root


def test_accepting_a_record_puts_it_in_the_contract_and_drops_the_withheld_count(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SC-003, end to end through both commands.

    The two halves are separately true and only interesting together: a record
    can be written to disk with `status: accepted` and still be withheld — an
    unreadable neighbour, a root the projection does not read — so the count line
    moving is what says the write reached the surface the feature exists for.
    """
    root = _arch_root(agent_dir, monkeypatch)
    _record(root, "a-decision", "proposed")
    _record(root, "another", "proposed")

    before = runner.invoke(app, ["arch", "context"]).output
    assert "2 records not shown (2 proposed)" in before

    result = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "on #321"])

    assert result.exit_code == 0
    after = runner.invoke(app, ["arch", "context"]).output
    assert "a-decision" in after
    assert "1 record not shown (1 proposed)" in after


def test_a_record_nobody_accepted_stays_out_of_the_contract(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The negative case. A rule that promotes everything is the same as no rule,
    and accepting one record is the moment a bug that promoted the set would be
    invisible — the command reports one success either way."""
    root = _arch_root(agent_dir, monkeypatch)
    _record(root, "a-decision", "proposed")
    _record(root, "untouched", "proposed")

    runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "on #321"])

    out = runner.invoke(app, ["arch", "context"]).output
    assert "untouched" not in out
    assert "1 record not shown" in out


def test_the_success_line_quotes_the_log_entry_it_wrote(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """That line is the entire artifact of the command.

    A ✓ that only names the slug sends the reader to open the file to see what
    was recorded, which is the one thing they cannot check afterwards if it is
    wrong — the citation is unverifiable by anything but a person reading it.
    """
    root = _arch_root(agent_dir, monkeypatch)
    _record(root, "a-decision", "proposed")

    out = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "on #321"]).output

    assert "a-decision is accepted — on #321" in out
    assert "accepted    — on #321" in out


def test_accepting_twice_refuses_and_names_when_the_first_one_happened(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """User Story 2 scenario 1: the refusal says *when*, not only *that*.

    Without the date the message is indistinguishable from a stale checkout or a
    typo'd slug that happened to hit an accepted record — and the reader's next
    move differs.
    """
    root = _arch_root(agent_dir, monkeypatch)
    path = _record(root, "a-decision", "proposed")
    runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "on #321"])
    after_first = path.read_text()

    result = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "again"])

    assert result.exit_code == 1
    assert "already accepted (" in result.output
    assert "Nothing to do" in result.output
    assert path.read_text() == after_first


def test_an_accepted_record_with_no_logged_acceptance_still_answers_when(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reachable because `_set_status` requires a `## Log`, not an entry in it.

    Dropping the clause would leave a reader unable to tell a missing date from
    a record accepted today, which is the distinction the sentence exists for.
    """
    root = _arch_root(agent_dir, monkeypatch)
    _record(root, "a-decision", "accepted", log="- 2026-03-14  proposed    — x")

    out = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "x"]).output

    assert "already accepted (no acceptance logged)" in out


@pytest.mark.parametrize("status", ["superseded", "rejected", "retired"])
def test_an_ended_record_is_refused_with_the_reason_a_new_record_is_needed(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    """Distinct from already-accepted, because the reader's next action is.

    "Nothing to do" and "write a new record" are opposite instructions, and a
    shared "not proposed" message gives neither.
    """
    root = _arch_root(agent_dir, monkeypatch)
    path = _record(root, "a-decision", status)
    before = path.read_text()

    result = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "x"])

    assert result.exit_code == 1
    assert f"is {status}, not proposed" in result.output
    assert "new record" in result.output
    assert path.read_text() == before


def test_an_unreadable_status_says_to_fix_the_frontmatter(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The third refusal, and the one where acting on the message matters most:
    accepting would overwrite a status line whose contents nobody could recover
    from the file afterwards."""
    root = _arch_root(agent_dir, monkeypatch)
    path = _record(root, "a-decision", "banana")
    before = path.read_text()

    result = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "x"])

    assert result.exit_code == 1
    assert "no readable status" in result.output
    assert "frontmatter" in result.output
    assert path.read_text() == before


def test_a_missing_citation_is_refused_before_anything_is_written(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The field the whole rule rests on.

    Not declared required to the option parser, because that would refuse the
    bare listing below for a citation it has no record to attach one to — so the
    check lives here and this is what proves it runs.
    """
    root = _arch_root(agent_dir, monkeypatch)
    path = _record(root, "a-decision", "proposed")
    before = path.read_text()

    result = runner.invoke(app, ["arch", "accept", "a-decision"])

    assert result.exit_code == 1
    assert "--agreed is required" in result.output
    assert path.read_text() == before


@pytest.mark.parametrize("citation", ["", "   ", "<where>", "<where the human agreed>"])
def test_an_empty_or_placeholder_citation_is_refused(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch, citation: str
) -> None:
    """A reader who pastes the help text back would otherwise commit a record
    whose evidence is the word `where` in angle brackets — the un-auditable
    transition wearing the command that exists to prevent it. Same guard
    `arch none --reason` carries, for the same reason."""
    root = _arch_root(agent_dir, monkeypatch)
    path = _record(root, "a-decision", "proposed")
    before = path.read_text()

    result = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", citation])

    assert result.exit_code == 1
    assert path.read_text() == before


def test_naming_no_record_lists_what_could_be_accepted(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-007. The count in `arch context` says how many are withheld and never
    which — which is how a backlog reached fourteen — so the names live here,
    where someone is already acting on one."""
    root = _arch_root(agent_dir, monkeypatch)
    _record(root, "waiting", "proposed")
    _record(root, "also-waiting", "proposed")
    _record(root, "in-force", "accepted")

    result = runner.invoke(app, ["arch", "accept"])

    assert result.exit_code == 1
    assert "waiting" in result.output
    assert "also-waiting" in result.output
    assert "in-force" not in result.output


def test_naming_no_record_with_nothing_promotable_still_exits_one(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Green over a no-op is the reading this repo refuses everywhere else.

    An earlier draft exited 0 here, reasoning that nothing was asked for that
    could not be given. A caller that asked to accept and accepted nothing has
    failed, and the reason it failed is not the caller's to guess from a 0.
    """
    root = _arch_root(agent_dir, monkeypatch)
    _record(root, "in-force", "accepted")

    result = runner.invoke(app, ["arch", "accept"])

    assert result.exit_code == 1
    assert "nothing is promotable" in result.output


def test_a_near_miss_slug_suggests_the_record_it_resembles(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Slugs are sentences with hyphens, so the common failure is a partial one
    rather than a wrong one — and printing fifteen names when the reader typed
    fourteen of the right characters buries the answer in the remedy."""
    root = _arch_root(agent_dir, monkeypatch)
    _record(root, "promised-evidence-blocks-on-silence", "proposed")

    result = runner.invoke(app, ["arch", "accept", "promised-evidence", "--agreed", "x"])

    assert result.exit_code == 1
    assert "did you mean" in result.output
    assert "promised-evidence-blocks-on-silence" in result.output


def test_a_slug_resembling_nothing_falls_back_to_the_listing(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One `✗` per refusal.

    The first shape printed the "no record" line and then the shared no-slug
    headline underneath it, so a single mistake arrived as two failures.
    """
    root = _arch_root(agent_dir, monkeypatch)
    _record(root, "waiting", "proposed")

    result = runner.invoke(app, ["arch", "accept", "zzzz", "--agreed", "x"])

    assert result.exit_code == 1
    assert result.output.count("✗") == 1
    assert "waiting" in result.output


def test_a_multi_line_citation_is_refused_and_names_the_flag(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The module refuses this too; this is the message a person can act on.

    `_set_status`'s wording has to be true for `supersede`'s reason as well, so it
    cannot name `--agreed`. A citation pasted whole from a review thread is the
    accidental case, and it is at least as likely as the deliberate one.
    """
    root = _arch_root(agent_dir, monkeypatch)
    path = _record(root, "a-decision", "proposed")
    before = path.read_text()

    result = runner.invoke(
        app,
        ["arch", "accept", "a-decision", "--agreed", "ok\n- 2020-01-01  accepted    — forged"],
    )

    assert result.exit_code == 1
    assert "--agreed must be one line" in result.output
    assert path.read_text() == before


def test_a_record_with_no_log_section_gets_a_sentence_not_a_traceback(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The fourth failure, and the only one the write discovers rather than the guard.

    The three status refusals are chosen from `record.status`, which the command
    already holds; this one is raised by `_set_status`. Uncaught it arrived as a
    rich traceback — the one output shape that says nothing about what to do next,
    in a command whose other failures each say it in a sentence.
    """
    root = _arch_root(agent_dir, monkeypatch)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "a-decision.md"
    path.write_text("---\nstatus: proposed\n---\n\n# a-decision\n\nNo log here.\n")
    before = path.read_text()

    result = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "on #321"])

    assert result.exit_code == 1
    assert "no '## Log' section" in result.output
    assert "Traceback" not in result.output
    assert path.read_text() == before


def test_the_echoed_entry_is_the_line_that_reached_the_file(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The console was the third caller of a column nobody had named.

    It hand-wrote `accepted` and four spaces while `_set_status` formatted the
    same field from `_LOG_STATUS_WIDTH`. They agreed by coincidence, and the two
    tests that pinned them held separate literals — so nothing would have caught
    the day they stopped agreeing. Comparing the echo to the file is what does.
    """
    root = _arch_root(agent_dir, monkeypatch)
    path = _record(root, "a-decision", "proposed")

    out = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "on #321"]).output

    written = path.read_text().splitlines()[-1]
    assert written in out
