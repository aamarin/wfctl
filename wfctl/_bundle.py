"""The vendored wf-skills tree and its fingerprint.

Its own module for the reason `_manifest` documents for itself: `install-skills`
and `doctor` both read it, and `content_hash` is the one piece of real logic here
worth exercising without importing typer, rich and every command.

Callers must read `BUNDLE_ROOT` through this module at call time
(`_bundle.BUNDLE_ROOT`), never bind it as a default argument. Tests monkeypatch
it to point at a fake tree, and a default argument captures the real path at
import time — before any fixture can replace it.
"""
from __future__ import annotations

import hashlib
from importlib.resources import files
from pathlib import Path

# The two vendored trees, and the only thing `content_hash` walks. Everything
# else under the package root is source: hashing `cli.py` would make every code
# edit read as installed-content drift, and hashing `__pycache__` would make the
# value depend on whether anything had been imported yet.
#
# Adding a third tree means adding it here *and* grafting it in MANIFEST.in.
# Neither half works alone — one ships the files, the other notices when they
# change — and `test_trees_match_the_grafted_directories_in_manifest_in` fails if
# the two drift apart.
TREES = ("agents", "specify")

# Where those trees came from, pinned to the revision they were copied at. In the
# tracked source rather than only in `git log`, because the upstream repository is
# archived by this same feature: a commit message pointing at a repo that has
# stopped taking commits is a dead end for whoever next needs to know which
# revision this tree is a copy of, and a re-sync needs that base to diff against.
#
# The diff base, not a claim the tree is byte-identical to it. Fixes landing here
# rather than upstream is the expected steady state now that wf-skills is
# archived, so `git log -- wfctl/agents wfctl/specify` is what says how far the
# copy has moved from this revision.
BUNDLE_SOURCE = "aamarin/wf-skills@9ee468a6fe19f57e426b1a4711d8ae8c6c40d210"

# `files()` returns a real directory path because wfctl is always installed
# unpacked — `uv tool install` and `pip install` both explode the wheel, and
# nothing here supports running from a zipimport. That is what lets this skip
# `as_file()` and hand back a plain Path the rest of the code can join onto.
BUNDLE_ROOT = Path(str(files("wfctl")))


def content_hash(root: Path) -> str:
    """A single digest over every file in the bundled trees under `root`.

    Covers paths as well as bytes, so a pure rename registers. Iterates sorted,
    because `rglob` order is filesystem-dependent and an unsorted walk would make
    two identical trees disagree — permanent phantom drift rather than a real
    finding.

    Path and content are length-prefixed rather than separated by a delimiter.
    File contents can contain any byte, so a delimiter alone leaves a seam where
    one tree's bytes could impersonate another tree's boundary; a length prefix
    closes it for two lines.

    One value for the whole bundle, not one per layer. `agents/trackers/github.json`
    is copied inline and belongs to no target list, so a per-layer hash would
    never see it. The cost is over-reporting — an edit under `specify/templates/`
    marks every layer stale — and the remedy is `wfctl install-skills` either way.

    Raises `FileNotFoundError` when no tree resolves at all. A missing bundle would
    otherwise hash to `sha256(b"")` — a well-formed, stable fingerprint meaning
    "nothing here", which `doctor` would report as ordinary drift and prescribe an
    install that installs nothing. One tree present is enough: a partial bundle is
    a real state during a re-sync, and its digest is honest.
    """
    trees = [root / tree for tree in TREES]
    if not any(base.is_dir() for base in trees):
        raise FileNotFoundError(
            f"no bundled trees under {root} — expected one of {', '.join(TREES)}. "
            "The wfctl install is incomplete; reinstall the package."
        )

    digest = hashlib.sha256()
    for base in trees:
        if not base.is_dir():
            continue
        # rglob, not glob.glob: the stdlib glob module drops dot-prefixed names,
        # which would silently exclude `agents/configs/workmux/.workmux.yaml`.
        for path in sorted(p for p in base.rglob("*") if p.is_file()):
            rel = path.relative_to(root).as_posix().encode()
            data = path.read_bytes()
            digest.update(b"%d:" % len(rel))
            digest.update(rel)
            digest.update(b"%d:" % len(data))
            digest.update(data)
    return digest.hexdigest()


def resolve_root(path: Path) -> Path:
    """Turn a user-supplied path into a validated, absolute bundle root.

    Two spellings are accepted because both are things a person has in hand: the
    package directory that holds the trees, and the checkout that holds the
    package. `--from ../116-pr` names a worktree; the trees are at
    `../116-pr/wfctl`.

    The given path is tried before the nested probe, so the spelling that is
    already a bundle root keeps its meaning rather than being reinterpreted as a
    checkout around one.

    Absolute, because the caller records the result and `doctor` reads it back
    from wherever the next session happens to be standing (FR-004). Resolution
    has to happen here, where the user's working directory is still the frame the
    path was written against.

    Raises `FileNotFoundError` in `content_hash`'s shape, but naming both places
    it looked and not its advice to reinstall the package — a source the caller
    named is a typo or a wrong layout, not a broken wheel. Naming only the given
    path leaves someone who pointed at a checkout root one level from the answer
    with no sign of it.
    """
    given = Path(path).expanduser()
    probe = given / "wfctl"
    for candidate in (given, probe):
        if any((candidate / tree).is_dir() for tree in TREES):
            return candidate.resolve()
    raise FileNotFoundError(
        f"no bundled trees under {given} — expected one of {', '.join(TREES)} "
        f"(also looked in {probe})"
    )
