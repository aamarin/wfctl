"""Path resolution for wfctl state, branch, spec dir, and repo root."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from wfctl._manifest import load_manifest


_STATE_DIR_OVERRIDE = "WFCTL_STATE_DIR"
_BRANCH_OVERRIDE = "WFCTL_BRANCH"
_SPEC_DIR_OVERRIDE = "WFCTL_SPEC_DIR"
_ARCH_DIR_OVERRIDE = "WFCTL_ARCH_DIR"
_REPO_ROOT_OVERRIDE = "WFCTL_REPO_ROOT"

# Default issue-key shape: a plain leading number (GitHub / stock spec-kit).
# Trackers with non-numeric keys override this via "key_pattern" in their config.
DEFAULT_KEY_PATTERN = r"\d+"

# Prefix, not a whole line: a heading that deviates from the template
# ("Issue Grouping Map (revised)") would otherwise read as claiming no
# issues at all, and a feature that claims nothing is one the ancestor walk
# still inherits — which is #120 arriving through a typo.
_GROUPING_HEADING = re.compile(r"^#+[ \t]*Issue Grouping Map", re.M)


def extract_issue_key(branch: str, pattern: str) -> str:
    """Pull the issue key off the front of a branch name; 'unknown' if none.

    The key is `pattern` anchored at the start, with an *optional* slug: it may
    stand alone (`342`) or be followed by a `-`/`_` separator (`342-foo`,
    `PROJ-123_bar`). A bad pattern degrades to no match, never raises.
    """
    try:
        m = re.match(rf"^({pattern})(?:[-_]|$)", branch)
    except re.error:
        return "unknown"
    return m.group(1) if m else "unknown"


def get_repo_root() -> Path:
    """Return git repo root; raises SystemExit(1) if not in a git repo."""
    override = os.environ.get(_REPO_ROOT_OVERRIDE)
    if override:
        return Path(override)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        raise SystemExit("wfctl: not a git repository")


def resolve_branch(repo_root: Path) -> str:
    """Return branch name: WFCTL_BRANCH → git → short SHA → 'detached'."""
    override = os.environ.get(_BRANCH_OVERRIDE)
    if override:
        return override
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, check=True,
            cwd=repo_root,
        )
        branch = result.stdout.strip()
        if branch:
            return branch
        # Detached HEAD — return short SHA
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
            cwd=repo_root,
        )
        return r.stdout.strip() or "detached"
    except subprocess.CalledProcessError:
        return "detached"


def _trunk_branch(repo_root: Path) -> str | None:
    """The repo's trunk — origin/HEAD when the remote publishes it, else the
    first local main/master/dev that exists. None when nothing looks like one."""
    head = subprocess.run(
        ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        cwd=repo_root, capture_output=True, text=True,
    )
    if head.returncode == 0 and head.stdout.strip():
        return head.stdout.strip()
    for name in ("main", "master", "dev"):
        if subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", name],
            cwd=repo_root, capture_output=True,
        ).returncode == 0:
            return name
    return None


def _ancestor_branches(branch: str, repo_root: Path) -> list[str]:
    """Local branches other than `branch` that are git ancestors of it, nearest first.

    Covers the "epic planning branch as worktree base" convention: a child issue's
    worktree branches off its parent epic's planning branch (which carries
    specs/{feature}/), rather than off the target branch directly.

    Once a parent epic merges, its spec dir lives on the trunk and ancestry stops
    identifying it; the delivery.md "Issue Grouping Map" leg of `resolve_spec_dir`
    is what resolves a sub-issue's spec dir from that point on.
    """
    try:
        result = subprocess.run(
            ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads/"],
            capture_output=True, text=True, check=True, cwd=repo_root,
        )
    except subprocess.CalledProcessError:
        return []

    def commits_ahead(candidate: str) -> int | None:
        is_ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", candidate, branch],
            cwd=repo_root, capture_output=True,
        )
        if is_ancestor.returncode != 0:
            return None
        count = subprocess.run(
            ["git", "rev-list", "--count", f"{candidate}..{branch}"],
            capture_output=True, text=True, check=True, cwd=repo_root,
        )
        return int(count.stdout.strip())

    trunk = _trunk_branch(repo_root)

    def carries_own_work(candidate: str) -> bool:
        """Does `candidate` hold commits the trunk doesn't?

        Every branch descends from the trunk, so plain ancestry makes every
        *merged* branch an ancestor of every branch cut after it — and a merged
        feature branch still has its `specs/<its-name>/` in the tree, so the
        exact-name match in `resolve_spec_dir` hits it and hands back a finished
        story's pipeline. Nearest-first ranking doesn't save us: the trunk has no
        `specs/<trunk>` to match, so the walk sails past it into the merged
        siblings behind it.

        Carrying unmerged commits is what separates a live parent epic (it holds
        its own spec commit) from a merged or empty sibling (it holds nothing the
        trunk lacks). Robust to the trunk advancing, unlike comparing tips.
        """
        if trunk is None:
            return True
        r = subprocess.run(
            ["git", "rev-list", "--count", f"{trunk}..{candidate}"],
            cwd=repo_root, capture_output=True, text=True,
        )
        return r.returncode == 0 and r.stdout.strip() not in ("", "0")

    candidates = [
        b for b in result.stdout.split() if b and b != branch and carries_own_work(b)
    ]
    ranked = sorted(
        ((b, ahead) for b in candidates if (ahead := commits_ahead(b)) is not None),
        key=lambda pair: pair[1],
    )
    return [b for b, _ in ranked]


def _manifest_root(base: Path, key: str) -> Path | None:
    """The root `key` declares in the manifest at `base`, or None.

    A relative value anchors to `base` — the directory of the manifest that
    declared it — never the cwd, so one relative value means one shared location
    from every worktree. An empty value counts as not declared.

    Raises when the manifest exists but cannot be parsed. A malformed manifest is
    a broken repo, not a missing setting: defaulting silently would put specs
    back inside the worktree with no signal, which is the failure this exists to
    remove.
    """
    value = load_manifest(base).get(key)
    if not value:
        return None
    declared = Path(value).expanduser()
    return declared if declared.is_absolute() else (base / declared).resolve()


def worktree_branches(repo_root: Path) -> list[str]:
    """Branch names checked out across every worktree of this repo.

    Parsed as whole records rather than by scanning for `branch` lines, because
    a record says more than which branch it holds. A worktree whose directory
    was deleted outside `git worktree remove` keeps its entry and its branch,
    with `prunable` alongside — reading the branch alone reports a checkout that
    is not there, and a caller asking "is anyone else on this issue" then gets a
    yes that never becomes a no.

    Detached worktrees contribute nothing — `--porcelain` prints `detached`
    instead of a `branch` line — and a repo git cannot answer for returns an
    empty list. Both degrade the same way, to "nobody else", which is the answer
    that lets a caller act; the callers here are hooks that must not become
    gates. `prunable` degrades that way too, which is why it is dropped rather
    than counted.
    """
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repo_root, capture_output=True, text=True,
    )
    if result.returncode != 0:
        return []
    branches = []
    for record in result.stdout.split("\n\n"):
        fields = {}
        for line in record.splitlines():
            if line:
                key, _, value = line.partition(" ")
                fields[key] = value
        if "prunable" in fields:
            continue
        ref = fields.get("branch")
        if ref:
            branches.append(ref.removeprefix("refs/heads/"))
    return branches


def main_checkout(repo_root: Path) -> Path | None:
    """The project's main checkout as seen from `repo_root`, or None.

    None when `repo_root` *is* the main checkout (nothing to fall back to) and
    when the layout has no identifiable one.

    ponytail: identifies a main checkout only when the git common dir is named
    exactly `.git` — the standard non-bare layout. In a bare or separate-gitdir
    layout the common dir is `<name>.git` and its parent is a container
    directory that may hold an unrelated project's manifest; reading that would
    silently apply another repo's spec root, which is worse than not resolving.
    Those layouts get no fallback. If they ever need one, the upgrade path is
    `git rev-parse --is-bare-repository` plus an explicit setting, not loosening
    this check.
    """
    common = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        cwd=repo_root, capture_output=True, text=True,
    )
    if common.returncode != 0 or not common.stdout.strip():
        return None
    # Relative ('.git') from the main checkout, absolute from a worktree.
    git_dir = (repo_root / common.stdout.strip()).resolve()
    if git_dir.name != ".git":
        return None
    parent = git_dir.parent
    return None if parent == repo_root.resolve() else parent


def _root_declaration(repo_root: Path, key: str) -> tuple[Path, Path] | None:
    """`(root, declaring dir)` for the nearest manifest declaring `key`.

    The one walk both the resolver and its reporting command use, so what
    resolves and what gets reported as its source cannot drift apart — the
    report exists to answer "where did this come from", and a second copy of the
    rule is how that answer goes quietly wrong.

    Deliberately not a loop over `(repo_root, main_checkout(repo_root))`: that
    tuple evaluates `main_checkout` eagerly, spawning a `git rev-parse` even when
    this repo's own manifest answers. `feature-paths` runs on every speckit
    script invocation, so the saved subprocess is worth the extra branch.
    """
    declared = _manifest_root(repo_root, key)
    if declared is not None:
        return declared, repo_root
    main = main_checkout(repo_root)
    if main is not None:
        declared = _manifest_root(main, key)
        if declared is not None:
            return declared, main
    return None


def spec_root_declaration(repo_root: Path) -> tuple[Path, Path] | None:
    """`(root, declaring dir)` for the nearest manifest declaring `spec_root`."""
    return _root_declaration(repo_root, "spec_root")


def arch_root_declaration(repo_root: Path) -> tuple[Path, Path] | None:
    """`(root, declaring dir)` for the nearest manifest declaring `arch_root`."""
    return _root_declaration(repo_root, "arch_root")


def spec_root(repo_root: Path) -> Path:
    """The directory this repo's spec dirs live under.

    WFCTL_SPEC_DIR → `spec_root` in this repo's manifest → `spec_root` in the
    main checkout's manifest → `repo_root/specs`. The env var stays a
    per-invocation escape hatch: it is process-global, so exporting it from a
    shell profile would redirect every repo wfctl touches. The manifest is
    already per-repo, which is why the persistent setting lives there.

    The main checkout is consulted because the manifest is gitignored and
    `install-skills` regenerates it in every fresh worktree — so a
    worktree-local setting cannot exist at the moment the pipeline first runs
    there. Without that fallback the setting is unreachable exactly when it
    matters, and specs land in the worktree and die with it.

    The single decision point for both call sites — `resolve_spec_dir` (which
    locates existing spec dirs) and `feature_paths_cmd` (which names the one to
    create). They disagreed before: reads honored the override, creates were
    hardcoded, so specs could be read from outside the repo but never written
    there.

    ponytail: never checks that the root exists, and never creates it. A
    not-yet-existing directory is exactly the case that broke the create path —
    `resolve_spec_dir` returns None for it, and the hardcoded fallback took over.
    Adding a check back would rebuild the bug; `setup-plan.sh` already mkdir -p's
    the feature dir when it writes there.
    """
    override = os.environ.get(_SPEC_DIR_OVERRIDE)
    if override:
        return Path(override)
    found = spec_root_declaration(repo_root)
    return found[0] if found is not None else repo_root / "specs"


def arch_root(repo_root: Path) -> Path:
    """The directory this repo's architecture records live under.

    WFCTL_ARCH_DIR → `arch_root` in this repo's manifest → `arch_root` in the
    main checkout's manifest → `repo_root/docs/architecture`. Same order and
    same reasoning as `spec_root`, including its rule that resolution neither
    checks the root exists nor creates it — a repo has no records until it
    writes its first one, and the existence check is what broke the spec-root
    create path.

    The default differs from `spec_root`'s in kind, not just in name: specs are
    working artifacts a repo may well want outside the tree, while a record is
    the constraint the code is written under. In-tree keeps the two in one
    commit and puts them in front of anyone who clones. Out-of-tree is honoured,
    but `wfctl arch-root` names what it costs.
    """
    override = os.environ.get(_ARCH_DIR_OVERRIDE)
    if override:
        # Anchored to the repo, never the cwd — the same rule `_manifest_root`
        # applies to a declared relative value. Left raw, one setting would name
        # a different directory per shell, and `arch-root` would report a root
        # inside the tree or outside it depending on where it was run.
        declared = Path(override).expanduser()
        return declared if declared.is_absolute() else repo_root / declared
    found = arch_root_declaration(repo_root)
    return found[0] if found is not None else repo_root / "docs" / "architecture"


def touched_on_this_branch(
    repo_root: Path, path: Path, exclude: Path | None = None
) -> bool | None:
    """Does the change under review add or modify anything under `path`?

    None when git cannot answer — no trunk to compare against, or a `path`
    outside the repository. Three states rather than two on purpose: the callers
    include a gate, and a gate that reads "cannot tell" as "no" refuses work it
    has no evidence against.

    Uncommitted first, because the common case is a record written moments ago
    and not yet committed. Then `trunk...HEAD`, so a record committed earlier on
    the same branch still counts — otherwise the gate would reopen every time
    the author commits.

    `exclude` drops one subtree from the question. Asking about a directory is
    recursive in git and cannot be made otherwise, so a caller that means "this
    root, but not that corner of it" has no way to say so through the pathspec
    it would write by hand.
    """
    def names(*args: str) -> str | None:
        """Paths git reports for `args`, or None when the command failed."""
        r = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None

    if not is_in_tree(path, repo_root):
        return None

    spec = [str(path)]
    if exclude is not None:
        # `:(exclude)` is magic-pathspec syntax and takes a repo-relative path —
        # given an absolute one git reads the whole thing as a literal name and
        # matches nothing, which fails open and is the direction that hurts.
        spec.append(f":(exclude){exclude.resolve().relative_to(repo_root.resolve())}")

    dirty = names("status", "--porcelain", "--", *spec)
    if dirty is None:
        return None
    if dirty:
        return True

    trunk = _trunk_branch(repo_root)
    if trunk is None:
        return None
    committed = names("diff", "--name-only", f"{trunk}...HEAD", "--", *spec)
    return None if committed is None else bool(committed)


def is_in_tree(root: Path, repo_root: Path) -> bool:
    """Would a file under `root` be committed with the code in `repo_root`?

    Its own function rather than a line inside the command so it can be checked
    with plain paths, per `plan.md`'s structure decision — inlined, the only way
    to exercise it is a CLI runner over a real git repo.
    """
    return root.resolve().is_relative_to(repo_root.resolve())

def delivery_issue_keys(spec_dir: Path, pattern: str) -> set[str] | None:
    """The issue keys `spec_dir`'s delivery.md claims in its Issue Grouping Map.

    None means the feature makes no claim at all — no delivery.md, or one with
    no grouping map. An empty *set* means the opposite: a map is there and no
    row in it could be read. Callers must not collapse the two. A feature that
    has not been decomposed says nothing about who owns it and is still
    inheritable; a map nobody can parse is a question that went unanswered, and
    answering it "yes, inherit" is how #120 gets back in. Failing closed on the
    second costs an unresolved spec dir, which is the loud failure.

    Rows are read from the first run of table lines under the heading, and only
    the leading key of the first cell. The wider scan `speckit-orchestrate` did
    by hand — every cell of every row — also matches a `Tasks` range or a
    `PR #12` column and invents a claim on a foreign feature. Stopping at the
    first blank line keeps a sibling table that shares the heading (a real one
    tallies acceptance criteria `1`, `3`, `4`, `5`) from being read as issues.

    The cell prefix is generous because the real files are: `**#575** — …`,
    `[#45](https://…)` and `aamarin/wfctl#24` all appear in the two spec roots
    this was measured against, and the first is the shape in #120's own repro.
    Generous here is safe in a way it is not inside the row — an unread row is a
    silent claim dropped, and a dropped claim is what makes a foreign feature
    look inheritable.

    `pattern` must compile; unlike `extract_issue_key` this does not degrade a
    bad one. `_tracker.load_key_pattern` is the only supported source and it
    guarantees a compilable value.
    """
    try:
        text = (spec_dir / "delivery.md").read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError):
        return None
    except (OSError, ValueError):
        # The file is there and cannot be read — not UTF-8 (UnicodeDecodeError is
        # a ValueError), unreadable permissions, a directory wearing the name.
        # That is the unanswered question, not the absent one, so it takes the
        # empty set and fails closed. Splitting these two excepts is the whole
        # point: catching them together returns None for both, and None is the
        # inheritable answer — which hands a foreign feature back exactly the way
        # #120 did, on any repo with one unreadable file under the spec root.
        # Caught rather than raised because a file nobody asked about must not
        # take `status`, `resume` and `feature-paths` down with it.
        return set()
    heading = _GROUPING_HEADING.search(text)
    if heading is None:
        return None

    keys = set()
    seen_row = False
    for line in text[heading.end():].splitlines():
        if not line.lstrip().startswith("|"):
            if seen_row:
                break
            continue
        seen_row = True
        cell = line.split("|")[1].strip()
        m = re.match(rf"^[*_ ]*\[?(?:[\w.-]+/[\w.-]+)?#?({pattern})\b", cell)
        if m is None:
            # Second tier, for cells that label the row before naming it —
            # `Child #304`, `Issue A (#461)`. Anywhere in the cell, but only
            # behind a literal `#`: without it `Wave 0 — Setup` claims issue 0.
            # Trackers whose keys carry no `#` get the leading position only,
            # which is the one their template mandates anyway.
            m = re.search(rf"#({pattern})\b", cell)
        if m:
            keys.add(m.group(1))
    return keys


def resolve_spec_dir(branch: str, repo_root: Path) -> Path | None:
    """Return spec dir: {spec root}/{branch-prefix}-* → None if not found.

    When `branch` has no match of its own, two fallbacks, in this order:

    First the feature whose delivery.md names this branch's issue key. That is
    the answer whenever it exists — a decomposed epic records which sub-issue
    owns which task range, and the key is the only thing that survives the
    sub-issue being named nothing like its parent.

    Then the same name lookup against ancestor branches, nearest first, which
    handles worktrees branched off a parent epic's planning branch instead of
    the target branch. An ancestor carrying a grouping map is a decomposed
    feature that had its chance to name this branch and did not — a sibling
    sub-issue of a foreign feature, which is the stacked-branch shape of #120,
    where a finished neighbour's `tasks.md` was counted as this story's and
    `status` said "open PR" on work that had not begun. Skip it: no spec dir is
    the loud, obviously wrong failure, and a foreign one is the quiet plausible
    one. Only a feature with no map at all is inherited, which is the epic that
    has not decomposed yet.

    That leaves one shape of #120 standing: a foreign ancestor that never
    decomposed has no map to contradict, and is inherited. Nothing in
    `delivery.md` can decide that case, and widening the fallback is the
    direction the bug came from — so it stays open rather than guessed at.

    A branch with no parseable issue key loses that inheritance too, since no
    map can name a key it does not have. wfctl's own worktrees always carry one
    (`pre_create` enforces it) but the repos wfctl installs into need not, and
    for them this is the loud failure replacing a guess, not a regression.

    Searches one root only, the one `spec_root` resolves. No second look under
    `repo_root/specs` when a root is configured: falling back would let one
    feature's artifacts split across two locations — spec.md found in the old
    root while plan.md is written to the new one. `wfctl doctor` reports the
    leftovers instead.
    """
    root = spec_root(repo_root)

    from wfctl import _tracker  # lazy: avoids import cycle at module load

    pattern = _tracker.load_key_pattern(repo_root)

    def match(candidate: str) -> Path | None:
        exact = root / candidate
        if exact.is_dir():
            return exact
        key = extract_issue_key(candidate, pattern)
        if key != "unknown":
            # is_dir(), like the exact-name branch above: a spec dir is a
            # directory. Unfiltered, a stray `42-notes.md` beside `42-feature/`
            # sorts first and is handed back as the feature dir, which makes
            # FEATURE_SPEC a path *inside* a file — `42-notes.md/spec.md`.
            matches = sorted(p for p in root.glob(f"{key}[-_]*") if p.is_dir())
            if matches:
                return matches[0]
        return None

    found = match(branch)
    if found is not None:
        return found

    key = extract_issue_key(branch, pattern)
    if key != "unknown":
        # Every claimant, not the first: two features claiming one key is a real
        # shape (a parent epic and the sub-feature that later grew its own dir),
        # and picking the lexicographically first is a silent arbitrary answer
        # about who owns a branch — the shape of answer #120 is about. Two
        # claimants with no dir of their own exist in a spec root this was
        # measured against; they resolve to nothing until a human breaks the tie.
        claimants = [
            d.parent for d in sorted(root.glob("*/delivery.md"))
            if key in (delivery_issue_keys(d.parent, pattern) or set())
        ]
        if len(claimants) == 1:
            return claimants[0]
        if claimants:
            return None

    for ancestor in _ancestor_branches(branch, repo_root):
        found = match(ancestor)
        if found is None:
            continue
        # `is not None`, not truthiness: a decomposed feature whose map could
        # not be read yields an empty set, and it is the one case that must not
        # be inherited. Reaching here at all means the leg above already failed
        # to find this key, so any map present is a map that does not name us.
        if delivery_issue_keys(found, pattern) is not None:
            continue
        return found

    return None


def project_name(repo_root: Path) -> str:
    """The project's name — the main checkout's directory, not the worktree's.

    The `<project>/` level separates one project's state from another's, but a
    linked worktree's own directory is named after the branch, so keying on it
    fabricates a project per branch (`440-editable-table-row/440-editable-table-row/`)
    and splits a project's state across every worktree it has ever had.
    `--git-common-dir` points at the main checkout's .git from anywhere in the
    repo, including from a worktree.
    """
    common = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        cwd=repo_root, capture_output=True, text=True,
    )
    if common.returncode != 0 or not common.stdout.strip():
        return repo_root.name
    # Relative ('.git') from the main checkout, absolute from a worktree.
    git_dir = (repo_root / common.stdout.strip()).resolve()
    return git_dir.parent.name or repo_root.name


def resolve_agent_dir(repo_root: Path, branch: str) -> Path:
    """Return state dir: WFCTL_STATE_DIR → `$XDG_STATE_HOME/wfctl/<project>/<branch>`.

    Creates the dir. Project directories sit directly under wfctl's own XDG
    namespace — no `repos/` or `stories/` level, since everything wfctl stores
    is a project, and everything under a project is a branch.
    """
    override = os.environ.get(_STATE_DIR_OVERRIDE)
    if override:
        d = Path(override)
        d.mkdir(parents=True, exist_ok=True)
        return d

    repo_name = project_name(repo_root)
    xdg_base = Path(os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state"))
    d = xdg_base / "wfctl" / repo_name / branch
    d.mkdir(parents=True, exist_ok=True)
    return d
