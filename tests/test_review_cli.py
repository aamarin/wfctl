"""Tests for `wfctl review` and `wfctl relay`: output lines and exit codes.

Every line asserted here is in contracts/cli.md, since the panel skill reads
this output to launch reviewers and a person reads the roster to decide.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from tests.test_review import commit, git, push_to_main, report, review_repo
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
        f"security run 001 · 2 commits since {base[:7]} · head {head[:7]}",
        f"reports: {runs(tmp_path) / '001'}/",
        "s1 claude",
        "s2 claude",
        "s3 claude",
    ]


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
        "✓ sent review notes to origin",
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
        "✓ sent review notes to origin",
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
        "✓ sent review notes to origin",
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


def test_sign_off_that_cannot_say_what_ci_would_count_refuses(
    tmp_path: Path, repo: Path, terminal: None,
) -> None:
    """A trunk the working tree declares and `origin` lacks hides its commits
    from the local list, and CI, which measures against `origin/main`, reads
    the sign-off note as covering them. So the sign-off stops before asking,
    rather than covering commits the person was never shown."""
    git(repo, "checkout", "-q", "-b", "x", "main")
    commit(repo, "hidden")
    git(repo, "checkout", "-q", "-B", "637-x", "x")
    commit(repo, "a")
    (repo / "wfctl.json").write_text(json.dumps({"trunk": "x"}))

    result = run("review", "sign-off")

    assert result.exit_code == 1, result.output
    assert result.output.splitlines() == ["✗ origin/x doesn't exist"]
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


# --- which groups the local commands use (FR-010, FR-010a) -----------------------


MONEY = {"group": "money-rules", "skill": "money-rules-review",
         "reviewers": [{"name": "claude", "count": 2}]}


def trunk_lists(tmp_path: Path, repo: Path, *groups: dict[str, object]) -> None:
    """Land a `wfctl.json` listing `groups` on `origin/main`. The branch never
    merges it, so its own committed file lists none of them."""
    push_to_main(tmp_path, repo, "wfctl.json", json.dumps({"review": {"groups": list(groups)}}))


def test_start_runs_a_group_the_branch_removed_with_the_trunks_reviewers(
    tmp_path: Path, repo: Path,
) -> None:
    """CI still requires a group the branch dropped, so the branch has to be
    able to run it. Its skill and reviewers come from the trunk's file, the
    only one that still lists it."""
    trunk_lists(tmp_path, repo, MONEY)
    commit(repo, "a")

    result = run("review", "start", "money-rules")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[2:] == ["m1 claude", "m2 claude"]


def test_groups_lists_a_group_the_branch_removed(tmp_path: Path, repo: Path) -> None:
    trunk_lists(tmp_path, repo, MONEY)

    result = run("review", "groups")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[-1] == "money-rules  money-rules-review  m1 m2 claude"


def test_start_runs_a_group_only_the_working_tree_lists(repo: Path) -> None:
    """A user tries a new group before committing it. Nothing requires it
    yet, but `review start` takes its reviewers from the working tree."""
    (repo / "wfctl.json").write_text(json.dumps({"review": {"groups": [
        {"group": "audit", "reviewers": [{"name": "claude", "count": 1}]},
    ]}}))
    commit(repo, "a")

    result = run("review", "start", "audit")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[2:] == ["a1 claude"]


def test_start_on_a_group_no_list_names_is_refused(tmp_path: Path, repo: Path) -> None:
    trunk_lists(tmp_path, repo, MONEY)

    result = run("review", "start", "nope")

    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "✗ no review group named 'nope'", "  security", "  code", "  money-rules",
    ]


def test_sign_off_lists_a_group_the_branch_removed(
    tmp_path: Path, repo: Path, terminal: None,
) -> None:
    """A sign-off that skipped the trunk's group would write a sign-off the
    guard accepts and CI rejects for the same commits."""
    trunk_lists(tmp_path, repo, MONEY)
    head = commit(repo, "a")

    result = run("review", "sign-off", input="no\n")

    assert f"money-rules  {head[:7]} a" in result.output.splitlines()


def test_relay_refuses_an_id_two_groups_share_and_names_the_one_to_rename(
    tmp_path: Path, repo: Path,
) -> None:
    """A group renamed on the branch leaves the trunk's old name required, so
    both use `m1`, `m2`, and a relay can't tell which run the report belongs
    to. The trunk still needs its group, so the branch's is the one to rename
    (FR-010a)."""
    trunk_lists(tmp_path, repo, MONEY)
    (repo / "wfctl.json").write_text(json.dumps({"review": {"groups": [
        {"group": "money", "reviewers": [{"name": "claude", "count": 2}]},
    ]}}))
    source = tmp_path / "r.md"
    source.write_text(report(commit(repo, "a")))

    result = run("relay", "m2", "--reason", "write denied", "--from", str(source))

    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "✗ reviewer m2 matches two groups, money-rules and money.",
        "  main still requires money-rules, so rename money in wfctl.json to start with a "
        "different letter.",
    ]


# --- review notes (US2) ----------------------------------------------------------


def note_on(repo: Path, sha: str) -> str | None:
    """The commit's review note, or None when it has none."""
    import subprocess

    shown = subprocess.run(
        ["git", "-C", str(repo), "notes", "--ref=wfctl-review", "show", sha],
        capture_output=True, text=True,
    )
    return shown.stdout.strip() if shown.returncode == 0 else None


def complete_security(repo: Path) -> str:
    reports, head = _started(repo)
    for rid in ("s1", "s2", "s3"):
        (reports / f"{rid}.md").write_text(report(head))
    return head


def lock_notes(repo: Path) -> Path:
    """Hold the lock on the notes ref, as another worktree's write would."""
    lock = repo / ".git" / "refs" / "notes" / "wfctl-review.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text("")
    return lock


def test_check_records_a_completed_run_on_its_head_and_sends_it(
    tmp_path: Path, repo: Path,
) -> None:
    """CI reads the notes on `origin`, so a run that completes only in the
    state directory leaves the PR failing (FR-001, FR-005)."""
    head = complete_security(repo)

    result = run("review", "check", "security")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[-2:] == [
        f"complete: security reviewed through {head[:7]}",
        "✓ sent review notes to origin",
    ]
    assert note_on(repo, head) == "reviewed by security"
    assert note_on(tmp_path / "origin.git", head) == "reviewed by security"
    reviewed = tmp_path / "state" / "reviews" / "security" / "last-reviewed.json"
    assert json.loads(reviewed.read_text())["sha"] == head


def test_check_on_an_incomplete_run_records_nothing(repo: Path) -> None:
    _, head = _started(repo)

    assert run("review", "check", "security").exit_code == 1
    assert note_on(repo, head) is None


def test_check_whose_push_fails_warns_and_exits_0(tmp_path: Path, repo: Path) -> None:
    """The run is complete and the note is saved here, so the review itself
    succeeded. `store reviews` is how the note reaches `origin` later."""
    head = complete_security(repo)
    git(repo, "remote", "set-url", "origin", str(tmp_path / "nowhere.git"))

    result = run("review", "check", "security")

    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[-2].startswith("⚠ couldn't send review notes: ")
    assert lines[-1] == "  The note is saved here. Run `wfctl store reviews` to send it."
    assert note_on(repo, head) == "reviewed by security"


def test_check_whose_note_write_fails_warns_and_records_it_next_time(repo: Path) -> None:
    """Another worktree can hold the lock on the notes ref. The run is still
    complete in the state directory, and the next check records the note,
    since recording skips a line that's already there (R6)."""
    head = complete_security(repo)
    lock = lock_notes(repo)

    result = run("review", "check", "security")

    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[-2].startswith("⚠ couldn't write the review note: ")
    assert lines[-1] == "  Run `wfctl review check security` again to record it."
    assert note_on(repo, head) is None

    lock.unlink()
    assert run("review", "check", "security").exit_code == 0
    assert note_on(repo, head) == "reviewed by security"


def test_check_records_the_note_whatever_the_trunks_config_says(
    tmp_path: Path, repo: Path,
) -> None:
    """A broken `review` key on the trunk fails every PR, and the fix is a PR
    whose own reviews must still be recorded (PR-024). `review check` reads
    no group list, so the run's own record is all it needs."""
    head = complete_security(repo)
    push_to_main(tmp_path, repo, "wfctl.json", json.dumps({"review": []}))

    assert run("review", "check", "security").exit_code == 0
    assert note_on(repo, head) == "reviewed by security"


def test_check_with_no_trunk_to_find_completes_and_writes_no_note(repo: Path) -> None:
    """CI's range can't be recomputed without the trunk on `origin`, and a
    note written anyway covers whatever commits CI finds under it. The run is
    still complete, since its reviewers all reported."""
    head = complete_security(repo)
    (repo / "wfctl.json").write_text(json.dumps({"trunk": "nope"}))

    result = run("review", "check", "security")

    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[-3] == f"complete: security reviewed through {head[:7]}"
    assert lines[-2].startswith("⚠ didn't write the review note: ")
    assert lines[-1] == "  Fix that and run `wfctl review check security` again to record it."
    assert note_on(repo, head) is None


def test_check_writes_no_note_over_a_commit_only_the_local_trunk_has(
    tmp_path: Path, repo: Path,
) -> None:
    """A run leaves out commits on the local `main`, and CI, which sees only
    `origin/main`, reads the note on the head as covering them. A branch cut
    from a `main` with an unpushed commit would pass CI with that commit
    unreviewed."""
    git(repo, "checkout", "-q", "main")
    unpushed = commit(repo, "unpushed")
    git(repo, "checkout", "-q", "-B", "637-x")
    head = complete_security(repo)

    result = run("review", "check", "security")

    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[-2] == (
        f"⚠ didn't write the review note: CI would count 1 commit no security run "
        f"reviewed: {unpushed[:7]}"
    )
    assert lines[-1] == (
        "  It isn't on origin/main. If origin/main is out of date, run git fetch and "
        "`wfctl review check security` again. Otherwise a person has to sign off on it "
        "with `wfctl review sign-off`."
    )
    assert note_on(repo, head) is None


def test_sign_off_lists_a_commit_only_the_local_trunk_has_and_unblocks_the_note(
    repo: Path, terminal: None,
) -> None:
    """`review check` points at a sign-off for a commit no run listed, and the
    local check finds nothing pending on a complete run. So the sign-off
    lists the commit itself. Otherwise the person signs off on commits they
    were never shown, or finds nothing to sign and the PR stays failing."""
    git(repo, "checkout", "-q", "main")
    unpushed = commit(repo, "unpushed")
    git(repo, "checkout", "-q", "-B", "637-x")
    head = complete_security(repo)
    assert run("review", "check", "security").exit_code == 0

    result = run("review", "sign-off", input=f"{head[:7]}\n")

    assert result.exit_code == 0, result.output
    assert f"security  {unpushed[:7]} unpushed" in result.output.splitlines()
    assert note_on(repo, head) == "signed off by a person"
    assert run("review", "check", "security").exit_code == 0
    assert note_on(repo, head) == "signed off by a person\nreviewed by security"


def test_check_counts_commits_an_earlier_run_reviewed_whose_note_was_not_written(
    repo: Path,
) -> None:
    """With no note on the first run's head, CI counts the second run's note
    from the merge base, so the first run's commits are in the range it
    reads. They were reviewed, and refusing them would leave a sign-off as
    the only way back."""
    first = complete_security(repo)
    lock = lock_notes(repo)
    assert run("review", "check", "security").exit_code == 0
    lock.unlink()
    assert note_on(repo, first) is None

    second = commit(repo, "b")
    started = run("review", "start", "security")
    reports = Path(started.output.splitlines()[1].removeprefix("reports: "))
    for rid in ("s1", "s2", "s3"):
        (reports / f"{rid}.md").write_text(report(second))

    assert run("review", "check", "security").exit_code == 0
    assert note_on(repo, second) == "reviewed by security"


def test_check_records_a_group_no_list_names_any_more(repo: Path) -> None:
    """A run started before its group was removed is still a review someone
    ran, and its note is harmless: CI ignores a line for a group it doesn't
    require."""
    (repo / "wfctl.json").write_text(json.dumps({"review": {"groups": [
        {"group": "audit", "reviewers": [{"name": "claude", "count": 1}]},
    ]}}))
    head = commit(repo, "a")
    started = run("review", "start", "audit")
    reports = Path(started.output.splitlines()[1].removeprefix("reports: "))
    (reports / "a1.md").write_text(report(head))
    (repo / "wfctl.json").unlink()

    assert run("review", "check", "audit").exit_code == 0
    assert note_on(repo, head) == "reviewed by audit"


def test_sign_off_records_and_sends_a_note_on_the_head(
    tmp_path: Path, repo: Path, terminal: None,
) -> None:
    head = commit(repo, "a")

    result = run("review", "sign-off", input=f"{head[:7]}\n")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[-1] == "✓ sent review notes to origin"
    assert note_on(repo, head) == "signed off by a person"
    assert note_on(tmp_path / "origin.git", head) == "signed off by a person"


def test_sign_off_whose_push_fails_names_store_reviews(
    tmp_path: Path, repo: Path, terminal: None,
) -> None:
    head = commit(repo, "a")
    git(repo, "remote", "set-url", "origin", str(tmp_path / "nowhere.git"))

    result = run("review", "sign-off", input=f"{head[:7]}\n")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[-1] == (
        "  The note is saved here. Run `wfctl store reviews` to send it."
    )


def test_sign_off_whose_note_write_fails_says_to_sign_off_again(
    repo: Path, terminal: None,
) -> None:
    """The sign-off is in the state directory, so the guard allows the PR,
    but CI reads only the note. Signing off again is how it gets written."""
    head = commit(repo, "a")
    lock_notes(repo)

    result = run("review", "sign-off", input=f"{head[:7]}\n")

    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[-2].startswith("⚠ couldn't write the review note: ")
    assert lines[-1] == "  Run `wfctl review sign-off` again to record it."


def test_signing_off_again_records_a_note_the_first_sign_off_missed(
    tmp_path: Path, repo: Path, terminal: None,
) -> None:
    """With the head signed off, nothing is unreviewed, and the old command
    stopped there. A note whose write failed would then never be written
    (PR-009)."""
    head = commit(repo, "a")
    lock = lock_notes(repo)
    run("review", "sign-off", input=f"{head[:7]}\n")
    lock.unlink()

    result = run("review", "sign-off")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        f"✓ recorded the sign-off through {head[:7]} as a review note",
        "✓ sent review notes to origin",
    ]
    assert note_on(tmp_path / "origin.git", head) == "signed off by a person"


def test_signing_off_again_with_the_note_written_needs_nothing(
    tmp_path: Path, repo: Path, terminal: None,
) -> None:
    head = commit(repo, "a")
    run("review", "sign-off", input=f"{head[:7]}\n")

    result = run("review", "sign-off")

    assert result.output == "nothing unreviewed; no sign-off needed\n"


# --- check reviews (US1) ---------------------------------------------------------


PASS = "✓ Every commit on this PR has been reviewed."
CLOSING = "  Run the review panel. If you already did, run `wfctl store reviews`."


def noted(repo: Path, sha: str, *lines: str) -> None:
    for line in lines:
        git(repo, "notes", "--ref=wfctl-review", "append", "--no-separator", "-m", line, sha)


def test_check_reviews_passes_when_both_groups_noted_the_head(repo: Path) -> None:
    commit(repo, "a")
    head = commit(repo, "b")
    noted(repo, head, "reviewed by security", "reviewed by code")

    result = run("check", "reviews", "--base", "main")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [PASS]


def test_check_reviews_lists_one_unreviewed_commit_with_its_groups(repo: Path) -> None:
    head = commit(repo, "fix: drop the stale ref")

    result = run("check", "reviews", "--base", "main")

    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "✗ 1 commit hasn't been reviewed:",
        f"    {head[:7]} fix: drop the stale ref   (security, code)",
        CLOSING,
    ]


def test_check_reviews_lists_each_commit_once_oldest_first(repo: Path) -> None:
    """A commit two groups owe is one line naming both, so the count matches
    what a person has to review, not the number of group and commit pairs."""
    first = commit(repo, "test: cover an empty note")
    noted(repo, first, "reviewed by code")
    second = commit(repo, "fix: drop the stale ref")

    result = run("check", "reviews", "--base", "main")

    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "✗ 2 commits haven't been reviewed:",
        f"    {first[:7]} test: cover an empty note   (security)",
        f"    {second[:7]} fix: drop the stale ref     (security, code)",
        CLOSING,
    ]


def test_check_reviews_ignores_an_uncommitted_config_edit(repo: Path) -> None:
    """CI reads the committed files, so a local run that read the working
    tree could pass here and fail there (FR-015)."""
    head = commit(repo, "a")
    noted(repo, head, "reviewed by security", "reviewed by code")
    (repo / "wfctl.json").write_text(json.dumps({"review": {"groups": [
        {"group": "audit", "reviewers": [{"name": "claude", "count": 1}]},
    ]}}))

    assert run("check", "reviews", "--base", "main").output.splitlines() == [PASS]


def test_a_clean_merge_of_main_on_a_reviewed_branch_needs_no_review(
    tmp_path: Path, repo: Path,
) -> None:
    """GitHub's "Update branch" makes a merge no local machine made. It
    changes nothing the branch wrote, so it mustn't fail the check (SC-003)."""
    head = commit(repo, "a")
    noted(repo, head, "reviewed by security", "reviewed by code")
    push_to_main(tmp_path, repo, "m")
    git(repo, "merge", "-q", "--no-edit", "origin/main")

    assert run("check", "reviews", "--base", "main").output.splitlines() == [PASS]


def test_check_reviews_ignores_a_trunk_key_naming_the_branch_itself(repo: Path) -> None:
    """A PR that names its own branch as trunk would read every commit as
    already on the trunk. CI passes the PR's real base, and that wins
    (FR-015a)."""
    git(repo, "push", "-q", "origin", "637-x")
    (repo / "wfctl.json").write_text(json.dumps({"trunk": "637-x"}))
    git(repo, "add", "wfctl.json")
    git(repo, "commit", "-q", "-m", "trunk")
    head = git(repo, "rev-parse", "HEAD")

    result = run("check", "reviews", "--base", "main")

    assert result.exit_code == 1
    assert f"    {head[:7]} trunk   (security, code)" in result.output.splitlines()


def test_check_reviews_requires_a_group_the_pr_adds_and_one_it_removes(
    tmp_path: Path, repo: Path,
) -> None:
    """A group the PR adds runs on that PR, and a group it drops still owes
    its review there, or a PR could skip a review by removing its group
    (R13)."""
    push_to_main(tmp_path, repo, "wfctl.json", json.dumps({"review": {"groups": [MONEY]}}))
    first = commit(repo, "a")
    (repo / "wfctl.json").write_text(json.dumps({"review": {"groups": [
        {"group": "audit", "reviewers": [{"name": "claude", "count": 1}]},
    ]}}))
    git(repo, "add", "wfctl.json")
    git(repo, "commit", "-q", "-m", "add audit")
    head = git(repo, "rev-parse", "HEAD")
    noted(repo, head, "reviewed by security", "reviewed by code")

    result = run("check", "reviews", "--base", "main")

    assert result.exit_code == 1
    assert result.output.splitlines()[1:3] == [
        f"    {first[:7]} a           (money-rules, audit)",
        f"    {head[:7]} add audit   (money-rules, audit)",
    ]


def cause(result: Result) -> str:
    assert result.exit_code == 1, result.output
    (line,) = result.output.splitlines()
    assert line.startswith("✗ can't check reviews: "), line
    return line.removeprefix("✗ can't check reviews: ")


def test_check_reviews_names_a_shallow_clone(
    tmp_path: Path, repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    commit(repo, "a")
    git(repo, "push", "-q", "origin", "637-x")
    shallow = tmp_path / "shallow"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", "--no-single-branch",
         f"file://{tmp_path / 'origin.git'}", str(shallow)],
        check=True,
    )
    git(shallow, "checkout", "-q", "637-x")
    monkeypatch.chdir(shallow)

    assert "shallow" in cause(run("check", "reviews", "--base", "main"))


def test_check_reviews_names_a_missing_trunk(repo: Path) -> None:
    """Without `--base`, the check finds the trunk the way the guard does."""
    commit(repo, "a")
    (repo / "wfctl.json").write_text(json.dumps({"trunk": "nope"}))

    assert cause(run("check", "reviews")) == (
        "can't find the trunk branch; set trunk in wfctl.json"
    )


def test_check_reviews_names_a_base_branch_origin_lacks(repo: Path) -> None:
    commit(repo, "a")

    assert cause(run("check", "reviews", "--base", "develop")) == "origin/develop doesn't exist"


def test_check_reviews_refuses_a_base_that_is_the_branch_under_review(repo: Path) -> None:
    commit(repo, "a")
    git(repo, "push", "-q", "origin", "637-x")

    assert cause(run("check", "reviews", "--base", "637-x")) == (
        "the trunk branch is 637-x, the branch under review"
    )


def test_check_reviews_names_the_commit_whose_note_it_cannot_read(repo: Path) -> None:
    head = commit(repo, "a")
    noted(repo, head, "reviewed by security")
    blob = git(repo, "notes", "--ref=wfctl-review", "list", head)
    (repo / ".git" / "objects" / blob[:2] / blob[2:]).unlink()

    assert cause(run("check", "reviews", "--base", "main")).startswith(
        f"can't read the note on {head[:7]}: "
    )


def test_check_reviews_names_a_broken_review_key_and_its_side(
    tmp_path: Path, repo: Path,
) -> None:
    """A broken trunk config fails every PR. Falling back to the defaults
    would drop a custom group's requirement with nobody noticing (R13)."""
    push_to_main(tmp_path, repo, "wfctl.json", json.dumps({"review": []}))
    commit(repo, "a")

    assert cause(run("check", "reviews", "--base", "main")) == (
        "wfctl.json at origin/main: review must be an object"
    )


# --- store reviews (US4) ---------------------------------------------------------


def recorded(repo: Path) -> str:
    """A commit with a review note on it that hasn't been sent."""
    head = commit(repo, "a")
    noted(repo, head, "reviewed by security")
    return head


def test_store_reviews_sends_the_notes(tmp_path: Path, repo: Path) -> None:
    head = recorded(repo)

    result = run("store", "reviews")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == ["✓ sent review notes to origin"]
    assert note_on(tmp_path / "origin.git", head) == "reviewed by security"


def test_store_reviews_joins_origins_notes_after_a_rejected_push(
    tmp_path: Path, repo: Path,
) -> None:
    head = recorded(repo)
    git(repo, "push", "-q", "origin", "637-x")
    other = tmp_path / "second"
    subprocess.run(["git", "clone", "-q", str(tmp_path / "origin.git"), str(other)], check=True)
    git(other, "fetch", "-q", "origin", "637-x")
    noted(other, head, "reviewed by code")
    git(other, "push", "-q", "origin", "refs/notes/wfctl-review")

    result = run("store", "reviews")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        "✓ joined origin's review notes with this machine's and sent them",
    ]
    assert note_on(tmp_path / "origin.git", head) == "reviewed by code\nreviewed by security"


@pytest.mark.parametrize("sent", [True, False])
def test_store_reviews_with_nothing_new_says_so(repo: Path, sent: bool) -> None:
    """Once the push worked there's nothing left to send, and saying so is
    the whole answer when no PR has a failed check to rerun."""
    if sent:
        recorded(repo)
        assert run("store", "reviews").exit_code == 0

    result = run("store", "reviews")

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == ["✓ nothing to send; origin has every review note"]


def test_store_reviews_with_nothing_to_send_still_reruns_the_failed_check(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CI failure says to run `store reviews`. When the notes reached
    `origin` while that check was running, there's nothing to send, and the
    check stays failing until something reruns it."""
    from wfctl import _review_notes

    monkeypatch.setattr(
        _review_notes, "rerun", lambda root, branch: _review_notes.Rerun(651, True, None),
    )
    recorded(repo)
    assert run("store", "reviews").exit_code == 0

    result = run("store", "reviews")

    assert result.output.splitlines() == [
        "✓ nothing to send; origin has every review note",
        "↻ reran the failed review check on PR #651",
    ]


def test_store_reviews_with_no_origin_names_it(repo: Path) -> None:
    recorded(repo)
    git(repo, "remote", "remove", "origin")

    result = run("store", "reviews")

    assert result.exit_code == 1
    assert result.output.splitlines() == ["✗ no origin remote to send review notes to"]


def test_store_reviews_refused_twice_exits_1_with_gits_message(
    tmp_path: Path, repo: Path,
) -> None:
    hook = tmp_path / "origin.git" / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\necho 'notes are frozen' >&2\nexit 1\n")
    hook.chmod(0o755)
    recorded(repo)

    result = run("store", "reviews")

    assert result.exit_code == 1
    assert result.output.startswith("✗ couldn't send review notes: ")
    assert "notes are frozen" in result.output


def test_store_reviews_reruns_the_failed_check_after_sending(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`rerun` is tested against a stubbed `gh` in test_review_notes.py. Here
    the line it adds is the point."""
    from wfctl import _review_notes

    monkeypatch.setattr(
        _review_notes, "rerun", lambda root, branch: _review_notes.Rerun(651, True, None),
    )
    recorded(repo)

    result = run("store", "reviews")

    assert result.output.splitlines() == [
        "✓ sent review notes to origin",
        "↻ reran the failed review check on PR #651",
    ]
