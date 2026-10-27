"""Tests for wfctl._review_notes: the review notes wfctl writes on a commit,
the coverage CI reads from them, and sending them to `origin`."""
from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path

import pytest

from tests.test_review import CODE, SECURITY, commit, complete, git, push_to_main, review_repo
from wfctl import _review, _review_config, _review_notes
from wfctl._review_config import Group, Reviewer


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    return review_repo(tmp_path, monkeypatch)


@pytest.fixture
def state(tmp_path: Path) -> Path:
    d = tmp_path / "state"
    d.mkdir()
    return d


def note(repo: Path, sha: str, *lines: str) -> None:
    """Append lines to a commit's note by hand, the way another machine's
    wfctl would have."""
    for line in lines:
        git(repo, "notes", "--ref=wfctl-review", "append", "-m", line, sha)


def notes_coverage(
    repo: Path, head: str, groups: list[Group],
) -> tuple[dict[str, str | None], tuple[str, ...]]:
    return _review_notes.coverage_from_notes(repo, head, groups)


# --- reading coverage from the notes ---------------------------------------------


def test_a_groups_last_reviewed_commit_is_its_nearest_noted_ancestor(repo: Path) -> None:
    """A run starts where the last one ended, so the nearest note covers every
    branch commit before it (R1)."""
    older = commit(repo, "a")
    note(repo, older, "reviewed by security")
    newer = commit(repo, "b")
    note(repo, newer, "reviewed by security", "reviewed by code")
    head = commit(repo, "c")

    assert notes_coverage(repo, head, [SECURITY, CODE]) == (
        {"security": newer, "code": newer}, (),
    )


def test_a_line_wfctl_does_not_recognize_is_skipped(repo: Path) -> None:
    """An older or newer wfctl may write a line this one can't use, and an
    error would fail every PR that carried one (`627-review-note-line-per-event.md`)."""
    head = commit(repo, "a")
    note(repo, head, "reviewed by security, run 003", "", "  reviewed by code  ")

    assert notes_coverage(repo, head, [SECURITY, CODE]) == (
        {"security": None, "code": head}, (),
    )


def test_a_line_for_a_group_no_list_names_is_ignored(repo: Path) -> None:
    """A note left by a group the repository later dropped says nothing about
    the groups CI requires now."""
    head = commit(repo, "a")
    note(repo, head, "reviewed by money-rules")

    assert notes_coverage(repo, head, [SECURITY]) == ({"security": None}, ())


def test_every_commit_with_a_sign_off_line_is_returned(repo: Path) -> None:
    """Each sign-off is a person's decision about the commits under it, and
    the notes keep all of them where the state directory keeps one."""
    first = commit(repo, "a")
    note(repo, first, "signed off by a person")
    second = commit(repo, "b")
    note(repo, second, "signed off by a person")

    assert set(notes_coverage(repo, second, [SECURITY])[1]) == {first, second}


def test_notes_on_trunk_commits_are_never_read(tmp_path: Path, repo: Path) -> None:
    """Commits on `main` carry notes from their own PRs. Picking one as this
    branch's last reviewed commit would make the two readers disagree (R3)."""
    on_main = push_to_main(tmp_path, repo, "m")
    git(repo, "fetch", "-q", "origin")
    note(repo, on_main, "reviewed by security", "signed off by a person")
    git(repo, "merge", "-q", "--no-edit", "origin/main")
    head = commit(repo, "a")

    assert notes_coverage(repo, head, [SECURITY]) == ({"security": None}, ())


def test_a_note_git_cannot_read_is_an_error_naming_the_commit(repo: Path) -> None:
    """`git log --notes` reads a note whose content is missing as empty, which
    hides the problem. The check names the commit instead, so a person knows
    which note to fix."""
    head = commit(repo, "a")
    note(repo, head, "reviewed by security")
    blob = git(repo, "notes", "--ref=wfctl-review", "list", head)
    (repo / ".git" / "objects" / blob[:2] / blob[2:]).unlink()

    with pytest.raises(_review.ReviewError, match=f"can't read the note on {head[:7]}"):
        notes_coverage(repo, head, [SECURITY])


def test_a_repository_with_no_notes_has_no_coverage(repo: Path) -> None:
    head = commit(repo, "a")

    assert notes_coverage(repo, head, [SECURITY, CODE]) == (
        {"security": None, "code": None}, (),
    )


# --- the two readers agree (SC-004) ----------------------------------------------


MONEY = Group("money-rules", "code-review", (Reviewer("m1", "claude", None),))


def test_both_readers_give_unreviewed_the_same_coverage(
    tmp_path: Path, repo: Path, state: Path,
) -> None:
    """The guard reads the state directory and CI reads the notes. If they
    disagree, a PR passes locally and fails in CI, or the other way round
    (`627-unreviewed-takes-coverage.md`).

    The trunk lists `money-rules` and the branch's committed `wfctl.json`
    removes it, so both readers must still count it."""
    money = {"group": "money-rules", "reviewers": [{"name": "claude", "count": 1}]}
    push_to_main(tmp_path, repo, "wfctl.json", json.dumps({"review": {"groups": [money]}}))
    git(repo, "merge", "-q", "--no-edit", "origin/main")
    git(repo, "rm", "-q", "wfctl.json")
    git(repo, "commit", "-q", "-m", "drop money-rules")

    commit(repo, "a")
    reviewed = complete(repo, state, SECURITY).head
    note(repo, reviewed, "reviewed by security")
    complete(repo, state, MONEY)
    note(repo, reviewed, "reviewed by money-rules")
    signed = commit(repo, "b")
    _review.sign_off(state, signed)
    note(repo, signed, "signed off by a person")
    head = commit(repo, "c")

    groups, problems = _review_config.required_at(repo, head, "refs/remotes/origin/main")
    assert problems == []
    assert [g.name for g in groups] == ["security", "code", "money-rules"]

    from_state = _review.coverage_from_state(state, groups)
    from_notes = notes_coverage(repo, head, groups)

    assert from_state == from_notes
    found = _review.unreviewed(repo, groups, head, *from_notes)
    assert found == _review.unreviewed(repo, groups, head, *from_state)
    assert found == {"security": (head,), "code": (head,), "money-rules": (head,)}


# --- recording a line -----------------------------------------------------------


def note_text(repo: Path, sha: str) -> str:
    return git(repo, "notes", "--ref=wfctl-review", "show", sha)


def test_record_creates_a_note_holding_the_line(repo: Path) -> None:
    head = commit(repo, "a")

    assert _review_notes.record(repo, head, "reviewed by security")
    assert note_text(repo, head) == "reviewed by security"


def test_record_appends_a_second_groups_line_to_the_same_note(repo: Path) -> None:
    """Git keeps one note per commit, so a second group completing on the same
    head has to add to the note rather than replace it."""
    head = commit(repo, "a")
    _review_notes.record(repo, head, "reviewed by security")
    _review_notes.record(repo, head, "reviewed by code")

    assert note_text(repo, head).splitlines() == ["reviewed by security", "reviewed by code"]


def test_record_skips_a_line_the_note_already_holds(repo: Path) -> None:
    """`review check` on a run that's already complete records again, and
    `git notes append` would add a second copy every time (R6)."""
    head = commit(repo, "a")
    _review_notes.record(repo, head, "reviewed by security")

    assert not _review_notes.record(repo, head, "reviewed by security")
    assert note_text(repo, head) == "reviewed by security"


# --- sending to origin -----------------------------------------------------------


def test_send_pushes_the_notes_ref_to_origin(tmp_path: Path, repo: Path, state: Path) -> None:
    head = commit(repo, "a")
    _review_notes.record(repo, head, "reviewed by security")

    assert _review_notes.send(repo, state, "637-x") == "sent"

    origin = tmp_path / "origin.git"
    assert git(origin, "notes", "--ref=wfctl-review", "show", head) == "reviewed by security"


def test_send_with_no_origin_raises_naming_it(repo: Path, state: Path) -> None:
    head = commit(repo, "a")
    _review_notes.record(repo, head, "reviewed by security")
    git(repo, "remote", "remove", "origin")

    with pytest.raises(_review_notes.NoOrigin, match="no origin remote to send review notes to"):
        _review_notes.send(repo, state, "637-x")


def test_each_push_is_recorded_as_an_outward_action(repo: Path, state: Path) -> None:
    """The event log is the only trace of a push a restarted session can
    read, and recording it lifts a hold a refused push filed."""
    head = commit(repo, "a")
    _review_notes.record(repo, head, "reviewed by security")

    _review_notes.send(repo, state, "637-x")

    events = [json.loads(line) for line in (state / "events.jsonl").read_text().splitlines()]
    assert {"event": "notify-action", "branch": "637-x", "action": "store-reviews"}.items() <= (
        events[-1].items()
    )


# --- rerunning the failed review job ---------------------------------------------


_GH = """\
#!{python}
import json, os, sys
table = json.load(open(os.environ["GH_STUB"]))
with open(os.environ["GH_STUB"] + ".calls", "a") as log:
    log.write(json.dumps(sys.argv[1:]) + "\\n")
args = sys.argv[1:]
for prefix, answer in table.items():
    if " ".join(args).startswith(prefix):
        print(answer.get("out", ""), end="")
        print(answer.get("err", ""), end="", file=sys.stderr)
        sys.exit(answer.get("code", 0))
print("unknown command", file=sys.stderr)
sys.exit(1)
"""

RUN_LINK = "https://github.com/acme/widgets/actions/runs/111/job/222"


@pytest.fixture
def gh(tmp_path: Path, repo: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[..., Path]:
    """Put a `gh` on PATH that answers from a table keyed by the start of its
    arguments, and point `origin` at GitHub."""
    import sys

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "gh"
    stub.write_text(_GH.format(python=sys.executable))
    stub.chmod(0o755)
    table = tmp_path / "gh.json"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("GH_STUB", str(table))
    git(repo, "remote", "set-url", "origin", "https://github.com/acme/widgets.git")

    def answer(**answers: dict[str, object]) -> Path:
        table.write_text(json.dumps({k.replace("_", " "): v for k, v in answers.items()}))
        return table

    return answer


def calls(table: Path) -> list[list[str]]:
    log = Path(f"{table}.calls")
    return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


def pr_open(number: int = 651) -> dict[str, object]:
    return {"out": json.dumps({"number": number, "state": "OPEN"})}


def checks(*found: dict[str, str], code: int = 0) -> dict[str, object]:
    return {"out": json.dumps(list(found)), "code": code}


def test_rerun_reruns_a_failed_review_check_by_its_run_and_job(
    repo: Path, gh: Callable[..., Path],
) -> None:
    """Pushing a notes ref doesn't start a CI run, so the job that failed for
    want of the note has to be rerun. `--job` leaves any other failed job
    alone (R8). `gh pr checks` exits 1 when a check failed, and that's an
    answer."""
    table = gh(
        pr_view=pr_open(),
        pr_checks=checks(
            {"name": "test (3.11)", "state": "FAILURE", "link": RUN_LINK.replace("222", "9")},
            {"name": "review", "state": "FAILURE", "link": RUN_LINK},
            code=1,
        ),
        run_rerun={},
    )

    assert _review_notes.rerun(repo, "637-x") == _review_notes.Rerun(651, True, None)
    assert calls(table)[-1] == ["run", "rerun", "111", "--job", "222"]


@pytest.mark.parametrize("case", ["no-pr", "closed", "no-check", "passed"])
def test_rerun_does_nothing_when_there_is_no_failed_review_check(
    repo: Path, gh: Callable[..., Path], case: str,
) -> None:
    view = {"err": "no pull requests found for branch \"637-x\"", "code": 1}
    found = [{"name": "review", "state": "FAILURE", "link": RUN_LINK}]
    if case == "closed":
        view = {"out": json.dumps({"number": 651, "state": "CLOSED"})}
    elif case != "no-pr":
        view = pr_open()
        found = [] if case == "no-check" else [
            {"name": "review", "state": "SUCCESS", "link": RUN_LINK},
        ]
    table = gh(pr_view=view, pr_checks=checks(*found))

    result = _review_notes.rerun(repo, "637-x")

    assert not result.reran and result.error is None
    assert not any(c[:2] == ["run", "rerun"] for c in calls(table))


def test_rerun_without_gh_or_off_github_does_nothing(
    repo: Path, gh: Callable[..., Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    """There's no check to rerun there, so saying anything would be noise on
    every review in a repository that isn't on GitHub."""
    table = gh(pr_view=pr_open())
    git(repo, "remote", "set-url", "origin", "git@gitlab.com:acme/widgets.git")
    assert _review_notes.rerun(repo, "637-x") == _review_notes.Rerun(None, False, None)
    assert calls(table) == []

    git(repo, "remote", "set-url", "origin", "git@github.com:acme/widgets.git")
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert _review_notes.rerun(repo, "637-x") == _review_notes.Rerun(None, False, None)


def test_rerun_that_fails_returns_gh_s_message_and_is_not_retried(
    repo: Path, gh: Callable[..., Path],
) -> None:
    """wfctl doesn't make up for a GitHub error. The user reruns the check, so
    the message is what they need, and a retry loop would only delay it."""
    table = gh(
        pr_view=pr_open(),
        pr_checks=checks({"name": "review", "state": "FAILURE", "link": RUN_LINK}, code=1),
        run_rerun={"err": "HTTP 403: Resource not accessible", "code": 1},
    )

    result = _review_notes.rerun(repo, "637-x")

    assert result == _review_notes.Rerun(651, False, "HTTP 403: Resource not accessible")
    assert sum(1 for c in calls(table) if c[:2] == ["run", "rerun"]) == 1


# --- a push origin rejects (US4) -------------------------------------------------


def second_clone(tmp_path: Path) -> Path:
    import subprocess

    other = tmp_path / "second"
    subprocess.run(["git", "clone", "-q", str(tmp_path / "origin.git"), str(other)], check=True)
    for key, val in (("user.email", "test@test.com"), ("user.name", "Test")):
        git(other, "config", key, val)
    return other


def test_a_rejected_push_joins_origins_notes_and_sends_them(
    tmp_path: Path, repo: Path, state: Path,
) -> None:
    """Two machines that each record a review on the same commit both push
    the notes ref, and the second is rejected. `cat_sort_uniq` keeps every
    line from both, so neither review is lost (R7)."""
    head = commit(repo, "a")
    git(repo, "push", "-q", "origin", "637-x")
    other = second_clone(tmp_path)
    git(other, "fetch", "-q", "origin", "637-x")
    _review_notes.record(other, head, "reviewed by code")
    _review_notes.send(other, state, "637-x")
    _review_notes.record(repo, head, "reviewed by security")

    assert _review_notes.send(repo, state, "637-x") == "joined"

    origin = tmp_path / "origin.git"
    assert git(origin, "notes", "--ref=wfctl-review", "show", head).splitlines() == [
        "reviewed by code", "reviewed by security",
    ]
    assert git(repo, "for-each-ref", "refs/notes/wfctl-review-remote") == ""


def test_a_second_rejection_raises_with_gits_message(
    tmp_path: Path, repo: Path, state: Path,
) -> None:
    """One retry is enough for one user. A remote that refuses twice is
    refusing for a reason a loop wouldn't change."""
    hook = tmp_path / "origin.git" / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\necho 'notes are frozen' >&2\nexit 1\n")
    hook.chmod(0o755)
    head = commit(repo, "a")
    _review_notes.record(repo, head, "reviewed by security")

    with pytest.raises(_review.ReviewError, match="notes are frozen"):
        _review_notes.send(repo, state, "637-x")


def test_unsent_compares_the_local_notes_with_origins(repo: Path, state: Path) -> None:
    head = commit(repo, "a")
    assert not _review_notes.unsent(repo)

    _review_notes.record(repo, head, "reviewed by security")
    assert _review_notes.unsent(repo)

    _review_notes.send(repo, state, "637-x")
    assert not _review_notes.unsent(repo)
