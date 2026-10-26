"""Review records: which commits each review group has covered on a branch.

Everything lives in the branch's state directory under `reviews/`, beside
`verify.json`, so `wfctl store specs` never commits it and removing a worktree
keeps it (`622-review-records-in-state-dir.md`):

    reviews/<group>/last-reviewed.json     the group's last reviewed commit
    reviews/<group>/runs/<NNN>/run.json    a run's expected reviewers and commits
    reviews/<group>/runs/<NNN>/<id>.md     one report per reviewer

wfctl, not the coordinating agent, decides whether a report counts and whether
a run is complete, since the agent would otherwise be grading its own panel
(`review-covers-unreviewed-commits`). Only the last reviewed commit, the run
records, and the reports are stored. Which commits are unreviewed is derived
from git on every read.

The guard imports this module on a matched command, so it imports nothing that
loads `typer` or `rich`, and every `git` call takes the caller's timeout.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from wfctl import _paths, _review_config
from wfctl._io import append_event, write_atomic
from wfctl._review_config import Group, Reviewer

TRUNK_MESSAGE = "can't find the trunk branch; set trunk in wfctl.json"

# Matched with `fullmatch`, never `match` and `$`, since `$` also matches
# before a trailing newline and the id becomes a file name.
REVIEWER_ID = re.compile(r"[a-z][0-9]+")

# Seven hex digits is what `git log --oneline` prints, so it is what a reviewer
# copies. Anything shorter can match more than one commit.
_MIN_SHA = 7
_REVIEWED = re.compile(r"^[^A-Za-z0-9\n]*Reviewed:[*_` \t]*([0-9A-Fa-f]+)", re.M)

# The anchor `fanning-out-code-review` has used since #368. It allows
# decoration before the word, so `**Verdict: Approve**` and `## Verdict` both
# count, and refuses other words, so prose that mentions a verdict doesn't.
_VERDICT_ANCHOR = re.compile(r"^[^A-Za-z]*Verdict")
# No letter before the word, so `Disapprove` isn't read as `Approve`. Nothing
# is required after it, so `Approved` and `_Approve_` still count.
_VERDICT_WORD = re.compile(r"(?<![A-Za-z])(?:Approve|Request changes)", re.I)
_FENCE = re.compile(r"`{3,}|~{3,}")

_RELAYED = "Relayed: "

# A file under `os.devnull` can't exist, so git reads no grafts and says
# nothing. `os.devnull` itself works too, but git then prints its grafts
# deprecation hint on stderr, and `_git` puts stderr in every error it raises.
_NO_GRAFTS = os.path.join(os.devnull, "grafts")

# A fetch refspec with one of these sources fetches every branch, so
# `origin/HEAD` can name the trunk rather than the one branch a clone took.
_EVERY_BRANCH = ("refs/heads/*", "refs/*")


class ReviewError(Exception):
    """A question git or a record couldn't answer. The message names which."""


class NoTrunk(ReviewError):
    def __init__(self, message: str = TRUNK_MESSAGE) -> None:
        super().__init__(message)


class ShallowClone(ReviewError):
    def __init__(self) -> None:
        super().__init__(
            "this clone is shallow, so wfctl can't see every commit on the branch; "
            "run git fetch --unshallow"
        )


class NoRun(ReviewError):
    def __init__(self, group: str) -> None:
        super().__init__(f"{group} has no run; run wfctl review start {group}")


class RoundCapReached(ReviewError):
    """A group has used the rounds `review.rounds` allows, and a commit is left
    that no sign-off covers.

    The first line follows the count and the cap, so a lowered cap and a cap of
    0 don't read as "run 4 of 3".
    """

    def __init__(self, group: str, rounds: int, cap: int) -> None:
        self.group = group
        self.rounds = rounds
        self.cap = cap
        if cap == 0:
            message = f"review.rounds is 0, so {group} doesn't run on this branch"
        elif rounds > cap:
            message = (
                f"{group} has run {rounds} rounds on this branch, "
                f"more than the {cap} review.rounds allows"
            )
        else:
            message = (
                f"{group} has run {rounds} of {cap} rounds on this branch, "
                "the most review.rounds allows"
            )
        super().__init__(message)


class RelayRefused(ReviewError):
    """A relay wfctl won't save. The message is the line the person reads."""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(
    repo_root: Path,
    *args: str,
    timeout: float | None,
    answers: tuple[int, ...] = (0,),
    honor_grafts: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run git in `repo_root`. An exit code outside `answers` is an error.

    `merge-base --is-ancestor` and `show-ref --verify` exit 1 to say no, which
    is an answer rather than a failure, so their callers pass `(0, 1)`.

    `--no-replace-objects` because a replace ref made with `git replace
    --graft` rewrites a commit's parents, and `rev-list` then skips the commits
    it cut out, so a completed run would mark them reviewed unseen. A
    `.git/info/grafts` line does the same, and `--no-replace-objects` doesn't
    turn it off, so `GIT_GRAFT_FILE` points at a file that can't exist.
    `commit_range` refuses both before it lists anything, since a reviewer's
    git reads them, and these keep wfctl's own reads on the real objects.
    `honor_grafts` leaves the caller's `GIT_GRAFT_FILE` alone, for the one
    call that asks git which grafts file a reviewer's git reads.
    """
    env = dict(os.environ) if honor_grafts else {**os.environ, "GIT_GRAFT_FILE": _NO_GRAFTS}
    r = subprocess.run(
        ["git", "--no-replace-objects", *args],
        cwd=repo_root, capture_output=True, text=True, timeout=timeout, env=env,
    )
    if r.returncode not in answers:
        detail = r.stderr.strip() or f"exit {r.returncode}"
        raise ReviewError(f"git {args[0]} failed: {detail}")
    return r


# --- the commits a run covers ----------------------------------------------------


@dataclass(frozen=True)
class Range:
    """The commits a group hasn't reviewed, newest first, and the commit they
    follow."""

    base: str
    commits: tuple[str, ...]


def head_commit(repo_root: Path, timeout: float | None = None) -> str:
    return _git(repo_root, "rev-parse", "HEAD", timeout=timeout).stdout.strip()


def _has_ref(repo_root: Path, ref: str, timeout: float | None) -> bool:
    found = _git(
        repo_root, "show-ref", "--verify", "--quiet", ref, timeout=timeout, answers=(0, 1),
    )
    return found.returncode == 0


@dataclass(frozen=True)
class ReviewTrunk:
    """The trunk reviews measure against.

    `source` is the ref whose `wfctl.json` named it, such as `origin/main`, and
    None when the trunk came from the working tree's resolution instead.
    `warnings` are the lines `review start` prints before any outcome.
    """

    name: str
    source: str | None
    warnings: tuple[str, ...]


def _read_config_at(
    repo_root: Path, ref: str, timeout: float | None,
) -> tuple[dict[str, object] | None, str | None]:
    """`wfctl.json` as it is on `ref`, and why it couldn't be read.

    `(None, None)` means the ref has no such file. `ls-tree` answers that
    first, since telling "no such path" from another `git show` failure would
    otherwise mean matching stderr text, and that wording changes between git
    versions. A real git failure raises rather than reading as "no file".
    """
    listed = _git(
        repo_root, "ls-tree", "--name-only", ref, "--", _review_config.CONFIG_PATH,
        timeout=timeout,
    ).stdout.strip()
    if not listed:
        return None, None
    text = _git(
        repo_root, "show", f"{ref}:{_review_config.CONFIG_PATH}", timeout=timeout,
    ).stdout
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return None, f"{e.msg} at line {e.lineno}"
    if not isinstance(data, dict):
        return None, "it isn't a JSON object"
    return data, None


def _origin_fetches_every_branch(repo_root: Path, timeout: float | None) -> tuple[bool, list[str]]:
    """Whether `origin` fetches every branch, and the sources it does fetch."""
    specs = _git(
        repo_root, "config", "--get-all", "remote.origin.fetch",
        timeout=timeout, answers=(0, 1),
    ).stdout.split()
    sources = [spec.removeprefix("+").split(":", 1)[0] for spec in specs]
    return any(source in _EVERY_BRANCH for source in sources), sources


def review_trunk(
    repo_root: Path, timeout: float | None = None, *, branch: str | None = None,
) -> ReviewTrunk:
    """The trunk reviews measure against, read from `wfctl.json` on the
    repository's default branch rather than the branch under review.

    The agent can edit the branch's own `trunk`, and `commit_range` leaves out
    every commit the trunk has, so a trunk the branch chose could hide its
    commits from the PR check and raise its own cap. The default branch is the
    one `origin/HEAD` names, which the agent can't push to
    (`review-round-cap`). A branch that names a different trunk gets a warning,
    and the review goes on against the default branch's.

    Without `origin/HEAD`, or when `origin` doesn't fetch every branch, there is
    no default branch to trust, so today's resolution applies and the working
    tree's `trunk` still decides. A working-tree trunk the clone lacks, or one
    that isn't a branch name, raises `NoTrunk`, which is what the guard's
    `_judge` does with it too.
    """
    name, problems = _paths.declared_trunk(repo_root)
    default = _git(
        repo_root, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD",
        timeout=timeout, answers=(0, 1),
    ).stdout.strip()
    if not default or not _origin_fetches_every_branch(repo_root, timeout)[0]:
        trunk = _paths.trunk_branch(repo_root, timeout=timeout)
        if trunk is None:
            raise NoTrunk()
        return ReviewTrunk(trunk, None, ())

    short = default.removeprefix("origin/")
    if not _has_ref(repo_root, f"refs/remotes/{default}", timeout):
        raise ReviewError(
            f"origin/HEAD names {default}, which this clone doesn't have; "
            "run git remote set-head origin --auto"
        )
    where = f"wfctl.json on {default}"
    warnings: list[str] = []
    used = default
    data, reason = _read_config_at(repo_root, f"refs/remotes/{default}", timeout)
    if reason is not None:
        warnings.append(f"can't read wfctl.json on {default} ({reason}); wfctl reviews against {short}")
    elif data is not None and _paths.TRUNK_KEY in data:
        declared = data[_paths.TRUNK_KEY]
        if not isinstance(declared, str) or not declared.strip() or declared == "HEAD":
            warnings.append(f"trunk on {default} isn't a branch name; wfctl reviews against {short}")
        else:
            used = _paths.resolve_declared(repo_root, declared, timeout=timeout) or ""
            if not used:
                raise NoTrunk(
                    f"can't find the trunk branch {declared}; check trunk in {where}, "
                    "or run git fetch"
                )

    if problems:
        raise NoTrunk()
    if name is not None:
        if branch is not None and name == branch:
            raise ReviewError(
                f"the trunk branch is {name}, the branch under review; "
                f"check trunk in {_review_config.CONFIG_PATH}"
            )
        mine = _paths.resolve_declared(repo_root, name, timeout=timeout)
        if mine is None:
            raise NoTrunk()
        if mine.removeprefix("origin/") != used.removeprefix("origin/"):
            warnings.append(
                f"this branch sets trunk to {name}, but wfctl reads "
                f"{used.removeprefix('origin/')} from {default} until the change merges"
            )
    return ReviewTrunk(used, default, tuple(warnings))


def trunk_refs(
    repo_root: Path, timeout: float | None = None, *, branch: str | None = None,
) -> list[str]:
    """The trunk branch on `origin` and its local branch, each when it exists,
    by full ref name.

    The trunk comes from `review_trunk`: the default branch's `wfctl.json`, or
    today's resolution where the clone has no default branch to trust. A
    declared trunk decides only on that fallback path.

    The remote ref comes first because a person's local `main` usually trails
    it, and excluding only the local branch would list everything merged since
    as the branch's own work. The local one is added because a commit can reach
    the local `main` before it is pushed. `_paths.trunk_branch` names either
    one, since a remote added with `git remote add` has no `origin/HEAD` and
    the trunk then resolves to the local name, so both are looked up.

    Full names because git resolves a short `main` to a tag of that name before
    the branch, and a tag on one of the branch's own commits made that work read
    as already on the trunk. A trunk found under neither name raises `NoTrunk`
    for the same reason: a clone that fetched only the feature branch has no
    `main` branch, and `_paths.trunk_branch` then finds the tag.

    The trunk has to be a different branch from the one under review, since
    every commit on the trunk is left out of the range. `branch` is the branch
    under review, and the caller passes it because the merge gate judges other
    branches from the `main` checkout, where the checked-out branch is the
    trunk (`642-commit-range-takes-judged-branch.md`).

    A name check can't catch a clone made with `--single-branch --branch
    <feature>` after a rename or on a detached HEAD. In such a clone,
    `origin/HEAD` can only name the branch the clone took, so a trunk found
    through it is refused unless `origin` fetches every branch. A declared
    trunk is used either way (`642-origin-head-trusted-on-full-fetch.md`).
    """
    found = review_trunk(repo_root, timeout, branch=branch)
    local = found.name.removeprefix("origin/")
    if branch is not None and local == branch:
        where = f"wfctl.json on {found.source}" if found.source else "wfctl.json"
        raise ReviewError(
            f"the trunk branch is {local}, the branch under review; check trunk in {where}"
        )
    if (
        found.source is None
        and found.name.startswith("origin/")
        and _paths.declared_trunk(repo_root)[0] is None
    ):
        _refuse_a_single_branch_clone(repo_root, local, timeout)
    refs = [
        ref for ref in (f"refs/remotes/origin/{local}", f"refs/heads/{local}")
        if _has_ref(repo_root, ref, timeout)
    ]
    if not refs:
        raise NoTrunk()
    return refs


@dataclass(frozen=True)
class TrunkRounds:
    """The cap read from the trunk, the short name of the ref it was read from,
    and a warning when the trunk's value couldn't be used."""

    cap: int
    ref: str
    warning: str | None


def trunk_rounds(
    repo_root: Path, timeout: float | None = None, *, branch: str | None = None,
) -> TrunkRounds:
    """The round cap from `wfctl.json` on the trunk `trunk_refs` returns first.

    That is the ref `commit_range` measures from, so the cap and the commit
    range come from the same trunk. A trunk with no file, no `review` key, or no
    `rounds` key gets the default without a warning, since the repository never
    set one. A value that can't be used gets the default and a warning, since a
    refusal would stop every review in the repository until the trunk was fixed.
    """
    ref = trunk_refs(repo_root, timeout, branch=branch)[0]
    short = ref.removeprefix("refs/remotes/").removeprefix("refs/heads/")
    fallback = _review_config.DEFAULT_ROUNDS
    data, reason = _read_config_at(repo_root, ref, timeout)
    if reason is not None:
        return TrunkRounds(
            fallback, short,
            f"can't read wfctl.json on {short} ({reason}); wfctl uses the default of {fallback}",
        )
    if data is None or "review" not in data:
        return TrunkRounds(fallback, short, None)
    review = data["review"]
    cap, problem = (
        _review_config.parse_rounds(review) if isinstance(review, dict)
        else (None, "not an object")
    )
    if problem is not None:
        return TrunkRounds(
            fallback, short,
            f"review.rounds on {short} isn't a whole number of 0 or more; "
            f"wfctl uses the default of {fallback}",
        )
    return TrunkRounds(fallback if cap is None else cap, short, None)


def _refuse_a_single_branch_clone(repo_root: Path, trunk: str, timeout: float | None) -> None:
    """Raise when `origin` fetches only some branches, so `origin/HEAD` can
    name the branch under review rather than the trunk."""
    every, sources = _origin_fetches_every_branch(repo_root, timeout)
    if every:
        return
    fetched = ", ".join(s.removeprefix("refs/heads/") for s in sources)
    what = f"only {fetched}" if fetched else "no branch"
    raise ReviewError(
        f"this clone fetches {what} from origin, so wfctl can't tell whether "
        f"{trunk} is the trunk; run git remote set-branches --add origin <trunk> and "
        "git fetch, then set trunk in wfctl.json"
    )


def is_commit(repo_root: Path, sha: str, timeout: float | None) -> bool:
    """Whether this repository has the commit. One it has never seen is no
    ancestor of anything, and asking `merge-base` about it is an error rather
    than a no."""
    r = _git(
        repo_root, "cat-file", "-e", f"{sha}^{{commit}}", timeout=timeout, answers=(0, 1, 128),
    )
    return r.returncode == 0


def _is_ancestor(repo_root: Path, older: str, newer: str, timeout: float | None) -> bool:
    r = _git(
        repo_root, "merge-base", "--is-ancestor", older, newer,
        timeout=timeout, answers=(0, 1),
    )
    return r.returncode == 0


def commit_range(
    repo_root: Path,
    head: str,
    last_reviewed: str | None,
    timeout: float | None = None,
    *,
    branch: str | None = None,
) -> Range:
    """The commits a group hasn't reviewed at `head` (research.md R3).

    The range starts at the last reviewed commit when it is an ancestor of the
    head, and at the merge base with the trunk otherwise. A rebase leaves the
    last reviewed commit off the branch, and starting there would list commits
    from a history the branch no longer has. Falling back costs one larger
    review and lets nothing through.

    A head that is the last reviewed commit, or one of its ancestors, has
    nothing to review. That happens when reviewed commits aren't pushed yet and
    a merge is judged at the pushed head, and every ancestor of a reviewed
    commit was covered by an earlier complete run.

    `--not` drops every commit that came in from the trunk, and a merge is
    dropped only when git would have made it on its own, so merging `main`
    doesn't force a round. A conflict resolution exists only in the merge
    commit, and dropping every merge would leave it unreviewed. Each merge in
    the range costs up to three more git calls, each under the same timeout.

    The arguments end with `--`, since git otherwise reads a bare `main` as a
    path when one exists and refuses the range as ambiguous.

    A shallow clone is refused. `rev-list` can't list commits past the cut, so
    a completed run would mark them reviewed unseen. A merge whose parents'
    nearest shared commit was cut is also redone against an older base, which
    can match a merge that kept a file `main` deleted.

    `branch` is the branch under review, and `trunk_refs` refuses a trunk of
    the same name. A caller that leaves it out gets no such check.
    """
    shallow = _git(repo_root, "rev-parse", "--is-shallow-repository", timeout=timeout)
    if shallow.stdout.strip() == "true":
        raise ShallowClone()
    _refuse_rewritten_history(repo_root, timeout)
    refs = trunk_refs(repo_root, timeout, branch=branch)
    base = None
    if last_reviewed is not None and is_commit(repo_root, last_reviewed, timeout):
        if _is_ancestor(repo_root, head, last_reviewed, timeout):
            return Range(last_reviewed, ())
        if _is_ancestor(repo_root, last_reviewed, head, timeout):
            base = last_reviewed
    if base is None:
        base = _git(repo_root, "merge-base", head, refs[0], timeout=timeout).stdout.strip()
    listed = _git(
        repo_root, "rev-list", "--parents", f"{base}..{head}", "--not", *refs, "--",
        timeout=timeout,
    ).stdout.splitlines()
    commits = []
    for line in listed:
        sha, *parents = line.split()
        if len(parents) < 2 or _has_own_edits(repo_root, sha, parents, timeout):
            commits.append(sha)
    return Range(base, tuple(commits))


def _refuse_rewritten_history(repo_root: Path, timeout: float | None) -> None:
    """Raise when a replace ref or a grafts file can change what a reviewer
    reads.

    wfctl lists commits with both turned off, and each reviewer reads a listed
    commit with plain `git show`, which honors both. A replaced commit, tree,
    or file shows other content. A graft onto a parent with the commit's own
    tree shows an empty diff, and one that cuts commits out shows them all as
    one diff. Any of these leaves the real change unread, so any replace ref or
    grafts file is refused rather than judged one at a time
    (`642-range-refuses-replace-refs-and-grafts.md`).

    `git replace -l` lists the namespace the reviewer's git reads, which
    `GIT_REPLACE_REF_BASE` can move. Every name counts, since git honors more
    than a bare object id: it reads the part after the last `/`, in either
    case, and ignores what follows the id. The remedy deletes each ref by its
    full name, which `git replace -d` can't reach for every name, and quotes
    it, since a ref name can hold characters a shell reads. It runs one
    `update-ref -d` per ref, because that command reads a second name as the
    value the first must hold, and passes `--no-deref`, because a symbolic
    replace ref would otherwise take its target branch with it. An empty base
    makes every ref in the repository a replace ref, so its remedy clears the
    variable rather than deleting branches.

    `--git-path info/grafts` names the file `GIT_GRAFT_FILE` points at,
    resolved from the top of the worktree the way git resolves it, or
    `info/grafts` in the common directory. An empty `GIT_GRAFT_FILE` reads no
    grafts file, and `--git-path` refuses it.
    """
    replaced = _git(repo_root, "replace", "-l", timeout=timeout).stdout.split()
    if replaced:
        base = os.environ.get("GIT_REPLACE_REF_BASE", "refs/replace/")
        remedy = "unset GIT_REPLACE_REF_BASE" if not base else " && ".join(
            f"git update-ref --no-deref -d {shlex.quote(base + name)}" for name in replaced
        )
        raise ReviewError(
            f"this repository has replace refs, so a reviewer's git show reads content other "
            f"than the commit's; remove each with {remedy}"
        )
    named = os.environ.get("GIT_GRAFT_FILE")
    if named == "":
        return
    # Only git's own line ending comes off, since a path can end in a space.
    grafts = Path(_git(
        repo_root, "rev-parse", "--path-format=absolute", "--git-path", "info/grafts",
        timeout=timeout, honor_grafts=True,
    ).stdout.removesuffix("\n"))
    # Bytes, since git reads the file as bytes and any content at all refuses.
    try:
        content = grafts.read_bytes()
    except (FileNotFoundError, NotADirectoryError):
        return
    except OSError as e:
        raise ReviewError(f"can't read {grafts}: {e}") from e
    if content:
        remedy = "unset GIT_GRAFT_FILE" if named else f"delete {grafts}"
        raise ReviewError(
            f"{grafts} grafts commits onto other parents, so a reviewer's git show reads "
            f"changes other than the commit's own; {remedy}"
        )


def _has_own_edits(
    repo_root: Path, merge: str, parents: list[str], timeout: float | None,
) -> bool:
    """Whether a merge differs from the one git makes from its parents unaided.

    `merge-tree` redoes the merge and exits 1 on a conflict, so any conflict
    counts, whichever side the person kept. A clean redo whose tree differs
    from the merge's own is a merge someone edited, `-s ours` included, which
    drops the trunk's changes without a conflict. `diff-tree --cc` answered
    this before and got both wrong: a conflict resolved by keeping one side
    printed nothing, and a clean merge of nearby lines printed a hunk.

    A merge with more than two parents has no single redo to compare against,
    so it stays in the range.

    A merge whose parents share no commit, such as a merged orphan branch,
    stays in the range too. `merge-tree` refuses to redo such a merge, and
    `--allow-unrelated-histories` would redo it against an empty base instead,
    which can't show that the merge kept a file one side deleted.
    """
    if len(parents) != 2:
        return True
    shared = _git(repo_root, "merge-base", *parents, timeout=timeout, answers=(0, 1))
    if shared.returncode == 1:
        return True
    redone = _git(
        repo_root, "merge-tree", "--write-tree", *parents, timeout=timeout, answers=(0, 1),
    )
    if redone.returncode == 1:
        return True
    own = _git(repo_root, "rev-parse", f"{merge}^{{tree}}", timeout=timeout).stdout.strip()
    return redone.stdout.split("\n", 1)[0].strip() != own


# --- records ---------------------------------------------------------------------


def group_dir(agent_dir: Path, group: str) -> Path:
    return agent_dir / "reviews" / group


def _read_json(path: Path) -> dict[str, object]:
    """A record wfctl wrote, or a `ReviewError` naming the file.

    A half-written or hand-edited record is an error rather than a missing one.
    Read as missing, a broken `last-reviewed.json` would restart the range at
    the merge base and look like a reset nobody asked for.
    """
    try:
        data = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ReviewError(f"can't read {path}: {e}") from e
    if not isinstance(data, dict):
        raise ReviewError(f"can't read {path}: not a JSON object")
    return data


def last_reviewed(agent_dir: Path, group: str) -> str | None:
    """The group's last reviewed commit, or None when no run has completed."""
    path = group_dir(agent_dir, group) / "last-reviewed.json"
    if not path.exists():
        return None
    sha = _read_json(path).get("sha")
    if not isinstance(sha, str) or not sha:
        raise ReviewError(f"can't read {path}: no sha")
    return sha


@dataclass(frozen=True)
class Run:
    number: int
    path: Path
    record: dict[str, object]

    @property
    def head(self) -> str:
        return str(self.record["head"])

    @property
    def reviewers(self) -> list[dict[str, str]]:
        found = self.record.get("reviewers")
        return [r for r in found if isinstance(r, dict)] if isinstance(found, list) else []


def _run_numbers(agent_dir: Path, group: str) -> list[int]:
    """The numbers of `group`'s runs, lowest first.

    A folder with no `run.json` is a start that was interrupted, or one still
    writing, and isn't a run. `latest_run` and `runs_started` share this rule,
    so the count and the next run number can't disagree about how many runs
    there have been.
    """
    runs = group_dir(agent_dir, group) / "runs"
    if not runs.is_dir():
        return []
    return sorted(
        int(p.name) for p in runs.glob("[0-9][0-9][0-9]*")
        if p.name.isdigit() and (p / "run.json").is_file()
    )


def runs_started(agent_dir: Path, group: str) -> int:
    """How many runs `group` has started on this branch, finished or not.

    The round cap limits starts. A run that got no reports still cost a round,
    and counting only complete runs would let an agent start runs without ever
    reaching the cap. Derived from the run folders on every call and stored
    nowhere (`review-round-count`).
    """
    return len(_run_numbers(agent_dir, group))


def latest_run(agent_dir: Path, group: str) -> Run | None:
    """The highest-numbered run of `group`, or None when it has never started.

    `check` and `relay` act on this run only. An earlier run that never
    completed stays on disk for reading, and its reports never count toward a
    later one.

    A folder with no `run.json` is a start that was interrupted, or one still
    writing, and is passed over. Read as the latest run, it would fail every
    `start`, `check` and `relay` on the group until someone deleted it.
    """
    numbers = _run_numbers(agent_dir, group)
    if not numbers:
        return None
    path = group_dir(agent_dir, group) / "runs" / f"{numbers[-1]:03d}"
    record = _read_json(path / "run.json")
    if not isinstance(record.get("head"), str):
        raise ReviewError(f"can't read {path / 'run.json'}: no head")
    return Run(numbers[-1], path, record)


# --- start -----------------------------------------------------------------------


@dataclass(frozen=True)
class Started:
    """What `review start` did. `run` is None when the group was up to date."""

    group: str
    base: str
    head: str
    commits: tuple[str, ...]
    run: Run | None
    reviewers: tuple[dict[str, str], ...]
    # Each model that can't run, with the reason, in the order the group lists it.
    unavailable: dict[str, str]
    # Runs the group had started before this call, so a header reads `rounds + 1`.
    rounds: int
    # The commit a sign-off covered the range through when the group was at its
    # cap and no run was written, otherwise None.
    sign_off: str | None

    @property
    def expected(self) -> list[str]:
        return [r["id"] for r in self.reviewers if r["state"] == "expected"]


def _availability(
    reviewers: Sequence[Reviewer], which: Callable[[str], str | None],
) -> tuple[list[dict[str, str]], dict[str, str]]:
    """Each reviewer as `run.json` records it, and why each missing model can't run.

    wfctl looks a model's command up on `PATH` itself, so the coordinator can't
    simply declare a reviewer unavailable. The lookup runs on the agent's
    `PATH`, which the agent can change, so this is visible rather than
    enforced: the roster and the `⚠` line both name a model left out
    (research.md R7).
    """
    unavailable: dict[str, str] = {}
    entries: list[dict[str, str]] = []
    for r in reviewers:
        entry = {"id": r.id, "model": r.model, "state": "expected"}
        if r.command is not None:
            entry["command"] = r.command
            if r.model not in unavailable:
                # `_review_config.load` refuses a command `shlex` can't split.
                program = (shlex.split(r.command) or [""])[0]
                if not program or which(program) is None:
                    unavailable[r.model] = f"`{program}` not found on PATH"
            if r.model in unavailable:
                entry["state"] = "unavailable"
                entry["reason"] = unavailable[r.model]
        entries.append(entry)
    return entries, unavailable


def start(
    repo_root: Path,
    agent_dir: Path,
    group: Group,
    *,
    timeout: float | None = None,
    which: Callable[[str], str | None] | None = None,
    branch: str | None = None,
    cap: int,
) -> Started:
    """Write the next run record for `group`, or nothing when it's up to date.

    A run is never started with no commits, since there's nothing to review and
    a record would read as a review waiting on reports. A run where no reviewer
    can run is still written, and `check` never completes it.

    A group that has started `cap` runs gets another only through a sign-off.
    When the sign-off covers every commit left, nothing is written and
    `Started.sign_off` names it. Otherwise this raises `RoundCapReached`. The
    range comes first, so a group with nothing left to review is up to date
    rather than refused.

    `cap` has no default, so a caller can't skip it without saying so.
    """
    head = head_commit(repo_root, timeout)
    found = commit_range(
        repo_root, head, last_reviewed(agent_dir, group.name), timeout, branch=branch,
    )
    # Resolved when called rather than bound as the default, so `shutil.which`
    # is whatever the module holds at the time.
    reviewers, unavailable = _availability(group.reviewers, which or shutil.which)
    rounds = runs_started(agent_dir, group.name)
    if not found.commits:
        return Started(
            group.name, found.base, head, (), None, tuple(reviewers), unavailable, rounds, None,
        )
    if rounds >= cap:
        signed, is_covered = _covered_by_sign_off(repo_root, agent_dir, timeout)
        if signed is None or not all(is_covered(c) for c in found.commits):
            raise RoundCapReached(group.name, rounds, cap)
        return Started(
            group.name, found.base, head, (), None, tuple(reviewers), unavailable,
            rounds, signed,
        )

    runs = group_dir(agent_dir, group.name) / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    previous = latest_run(agent_dir, group.name)
    number = (previous.number if previous else 0) + 1
    # `exist_ok=False` so two starts racing for one number can't share a folder.
    while True:
        path = runs / f"{number:03d}"
        try:
            path.mkdir()
            break
        except FileExistsError:
            number += 1
    record: dict[str, object] = {
        "group": group.name,
        "run": number,
        "base": found.base,
        "head": head,
        "commits": list(found.commits),
        "reviewers": reviewers,
        "started_at": _now(),
        "completed_at": None,
    }
    write_atomic(path / "run.json", json.dumps(record, indent=2) + "\n")
    started = Started(
        group.name, found.base, head, found.commits, Run(number, path, record),
        tuple(reviewers), unavailable, rounds, None,
    )
    append_event(
        agent_dir, "review-start", group=group.name, run=number, head=head,
        reviewers=len(started.expected),
    )
    return started


# --- reports ---------------------------------------------------------------------


def judge(text: str, head: str) -> str | None:
    """None when a report counts, or the reason it doesn't (research.md R2).

    A report counts when a `Reviewed: <sha>` line names the run's head, with at
    least seven digits, and its last non-blank line holds `Approve` or
    `Request changes` with the verdict anchor on that line or the non-blank
    line before it. The verdict has to be at the end, so a report cut off after
    an early mention of one carries none. The whole report is read, since a
    reviewer may put the `Reviewed:` line after its findings.
    """
    named = [m.group(1).lower() for m in _REVIEWED.finditer(text)]
    if not named:
        return "no Reviewed: line"
    if not any(len(sha) >= _MIN_SHA and head.lower().startswith(sha) for sha in named):
        return f"names {named[-1][:_MIN_SHA]}, not {head[:_MIN_SHA]}"
    # A reviewer that wraps its report in a code fence ends on the fence, and
    # the verdict is the line inside it.
    lines = [
        line for line in text.splitlines() if line.strip() and not _FENCE.fullmatch(line.strip())
    ]
    last = lines[-1] if lines else ""
    before = lines[-2] if len(lines) > 1 else ""
    if not _VERDICT_WORD.search(last) or not (
        _VERDICT_ANCHOR.match(last) or _VERDICT_ANCHOR.match(before)
    ):
        return "no verdict at the end"
    return None


def _relay_reason(text: str) -> str | None:
    first = text.split("\n", 1)[0]
    return first.removeprefix(_RELAYED).strip() if first.startswith(_RELAYED) else None


@dataclass(frozen=True)
class Entry:
    """One line of the roster. `note` is the reason a report didn't count, or
    the relay reason on a report that did. `expected` is False for a reviewer
    whose model couldn't run, which the run doesn't wait for."""

    id: str
    model: str
    counted: bool
    note: str | None
    expected: bool = True


@dataclass(frozen=True)
class Checked:
    group: str
    run: Run
    entries: tuple[Entry, ...]
    expected: int
    complete: bool

    @property
    def missing(self) -> int:
        return sum(1 for e in self.entries if e.expected and not e.counted)


def _roster(run: Run) -> list[Entry]:
    entries: list[Entry] = []
    for r in run.reviewers:
        rid, model = str(r.get("id", "?")), str(r.get("model", "?"))
        if r.get("state") == "unavailable":
            entries.append(
                Entry(rid, model, False, f"unavailable: {r.get('reason', '')}", expected=False)
            )
            continue
        path = run.path / f"{rid}.md"
        if not REVIEWER_ID.fullmatch(rid) or not path.is_file():
            entries.append(Entry(rid, model, False, "no report"))
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError as e:
            entries.append(Entry(rid, model, False, f"can't read report: {e.strerror}"))
            continue
        reason = judge(text, run.head)
        if reason is not None:
            entries.append(Entry(rid, model, False, reason))
            continue
        relayed = _relay_reason(text)
        entries.append(Entry(rid, model, True, f"relayed: {relayed}" if relayed else None))
    return entries


def check(agent_dir: Path, group: str) -> Checked:
    """Judge the latest run's reports and complete the run when every expected
    reviewer has a counted report.

    The expected reviewers come from the run record, never from the config. A
    config read again here would let a repository drop a reviewer whose report
    was bad and complete the run without it.

    Completion moves `last-reviewed.json` to the run's head, then sets
    `completed_at` and changes nothing else in the run record. A run already
    complete is judged again and left as it is, so `check` is safe to run
    twice. The order matters for a write that fails halfway: a run marked
    complete is never completed again, so `last-reviewed.json` goes first, and
    a failure before the second write leaves a run the next `check` completes.

    A run stays complete when a report changes afterwards. The last reviewed
    commit has already moved, so calling the run incomplete again would
    contradict the record the next run starts from. The roster still shows the
    changed report, and `missing` counts it.
    """
    run = latest_run(agent_dir, group)
    if run is None:
        raise NoRun(group)
    entries = _roster(run)
    expected = sum(1 for e in entries if e.expected)
    if run.record.get("completed_at") is not None:
        return Checked(group, run, tuple(entries), expected, True)
    complete = expected > 0 and all(e.counted for e in entries if e.expected)
    if complete:
        at = _now()
        record = {**run.record, "completed_at": at}
        write_atomic(
            group_dir(agent_dir, group) / "last-reviewed.json",
            json.dumps({"sha": run.head, "run": run.number, "at": at}, indent=2) + "\n",
        )
        write_atomic(run.path / "run.json", json.dumps(record, indent=2) + "\n")
        append_event(agent_dir, "review-complete", group=group, run=run.number, head=run.head)
        run = Run(run.number, run.path, record)
    return Checked(group, run, tuple(entries), expected, complete)


# --- sign-off and what is still unreviewed ---------------------------------------


def sign_off_path(agent_dir: Path) -> Path:
    return agent_dir / "reviews" / "sign-off.json"


def signed_off(agent_dir: Path) -> str | None:
    """The commit a person last signed off through, or None."""
    path = sign_off_path(agent_dir)
    if not path.exists():
        return None
    sha = _read_json(path).get("sha")
    if not isinstance(sha, str) or not sha:
        raise ReviewError(f"can't read {path}: no sha")
    return sha


def sign_off(agent_dir: Path, sha: str) -> None:
    """Record a person's sign-off through `sha`, replacing any earlier one.

    One file for every group, since a sign-off is one decision about the
    branch, and making a person sign once per group adds nothing (research.md
    R9).
    """
    path = sign_off_path(agent_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(path, json.dumps({"sha": sha, "at": _now()}, indent=2) + "\n")
    append_event(agent_dir, "review-sign-off", sha=sha)


def _covered_by_sign_off(
    repo_root: Path, agent_dir: Path, timeout: float | None,
) -> tuple[str | None, Callable[[str], bool]]:
    """The commit a person signed off through, and a function that says whether
    that sign-off covers a given commit.

    A sign-off covers a commit when it is the signed-off commit or one of its
    ancestors. One naming a commit this repository has never seen covers
    nothing, since `merge-base` errors on an unknown commit rather than saying
    no. `unreviewed` and `start` both ask this, so `review start` and the
    worktree guard can't disagree about what a sign-off covers.
    """
    signed = signed_off(agent_dir)
    if signed is not None and not is_commit(repo_root, signed, timeout):
        signed = None
    covered: dict[str, bool] = {}

    def is_covered(sha: str) -> bool:
        if signed is None:
            return False
        if sha not in covered:
            covered[sha] = sha == signed or _is_ancestor(repo_root, sha, signed, timeout)
        return covered[sha]

    return signed, is_covered


def unreviewed(
    repo_root: Path,
    agent_dir: Path,
    groups: Sequence[Group],
    head: str,
    timeout: float | None = None,
    *,
    branch: str | None = None,
) -> dict[str, tuple[str, ...]]:
    """Each group's commits at `head` that no complete run and no sign-off
    covers, oldest first. A group with none is left out.

    A sign-off covers a commit when it is the signed-off commit or one of its
    ancestors, so a commit added after the sign-off is unreviewed again. Every
    group has to have reviewed the head, so a fix the code group commits after
    the security group's run is unreviewed for `security`.
    """
    _, is_covered = _covered_by_sign_off(repo_root, agent_dir, timeout)

    found: dict[str, tuple[str, ...]] = {}
    for group in groups:
        commits = commit_range(
            repo_root, head, last_reviewed(agent_dir, group.name), timeout, branch=branch,
        ).commits
        left = tuple(c for c in reversed(commits) if not is_covered(c))
        if left:
            found[group.name] = left
    return found


def subjects(repo_root: Path, shas: Sequence[str], timeout: float | None = None) -> dict[str, str]:
    """Each commit's subject line, in one git call."""
    unique = list(dict.fromkeys(shas))
    if not unique:
        return {}
    shown = _git(
        repo_root, "show", "-s", "--no-walk=unsorted", "--format=%H%x00%s", *unique, "--",
        timeout=timeout,
    ).stdout
    return dict(line.split("\0", 1) for line in shown.splitlines() if "\0" in line)


def pending_lines(pending: dict[str, tuple[str, ...]], subjects: dict[str, str]) -> list[str]:
    """One line per unreviewed commit under its group, such as
    `security  9f8e7d6 test: cover an empty note`."""
    width = max((len(g) for g in pending), default=0)
    return [
        f"{group:<{width}}  {sha[:_MIN_SHA]} {subjects.get(sha, '')}".rstrip()
        for group, commits in pending.items()
        for sha in commits
    ]


def roster_lines(entries: Sequence[Entry]) -> list[str]:
    """One line per reviewer, such as `s2 claude ✓ relayed: write denied`.

    The model column is padded to the widest model in the run, so a ✓ or ✗
    lines up under the others.
    """
    id_width = max((len(e.id) for e in entries), default=0)
    width = max((len(e.model) for e in entries), default=0)
    lines = []
    for e in entries:
        mark = "✓" if e.counted else "✗"
        note = f" {e.note}" if e.note else ""
        lines.append(f"{e.id:<{id_width}} {e.model:<{width}} {mark}{note}")
    return lines


# --- relay -----------------------------------------------------------------------


def relay(
    agent_dir: Path, groups: Sequence[Group], reviewer: str, reason: str, text: str,
) -> str:
    """Save a blocked reviewer's report as that reviewer's, marked as relayed.

    The report is saved under the reviewer's id in its group's latest run, with
    a header naming the reason, so the roster can show a relay rather than pass
    it off as a report the reviewer wrote
    (`622-blocked-reviewer-relays-report.md`). The group is found by the id's
    letter, which no two groups share. Returns the reason as saved, collapsed to
    one line so it can't add a line to the header.
    """
    reason = " ".join(reason.split())
    if not reason:
        raise RelayRefused("a relay needs --reason saying why the reviewer couldn't write")
    group = next((g for g in groups if g.name[0] == reviewer[:1]), None)
    if group is None or not REVIEWER_ID.fullmatch(reviewer):
        raise RelayRefused(f"{reviewer} isn't a reviewer in any review group")
    run = latest_run(agent_dir, group.name)
    if run is None:
        raise NoRun(group.name)
    listed = {str(r.get("id")) for r in run.reviewers if r.get("state") == "expected"}
    if reviewer not in listed:
        raise RelayRefused(f"{reviewer} isn't a reviewer in {group.name} run {run.number:03d}")
    path = run.path / f"{reviewer}.md"
    if path.exists():
        raise RelayRefused(f"{reviewer} already has a report in run {run.number:03d}")
    write_atomic(path, f"{_RELAYED}{reason}\nRelayed-at: {_now()}\n\n{text}")
    append_event(
        agent_dir, "review-relay", group=group.name, run=run.number, id=reviewer, reason=reason,
    )
    return reason
