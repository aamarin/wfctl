"""Tests for wfctl._review: commit ranges, run records, reports, and relays."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

from wfctl import _review
from wfctl._review_config import Group, Reviewer


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True,
    ).stdout.strip()


def commit(repo: Path, name: str, text: str | None = None) -> str:
    """Commit the file `name`, holding `text` or its own name, and return the
    commit's full sha."""
    (repo / name).write_text(text if text is not None else f"{name}\n")
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


def push_to_main(tmp_path: Path, repo: Path, name: str, text: str | None = None) -> str:
    """Land a commit on `origin/main` from a second clone, and fetch it.

    The local `main` stays where it was, which is the stale trunk a person's
    checkout usually has.
    """
    other = tmp_path / f"other-{len(list(tmp_path.glob('other-*')))}"
    subprocess.run(["git", "clone", "-q", str(tmp_path / "origin.git"), str(other)], check=True)
    for key, val in (("user.email", "test@test.com"), ("user.name", "Test")):
        git(other, "config", key, val)
    sha = commit(other, name, text)
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
    started = _review.start(repo, state, group, cap=9)
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

    assert _review.trunk_refs(repo) == ["refs/remotes/origin/main", "refs/heads/main"]
    assert git(repo, "rev-parse", "main") != git(repo, "rev-parse", "origin/main")
    found = _review.commit_range(repo, own, reviewed)
    assert from_main not in found.commits
    assert found.commits == (own,)


def test_trunk_refs_leave_out_a_local_branch_that_does_not_exist(repo: Path) -> None:
    """`--not main` with no `main` is a git error, which would read as the
    whole range failing."""
    git(repo, "branch", "-q", "-D", "main")
    assert _review.trunk_refs(repo) == ["refs/remotes/origin/main"]


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

    started = _review.start(repo, resolve_agent_dir(repo, "637-x"), SECURITY, cap=9)

    assert started.base == git(repo, "merge-base", "HEAD", "origin/main")
    assert started.commits[0] == head
    assert len(started.commits) == 2


def test_every_git_call_in_the_range_takes_the_callers_timeout(
    tmp_path: Path, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The guard will call these with a 5-second bound, before every Bash call
    that names a PR command. One unbounded call is a hook that can hang the
    agent's shell. The merge from `main` is there so the calls that judge a
    merge are recorded too."""
    reviewed = commit(repo, "a")
    push_to_main(tmp_path, repo, "m1")
    git(repo, "merge", "-q", "--no-edit", "origin/main")
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


def test_range_works_beside_a_path_named_after_the_trunk(repo: Path) -> None:
    """git reads a bare `main` as a path too when one exists, and an untracked
    build output or a `main/` folder made `rev-list` refuse the range as
    ambiguous, so `review start` failed in that repository every time."""
    reviewed = commit(repo, "a")
    head = commit(repo, "b")
    (repo / "main").mkdir()

    assert _review.commit_range(repo, head, reviewed).commits == (head,)


def test_range_keeps_a_merge_edited_before_it_was_committed(
    tmp_path: Path, repo: Path
) -> None:
    """An edit made during a merge exists only in the merge commit. Dropping
    every merge meant a branch whose only new commit was that merge read as
    up to date, and nobody reviewed the edit."""
    reviewed = commit(repo, "a")
    push_to_main(tmp_path, repo, "m1")
    git(repo, "merge", "-q", "--no-commit", "origin/main")
    (repo / "a").write_text("edited in the merge\n")
    git(repo, "add", "a")
    git(repo, "commit", "-q", "--no-edit")
    merge = git(repo, "rev-parse", "HEAD")

    assert _review.commit_range(repo, merge, reviewed).commits == (merge,)


def test_range_keeps_a_conflict_resolved_by_keeping_the_branchs_side(
    tmp_path: Path, repo: Path
) -> None:
    """Keeping one side is the most common resolution, and here it undoes the
    fix `main` made to the same line. `diff-tree --cc` printed nothing for it,
    since the result matches a parent, so the merge left the range unreviewed."""
    reviewed = commit(repo, "init", "branch edit\n")
    push_to_main(tmp_path, repo, "init", "security fix\n")
    conflicted = subprocess.run(
        ["git", "-C", str(repo), "merge", "-q", "--no-edit", "origin/main"],
        capture_output=True,
    )
    assert conflicted.returncode == 1
    git(repo, "checkout", "--ours", "init")
    git(repo, "add", "init")
    git(repo, "commit", "-q", "--no-edit")
    merge = git(repo, "rev-parse", "HEAD")

    assert _review.commit_range(repo, merge, reviewed).commits == (merge,)


def test_range_keeps_a_merge_that_discards_mains_changes(
    tmp_path: Path, repo: Path
) -> None:
    """`git merge -s ours` records `main` as merged and keeps none of it, so
    landing the branch deletes `main`'s work with no conflict to notice."""
    reviewed = commit(repo, "a")
    push_to_main(tmp_path, repo, "fix")
    git(repo, "merge", "-q", "-s", "ours", "--no-edit", "origin/main")
    merge = git(repo, "rev-parse", "HEAD")

    assert _review.commit_range(repo, merge, reviewed).commits == (merge,)


def test_range_leaves_out_a_clean_merge_of_nearby_lines(
    tmp_path: Path, repo: Path
) -> None:
    """Both sides editing lines close together in one file put one hunk of
    each parent in `diff-tree --cc`, so a merge git made on its own forced a
    review round (US2 scenario 4)."""
    commit(repo, "a")
    push_to_main(tmp_path, repo, "f", "1\n2\n3\n4\n")
    git(repo, "merge", "-q", "--no-edit", "origin/main")
    reviewed = commit(repo, "f", "one\n2\n3\n4\n")
    push_to_main(tmp_path, repo, "f", "1\n2\nthree\n4\n")
    git(repo, "merge", "-q", "--no-edit", "origin/main")
    own = commit(repo, "b")

    assert (repo / "f").read_text() == "one\n2\nthree\n4\n"
    assert _review.commit_range(repo, own, reviewed).commits == (own,)


def test_range_keeps_a_merge_of_a_history_with_no_common_commit(repo: Path) -> None:
    """A merged orphan branch shares no commit with the branch, and
    `merge-tree` refuses to redo that merge, so every `review start` on such a
    branch failed with a git error."""
    reviewed = commit(repo, "a")
    git(repo, "checkout", "-q", "--orphan", "vendor")
    git(repo, "rm", "-q", "-r", "-f", ".")
    vendored = commit(repo, "lib")
    git(repo, "checkout", "-q", "637-x")
    git(repo, "merge", "-q", "--no-edit", "--allow-unrelated-histories", "vendor")
    merge = git(repo, "rev-parse", "HEAD")
    own = commit(repo, "b")

    found = _review.commit_range(repo, own, reviewed).commits
    assert set(found) == {vendored, merge, own}


def test_range_refuses_a_shallow_clone(tmp_path: Path, repo: Path) -> None:
    """`rev-list` can't list commits past a shallow cut, so a completed run
    marked them reviewed unseen. A merge whose parents' shared commit was cut
    was also redone against an older base, and one that kept a file `main`
    deleted matched its redo and left the range."""
    commit(repo, "a")
    head = commit(repo, "b")
    git(repo, "checkout", "-q", "main")
    shallow = tmp_path / "shallow"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", "--no-single-branch",
         f"file://{repo}", str(shallow)],
        check=True,
    )
    git(shallow, "checkout", "-q", "637-x")

    with pytest.raises(_review.ShallowClone, match="git fetch --unshallow"):
        _review.commit_range(shallow, head, None)


def test_range_judges_a_feature_head_from_the_main_checkout(repo: Path) -> None:
    """The merge gate judges a pull request's head from the `main` checkout. A
    check that compared the trunk with the checked-out branch refused every
    range computed there, since the checkout is on the trunk itself."""
    first = commit(repo, "a")
    head = commit(repo, "b")
    git(repo, "checkout", "-q", "main")

    assert set(_review.commit_range(repo, head, None).commits) == {first, head}
    found = _review.commit_range(repo, head, None, branch="637-x")
    assert set(found.commits) == {first, head}


def replace_ref(repo: Path, kind: str, first: str, head: str) -> str:
    """Make a replace ref of `kind` against a branch whose commits are `first`
    and `head`, and return the object it replaces."""
    main = git(repo, "rev-parse", "main")
    if kind == "graft-out":
        git(repo, "replace", "--graft", head, main)
        return head
    if kind == "same-tree-graft":
        decoy = git(repo, "commit-tree", f"{head}^{{tree}}", "-m", "decoy")
        git(repo, "replace", "--graft", head, decoy)
        return head
    if kind == "blob":
        blob = git(repo, "rev-parse", f"{head}:b")
        benign = subprocess.run(
            ["git", "hash-object", "-w", "--stdin"], cwd=repo, input="benign\n",
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        git(repo, "replace", blob, benign)
        return blob
    target = first if kind == "listed-commit" else main
    (repo / "other").write_text("other\n")
    git(repo, "add", "other")
    tree = git(repo, "write-tree")
    git(repo, "reset", "-q", "other")
    git(repo, "replace", target, git(repo, "commit-tree", tree, "-m", "other"))
    return target


@pytest.mark.parametrize(
    "kind", ["graft-out", "same-tree-graft", "blob", "listed-commit", "parent-commit"],
)
def test_range_refuses_any_replace_ref(repo: Path, kind: str) -> None:
    """wfctl lists commits with `--no-replace-objects`, and a reviewer reads
    them with a plain `git show`, which honors replace refs. A check of the
    replaced commit's tree let three kinds through: a replaced blob showed
    other file content, and a graft onto a parent with the same tree showed an
    empty diff, so the real change went unread. Grafting commits out made the
    reviewer's diff span them all, against a range listing them one by one.
    The remedy deletes each ref by its full name, since `git replace -d`
    resolves its argument as an object and can't reach every name."""
    first = commit(repo, "a")
    head = commit(repo, "b")
    replaced = replace_ref(repo, kind, first, head)

    with pytest.raises(_review.ReviewError, match=f"git update-ref --no-deref -d refs/replace/{replaced}$"):
        _review.commit_range(repo, head, None)


def test_range_keeps_a_merge_of_more_than_two_branches(repo: Path) -> None:
    """An octopus merge has no single two-parent redo to compare against, so
    nothing can show git made it unaided, and it stays in the range."""
    reviewed = commit(repo, "a")
    for name in ("b1", "b2"):
        git(repo, "checkout", "-q", "-b", name, reviewed)
        commit(repo, name)
    git(repo, "checkout", "-q", "637-x")
    git(repo, "merge", "-q", "--no-ff", "--no-edit", "b1", "b2")
    merge = git(repo, "rev-parse", "HEAD")

    assert len(git(repo, "rev-list", "--parents", "-1", merge).split()) == 4
    assert merge in _review.commit_range(repo, merge, reviewed).commits


def test_range_ignores_a_tag_named_after_the_trunk(repo: Path) -> None:
    """git resolves a short `main` to a tag before the branch, so a tag named
    `main` on the branch's own commit made that commit read as already on the
    trunk."""
    own = commit(repo, "a")
    git(repo, "tag", "main", own)

    assert _review.commit_range(repo, own, None).commits == (own,)


def test_range_reads_origin_main_when_origin_head_is_not_set(
    tmp_path: Path, repo: Path
) -> None:
    """A remote added with `git remote add` has no `origin/HEAD`, so the trunk
    resolves to the local `main`. A stale local `main` then made every commit
    merged in from `origin/main` read as the branch's own work."""
    reviewed = commit(repo, "a")
    from_main = push_to_main(tmp_path, repo, "m1")
    git(repo, "merge", "-q", "--no-edit", "origin/main")
    own = commit(repo, "b")
    git(repo, "symbolic-ref", "--delete", "refs/remotes/origin/HEAD")

    assert _review.trunk_refs(repo) == ["refs/remotes/origin/main", "refs/heads/main"]
    found = _review.commit_range(repo, own, reviewed)
    assert from_main not in found.commits
    assert found.commits == (own,)


def single_branch_clone(tmp_path: Path, repo: Path, branch: str = "637-x") -> Path:
    """A clone that fetched only `branch` from `origin`, the way
    `git clone --single-branch --branch <branch>` makes one."""
    git(repo, "push", "-q", "origin", "637-x")
    clone = tmp_path / f"single-{branch}"
    subprocess.run(
        ["git", "clone", "-q", "--single-branch", "--branch", branch,
         str(tmp_path / "origin.git"), str(clone)],
        check=True,
    )
    for key, val in (("user.email", "test@test.com"), ("user.name", "Test")):
        git(clone, "config", key, val)
    return clone


@pytest.mark.parametrize("parent", ["main", "same-tree"])
def test_range_refuses_a_grafts_file(repo: Path, parent: str) -> None:
    """A `.git/info/grafts` line rewrites a commit's parents, and
    `--no-replace-objects` doesn't turn it off. wfctl now ignores the file,
    but a reviewer's `git show` still reads it, so a line pointing the head at
    a parent with its own tree showed the reviewer an empty diff."""
    commit(repo, "a")
    head = commit(repo, "b")
    onto = (
        git(repo, "rev-parse", "main") if parent == "main"
        else git(repo, "commit-tree", f"{head}^{{tree}}", "-m", "decoy")
    )
    grafts = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-path", "info/grafts"))
    grafts.parent.mkdir(parents=True, exist_ok=True)
    grafts.write_text(f"{head} {onto}\n")

    with pytest.raises(_review.ReviewError, match="grafts"):
        _review.commit_range(repo, head, None)


@pytest.mark.parametrize("form", ["nested", "upper", "suffixed", "longer", "not an id"])
def test_range_refuses_a_replace_ref_under_any_name(repo: Path, form: str) -> None:
    """Git reads a replace ref's name after its last `/`, in either case, and
    ignores what follows the id, so a check for exactly 40 or 64 lowercase hex
    digits let four names through that swapped what a reviewer read. A name
    git ignores is refused too, since its remedy works for any name."""
    head = commit(repo, "a")
    blob = git(repo, "rev-parse", f"{head}:a")
    name = {
        "nested": f"x/{blob}",
        "upper": blob.upper(),
        "suffixed": f"{blob}zz",
        "longer": f"{blob}0",
        "not an id": "foo",
    }[form]
    git(repo, "update-ref", f"refs/replace/{name}", git(repo, "rev-parse", "main:"))

    with pytest.raises(
        _review.ReviewError, match=re.escape(f"git update-ref --no-deref -d refs/replace/{name}")
    ):
        _review.commit_range(repo, head, None)


@pytest.mark.parametrize("base", [None, "refs/other/", "refs/other"])
def test_range_refusal_prints_a_remedy_that_deletes_every_replace_ref(
    repo: Path, monkeypatch: pytest.MonkeyPatch, base: str | None
) -> None:
    """`git update-ref -d` deletes one ref and reads a second name as the
    value the first must hold, so one command naming every ref deleted none of
    two and failed outright on three. The remedy builds each name from
    `GIT_REPLACE_REF_BASE`, which no test had set, and older git strips a base
    with no trailing slash literally. Newer git, 2.55 on CI and 2.56 on
    Alpine, aborts every command that reads objects under such a base, so a
    reviewer's `git show` hides nothing there and the range refuses on git's
    own failure. The refs are made before the base is set, since `update-ref`
    aborts under it too. The test runs the remedy as printed."""
    head = commit(repo, "a")
    namespace = (base or "refs/replace/").rstrip("/")
    for name in ("a", "b", "c"):
        git(repo, "update-ref", f"{namespace}/{name}", git(repo, "rev-parse", "main:"))
    if base is not None:
        monkeypatch.setenv("GIT_REPLACE_REF_BASE", base)

    if subprocess.run(["git", "replace", "-l"], cwd=repo, capture_output=True).returncode:
        with pytest.raises(_review.ReviewError, match="git replace failed"):
            _review.commit_range(repo, head, None)
        return
    with pytest.raises(_review.ReviewError) as refused:
        _review.commit_range(repo, head, None)
    remedy = str(refused.value).split("remove each with ", 1)[1]
    subprocess.run(remedy, shell=True, cwd=repo, check=True)

    assert git(repo, "replace", "-l") == ""


def test_range_refusal_deletes_a_symbolic_replace_ref_and_not_its_target(repo: Path) -> None:
    """Git honors a symbolic ref under `refs/replace/`, and `update-ref -d`
    follows one unless told not to, so the remedy deleted the branch it
    pointed at and left the replace ref in place to refuse again."""
    head = commit(repo, "a")
    git(repo, "branch", "side")
    git(repo, "symbolic-ref", f"refs/replace/{head}", "refs/heads/side")

    with pytest.raises(_review.ReviewError) as refused:
        _review.commit_range(repo, head, None)
    remedy = str(refused.value).split("remove each with ", 1)[1]
    subprocess.run(remedy, shell=True, cwd=repo, check=True)

    assert git(repo, "replace", "-l") == ""
    assert git(repo, "rev-parse", "--verify", "refs/heads/side") == head


def test_range_refuses_an_empty_replace_ref_base_with_a_remedy_that_clears_it(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Git takes an empty `GIT_REPLACE_REF_BASE` as given, so `replace -l`
    lists every ref in the repository. The remedy named
    `refs/replace/refs/heads/main`, which doesn't exist, so deleting it did
    nothing and every review stayed refused."""
    head = commit(repo, "a")
    monkeypatch.setenv("GIT_REPLACE_REF_BASE", "")

    with pytest.raises(_review.ReviewError, match="unset GIT_REPLACE_REF_BASE$"):
        _review.commit_range(repo, head, None)


def test_range_refuses_a_grafts_file_of_only_whitespace(repo: Path) -> None:
    """The record refuses a grafts file with any content, and the check
    stripped whitespace first, so a file of blank lines passed it."""
    head = commit(repo, "a")
    grafts = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-path", "info/grafts"))
    grafts.parent.mkdir(parents=True, exist_ok=True)
    grafts.write_text("\n \n")

    with pytest.raises(_review.ReviewError, match="grafts"):
        _review.commit_range(repo, head, None)


def test_range_lists_when_the_grafts_variable_is_empty(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Git reads no grafts file when `GIT_GRAFT_FILE` is set and empty, and
    `rev-parse --git-path` refuses the empty value, so every review failed
    with an error that named no remedy."""
    head = commit(repo, "a")
    monkeypatch.setenv("GIT_GRAFT_FILE", "")

    assert _review.commit_range(repo, head, None).commits == (head,)


def test_range_refuses_a_grafts_file_that_is_not_text(repo: Path) -> None:
    """Git reads a grafts file as bytes, and wfctl read it as UTF-8, so a file
    holding other bytes raised a decode error, which `review start` printed as
    a traceback rather than a refusal."""
    head = commit(repo, "a")
    grafts = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-path", "info/grafts"))
    grafts.parent.mkdir(parents=True, exist_ok=True)
    grafts.write_bytes(b"\xff\xfe\x00bad\n")

    with pytest.raises(_review.ReviewError, match="grafts"):
        _review.commit_range(repo, head, None)


@pytest.mark.parametrize("named", ["absolute", "relative", "trailing space"])
def test_range_refuses_a_grafts_file_named_by_the_environment(
    tmp_path: Path, repo: Path, monkeypatch: pytest.MonkeyPatch, named: str
) -> None:
    """A reviewer's git reads the grafts file `GIT_GRAFT_FILE` names in place
    of `.git/info/grafts`, so that is the file to look at. Git resolves a
    relative name from the top of the worktree, and wfctl resolved it from
    its own directory, so a run from a subdirectory missed the file. wfctl
    also stripped the path git printed, so a name ending in a space named
    another file."""
    commit(repo, "a")
    head = commit(repo, "b")
    grafts = {
        "absolute": tmp_path / "elsewhere",
        "relative": repo / "grafts",
        "trailing space": tmp_path / "elsewhere ",
    }[named]
    grafts.write_text(f"{head} {git(repo, 'rev-parse', 'main')}\n")
    (repo / "sub").mkdir()
    monkeypatch.chdir(repo / "sub")
    monkeypatch.setenv("GIT_GRAFT_FILE", "grafts" if named == "relative" else str(grafts))

    with pytest.raises(_review.ReviewError, match="unset GIT_GRAFT_FILE"):
        _review.commit_range(repo, head, None)


def test_range_refuses_a_tag_named_after_a_trunk_branch_the_clone_lacks(
    tmp_path: Path, repo: Path
) -> None:
    """A clone that fetched only the feature branch has no `main` branch, so
    the trunk lookup fell back to the short name, and git resolved it to a tag
    named `main` on the branch's own commit. Every commit up to the tag then
    read as already on the trunk."""
    commit(repo, "a")
    clone = single_branch_clone(tmp_path, repo)
    head = git(clone, "rev-parse", "HEAD")
    git(clone, "tag", "main", head)

    with pytest.raises(_review.NoTrunk):
        _review.commit_range(clone, head, None)


@pytest.mark.parametrize("checkout", ["as-cloned", "renamed", "detached"])
def test_range_refuses_a_single_branch_clone_whose_origin_head_names_the_branch(
    tmp_path: Path, repo: Path, checkout: str
) -> None:
    """In a clone of only the feature branch, `origin/HEAD` can point only at
    that branch. It then reads as the trunk, `--not` drops every commit on the
    branch, and `review start` reported the group up to date with nothing
    reviewed. Comparing branch names doesn't catch it after a rename or on a
    detached HEAD, so the refusal reads the clone's fetch refspec instead.
    `origin/HEAD` is set by hand, the way `git remote set-head` sets it."""
    commit(repo, "a")
    clone = single_branch_clone(tmp_path, repo)
    git(clone, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/637-x")
    if checkout == "renamed":
        git(clone, "branch", "-m", "637-x", "642-renamed")
    elif checkout == "detached":
        git(clone, "checkout", "-q", "--detach")
    head = commit(clone, "b")

    with pytest.raises(_review.ReviewError, match="fetches only"):
        _review.commit_range(clone, head, None)


def test_range_refusal_names_a_clone_that_fetches_no_branch(
    tmp_path: Path, repo: Path
) -> None:
    """With no fetch refspec at all, the refusal said "fetches only no
    branch"."""
    commit(repo, "a")
    clone = single_branch_clone(tmp_path, repo)
    git(clone, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/637-x")
    git(clone, "config", "--unset-all", "remote.origin.fetch")
    head = commit(clone, "b")

    with pytest.raises(_review.ReviewError, match="this clone fetches no branch from origin"):
        _review.commit_range(clone, head, None)


def test_range_reads_a_declared_trunk_in_a_single_branch_clone_of_it(
    tmp_path: Path, repo: Path
) -> None:
    """The refusal above names declaring the trunk as the way out, so a
    single-branch clone of `main` with `trunk` declared has to work."""
    clone = single_branch_clone(tmp_path, repo, "main")
    git(clone, "checkout", "-q", "-b", "642-y")
    (clone / "wfctl.json").write_text(json.dumps({"trunk": "main"}))
    head = commit(clone, "a")

    assert _review.commit_range(clone, head, None).commits == (head,)


def test_range_refuses_a_trunk_that_is_the_branch_under_review(
    repo: Path, state: Path
) -> None:
    """With `origin/HEAD` on the branch itself, every commit on it reads as
    already on the trunk. The guard refused that, but `review start` reported
    the group up to date with nothing reviewed."""
    commit(repo, "a")
    git(repo, "push", "-q", "origin", "637-x")
    git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/637-x")
    head = commit(repo, "b")

    with pytest.raises(_review.ReviewError, match="the branch under review"):
        _review.commit_range(repo, head, None, branch="637-x")
    with pytest.raises(_review.ReviewError, match="the branch under review"):
        _review.start(repo, state, SECURITY, branch="637-x", cap=9)
    with pytest.raises(_review.ReviewError, match="the branch under review"):
        _review.unreviewed(repo, state, [SECURITY], head, branch="637-x")


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

    started = _review.start(repo, state, group, which=lambda _: "/bin/codex", cap=9)

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
    numbers = [_review.start(repo, state, SECURITY, cap=9).run for _ in range(3)]
    assert [r.number for r in numbers if r] == [1, 2, 3]
    assert sorted(p.name for p in (state / "reviews/security/runs").iterdir()) == [
        "001", "002", "003",
    ]


def test_start_with_nothing_unreviewed_writes_nothing(repo: Path, state: Path) -> None:
    """An empty run can't be reviewed, and a run record for one would read as a
    review that's waiting on reports."""
    commit(repo, "a")
    complete(repo, state)

    started = _review.start(repo, state, SECURITY, cap=9)

    assert started.run is None
    assert started.commits == ()
    assert sorted(p.name for p in (state / "reviews/security/runs").iterdir()) == ["001"]


# --- the round cap -------------------------------------------------------------


def run_folders(state: Path) -> list[str]:
    runs = state / "reviews/security/runs"
    return sorted(p.name for p in runs.iterdir()) if runs.is_dir() else []


def test_start_under_the_cap_writes_the_run_and_reports_the_rounds_before_it(
    repo: Path, state: Path,
) -> None:
    """`rounds` is the count before this call, so the header prints `rounds + 1`
    and the first run reads as round 1 of the cap."""
    commit(repo, "a")

    first = _review.start(repo, state, SECURITY, cap=3)
    second = _review.start(repo, state, SECURITY, cap=3)

    assert first.run is not None and first.rounds == 0 and first.sign_off is None
    assert second.run is not None and second.rounds == 1 and second.sign_off is None


def test_start_with_nothing_to_review_is_up_to_date_even_at_the_cap(
    repo: Path, state: Path,
) -> None:
    """FR-002 checks the range before the count. A group that has run its
    rounds and reviewed everything is finished, so refusing it would tell the
    agent a limit was hit when there was nothing left to review."""
    commit(repo, "a")
    complete(repo, state)

    started = _review.start(repo, state, SECURITY, cap=1)

    assert started.run is None and started.sign_off is None
    assert started.commits == () and started.rounds == 1
    assert run_folders(state) == ["001"]


def test_start_with_nothing_to_review_is_up_to_date_under_a_cap_of_zero(
    repo: Path, state: Path,
) -> None:
    """A cap of 0 says no review runs. With no commits there is still nothing
    to refuse, so a branch with no work doesn't need a sign-off."""
    started = _review.start(repo, state, SECURITY, cap=0)

    assert started.run is None and started.sign_off is None and started.commits == ()


def test_start_at_the_cap_with_a_sign_off_over_every_commit_writes_nothing(
    repo: Path, state: Path,
) -> None:
    """The sign-off is the user's way past the cap. `sign_off` names the signed
    commit so the command can say what covers the range, and no run folder is
    made, since nothing is left for a reviewer to read."""
    head = commit(repo, "a")
    _review.start(repo, state, SECURITY, cap=1)
    _review.sign_off(state, head)

    started = _review.start(repo, state, SECURITY, cap=1)

    assert started.run is None
    assert started.sign_off == head
    assert started.rounds == 1
    assert run_folders(state) == ["001"]


def test_start_at_the_cap_refuses_when_a_commit_is_not_signed_off(
    repo: Path, state: Path,
) -> None:
    """A refusal writes no folder, so the count stays at the cap and the next
    attempt reaches the same answer."""
    commit(repo, "a")
    _review.start(repo, state, SECURITY, cap=1)

    with pytest.raises(_review.RoundCapReached) as refused:
        _review.start(repo, state, SECURITY, cap=1)

    assert (refused.value.group, refused.value.rounds, refused.value.cap) == ("security", 1, 1)
    assert run_folders(state) == ["001"]


def test_start_at_the_cap_refuses_a_commit_made_after_the_sign_off(
    repo: Path, state: Path,
) -> None:
    """A sign-off covers a commit when it is the signed commit or an ancestor,
    so one commit added afterwards is unreviewed again, as it is for the
    guard."""
    signed = commit(repo, "a")
    _review.start(repo, state, SECURITY, cap=1)
    _review.sign_off(state, signed)
    commit(repo, "b")

    with pytest.raises(_review.RoundCapReached):
        _review.start(repo, state, SECURITY, cap=1)


def test_start_at_the_cap_allows_a_clean_merge_of_main_after_the_sign_off(
    tmp_path: Path, repo: Path, state: Path,
) -> None:
    """`commit_range` leaves out a merge git would have made on its own, so the
    new head isn't covered by the sign-off but every commit in the range is.
    The guard allows that PR, and `review start` has to agree. Checking the
    head would ask the user for a sign-off they already gave."""
    signed = commit(repo, "a")
    _review.start(repo, state, SECURITY, cap=1)
    _review.sign_off(state, signed)
    push_to_main(tmp_path, repo, "from-main")
    git(repo, "merge", "-q", "--no-ff", "-m", "merge main", "origin/main")

    started = _review.start(repo, state, SECURITY, cap=1)

    assert started.run is None
    assert started.sign_off == signed
    assert started.commits == ()


def test_start_past_a_lowered_cap_refuses(repo: Path, state: Path) -> None:
    """The trunk can lower the cap below a count the branch already reached."""
    commit(repo, "a")
    for _ in range(3):
        _review.start(repo, state, SECURITY, cap=9)

    with pytest.raises(_review.RoundCapReached) as refused:
        _review.start(repo, state, SECURITY, cap=2)

    assert (refused.value.rounds, refused.value.cap) == (3, 2)


def test_start_under_a_cap_of_zero_refuses_any_commit_without_a_sign_off(
    repo: Path, state: Path,
) -> None:
    commit(repo, "a")

    with pytest.raises(_review.RoundCapReached) as refused:
        _review.start(repo, state, SECURITY, cap=0)

    assert (refused.value.rounds, refused.value.cap) == (0, 0)
    assert run_folders(state) == []


def test_start_under_a_cap_of_zero_allows_a_signed_off_range(
    repo: Path, state: Path,
) -> None:
    """With a cap of 0 every change needs a sign-off, and that sign-off is what
    lets the PR through."""
    head = commit(repo, "a")
    _review.sign_off(state, head)

    started = _review.start(repo, state, SECURITY, cap=0)

    assert started.run is None and started.sign_off == head and started.rounds == 0


def test_start_ignores_a_sign_off_for_a_commit_the_repository_never_saw(
    repo: Path, state: Path,
) -> None:
    """`unreviewed` treats a sign-off naming an unknown commit as no sign-off,
    since `merge-base` errors on one. `start` shares that rule rather than
    crashing at the cap."""
    commit(repo, "a")
    _review.start(repo, state, SECURITY, cap=1)
    _review.sign_off(state, "0" * 40)

    with pytest.raises(_review.RoundCapReached):
        _review.start(repo, state, SECURITY, cap=1)


@pytest.mark.parametrize(("rounds", "cap", "message"), [
    (3, 3, "security has run 3 of 3 rounds on this branch, the most review.rounds allows"),
    (4, 3, "security has run 4 rounds on this branch, more than the 3 review.rounds allows"),
    (0, 0, "review.rounds is 0, so security doesn't run on this branch"),
    (2, 0, "review.rounds is 0, so security doesn't run on this branch"),
])
def test_the_cap_refusal_says_which_limit_was_reached(
    rounds: int, cap: int, message: str,
) -> None:
    """The first line follows the count and the cap, so a lowered cap and a cap
    of 0 each read as what they are rather than as 'run 4 of 3'."""
    refused = _review.RoundCapReached("security", rounds, cap)

    assert str(refused) == message
    assert isinstance(refused, _review.ReviewError)
    assert (refused.group, refused.rounds, refused.cap) == ("security", rounds, cap)


def test_check_completes_a_run_only_when_every_reviewer_reported(
    repo: Path, state: Path
) -> None:
    """Completion moves the last reviewed commit, which is what later decides
    whether a PR can open. Only wfctl's own reading of the reports moves it
    (SC-002)."""
    commit(repo, "a")
    started = _review.start(repo, state, SECURITY, cap=9)
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
    started = _review.start(repo, state, SECURITY, cap=9)
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
    started = _review.start(repo, state, SECURITY, cap=9)
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
    first = _review.start(repo, state, SECURITY, cap=9)
    assert first.run is not None
    for r in ("s1", "s2", "s3"):
        (first.run.path / f"{r}.md").write_text(report(first.head))

    second = _review.start(repo, state, SECURITY, cap=9)

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
    started = _review.start(repo, state, SECURITY, cap=9)
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


def test_a_complete_run_stays_complete_when_a_report_changes_later(
    repo: Path, state: Path
) -> None:
    """The last reviewed commit has already moved, so reading the run as
    incomplete again would contradict the record every later run starts from.
    The roster still shows the changed report."""
    commit(repo, "a")
    started = complete(repo, state)
    assert started.run is not None
    (started.run.path / "s2.md").unlink()

    checked = _review.check(state, "security")

    assert checked.complete
    assert checked.missing == 1
    assert checked.run.record["completed_at"] is not None


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
        _review.start(repo, state, SECURITY, cap=9)
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


# --- relay ---------------------------------------------------------------------


def _relay(state: Path, rid: str, reason: str, text: str) -> str:
    return _review.relay(state, [SECURITY], rid, reason, text)


def test_a_relayed_report_naming_the_head_counts_and_shows_its_reason(
    repo: Path, state: Path
) -> None:
    """A reviewer the host blocked from writing still did the review. The
    roster line is where a person sees that it was relayed, and why
    (`622-blocked-reviewer-relays-report.md`, Verification)."""
    commit(repo, "a")
    started = _review.start(repo, state, SECURITY, cap=9)
    assert started.run is not None
    for rid in ("s1", "s3"):
        (started.run.path / f"{rid}.md").write_text(report(started.head))

    _relay(state, "s2", "write denied", report(started.head))
    checked = _review.check(state, "security")

    assert checked.complete
    assert _review.roster_lines(checked.entries) == [
        "s1 claude ✓", "s2 claude ✓ relayed: write denied", "s3 claude ✓",
    ]


def test_a_relayed_report_is_saved_under_a_header_then_verbatim(
    repo: Path, state: Path
) -> None:
    """The header is what tells a relay apart from a report the reviewer wrote,
    and the body has to arrive word for word to be judged as the reviewer's."""
    commit(repo, "a")
    started = _review.start(repo, state, SECURITY, cap=9)
    assert started.run is not None
    body = report(started.head) + "\n  trailing indent kept\n"

    _relay(state, "s2", "write   denied\n", body)

    saved = (started.run.path / "s2.md").read_text()
    header, rest = saved.split("\n\n", 1)
    reason, at = header.split("\n")
    assert reason == "Relayed: write denied"
    assert re.fullmatch(r"Relayed-at: \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", at)
    assert rest == body


@pytest.mark.parametrize("reason", ["", "   ", "\n"])
def test_a_relay_with_no_reason_is_refused_and_the_run_stays_incomplete(
    repo: Path, state: Path, reason: str
) -> None:
    """Every relayed report carries a reason a person can check against what
    the coordinator saw. One without a reason is a report the coordinator wrote
    for a reviewer, with nothing to show it."""
    commit(repo, "a")
    started = _review.start(repo, state, SECURITY, cap=9)
    assert started.run is not None
    for rid in ("s1", "s3"):
        (started.run.path / f"{rid}.md").write_text(report(started.head))

    with pytest.raises(_review.RelayRefused):
        _relay(state, "s2", reason, report(started.head))

    assert not (started.run.path / "s2.md").exists()
    assert not _review.check(state, "security").complete


def test_a_relayed_report_naming_an_older_commit_does_not_count(
    repo: Path, state: Path
) -> None:
    """A relay is judged like any other report, so it can't carry a review of
    code the branch no longer has."""
    older = commit(repo, "a")
    commit(repo, "b")
    started = _review.start(repo, state, SECURITY, cap=9)
    assert started.run is not None

    _relay(state, "s2", "write denied", report(older))

    entry = next(e for e in _review.check(state, "security").entries if e.id == "s2")
    assert not entry.counted
    assert entry.note == f"names {older[:7]}, not {started.head[:7]}"


def test_a_relay_appends_its_event(repo: Path, state: Path) -> None:
    """A restarted session reads `events.jsonl` to learn what happened, and a
    relay is the one report a coordinator handed in for someone else."""
    commit(repo, "a")
    started = _review.start(repo, state, SECURITY, cap=9)

    _relay(state, "s2", "write denied", report(started.head))

    last = json.loads((state / "events.jsonl").read_text().splitlines()[-1])
    assert {k: v for k, v in last.items() if k != "ts"} == {
        "event": "review-relay", "group": "security", "run": 1, "id": "s2",
        "reason": "write denied",
    }


# --- models that can't run -----------------------------------------------------


CODEX = "codex exec --sandbox read-only"
MIXED = Group("security", "reviewing-security", (
    Reviewer("s1", "claude", None), Reviewer("s2", "claude", None),
    Reviewer("s3", "codex", CODEX), Reviewer("s4", "codex", CODEX),
))
ONLY_CODEX = Group("security", "reviewing-security", (Reviewer("s1", "codex", CODEX),))


def test_a_model_whose_command_is_not_on_path_is_recorded_unavailable(
    repo: Path, state: Path
) -> None:
    """wfctl decides availability, so the coordinator can't declare a
    reviewer it would rather skip unavailable (research.md R7)."""
    commit(repo, "a")

    started = _review.start(repo, state, MIXED, which=lambda _: None, cap=9)

    assert started.run is not None
    reviewers = json.loads((started.run.path / "run.json").read_text())["reviewers"]
    assert reviewers[2:] == [
        {"id": f"s{i}", "model": "codex", "state": "unavailable", "command": CODEX,
         "reason": "`codex` not found on PATH"}
        for i in (3, 4)
    ]
    assert started.unavailable == {"codex": "`codex` not found on PATH"}
    assert started.expected == ["s1", "s2"]


def test_a_run_completes_on_the_reviewers_that_could_run(repo: Path, state: Path) -> None:
    """A repository that lists Codex shouldn't be stuck on a machine without
    it, and the roster still names the reviewers that were left out."""
    commit(repo, "a")
    started = _review.start(repo, state, MIXED, which=lambda _: None, cap=9)
    assert started.run is not None
    for rid in ("s1", "s2"):
        (started.run.path / f"{rid}.md").write_text(report(started.head))

    checked = _review.check(state, "security")

    assert checked.complete
    assert _review.roster_lines(checked.entries)[2:] == [
        "s3 codex  ✗ unavailable: `codex` not found on PATH",
        "s4 codex  ✗ unavailable: `codex` not found on PATH",
    ]


def test_a_run_where_no_reviewer_can_run_is_written_and_never_completes(
    repo: Path, state: Path
) -> None:
    """A group that completed with no review at all is the failure FR-001
    forbids. A person installs the model or signs off instead."""
    commit(repo, "a")

    started = _review.start(repo, state, ONLY_CODEX, which=lambda _: None, cap=9)

    assert started.run is not None
    assert started.expected == []
    checked = _review.check(state, "security")
    assert not checked.complete
    assert checked.expected == 0
    assert not (state / "reviews/security/last-reviewed.json").exists()


def test_a_model_on_path_that_writes_no_report_reads_as_no_report(
    repo: Path, state: Path
) -> None:
    """Codex installed but not logged in fails when it runs. That's a missing
    report, not an unavailable model, so the run waits for it."""
    commit(repo, "a")
    started = _review.start(repo, state, ONLY_CODEX, which=lambda _: "/bin/codex", cap=9)
    assert started.run is not None

    checked = _review.check(state, "security")

    assert not checked.complete
    assert [(e.id, e.note) for e in checked.entries] == [("s1", "no report")]


def test_claude_has_no_command_and_is_always_available(repo: Path, state: Path) -> None:
    """Claude runs inside the current agent, so there is nothing to look up,
    and a `which` that finds nothing mustn't mark it unavailable."""
    commit(repo, "a")

    started = _review.start(repo, state, SECURITY, which=lambda _: None, cap=9)

    assert started.expected == ["s1", "s2", "s3"]
    assert started.unavailable == {}


# --- what a run folder or a report left half-written does ----------------------


def test_a_run_folder_with_no_run_record_is_passed_over(repo: Path, state: Path) -> None:
    """An interrupted `start` leaves a folder with no `run.json`. Read as the
    latest run, it failed every `start`, `check` and `relay` on the group until
    someone deleted it by hand."""
    commit(repo, "a")
    _review.start(repo, state, SECURITY, cap=9)
    (state / "reviews/security/runs/002").mkdir()

    assert _review.check(state, "security").run.number == 1
    started = _review.start(repo, state, SECURITY, cap=9)
    assert started.run is not None and started.run.number == 3
    assert _review.check(state, "security").run.number == 3


def test_runs_started_is_zero_for_a_group_that_never_started(state: Path) -> None:
    assert _review.runs_started(state, "security") == 0


def test_runs_started_counts_a_run_that_never_completed(repo: Path, state: Path) -> None:
    """The cap limits rounds started, not rounds finished. A run that got no
    reports still cost the agent a round, and not counting it would let the
    agent start runs it never finishes without ever reaching the cap."""
    commit(repo, "a")
    for _ in range(3):
        _review.start(repo, state, SECURITY, cap=9)

    assert _review.runs_started(state, "security") == 3
    assert not _review.check(state, "security").complete


def test_runs_started_skips_a_folder_with_no_run_record(repo: Path, state: Path) -> None:
    """An interrupted `start` leaves a folder with no `run.json`, and `latest_run`
    passes it over. If the count used another rule, it and the next run number
    could disagree about how many runs there have been."""
    commit(repo, "a")
    _review.start(repo, state, SECURITY, cap=9)
    (state / "reviews/security/runs/002").mkdir()
    _review.start(repo, state, SECURITY, cap=9)

    assert _review.runs_started(state, "security") == 2
    latest = _review.latest_run(state, "security")
    assert latest is not None and latest.number == 3


def test_runs_started_ignores_a_name_that_is_not_a_run_number(repo: Path, state: Path) -> None:
    """`latest_run` reads only digit names, so a stray folder or file under
    `runs/` is no round."""
    commit(repo, "a")
    _review.start(repo, state, SECURITY, cap=9)
    (state / "reviews/security/runs/notes").mkdir()
    (state / "reviews/security/runs/notes/run.json").write_text("{}")

    assert _review.runs_started(state, "security") == 1


@pytest.mark.parametrize("failing", ["last-reviewed.json", "run.json"])
def test_a_completion_cut_off_partway_is_finished_by_the_next_check(
    repo: Path, state: Path, monkeypatch: pytest.MonkeyPatch, failing: str
) -> None:
    """A run marked complete is never completed again. Marking it before
    `last-reviewed.json` was written would leave a run every later `check`
    calls complete, with the last reviewed commit never moved."""
    commit(repo, "a")
    started = _review.start(repo, state, SECURITY, cap=9)
    assert started.run is not None
    for r in started.expected:
        (started.run.path / f"{r}.md").write_text(report(started.head))
    real = _review.write_atomic

    def fail_on(path: Path, content: str, newline: str | None = None) -> None:
        if path.name == failing:
            raise OSError("disk full")
        real(path, content, newline)

    monkeypatch.setattr(_review, "write_atomic", fail_on)
    with pytest.raises(OSError):
        _review.check(state, "security")
    monkeypatch.setattr(_review, "write_atomic", real)

    assert _review.check(state, "security").complete
    assert json.loads((started.run.path / "run.json").read_text())["completed_at"]
    assert _review.last_reviewed(state, "security") == started.head


def test_a_report_that_cannot_be_read_is_a_reason_rather_than_a_traceback(
    repo: Path, state: Path
) -> None:
    """The roster is where a person learns which report to fix, and a
    traceback hides the other reviewers' lines."""
    commit(repo, "a")
    started = _review.start(repo, state, SECURITY, cap=9)
    assert started.run is not None
    unreadable = started.run.path / "s1.md"
    unreadable.write_text(report(started.head))
    unreadable.chmod(0)
    try:
        entries = _review.check(state, "security").entries
    finally:
        unreadable.chmod(0o600)

    assert entries[0].note == "can't read report: Permission denied"


def test_a_verdict_inside_a_closing_code_fence_counts() -> None:
    """The rubric's own example wraps the report in a fence, so a reviewer
    copying it ends on the fence rather than on the verdict."""
    text = f"```\nReviewed: {HEAD[:7]}\n\nVerdict: Approve\n```\n"
    assert _review.judge(text, HEAD) is None


def test_a_verdict_inside_a_closing_tilde_fence_counts() -> None:
    """Markdown fences with `~~~` as well, and a report wrapped that way read
    as having no verdict."""
    text = f"~~~\nReviewed: {HEAD[:7]}\n\nVerdict: Approve\n~~~\n"
    assert _review.judge(text, HEAD) is None


def test_a_verdict_inside_a_longer_closing_fence_counts() -> None:
    """A report holding its own three-backtick blocks is wrapped in four, and
    only exactly three were recognised as a fence."""
    text = f"````\nReviewed: {HEAD[:7]}\n\nVerdict: Approve\n````\n"
    assert _review.judge(text, HEAD) is None


@pytest.mark.parametrize(
    "ending",
    [
        "**Verdict:** _Approve_",
        "Verdict: __Approve__",
        "Verdict: _Request changes_ (1 blocker)",
        "Verdict: Approved",
    ],
)
def test_a_verdict_with_underscores_or_a_past_tense_counts(ending: str) -> None:
    """Matching whole words rejected these, since `_` is a word character and
    `Approved` runs past the word. Each counted before, and a run stayed
    incomplete over a report that had finished."""
    assert _review.judge(f"Reviewed: {HEAD[:7]}\n\n{ending}\n", HEAD) is None


@pytest.mark.parametrize("ending", ["Verdict: Disapprove", "Verdict: Unapproved"])
def test_a_verdict_word_inside_another_word_is_not_a_verdict(ending: str) -> None:
    """The word was matched anywhere in the line, so `Disapprove` read as
    `Approve` and a verdict outside the rubric's two counted."""
    assert _review.judge(f"Reviewed: {HEAD[:7]}\n\n{ending}\n", HEAD) == (
        "no verdict at the end"
    )


def test_a_report_naming_a_full_sha_of_another_commit_shows_seven_digits() -> None:
    """The roster line has to fit on a terminal, and seven digits name the
    commit as well as forty."""
    other = "5c4b3a2" + "0" * 33
    assert _review.judge(f"Reviewed: {other}\n\nVerdict: Approve\n", HEAD) == (
        f"names 5c4b3a2, not {HEAD[:7]}"
    )


def test_a_quoted_program_path_is_looked_up_whole(repo: Path, state: Path) -> None:
    """Splitting on spaces looked up `"/opt/my` for a quoted path with a space
    in it, and marked a model that is installed as unavailable."""
    commit(repo, "a")
    seen: list[str] = []
    group = Group("security", "reviewing-security",
                  (Reviewer("s1", "codex", '"/opt/my tools/codex" exec'),))

    _review.start(repo, state, group, which=lambda p: seen.append(p) or p, cap=9)

    assert seen == ["/opt/my tools/codex"]


# --- sign-off ------------------------------------------------------------------


CODE = Group("code", "code-review", tuple(Reviewer(f"c{i}", "claude", None) for i in (1, 2, 3)))


def test_a_sign_off_covers_the_signed_commit_and_its_ancestors(repo: Path, state: Path) -> None:
    """R9. A sign-off covers what a person read when they signed, so every
    group's unreviewed commits up to the signed head are covered."""
    commit(repo, "a")
    head = commit(repo, "b")

    _review.sign_off(state, head)

    assert _review.unreviewed(repo, state, [SECURITY, CODE], head) == {}


def test_a_commit_after_the_sign_off_is_not_covered(repo: Path, state: Path) -> None:
    """A commit added later isn't an ancestor of the signed-off commit, so the
    person never read it."""
    signed = commit(repo, "a")
    _review.sign_off(state, signed)
    later = commit(repo, "b")

    assert _review.unreviewed(repo, state, [SECURITY, CODE], later) == {
        "security": (later,), "code": (later,),
    }


def test_unreviewed_commits_are_listed_oldest_first_per_group(repo: Path, state: Path) -> None:
    """The refusal reads top to bottom in the order the commits were made, and
    a group whose run completed is left out."""
    first = commit(repo, "a")
    second = commit(repo, "b")
    complete(repo, state, CODE)

    assert _review.unreviewed(repo, state, [SECURITY, CODE], second) == {
        "security": (first, second),
    }


def test_each_sign_off_replaces_the_last(repo: Path, state: Path) -> None:
    """One file holds one decision about the branch, so a second sign-off
    overwrites the first rather than adding to a list."""
    first = commit(repo, "a")
    _review.sign_off(state, first)
    second = commit(repo, "b")
    _review.sign_off(state, second)

    record = json.loads(_review.sign_off_path(state).read_text())

    assert record["sha"] == second
    assert set(record) == {"sha", "at"}
    assert _review.signed_off(state) == second


# --- the trunk reviews read, and the cap it carries ------------------------------


def declare_on_main(tmp_path: Path, repo: Path, text: str) -> None:
    """Land `wfctl.json` on `origin/main`, the file reviews read the trunk and
    the cap from."""
    push_to_main(tmp_path, repo, "wfctl.json", text)


def publish_branch(repo: Path, name: str) -> None:
    """Create `name` at `main` and push it, so the clone has `origin/<name>`."""
    git(repo, "branch", name, "main")
    git(repo, "push", "-q", "origin", name)


def test_read_config_at_tells_no_file_from_a_file_it_cannot_read(
    tmp_path: Path, repo: Path,
) -> None:
    """A missing file is the ordinary case and needs no warning, while bad JSON
    is a mistake the person has to hear about, so the two are different
    answers."""
    ref = "refs/remotes/origin/main"
    assert _review._read_config_at(repo, ref, None) == (None, None)

    declare_on_main(tmp_path, repo, "{not json")
    data, reason = _review._read_config_at(repo, ref, None)
    assert data is None and reason

    declare_on_main(tmp_path, repo, "[1]")
    assert _review._read_config_at(repo, ref, None) == (None, "it isn't a JSON object")

    declare_on_main(tmp_path, repo, '{"trunk": "main"}')
    assert _review._read_config_at(repo, ref, None) == ({"trunk": "main"}, None)


@pytest.mark.parametrize("locale_encoding", [None, "latin-1"])
def test_read_config_at_reports_a_file_that_is_not_utf8_instead_of_crashing(
    repo: Path, monkeypatch: pytest.MonkeyPatch, locale_encoding: str | None,
) -> None:
    """A trunk `wfctl.json` saved in another encoding made `git show` output
    fail to decode, and the `UnicodeDecodeError` escaped as a traceback from
    `review start` and as a refused PR from the guard. A bad trunk file is
    supposed to warn, so it has to come back as a reason like bad JSON does.

    The `latin-1` case stands in for a machine whose locale isn't UTF-8.
    `text=True` decodes with the locale's encoding, and Latin-1 decodes any
    byte, so the file read cleanly there and the warning never appeared."""
    if locale_encoding is not None:
        real_run = subprocess.run

        def run_under_locale(*args: object, **kwargs: object) -> object:
            if kwargs.get("text") and kwargs.get("encoding") is None:
                kwargs["encoding"] = locale_encoding
            return real_run(*args, **kwargs)  # type: ignore[call-overload]

        monkeypatch.setattr(_review.subprocess, "run", run_under_locale)
    (repo / "wfctl.json").write_bytes(b'{"trunk": "caf\xe9"}')
    git(repo, "add", "wfctl.json")
    git(repo, "commit", "-q", "-m", "latin-1 config")

    data, reason = _review._read_config_at(repo, "HEAD", None)

    assert data is None
    assert reason == "it isn't UTF-8"


@pytest.mark.parametrize(("text", "cap"), [
    (None, 3),
    ("{}", 3),
    ('{"review": {}}', 3),
    ('{"review": {"rounds": 5}}', 5),
    ('{"review": {"rounds": 0}}', 0),
])
def test_trunk_rounds_reads_the_cap_without_a_warning_when_there_is_nothing_wrong(
    tmp_path: Path, repo: Path, text: str | None, cap: int,
) -> None:
    """An absent file, key, or `review` object is a repository that never set a
    cap, so it gets the default and no warning."""
    if text is not None:
        declare_on_main(tmp_path, repo, text)

    found = _review.trunk_rounds(repo, None, branch="637-x")

    assert (found.cap, found.ref, found.warning) == (cap, "origin/main", None)


@pytest.mark.parametrize("text", [
    '{"review": {"rounds": -1}}',
    '{"review": {"rounds": 1.5}}',
    '{"review": {"rounds": "3"}}',
    '{"review": {"rounds": true}}',
])
def test_trunk_rounds_uses_the_default_and_warns_on_a_value_it_cannot_use(
    tmp_path: Path, repo: Path, text: str,
) -> None:
    """Refusing here would stop every review in the repository until someone
    fixed the trunk, so a bad value warns and the default applies."""
    declare_on_main(tmp_path, repo, text)

    found = _review.trunk_rounds(repo, None, branch="637-x")

    assert found.cap == 3
    assert found.warning == (
        "review.rounds on origin/main isn't a whole number of 0 or more; "
        "wfctl uses the default of 3"
    )


def test_trunk_rounds_names_the_review_key_when_it_is_not_an_object(
    tmp_path: Path, repo: Path,
) -> None:
    """When `review` is a number, the file has no `review.rounds`, so a warning
    that names `review.rounds` sends the reader looking for a key that isn't
    there."""
    declare_on_main(tmp_path, repo, '{"review": 4}')

    found = _review.trunk_rounds(repo, None, branch="637-x")

    assert found.cap == 3
    assert found.warning == (
        "review on origin/main isn't an object; wfctl uses the default of 3"
    )


@pytest.mark.parametrize("text", ["{not json", "[1]"])
def test_trunk_rounds_warns_when_the_trunks_file_is_not_a_json_object(
    tmp_path: Path, repo: Path, text: str,
) -> None:
    declare_on_main(tmp_path, repo, text)

    found = _review.trunk_rounds(repo, None, branch="637-x")

    assert found.cap == 3
    assert found.warning is not None
    assert found.warning.startswith("can't read wfctl.json on origin/main (")
    assert found.warning.endswith("); wfctl uses the default of 3")


def test_trunk_rounds_reads_the_local_branch_when_there_is_no_remote(
    repo: Path,
) -> None:
    """The remote ref comes first because a person's local `main` trails it. With
    no remote at all the local branch is the trunk, so the cap comes from it."""
    git(repo, "checkout", "-q", "main")
    commit(repo, "wfctl.json", '{"review": {"rounds": 5}}')
    git(repo, "checkout", "-q", "637-x")
    git(repo, "remote", "remove", "origin")

    found = _review.trunk_rounds(repo, None, branch="637-x")

    assert (found.cap, found.ref, found.warning) == (5, "main", None)


def test_review_trunk_reads_the_default_branch_and_says_where_it_looked(
    repo: Path,
) -> None:
    found = _review.review_trunk(repo, None, branch="637-x")

    assert (found.name, found.source, found.warnings) == ("origin/main", "origin/main", ())


def test_review_trunk_follows_a_trunk_the_default_branch_declares(
    tmp_path: Path, repo: Path,
) -> None:
    """A repository whose trunk is `develop` declares it where the agent can't
    push, which is the default branch."""
    publish_branch(repo, "develop")
    declare_on_main(tmp_path, repo, '{"trunk": "develop"}')

    found = _review.review_trunk(repo, None, branch="637-x")

    assert (found.name, found.source, found.warnings) == ("origin/develop", "origin/main", ())
    assert _review.trunk_refs(repo, None, branch="637-x")[0] == "refs/remotes/origin/develop"


def test_review_trunk_ignores_a_trunk_only_the_branch_declares_and_warns(
    repo: Path,
) -> None:
    """The branch's own `trunk` could hide its commits from the PR check, so the
    default branch decides and the branch hears that its edit has no effect."""
    git(repo, "branch", "loose", "main")
    (repo / "wfctl.json").write_text('{"trunk": "loose"}')

    found = _review.review_trunk(repo, None, branch="637-x")

    assert found.name == "origin/main"
    assert found.warnings == (
        "this branch sets trunk to loose, but wfctl reads main from origin/main "
        "until the change merges",
    )


def test_review_trunk_does_not_warn_when_the_branch_declares_the_same_trunk(
    repo: Path,
) -> None:
    (repo / "wfctl.json").write_text('{"trunk": "main"}')

    assert _review.review_trunk(repo, None, branch="637-x").warnings == ()


def test_review_trunk_refuses_a_default_branch_trunk_the_clone_lacks(
    tmp_path: Path, repo: Path,
) -> None:
    """Measuring against the default branch instead would review the wrong
    commits with nothing to say so. `git fetch` is the usual fix."""
    declare_on_main(tmp_path, repo, '{"trunk": "develop"}')

    with pytest.raises(_review.NoTrunk) as refused:
        _review.review_trunk(repo, None, branch="637-x")

    assert str(refused.value) == (
        "can't find the trunk branch develop; check trunk in wfctl.json on origin/main, "
        "or run git fetch"
    )


@pytest.mark.parametrize("trunk", ['5', '""', '"HEAD"', 'null'])
def test_review_trunk_warns_and_uses_the_default_for_a_trunk_that_is_not_a_name(
    tmp_path: Path, repo: Path, trunk: str,
) -> None:
    declare_on_main(tmp_path, repo, f'{{"trunk": {trunk}}}')

    found = _review.review_trunk(repo, None, branch="637-x")

    assert found.name == "origin/main"
    assert found.warnings == (
        "trunk on origin/main isn't a branch name; wfctl reviews against main",
    )


def test_review_trunk_warns_when_the_default_branchs_file_is_not_json(
    tmp_path: Path, repo: Path,
) -> None:
    declare_on_main(tmp_path, repo, "{not json")

    found = _review.review_trunk(repo, None, branch="637-x")

    assert found.name == "origin/main"
    assert len(found.warnings) == 1
    assert found.warnings[0].startswith("can't read wfctl.json on origin/main (")
    assert found.warnings[0].endswith("); wfctl reviews against main")


def test_review_trunk_refuses_a_working_tree_trunk_the_clone_lacks(repo: Path) -> None:
    """The guard refuses the same branch, so a warning here would tell the user
    the change can merge and the guard would then say otherwise."""
    (repo / "wfctl.json").write_text('{"trunk": "nope"}')

    with pytest.raises(_review.NoTrunk):
        _review.review_trunk(repo, None, branch="637-x")


def test_review_trunk_refuses_a_working_tree_trunk_that_is_not_a_name(repo: Path) -> None:
    (repo / "wfctl.json").write_text('{"trunk": 5}')

    with pytest.raises(_review.NoTrunk):
        _review.review_trunk(repo, None, branch="637-x")


def test_review_trunk_without_origin_head_leaves_the_branch_to_choose(repo: Path) -> None:
    """A remote added by hand records no `origin/HEAD`. That layout keeps
    today's resolution, which reads the working tree's `trunk` first."""
    git(repo, "symbolic-ref", "--delete", "refs/remotes/origin/HEAD")
    git(repo, "branch", "loose", "main")
    (repo / "wfctl.json").write_text('{"trunk": "loose"}')

    found = _review.review_trunk(repo, None, branch="637-x")

    assert (found.name, found.source, found.warnings) == ("loose", None, ())


def test_review_trunk_does_not_trust_origin_head_in_a_single_branch_clone(
    tmp_path: Path, repo: Path,
) -> None:
    """`origin/HEAD` can name the branch under review there, so the default
    branch's file isn't read and today's resolution applies."""
    publish_branch(repo, "develop")
    declare_on_main(tmp_path, repo, '{"trunk": "develop"}')
    git(repo, "config", "remote.origin.fetch", "+refs/heads/main:refs/remotes/origin/main")

    found = _review.review_trunk(repo, None, branch="637-x")

    assert (found.name, found.source) == ("origin/main", None)


def test_review_trunk_refuses_an_origin_head_naming_a_ref_the_clone_lacks(
    repo: Path,
) -> None:
    """Skipping it would turn the check off with no message, and one git command
    fixes it."""
    git(repo, "update-ref", "-d", "refs/remotes/origin/main")

    with pytest.raises(_review.ReviewError) as refused:
        _review.review_trunk(repo, None, branch="637-x")

    assert str(refused.value) == (
        "origin/HEAD names origin/main, which this clone doesn't have; "
        "run git remote set-head origin --auto"
    )


def test_review_trunk_tells_a_missing_origin_head_from_a_git_failure(
    tmp_path: Path, repo: Path,
) -> None:
    """A missing `origin/HEAD` exits 1 under `--quiet` and falls back. Any other
    failure, such as a directory that isn't a repository, exits 128 and refuses,
    so a broken git can't pass for a clone with no default branch."""
    git(repo, "symbolic-ref", "--delete", "refs/remotes/origin/HEAD")
    assert _review.review_trunk(repo, None, branch="637-x").source is None

    with pytest.raises(_review.ReviewError, match="git symbolic-ref failed"):
        _review.review_trunk(tmp_path, None, branch="637-x")


def test_a_working_tree_trunk_that_is_the_branch_under_review_is_refused(
    repo: Path,
) -> None:
    """PR-023. With `origin/HEAD` set the branch's setting no longer picks the
    trunk, but a trunk equal to the branch would still hide every commit, so
    the same-name refusal holds on this path too, without a mismatch warning."""
    (repo / "wfctl.json").write_text('{"trunk": "637-x"}')
    expected = (
        "the trunk branch is 637-x, the branch under review; check trunk in wfctl.json"
    )

    with pytest.raises(_review.ReviewError) as from_trunk:
        _review.review_trunk(repo, None, branch="637-x")
    with pytest.raises(_review.ReviewError) as from_refs:
        _review.trunk_refs(repo, None, branch="637-x")

    assert str(from_trunk.value) == expected
    assert str(from_refs.value) == expected


def test_a_default_branch_trunk_that_is_the_branch_under_review_names_that_file(
    tmp_path: Path, repo: Path,
) -> None:
    declare_on_main(tmp_path, repo, '{"trunk": "637-x"}')
    git(repo, "push", "-q", "origin", "637-x")

    with pytest.raises(_review.ReviewError) as refused:
        _review.trunk_refs(repo, None, branch="637-x")

    assert str(refused.value) == (
        "the trunk branch is 637-x, the branch under review; "
        "check trunk in wfctl.json on origin/main"
    )
