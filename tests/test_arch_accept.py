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

pytestmark = pytest.mark.usefixtures("ask_rules_installed")


def _record(root: Path, slug: str, status: str, log: str = "- 2026-03-14  proposed    — x") -> Path:
    """A record with a `## Log` and a drawing, unlike `test_remaining_commands._record`.

    The transition under test appends to `## Log` and raises without one, so a
    helper that omitted it would make every test here fail for a reason none of
    them is about — and since #109, `accept` also refuses a record with no
    drawing under `## Boundary` and no declared kind, so both ship here too.
    The drawing gate itself is `test_arch_accept_drawing.py`'s own fixture.
    """
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{slug}.md"
    path.write_text(
        f"---\nstatus: {status}\ndiagram: state\n---\n\n# {slug}\n\n## Decision\n\nx\n\n"
        f"## Boundary\n\n```mermaid\nflowchart LR\n  A --> B\n```\n\n## Log\n\n{log}\n"
    )
    return path


def _arch_root(agent_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = agent_dir.parent / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    # The real accept refuses without a terminal (FR-024), and CliRunner is
    # never one. The test for that refusal patches it back.
    monkeypatch.setattr("wfctl.cli._at_terminal", lambda: True)
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


_AMENDED_LOG = (
    "- 2026-03-14  proposed    — x\n"
    "- 2026-03-15  accepted    — on #321\n"
    "- 2026-03-16  amended     — #838: the guard lets through a quoted string"
)


def test_accepting_an_amended_record_writes_a_new_accepted_line(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#838: on #407 a record was amended after acceptance, the user ran the
    accept again, and the file didn't change, so the Log showed an amendment
    nobody had agreed to. The new line is the user's agreement to it."""
    root = _arch_root(agent_dir, monkeypatch)
    path = _record(root, "a-decision", "accepted", log=_AMENDED_LOG)

    result = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "on #838"])

    assert result.exit_code == 0, result.output
    assert "a-decision: amendment accepted — on #838" in result.output
    log = path.read_text().split("## Log\n", 1)[1].strip().splitlines()
    assert log[-1].startswith("- ") and "accepted    — on #838" in log[-1]
    assert log[-2].startswith("- 2026-03-16  amended")
    assert "status: accepted\n" in path.read_text()


def test_an_amended_record_accepted_again_refuses_the_third_time(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Once the amendment is agreed to, the last Log line is `accepted`, so a
    third run has nothing new to agree to and writes nothing."""
    root = _arch_root(agent_dir, monkeypatch)
    path = _record(root, "a-decision", "accepted", log=_AMENDED_LOG)
    runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "on #838"])
    after_second = path.read_text()

    result = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "again"])

    assert result.exit_code == 1
    assert "already accepted (" in result.output
    assert path.read_text() == after_second


def test_a_bare_accept_lists_an_amended_record_as_one_it_could_accept(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The slug form accepts an amended record, but the listing a bare accept
    prints read only `proposed`, so it said nothing was promotable while the
    amendment waited. Found by Codex on #846."""
    root = _arch_root(agent_dir, monkeypatch)
    _record(root, "a-decision", "accepted", log=_AMENDED_LOG)

    result = runner.invoke(app, ["arch", "accept"])

    assert result.exit_code == 1
    assert "nothing is promotable" not in result.output
    assert "a-decision" in result.output


def test_the_dry_run_on_an_amended_record_says_the_amendment_would_be_accepted(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The dry run walks the same path as the write, so it names the same
    outcome and leaves the file as it was."""
    root = _arch_root(agent_dir, monkeypatch)
    path = _record(root, "a-decision", "accepted", log=_AMENDED_LOG)
    before = path.read_text()

    result = runner.invoke(app, ["arch", "check-accept", "a-decision"])

    assert result.exit_code == 0, result.output
    assert "amendment would be accepted" in result.output
    assert path.read_text() == before


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


def test_a_proposed_record_with_no_log_section_is_not_listed_as_promotable(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The listing's own suggested command must not fail.

    A record was `proposed` and appeared under "Proposed, and promotable" with
    no `## Log` section — its own suggested `wfctl arch accept <slug> --agreed`
    then raised. Found by Codex reviewing this diff.
    """
    root = _arch_root(agent_dir, monkeypatch)
    root.mkdir(parents=True, exist_ok=True)
    (root / "malformed.md").write_text("---\nstatus: proposed\n---\n\n# malformed\n\nNo log.\n")
    _record(root, "well-formed", "proposed")

    result = runner.invoke(app, ["arch", "accept"])

    assert "malformed" not in result.output
    assert "well-formed" in result.output


@pytest.mark.parametrize("dry_run", [False, True])
def test_accept_without_a_terminal_refuses_before_writing(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch, dry_run: bool
) -> None:
    """The guard reads the command's text, so any alternative invocation it
    doesn't recognize, such as a shell alias, would let an agent sign off a
    drawing nobody looked at. The terminal check catches those. A dry run
    writes nothing, so it still runs anywhere (FR-024)."""
    root = _arch_root(agent_dir, monkeypatch)
    monkeypatch.setattr("wfctl.cli._at_terminal", lambda: False)
    path = _record(root, "a-decision", "proposed")
    before = path.read_text()

    args = ["arch", "accept", "a-decision", "--agreed", "on #321"]
    result = runner.invoke(app, [*args, "--dry-run"] if dry_run else args)

    if dry_run:
        assert result.exit_code == 0, result.output
    else:
        assert result.exit_code == 1
        assert "✗ wfctl arch accept needs a person at an interactive terminal" in result.output
    assert path.read_text() == before


# --- the host's prompt (#833) ------------------------------------------------------


def _no_terminal(monkeypatch: pytest.MonkeyPatch, claudecode: str | None) -> None:
    monkeypatch.setattr("wfctl.cli._at_terminal", lambda: False)
    if claudecode is None:
        monkeypatch.delenv("CLAUDECODE", raising=False)
    else:
        monkeypatch.setenv("CLAUDECODE", claudecode)


@pytest.mark.parametrize(("args", "line"), [
    (["--agreed", "on #833"], "accepted    — on #833"),
    ([], "accepted    — approved at the permission prompt"),
    (["--agreed", ""], "accepted    — approved at the permission prompt"),
    (["--agreed", "   "], "accepted    — approved at the permission prompt"),
])
def test_with_no_terminal_under_claude_code_the_accept_writes_its_log_line(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch, args: list[str], line: str,
) -> None:
    """Claude Code asked the user before the command ran, and that yes is the
    agreement, so the citation is optional. With none, the Log line claims
    only what wfctl saw, and a blank one says nothing, so it counts as none."""
    root = _arch_root(agent_dir, monkeypatch)
    _no_terminal(monkeypatch, "1")
    path = _record(root, "a-decision", "proposed")

    result = runner.invoke(app, ["arch", "accept", "a-decision", *args])

    assert result.exit_code == 0, result.output
    assert line in path.read_text()
    assert line in result.output


def test_at_a_terminal_the_citation_is_still_required(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """At a terminal nobody saw a prompt, so nothing but the citation records
    where the person agreed, even with `CLAUDECODE` set in that shell."""
    root = _arch_root(agent_dir, monkeypatch)
    monkeypatch.setenv("CLAUDECODE", "1")
    path = _record(root, "a-decision", "proposed")
    before = path.read_text()

    result = runner.invoke(app, ["arch", "accept", "a-decision"])

    assert result.exit_code == 1
    assert "--agreed is required" in result.output
    assert path.read_text() == before


@pytest.mark.parametrize("env", [{}, {"WFCTL_AGENT": "claude"}])
def test_with_no_terminal_and_no_claude_code_the_accept_still_refuses(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch, env: dict[str, str],
) -> None:
    """A host wfctl doesn't support runs no guard and shows no prompt. The
    user's profile sets `WFCTL_AGENT` in every shell, their own terminal
    included, so it says nothing about whether a prompt appeared."""
    root = _arch_root(agent_dir, monkeypatch)
    _no_terminal(monkeypatch, None)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    path = _record(root, "a-decision", "proposed")
    before = path.read_text()

    result = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "on #833"])

    assert result.exit_code == 1
    assert "needs a person at an interactive terminal" in result.output
    assert "wfctl arch check-accept" in result.output
    assert path.read_text() == before
