from __future__ import annotations

from pathlib import Path

import pytest

from wfctl._bundle import TREES, content_hash

# A tree with one file in each of the six sourceable directories, including the
# dot-prefixed workmux config — the file setuptools' globs drop by default and
# the stdlib `glob` module cannot see.
_FIXED_TREE = {
    "agents/skills/alpha/SKILL.md": "alpha\n",
    "agents/commands/beta.md": "beta\n",
    "agents/trackers/github.json": '{"key_pattern": "\\\\d+"}\n',
    "agents/configs/workmux/.workmux.yaml": "session: x\n",
    "specify/scripts/bash/run.sh": "#!/usr/bin/env bash\necho hi\n",
    "specify/templates/plan-template.md": "# Plan\n",
}

# Recorded, not computed at test time. Equality-within-one-run passes even if
# macOS and Linux disagree about the digest, and that is exactly the split this
# repo runs across: development on darwin, CI on ubuntu-latest only. A literal
# is the only form of this assertion that catches it.
_FIXED_TREE_DIGEST = "9a8acd2b883c10f11cf688322c2a5560648a02db849c1f11518cd105646c95e5"


def _build(root: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return root


def test_content_hash_is_stable_for_identical_trees(tmp_path: Path) -> None:
    forward = _build(tmp_path / "forward", _FIXED_TREE)
    backward = _build(tmp_path / "backward", dict(reversed(list(_FIXED_TREE.items()))))

    assert content_hash(forward) == content_hash(backward)
    assert content_hash(forward) == _FIXED_TREE_DIGEST


def test_content_hash_changes_on_edit_and_on_rename(tmp_path: Path) -> None:
    original = _build(tmp_path / "original", _FIXED_TREE)
    baseline = content_hash(original)

    edited = _build(tmp_path / "edited", _FIXED_TREE)
    (edited / "agents/commands/beta.md").write_text("beta!\n")
    assert content_hash(edited) != baseline

    # Same bytes, new path. A hash over contents alone cannot tell these apart,
    # and a repo that renamed a command would be reported as current.
    renamed = _build(tmp_path / "renamed", _FIXED_TREE)
    (renamed / "agents/commands/beta.md").rename(renamed / "agents/commands/gamma.md")
    assert content_hash(renamed) != baseline


@pytest.mark.parametrize("relative_path", list(_FIXED_TREE))
def test_content_hash_covers_every_sourceable_directory(
    tmp_path: Path, relative_path: str
) -> None:
    """Every directory an install can source from must be inside the hash.

    `agents/trackers/` is the case a per-layer hash would miss — it is copied
    inline and belongs to no target list. The other five catch a hash that
    silently skips a subtree.
    """
    baseline = content_hash(_build(tmp_path / "baseline", _FIXED_TREE))

    mutated = _build(tmp_path / "mutated", _FIXED_TREE)
    (mutated / relative_path).write_text("changed\n")

    assert content_hash(mutated) != baseline


def test_content_hash_ignores_everything_outside_the_bundled_trees(
    tmp_path: Path,
) -> None:
    """The hash is scoped to the vendored trees, not the whole package.

    `BUNDLE_ROOT` is the `wfctl` package directory, which also holds `cli.py` and
    `__pycache__`. Hashing those would report every code edit as installed-content
    drift, and make the value depend on what had been imported.
    """
    root = _build(tmp_path / "root", _FIXED_TREE)
    baseline = content_hash(root)

    (root / "cli.py").write_text("# not bundled content\n")
    (root / "__pycache__").mkdir()
    (root / "__pycache__" / "cli.cpython-311.pyc").write_bytes(b"\x00\x01")

    assert content_hash(root) == baseline


def test_content_hash_is_defined_for_a_tree_that_is_missing_one_half(
    tmp_path: Path,
) -> None:
    """A partial root hashes rather than raising.

    The fake bundle the suite installs has no `specify/` at all, so this is the
    common case in tests, not a corner of it.
    """
    agents_only = {k: v for k, v in _FIXED_TREE.items() if k.startswith("agents/")}
    root = _build(tmp_path / "partial", agents_only)

    assert content_hash(root)
    assert content_hash(root) != content_hash(_build(tmp_path / "full", _FIXED_TREE))


def test_trees_are_the_two_vendored_directories() -> None:
    """Guards the pairing with `[tool.setuptools.package-data]` in pyproject.toml.

    A third vendored tree has to be added in both places: one ships the files,
    the other notices when they change. This test is what makes the second half
    fail loudly instead of silently under-hashing.
    """
    assert TREES == ("agents", "specify")
