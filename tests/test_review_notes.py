"""Tests for wfctl._review_notes: the review notes wfctl writes on a commit,
the coverage CI reads from them, and sending them to `origin`."""
from __future__ import annotations

import json
import os
import subprocess
import sys
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


# --- approving imports (T046) -----------------------------------------------------
#
# `run_approve_imports` runs the default branch's copy of the import check to
# list a branch's additions, and writes the approval note once the person types
# the digest back. Each fixture puts the real script on `origin/main`.

ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = ".github/scripts/check_imports.py"
_PAGE = "docs/architecture/domain/wfctl.md"
_BASELINE = ".github/scripts/check_imports.baseline"
_REVIEW_YML = ".github/workflows/review.yml"


def _write(repo: Path, rel: str, text: str) -> None:
    (repo / rel).parent.mkdir(parents=True, exist_ok=True)
    (repo / rel).write_text(text)


@pytest.fixture
def imports_repo(repo: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """`origin/main` holds the import check, the real domain page, an empty
    baseline, and a `review.yml`. The branch `637-x` adds one baseline line
    and is pushed, so `HEAD` equals `origin/637-x`."""
    git(repo, "checkout", "-q", "main")
    _write(repo, _SCRIPT, (ROOT / _SCRIPT).read_text())
    _write(repo, _PAGE, (ROOT / _PAGE).read_text())
    _write(repo, _BASELINE, "")
    _write(repo, _REVIEW_YML, "name: Review\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "the check")
    git(repo, "push", "-q", "origin", "main")
    git(repo, "checkout", "-q", "637-x")
    git(repo, "rebase", "-q", "main")
    _write(repo, _BASELINE, "_new.py session\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "place a module")
    git(repo, "push", "-q", "-u", "origin", "637-x")
    monkeypatch.setattr(_review_notes, "_at_terminal", lambda: True)
    monkeypatch.setattr(
        _review_notes, "rerun", lambda *a, **k: _review_notes.Rerun(None, False, None),
    )
    return repo


def approve_run(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    typed: str = "",
) -> tuple[int, str]:
    monkeypatch.setattr("builtins.input", lambda prompt="": typed)
    code = _review_notes.run_approve_imports(repo)
    return code, capsys.readouterr().out


def head_note(repo: Path) -> str:
    if not git(repo, "for-each-ref", "refs/notes/wfctl-review"):
        return ""
    return subprocess.run(
        ["git", "-C", str(repo), "notes", "--ref=wfctl-review", "show", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip()


def listed_digest(repo: Path) -> str:
    done = subprocess.run(
        [sys.executable, "-I", str(repo / _SCRIPT), "--approvals", "--base",
         "origin/main", "--json"], cwd=repo, capture_output=True, text=True, check=True,
    )
    return str(json.loads(done.stdout)["digest"])


def test_approving_writes_the_digest_mains_copy_printed_and_sends_it(
    tmp_path: Path, imports_repo: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """FR-015. The digest is the one `main`'s copy computed, so CI, which runs
    the same copy, finds it. The person types only the first 12 characters,
    and the note keeps all 64. The branch's author controls both the set the
    person approves and the set CI later checks, so matching 12 characters
    takes about 2^24 hashes, and matching 64 isn't feasible."""
    digest = listed_digest(imports_repo)
    assert len(digest) == 64

    code, out = approve_run(imports_repo, monkeypatch, capsys, typed=digest[:12])

    assert code == 0, out
    assert "_new.py session" in out
    assert head_note(imports_repo) == f"imports approved {digest}"
    origin = tmp_path / "origin.git"
    assert git(origin, "notes", "--ref=wfctl-review", "show", "637-x") == (
        f"imports approved {digest}"
    )


def test_typing_anything_but_the_digest_writes_nothing(
    imports_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    code, out = approve_run(imports_repo, monkeypatch, capsys, typed="yes")

    assert code == 1
    assert "nothing written" in out
    assert head_note(imports_repo) == ""


def test_approving_refuses_without_a_terminal(
    imports_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """A second obstacle behind the guard's text match, the same one the
    person-only review command has. A pseudo-terminal satisfies it."""
    monkeypatch.setattr(_review_notes, "_at_terminal", lambda: False)

    code, out = approve_run(imports_repo, monkeypatch, capsys)

    assert code == 1
    assert "needs a person at an interactive terminal" in out


def test_the_approval_function_itself_refuses_without_a_terminal(
    imports_repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An agent calling it from a one-line script skips the command's own
    check, so the function repeats it. This narrows the gap and doesn't close
    it, as plan item 6.3.5 states."""
    monkeypatch.setattr(_review_notes, "_at_terminal", lambda: False)

    with pytest.raises(_review.ReviewError, match="interactive terminal"):
        _review_notes.approve_imports(imports_repo, "0123456789ab")
    assert head_note(imports_repo) == ""


def test_approving_refuses_when_wfctl_runs_from_a_worktree_of_this_repository(
    imports_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """Under `uv run wfctl` in a branch's worktree, the command is the
    branch's own code. The paths are compared resolved, since macOS reports
    `/tmp` and `/private/tmp` for the same folder."""
    inside = imports_repo / "wfctl"
    inside.mkdir()
    monkeypatch.setattr(_review_notes, "_wfctl_source", lambda: inside)

    code, out = approve_run(imports_repo, monkeypatch, capsys)

    assert code == 1
    assert "installed wfctl" in out


def test_approving_refuses_on_a_detached_head(
    imports_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    git(imports_repo, "checkout", "-q", "--detach")

    code, out = approve_run(imports_repo, monkeypatch, capsys)

    assert code == 1
    assert "check out the PR's branch" in out


def test_approving_refuses_a_branch_origin_doesnt_have(
    imports_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    git(imports_repo, "checkout", "-q", "-b", "637-unpushed")

    code, out = approve_run(imports_repo, monkeypatch, capsys)

    assert code == 1
    assert "push" in out and "origin/637-unpushed" in out


@pytest.mark.parametrize(("move", "says"), [("ahead", "push"), ("behind", "pull")])
def test_approving_refuses_when_head_differs_from_origin(
    imports_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    move: str, says: str,
) -> None:
    """The approval has to land on the commit CI checks, or the check stays
    red with a matching merge base and nothing on screen saying why."""
    if move == "ahead":
        commit(imports_repo, "later")
    else:
        git(imports_repo, "reset", "-q", "--hard", "HEAD~1")

    code, out = approve_run(imports_repo, monkeypatch, capsys)

    assert code == 1
    assert says in out


def test_approving_fails_when_origin_head_is_unset(
    imports_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    git(imports_repo, "symbolic-ref", "--delete", "refs/remotes/origin/HEAD")

    code, out = approve_run(imports_repo, monkeypatch, capsys)

    assert code == 1
    assert "origin/HEAD" in out


def test_approving_fails_when_the_fetch_fails(
    tmp_path: Path, imports_repo: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    git(imports_repo, "remote", "set-url", "origin", str(tmp_path / "gone.git"))

    code, out = approve_run(imports_repo, monkeypatch, capsys)

    assert code == 1
    assert "fetch" in out


def test_approving_shows_the_diff_of_a_changed_trusted_file(
    imports_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """The person reads what changed rather than a blob hash."""
    _write(imports_repo, _REVIEW_YML, "name: Review\n# loosened\n")
    git(imports_repo, "commit", "-q", "-am", "loosen")
    git(imports_repo, "push", "-q", "origin", "637-x")

    code, out = approve_run(imports_repo, monkeypatch, capsys)

    assert code == 1
    assert "+# loosened" in out


def test_approving_shows_the_diff_even_when_the_branch_marks_the_file_binary(
    imports_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """A `-diff` line in the branch's `.gitattributes` makes `git diff` print
    "Binary files differ", and changing `.gitattributes` needs no approval, so
    the person would approve a trusted file they couldn't read."""
    _write(imports_repo, ".gitattributes", "*.yml -diff\n")
    _write(imports_repo, _REVIEW_YML, "name: Review\n# weakened\n")
    git(imports_repo, "add", "-A")
    git(imports_repo, "commit", "-q", "-m", "hide")
    git(imports_repo, "push", "-q", "origin", "637-x")

    code, out = approve_run(imports_repo, monkeypatch, capsys)

    assert code == 1
    assert "+# weakened" in out and "Binary files" not in out


def test_approving_shows_control_characters_in_the_diff_instead_of_running_them(
    imports_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """The branch writes the diff the person approves. A carriage return or an
    erase-line code in a comment could redraw the screen over the real change,
    and the person would then type the code for lines they never saw."""
    _write(imports_repo, _REVIEW_YML, "name: Review\n# weakened\r\x1b[2K# harmless\n")
    git(imports_repo, "commit", "-q", "-am", "hide")
    git(imports_repo, "push", "-q", "origin", "637-x")

    code, out = approve_run(imports_repo, monkeypatch, capsys)

    assert code == 1
    assert "\x1b" not in out and "\r" not in out
    assert "+# weakened\\r\\x1b[2K# harmless" in out


def test_approving_with_no_script_on_the_trunk_says_to_merge_by_hand(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """The first baseline has nothing on the trunk to check it against, so a
    person approves it by merging its PR. The command never reads as an
    approval it didn't write."""
    git(repo, "push", "-q", "-u", "origin", "637-x")
    monkeypatch.setattr(_review_notes, "_at_terminal", lambda: True)

    code, out = approve_run(repo, monkeypatch, capsys)

    assert code == 1
    assert "merging its PR by hand" in out


@pytest.mark.parametrize("fails", ["exits", "hangs"])
def test_approving_stops_before_the_prompt_when_the_diff_fails(
    imports_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    fails: str,
) -> None:
    """A failed `git diff` prints nothing, so the person saw the file's name
    with no change under it and was still asked for the digest. Typing it out
    of habit approved a trusted file nobody read. A hung diff crashed the
    command with a traceback instead. git's stderr comes from the local
    repository, so it is escaped the same way the diff is."""
    _write(imports_repo, _REVIEW_YML, "name: Review\n# loosened\n")
    git(imports_repo, "commit", "-q", "-am", "loosen")
    git(imports_repo, "push", "-q", "origin", "637-x")
    digest = listed_digest(imports_repo)
    real = subprocess.run

    def diff_fails(cmd: list[str], *args: object, **kwargs: object) -> object:
        if cmd[:2] != ["git", "diff"]:
            return real(cmd, *args, **kwargs)  # type: ignore[call-overload]
        if fails == "hangs":
            raise subprocess.TimeoutExpired(cmd, 60)
        return subprocess.CompletedProcess(
            cmd, 128, b"", b"fatal: unable to read 1a2b\x1b[2K\n",
        )

    monkeypatch.setattr(_review_notes.subprocess, "run", diff_fails)
    asked: list[str] = []

    def answer(prompt: str = "") -> str:
        asked.append(prompt)
        return digest[:12]

    monkeypatch.setattr("builtins.input", answer)

    code = _review_notes.run_approve_imports(imports_repo)
    out = capsys.readouterr().out

    assert code == 1, out
    assert asked == []
    assert head_note(imports_repo) == ""
    assert "\x1b" not in out
    if fails == "exits":
        assert "fatal: unable to read 1a2b\\x1b[2K" in out
    else:
        assert "timed out" in out
