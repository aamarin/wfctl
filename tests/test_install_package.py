"""The `wfctl.install` package's public surface, and what importing it costs.

The package re-exports through a module-level `__getattr__`, so mypy types a
misspelled name as `object` rather than failing on it, and nothing else checks
`__all__`, the lazy table, and the `TYPE_CHECKING` imports against each other.
These tests are that check.
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from wfctl import install

INIT = Path(install.__file__)


def _type_checking_names() -> set[str]:
    """The names the `if TYPE_CHECKING:` block imports, which is what a type
    checker and an IDE read for each re-export's real signature."""
    tree = ast.parse(INIT.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.If) and getattr(node.test, "id", None) == "TYPE_CHECKING":
            return {
                alias.asname or alias.name
                for stmt in node.body
                if isinstance(stmt, ast.ImportFrom)
                for alias in stmt.names
            }
    raise AssertionError("wfctl/install/__init__.py has no `if TYPE_CHECKING:` block")


def test_all_the_lazy_table_and_the_type_checking_block_name_the_same_things() -> None:
    """A name in `_LAZY` but not `__all__` imports fine and is invisible to a
    star import and to mypy's re-export rules; a name in `__all__` but not
    `_LAZY` raises on first use. Either goes unseen until a caller hits it."""
    assert len(install.__all__) == len(set(install.__all__)), "a name is listed twice"
    assert set(install.__all__) == set(install._LAZY)
    assert set(install.__all__) == _type_checking_names()


def test_every_public_name_is_the_object_its_module_defines() -> None:
    """A table entry pointing at the wrong module raises `AttributeError` on
    first use, which is far from the typo.

    Run in a fresh interpreter, since conftest's autouse fixtures replace
    `BUNDLE_ROOT` and `read` on the package for every test in this one."""
    probe = (
        "from importlib import import_module\n"
        "from wfctl import install\n"
        "for name, module in install._LAZY.items():\n"
        "    defining = import_module(module, install.__name__)\n"
        "    if getattr(install, name) is not getattr(defining, name):\n"
        "        print(name)\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=True,
    )
    assert done.stdout == ""


def test_an_unknown_name_raises_the_error_python_raises_for_any_module() -> None:
    """`from wfctl.install import missing` turns this into the `ImportError` a
    caller expects, so the message has to read as Python's own would."""
    with pytest.raises(AttributeError) as raised:
        getattr(install, "no_such_name")
    assert str(raised.value) == "module 'wfctl.install' has no attribute 'no_such_name'"


def _loaded_after(statement: str) -> set[str]:
    """The wfctl modules a fresh interpreter holds after `statement`."""
    probe = (
        f"{statement}\n"
        "import sys\n"
        "print('\\n'.join(m for m in sys.modules if m.startswith('wfctl')))\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=True,
    )
    return set(done.stdout.split())


def test_importing_the_package_loads_none_of_its_modules() -> None:
    """One eager re-export would load its module for every caller that wanted
    any other name, which is the cost `contexts-are-packages` rules out."""
    loaded = _loaded_after("import wfctl.install")
    assert "wfctl.install" in loaded
    assert not {m for m in loaded if m.startswith("wfctl.install.")}


def test_one_name_loads_only_the_module_that_defines_it() -> None:
    loaded = _loaded_after("from wfctl.install import tmux_safe")
    assert {m for m in loaded if m.startswith("wfctl.install.")} == {"wfctl.install._workmux"}


def test_the_worktree_guard_does_not_load_the_install_package() -> None:
    """The guard runs before every shell command an agent issues, and it
    needs nothing from install and drift."""
    loaded = _loaded_after("import wfctl._guard")
    assert not {m for m in loaded if m.startswith("wfctl.install")}
