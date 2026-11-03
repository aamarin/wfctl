"""Check wfctl's imports against the Context Map on the domain page.

`docs/architecture/contexts-are-packages.md` says which context may import
which, and `docs/architecture/domain/wfctl.md` draws the map. This script reads
the map and the package names from that page, builds the import graph from the
source under `wfctl/`, and fails any import the map doesn't allow. Modules that
haven't moved into their context's package yet are placed by
`check_imports.baseline`, which also lists the imports that break the map today.

The script uses the standard library only, since CI runs it with the runner's
Python before `uv sync`, and it never imports wfctl.

It takes the tree to check from the current directory and never from its own
path. CI's `review` job runs the default branch's copy from inside the PR's
checkout, and a script that found the tree from its own path would check the
trusted tree and pass every PR.
"""
from __future__ import annotations

import ast
import os
import re
import sys
from collections.abc import Collection, Iterator
from dataclasses import dataclass, field
from pathlib import Path

# The layer above the contexts that routes a command to them. A wiring file may
# import any context's package, so the list is closed, and adding a name changes
# this script, which waits for a person's approval.
WIRING = ("cli.py", "_entry.py")

# Directories under `wfctl/` that ship as package data and hold no module the
# check places.
PACKAGE_DATA = ("agents", "specify", "contracts")

# The files CI runs the check with. A branch that changes one of them adds
# something a person has to approve, since CI takes both from the default
# branch and a weakened copy there would pass every later branch.
TRUSTED = (".github/scripts/check_imports.py", ".github/workflows/review.yml")

# The note line a person's approval writes under `refs/notes/wfctl-review`. The
# script can't import wfctl, so a test pins this against
# `wfctl._review_notes.IMPORTS_APPROVED_PREFIX`.
IMPORTS_APPROVED_PREFIX = "imports approved "

PAGE = "docs/architecture/domain/wfctl.md"
BASELINE = ".github/scripts/check_imports.baseline"
SOURCE = "wfctl"

_WIDTH = 78


class UnsafePath(Exception):
    """A path the script refuses to read, because it is a symlink or resolves
    outside the tree. The message names the path and never its target."""


class DomainError(Exception):
    """The domain page can't be read as a map. `line` is 0 when the problem is
    a missing section rather than one line."""

    def __init__(self, message: str, line: int = 0, text: str = "") -> None:
        super().__init__(message)
        self.line = line
        self.text = text


class BaselineError(Exception):
    def __init__(self, message: str, line: int) -> None:
        super().__init__(message)
        self.line = line


# --- reading a file the tree holds -----------------------------------------------


def safe_read(root: Path, path: Path) -> str:
    """The text of a regular file inside `root`.

    Every component from `root` down is checked, so a symlinked directory is
    refused as well as a symlinked file. In the `review` job a PR could link
    the baseline to `pr/.git/config`, and a failure that quoted the bad line
    would print that file to a public log.
    """
    rel = path.relative_to(root) if path.is_absolute() else path
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise UnsafePath(f"{rel} is a symlink; the check reads only regular files")
    full = root / rel
    if not full.resolve().is_relative_to(root.resolve()):
        raise UnsafePath(f"{rel} resolves outside the repository")
    return full.read_text(encoding="utf-8")


# --- the domain page ---------------------------------------------------------------


@dataclass(frozen=True)
class Domain:
    """What the check reads from the page. `contexts` maps a context's name to
    its package, `arrows` holds (upstream, downstream) pairs of context names,
    and `shared` names the packages that belong to no context."""

    contexts: dict[str, str]
    shared: frozenset[str]
    arrows: frozenset[tuple[str, str]]

    def packages(self) -> frozenset[str]:
        return frozenset(p for p in self.contexts.values() if p) | self.shared

    def context_of(self, package: str) -> str | None:
        return next((c for c, p in self.contexts.items() if p == package), None)


_HEADER = re.compile(r"flowchart\s+\w+")
_NODE = re.compile(r'(?P<id>\w+)\["(?P<label>[^"]+)"\]')
_EDGE = re.compile(r'(?P<up>\w+)\s+-->\s*(?:\|"[^"]*"\|\s*)?(?P<down>\w+)')
_OUTSIDE = "(outside)"


def _section(lines: list[str], heading: str) -> int | None:
    """The index of the line after `heading`, or None when the page has none."""
    for i, line in enumerate(lines):
        if line.strip() == heading:
            return i + 1
    return None


def _table(lines: list[str], start: int) -> list[tuple[int, list[str]]]:
    """The rows of the first markdown table at or after `start`, header first,
    each with its 1-based line number. The separator row is dropped."""
    i = start
    while i < len(lines) and not lines[i].lstrip().startswith("|"):
        if lines[i].startswith("#"):
            return []
        i += 1
    rows: list[tuple[int, list[str]]] = []
    while i < len(lines) and lines[i].lstrip().startswith("|"):
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        if not all(re.fullmatch(r":?-+:?", c) for c in cells):
            rows.append((i + 1, cells))
        i += 1
    return rows


def _cell(text: str) -> str:
    return text.strip().strip("`").strip()


def read_domain(page: Path, *, merge_base: bool = False, text: str | None = None) -> Domain:
    """Read the contexts table, the Shared packages table, and the Context Map.

    Every line inside the map's mermaid block must be the `flowchart` header, a
    node, or an edge, and a blank line is skipped. Anything else fails with its
    line number, because a skipped arrow refuses imports with no visible cause.

    With `merge_base`, the page is the one at the branch's merge base, read for
    the approval check. Its contexts table may lack the Package column and the
    Shared packages table may be missing. Each allowance can only add to the
    additions the approval check lists, so none of them can hide one.
    """
    lines = (page.read_text(encoding="utf-8") if text is None else text).splitlines()

    start = _section(lines, "## Bounded Contexts")
    rows = _table(lines, start) if start is not None else []
    if not rows:
        raise DomainError("has no Bounded Contexts table under `## Bounded Contexts`")
    header = [c.lower() for c in rows[0][1]]
    if "context" not in header:
        raise DomainError("the Bounded Contexts table has no Context column", rows[0][0])
    name_at = header.index("context")
    package_at = header.index("package") if "package" in header else None
    if package_at is None and not merge_base:
        raise DomainError("the Bounded Contexts table has no Package column", rows[0][0])
    contexts: dict[str, str] = {}
    seen: dict[str, int] = {}
    for number, cells in rows[1:]:
        name = _cell(cells[name_at])
        package = _cell(cells[package_at]) if package_at is not None else ""
        contexts[name] = package
        if package:
            if package in seen:
                raise DomainError(f"package `{package}` is named twice", number)
            seen[package] = number

    start = _section(lines, "### Shared packages")
    shared_rows = _table(lines, start) if start is not None else []
    if not shared_rows:
        if not merge_base:
            raise DomainError("has no Shared packages table under `### Shared packages`")
        shared: frozenset[str] = frozenset()
    else:
        header = [c.lower() for c in shared_rows[0][1]]
        if "package" not in header:
            raise DomainError("the Shared packages table has no Package column",
                              shared_rows[0][0])
        at = header.index("package")
        names: set[str] = set()
        for number, cells in shared_rows[1:]:
            package = _cell(cells[at])
            if package in seen:
                raise DomainError(f"package `{package}` is named twice", number)
            seen[package] = number
            names.add(package)
        shared = frozenset(names)

    return Domain(contexts, shared, _read_map(lines, set(contexts)))


def _read_map(lines: list[str], names: set[str]) -> frozenset[tuple[str, str]]:
    start = _section(lines, "### Context Map")
    if start is None:
        raise DomainError("has no `### Context Map` section")
    i = start
    while i < len(lines) and lines[i].strip() != "```mermaid":
        if lines[i].startswith("#"):
            i = len(lines)
            break
        i += 1
    if i >= len(lines):
        raise DomainError("has no mermaid block under `### Context Map`")
    nodes: dict[str, str | None] = {}
    edges: list[tuple[int, str, str]] = []
    i += 1
    while True:
        if i >= len(lines):
            raise DomainError("the Context Map block is never closed")
        line = lines[i].strip()
        number = i + 1
        i += 1
        if line == "```":
            break
        if not line or _HEADER.fullmatch(line):
            continue
        node = _NODE.fullmatch(line)
        if node:
            label = node["label"]
            if label.endswith(_OUTSIDE):
                nodes[node["id"]] = None
            elif label in names:
                nodes[node["id"]] = label
            else:
                raise DomainError(
                    f'the Context Map names "{label}", which no row of the Bounded '
                    "Contexts table names. Mark a party outside wfctl with "
                    f"`{_OUTSIDE}` at the end of its label.",
                    number, line,
                )
            continue
        edge = _EDGE.fullmatch(line)
        if edge:
            edges.append((number, edge["up"], edge["down"]))
            continue
        raise DomainError("the Context Map block has a line the check can't read", number, line)
    arrows: set[tuple[str, str]] = set()
    for number, up, down in edges:
        for node_id in (up, down):
            if node_id not in nodes:
                raise DomainError(
                    f"the Context Map draws an arrow from or to `{node_id}`, which it "
                    "never declares as a node",
                    number, lines[number - 1].strip(),
                )
        up_name, down_name = nodes[up], nodes[down]
        if up_name is not None and down_name is not None:
            arrows.add((up_name, down_name))
    return frozenset(arrows)


# --- the baseline -----------------------------------------------------------------


@dataclass(frozen=True)
class Placement:
    module: str
    package: str
    line: int


@dataclass(frozen=True)
class Violation:
    src: str
    dst: str
    line: int


@dataclass(frozen=True)
class Baseline:
    placements: tuple[Placement, ...] = ()
    violations: tuple[Violation, ...] = ()

    def entries(self) -> int:
        return len(self.placements) + len(self.violations)

    def lines(self) -> list[str]:
        return [f"{p.module} {p.package}" for p in self.placements] + [
            f"{v.src} -> {v.dst}" for v in self.violations
        ]


_FLAT = r"[A-Za-z_]\w*\.py"
_MODULE_PATH = r"[A-Za-z_]\w*(?:/[A-Za-z_]\w*)*\.py"
_PLACEMENT = re.compile(rf"(?P<module>{_FLAT}) (?P<package>[a-z_]\w*)")
_VIOLATION = re.compile(rf"(?P<src>{_MODULE_PATH}) -> (?P<dst>{_MODULE_PATH})")


def parse_baseline(text: str, packages: Collection[str] | None = None) -> Baseline:
    placements: list[Placement] = []
    violations: list[Violation] = []
    placed: dict[str, int] = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        violation = _VIOLATION.fullmatch(line)
        if violation:
            violations.append(Violation(violation["src"], violation["dst"], number))
            continue
        placement = _PLACEMENT.fullmatch(line)
        if not placement:
            raise BaselineError(
                "is neither `<file> <package>` nor `<file> -> <file>`", number,
            )
        module, package = placement["module"], placement["package"]
        if packages is not None and package not in packages:
            raise BaselineError(
                f"places {module} in `{package}`, which the domain page names as no "
                "context's package and no shared package",
                number,
            )
        if module in placed:
            raise BaselineError(
                f"places {module} a second time; line {placed[module]} already places it",
                number,
            )
        placed[module] = number
        placements.append(Placement(module, package, number))
    return Baseline(tuple(placements), tuple(violations))


def read_baseline(path: Path, packages: Collection[str] | None = None) -> Baseline:
    """Read the baseline. A missing file reads as empty, since every flat
    module then fails as unplaced, which says what to add."""
    if not path.exists() and not path.is_symlink():
        return Baseline()
    return parse_baseline(path.read_text(encoding="utf-8"), packages)


# --- which context each module belongs to ------------------------------------------


@dataclass(frozen=True)
class Owner:
    """`kind` is `context`, `shared`, or `wiring`. `moved` says the module sits
    inside its package's directory rather than being placed by a baseline line."""

    kind: str
    package: str = ""
    context: str = ""
    moved: bool = False


WIRED = Owner("wiring")


@dataclass(frozen=True)
class Failure:
    """One problem the check found. `src` is a path under the root, `dst` a
    dotted module name, and `contexts` the names `render` draws."""

    kind: str
    src: str = ""
    dst: str = ""
    line: int = 0
    contexts: tuple[str, ...] = ()
    detail: str = ""
    extra: tuple[str, ...] = field(default=())


def _dotted(rel: Path) -> str:
    """`wfctl/evidence/_status.py` -> `wfctl.evidence._status`."""
    parts = list(rel.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def python_files(root: Path) -> Iterator[Path]:
    """Every `.py` file under `root/wfctl`, as a path relative to `root`.

    Symlinked directories aren't followed, and a symlinked file or directory
    raises, naming the path.
    """
    source = root / SOURCE
    if source.is_symlink():
        raise UnsafePath(f"{SOURCE} is a symlink; the check reads only regular files")
    for dirpath, dirnames, filenames in os.walk(source, followlinks=False):
        here = Path(dirpath)
        for name in sorted(dirnames):
            if (here / name).is_symlink():
                raise UnsafePath(
                    f"{(here / name).relative_to(root)} is a symlink; the check reads "
                    "only regular files"
                )
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for name in sorted(filenames):
            if name.endswith(".py"):
                path = here / name
                if path.is_symlink():
                    raise UnsafePath(
                        f"{path.relative_to(root)} is a symlink; the check reads only "
                        "regular files"
                    )
                yield path.relative_to(root)


def _imports_wfctl(root: Path, rel: Path) -> bool:
    tree = ast.parse(safe_read(root, rel))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level or (node.module or "").split(".")[0] == SOURCE:
                return True
        elif isinstance(node, ast.Import):
            if any(a.name.split(".")[0] == SOURCE for a in node.names):
                return True
    return False


def module_contexts(
    root: Path, domain: Domain, baseline: Baseline,
) -> tuple[dict[str, Owner], list[Failure]]:
    """Map every module under `wfctl/` to its owner, and fail each one with no
    owner (FR-007, FR-008)."""
    placements = {p.module: p.package for p in baseline.placements}
    owners: dict[str, Owner] = {}
    failures: list[Failure] = []

    def owner_of(package: str, moved: bool) -> Owner:
        if package in domain.shared:
            return Owner("shared", package, "", moved)
        return Owner("context", package, domain.context_of(package) or "", moved)

    for rel in python_files(root):
        inside = rel.parts[1:]
        dotted = _dotted(rel)
        if len(inside) > 1:
            top = inside[0]
            if top in PACKAGE_DATA:
                continue
            if top in domain.packages():
                owners[dotted] = owner_of(top, True)
                continue
            failures.append(Failure("unplaced-module", rel.as_posix()))
            continue
        name = inside[0]
        if name in WIRING:
            owners[dotted] = WIRED
        elif name in placements:
            owners[dotted] = owner_of(placements[name], False)
        elif name == "__init__.py" and not _imports_wfctl(root, rel):
            continue
        else:
            failures.append(Failure("unplaced-module", rel.as_posix()))
    return owners, failures


# --- the import graph ---------------------------------------------------------------


@dataclass(frozen=True)
class Import:
    src: str
    dst: str
    line: int


def _modules(source: Path) -> dict[str, Path]:
    root = source.parent
    return {_dotted(rel): rel for rel in python_files(root)}


def _longest_module(name: str, modules: Collection[str]) -> str | None:
    parts = name.split(".")
    for n in range(len(parts), 0, -1):
        candidate = ".".join(parts[:n])
        if candidate in modules:
            return candidate
    return None


def _attribute_chain(node: ast.Attribute) -> list[str] | None:
    names: list[str] = []
    current: ast.expr = node
    while isinstance(current, ast.Attribute):
        names.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    names.append(current.id)
    return list(reversed(names))


def import_graph(source: Path) -> list[Import]:
    """One `Import` per import of a wfctl module, in every form the code uses.

    The walk covers the whole tree, since half of wfctl's internal imports are
    function-local. In `from P import N`, the import targets `P.N` when that is
    a module, so `from wfctl.evidence import _status` is an import of the
    private module and not of the package. A module bound by an import and then
    read as an attribute, such as `evidence._status.derive()`, is an import of
    the module the attribute reaches.
    """
    root = source.parent
    modules = _modules(source)
    found: list[Import] = []
    for src, rel in sorted(modules.items()):
        is_package = rel.name == "__init__.py"
        package = src if is_package else src.rpartition(".")[0]
        tree = ast.parse(safe_read(root, rel))
        bound: dict[str, str] = {}

        def add(dst: str | None, line: int) -> None:
            if dst is not None and dst != src:
                found.append(Import(src, dst, line))

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    anchor = package.split(".")
                    anchor = anchor[: len(anchor) - (node.level - 1)]
                    base = ".".join([*anchor, *([node.module] if node.module else [])])
                else:
                    base = node.module or ""
                if base.split(".")[0] != SOURCE:
                    continue
                for alias in node.names:
                    candidate = f"{base}.{alias.name}"
                    if candidate in modules:
                        add(candidate, node.lineno)
                        bound[alias.asname or alias.name] = candidate
                    else:
                        add(_longest_module(base, modules), node.lineno)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] != SOURCE:
                        continue
                    add(_longest_module(alias.name, modules), node.lineno)
                    if alias.asname:
                        target = _longest_module(alias.name, modules)
                        if target is not None:
                            bound[alias.asname] = target
                    elif SOURCE in modules:
                        bound[SOURCE] = SOURCE

        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute):
                continue
            chain = _attribute_chain(node)
            if chain is None or chain[0] not in bound:
                continue
            reached = _longest_module(".".join([bound[chain[0]], *chain[1:]]), modules)
            if reached is not None and reached != bound[chain[0]]:
                add(reached, node.lineno)
    return sorted(set(found), key=lambda i: (i.src, i.line, i.dst))


# --- output ------------------------------------------------------------------------


def _fill(text: str, first: str = "  ", rest: str = "  ") -> str:
    import textwrap

    return textwrap.fill(
        text, width=_WIDTH, initial_indent=first, subsequent_indent=rest,
        break_long_words=False, break_on_hyphens=False,
    )


def render(failure: Failure) -> str:
    kind = failure.kind
    if kind == "unplaced-module":
        return _fill(
            f"{failure.src} has no package and no placement line in {BASELINE}. Put it in "
            "its context's package, or ask the user to approve a placement line for it.",
            "✗ ",
        )
    if kind == "unsafe-path":
        return f"✗ {failure.detail}"
    if kind == "unreadable-baseline":
        return _fill(f"{BASELINE}:{failure.line}: {failure.detail}", "✗ ")
    if kind == "unreadable-domain":
        where = f"{PAGE}:{failure.line}" if failure.line else PAGE
        if failure.extra:
            return "\n".join([
                _fill(f"{where}: {failure.detail}:", "✗ "),
                "",
                f"    {failure.extra[0]}",
                "",
                _fill(
                    'Use `A --> B` or `A -->|"label"| B`. The check doesn\'t skip a line it '
                    "can't read, because a skipped arrow refuses imports with no visible cause."
                ),
            ])
        return _fill(f"{where}: {failure.detail}.", "✗ ")
    raise ValueError(f"no output for a {kind} failure")


# --- running it --------------------------------------------------------------------


def rule_check(root: Path) -> tuple[list[Failure], int, int]:
    """Every failure the rule check finds in the tree at `root`, the number of
    modules it placed, and the number of baseline entries."""
    try:
        domain = read_domain(root / PAGE, text=safe_read(root, Path(PAGE)))
    except UnsafePath as e:
        return [Failure("unsafe-path", detail=str(e))], 0, 0
    except DomainError as e:
        detail = str(e)
        if e.text and "can't read" in detail:
            return [Failure("unreadable-domain", line=e.line, detail=detail,
                            extra=(e.text,))], 0, 0
        return [Failure("unreadable-domain", line=e.line, detail=detail)], 0, 0
    try:
        base = root / BASELINE
        if base.exists() or base.is_symlink():
            baseline = parse_baseline(safe_read(root, Path(BASELINE)), domain.packages())
        else:
            baseline = Baseline()
    except UnsafePath as e:
        return [Failure("unsafe-path", detail=str(e))], 0, 0
    except BaselineError as e:
        return [Failure("unreadable-baseline", line=e.line, detail=str(e))], 0, 0
    try:
        owners, failures = module_contexts(root, domain, baseline)
    except UnsafePath as e:
        return [Failure("unsafe-path", detail=str(e))], 0, 0
    return failures, len(owners), baseline.entries()


def main(argv: list[str] | None = None) -> int:
    root = Path.cwd()
    failures, modules, entries = rule_check(root)
    if not failures:
        print(f"✓ imports follow the Context Map ({modules} modules, {entries} baseline lines)")
        return 0
    print("\n\n".join(render(f) for f in failures))
    n = len(failures)
    print(f"\n{n} problem{'s' if n != 1 else ''} found")
    return 1


if __name__ == "__main__":
    sys.exit(main())
