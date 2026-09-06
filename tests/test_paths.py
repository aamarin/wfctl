"""Tests for wfctl._paths — path resolution."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from wfctl._paths import (
    delivery_issue_keys,
    project_name,
    resolve_agent_dir,
    resolve_branch,
    resolve_spec_dir,
    worktree_branches,
)


def test_resolve_branch_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WFCTL_BRANCH", "999-my-feature")
    assert resolve_branch(tmp_path) == "999-my-feature"


def test_resolve_branch_from_git(repo_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WFCTL_BRANCH", raising=False)
    import subprocess
    subprocess.run(["git", "-C", str(repo_root), "checkout", "-b", "422-test-branch"],
                   check=True, capture_output=True)
    result = resolve_branch(repo_root)
    assert result == "422-test-branch"


def test_resolve_spec_dir_finds_prefix_match(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    specs = tmp_path / "specs"
    target = specs / "422-foo-bar"
    target.mkdir(parents=True)
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(specs))
    result = resolve_spec_dir("422-something", tmp_path)
    assert result == target


def test_resolve_spec_dir_exact_match(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    specs = tmp_path / "specs"
    target = specs / "422-something"
    target.mkdir(parents=True)
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(specs))
    result = resolve_spec_dir("422-something", tmp_path)
    assert result == target


def test_resolve_spec_dir_returns_none_when_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    specs = tmp_path / "specs"
    specs.mkdir()
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(specs))
    result = resolve_spec_dir("422-missing", tmp_path)
    assert result is None


def _init_commit(repo_root: Path) -> None:
    """First commit on the repo_root fixture's unborn HEAD, giving it a real branch."""
    import subprocess

    (repo_root / "README.md").write_text("test\n")
    subprocess.run(["git", "-C", str(repo_root), "add", "README.md"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "commit", "-m", "init"], check=True, capture_output=True
    )


def test_resolve_spec_dir_does_not_inherit_an_undecomposed_ancestor(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#263: this tree used to resolve to the ancestor, and it is the tree the
    bug was reported on — a worktree cut with the wrong `--base` reported three
    of another feature's steps as done and handed the agent `/speckit.analyze`
    on a pipeline it had not entered.

    It is also, byte for byte, the epic-planning-branch convention the ancestor
    walk was written for. The two are indistinguishable from the tree, which is
    why `a-branch-is-claimed-not-inherited` retired the walk rather than
    narrowing it: nothing an implementation can read separates a base that was
    chosen from one that was mistyped."""
    import subprocess

    _init_commit(repo_root)
    subprocess.run(
        ["git", "-C", str(repo_root), "checkout", "-b", "330-epic-not-yet-decomposed"],
        check=True, capture_output=True,
    )
    specs = repo_root / "specs" / "330-epic-not-yet-decomposed"
    specs.mkdir(parents=True)
    (specs / "tasks.md").write_text("x")
    subprocess.run(["git", "-C", str(repo_root), "add", "specs"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "commit", "-m", "spec"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_root), "checkout", "-b", "464-period-nav-pill"],
        check=True, capture_output=True,
    )
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)

    assert resolve_spec_dir("464-period-nav-pill", repo_root) is None


def test_resolve_spec_dir_ignores_unrelated_branches(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A same-named specs/ dir on a branch that isn't an ancestor must not match."""
    import subprocess

    _init_commit(repo_root)
    base = subprocess.run(
        ["git", "-C", str(repo_root), "branch", "--show-current"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()

    subprocess.run(
        ["git", "-C", str(repo_root), "checkout", "-b", "999-unrelated"],
        check=True, capture_output=True,
    )
    specs = repo_root / "specs" / "999-unrelated"
    specs.mkdir(parents=True)
    (specs / "tasks.md").write_text("x")
    subprocess.run(["git", "-C", str(repo_root), "add", "specs"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "commit", "-m", "unrelated spec"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_root), "checkout", base],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_root), "checkout", "-b", "464-no-relation"],
        check=True, capture_output=True,
    )
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)

    result = resolve_spec_dir("464-no-relation", repo_root)
    assert result is None


def _delivery_map(*rows: str) -> str:
    """A delivery.md whose Issue Grouping Map claims `rows`, and nothing else.

    Rows are passed as the literal first cell, not as bare keys: the real files
    write `**#575** — the invariant`, `[#45](url)` and `Issue A (#461)`, and a
    parser tested only against `| #575 |` read every one of them as claiming
    nothing — which is #120's own `delivery.md` among them.
    """
    body = "\n".join(f"| {r} | T001-T005 | `[x] group` | S | PR #1 |" for r in rows)
    return (
        "# Delivery Plan\n\n## Issue Grouping Map\n\n"
        "| Issue | Tasks | Title | Estimate | Closes With |\n"
        "|-------|-------|-------|----------|-------------|\n"
        f"{body}\n\n## Parallelization Opportunities\n\n| Wave | Tasks |\n"
        "|------|-------|\n| 1 | T001 |\n"
    )


_CLAIMS_OTHERS = object()


def _stacked_repo(repo_root: Path, delivery: object = _CLAIMS_OTHERS) -> Path:
    """#120's shape: branch `567-…` stacked on a sibling of a *finished* feature.

    `562-transaction-balance` is decomposed — its delivery.md claims 575 and 576,
    never 567 — and its tasks.md is complete. Its planning branch is an ancestor
    of `567-…` because worktrees branch off the branch below them in the stack.
    A finished foreign feature is what makes the failure say "ship it".

    `delivery` is the one axis worth varying: str writes that text, bytes write
    those bytes, None writes no delivery.md at all. One builder rather than two
    keeps the tree that reads as "#120's shape" from drifting between the test
    that names it and the one that sweeps it.
    """
    import subprocess

    def git(*args: str) -> None:
        subprocess.run(
            ["git", "-C", str(repo_root), *args], check=True, capture_output=True
        )

    _init_commit(repo_root)
    git("checkout", "-b", "562-transaction-balance")
    foreign = repo_root / "specs" / "562-transaction-balance"
    foreign.mkdir(parents=True)
    (foreign / "tasks.md").write_text("- [x] T001 done\n")
    if delivery is _CLAIMS_OTHERS:
        (foreign / "delivery.md").write_text(
            _delivery_map("**#575** — the invariant", "**#576** — entry form")
        )
    elif isinstance(delivery, bytes):
        (foreign / "delivery.md").write_bytes(delivery)
    elif delivery is not None:
        (foreign / "delivery.md").write_text(str(delivery))
    git("add", "specs")
    git("commit", "-m", "spec")
    git("checkout", "-b", "576-transaction-entry-form")
    git("checkout", "-b", "567-readers-to-chart-accounts")
    return foreign


@pytest.mark.parametrize(
    "delivery",
    [
        pytest.param(None, id="never-decomposed"),
        pytest.param(_CLAIMS_OTHERS, id="decomposed-claiming-other-issues"),
        pytest.param(
            "## Issue Grouping Map\n\n| Issue | Number |\n|---|---|\n| Wave 0 | 575 |\n",
            id="map-the-parser-cannot-read",
        ),
        pytest.param(b"\xff\xfe## Issue Grouping Map\n", id="delivery-md-not-utf8"),
    ],
)
def test_resolve_spec_dir_never_inherits_from_an_ancestor(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch, delivery: object
) -> None:
    """#120 and #263, as one constraint: ancestry never claims a branch.

    Each case is a foreign feature whose planning branch is an ancestor of a
    branch with no artifacts of its own, and they differ only in what the
    ancestor's delivery.md says. Inheriting any of them counted a finished
    feature's 46/46 as this story's and told a session with no work done to open
    a PR.

    They pin different strengths, which is why all four are kept. Only
    `never-decomposed` failed against the code before #263 — the other three
    were already skipped by the guard #120 added, so they catch a restoration
    that is *less* careful than the leg that was deleted. And they are not idle
    in the meantime: the claimant scan reads every delivery.md under the spec
    root, so the last three still reach the parser through that leg, and
    `delivery-md-not-utf8` is what keeps an undecodable file from raising
    `UnicodeDecodeError` out of `resolve_spec_dir` itself.
    """
    _stacked_repo(repo_root, delivery)
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)

    assert resolve_spec_dir("567-readers-to-chart-accounts", repo_root) is None


def test_resolve_spec_dir_ignores_a_merged_sibling_feature(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A merged feature branch is an ancestor of every branch cut after it, and
    its specs/ dir is still in the tree — so this was the shape that made plain
    ancestry hand a brand-new branch a completed story's pipeline. It resolves
    to nothing now for the same reason every ancestor does, but the tree is kept
    because it is the one a reader expects ancestry to reach."""
    import subprocess

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

    _init_commit(repo_root)
    trunk = git("branch", "--show-current")

    git("checkout", "-b", "install-config-workmux")
    specs = repo_root / "specs" / "install-config-workmux"
    specs.mkdir(parents=True)
    (specs / "tasks.md").write_text("x")
    git("add", "specs")
    git("commit", "-m", "spec")

    git("checkout", trunk)
    git("merge", "--no-ff", "-m", "merge", "install-config-workmux")
    git("checkout", "-b", "005-brand-new")
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)

    assert resolve_spec_dir("005-brand-new", repo_root) is None


def test_resolve_spec_dir_prefers_the_feature_whose_delivery_claims_the_key(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The sub-issue's real feature is found by the key its delivery.md claims.
    Neither the branch name nor ancestry relates `567-…` to
    `555-taxonomy-redesign`, and the ancestor it does have carries a different
    feature — so this pins that a claim reaches across a stack, which is the
    resolution left standing once ancestry stopped being one."""
    _stacked_repo(repo_root)
    real = repo_root / "specs" / "555-taxonomy-redesign"
    real.mkdir(parents=True)
    (real / "delivery.md").write_text(_delivery_map("#566", "#567"))
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)

    assert resolve_spec_dir("567-readers-to-chart-accounts", repo_root) == real


def test_resolve_spec_dir_keeps_a_branchs_own_dir_over_a_later_epic_claim(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The order the two legs run in, which nothing pinned before.

    A child of an epic that had not decomposed gets `<spec root>/<branch>` from
    `feature-paths` and starts writing there. When the epic decomposes later and
    its grouping map names that key, resolution stays on the child's own
    directory — the name legs run ahead of the claimant scan.

    Reported against the record on #269 as a recovery path that does not exist,
    and it does not; the record was wrong rather than the code. Moving the claim
    ahead would hand a branch holding its own spec.md the epic's task range
    instead, which loses the artifacts somebody wrote — worse than the failure
    #263 removed, not a repair of it.
    """
    specs = repo_root / "specs"
    own = specs / "200-child"
    own.mkdir(parents=True)
    (own / "spec.md").write_text("# the child's own work\n")
    epic = specs / "100-parent"
    epic.mkdir(parents=True)
    (epic / "delivery.md").write_text(_delivery_map("**#200** — the child"))
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(specs))

    assert resolve_spec_dir("200-child", repo_root) == own


def test_resolve_spec_dir_refuses_a_key_two_features_both_claim(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A parent epic and a sub-feature that later grew its own dir can both list
    the same key. Taking the first sorted match makes the answer depend on
    directory names, which is a silent arbitrary verdict about who owns a
    branch — the shape of answer #120 is about, arriving from the other leg."""
    _init_commit(repo_root)
    specs = repo_root / "specs"
    for name in ("539-coa-taxonomy", "543-chart-consolidation"):
        (specs / name).mkdir(parents=True)
        (specs / name / "delivery.md").write_text(_delivery_map("#544"))
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(specs))

    assert resolve_spec_dir("544-account-tiers", repo_root) is None


def test_delivery_issue_keys_separates_no_map_from_an_unreadable_one(
    tmp_path: Path
) -> None:
    """Two answers that mean different things: a feature nobody has decomposed
    said nothing, and one whose map nobody can parse left a question open. No
    caller separates them today — `resolve_spec_dir` asks only whether a key is
    claimed, and neither claims — so this is where the contract is pinned rather
    than at a call site, which is what an un-underscored name promises
    (`the-underscore-is-the-module-contract`)."""
    absent = tmp_path / "no-delivery"
    absent.mkdir()
    assert delivery_issue_keys(absent, r"\d+") is None

    no_map = tmp_path / "no-map"
    no_map.mkdir()
    (no_map / "delivery.md").write_text("# Delivery Plan\n\nNot decomposed yet.\n")
    assert delivery_issue_keys(no_map, r"\d+") is None

    unreadable = tmp_path / "unreadable"
    unreadable.mkdir()
    (unreadable / "delivery.md").write_text(
        "## Issue Grouping Map\n\n| Issue |\n|---|\n| Child A |\n"
    )
    assert delivery_issue_keys(unreadable, r"\d+") == set()


def test_delivery_issue_keys_reads_a_tracker_whose_keys_carry_no_hash(
    tmp_path: Path
) -> None:
    """`#` is GitHub's convention, not every tracker's, and the second parse
    tier requires one. A `PROJ-123` repo therefore gets the leading-position
    tier only — which is the position its own template mandates, but it means
    the tier that rescues `Child #304` does not exist for it."""
    (tmp_path / "delivery.md").write_text(
        "## Issue Grouping Map\n\n| Issue |\n|---|\n| PROJ-123 |\n| Child PROJ-9 |\n"
    )

    assert delivery_issue_keys(tmp_path, r"[A-Z]+-\d+") == {"PROJ-123"}


def test_delivery_issue_keys_stops_at_the_end_of_the_first_table(
    tmp_path: Path
) -> None:
    """A second table under the same heading is not more issues. A real
    delivery.md tallies acceptance criteria `1`, `3`, `4`, `5` in a table below
    its map, and reading those as claims made one feature answer for four
    branches it had nothing to do with."""
    (tmp_path / "delivery.md").write_text(
        "## Issue Grouping Map\n\n| Issue |\n|---|\n| #5 |\n\n"
        "Corrections needed before the PR lands:\n\n"
        "| Criterion | Says | Built |\n|---|---|---|\n| 1 | a | b |\n| 3 | c | d |\n"
    )

    assert delivery_issue_keys(tmp_path, r"\d+") == {"5"}


def test_delivery_issue_keys_fails_closed_on_a_delivery_md_it_cannot_decode(
    tmp_path: Path
) -> None:
    """Two ways to fail this, and the first fix landed on the second.

    `UnicodeDecodeError` is a ValueError, not an OSError, so uncaught it left
    `status`, `resume` and `feature-paths` raising over one unreadable file
    nobody had asked about — and the claimant scan reads every delivery.md under
    the spec root, so one such file anywhere reaches every caller. Caught
    alongside a missing file it would answer None, which says the feature made
    no claim; the file is present, so it is the unanswered question, not the
    absent one.
    """
    (tmp_path / "delivery.md").write_bytes(b"\xff\xfe## Issue Grouping Map\n")

    assert delivery_issue_keys(tmp_path, r"\d+") == set()


def test_delivery_issue_keys_returns_none_when_there_is_no_delivery_md(
    tmp_path: Path
) -> None:
    """The other side of that split, and the only case that reaches None: a
    feature with no delivery.md has not been decomposed, so it made no claim.
    Every read failure answers with the empty set instead, because a file that
    exists and cannot be read is not the same as one that was never written."""
    assert delivery_issue_keys(tmp_path, r"\d+") is None


def test_delivery_issue_keys_reads_a_heading_that_carries_a_suffix(
    tmp_path: Path
) -> None:
    """A heading the exact-line match missed — `## Issue Grouping Map (revised)`
    — reads as a map claiming nothing, so every sub-issue the map names loses
    its only route to its epic. A typo turning a decomposed feature back into an
    unresolved one."""
    (tmp_path / "delivery.md").write_text(
        _delivery_map("#575").replace("## Issue Grouping Map", "## Issue Grouping Map (revised)")
    )

    assert delivery_issue_keys(tmp_path, r"\d+") == {"575"}


def test_delivery_issue_keys_ignores_cells_that_are_not_the_issue_column(
    tmp_path: Path
) -> None:
    """Two scopes at once, both load-bearing. Column: the hand-rolled scan this
    replaces searched the whole row, so `T001-T005` and `PR #1` became claims.
    Section: the wave table below the map is not more issues. A claim invented
    for the wrong feature is exactly the bug being fixed."""
    (tmp_path / "delivery.md").write_text(_delivery_map("#575"))

    assert delivery_issue_keys(tmp_path, r"\d+") == {"575"}


def test_resolve_agent_dir_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    override = tmp_path / "custom-state"
    monkeypatch.setenv("WFCTL_STATE_DIR", str(override))
    result = resolve_agent_dir(tmp_path, "422-branch")
    assert result == override
    assert result.exists()


def test_resolve_agent_dir_creates_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    override = tmp_path / "nonexistent" / "deep" / "dir"
    monkeypatch.setenv("WFCTL_STATE_DIR", str(override))
    result = resolve_agent_dir(tmp_path, "422-branch")
    assert result.exists()


def test_resolve_agent_dir_xdg_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WFCTL_STATE_DIR", raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg"))
    repo = tmp_path / "myrepo"
    repo.mkdir()
    result = resolve_agent_dir(repo, "123-feature")
    assert result == tmp_path / "xdg" / "wfctl" / "myrepo" / "123-feature"
    assert result.exists()


def test_resolve_agent_dir_keys_on_main_checkout_not_worktree(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A linked worktree's directory is named after its branch, so keying state on
    it would fabricate a repo per branch and split one project's state across all
    of them. The main checkout's name is the project's name from anywhere."""
    import subprocess

    def git(*args: str, cwd: Path | None = None) -> str:
        return subprocess.run(
            ["git", "-C", str(cwd or repo_root), *args],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

    _init_commit(repo_root)
    monkeypatch.delenv("WFCTL_STATE_DIR", raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))

    wt = tmp_path / "wt" / "330-epic-not-yet-decomposed"
    git("worktree", "add", "-b", "330-epic-not-yet-decomposed", str(wt))

    from_main = resolve_agent_dir(repo_root, "330-epic-not-yet-decomposed")
    from_worktree = resolve_agent_dir(wt, "330-epic-not-yet-decomposed")

    assert from_main == from_worktree
    assert from_worktree.parent.name == repo_root.name


def test_project_name_from_a_worktree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The project's name, not the worktree's directory name.

    `--show-toplevel` returns the *worktree* path, so its basename is the branch
    handle. Deriving the name that way would write `window_prefix:
    '9-align-node-versions__'` into a committed file from a seed-once command.
    `--git-common-dir` points at the main checkout's .git from anywhere in the
    repo, which is what makes both call sites below agree.

    This is the regression guard the helper never had — it shipped with one
    caller and zero tests.
    """
    import subprocess

    # Not the `repo_root` fixture: this test needs the checkout directory to have
    # a name distinguishable from the worktree's, which is the whole point.
    repo_root = tmp_path / "myproject"
    repo_root.mkdir()
    subprocess.run(["git", "init", str(repo_root)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "config", "user.email", "test@test.com"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_root), "config", "user.name", "Test"],
        check=True, capture_output=True,
    )
    _init_commit(repo_root)

    wt = tmp_path / "myproject" / "wt" / "9-align-node-versions"
    subprocess.run(
        ["git", "-C", str(repo_root), "worktree", "add", "-b", "9-align-node-versions", str(wt)],
        check=True, capture_output=True,
    )

    assert project_name(repo_root) == "myproject"
    assert project_name(wt) == "myproject"
    assert project_name(wt) != wt.name, "would be the branch handle, not the project"


# --- spec_root: where a repo's specs live (issue #18) ------------------------


def _write_manifest(repo_root: Path, **keys: str) -> None:
    """Write a manifest carrying a realistic layer entry plus the given keys."""
    import json
    payload: dict = {"base": {"repo": "x", "ref": "main", "commit": "c", "items": []}}
    payload.update(keys)
    (repo_root / ".wf-skills-manifest.json").write_text(json.dumps(payload))


def test_spec_root_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Precedence: env override > manifest > repo_root/specs.

    The env var stays a per-invocation escape hatch — it is process-global, so
    exporting it from a shell profile would redirect every repo wfctl touches.
    That is why the persistent setting lives in the manifest instead.
    """
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    assert spec_root(tmp_path) == tmp_path / "specs"

    _write_manifest(tmp_path, spec_root=str(tmp_path / "from-manifest"))
    assert spec_root(tmp_path) == tmp_path / "from-manifest"

    monkeypatch.setenv("WFCTL_SPEC_DIR", str(tmp_path / "from-env"))
    assert spec_root(tmp_path) == tmp_path / "from-env"


def test_spec_root_empty_value_is_not_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty string means "not recorded", not "resolve to the repo root"."""
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    _write_manifest(tmp_path, spec_root="")
    assert spec_root(tmp_path) == tmp_path / "specs"


def test_spec_root_never_creates_the_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A root that does not exist yet is the case that broke the create
    path — `resolve_spec_dir` returned None for it and the hardcoded fallback
    took over. Resolving must never validate or create it."""
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    target = tmp_path / "not-created-yet"
    _write_manifest(tmp_path, spec_root=str(target))
    assert spec_root(tmp_path) == target
    assert not target.exists()


def test_spec_root_path_forms(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Absolute as-is; `~` expanded at read time; relative anchored to
    the manifest's own directory, never cwd — so one relative value declared
    once means one shared location from every worktree."""
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)

    _write_manifest(tmp_path, spec_root="/srv/specs")
    assert spec_root(tmp_path) == Path("/srv/specs")

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    _write_manifest(tmp_path, spec_root="~/Development/pfms-specs")
    assert spec_root(tmp_path) == home / "Development" / "pfms-specs"

    _write_manifest(tmp_path, spec_root="../shared-specs")
    monkeypatch.chdir(home)  # cwd must not influence the result
    assert spec_root(tmp_path) == (tmp_path / ".." / "shared-specs").resolve()


def test_feature_paths_uses_spec_root_when_no_spec_dir_exists(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The core regression.

    `resolve_spec_dir` honored WFCTL_SPEC_DIR, but `feature-paths` hardcoded
    `repo_root/specs/<branch>` when nothing existed yet — so reads were
    redirectable and creates were not. Every speckit script routes through this
    command, so that one line decided where every new spec was written.
    """
    from typer.testing import CliRunner

    from wfctl.cli import app

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo_root))
    monkeypatch.setenv("WFCTL_BRANCH", "18-spec-root")
    monkeypatch.setenv("WFCTL_STATE_DIR", str(tmp_path / "state"))
    elsewhere = tmp_path / "outside-the-repo"
    _write_manifest(repo_root, spec_root=str(elsewhere))

    result = CliRunner().invoke(app, ["feature-paths"])

    assert result.exit_code == 0, result.output
    assert f"FEATURE_DIR='{elsewhere / '18-spec-root'}'" in result.output
    assert str(repo_root / "specs") not in result.output


def test_recorded_root_does_not_fall_back_to_in_repo_specs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The recorded root is the only root.

    Falling back would let one feature's artifacts split across two locations —
    spec.md found in the old root while plan.md is written to the new one.
    """
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    (tmp_path / "specs" / "18-legacy").mkdir(parents=True)
    _write_manifest(tmp_path, spec_root=str(tmp_path / "configured"))

    assert resolve_spec_dir("18-legacy", tmp_path) is None


def test_spec_root_matches_by_issue_key_under_the_configured_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only the root moves. Exact-name and issue-key matching are
    unchanged, and still apply under a configured root."""
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    configured = tmp_path / "configured"
    target = configured / "18-recorded-name"
    target.mkdir(parents=True)
    _write_manifest(tmp_path, spec_root=str(configured))

    assert resolve_spec_dir("18-different-slug", tmp_path) == target


def test_unparseable_manifest_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A malformed manifest is a broken repo, not a missing setting.

    Defaulting silently would put specs back inside the worktree with no signal
    — the exact failure this feature removes.
    """
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    (tmp_path / ".wf-skills-manifest.json").write_text("{not json")

    with pytest.raises(json.JSONDecodeError):
        spec_root(tmp_path)


def _worktree_project(tmp_path: Path) -> tuple[Path, Path]:
    """A real main checkout plus a linked worktree. Returns (main, worktree).

    Real git, no mocking: the fallback keys on `git rev-parse --git-common-dir`,
    and the layout it must distinguish (`.git` file in a worktree pointing at the
    main checkout's `.git` dir) is not something a fake reproduces faithfully.
    """
    import subprocess

    main = tmp_path / "myproject"
    main.mkdir()
    subprocess.run(["git", "init", str(main)], check=True, capture_output=True)
    for key, val in (("user.email", "test@test.com"), ("user.name", "Test")):
        subprocess.run(["git", "-C", str(main), "config", key, val],
                       check=True, capture_output=True)
    _init_commit(main)

    wt = main / "wt" / "18-spec-root"
    subprocess.run(
        ["git", "-C", str(main), "worktree", "add", "-b", "18-spec-root", str(wt)],
        check=True, capture_output=True,
    )
    return main, wt


def test_worktree_inherits_spec_root_from_main_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The whole reason the fallback exists.

    The manifest is gitignored and `install-skills` regenerates it in every
    fresh worktree, so a worktree-local spec_root cannot exist at the moment the
    pipeline first runs there. Without this, specs fall back into the worktree
    and die with it — the failure this feature removes.
    """
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    main, wt = _worktree_project(tmp_path)
    _write_manifest(main, spec_root=str(tmp_path / "shared-specs"))
    _write_manifest(wt)  # what install-skills writes: layers, no spec_root

    assert spec_root(wt) == tmp_path / "shared-specs"


def test_worktree_own_spec_root_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The fallback is a fallback: a worktree that declares its own is not
    overridden by the main checkout's."""
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    main, wt = _worktree_project(tmp_path)
    _write_manifest(main, spec_root=str(tmp_path / "main-specs"))
    _write_manifest(wt, spec_root=str(tmp_path / "worktree-specs"))

    assert spec_root(wt) == tmp_path / "worktree-specs"


def test_no_main_checkout_reads_no_outside_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The guard on reading a manifest outside this repo.

    In a bare or separate-gitdir layout the common dir is `<name>.git`, and its
    parent is a container directory that may hold an unrelated project's
    manifest. Reading that would silently apply another repo's spec root, so a
    common dir not named exactly `.git` gets no fallback at all.
    """
    import subprocess

    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    container = tmp_path / "container"
    container.mkdir()
    # The sibling manifest that must NOT be read.
    _write_manifest(container, spec_root=str(tmp_path / "someone-elses-specs"))

    repo = container / "checkout"
    repo.mkdir()
    gitdir = container / "myproject.git"
    subprocess.run(
        ["git", "init", "--separate-git-dir", str(gitdir), str(repo)],
        check=True, capture_output=True,
    )
    _write_manifest(repo)  # layers only, no spec_root

    assert spec_root(repo) == repo / "specs"


def test_unparseable_main_checkout_manifest_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Raising covers both manifests. The current-repo half is pinned above;
    this is the half that only exists once the fallback does."""
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    main, wt = _worktree_project(tmp_path)
    (main / ".wf-skills-manifest.json").write_text("{not json")
    _write_manifest(wt)  # the worktree's own is fine and declares nothing

    with pytest.raises(json.JSONDecodeError):
        spec_root(wt)


def test_relative_spec_root_in_main_checkout_is_one_shared_location(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Relative values across worktrees: one anchors to the manifest that
    declared it, so main checkout and worktree resolve to the same directory —
    the property that makes `../pfms-specs` usable at all."""
    from wfctl._paths import spec_root

    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    main, wt = _worktree_project(tmp_path)
    _write_manifest(main, spec_root="../shared-specs")
    _write_manifest(wt)

    assert spec_root(wt) == spec_root(main) == (main / ".." / "shared-specs").resolve()


def test_issue_key_match_ignores_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The key glob returns a spec *directory*, never a file that shares the key.

    The exact-name branch has always checked `is_dir()`; the glob branch took
    `matches[0]` blind. A stray `42-notes.md` beside `42-feature/` sorts first
    and was handed back as the feature dir, making FEATURE_SPEC a path *inside*
    a file: `specs/42-notes.md/spec.md`.
    """
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    specs = tmp_path / "specs"
    real = specs / "42-feature"
    real.mkdir(parents=True)
    (specs / "42-aaa-notes.md").write_text("stray")

    # Branch name differs from the dir name, so resolution goes through the glob.
    assert resolve_spec_dir("42-renamed", tmp_path) == real


def test_issue_key_match_with_no_matching_directory_is_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Files alone are not a match — better no spec dir than a bogus one."""
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "42-notes.md").write_text("stray")

    assert resolve_spec_dir("42-renamed", tmp_path) is None


def test_worktree_branches_drops_a_worktree_whose_directory_is_gone(
    agent_dir: Path, tmp_path: Path
) -> None:
    """A deleted directory leaves the branch in `worktree list`, marked prunable.

    Reading the `branch` line alone reports a checkout that is not there, and the
    caller — `wfctl issue stop`, asking whether anyone else holds this issue —
    then gets a yes that never becomes a no, so the board sticks on `In Progress`
    for good. Whole records rather than matching lines is what sees the marker.
    """
    import subprocess

    repo_root = agent_dir.parent
    ghost = tmp_path / "ghost-worktree"
    subprocess.run(
        ["git", "-C", str(repo_root), "worktree", "add", "-b", "42-ghost", str(ghost)],
        check=True, capture_output=True,
    )
    assert "42-ghost" in worktree_branches(repo_root)

    shutil.rmtree(ghost)
    assert "42-ghost" not in worktree_branches(repo_root)
