"""Path resolution for wfctl state, branch, spec dir, and repo root."""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from collections.abc import Sequence
from typing import NamedTuple

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
# ("Issue Grouping Map (revised)") would otherwise read as claiming no issues at
# all, so every sub-issue the map names loses its only route to the epic — a
# typo turning a decomposed feature back into an unresolved one.
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


def is_detached(repo_root: Path) -> bool:
    """HEAD names no branch, and nobody named one through `WFCTL_BRANCH`.

    The question `resolve_branch` answers around rather than reports: it hands
    back the short hash in place of a branch name, and an all-digit hash then
    parses as an issue key. A caller that needs to know the branch is real asks
    here instead of reading that name.
    """
    if os.environ.get(_BRANCH_OVERRIDE):
        return False
    r = subprocess.run(
        ["git", "symbolic-ref", "-q", "HEAD"], cwd=repo_root, capture_output=True,
    )
    return r.returncode != 0


def is_bare_layout(repo_root: Path) -> bool:
    """Is this checkout a worktree of a bare repository, where none is the main one?"""
    r = subprocess.run(
        ["git", "config", "--bool", "core.bare"], cwd=repo_root, capture_output=True, text=True,
    )
    return r.stdout.strip() == "true"


def _bare_head(repo_root: Path) -> str | None:
    """The branch a bare repository's own HEAD names, or None outside a bare layout."""
    if not is_bare_layout(repo_root):
        return None
    common = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=repo_root, capture_output=True, text=True,
    )
    if common.returncode != 0:
        return None
    git_dir = common.stdout.strip()
    head = subprocess.run(
        ["git", f"--git-dir={git_dir}", "symbolic-ref", "--short", "HEAD"],
        capture_output=True, text=True,
    )
    branch = head.stdout.strip() if head.returncode == 0 else ""
    if not branch:
        return None
    # `HEAD` names whatever branch existed when the bare repository was made
    # (`git init --bare` defaults to `master`) and is never moved when the
    # default branch changes afterwards, so the name it holds can be one
    # nothing points at any more. Returning it unchecked regressed trunk
    # detection below the name guess it replaced: a `main` worktree, with no
    # `master` left, was refused as naming no issue.
    exists = subprocess.run(
        ["git", f"--git-dir={git_dir}", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
        capture_output=True,
    )
    return branch if exists.returncode == 0 else None


# Spelled out rather than imported from `_verify`, which sits a band above this
# module and loads rich at import. `hook session-restart` imports this module on
# a path that must load neither, and `test_restart_hook_cli` is what says so.
_CONFIG_PATH = "wfctl.json"
TRUNK_KEY = "trunk"


def declared_trunk(repo_root: Path) -> tuple[str | None, list[str]]:
    """Return (the branch `wfctl.json` names as trunk, problems). Both empty
    means the repository declares none.

    A declaration that is present but unusable comes back as a problem and no
    name, never as "none declared". `trunk_branch` reads the difference: the
    first falls through to discovery, and the second must not, because a
    declaration wfctl drops without saying so is indistinguishable to its author
    from one wfctl never read.

    A file that will not parse, or whose top level is not an object, is "none
    declared" rather than a problem here.
    `doctor` and `check config` both report it already, and this reader runs
    inside `start` and `status`, where a third copy of the same finding is not
    what anyone asked for.
    """
    path = repo_root / _CONFIG_PATH
    if not path.exists():
        return None, []
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None, []
    if not isinstance(data, dict):
        return None, []
    # Presence, not value: `"trunk": null` is a declaration that names nothing,
    # and `.get` would read it as the key being absent and let discovery answer.
    if TRUNK_KEY not in data:
        return None, []
    declared = data[TRUNK_KEY]
    if not isinstance(declared, str) or not declared.strip():
        return None, [f"'{TRUNK_KEY}' must be a branch name, such as \"main\""]
    return declared, []


def _resolve_declared(repo_root: Path, name: str) -> str | None:
    """The revision a declared branch name stands for: `origin/<name>` when the
    remote has it, else the local branch, else None.

    The declaration names a plain branch, and the remote-tracking form wins
    because it is what discovery already hands back from `origin/HEAD`. Used
    verbatim, `"trunk": "main"` would diff against a local `main` that can sit
    behind `origin/main`, so declaring the trunk discovery already found would
    change which commits `touched_on_this_branch` compares, and records already
    on trunk would read as this branch's. A bare clone keeps no remote-tracking
    refs by default, so there the local branch is the answer.

    `show-ref --verify` rather than `rev-parse --verify`: the latter parses a
    revision expression, so `"main~1"` would resolve to an ancestor commit and
    pass for a branch name. `show-ref` accepts only a ref that exists by that
    exact name.

    `HEAD` is refused by name. A clone carries `refs/remotes/origin/HEAD`, a
    symbolic ref to the remote's default branch, so `show-ref` finds it and
    `"trunk": "HEAD"` would pass as a branch while naming whatever discovery
    guessed, which is the answer a declaration exists to overrule.
    """
    if name == "HEAD":
        return None
    for ref, answer in (
        (f"refs/remotes/origin/{name}", f"origin/{name}"),
        (f"refs/heads/{name}", name),
    ):
        if subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", ref],
            cwd=repo_root, capture_output=True,
        ).returncode == 0:
            return answer
    return None


def declared_trunk_problems(repo_root: Path) -> list[str]:
    """Everything wrong with the repository's trunk declaration, for `check config`."""
    name, problems = declared_trunk(repo_root)
    if name is not None and _resolve_declared(repo_root, name) is None:
        problems.append(
            f"'{TRUNK_KEY}' names '{name}', which is neither a "
            "local branch nor a branch on origin"
        )
    return problems


def trunk_branch(repo_root: Path) -> str | None:
    """The repo's trunk: the branch `wfctl.json` declares, else origin/HEAD when
    the remote publishes it, then a bare repository's own HEAD, else the first
    local main/master/dev that exists. None when nothing looks like one.

    The declaration comes first because a repository that declares its trunk is
    correcting discovery, and one read only where discovery failed would correct
    nothing. A declaration that names no branch, or is not a name at all, answers
    None rather than falling through: discovery is the answer the author wrote
    the declaration to overrule, and `check config` is where they learn it is
    broken.

    The bare HEAD is there because a bare clone records no origin/HEAD, so a
    bare layout otherwise always falls through to the name guess, and a repo
    whose trunk is `dev` but which also carries `main` is read as trunk `main`.
    It is read only when `core.bare` says the layout is bare: in a normal layout
    the shared HEAD is whatever the main checkout has checked out, which can be a
    feature branch. `core.bare` rather than `rev-parse --is-bare-repository`,
    which answers false from inside a bare layout's worktree. Both discovered
    sources are as stale as the clone, and a changed default reaches them only
    through a fresh clone; the declaration is the one source that moves when
    the repository says so.
    """
    name, problems = declared_trunk(repo_root)
    if problems:
        return None
    if name is not None:
        return _resolve_declared(repo_root, name)
    head = subprocess.run(
        ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        cwd=repo_root, capture_output=True, text=True,
    )
    if head.returncode == 0 and head.stdout.strip():
        return head.stdout.strip()
    bare = _bare_head(repo_root)
    if bare is not None:
        return bare
    for name in ("main", "master", "dev"):
        if subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", name],
            cwd=repo_root, capture_output=True,
        ).returncode == 0:
            return name
    return None


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


# The arch-root subtree holding what a review step's scan covered, rather than
# what a run decided (#307). A name and not a literal at each call site, because
# three readers of the arch root now have to agree about which corner of it is
# not a record, and a fourth added later has one place to find that out.
SCANS_DIR = "scans"

# The arch-root subtree holding an implementation note — prose saying why one
# mechanism was picked over a cheaper one, written during level 4 (#370). It
# decides nothing either, so it reaches the readers below for `scans/`' reason
# and has to be dropped for it.
IMPLEMENTATION_DIR = "implementation"

# The arch-root subtree holding a person's claim that one pipeline pass does
# not apply to this change (#339, `an-absent-artifact-is-claimed-not-inferred`).
# A claim answers a narrower question than a record does and decides nothing
# about the boundary a record decides — left out, `wfctl step none` would
# double as an unintended way to satisfy the design gate (FR-016, SC-006), the
# same failure `scans/` and `implementation/` are excluded to prevent.
STEP_CLAIMS_DIR = "step-claims"

# The arch-root subtree holding a domain model — the language, contexts and
# invariants `model-the-domain` found (#464). It describes what a record
# decided and decides nothing itself, and it is written at level 2, the one
# level whose gate asks whether the boundary was put: counted, a modeling round
# that wrote a document and drew nothing would read as having answered.
DOMAIN_DIR = "domain"

# The arch-root subtree holding level-3 design records. Unlike the subtrees
# above it *is* a record tier, so it is absent from `non_record_subtrees` and every
# caller that wants it dropped says so itself. It has a name here anyway,
# because the placement check reads it as a tier rather than dropping it, and a
# literal at one call site and a constant at the other is how `scans/` came to
# be spelled out four times.
DESIGN_DIR = "design"


def non_record_subtrees(arch: Path) -> list[Path]:
    """The corners of the arch root holding documents that decided nothing.

    One list rather than a constant per directory, because the readers below do
    not care which corner a path fell in — only that it is not a record. A fifth
    non-record subtree is then an entry here and no edit at any call site, which
    is the failure this replaces: `scans/` was named at each of them, and the
    second such subtree had to find all four.
    """
    return [
        arch / SCANS_DIR,
        arch / IMPLEMENTATION_DIR,
        arch / STEP_CLAIMS_DIR,
        arch / DOMAIN_DIR,
    ]


def touched_on_this_branch(
    repo_root: Path, path: Path, exclude: Sequence[Path] | None = None
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

    `exclude` drops subtrees from the question. Asking about a directory is
    recursive in git and cannot be made otherwise, so a caller that means "this
    root, but not those corners of it" has no way to say so through the pathspec
    it would write by hand. A sequence rather than one path because the arch root
    holds several such corners and will hold more; `non_record_subtrees` names
    the set.
    """
    def names(*args: str) -> str | None:
        """Paths git reports for `args`, or None when the command failed."""
        r = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None

    if not is_in_tree(path, repo_root):
        return None

    spec = [str(path)]
    for dropped in exclude or ():
        # `:(exclude)` is magic-pathspec syntax and takes a repo-relative path —
        # given an absolute one git reads the whole thing as a literal name and
        # matches nothing, which fails open and is the direction that hurts.
        spec.append(f":(exclude){dropped.resolve().relative_to(repo_root.resolve())}")

    dirty = names("status", "--porcelain", "--", *spec)
    if dirty is None:
        return None
    if dirty:
        return True

    trunk = trunk_branch(repo_root)
    if trunk is None:
        return None
    committed = names("diff", "--name-only", f"{trunk}...HEAD", "--", *spec)
    return None if committed is None else bool(committed)


def records_on_this_branch(
    repo_root: Path,
    arch: Path,
    exclude: Sequence[Path] | None = None,
    *,
    added_only: bool = False,
) -> list[str]:
    """The record slugs this branch adds or modifies, uncommitted work included.

    `added_only` narrows the listing to records the branch base does not have.
    A reader judging a record by rules newer than the record needs that line:
    an edit to a record written before the rules existed would otherwise be
    held to them.

    "The base does not have it" is asked of the base's tree, never of git's
    change codes. Those codes turn on whether git paired two paths as a rename
    or a copy, which is a similarity guess that moves with staging and with each
    machine's `diff.renames` and `status.renames`. Read that way, the same record
    was judged before a commit and released after it, and a new record that git
    paired with a deleted one was never judged at all. A rename is new by this
    test, since the base has no file at its path, so renaming an older record
    holds the branch on its drawing; that is the direction that fails closed.

    A sibling of `touched_on_this_branch` rather than a widening of it, because
    the two answer different questions and only one of them gates. That one
    returns three states so a gate with no evidence does not refuse; this one is
    a listing, where "cannot tell" and "nothing" are the same empty line and no
    caller can act differently on them. Widening the gate's return to carry names
    would make every caller of a refusal handle a list.

    Slugs rather than paths: a record's identity *is* its slug
    (`architecture-decisions`), and a reader scanning a PR for what a run decided
    is matching names, not directories.

    `exclude` drops subtrees, for its sibling's reason and one of its own. A git
    pathspec naming a directory is recursive and cannot be made otherwise, and the
    arch root holds documents that decided nothing: `scans/` is what a review step
    covered, not what a run chose, and `implementation/` is why a mechanism was
    picked once a boundary was already settled. Listed as a record either answers
    the caller's question wrongly in the one mode that has no reader to notice
    (#307).
    """
    if not is_in_tree(arch, repo_root):
        return []

    def names(*args: str) -> list[str]:
        r = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True)
        if r.returncode != 0:
            return []
        # `status --porcelain` prefixes each line with a two-column code; `diff
        # --name-only` does not. Splitting on whitespace from the right leaves
        # the path in both, and a record path never contains one.
        return [line.split()[-1] for line in r.stdout.splitlines() if line.strip()]

    spec = [str(arch)]
    for dropped in exclude or ():
        # `:(exclude)` is magic-pathspec syntax and takes a repo-relative path —
        # the same constraint `touched_on_this_branch` documents, and the same
        # direction of failure: an absolute path is read as a literal name,
        # matches nothing, and the subtree comes back in the listing.
        spec.append(f":(exclude){dropped.resolve().relative_to(repo_root.resolve())}")
    # `-uall`, unlike `touched_on_this_branch`'s bare `--porcelain`. Git collapses
    # an untracked *directory* to one entry, so the first record written into a
    # repo that has none reports `docs/architecture/` and no filename — which a
    # caller asking "did anything change" can still read as yes, and a caller
    # asking "which records" reads as none.
    found = names("status", "--porcelain", "-uall", "--", *spec)
    trunk = trunk_branch(repo_root)
    if trunk is not None:
        found += names("diff", "--name-only", f"{trunk}...HEAD", "--", *spec)

    if added_only:
        # The merge base is what `trunk...HEAD` diffs against. With no trunk,
        # HEAD is the only base there is: a record committed before this read is
        # indistinguishable from one on trunk. This filter cannot close that gap,
        # so the design gate names it on its own row instead (#508). A base git
        # cannot read lists nothing, so every touched record counts as added,
        # which again fails closed.
        base = names("merge-base", trunk, "HEAD") if trunk is not None else ["HEAD"]
        rel = str(arch.resolve().relative_to(repo_root.resolve()))
        tree = ["ls-tree", "-r", "--name-only", "--full-name"]
        on_base = set(names(*tree, base[0], "--", rel)) if base else set()
        found = [p for p in found if p not in on_base]

    slugs = {Path(p).stem for p in found if p.endswith(".md")}
    return sorted(slugs)


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
    row in it could be read.

    No caller separates the two today. `resolve_spec_dir`'s only consumer asks
    whether a key is claimed, and neither answer claims anything, so both mean
    "not yours" — which is the whole answer now that inheriting an ancestor is
    gone (`a-branch-is-claimed-not-inherited`). The distinction is kept rather
    than collapsed because it is the difference between a question nobody asked
    and one that went unanswered, and a later caller that acts on a claim's
    absence needs to know which it has.

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
    silent claim dropped, and a dropped claim costs the sub-issue it named its
    only route to its epic.

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
        # empty set. Caught rather than raised because the claimant scan reads
        # every delivery.md under the spec root: one unreadable file would
        # otherwise take `status`, `resume` and `feature-paths` down over a
        # feature nobody asked about.
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

    When `branch` has no match of its own, one fallback: the feature whose
    delivery.md names this branch's issue key. A decomposed epic records which
    sub-issue owns which task range, and the key is the only thing that survives
    the sub-issue being named nothing like its parent.

    Nothing else claims a branch. Git ancestry used to, for worktrees cut from a
    parent epic's planning branch, and `a-branch-is-claimed-not-inherited`
    retired it: a base records where a worktree came from, which is the same
    fact whether the epic was chosen or mistyped, so it cannot answer which
    feature owns the branch. Unresolved is the loud failure; a foreign feature's
    finished pipeline is the quiet one (#120, #263).

    A branch with no parseable issue key resolves only by its own name, since no
    map can name a key it does not have. `wfctl start` refuses a session in a
    linked worktree whose branch carries none, in a repo with a tracker, but the
    branch still exists and still resolves; the main checkout and a repo with no
    tracker are never asked for one.

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

    return None


class ClaimConflict(NamedTuple):
    """One issue key that more than one feature under the spec root claims.

    Two lists rather than one, because the two kinds of claim are not
    interchangeable: a directory carrying the key in its own name beats any
    number of grouping map rows naming it, so which list a claimant is in is
    what decides the answer. Collapsed into one list, a report could name the
    claimants and not which of them resolution returns.
    """
    key: str
    own: list[Path]
    mapped: list[Path]


def claim_conflicts(repo_root: Path) -> list[ClaimConflict]:
    """Every issue key claimed by more than one feature under the spec root.

    A directory claims the key its own name carries; a delivery.md claims every
    key its Issue Grouping Map names. Both are on disk and neither needs a
    branch to be read, which is why the disagreement is reportable at all —
    `resolve_spec_dir` is asked about one branch and never sees the claims that
    do not bear on it, so the resolver cannot be the thing that notices.

    A feature claiming its own key twice — a directory named `100-epic` whose
    map also lists `#100` — is one claimant, not two. The map row is redundant
    there, not a disagreement, and reporting it would fire on the ordinary case.

    Reads artifacts only, and answers nothing `resolve_spec_dir` answers: a
    conflict here does not change which directory a branch resolves to
    (`a-branch-is-claimed-not-inherited`).
    """
    root = spec_root(repo_root)
    if not root.is_dir():
        return []

    from wfctl import _tracker  # lazy: avoids import cycle at module load

    pattern = _tracker.load_key_pattern(repo_root)

    try:
        features = sorted(p for p in root.iterdir() if p.is_dir())
    except OSError:
        # A configured root is an arbitrary path off this machine — an external
        # directory whose permissions have nothing to do with the repo, unlike
        # the in-repo `specs/` the migration check reads. `is_dir()` passes on
        # one this user cannot list, and the raise lands in `doctor` before it
        # has reported the layer checks that come after. Silent rather than a
        # warning because a root that cannot be read stops `status` and
        # `feature-paths` outright: by the time this would say so, it has been
        # said louder.
        return []

    own: dict[str, list[Path]] = {}
    mapped: dict[str, list[Path]] = {}
    for d in features:
        key = extract_issue_key(d.name, pattern)
        if key != "unknown":
            own.setdefault(key, []).append(d)
        for claimed in delivery_issue_keys(d, pattern) or ():
            if claimed != key:
                mapped.setdefault(claimed, []).append(d)

    # Numeric keys sort as numbers, everything else after them alphabetically.
    # A plain string sort files issue 100 ahead of issue 9, and the reader is
    # scanning this list for a key they already have in mind.
    def order(k: str) -> tuple[int, int, str]:
        return (0, int(k), "") if k.isdigit() else (1, 0, k)

    conflicts = [
        ClaimConflict(k, own.get(k, []), mapped.get(k, []))
        for k in sorted(own.keys() | mapped.keys(), key=order)
    ]
    return [c for c in conflicts if len(c.own) + len(c.mapped) > 1]


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


def project_state_dir(repo_root: Path) -> Path:
    """`$XDG_STATE_HOME/wfctl/<project>`, the parent of every branch's state dir."""
    xdg_base = Path(os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state"))
    return xdg_base / "wfctl" / project_name(repo_root)


def state_root(repo_root: Path) -> Path:
    """The directory holding every state dir a session here may write to.

    `WFCTL_STATE_DIR` names one state dir and nothing beside it, so it is its
    own root. Otherwise it is the project's directory, which holds every
    branch's, since a worktree handoff writes into a child branch's state dir
    from the parent's worktree.
    """
    override = os.environ.get(_STATE_DIR_OVERRIDE)
    return Path(override) if override else project_state_dir(repo_root)


def resolve_agent_dir(repo_root: Path, branch: str, create: bool = True) -> Path:
    """Return state dir: WFCTL_STATE_DIR → `$XDG_STATE_HOME/wfctl/<project>/<branch>`.

    Creates the dir unless `create` is False. Project directories sit directly
    under wfctl's own XDG namespace — no `repos/` or `stories/` level, since
    everything wfctl stores is a project, and everything under a project is a
    branch.

    `create=False` is for a reader that runs whether or not wfctl was ever used
    on the branch — the session-restart hook fires on every reply end in every
    repo with the claude layer, and creating a directory there would leave one
    behind for each branch anyone replied on.
    """
    override = os.environ.get(_STATE_DIR_OVERRIDE)
    d = Path(override) if override else project_state_dir(repo_root) / branch
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d
