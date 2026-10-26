"""Tests for `wfctl review` and `wfctl relay`: output lines and exit codes.

Every line asserted here is in contracts/cli.md, since the panel skill reads
this output to launch reviewers and a person reads the roster to decide.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from tests.test_review import commit, git, report, review_repo
from wfctl.cli import app


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = review_repo(tmp_path, monkeypatch)
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("WFCTL_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.chdir(repo)
    return repo


def run(*args: str, input: str | None = None) -> Result:
    return CliRunner().invoke(app, list(args), input=input)


def runs(tmp_path: Path, group: str = "security") -> Path:
    return tmp_path / "state" / "reviews" / group / "runs"


# --- review start --------------------------------------------------------------


def test_start_prints_the_run_the_reports_path_and_one_line_per_reviewer(
    tmp_path: Path, repo: Path
) -> None:
    """The panel skill launches one reviewer per line and learns where reports
    go from the `reports:` line, so both have to be exactly this (FR-011)."""
    base = git(repo, "rev-parse", "HEAD")
    commit(repo, "a")
    head = commit(repo, "b")

    result = run("review", "start", "security")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        f"security run 001 · round 1 of 3 · 2 commits since {base[:7]} · head {head[:7]}",
        f"reports: {runs(tmp_path) / '001'}/",
        "s1 claude",
        "s2 claude",
        "s3 claude",
    ]


def start_rounds(n: int, group: str = "security") -> None:
    """Start `n` runs of `group` that never complete, so each one is a round."""
    for _ in range(n):
        assert run("review", "start", group).exit_code == 0


def sign_off(tmp_path: Path, sha: str) -> None:
    """Write the user's sign-off the way `review sign-off` does, without the
    terminal and typed sha the command asks a person for."""
    from wfctl import _review

    _review.sign_off(tmp_path / "state", sha)


def test_a_later_run_prints_its_round_of_the_cap(repo: Path) -> None:
    """The round is the runs started before this one, plus 1, so the agent sees
    how close it is to the cap from the line it already reads."""
    commit(repo, "a")
    start_rounds(1)

    result = run("review", "start", "security")

    assert result.exit_code == 0, result.output
    assert " run 002 · round 2 of 3 · " in result.output.splitlines()[0]


def test_start_at_the_cap_refuses_and_asks_the_user_to_sign_off(
    tmp_path: Path, repo: Path,
) -> None:
    """Outcome 4. The second line tells the agent whose move it is, since the
    agent shouldn't start another round or sign off itself."""
    commit(repo, "a")
    start_rounds(3)

    result = run("review", "start", "security")

    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "✗ security has run 3 of 3 rounds on this branch, the most review.rounds allows",
        "  Ask the user to run `wfctl review sign-off` in their own terminal.",
    ]
    assert sorted(p.name for p in runs(tmp_path).iterdir()) == ["001", "002", "003"]


def test_start_past_a_lowered_cap_says_more_than_the_cap_allows(
    tmp_path: Path, repo: Path,
) -> None:
    """The cap read from the trunk can be lower than a count the branch already
    reached. Read as 'run 4 of 3' it would look like a miscount."""
    commit(repo, "a")
    start_rounds(3)
    (runs(tmp_path) / "004").mkdir()
    (runs(tmp_path) / "004" / "run.json").write_text(json.dumps({"head": "x", "reviewers": []}))

    result = run("review", "start", "security")

    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "✗ security has run 4 rounds on this branch, more than the 3 review.rounds allows",
        "  Ask the user to run `wfctl review sign-off` in their own terminal.",
    ]


def test_start_at_the_cap_with_a_sign_off_says_nothing_is_left_to_review(
    tmp_path: Path, repo: Path,
) -> None:
    """Outcome 3. It exits 0 and names the signed-off commit, not the head, so
    the agent goes on to the next group instead of stopping."""
    head = commit(repo, "a")
    start_rounds(3)
    sign_off(tmp_path, head)

    result = run("review", "start", "security")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        "security has run 3 of 3 rounds; "
        f"the sign-off at {head[:7]} covers every commit left to review",
    ]
    assert sorted(p.name for p in runs(tmp_path).iterdir()) == ["001", "002", "003"]


def test_start_past_a_lowered_cap_with_a_sign_off_says_so_in_the_same_words(
    tmp_path: Path, repo: Path,
) -> None:
    head = commit(repo, "a")
    start_rounds(3)
    (runs(tmp_path) / "004").mkdir()
    (runs(tmp_path) / "004" / "run.json").write_text(json.dumps({"head": "x", "reviewers": []}))
    sign_off(tmp_path, head)

    result = run("review", "start", "security")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        "security has run 4 rounds, more than the 3 review.rounds allows; "
        f"the sign-off at {head[:7]} covers every commit left to review",
    ]


def test_start_at_the_cap_with_a_commit_after_the_sign_off_still_refuses(
    tmp_path: Path, repo: Path,
) -> None:
    signed = commit(repo, "a")
    start_rounds(3)
    sign_off(tmp_path, signed)
    commit(repo, "b")

    result = run("review", "start", "security")

    assert result.exit_code == 1
    assert result.output.splitlines()[0].startswith("✗ security has run 3 of 3 rounds")


def test_start_up_to_date_at_the_cap_is_not_refused(repo: Path) -> None:
    """The range is checked before the count, so a group that has finished its
    rounds and reviewed everything reads as up to date."""
    head = commit(repo, "a")
    start_rounds(2)
    third = run("review", "start", "security")
    reports = Path(third.output.splitlines()[1].removeprefix("reports: "))
    for rid in ("s1", "s2", "s3"):
        (reports / f"{rid}.md").write_text(report(head))
    assert run("review", "check", "security").exit_code == 0

    result = run("review", "start", "security")

    assert result.exit_code == 0
    assert result.output.splitlines() == [f"security is up to date at {head[:7]}"]


def test_start_says_one_commit_rather_than_one_commits(repo: Path) -> None:
    """A single fix commit is the commonest second run."""
    commit(repo, "a")
    result = run("review", "start", "code")
    assert " · 1 commit since " in result.output.splitlines()[0]


def test_start_prints_the_command_after_a_reviewer_on_another_model(
    tmp_path: Path, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The coordinator runs that command for the reviewer, and the line is where
    it learns which one."""
    (repo / "wfctl.json").write_text(json.dumps({"review": {
        "commands": {"codex": "codex exec --sandbox read-only"},
        "groups": [{"group": "security", "reviewers": [
            {"name": "claude", "count": 2}, {"name": "codex", "count": 2}]}],
    }}))
    monkeypatch.setattr("shutil.which", lambda name: f"/bin/{name}")
    commit(repo, "a")

    result = run("review", "start", "security")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[2:] == [
        "s1 claude",
        "s2 claude",
        "s3 codex  codex exec --sandbox read-only",
        "s4 codex  codex exec --sandbox read-only",
    ]


def test_start_with_nothing_new_says_the_group_is_up_to_date(repo: Path) -> None:
    """The coordinator reads this as "skip this group", which is right only
    when the last run covered the head."""
    head = commit(repo, "a")
    started = run("review", "start", "security")
    reports = Path(started.output.splitlines()[1].removeprefix("reports: "))
    for rid in ("s1", "s2", "s3"):
        (reports / f"{rid}.md").write_text(report(head))
    assert run("review", "check", "security").exit_code == 0

    result = run("review", "start", "security")

    assert result.exit_code == 0
    assert result.output.splitlines() == [f"security is up to date at {head[:7]}"]


def test_start_with_no_trunk_branch_names_the_trunk_key(repo: Path) -> None:
    """There's no merge base to start from, and declaring the trunk is the fix."""
    (repo / "wfctl.json").write_text(json.dumps({"trunk": "nope"}))
    commit(repo, "a")

    result = run("review", "start", "security")

    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "✗ can't find the trunk branch; set trunk in wfctl.json",
    ]


def test_start_refuses_a_trunk_that_is_the_branch_under_review(repo: Path) -> None:
    """Every commit on the branch reads as already on the trunk, so the group
    was reported up to date with nothing reviewed."""
    (repo / "wfctl.json").write_text(json.dumps({"trunk": "637-x"}))
    commit(repo, "a")

    result = run("review", "start", "security")

    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "✗ the trunk branch is 637-x, the branch under review; check trunk in wfctl.json",
    ]


def test_start_on_an_unknown_group_lists_the_groups_there_are(repo: Path) -> None:
    """A typo in a group name would otherwise start nothing and say nothing
    useful."""
    result = run("review", "start", "secruity")

    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "✗ no review group named 'secruity'",
        "  security",
        "  code",
    ]


def test_start_on_an_invalid_review_key_prints_the_check_config_findings(
    repo: Path,
) -> None:
    """A run started from half a declaration would expect a roster the
    repository never wrote."""
    (repo / "wfctl.json").write_text(json.dumps({"review": {"groups": {}}}))

    result = run("review", "start", "security")

    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "✗ wfctl.json:",
        "  - review.groups must be a list",
    ]


# --- review check --------------------------------------------------------------


def _started(repo: Path) -> tuple[Path, str]:
    head = commit(repo, "a")
    started = run("review", "start", "security")
    assert started.exit_code == 0, started.output
    return Path(started.output.splitlines()[1].removeprefix("reports: ")), head


def test_check_prints_the_roster_and_completes_when_every_report_counts(repo: Path) -> None:
    """The roster comes from wfctl's reading of the files, not from the
    coordinator's count, and `complete:` is the line that says the last
    reviewed commit moved."""
    reports, head = _started(repo)
    for rid in ("s1", "s2", "s3"):
        (reports / f"{rid}.md").write_text(report(head))

    result = run("review", "check", "security")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        f"security run 001 · head {head[:7]}",
        "s1 claude ✓",
        "s2 claude ✓",
        "s3 claude ✓",
        f"complete: security reviewed through {head[:7]}",
    ]


def test_check_names_the_reason_each_report_did_not_count(repo: Path) -> None:
    """A ✗ with no reason leaves the coordinator guessing which reviewer to
    run again and what to tell it."""
    reports, head = _started(repo)
    (reports / "s1.md").write_text("Reviewed: 5c4b3a2\n\nVerdict: Approve\n")
    (reports / "s2.md").write_text("No findings.\n\nVerdict: Approve\n")
    (reports / "s3.md").write_text(f"Reviewed: {head[:7]}\n\nNo findings.\n")

    result = run("review", "check", "security")

    assert result.exit_code == 1
    assert result.output.splitlines() == [
        f"security run 001 · head {head[:7]}",
        f"s1 claude ✗ names 5c4b3a2, not {head[:7]}",
        "s2 claude ✗ no Reviewed: line",
        "s3 claude ✗ no verdict at the end",
        "incomplete: 3 of 3 expected reports missing",
    ]


def test_check_with_a_report_missing_is_incomplete(repo: Path) -> None:
    """A reviewer that never wrote is the commonest gap, and it reads as
    `no report` rather than as nothing."""
    reports, head = _started(repo)
    for rid in ("s1", "s2"):
        (reports / f"{rid}.md").write_text(report(head))

    result = run("review", "check", "security")

    assert result.exit_code == 1
    assert result.output.splitlines()[-2:] == [
        "s3 claude ✗ no report",
        "incomplete: 1 of 3 expected reports missing",
    ]


def test_check_after_a_report_changed_on_a_complete_run_stays_complete_and_warns(
    repo: Path,
) -> None:
    """The run printed `incomplete` and exited 1 while its records still said
    complete, and the last reviewed commit had already moved."""
    reports, head = _started(repo)
    for rid in ("s1", "s2", "s3"):
        (reports / f"{rid}.md").write_text(report(head))
    assert run("review", "check", "security").exit_code == 0
    (reports / "s2.md").unlink()

    result = run("review", "check", "security")

    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[2:4] == ["s2 claude ✗ no report", "s3 claude ✓"]
    assert lines[4] == f"complete: security reviewed through {head[:7]}"
    assert re.fullmatch(r"⚠ 1 report no longer counts since the run completed at \S+Z", lines[5])


def test_check_with_no_run_says_how_to_start_one(repo: Path) -> None:
    """Nothing has been reviewed, and the fix is one command away."""
    result = run("review", "check", "security")

    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "✗ security has no run; run wfctl review start security",
    ]


def test_check_refuses_a_group_name_that_could_leave_the_reviews_folder(repo: Path) -> None:
    """The name becomes a path under `reviews/`, and `../x` would read another
    folder's records as this group's."""
    result = run("review", "check", "../x")

    assert result.exit_code == 1
    assert result.output.splitlines() == ["✗ no review group named '../x'"]


# --- relay ---------------------------------------------------------------------


def test_relay_saves_the_report_and_says_so(tmp_path: Path, repo: Path) -> None:
    """The line names the reason, which is what the roster will show too."""
    reports, head = _started(repo)
    source = tmp_path / "s2-report.md"
    source.write_text(report(head))

    result = run("relay", "s2", "--reason", "write denied", "--from", str(source))

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == ["✓ s2 relayed: write denied"]
    assert (reports / "s2.md").read_text().startswith("Relayed: write denied\n")


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_relay_without_a_reason_is_refused(
    tmp_path: Path, repo: Path, reason: str | None
) -> None:
    """A relay with no reason is a report the coordinator wrote for a reviewer,
    with nothing on the roster to show it."""
    reports, head = _started(repo)
    source = tmp_path / "r.md"
    source.write_text(report(head))
    args = ["relay", "s2", "--from", str(source)]
    if reason is not None:
        args += ["--reason", reason]

    result = run(*args)

    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "✗ a relay needs --reason saying why the reviewer couldn't write",
    ]
    assert not (reports / "s2.md").exists()


def test_relay_without_from_is_refused_and_never_reads_stdin(repo: Path) -> None:
    """A report fed on stdin is usually a heredoc, which puts the report back
    in the command's text, where the guard matches every command a security
    report quotes (research.md R8)."""
    reports, head = _started(repo)

    result = run("relay", "s2", "--reason", "write denied", input=report(head))

    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "✗ a relay needs --from naming the file that holds the report",
    ]
    assert not (reports / "s2.md").exists()


def test_relay_reads_only_the_file_even_when_stdin_holds_a_report(
    tmp_path: Path, repo: Path
) -> None:
    """The file is the report. Text on stdin is ignored rather than appended,
    so what's saved is what the coordinator put in the file."""
    reports, head = _started(repo)
    source = tmp_path / "r.md"
    source.write_text(report(head))

    result = run("relay", "s2", "--reason", "write denied", "--from", str(source),
                 input="Reviewed: 5c4b3a2\n\nVerdict: Approve\n")

    assert result.exit_code == 0, result.output
    assert "5c4b3a2" not in (reports / "s2.md").read_text()


def test_relay_of_a_file_that_does_not_exist_names_it(tmp_path: Path, repo: Path) -> None:
    """The coordinator saved the reply somewhere, and the line has to say
    where wfctl looked."""
    _started(repo)
    missing = tmp_path / "nope.md"

    result = run("relay", "s2", "--reason", "write denied", "--from", str(missing))

    assert result.exit_code == 1
    assert result.output.splitlines() == [
        f"✗ can't read {missing}: No such file or directory",
    ]


def test_relay_of_a_file_that_cannot_be_read_names_it(tmp_path: Path, repo: Path) -> None:
    """A directory passed by mistake is the commonest unreadable `--from`."""
    _started(repo)
    folder = tmp_path / "a-folder"
    folder.mkdir()

    result = run("relay", "s2", "--reason", "write denied", "--from", str(folder))

    assert result.exit_code == 1
    assert result.output.splitlines()[0].startswith(f"✗ can't read {folder}: ")


def test_relay_of_an_empty_file_is_refused(tmp_path: Path, repo: Path) -> None:
    """An empty file is a save that didn't happen, not a report."""
    reports, _ = _started(repo)
    source = tmp_path / "r.md"
    source.write_text("\n\n")

    result = run("relay", "s2", "--reason", "write denied", "--from", str(source))

    assert result.exit_code == 1
    assert result.output.splitlines() == [f"✗ {source} is empty; nothing to relay for s2"]
    assert not (reports / "s2.md").exists()


def test_relay_for_an_id_not_in_the_latest_run_is_refused(
    tmp_path: Path, repo: Path
) -> None:
    """A report under an id nobody launched would count toward nothing, and
    one under another group's letter would land in the wrong run."""
    _, head = _started(repo)
    source = tmp_path / "r.md"
    source.write_text(report(head))

    result = run("relay", "s9", "--reason", "write denied", "--from", str(source))

    assert result.exit_code == 1
    assert result.output.splitlines() == ["✗ s9 isn't a reviewer in security run 001"]


def test_relay_for_an_id_that_already_has_a_report_is_refused(
    tmp_path: Path, repo: Path
) -> None:
    """Overwriting a report the reviewer wrote would replace its findings with
    the coordinator's copy."""
    reports, head = _started(repo)
    (reports / "s2.md").write_text(report(head))
    source = tmp_path / "r.md"
    source.write_text(report(head))

    result = run("relay", "s2", "--reason", "write denied", "--from", str(source))

    assert result.exit_code == 1
    assert result.output.splitlines() == ["✗ s2 already has a report in run 001"]


# --- models that can't run -----------------------------------------------------


_MIXED = {"review": {
    "commands": {"codex": "codex exec --sandbox read-only"},
    "groups": [{"group": "security", "reviewers": [
        {"name": "claude", "count": 2}, {"name": "codex", "count": 2}]}],
}}


def test_start_marks_a_missing_model_and_says_which_reviewers_it_left_out(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The ⚠ line is how a person learns the run is smaller than the
    repository declared."""
    (repo / "wfctl.json").write_text(json.dumps(_MIXED))
    monkeypatch.setattr("shutil.which", lambda name: None)
    commit(repo, "a")

    result = run("review", "start", "security")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[2:] == [
        "s1 claude",
        "s2 claude",
        "s3 codex  ✗ unavailable",
        "s4 codex  ✗ unavailable",
        "⚠ codex: `codex` not found on PATH; s3 and s4 left out of this run",
    ]


def test_start_where_no_reviewer_can_run_warns_and_still_exits_0(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The run is written so the roster can show why it never completes, and
    start itself did what it was asked."""
    (repo / "wfctl.json").write_text(json.dumps({"review": {
        "commands": {"codex": "codex exec"},
        "groups": [{"group": "security", "reviewers": [{"name": "codex", "count": 1}]}],
    }}))
    monkeypatch.setattr("shutil.which", lambda name: None)
    commit(repo, "a")

    result = run("review", "start", "security")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[-1] == (
        "⚠ no reviewer in security can run; the run can't complete until one can, "
        "or a person signs off"
    )


def test_check_shows_the_unavailable_reason_and_completes_on_the_rest(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unavailable reviewer isn't a missing report, so it doesn't count
    against completion, and the roster still names it."""
    (repo / "wfctl.json").write_text(json.dumps(_MIXED))
    monkeypatch.setattr("shutil.which", lambda name: None)
    reports, head = _started(repo)
    for rid in ("s1", "s2"):
        (reports / f"{rid}.md").write_text(report(head))

    result = run("review", "check", "security")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[3:] == [
        "s3 codex  ✗ unavailable: `codex` not found on PATH",
        "s4 codex  ✗ unavailable: `codex` not found on PATH",
        f"complete: security reviewed through {head[:7]}",
    ]


def test_check_where_no_reviewer_could_run_says_so(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`0 of 0 expected reports missing` would read as nothing left to do."""
    (repo / "wfctl.json").write_text(json.dumps({"review": {
        "commands": {"codex": "codex exec"},
        "groups": [{"group": "security", "reviewers": [{"name": "codex", "count": 1}]}],
    }}))
    monkeypatch.setattr("shutil.which", lambda name: None)
    _started(repo)

    result = run("review", "check", "security")

    assert result.exit_code == 1
    assert result.output.splitlines()[-1] == "incomplete: no reviewer in security could run"


def test_relay_refuses_dev_stdin(repo: Path) -> None:
    """`--from /dev/stdin` with a heredoc puts the report back in the command's
    text, which is the whole reason `relay` reads a file."""
    reports, head = _started(repo)

    result = run("relay", "s2", "--reason", "write denied", "--from", "/dev/stdin",
                 input=report(head))

    assert result.exit_code == 1
    assert result.output.splitlines() == ["✗ can't read /dev/stdin: not a regular file"]
    assert not (reports / "s2.md").exists()


def test_start_pads_the_id_column_once_a_group_has_ten_reviewers(repo: Path) -> None:
    """The coordinator reads the model from the second column, and `s10`
    pushed it out of line with `s1` to `s9`."""
    (repo / "wfctl.json").write_text(json.dumps({"review": {"groups": [
        {"group": "security", "reviewers": [{"name": "claude", "count": 10}]}]}}))
    commit(repo, "a")

    lines = run("review", "start", "security").output.splitlines()

    assert lines[2] == "s1  claude"
    assert lines[11] == "s10 claude"


# --- review sign-off -----------------------------------------------------------


@pytest.fixture
def terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stand in for a person at a terminal. `CliRunner` swaps `sys.stdin` and
    `sys.stdout` for streams that are never a terminal, so the check is patched
    where the command reads it."""
    monkeypatch.setattr("wfctl.cli._at_terminal", lambda: True)


def test_sign_off_without_a_terminal_refuses(repo: Path) -> None:
    """FR-013. An agent's shell tool has no terminal, so a spelling the guard's
    pattern misses still fails here."""
    commit(repo, "a")

    result = run("review", "sign-off")

    assert result.exit_code == 1
    assert result.output == "✗ wfctl review sign-off needs a person at an interactive terminal\n"
    assert not (Path(str(repo)).parent / "state" / "reviews" / "sign-off.json").exists()


def test_sign_off_lists_the_commits_then_asks_for_the_head_sha(
    tmp_path: Path, repo: Path, terminal: None,
) -> None:
    """Typing the sha makes the person read what they're signing off. A run is
    not required first, since a sign-off doesn't wait for three rounds."""
    first = commit(repo, "a")
    head = commit(repo, "b")

    result = run("review", "sign-off", input=f"{head[:7]}\n")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        f"security  {first[:7]} a",
        f"security  {head[:7]} b",
        f"code      {first[:7]} a",
        f"code      {head[:7]} b",
        f"Type {head[:7]} to sign off on these commits: ✓ signed off through {head[:7]}",
    ]
    record = json.loads((tmp_path / "state" / "reviews" / "sign-off.json").read_text())
    assert record["sha"] == head
    events = (tmp_path / "state" / "events.jsonl").read_text()
    assert '"review-sign-off"' in events and head in events


def test_sign_off_with_anything_else_typed_writes_nothing(
    tmp_path: Path, repo: Path, terminal: None,
) -> None:
    """An `y` or a stray Enter isn't a decision about these commits."""
    commit(repo, "a")

    result = run("review", "sign-off", input="y\n")

    assert result.exit_code == 1
    assert result.output.splitlines()[-1].endswith("✗ not signed off; nothing written")
    assert not (tmp_path / "state" / "reviews" / "sign-off.json").exists()


def test_sign_off_with_nothing_unreviewed_needs_none(
    tmp_path: Path, repo: Path, terminal: None,
) -> None:
    """There is nothing to sign, so the command doesn't ask."""
    result = run("review", "sign-off")

    assert result.exit_code == 0
    assert result.output == "nothing unreviewed; no sign-off needed\n"
    assert not (tmp_path / "state" / "reviews" / "sign-off.json").exists()


# --- review groups -------------------------------------------------------------


def test_groups_lists_the_two_built_in_groups_with_no_review_key(repo: Path) -> None:
    """`opening-a-change` runs exactly these lines, in this order, so a
    repository that configures nothing still gets both groups (FR-022)."""
    result = run("review", "groups")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        "security  reviewing-security  s1 s2 s3 claude",
        "code      code-review         c1 c2 c3 claude",
    ]


def test_groups_lists_a_custom_group_after_the_built_in_ones(repo: Path) -> None:
    """FR-019. The code group reviews the security group's fixes, and a custom
    group reviews the result of both, whatever order the list gives."""
    (repo / "wfctl.json").write_text(json.dumps({"review": {
        "commands": {"codex": "codex exec"},
        "groups": [
            {"group": "money-rules", "skill": "money-rules-review",
             "reviewers": [{"name": "claude", "count": 2}]},
            {"group": "security", "reviewers": [
                {"name": "claude", "count": 1}, {"name": "codex", "count": 1}]},
        ],
    }}))

    result = run("review", "groups")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        "security     reviewing-security  s1 claude, s2 codex",
        "code         code-review         c1 c2 c3 claude",
        "money-rules  money-rules-review  m1 m2 claude",
    ]


def test_groups_with_an_invalid_review_key_prints_the_findings(repo: Path) -> None:
    """The skill reads this list to decide what runs, so a broken key stops it
    rather than running the defaults."""
    (repo / "wfctl.json").write_text(json.dumps({"review": {"groups": "security"}}))

    result = run("review", "groups")

    assert result.exit_code == 1
    assert result.output.startswith("✗ wfctl.json:\n  - ")
