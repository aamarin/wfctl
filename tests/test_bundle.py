from __future__ import annotations

from pathlib import Path

import pytest

from wfctl._bundle import TREES, content_hash, resolve_root

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


def test_content_hash_raises_when_no_tree_is_present(tmp_path: Path) -> None:
    """A root with neither tree is a broken install, not an empty one.

    Without the guard this returns `sha256(b"")` — a stable, well-formed digest
    meaning "nothing here". `doctor` compares it against the recorded hash, sees a
    mismatch, and prescribes `install-skills`, which would then install nothing.
    """
    with pytest.raises(FileNotFoundError):
        content_hash(tmp_path / "nowhere")

    empty = tmp_path / "no-trees"
    (empty / "unrelated").mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        content_hash(empty)


def test_content_hash_distinguishes_a_path_boundary_from_its_content(
    tmp_path: Path,
) -> None:
    """The length prefixes, asserted rather than only argued for in the docstring.

    Concatenating path and bytes with no prefix makes these two trees identical to
    the digest: `agents/ab` holding `c` and `agents/a` holding `bc` both feed it
    `agents/abc`. One tree's contents impersonating another's path boundary is the
    seam the prefixes close.
    """
    left = _build(tmp_path / "left", {"agents/ab": "c"})
    right = _build(tmp_path / "right", {"agents/a": "bc"})

    assert content_hash(left) != content_hash(right)


def test_trees_match_the_grafted_directories_in_manifest_in() -> None:
    """Guards the pairing between `TREES` and `MANIFEST.in`.

    A third vendored tree has to be added in both places: the graft ships the
    files, `TREES` decides what gets hashed. The dangerous direction is grafting
    a tree and forgetting `TREES` — the files ship, nothing ever hashes them, and
    drift in them stays invisible to `doctor` forever.

    Asserting a literal here would not catch that: `TREES` would still equal its
    old value and the test would pass. Reading `MANIFEST.in` is what makes the
    assertion bidirectional rather than a change-detector for one of the two.
    """
    manifest = (Path(__file__).parent.parent / "MANIFEST.in").read_text()
    grafted = {
        line.split()[1].removeprefix("wfctl/")
        for line in manifest.splitlines()
        if line.startswith("graft ")
    }

    assert grafted == set(TREES)


def test_the_bundled_teardown_hook_names_the_current_command() -> None:
    """The seeded `pre_remove` must not hand out the pre-rename command name.

    `archive-story` is a hidden alias kept so repos seeded before the rename keep
    archiving. Shipping it in the template inverts that: every newly seeded repo
    is *born* needing the alias, so the alias can never be retired and the notice
    that reports it never goes quiet. That is the condition issue #36 exists to
    make reachable.

    Reads the real bundled file rather than a fixture — a fixture would assert
    what the test itself wrote, which is the failure mode this guards against.
    Both the hook line and the comment above it are checked: a corrected command
    beside a comment naming the old one is a contradiction the reader has to
    resolve, and the comment is what they read first.

    Resolved through `importlib.resources` rather than `_bundle.BUNDLE_ROOT`,
    which conftest's autouse `bundle` fixture repoints at a fake for every test.
    Importing that name happens to capture the real value before the fixture
    runs, so it works — but by import ordering rather than by intent, and the day
    the fake bundle grows a `configs/` directory this would silently assert
    against it. This test is specifically about what ships.
    """
    from importlib.resources import files

    template = Path(str(files("wfctl"))) / "agents" / "configs" / "workmux" / ".workmux.yaml"
    text = template.read_text()

    assert "archive-story" not in text, "the bundled hook still seeds the retired command name"
    assert "wfctl archive-specs" in text, "the bundled hook must invoke the archive command"


def test_resolve_root_accepts_the_package_directory_itself(tmp_path: Path) -> None:
    """The path holding the trees is already a bundle root.

    This is what `--from` receives when someone points it at `…/wfctl` rather
    than at the checkout around it.
    """
    root = _build(tmp_path / "pkg", _FIXED_TREE)

    assert resolve_root(root) == root.resolve()


def test_resolve_root_probes_one_level_in_for_a_checkout_root(tmp_path: Path) -> None:
    """A checkout root is what people have in hand, not the package inside it.

    `--from ../116-pr` names a worktree; the trees live at `../116-pr/wfctl`.
    Refusing that would make the failure message the only thing that teaches the
    layout.
    """
    checkout = tmp_path / "checkout"
    _build(checkout / "wfctl", _FIXED_TREE)
    (checkout / "pyproject.toml").write_text("[project]\n")

    assert resolve_root(checkout) == (checkout / "wfctl").resolve()


def test_resolve_root_prefers_the_given_path_over_the_nested_probe(tmp_path: Path) -> None:
    """A wfctl checkout holds both, and the outer one is not a bundle root.

    Only relevant because the trees at `<path>/wfctl` exist in every wfctl
    checkout: probing first would resolve `--from <checkout>/wfctl` — which is
    already correct — to `<checkout>/wfctl/wfctl`, which does not exist.
    """
    root = _build(tmp_path / "both", _FIXED_TREE)
    _build(root / "wfctl", _FIXED_TREE)

    assert resolve_root(root) == root.resolve()


def test_resolve_root_names_both_locations_it_looked_in(tmp_path: Path) -> None:
    """The message is the whole remedy — nothing else tells the caller the layout.

    Naming only the path given leaves someone who pointed at a checkout root one
    level away from the answer with no sign of it.
    """
    nowhere = tmp_path / "not-a-checkout"
    nowhere.mkdir()

    with pytest.raises(FileNotFoundError) as excinfo:
        resolve_root(nowhere)

    message = str(excinfo.value)
    assert str(nowhere) in message
    assert str(nowhere / "wfctl") in message
    for tree in TREES:
        assert tree in message


def test_resolve_root_raises_for_a_path_that_does_not_exist(tmp_path: Path) -> None:
    """A typo'd `--from` is the common way to reach this, not a broken install."""
    with pytest.raises(FileNotFoundError):
        resolve_root(tmp_path / "no-such-directory")


def test_resolve_root_returns_an_absolute_path(tmp_path: Path, monkeypatch) -> None:
    """FR-004: the recorded value has to mean the same thing from any directory.

    `doctor` runs from wherever the session happens to be, so a relative source
    resolved at install time and stored as given would resolve against the wrong
    frame every session after.
    """
    _build(tmp_path / "pkg", _FIXED_TREE)
    monkeypatch.chdir(tmp_path)

    resolved = resolve_root(Path("pkg"))

    assert resolved.is_absolute()
    assert resolved == (tmp_path / "pkg").resolve()
