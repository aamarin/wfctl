"""The current-state view is checked against the code, not trusted.

`docs/architecture/views/current-state.md` draws wfctl's modules in four bands.
A drawing nobody can falsify is a claim, so the three fenced blocks at the foot
of that file are parsed here and compared against an import graph derived from
the source. Every failure below means the drawing and the code disagree; which
one is wrong is for the reader to decide.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PKG = REPO_ROOT / "wfctl"
VIEW = REPO_ROOT / "docs" / "architecture" / "views" / "current-state.md"


def _block(name: str) -> list[str]:
    """The non-empty lines of the ```<name> fence in the view."""
    match = re.search(rf"^```{name}\n(.*?)^```", VIEW.read_text(), re.S | re.M)
    assert match, f"the view has no ```{name} block"
    return [line for line in match.group(1).splitlines() if line.strip()]


def _modules() -> set[str]:
    return {p.stem for p in PKG.glob("*.py") if p.stem != "__init__"}


def _graph() -> tuple[dict[str, set[str]], set[tuple[str, str, str]]]:
    """(module -> modules it imports, {(src, dst, private name)}).

    Walks the whole tree rather than module-level statements only: half of
    wfctl's internal edges are function-local imports, and a pass that missed
    them would report a graph with no cycle at all.
    """
    mods = _modules()
    edges: dict[str, set[str]] = {m: set() for m in mods}
    private: set[tuple[str, str, str]] = set()

    for path in sorted(PKG.glob("*.py")):
        src = path.stem
        if src == "__init__":
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom):
                # `from . import _arch` / `from wfctl import _arch` name the
                # module in `names`; `from wfctl._arch import x` names it in
                # `module`. Both forms are in use.
                if (node.level and not node.module) or node.module == "wfctl":
                    edges[src] |= {a.name for a in node.names if a.name in mods}
                    continue
                dst = (node.module or "").rsplit(".", 1)[-1]
                if dst in mods:
                    edges[src].add(dst)
                    private |= {
                        (src, dst, a.name)
                        for a in node.names
                        if a.name.startswith("_")
                    }
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    tail = alias.name.rsplit(".", 1)[-1]
                    if alias.name.startswith("wfctl") and tail in mods:
                        edges[src].add(tail)
    return edges, private


@pytest.fixture(scope="module")
def bands() -> dict[str, str]:
    """module -> band name, from the view's ```layers block."""
    out = {}
    for line in _block("layers"):
        band, *members = line.split()
        for member in members:
            out[member] = band
    return out


def test_every_module_has_a_band(bands: dict[str, str]) -> None:
    """A module the view does not place is a module the drawing does not show.

    This is the failure a new module causes — `_settings` was added after the
    graph in #149's first comment was taken, and nothing said so.
    """
    assert _modules() == set(bands), "modules and the view's ```layers disagree"


def test_only_the_declared_edge_runs_upward(bands: dict[str, str]) -> None:
    """Edges run downward or sideways; the view draws every exception.

    The band order is the drawing's whole claim. An undrawn upward edge means
    the layering the view recovered no longer holds.
    """
    order = [line.split()[0] for line in _block("layers")]
    declared = {tuple(line.split(" -> ")) for line in _block("upward")}
    edges, _ = _graph()

    # An unplaced module is the test above's failure, not this one's. Indexing
    # it here would raise KeyError and report a missing band as a broken layer.
    upward = {
        (src, dst)
        for src, dsts in edges.items()
        for dst in dsts
        if src in bands and dst in bands
        if order.index(bands[dst]) < order.index(bands[src])
    }
    assert upward == declared


def test_the_private_crossings_are_the_four_the_view_draws() -> None:
    """Four private names cross a module boundary, and the view names them.

    Both directions matter: a fifth crossing is drift the drawing missed, and a
    crossing that gets resolved leaves the drawing claiming a problem the code
    no longer has.
    """
    expected = set()
    for line in _block("crossings"):
        src, target = line.split(" -> ")
        dst, name = target.split(".", 1)
        expected.add((src, dst, name))

    _, private = _graph()
    assert private == expected
