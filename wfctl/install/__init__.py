"""Install and drift: putting wfctl's skills and config into a project, and
reporting when they drift from the bundle the running wfctl ships.

Other contexts and the wiring import from this package, never from a module
inside it (`docs/architecture/contexts-are-packages.md`). Every re-export loads
on first use, because the worktree guard imports wfctl before every shell
command an agent runs, and an eager import here would load the whole context
each time.
"""
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._bob_settings import remove_tool_allow
    from ._bundle import BUNDLE_ROOT, TREES, content_hash, resolve_root
    from ._provenance import Kind, describe, read, runner
    from ._settings import (
        MANAGED_PREFIX,
        managed_command,
        managed_matcher,
        managed_subcommands,
        merge_hook,
        merge_permission,
        permission_present,
        prune_unshipped,
        related_rules,
        remove_hooks,
        remove_permission,
        subcommand_of,
    )
    from ._workmux import (
        PROJECT_PLACEHOLDER,
        REMOVE_HOOK,
        patch_seed,
        post_create_wired,
        pre_remove_masked,
        pre_remove_wired,
        tmux_safe,
        unsubstituted_placeholder,
        wire_pre_remove,
        worktree_dir,
        worktree_dir_line,
    )

_LAZY = {
    "remove_tool_allow": "._bob_settings",
    "BUNDLE_ROOT": "._bundle",
    "TREES": "._bundle",
    "content_hash": "._bundle",
    "resolve_root": "._bundle",
    "Kind": "._provenance",
    "describe": "._provenance",
    "read": "._provenance",
    "runner": "._provenance",
    "MANAGED_PREFIX": "._settings",
    "managed_command": "._settings",
    "managed_matcher": "._settings",
    "managed_subcommands": "._settings",
    "merge_hook": "._settings",
    "merge_permission": "._settings",
    "permission_present": "._settings",
    "prune_unshipped": "._settings",
    "related_rules": "._settings",
    "remove_hooks": "._settings",
    "remove_permission": "._settings",
    "subcommand_of": "._settings",
    "PROJECT_PLACEHOLDER": "._workmux",
    "REMOVE_HOOK": "._workmux",
    "patch_seed": "._workmux",
    "post_create_wired": "._workmux",
    "pre_remove_masked": "._workmux",
    "pre_remove_wired": "._workmux",
    "tmux_safe": "._workmux",
    "unsubstituted_placeholder": "._workmux",
    "wire_pre_remove": "._workmux",
    "worktree_dir": "._workmux",
    "worktree_dir_line": "._workmux",
}

__all__ = [
    "remove_tool_allow",
    "BUNDLE_ROOT",
    "TREES",
    "content_hash",
    "resolve_root",
    "Kind",
    "describe",
    "read",
    "runner",
    "MANAGED_PREFIX",
    "managed_command",
    "managed_matcher",
    "managed_subcommands",
    "merge_hook",
    "merge_permission",
    "permission_present",
    "prune_unshipped",
    "related_rules",
    "remove_hooks",
    "remove_permission",
    "subcommand_of",
    "PROJECT_PLACEHOLDER",
    "REMOVE_HOOK",
    "patch_seed",
    "post_create_wired",
    "pre_remove_masked",
    "pre_remove_wired",
    "tmux_safe",
    "unsubstituted_placeholder",
    "wire_pre_remove",
    "worktree_dir",
    "worktree_dir_line",
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
