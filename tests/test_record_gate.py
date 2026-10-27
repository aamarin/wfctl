"""Tests for the guard's record checks (`wfctl/_record_gate.py`).

Each test runs a hook payload through `_hook.worktree_guard`, the same way the
host does, on the real repository `test_review_gate.py` builds: a bare
`origin`, a `main` checkout, and worktrees on `604-x` and `630-x`. The review
groups are completed first in every test that expects the record checks to
run, since they run only once the review check finds nothing pending.
"""
from __future__ import annotations

import json
import shlex
from pathlib import Path

import pytest

from tests.test_paths import _delivery_map
from tests import test_review_gate
from tests.test_review_gate import Guard, Repos, git
from wfctl import _design_exceptions, _review_gate

# `test_review_gate`'s repository and guard, shared rather than rebuilt: the
# record checks run only after its review check, on the same repository.
repos = test_review_gate.repos
guard = test_review_gate.guard

RECORD = "---\nstatus: {status}\n---\n\n# A decision\n"


@pytest.fixture
def specs(repos: Repos, monkeypatch: pytest.MonkeyPatch) -> Path:
    """One spec root every checkout reads, as a repo that records a spec root
    outside its working tree does."""
    root = repos.tmp / "specs"
    root.mkdir()
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(root))
    return root


def record(repo: Path, slug: str, status: str, under: str = "") -> str:
    """Commit one record on `repo`'s branch and push it, returning the commit."""
    folder = repo / "docs" / "architecture" / under
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{slug}.md").write_text(RECORD.format(status=status))
    git(repo, "add", "docs")
    git(repo, "commit", "-q", "-m", f"record {slug}")
    git(repo, "push", "-q", "origin", "HEAD")
    return git(repo, "rev-parse", "HEAD")


def own_exception(specs: Path, branch: str) -> Path:
    spec_dir = specs / branch
    _design_exceptions.write(spec_dir, _design_exceptions.BOUNDARY, "nothing moves")
    return _design_exceptions.path(spec_dir, _design_exceptions.BOUNDARY)


def test_a_record_contradicting_the_branchs_own_answer_is_refused(
    repos: Repos, guard: Guard, specs: Path,
) -> None:
    """Scenario 5.3. The gate reads the exception before it asks git about
    records, so a "no new boundary" written early and a record added later both
    pass it. The record is the answer, so the refusal says to delete the
    exception and prints the path to delete."""
    exception = own_exception(specs, "604-x")
    record(repos.feature, "owns-a-thing", "accepted")
    repos.complete(repos.feature, "604-x")

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert err == (
        "✗ 604-x touches docs/architecture/owns-a-thing.md, but its spec folder says no "
        "boundary moved.\n"
        "  The record answers the boundary question, so delete the exception:\n"
        f"  rm {shlex.quote(str(exception))}\n"
    )


def test_an_exception_inherited_from_an_epic_is_not_a_contradiction(
    repos: Repos, guard: Guard, specs: Path,
) -> None:
    """Scenario 5.4. The epic's "no" stays true for its other sub-issues, and
    this sub-issue's record answers the question for it, so refusing would ask
    the sub-issue to delete an answer its siblings still rely on."""
    epic = specs / "600-epic"
    epic.mkdir()
    (epic / "delivery.md").write_text(_delivery_map("#604"))
    _design_exceptions.write(epic, _design_exceptions.BOUNDARY, "the epic reuses the store")
    record(repos.feature, "owns-a-thing", "accepted")
    repos.complete(repos.feature, "604-x")

    assert guard("gh pr create --fill", repos.feature) == (0, "")


def test_a_proposed_record_holds_both_the_create_and_the_merge(
    repos: Repos, guard: Guard, specs: Path,
) -> None:
    """Scenario 5.5. Before this, a record nobody accepted showed as an unmet
    fact in `wfctl status` and nothing else, so an unattended run could open
    and merge a PR whose boundary nobody approved."""
    head = record(repos.feature, "owns-a-thing", "proposed")
    repos.complete(repos.feature, "604-x")
    repos.gh(prs={"": {"headRefName": "604-x", "headRefOid": head}})
    expected = (
        "✗ 604-x touches records nobody has accepted:\n"
        "  owns-a-thing (proposed)\n"
        "  Ask a person to accept or reject each one before the PR opens.\n"
    )

    assert guard("gh pr create --fill", repos.feature) == (2, expected)
    assert guard("gh pr merge --merge", repos.feature) == (2, expected)


def test_a_merge_from_main_reads_the_status_at_the_prs_head(
    repos: Repos, guard: Guard, specs: Path,
) -> None:
    """Scenario 5.6. `gh pr merge` from the `main` checkout judges a branch that
    isn't checked out. A check that read the working tree would find `main`'s
    records there, here an accepted copy of the same slug, and let the merge
    through."""
    head = record(repos.other, "owns-a-thing", "proposed")
    repos.complete(repos.other, "630-x")
    repos.gh(prs={"630": {"headRefName": "630-x", "headRefOid": head}})
    stale = repos.main / "docs" / "architecture"
    stale.mkdir(parents=True)
    (stale / "owns-a-thing.md").write_text(RECORD.format(status="accepted"))

    code, err = guard("gh pr merge 630", repos.main)

    assert code == 2
    assert "  owns-a-thing (proposed)" in err


def test_a_git_failure_reading_the_records_refuses(
    repos: Repos, guard: Guard, specs: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-018. Like the review check, an error refuses: a check that allowed on
    error would let every bug through as an approved boundary."""
    record(repos.feature, "owns-a-thing", "accepted")
    repos.complete(repos.feature, "604-x")
    run = _review_gate._Session.run

    def diff_fails(self: _review_gate._Session, *args: str) -> str:
        if args[0] == "git" and "diff" in args:
            raise _review_gate._Failed("git diff failed: bad revision")
        return run(self, *args)

    monkeypatch.setattr(_review_gate._Session, "run", diff_fails)

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert "✗ the review check failed: git diff failed: bad revision" in err


@pytest.mark.parametrize("exception", [True, False], ids=["exception", "no-exception"])
def test_a_level_3_record_alone_passes_both_checks(
    repos: Repos, guard: Guard, specs: Path, exception: bool,
) -> None:
    """A level-3 record governs one feature and draws no boundary, so it
    neither contradicts "no new boundary" nor needs a person's ruling here."""
    if exception:
        own_exception(specs, "604-x")
    record(repos.feature, "a-choice", "proposed", under="design")
    repos.complete(repos.feature, "604-x")

    assert guard("gh pr create --fill", repos.feature) == (0, "")


def test_a_deleted_file_under_the_arch_root_passes(
    repos: Repos, guard: Guard, specs: Path,
) -> None:
    """A deleted record decides nothing a person has to rule on, at the top
    level or under a subdirectory, so `--diff-filter=d` leaves it out."""
    record(repos.main, "old", "proposed")
    record(repos.main, "a-scan", "proposed", under="scans")
    git(repos.feature, "fetch", "-q", "origin")
    git(repos.feature, "merge", "-q", "origin/main")
    git(repos.feature, "rm", "-q", "docs/architecture/old.md", "docs/architecture/scans/a-scan.md")
    git(repos.feature, "commit", "-q", "-m", "drop them")
    repos.complete(repos.feature, "604-x")

    assert guard("gh pr create --fill", repos.feature) == (0, "")


def test_a_record_the_trunk_gained_after_the_branch_point_is_not_the_branchs(
    repos: Repos, guard: Guard, specs: Path,
) -> None:
    """The diff runs from the merge base, so a proposed record that reached
    `main` after the branch was cut holds only the branch that wrote it."""
    record(repos.main, "someone-elses", "proposed")
    git(repos.feature, "fetch", "-q", "origin")
    repos.complete(repos.feature, "604-x")

    assert guard("gh pr create --fill", repos.feature) == (0, "")


def test_the_guard_lists_the_records_the_accepted_fact_lists(
    repos: Repos, specs: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The guard and the "architecture accepted" fact have to agree on which
    records the branch changed. Built twice, they would drift, and a branch
    held for a record the fact never listed is held for a reason nothing else
    on screen names."""
    from wfctl._evidence import branch_records
    from wfctl._paths import arch_root, trunk_branch
    from wfctl._record_gate import touched

    record(repos.main, "old", "accepted")
    git(repos.feature, "fetch", "-q", "origin")
    git(repos.feature, "merge", "-q", "origin/main")
    record(repos.feature, "new-one", "proposed")
    record(repos.feature, "a-choice", "proposed", under="design")
    record(repos.feature, "a-scan", "proposed", under="scans")
    git(repos.feature, "rm", "-q", "docs/architecture/old.md")
    git(repos.feature, "commit", "-q", "-m", "drop old")
    monkeypatch.chdir(repos.feature)
    monkeypatch.setenv("WFCTL_BRANCH", "604-x")

    session = _review_gate._Session.open(str(repos.feature))
    trunk = trunk_branch(repos.feature)
    assert trunk is not None
    head = git(repos.feature, "rev-parse", "HEAD")
    listed = sorted(p.stem for p in touched(session, trunk, head))

    assert listed == ["new-one"]
    assert listed == sorted(branch_records(repos.feature, arch_root(repos.feature)))


def test_a_branch_with_no_records_passes_whatever_its_spec_folder_says(
    repos: Repos, guard: Guard, specs: Path,
) -> None:
    """The existing guard tests run on branches with no records, and must stay
    green unchanged. The record checks ask git for nothing more once the list
    comes back empty."""
    own_exception(specs, "604-x")
    repos.complete(repos.feature, "604-x")

    assert guard("gh pr create --fill", repos.feature) == (0, "")
    assert json.loads(repos.table.read_text())["repo"] == "acme/widgets"


def test_the_printed_rm_survives_a_quote_in_the_spec_folders_path(
    repos: Repos, guard: Guard, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The refusal tells the agent to run the `rm` it prints. Wrapped in bare
    single quotes, a path holding one closed the quote early, so the shell ran
    the rest of the path as a second command."""
    root = repos.tmp / "it's specs"
    root.mkdir()
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(root))
    exception = own_exception(root, "604-x")
    record(repos.feature, "owns-a-thing", "accepted")
    repos.complete(repos.feature, "604-x")

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    command = err.splitlines()[-1].strip()
    assert shlex.split(command) == ["rm", str(exception)]


def test_a_proposed_record_with_a_non_ascii_name_still_holds_the_pr(
    repos: Repos, guard: Guard, specs: Path,
) -> None:
    """Git quotes a path holding a non-ASCII character in `--name-only` output,
    so the line ended in `.md"` and the `.md` test dropped it. A proposed
    record named that way let a PR open that nobody had accepted."""
    record(repos.feature, "décision", "proposed")
    repos.complete(repos.feature, "604-x")

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert "décision (proposed)" in err


def test_a_proposed_record_with_a_quote_in_its_name_still_holds_the_pr(
    repos: Repos, guard: Guard, specs: Path,
) -> None:
    """`core.quotePath=false` stops git quoting non-ASCII names only. A name
    holding `"` still came back quoted, ending in `.md"`, and the guard dropped
    it while `branch_records` listed it."""
    record(repos.feature, 'a"b', "proposed")
    repos.complete(repos.feature, "604-x")

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert 'a"b (proposed)' in err


def test_a_folder_found_by_issue_number_is_the_branchs_own(
    repos: Repos, guard: Guard, specs: Path,
) -> None:
    """Plan review PR-020. `resolve_spec_dir` finds `604-other` for branch
    `604-x` by its issue number, so the folder is the branch's own. Comparing
    exact names called it an epic's, and the guard let a record through beside
    the branch's own "no boundary moved"."""
    spec_dir = specs / "604-other"
    _design_exceptions.write(spec_dir, _design_exceptions.BOUNDARY, "nothing moves")
    record(repos.feature, "owns-a-thing", "accepted")
    repos.complete(repos.feature, "604-x")

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert "but its spec folder says no boundary moved" in err
