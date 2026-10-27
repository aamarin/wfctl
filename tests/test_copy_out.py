"""Tests for `wfctl._copy_out` — copy a worktree's spec files to the main checkout's spec dir."""
from __future__ import annotations

from pathlib import Path

import pytest

from wfctl import _copy_out


def _write(path: Path, text: str | bytes = "x\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(text, bytes):
        path.write_bytes(text)
    else:
        path.write_text(text)
    return path


@pytest.fixture
def dirs(tmp_path: Path) -> tuple[Path, Path]:
    """A source spec dir inside a worktree and a destination in the main checkout."""
    return tmp_path / "wt" / "specs" / "40-x", tmp_path / "main" / "specs" / "40-x"


def test_missing_file_is_copied_and_an_identical_one_is_left_alone(
    dirs: tuple[Path, Path],
) -> None:
    """Identical files never stop a removal, and rewriting them would only touch timestamps (FR-026)."""
    source, dest = dirs
    _write(source / "spec.md", "same\n")
    _write(source / "plan.md", "new\n")
    _write(dest / "spec.md", "same\n")
    before = (dest / "spec.md").stat().st_mtime_ns

    result = _copy_out.plan(source, dest)
    _copy_out.apply(result, overwrite=False)

    assert result.missing == ["plan.md"]
    assert result.same == ["spec.md"]
    assert result.different == {}
    assert (dest / "plan.md").read_text() == "new\n"
    assert (dest / "spec.md").stat().st_mtime_ns == before


def test_differing_file_carries_a_diff_with_the_destination_first(
    dirs: tuple[Path, Path],
) -> None:
    """The diff is what lets a person decide whether the older copy has something the newer one lacks (FR-024)."""
    source, dest = dirs
    _write(source / "spec.md", "one\nthree\n")
    _write(dest / "spec.md", "one\ntwo\n")

    result = _copy_out.plan(source, dest)

    diff = result.different["spec.md"]
    assert "--- main checkout/spec.md" in diff
    assert "+++ worktree/spec.md" in diff
    assert "-two" in diff
    assert "+three" in diff
    assert diff.index("-two") < diff.index("+three")


def test_a_differing_file_is_not_written_without_overwrite(dirs: tuple[Path, Path]) -> None:
    """The store refuses before calling `apply`, but `apply` has to be safe on its own (FR-025)."""
    source, dest = dirs
    _write(source / "spec.md", "worktree\n")
    _write(dest / "spec.md", "main\n")

    _copy_out.apply(_copy_out.plan(source, dest), overwrite=False)

    assert (dest / "spec.md").read_text() == "main\n"


def test_overwrite_replaces_only_the_differing_files(dirs: tuple[Path, Path]) -> None:
    """`--overwrite` is a decision about the files that differ and nothing else (FR-027)."""
    source, dest = dirs
    _write(source / "spec.md", "worktree\n")
    _write(source / "plan.md", "new\n")
    _write(source / "tasks.md", "same\n")
    _write(dest / "spec.md", "main\n")
    _write(dest / "tasks.md", "same\n")
    kept = dest / "tasks.md"
    before = kept.stat().st_mtime_ns

    _copy_out.apply(_copy_out.plan(source, dest), overwrite=True)

    assert (dest / "spec.md").read_text() == "worktree\n"
    assert (dest / "plan.md").read_text() == "new\n"
    assert kept.stat().st_mtime_ns == before


@pytest.mark.parametrize("overwrite", [False, True])
def test_a_file_only_in_the_destination_is_never_touched(
    dirs: tuple[Path, Path], overwrite: bool
) -> None:
    """Someone else's spec file in that folder isn't ours to delete, with or without `--overwrite` (FR-025)."""
    source, dest = dirs
    _write(source / "spec.md", "worktree\n")
    _write(dest / "notes.md", "theirs\n")

    result = _copy_out.plan(source, dest)
    _copy_out.apply(result, overwrite=overwrite)

    assert (dest / "notes.md").read_text() == "theirs\n"
    assert "notes.md" not in result.missing + result.same + list(result.different)


def test_a_file_that_is_not_utf8_reports_binary_file_differs(dirs: tuple[Path, Path]) -> None:
    """A diff of bytes that don't decode is noise, so the report says only that they differ (research R6)."""
    source, dest = dirs
    _write(source / "image.bin", b"\xff\xfe\x00one")
    _write(dest / "image.bin", b"\xff\xfe\x00two")

    result = _copy_out.plan(source, dest)

    assert result.different["image.bin"] == "binary file differs"


def test_a_copy_that_raises_propagates_so_the_store_can_stop_the_removal(
    dirs: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """`apply` raises instead of swallowing, since a swallowed failure lets the worktree be deleted (FR-028)."""
    source, dest = dirs
    _write(source / "spec.md", "new\n")

    def no_space(src: object, dst: object) -> None:
        raise OSError("No space left on device")

    monkeypatch.setattr(_copy_out.shutil, "copy2", no_space)

    with pytest.raises(OSError, match="No space left on device"):
        _copy_out.apply(_copy_out.plan(source, dest), overwrite=False)


def test_a_symlink_is_copied_as_a_link_and_never_followed(dirs: tuple[Path, Path]) -> None:
    """The plan skipped links, so a link in the spec dir was neither copied nor reported (FR-019).

    The link points outside the spec dir. Copying what it points at would bring
    unrelated content in, so the copy has to be the link itself.
    """
    source, dest = dirs
    _write(source / "spec.md", "s\n")
    outside = _write(source.parent / "outside.txt", "not a spec file\n")
    (source / "notes").symlink_to(outside)
    (source / "gone").symlink_to("does-not-exist")

    result = _copy_out.plan(source, dest)
    _copy_out.apply(result, overwrite=False)

    assert result.missing == ["gone", "notes", "spec.md"]
    assert (dest / "notes").is_symlink()
    assert (dest / "notes").readlink() == outside
    assert (dest / "gone").is_symlink()
    assert not (dest / "notes").parent.joinpath("outside.txt").exists()


def test_a_link_to_the_same_place_is_the_same_and_a_different_one_is_not(
    dirs: tuple[Path, Path],
) -> None:
    """A differing link stops the removal like a differing file, and overwrite replaces it."""
    source, dest = dirs
    _write(source / "spec.md", "s\n")
    dest.mkdir(parents=True)
    (source / "same").symlink_to("target-a")
    (dest / "same").symlink_to("target-a")
    (source / "moved").symlink_to("target-b")
    (dest / "moved").symlink_to("target-a")

    result = _copy_out.plan(source, dest)

    assert "same" in result.same
    assert list(result.different) == ["moved"]
    assert "target-b" in result.different["moved"]

    _copy_out.apply(result, overwrite=True)

    assert (dest / "moved").readlink() == Path("target-b")


def test_a_link_in_the_destination_is_replaced_and_never_written_through(
    dirs: tuple[Path, Path],
) -> None:
    """Copying onto a destination link followed it, so `--overwrite` rewrote a file outside the spec dir.

    A link that points nowhere used to read as "missing" and the copy then created
    the file at the link's target, with or without `--overwrite`.
    """
    source, dest = dirs
    _write(source / "spec.md", "worktree\n")
    _write(source / "plan.md", "worktree plan\n")
    outside = _write(dest.parent / "outside.txt", "keep me\n")
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "spec.md").symlink_to(outside)
    (dest / "plan.md").symlink_to(dest.parent / "nowhere.txt")

    result = _copy_out.plan(source, dest)

    assert sorted(result.different) == ["plan.md", "spec.md"]
    _copy_out.apply(result, overwrite=False)
    assert not (dest.parent / "nowhere.txt").exists()

    _copy_out.apply(result, overwrite=True)

    assert not (dest / "spec.md").is_symlink()
    assert (dest / "spec.md").read_text() == "worktree\n"
    assert outside.read_text() == "keep me\n"
    assert not (dest.parent / "nowhere.txt").exists()


def test_a_folder_in_the_destination_is_a_difference_and_never_filled(
    dirs: tuple[Path, Path],
) -> None:
    """A folder at the file's name used to take the file inside it, and the run still said "copied"."""
    source, dest = dirs
    _write(source / "tasks.md", "t\n")
    (dest / "tasks.md").mkdir(parents=True)

    result = _copy_out.plan(source, dest)

    assert list(result.different) == ["tasks.md"]
    with pytest.raises(OSError):
        _copy_out.apply(result, overwrite=True)
    assert not (dest / "tasks.md" / "tasks.md").exists()
