"""The git side of the redraw exemption: which changed records a skip may drop.

`arch.redraw_only` reads a record, and `_paths` asks git for the diff it reads.
These tests run against a real repository with a stand-in skip, so a failure
here is about the diff's base and what counts as "no file to compare", not about
the Log format.
"""
import subprocess
from pathlib import Path

from tests.conftest import git_repo

RECORD = "docs/architecture/rec.md"
BODY = "# Rec\n\n## Decision\n\nWe pick A.\n\n## Log\n\n- 2026-01-01  accepted\n"
REDRAW = "- 2026-02-01  redrawn  fixed layout\n"


def _skip(diff: str, text: str) -> bool:
    """True when the diff only adds `redrawn` lines and removes none."""
    lines = diff.splitlines()
    added = [x for x in lines if x.startswith("+") and not x.startswith("+++")]
    removed = [x for x in lines if x.startswith("-") and not x.startswith("---")]
    return bool(added) and not removed and all("redrawn" in x for x in added)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _branch_with_record(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A repo whose `main` holds the record and whose checked-out branch is a feature."""
    repo = git_repo(tmp_path / "repo")
    arch = repo / "docs" / "architecture"
    arch.mkdir(parents=True)
    (arch / "rec.md").write_text(BODY)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "record")
    _git(repo, "checkout", "-b", "feature")
    return repo, arch, arch / "rec.md"


def _commit_redraw(repo: Path, record: Path) -> None:
    with record.open("a") as f:
        f.write(REDRAW)
    _git(repo, "commit", "-am", "redraw")


def test_a_committed_redraw_is_dropped_by_skip_and_decides_nothing(tmp_path: Path) -> None:
    """A branch whose only change to a record is a redraw has made no decision.

    This is the reason for the exemption: without it the record gate refuses a
    branch that truthfully says no boundary moved.
    """
    from wfctl._paths import decided_on_this_branch, records_on_this_branch

    repo, arch, record = _branch_with_record(tmp_path)
    _commit_redraw(repo, record)

    assert records_on_this_branch(repo, arch) == ["rec"]
    assert records_on_this_branch(repo, arch, skip=_skip) == []
    assert decided_on_this_branch(repo, arch, [], _skip) is False


def test_an_uncommitted_edit_beside_a_committed_redraw_keeps_the_record(tmp_path: Path) -> None:
    """The diff runs to the working tree, so a hand edit can't hide behind a redraw.

    Diffing only `trunk...HEAD` saw the redraw alone and let the second edit
    through unreviewed (PR-025).
    """
    from wfctl._paths import decided_on_this_branch, records_on_this_branch

    repo, arch, record = _branch_with_record(tmp_path)
    _commit_redraw(repo, record)
    record.write_text(record.read_text().replace("We pick A.", "We pick B."))

    assert records_on_this_branch(repo, arch, skip=_skip) == ["rec"]
    assert decided_on_this_branch(repo, arch, [], _skip) is True


def test_record_change_returns_the_diff_and_the_current_text(tmp_path: Path) -> None:
    """`skip` gets the merge-base diff of one file, plus the file as it stands now."""
    from wfctl._paths import record_change

    repo, arch, record = _branch_with_record(tmp_path)
    _commit_redraw(repo, record)

    change = record_change(repo, record)

    assert change is not None
    diff, text = change
    assert "+- 2026-02-01  redrawn  fixed layout" in diff
    assert "+++ b/" + RECORD in diff
    assert text == record.read_text()


def test_record_change_ignores_the_users_diff_color_and_external_tool(tmp_path: Path) -> None:
    """The code panel on #769 found both diffs reading the user's git config.
    `color.ui=always` wraps each hunk header in escape codes, so a real redraw
    read as a boundary change, and `diff.external` replaces the hunks with
    whatever the tool prints, which can pass a change off as a redraw."""
    from wfctl._paths import record_change

    repo, arch, record = _branch_with_record(tmp_path)
    _commit_redraw(repo, record)
    _git(repo, "config", "color.ui", "always")
    _git(repo, "config", "diff.external", "echo")

    change = record_change(repo, record)

    assert change is not None
    diff, _ = change
    assert "\x1b[" not in diff
    assert "\n@@ " in diff
    assert "+- 2026-02-01  redrawn  fixed layout" in diff


def test_an_untracked_new_record_is_never_dropped(tmp_path: Path) -> None:
    """The merge base has no file for a new record, so there is nothing to call a redraw."""
    from wfctl._paths import decided_on_this_branch, record_change, records_on_this_branch

    repo, arch, _ = _branch_with_record(tmp_path)
    new = arch / "fresh.md"
    new.write_text(BODY + REDRAW)

    assert record_change(repo, new) is None
    assert records_on_this_branch(repo, arch, skip=lambda d, t: True) == ["fresh"]
    assert decided_on_this_branch(repo, arch, [], lambda d, t: True) is True


def test_a_record_deleted_in_the_working_tree_is_never_dropped(tmp_path: Path) -> None:
    """A deletion is listed by git status, and a deleted file has no text to judge."""
    from wfctl._paths import record_change, records_on_this_branch

    repo, arch, record = _branch_with_record(tmp_path)
    record.unlink()

    assert record_change(repo, record) is None
    assert records_on_this_branch(repo, arch, skip=lambda d, t: True) == ["rec"]


def test_a_repo_with_no_trunk_never_drops_a_record(tmp_path: Path) -> None:
    """Without a trunk there is no merge base, and a skip that guessed one could hide a change.

    The redraw is left uncommitted, since with no trunk the listing reads only
    `git status`, and a committed change wouldn't be listed for the skip to drop.
    """
    from wfctl._paths import record_change, records_on_this_branch, trunk_branch

    repo, arch, record = _branch_with_record(tmp_path)
    with record.open("a") as f:
        f.write(REDRAW)
    _git(repo, "branch", "-m", "main", "base")
    assert trunk_branch(repo) is None

    assert record_change(repo, record) is None
    assert records_on_this_branch(repo, arch, skip=lambda d, t: True) == ["rec"]
