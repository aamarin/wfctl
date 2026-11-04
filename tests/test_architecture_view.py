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
    match = re.search(rf"^```{name}\n(.*?)^```", VIEW.read_text(encoding="utf-8"), re.S | re.M)
    assert match, f"the view has no ```{name} block"
    return [line for line in match.group(1).splitlines() if line.strip()]


# Directories under `wfctl/` that ship as package data rather than code.
PACKAGE_DATA = ("agents", "specify", "contracts")


def _name(path: Path) -> str:
    """A module's name below `wfctl`, as the view writes it.

    `_paths.py` is `_paths`, `install/_bundle.py` is `install._bundle`, and
    `install/__init__.py` is `install`. The root `__init__.py` is `""`, since it
    is the package every name here sits under rather than a module of it.
    """
    parts = list(path.relative_to(PKG).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _sources() -> dict[str, Path]:
    """Every module under `wfctl/`, subpackages included, by `_name`."""
    found = {}
    for path in sorted(PKG.rglob("*.py")):
        rel = path.relative_to(PKG).parts
        if "__pycache__" in rel or rel[0] in PACKAGE_DATA:
            continue
        name = _name(path)
        if name:
            found[name] = path
    return found


def _modules() -> set[str]:
    return set(_sources())


def _longest(name: str, mods: set[str]) -> str | None:
    """The longest prefix of the dotted `name` that is a module, or None."""
    parts = name.split(".")
    for n in range(len(parts), 0, -1):
        candidate = ".".join(parts[:n])
        if candidate in mods:
            return candidate
    return None


def _graph() -> tuple[dict[str, set[str]], set[tuple[str, str, str]]]:
    """(module -> modules it imports, {(src, dst, private name)}).

    Walks the whole tree rather than module-level statements only: half of
    wfctl's internal edges are function-local imports, and a pass that missed
    them would report a graph with no cycle at all.
    """
    sources = _sources()
    mods = set(sources)
    edges: dict[str, set[str]] = {m: set() for m in mods}
    private: set[tuple[str, str, str]] = set()

    for src, path in sources.items():
        # The package a relative import starts from: the module's own name for
        # an `__init__.py`, and its parent's for any other file.
        package = src if path.name == "__init__.py" else src.rpartition(".")[0]
        tree = ast.parse(path.read_text(encoding="utf-8"))
        # Local name -> module it refers to, for the import forms that bind the
        # module itself. Collected first because the attribute sweep below runs
        # over the same tree and a lazy import inside a function still binds.
        bound: dict[str, str] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                # `from wfctl import _arch` names the module in `names`, and
                # `from wfctl._arch import x` names it in `module`. Both forms
                # are in use, and a package's `from ._bundle import x` is the
                # second one, relative to the package.
                if node.level:
                    anchor = package.split(".") if package else []
                    anchor = anchor[: len(anchor) - (node.level - 1)]
                    base = ".".join([*anchor, *([node.module] if node.module else [])])
                elif node.module == "wfctl":
                    base = ""
                elif (node.module or "").startswith("wfctl."):
                    base = node.module.removeprefix("wfctl.")
                else:
                    continue
                for a in node.names:
                    candidate = f"{base}.{a.name}" if base else a.name
                    if candidate in mods:
                        if candidate != src:
                            edges[src].add(candidate)
                        bound[a.asname or a.name] = candidate
                        continue
                    dst = _longest(base, mods) if base else None
                    if dst is None or dst == src:
                        continue
                    edges[src].add(dst)
                    if a.name.startswith("_"):
                        private.add((src, dst, a.name))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if not alias.name.startswith("wfctl."):
                        continue
                    dst = _longest(alias.name.removeprefix("wfctl."), mods)
                    if dst is not None and dst != src:
                        edges[src].add(dst)
                        if alias.asname:
                            bound[alias.asname] = dst

        # `from wfctl import _paths` then `_paths._STATE_DIR_OVERRIDE` is a
        # private crossing that no import statement records, and it is the form
        # `cli` uses for most of its imports — so a sweep that only read import
        # statements guaranteed less than the view claims it did.
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id in bound
                and node.attr.startswith("_")
            ):
                private.add((src, bound[node.value.id], node.attr))

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


def test_a_subpackage_module_is_named_by_its_package() -> None:
    """The view globbed one level until #720 moved install and drift into
    `wfctl/install/`. A flat glob drops a subpackage's modules from both sides
    of the comparison above, which then agrees while the drawing stops
    describing the code. So the names come from every file under `wfctl/`, and
    a package's own imports resolve against it.
    """
    mods = _modules()
    assert {"install", "install._bundle", "install._provenance"} <= mods
    assert not any(m.split(".")[0] in PACKAGE_DATA for m in mods)

    edges, _ = _graph()
    assert "install" in edges["cli"], "cli imports the package, not its modules"
    assert "install._bundle" in edges["install"], "a relative import inside the package"


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


def test_the_private_crossings_are_the_nine_the_view_draws() -> None:
    """Nine private names cross a module boundary, and the view names them.

    Ten until #679, when `report-block` stopped reaching `_STEP_NAMES` for the
    last step and named `implement` instead.

    Six until #339 added three: `_declared` reaches `_pipeline._STEP_NAMES` and
    `_pipeline._STEPS` for the reason the view's own crossings block gives —
    ordering a declared pass against wfctl's own means knowing their names —
    and `cli` reaches `_pipeline._outstanding_pass` to route `next` and
    `status` to the pass holding a step up, the same way it already reaches
    `_current_step_name` for the step doing the same job one level up.

    `_contexts` reaches `_arch._key_value` so the domain page's header lines
    and a record's frontmatter follow one rule for what counts as a key (#655).

    Both directions matter: a tenth crossing is drift the drawing missed, and
    a crossing that gets resolved leaves the drawing claiming a problem the
    code no longer has.
    """
    expected = set()
    for line in _block("crossings"):
        src, target = line.split(" -> ")
        dst, name = target.rsplit(".", 1)
        expected.add((src, dst, name))

    _, private = _graph()
    assert private == expected
