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
# Adding a third tree means adding it here *and* to `[tool.setuptools.package-data]`
# in pyproject.toml. Neither half works alone — one ships the files, the other
# notices when they change.
TREES = ("agents", "specify")

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
    """
    digest = hashlib.sha256()
    for tree in TREES:
        base = root / tree
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
