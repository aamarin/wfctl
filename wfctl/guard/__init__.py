"""Worktree guard: the hook that runs before every shell command an agent runs,
and the rules that decide whether the command may reach another worktree.

Other contexts and the wiring import from this package, never from a module
inside it (`docs/architecture/contexts-are-packages.md`). The one re-export
loads on first use, because `_entry` imports this package for every shell
command, and most of those commands never reach `_guard`'s rules.

The review and record checks the hook runs before `gh pr create` and `gh pr
merge` belong to evidence, not here. The guard calls them and prints their
refusals.
"""
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._hook import worktree_guard

_LAZY = {
    "worktree_guard": "._hook",
}

__all__ = [
    "worktree_guard",
]


def __getattr__(name: str) -> object:
    module = _LAZY.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module, __name__), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return list(__all__)
