"""Tests for wfctl._review: commit ranges, run records, reports, and relays."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from wfctl import _review
from wfctl._review_config import Group, Reviewer


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True,
    ).stdout.strip()


def commit(repo: Path, name: str) -> str:
    """Commit one new file named `name`, and return the commit's full sha."""
    (repo / name).write_text(f"{name}\n")
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", name)
    return git(repo, "rev-parse", "HEAD")


def review_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A clone on branch `637-x`, one commit past `main`, with a bare `origin`
    whose HEAD names `main`.

    `origin/HEAD` is set by hand because a clone of an empty bare repository
    doesn't record it, and `trunk_branch` reads it first. `-b main` is explicit
    since CI sets `init.defaultBranch master`.
    """
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    repo = tmp_path / "work"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    for key, val in (("user.email", "test@test.com"), ("user.name", "Test")):
        git(repo, "config", key, val)
    commit(repo, "init")
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "-q", "-u", "origin", "main")
    git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    git(repo, "checkout", "-q", "-b", "637-x")
    for name in ("WFCTL_BRANCH", "WFCTL_STATE_DIR", "WFCTL_REPO_ROOT", "WFCTL_SPEC_DIR"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg"))
    return repo


def push_to_main(tmp_path: Path, repo: Path, name: str) -> str:
    """Land a commit on `origin/main` from a second clone, and fetch it.

    The local `main` stays where it was, which is the stale trunk a person's
    checkout usually has.
    """
    other = tmp_path / f"other-{name}"
    subprocess.run(["git", "clone", "-q", str(tmp_path / "origin.git"), str(other)], check=True)
    for key, val in (("user.email", "test@test.com"), ("user.name", "Test")):
        git(other, "config", key, val)
    sha = commit(other, name)
    git(other, "push", "-q", "origin", "main")
    git(repo, "fetch", "-q", "origin")
    return sha


def report(head: str, *, verdict: str = "Verdict: Approve") -> str:
    return f"Reviewed: {head[:7]}\n\nNo findings.\n\n{verdict}\n"


SECURITY = Group(
    "security", "reviewing-security",
    tuple(Reviewer(f"s{i}", "claude", None) for i in (1, 2, 3)),
)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    return review_repo(tmp_path, monkeypatch)


@pytest.fixture
def state(tmp_path: Path) -> Path:
    d = tmp_path / "state"
    d.mkdir()
    return d


def complete(repo: Path, state: Path, group: Group = SECURITY) -> _review.Started:
    """Start a run of `group` and write a counted report for every reviewer."""
    started = _review.start(repo, state, group)
    assert started.run is not None
    for r in started.expected:
        (started.run.path / f"{r}.md").write_text(report(started.head))
    assert _review.check(state, group.name).complete
    return started


# --- range ---------------------------------------------------------------------


def test_range_of_a_first_run_starts_where_the_branch_left_main(repo: Path) -> None:
    """With no review on record, every commit the branch added is unreviewed,
    and nothing that was already on `main` is (FR-007)."""
    first = commit(repo, "a")
    second = commit(repo, "b")

    found = _review.commit_range(repo, second, None)

    assert found.base == git(repo, "merge-base", "HEAD", "origin/main")
    assert found.commits == (second, first)


def test_range_of_a_later_run_starts_after_the_last_reviewed_commit(repo: Path) -> None:
    """A review covers what came after the last one, so a fix commit isn't read
    alongside the whole branch again."""
    reviewed = commit(repo, "a")
    fix = commit(repo, "fix")

    found = _review.commit_range(repo, fix, reviewed)

    assert found.base == reviewed
    assert found.commits == (fix,)


def test_range_after_a_rebase_falls_back_to_the_merge_base(repo: Path) -> None:
    """A rebase leaves the last reviewed commit off the branch. Starting there
    would list commits from a history the branch no longer has, so the next
    review covers the whole branch instead."""
    reviewed = commit(repo, "a")
    git(repo, "reset", "-q", "--hard", "main")
    rewritten = commit(repo, "a-rewritten")

    found = _review.commit_range(repo, rewritten, reviewed)

    assert found.base == git(repo, "merge-base", "HEAD", "origin/main")
    assert found.commits == (rewritten,)


def test_range_leaves_out_commits_and_the_merge_that_came_in_from_main(
    tmp_path: Path, repo: Path
) -> None:
    """Merging `main` brings in commits the branch didn't write, and a merge
    commit nobody needs to review. Counting either would force a review round
    after every merge (US2 scenario 4)."""
    reviewed = commit(repo, "a")
    from_main = push_to_main(tmp_path, repo, "m1")
    git(repo, "merge", "-q", "--no-edit", "origin/main")
    merge = git(repo, "rev-parse", "HEAD")
    own = commit(repo, "b")

    found = _review.commit_range(repo, own, reviewed)

    assert found.commits == (own,)
    assert from_main not in found.commits
    assert merge not in found.commits


def test_range_reads_origin_main_so_a_stale_local_main_hides_nothing(
    tmp_path: Path, repo: Path
) -> None:
    """A person's local `main` usually trails `origin/main`. Excluding only
    the local branch would list everything merged since as the branch's own
    work."""
    reviewed = commit(repo, "a")
    from_main = push_to_main(tmp_path, repo, "m1")
    git(repo, "merge", "-q", "--no-edit", "origin/main")
    own = commit(repo, "b")

    assert _review.trunk_refs(repo) == ["origin/main", "main"]
    assert git(repo, "rev-parse", "main") != git(repo, "rev-parse", "origin/main")
    found = _review.commit_range(repo, own, reviewed)
    assert from_main not in found.commits
    assert found.commits == (own,)


def test_trunk_refs_leave_out_a_local_branch_that_does_not_exist(repo: Path) -> None:
    """`--not main` with no `main` is a git error, which would read as the
    whole range failing."""
    git(repo, "branch", "-q", "-D", "main")
    assert _review.trunk_refs(repo) == ["origin/main"]


def test_range_is_empty_at_or_behind_the_last_reviewed_commit(repo: Path) -> None:
    """Reviewed commits that aren't pushed yet put the head GitHub knows behind
    the last reviewed commit. Every ancestor of a reviewed commit was covered,
    so falling back to the merge base there would list the whole branch as
    unreviewed (R3 item 3)."""
    older = commit(repo, "a")
    reviewed = commit(repo, "b")

    assert _review.commit_range(repo, reviewed, reviewed).commits == ()
    assert _review.commit_range(repo, older, reviewed).commits == ()


def test_range_with_no_trunk_branch_names_the_trunk_key(repo: Path) -> None:
    """Without a trunk there is no merge base to start a first review from, and
    the person can fix that only by declaring one."""
    (repo / "wfctl.json").write_text(json.dumps({"trunk": "nope"}))
    head = commit(repo, "a")

    with pytest.raises(_review.NoTrunk) as raised:
        _review.commit_range(repo, head, None)
    assert str(raised.value) == "can't find the trunk branch; set trunk in wfctl.json"


def test_range_restarts_at_the_merge_base_when_the_state_dir_is_empty(
    tmp_path: Path, repo: Path, state: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Losing the state directory costs one larger review and lets nothing
    through, which is why the records can live outside the repository
    (`622-review-records-in-state-dir.md`, Verification)."""
    commit(repo, "a")
    complete(repo, state)
    head = commit(repo, "b")
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setenv("WFCTL_STATE_DIR", str(empty))
    from wfctl._paths import resolve_agent_dir

    started = _review.start(repo, resolve_agent_dir(repo, "637-x"), SECURITY)

    assert started.base == git(repo, "merge-base", "HEAD", "origin/main")
    assert started.commits[0] == head
    assert len(started.commits) == 2


def test_every_git_call_in_the_range_takes_the_callers_timeout(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The guard will call these with a 5-second bound, before every Bash call
    that names a PR command. One unbounded call is a hook that can hang the
    agent's shell."""
    reviewed = commit(repo, "a")
    head = commit(repo, "b")
    real = subprocess.run
    seen: list[object] = []

    def recording(args: list[str], **kwargs: object) -> object:
        if args and args[0] == "git":
            seen.append(kwargs.get("timeout"))
        return real(args, **kwargs)  # type: ignore[call-overload]

    monkeypatch.setattr(subprocess, "run", recording)
    _review.commit_range(repo, head, reviewed, timeout=5)
    _review.commit_range(repo, head, "0" * 40, timeout=5)

    assert seen
    assert set(seen) == {5}


# --- reports -------------------------------------------------------------------


HEAD = "9f8e7d6c5b4a39281706f5e4d3c2b1a098765432"


@pytest.mark.parametrize("sha", [HEAD[:7], HEAD[:12], HEAD])
def test_report_counts_with_seven_or_more_digits_of_the_head(sha: str) -> None:
    """Seven digits is what `git log --oneline` prints, so it's what a reviewer
    copies."""
    assert _review.judge(f"Reviewed: {sha}\n\nVerdict: Approve\n", HEAD) is None


def test_report_with_a_shorter_prefix_does_not_count() -> None:
    """Six digits can match more than one commit in a large repository, so a
    report naming one hasn't said which it read."""
    assert _review.judge(f"Reviewed: {HEAD[:6]}\n\nVerdict: Approve\n", HEAD) == (
        f"names {HEAD[:6]}, not {HEAD[:7]}"
    )


def test_report_naming_another_commit_says_which_it_named() -> None:
    """A reviewer that read an older head reviewed code the branch no longer
    has, and the roster has to say so to be acted on (FR-008)."""
    assert _review.judge("Reviewed: 5c4b3a2\n\nVerdict: Approve\n", HEAD) == (
        f"names 5c4b3a2, not {HEAD[:7]}"
    )


def test_report_with_no_reviewed_line_does_not_count() -> None:
    """Without the line there's no telling which commit the reviewer read."""
    assert _review.judge("No findings.\n\nVerdict: Approve\n", HEAD) == "no Reviewed: line"


@pytest.mark.parametrize(
    "ending",
    [
        "Verdict: Approve",
        "**Verdict: Approve**",
        "## Verdict\n\nApprove",
        "### Verdict\nApprove",
        "Verdict: Request changes",
        "## Verdict\n\nRequest changes",
    ],
)
def test_report_counts_with_each_verdict_spelling_reviewers_use(ending: str) -> None:
    """These are the spellings the panels in this project's spec root wrote,
    pinned today by `test_the_verdict_anchor_accepts_every_spelling_reviewers_use`.
    A check keyed on `^Verdict:` alone takes about half of them."""
    text = f"Reviewed: {HEAD[:7]}\n\nBLOCKER cli.py:L1 - x\n\n{ending}\n\n"
    assert _review.judge(text, HEAD) is None


def test_report_cut_off_after_an_early_verdict_does_not_count() -> None:
    """A report the reviewer never finished carries no verdict at its end, even
    when it mentioned one on the way."""
    text = (
        f"Reviewed: {HEAD[:7]}\n\nVerdict: Approve so far\n\n"
        "BLOCKER cli.py:L1 - the rest of this finding was lost\n"
    )
    assert _review.judge(text, HEAD) == "no verdict at the end"


def test_prose_that_mentions_a_verdict_is_not_one() -> None:
    """The anchor allows decoration before the word, never other words."""
    text = f"Reviewed: {HEAD[:7]}\n\nThe Verdict stands, and I Approve of it.\n"
    assert _review.judge(text, HEAD) == "no verdict at the end"


def test_report_is_read_whole_so_a_late_reviewed_line_counts() -> None:
    """The panel skill used to read the first lines of a report. A reviewer
    that puts the line after its findings still names the commit it read."""
    findings = "".join(f"NIT x.py:L{i} - y\n" for i in range(200))
    text = f"{findings}\nReviewed: {HEAD[:7]}\n\nVerdict: Approve\n"
    assert _review.judge(text, HEAD) is None


# --- runs ----------------------------------------------------------------------


def test_start_writes_the_run_record(repo: Path, state: Path) -> None:
    """The run record is what makes a review checkable: the reviewers it
    expects and the commits they read, fixed when the run starts (FR-005)."""
    first = commit(repo, "a")
    second = commit(repo, "b")
    codex = "codex exec --sandbox read-only"
    group = Group("security", "reviewing-security", (
        Reviewer("s1", "claude", None), Reviewer("s2", "codex", codex),
    ))

    started = _review.start(repo, state, group, which=lambda _: "/bin/codex")

    path = state / "reviews" / "security" / "runs" / "001" / "run.json"
    assert started.run is not None and started.run.path == path.parent
    record = json.loads(path.read_text())
    assert record == {
        "group": "security",
        "run": 1,
        "base": git(repo, "merge-base", "HEAD", "origin/main"),
        "head": second,
        "commits": [second, first],
        "reviewers": [
            {"id": "s1", "model": "claude", "state": "expected"},
            {"id": "s2", "model": "codex", "state": "expected", "command": codex},
        ],
        "started_at": record["started_at"],
        "completed_at": None,
    }
    assert record["started_at"].endswith("Z")


def test_runs_are_numbered_in_start_order(repo: Path, state: Path) -> None:
    """A run that never completes is kept for reading, so the next one needs
    its own folder."""
    commit(repo, "a")
    numbers = [_review.start(repo, state, SECURITY).run for _ in range(3)]
    assert [r.number for r in numbers if r] == [1, 2, 3]
    assert sorted(p.name for p in (state / "reviews/security/runs").iterdir()) == [
        "001", "002", "003",
    ]


def test_start_with_nothing_unreviewed_writes_nothing(repo: Path, state: Path) -> None:
    """An empty run can't be reviewed, and a run record for one would read as a
    review that's waiting on reports."""
    commit(repo, "a")
    complete(repo, state)

    started = _review.start(repo, state, SECURITY)

    assert started.run is None
    assert started.commits == ()
    assert sorted(p.name for p in (state / "reviews/security/runs").iterdir()) == ["001"]


def test_check_completes_a_run_only_when_every_reviewer_reported(
    repo: Path, state: Path
) -> None:
    """Completion moves the last reviewed commit, which is what later decides
    whether a PR can open. Only wfctl's own reading of the reports moves it
    (SC-002)."""
    commit(repo, "a")
    started = _review.start(repo, state, SECURITY)
    assert started.run is not None
    before = (started.run.path / "run.json").read_text()

    for r in started.expected:
        (started.run.path / f"{r}.md").write_text(report(started.head))
    checked = _review.check(state, "security")

    assert checked.complete
    after = json.loads((started.run.path / "run.json").read_text())
    assert after["completed_at"].endswith("Z")
    assert {**after, "completed_at": None} == json.loads(before)
    last = json.loads((state / "reviews/security/last-reviewed.json").read_text())
    assert last == {"sha": started.head, "run": 1, "at": last["at"]}


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        pytest.param(None, "no report", id="missing"),
        pytest.param("Reviewed: {head}\n\nNo findings.\n", "no verdict at the end",
                     id="no-verdict"),
        pytest.param("Reviewed: 5c4b3a2\n\nVerdict: Approve\n", "names 5c4b3a2, not {head}",
                     id="another-commit"),
    ],
)
def test_one_uncounted_report_leaves_the_run_incomplete(
    repo: Path, state: Path, text: str | None, reason: str
) -> None:
    """Each is a way a panel reported a review as done when it wasn't: a
    reviewer that never wrote, one cut off, and one that read the wrong
    commit."""
    commit(repo, "a")
    started = _review.start(repo, state, SECURITY)
    assert started.run is not None
    head = started.head[:7]
    for r in ("s1", "s2"):
        (started.run.path / f"{r}.md").write_text(report(started.head))
    if text is not None:
        (started.run.path / "s3.md").write_text(text.format(head=head))

    checked = _review.check(state, "security")

    assert not checked.complete
    assert checked.missing == 1
    assert [e.note for e in checked.entries if not e.counted] == [reason.format(head=head)]
    assert json.loads((started.run.path / "run.json").read_text())["completed_at"] is None
    assert not (state / "reviews/security/last-reviewed.json").exists()


def test_a_config_change_after_start_does_not_change_who_is_expected(
    repo: Path, state: Path
) -> None:
    """`check` reads the reviewers from the run record. Reading the config
    again would let a repository drop a reviewer whose report was bad and
    complete the run without it."""
    (repo / "wfctl.json").write_text(json.dumps({"review": {"groups": [
        {"group": "security", "reviewers": [{"name": "claude", "count": 1}]},
    ]}}))
    commit(repo, "a")
    started = _review.start(repo, state, SECURITY)
    assert started.run is not None
    (started.run.path / "s1.md").write_text(report(started.head))

    checked = _review.check(state, "security")

    assert [e.id for e in checked.entries] == ["s1", "s2", "s3"]
    assert not checked.complete


def test_a_new_start_after_an_incomplete_run_opens_the_next_from_the_same_base(
    repo: Path, state: Path
) -> None:
    """Reports belong to the run they were written for. Counting run 1's
    reports toward run 2 would let a panel complete with reviewers from two
    different rounds."""
    commit(repo, "a")
    first = _review.start(repo, state, SECURITY)
    assert first.run is not None
    for r in ("s1", "s2", "s3"):
        (first.run.path / f"{r}.md").write_text(report(first.head))

    second = _review.start(repo, state, SECURITY)

    assert second.run is not None and second.run.number == 2
    assert second.base == first.base
    checked = _review.check(state, "security")
    assert checked.run.number == 2
    assert not checked.complete
    assert [e.note for e in checked.entries] == ["no report"] * 3


def test_a_commit_added_while_reviewers_read_leaves_the_run_incomplete(
    repo: Path, state: Path
) -> None:
    """Reviewers name the head they were given, and a commit added after start
    is one none of them read. The run's head is the one the reports have to
    name, and the next run covers the new commit."""
    commit(repo, "a")
    started = _review.start(repo, state, SECURITY)
    assert started.run is not None
    later = commit(repo, "b")
    for r in started.expected:
        (started.run.path / f"{r}.md").write_text(report(later))

    checked = _review.check(state, "security")

    assert not checked.complete
    assert {e.note for e in checked.entries} == {f"names {later[:7]}, not {started.head[:7]}"}


def test_start_and_check_append_their_events(repo: Path, state: Path) -> None:
    """`events.jsonl` is the only trace of a review a restarted session can
    read, and the counts in it say how many reviewers a run expected."""
    commit(repo, "a")
    started = complete(repo, state)

    events = [json.loads(line) for line in (state / "events.jsonl").read_text().splitlines()]
    assert [{k: v for k, v in e.items() if k != "ts"} for e in events] == [
        {"event": "review-start", "group": "security", "run": 1, "head": started.head,
         "reviewers": 3},
        {"event": "review-complete", "group": "security", "run": 1, "head": started.head},
    ]


def test_checking_a_complete_run_again_changes_nothing(repo: Path, state: Path) -> None:
    """`check` is safe to run twice. A second completion would rewrite the time
    the run finished and log a second event for one review."""
    commit(repo, "a")
    started = complete(repo, state)
    assert started.run is not None
    record = (started.run.path / "run.json").read_text()
    last = (state / "reviews/security/last-reviewed.json").read_text()

    assert _review.check(state, "security").complete

    assert (started.run.path / "run.json").read_text() == record
    assert (state / "reviews/security/last-reviewed.json").read_text() == last
    assert len((state / "events.jsonl").read_text().splitlines()) == 2


def test_check_with_no_run_raises_naming_the_group(state: Path) -> None:
    """There is nothing to judge, and the fix is to start one."""
    with pytest.raises(_review.NoRun):
        _review.check(state, "security")


def test_a_half_written_last_reviewed_file_is_an_error_naming_it(
    repo: Path, state: Path
) -> None:
    """Treating an unreadable record as missing would start the range at the
    merge base and look like a reset, and the guard will refuse on it."""
    commit(repo, "a")
    path = state / "reviews" / "security" / "last-reviewed.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"sha": "9f8e')

    with pytest.raises(_review.ReviewError) as raised:
        _review.start(repo, state, SECURITY)
    assert str(path) in str(raised.value)


def test_the_review_modules_load_neither_typer_nor_rich() -> None:
    """The worktree guard imports both modules on a matched command, before
    every Bash call that names one, and `typer` and `rich` cost about 74 ms
    there between them (`_hook.py`'s docstring)."""
    import sys

    probe = (
        "import sys, wfctl._review, wfctl._review_config; "
        "print(sorted(m for m in ('typer', 'rich') if m in sys.modules))"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], check=True, capture_output=True, text=True,
    ).stdout.strip()
    assert out == "[]"
