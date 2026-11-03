"""The import check: an import the Context Map doesn't allow fails the change.

The check is a standalone script under `.github/scripts/`, so it is loaded by
path, the way `test_release_note_check.py` loads its script. Most tests build a
fake `wfctl/` tree and a domain page under `tmp_path`, with real subpackages, so
the rules for moved packages are tested before any context moves. A few read
this repository's own page and tree, since a check that passes on fixtures and
fails on the real page is no check at all.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / ".github" / "scripts" / "check_imports.py"
REAL_PAGE = ROOT / "docs" / "architecture" / "domain" / "wfctl.md"
REAL_BASELINE = ROOT / ".github" / "scripts" / "check_imports.baseline"


def load_check() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_imports", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclasses look the module up by name while the class body runs.
    sys.modules["check_imports"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def check() -> ModuleType:
    return load_check()


# The fixture page has the real page's shape: a Bounded Contexts table with a
# backticked Package column, a Shared packages table, and a mermaid block whose
# lines are indented and split by a blank line. Four contexts, one outside
# party, and three arrows between two contexts.
PAGE = """\
# Fixture domain model

## Bounded Contexts

| Context | Package | Purpose |
| --- | --- | --- |
| Evidence and derivation | `evidence` | Derive status. |
| Session continuity | `session` | Carry work across sessions. |
| Architecture records | `arch` | Keep decisions. |
| Worktree guard | `guard` | Keep agents in their worktree. |

### Shared packages

| Package | Pattern | Holds |
| --- | --- | --- |
| `core` | Shared Kernel | Lookups |
| `tracker` | Anticorruption Layer | Tracker verbs |

### Context Map

```mermaid
flowchart LR
    SK["Spec Kit (outside)"]
    EV["Evidence and derivation"]
    SC["Session continuity"]
    AR["Architecture records"]
    WG["Worktree guard"]

    SK -->|"steps and templates"| EV
    EV -->|"status payload"| SC
    AR -->|"obligations"| EV
    EV --> WG
```
"""


def make_tree(
    root: Path,
    files: dict[str, str],
    baseline: str = "",
    page: str = PAGE,
) -> Path:
    """Write a fake repository: `wfctl/` modules, the domain page, and the
    baseline. `files` maps a path under `wfctl/` to its source."""
    for rel, source in files.items():
        path = root / "wfctl" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(source))
    (root / "wfctl").mkdir(parents=True, exist_ok=True)
    page_path = root / "docs" / "architecture" / "domain" / "wfctl.md"
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_text(page)
    base = root / ".github" / "scripts" / "check_imports.baseline"
    base.parent.mkdir(parents=True, exist_ok=True)
    base.write_text(textwrap.dedent(baseline))
    return root


def page_at(root: Path) -> Path:
    return root / "docs" / "architecture" / "domain" / "wfctl.md"


def baseline_at(root: Path) -> Path:
    return root / ".github" / "scripts" / "check_imports.baseline"


def run_main(check: ModuleType, root: Path, monkeypatch: pytest.MonkeyPatch,
             capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str]:
    monkeypatch.chdir(root)
    code = check.main(list(args))
    return code, capsys.readouterr().out


def test_the_script_loads_and_exits_zero_with_nothing_to_report(check: ModuleType) -> None:
    """The loader every test here uses has to find the script and its constants."""
    assert check.WIRING == ("cli.py", "_entry.py")
    assert check.PACKAGE_DATA == ("agents", "specify", "contracts")
    assert check.TRUSTED == (".github/scripts/check_imports.py", ".github/workflows/review.yml")


# --- reading the domain page (T005) --------------------------------------------


def test_the_domain_reader_returns_contexts_shared_packages_and_arrows(
    check: ModuleType, tmp_path: Path,
) -> None:
    """The map is the page's, so every name the rules use comes from it.

    Backticks around a Package cell are stripped, since the real table writes
    `` `evidence` ``, and arrows are pairs of context names so a package rename
    doesn't change them.
    """
    root = make_tree(tmp_path, {})
    domain = check.read_domain(page_at(root))

    assert domain.contexts == {
        "Evidence and derivation": "evidence",
        "Session continuity": "session",
        "Architecture records": "arch",
        "Worktree guard": "guard",
    }
    assert domain.shared == frozenset({"core", "tracker"})
    assert domain.arrows == frozenset({
        ("Evidence and derivation", "Session continuity"),
        ("Architecture records", "Evidence and derivation"),
        ("Evidence and derivation", "Worktree guard"),
    })


def test_a_package_named_twice_across_the_two_tables_fails(
    check: ModuleType, tmp_path: Path,
) -> None:
    """Two owners for one package would make every module in it ambiguous."""
    page = PAGE.replace("| `tracker` |", "| `session` |")
    root = make_tree(tmp_path, {}, page=page)

    with pytest.raises(check.DomainError, match="session"):
        check.read_domain(page_at(root))


# --- reading the baseline (T006) -----------------------------------------------


def test_the_baseline_reader_skips_comments_and_reads_both_kinds_of_line(
    check: ModuleType, tmp_path: Path,
) -> None:
    root = make_tree(tmp_path, {}, baseline="""\
        # placements

        _session.py session
        _paths.py core
        _pipeline.py -> _session.py
    """)
    baseline = check.read_baseline(baseline_at(root))

    assert [(p.module, p.package, p.line) for p in baseline.placements] == [
        ("_session.py", "session", 3),
        ("_paths.py", "core", 4),
    ]
    assert [(v.src, v.dst, v.line) for v in baseline.violations] == [
        ("_pipeline.py", "_session.py", 5),
    ]


@pytest.mark.parametrize("line", [
    "_session.py",
    "_session.py session extra",
    "_pipeline.py => _session.py",
    "_pipeline.py -> ",
    "session/_x.py session",
])
def test_a_malformed_baseline_line_fails_with_its_line_number(
    check: ModuleType, tmp_path: Path, line: str,
) -> None:
    """A line the reader skipped would place nothing and excuse nothing, and
    the failure it caused would point somewhere else."""
    root = make_tree(tmp_path, {}, baseline=f"# header\n{line}\n")

    with pytest.raises(check.BaselineError) as caught:
        check.read_baseline(baseline_at(root))
    assert caught.value.line == 2


def test_a_placement_naming_an_unknown_package_fails(check: ModuleType, tmp_path: Path) -> None:
    root = make_tree(tmp_path, {}, baseline="_x.py nowhere\n")
    domain = check.read_domain(page_at(root))

    with pytest.raises(check.BaselineError, match="nowhere") as caught:
        check.read_baseline(baseline_at(root), domain.packages())
    assert caught.value.line == 1


def test_a_module_placed_twice_fails(check: ModuleType, tmp_path: Path) -> None:
    root = make_tree(tmp_path, {}, baseline="_x.py core\n_x.py session\n")

    with pytest.raises(check.BaselineError, match="_x.py") as caught:
        check.read_baseline(baseline_at(root))
    assert caught.value.line == 2


# --- placing modules (T007) ----------------------------------------------------


def place(check: ModuleType, root: Path) -> tuple[dict[str, object], list[object]]:
    domain = check.read_domain(page_at(root))
    baseline = check.read_baseline(baseline_at(root), domain.packages())
    return check.module_contexts(root, domain, baseline)


def test_a_file_under_a_listed_package_takes_that_packages_context(
    check: ModuleType, tmp_path: Path,
) -> None:
    root = make_tree(tmp_path, {
        "evidence/__init__.py": "",
        "evidence/_status.py": "",
        "core/__init__.py": "",
    })
    owners, failures = place(check, root)

    assert failures == []
    assert owners["wfctl.evidence"].package == "evidence"
    assert owners["wfctl.evidence"].moved
    assert owners["wfctl.evidence._status"].context == "Evidence and derivation"
    assert owners["wfctl.core"].kind == "shared"


def test_a_placed_flat_file_takes_its_placement(check: ModuleType, tmp_path: Path) -> None:
    root = make_tree(tmp_path, {"_session.py": ""}, baseline="_session.py session\n")
    owners, failures = place(check, root)

    assert failures == []
    assert owners["wfctl._session"].context == "Session continuity"
    assert not owners["wfctl._session"].moved


def test_cli_and_entry_are_wiring(check: ModuleType, tmp_path: Path) -> None:
    """FR-006. Wiring routes a command to the contexts and belongs to none."""
    root = make_tree(tmp_path, {"cli.py": "", "_entry.py": ""})
    owners, failures = place(check, root)

    assert failures == []
    assert owners["wfctl.cli"].kind == "wiring"
    assert owners["wfctl._entry"].kind == "wiring"


def test_the_top_init_is_skipped_until_it_imports_a_wfctl_module(
    check: ModuleType, tmp_path: Path,
) -> None:
    """It imports nothing today. Once it does, a person decides where it goes."""
    quiet = make_tree(tmp_path / "quiet", {"__init__.py": '"""wfctl."""\n'})
    owners, failures = place(check, quiet)
    assert failures == [] and "wfctl" not in owners

    loud = make_tree(tmp_path / "loud", {"__init__.py": "from wfctl import _paths\n",
                                          "_paths.py": ""},
                     baseline="_paths.py core\n")
    _, failures = place(check, loud)
    assert [(f.kind, f.src) for f in failures] == [("unplaced-module", "wfctl/__init__.py")]


def test_package_data_is_skipped(check: ModuleType, tmp_path: Path) -> None:
    root = make_tree(tmp_path, {"agents/hooks/x.py": "", "specify/y.py": "", "contracts/z.py": ""})
    owners, failures = place(check, root)

    assert failures == [] and owners == {}


def test_an_unplaced_flat_file_fails(check: ModuleType, tmp_path: Path) -> None:
    """FR-008. A new flat module with no line would otherwise sit outside every rule."""
    root = make_tree(tmp_path, {"_new.py": ""})
    _, failures = place(check, root)

    assert [(f.kind, f.src) for f in failures] == [("unplaced-module", "wfctl/_new.py")]


def test_a_file_under_an_unlisted_directory_fails_as_unplaced(
    check: ModuleType, tmp_path: Path,
) -> None:
    """A renamed package or a new `wfctl/util/` can't carry modules past the check."""
    root = make_tree(tmp_path, {"util/__init__.py": "", "util/_x.py": ""})
    _, failures = place(check, root)

    assert sorted((f.kind, f.src) for f in failures) == [
        ("unplaced-module", "wfctl/util/__init__.py"),
        ("unplaced-module", "wfctl/util/_x.py"),
    ]


# --- the import graph (T008) ---------------------------------------------------


def graph(check: ModuleType, root: Path) -> set[tuple[str, str]]:
    return {(i.src, i.dst) for i in check.import_graph(root / "wfctl")}


def test_every_import_form_in_use_reaches_the_graph(check: ModuleType, tmp_path: Path) -> None:
    """Half of wfctl's internal edges are function-local, and `cli` binds most
    modules with `from wfctl import _x`, so a walk that read only module-level
    statements would miss most of the graph."""
    root = make_tree(tmp_path, {
        "_a.py": """\
            from wfctl import _b
            from . import _c
            from ._d import thing
            import wfctl._e
            import wfctl._f as f

            def later():
                from wfctl._g import other
        """,
        "_b.py": "", "_c.py": "", "_d.py": "", "_e.py": "", "_f.py": "", "_g.py": "",
    })

    assert graph(check, root) == {
        ("wfctl._a", f"wfctl._{x}") for x in "bcdefg"
    }


def test_a_module_bound_by_an_import_and_read_as_an_attribute_is_an_import(
    check: ModuleType, tmp_path: Path,
) -> None:
    root = make_tree(tmp_path, {
        "_a.py": """\
            from wfctl import evidence
            evidence._status.derive()
        """,
        "evidence/__init__.py": "",
        "evidence/_status.py": "",
    })

    assert graph(check, root) == {
        ("wfctl._a", "wfctl.evidence"),
        ("wfctl._a", "wfctl.evidence._status"),
    }


def test_from_a_package_import_a_private_module_targets_the_module(
    check: ModuleType, tmp_path: Path,
) -> None:
    """Spec Edge Cases. Read as an import of `wfctl.evidence`, this would pass
    the internal-module rule while reaching straight past the package."""
    root = make_tree(tmp_path, {
        "session/__init__.py": "",
        "session/_handoff.py": "from wfctl.evidence import _status\n",
        "evidence/__init__.py": "",
        "evidence/_status.py": "",
    })

    assert graph(check, root) == {("wfctl.session._handoff", "wfctl.evidence._status")}


def test_dotted_and_relative_names_resolve_inside_subpackages(
    check: ModuleType, tmp_path: Path,
) -> None:
    root = make_tree(tmp_path, {
        "evidence/__init__.py": "from ._status import derive\n",
        "evidence/_status.py": "from .._paths import repo\nimport wfctl.evidence._other\n",
        "evidence/_other.py": "",
        "_paths.py": "",
    })

    assert graph(check, root) == {
        ("wfctl.evidence", "wfctl.evidence._status"),
        ("wfctl.evidence._status", "wfctl._paths"),
        ("wfctl.evidence._status", "wfctl.evidence._other"),
    }


def test_the_real_domain_page_reads_as_seven_contexts_two_shared_and_six_arrows(
    check: ModuleType,
) -> None:
    """The fixture page is written to match the real one, and this is what
    says it still does. The real block indents its lines and has a blank line
    between nodes and edges."""
    domain = check.read_domain(REAL_PAGE)

    assert len(domain.contexts) == 7
    assert domain.shared == frozenset({"core", "tracker"})
    assert len(domain.arrows) == 6


# --- where the tree comes from, and what it may be (T009) ----------------------


def test_the_tree_comes_from_the_current_directory_not_the_scripts_path(
    tmp_path: Path,
) -> None:
    """The `review` job runs the trusted copy from inside the PR's checkout. A
    script that found the tree from its own path would check the trusted tree
    and pass every PR."""
    root = make_tree(tmp_path, {"_new.py": ""})

    done = subprocess.run(
        [sys.executable, "-I", str(SCRIPT)], cwd=root, capture_output=True, text=True,
        env={**os.environ, "NO_COLOR": "1"},
    )

    assert done.returncode == 1
    assert "wfctl/_new.py has no package" in done.stdout


@pytest.mark.parametrize("which", ["page", "baseline", "module"])
def test_a_symlinked_input_fails_and_never_prints_its_target(
    check: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], which: str,
) -> None:
    """In the `review` job, a PR could link the baseline to `pr/.git/config`,
    and a failure that quoted the bad line would print that file to a public
    log."""
    secret = tmp_path / "secret.txt"
    secret.write_text("token=hunter2\n")
    root = make_tree(tmp_path / "repo", {"_x.py": ""}, baseline="_x.py core\n")
    target = {
        "page": page_at(root),
        "baseline": baseline_at(root),
        "module": root / "wfctl" / "_x.py",
    }[which]
    target.unlink()
    target.symlink_to(secret)

    code, out = run_main(check, root, monkeypatch, capsys)

    assert code == 1
    assert str(target.relative_to(root)) in out
    assert "symlink" in out
    assert "hunter2" not in out


# --- US1: an import the map doesn't allow fails (T016, T017) -------------------


def flat(text: str) -> str:
    """Whitespace collapsed, so prose is compared without its line breaks."""
    return " ".join(text.split())


def rules(check: ModuleType, root: Path) -> list[tuple[str, str, str]]:
    failures, _, _ = check.rule_check(root)
    return [(f.kind, f.src, f.dst) for f in failures]


PLACED = """\
    _verify.py evidence
    _pipeline.py evidence
    _session.py session
    _paths.py core
    _tracker.py tracker
"""


def test_an_evidence_module_importing_a_session_module_fails_as_no_arrow(
    check: ModuleType, tmp_path: Path,
) -> None:
    """US1 scenario 1, FR-003. The map draws Evidence to Session and not back."""
    root = make_tree(tmp_path, {
        "_verify.py": "from wfctl._session import record_blocked\n",
        "_pipeline.py": "", "_session.py": "", "_paths.py": "", "_tracker.py": "",
    }, baseline=PLACED)

    assert rules(check, root) == [("no-arrow", "wfctl/_verify.py", "wfctl._session")]


def test_a_session_module_importing_the_evidence_package_passes(
    check: ModuleType, tmp_path: Path,
) -> None:
    """US1 scenario 2. The arrow runs from Evidence to Session."""
    root = make_tree(tmp_path, {
        "session/__init__.py": "",
        "session/_handoff.py": "from wfctl.evidence import derive\n",
        "evidence/__init__.py": "def derive(): ...\n",
    })

    assert rules(check, root) == []


def test_two_modules_in_one_context_pass(check: ModuleType, tmp_path: Path) -> None:
    """US1 scenario 3, FR-001. A context's own modules import each other freely."""
    root = make_tree(tmp_path, {
        "_verify.py": "from wfctl import _pipeline\n",
        "_pipeline.py": "", "_session.py": "", "_paths.py": "", "_tracker.py": "",
    }, baseline=PLACED)

    assert rules(check, root) == []


def test_the_no_arrow_failure_draws_the_boundary_and_says_what_to_do(
    check: ModuleType,
) -> None:
    """FR-011. The block names the file and line, both contexts, the drawn
    boundary, and the action, in the shape `contracts/failure-output.md` gives."""
    out = check.render(check.Failure(
        "no-arrow", "wfctl/evidence/_status.py", "wfctl.session", 41,
        ("Evidence and derivation", "Session continuity"), reverse=True,
    ))
    lines = out.splitlines()

    assert lines[0] == "✗ wfctl/evidence/_status.py:41 imports wfctl.session"
    assert lines[1] == ""
    assert lines[2].startswith("  ┌ Evidence and derivation ")
    assert "┌ Session continuity " in lines[2]
    assert "◀──────────│" in lines[3] and lines[3].endswith("  allowed, the map draws it")
    assert "│ _status.py ─" in lines[4] and "┼─────✗────▶│ wfctl.session" in lines[4]
    assert lines[4].endswith("  refused, no arrow this way")
    assert lines[5].startswith("  └") and lines[5].endswith("┘")
    assert flat("\n".join(lines[6:])) == (
        "Move what you need into Evidence and derivation. If the dependency is meant, "
        "ask the user to add the arrow in docs/architecture/domain/wfctl.md."
    )


def test_the_no_arrow_drawing_leaves_out_an_arrow_the_map_doesnt_draw(
    check: ModuleType,
) -> None:
    """With no arrow either way, a line saying one is allowed would be false."""
    out = check.render(check.Failure(
        "no-arrow", "wfctl/_issue_check.py", "wfctl._provenance", 3,
        ("Session continuity", "Install and drift"),
    ))

    assert "allowed" not in out and "◀" not in out


def test_every_box_line_lines_up(check: ModuleType) -> None:
    """A box whose borders drift by one column reads as a broken drawing."""
    for failure in (
        check.Failure("no-arrow", "wfctl/_verify.py", "wfctl._session", 1,
                      ("Evidence and derivation", "Session continuity"), reverse=True),
        check.Failure("internal-module", "wfctl/session/_handoff.py",
                      "wfctl.evidence._paths", 12,
                      ("Session continuity", "Evidence and derivation"),
                      detail="wfctl.evidence"),
    ):
        drawing = check.render(failure).splitlines()[2:6]
        corners = [line.index("┐") for line in drawing[:1]]
        assert [line[corners[0]] for line in drawing] == ["┐", "│", "┼", "┘"]


# --- US2: a context's package, never its modules (T021 to T023) ----------------


def test_importing_a_module_inside_another_contexts_package_fails(
    check: ModuleType, tmp_path: Path,
) -> None:
    """US2 scenario 1, FR-004. The arrow allows the package, not its insides."""
    root = make_tree(tmp_path, {
        "session/__init__.py": "",
        "session/_handoff.py": "from wfctl.evidence import _status\n",
        "evidence/__init__.py": "",
        "evidence/_status.py": "",
    })
    failures, _, _ = check.rule_check(root)

    assert [(f.kind, f.src, f.dst, f.detail) for f in failures] == [
        ("internal-module", "wfctl/session/_handoff.py", "wfctl.evidence._status",
         "wfctl.evidence"),
    ]


def test_any_module_may_import_a_shared_package(check: ModuleType, tmp_path: Path) -> None:
    """US2 scenario 2, FR-005. Even a module inside `core` is open to all."""
    root = make_tree(tmp_path, {
        "core/__init__.py": "", "core/_paths.py": "",
        "tracker/__init__.py": "",
        "evidence/__init__.py": "from wfctl.core import _paths\nfrom wfctl import tracker\n",
        "session/__init__.py": "import wfctl.core._paths\n",
    })

    assert rules(check, root) == []


def test_wiring_may_import_a_contexts_package_and_not_a_module_inside_it(
    check: ModuleType, tmp_path: Path,
) -> None:
    """US2 scenario 3, FR-006."""
    root = make_tree(tmp_path, {
        "cli.py": "from wfctl import evidence, session\nfrom wfctl.evidence import _status\n",
        "_entry.py": "from wfctl.session import _restart\n",
        "evidence/__init__.py": "", "evidence/_status.py": "",
        "session/__init__.py": "", "session/_restart.py": "",
    })

    assert rules(check, root) == [
        ("internal-module", "wfctl/_entry.py", "wfctl.session._restart"),
        ("internal-module", "wfctl/cli.py", "wfctl.evidence._status"),
    ]


def test_a_shared_package_importing_a_context_fails(check: ModuleType, tmp_path: Path) -> None:
    """A shared package that imports a context makes every context depend on it."""
    root = make_tree(tmp_path, {
        "_tracker.py": "from wfctl import _session\n",
        "_session.py": "", "_verify.py": "", "_pipeline.py": "", "_paths.py": "",
    }, baseline=PLACED)

    assert rules(check, root) == [
        ("shared-imports-context", "wfctl/_tracker.py", "wfctl._session"),
    ]


def test_an_unmoved_target_is_exempt_from_the_internal_module_rule(
    check: ModuleType, tmp_path: Path,
) -> None:
    """A flat module has no package to import it through yet, so the map's
    arrow is the whole of what applies to it."""
    root = make_tree(tmp_path, {
        "session/__init__.py": "",
        "session/_handoff.py": "from wfctl import _verify\n",
        "_verify.py": "", "_pipeline.py": "", "_session.py": "", "_paths.py": "",
        "_tracker.py": "",
    }, baseline=PLACED.replace("    _session.py session\n", ""))
    (root / "wfctl" / "_session.py").unlink()

    assert rules(check, root) == []


def test_a_dependency_through_an_allowed_package_is_not_a_violation(
    check: ModuleType, tmp_path: Path,
) -> None:
    """Guard imports Evidence and Evidence imports Architecture records. Only
    direct imports are checked, so the guard reaching records through Evidence
    is the map working, not a gap in it."""
    root = make_tree(tmp_path, {
        "guard/__init__.py": "from wfctl import evidence\n",
        "evidence/__init__.py": "from wfctl import arch\n",
        "arch/__init__.py": "",
    })

    assert rules(check, root) == []


def test_the_internal_module_and_shared_failures_print_in_the_contracts_shape(
    check: ModuleType,
) -> None:
    internal = check.render(check.Failure(
        "internal-module", "wfctl/session/_handoff.py", "wfctl.evidence._paths", 12,
        ("Session continuity", "Evidence and derivation"), detail="wfctl.evidence",
    )).splitlines()

    assert internal[0] == "✗ wfctl/session/_handoff.py:12 imports wfctl.evidence._paths"
    assert "──────────▶│ wfctl.evidence " in internal[3]
    assert internal[3].endswith("  allowed")
    assert "┼─────✗────▶│ _paths " in internal[4]
    assert internal[4].endswith("  refused, internal")
    assert flat("\n".join(internal[6:])) == (
        "Import it from wfctl.evidence. If the package lacks what you need, export it "
        "from its __init__.py."
    )

    shared = check.render(check.Failure(
        "shared-imports-context", "wfctl/_tracker.py", "wfctl._session", 309,
        detail="tracker",
    )).splitlines()

    assert shared[0] == "✗ wfctl/_tracker.py:309 imports wfctl._session"
    assert flat("\n".join(shared[1:])) == (
        "_tracker.py is in tracker, which any context may import. A shared package that "
        "imports a context makes every context depend on that one. Pass in what you need "
        "from the caller instead."
    )
