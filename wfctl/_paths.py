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
    identifying it; the delivery.md "Issue Grouping Map" scan in speckit-orchestrate
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


def touched_on_this_branch(repo_root: Path, path: Path) -> bool | None:
    """Does the change under review add or modify anything under `path`?

    None when git cannot answer — no trunk to compare against, or a `path`
    outside the repository. Three states rather than two on purpose: the one
    caller is a gate, and a gate that reads "cannot tell" as "no" refuses work
    it has no evidence against.

    Uncommitted first, because the common case is a record written moments ago
    and not yet committed. Then `trunk...HEAD`, so a record committed earlier on
    the same branch still counts — otherwise the gate would reopen every time
    the author commits.
    """
    def names(*args: str) -> str | None:
        """Paths git reports for `args`, or None when the command failed."""
        r = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None

    if not is_in_tree(path, repo_root):
        return None

    dirty = names("status", "--porcelain", "--", str(path))
    if dirty is None:
        return None
    if dirty:
        return True

    trunk = _trunk_branch(repo_root)
    if trunk is None:
        return None
    committed = names("diff", "--name-only", f"{trunk}...HEAD", "--", str(path))
    return None if committed is None else bool(committed)


def is_in_tree(root: Path, repo_root: Path) -> bool:
    """Would a file under `root` be committed with the code in `repo_root`?

    Its own function rather than a line inside the command so it can be checked
    with plain paths, per `plan.md`'s structure decision — inlined, the only way
    to exercise it is a CLI runner over a real git repo.
    """
    return root.resolve().is_relative_to(repo_root.resolve())


def resolve_spec_dir(branch: str, repo_root: Path) -> Path | None:
    """Return spec dir: {spec root}/{branch-prefix}-* → None if not found.

    Falls back to the same lookup against ancestor branches (nearest first) when
    `branch` itself has no match — handles worktrees branched off a parent epic's
    planning branch instead of the target branch.

    Searches one root only, the one `spec_root` resolves. No second look under
    `repo_root/specs` when a root is configured: falling back would let one
    feature's artifacts split across two locations — spec.md found in the old
    root while plan.md is written to the new one. `wfctl doctor` reports the
    leftovers instead.
    """
    root = spec_root(repo_root)

    from wfctl import _tracker  # lazy: avoids import cycle at module load

    def match(candidate: str) -> Path | None:
        exact = root / candidate
        if exact.is_dir():
            return exact
        key = extract_issue_key(candidate, _tracker.load_key_pattern(repo_root))
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

    for ancestor in _ancestor_branches(branch, repo_root):
        found = match(ancestor)
        if found is not None:
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
