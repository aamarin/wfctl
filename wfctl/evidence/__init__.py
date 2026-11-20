"""Evidence and derivation: what has happened, based on what the durable
artifacts prove.

Most of this context's modules still sit flat under `wfctl/`, placed here by
the import check's baseline, and move in under #768. The event log and the
approval mode moved first, because session continuity reads both and the
status code reads both, and evidence may not import session continuity.

Other contexts import from this package, never from a module inside it
(`docs/architecture/contexts-are-packages.md`). Each re-export loads on first
use. The worktree guard imports evidence modules before every shell command
an agent runs, and the restart hook runs on every reply end, so an eager import
here would add its cost to both.
"""
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._events import (
        StandingBlock,
        identity,
        last_session_id,
        last_stop,
        read_events,
        record_blocked,
        record_outward_action,
        record_worktree_span,
        session_open_for,
        session_started,
        standing_blocks,
        worktree_created,
    )
    from ._timings import (
        compute_summary,
        load_branch_events,
        main_checkout_branch,
        read_open_worktrees,
        render_summary,
    )
    from ._mode import (
        MODE_NAME,
        ModeChange,
        auto_approve,
        grant_auto_approve,
        last_change,
        newest_is_grant,
        revoke_auto_approve,
        revoked,
    )

_LAZY = {
    "StandingBlock": "._events",
    "identity": "._events",
    "last_session_id": "._events",
    "last_stop": "._events",
    "read_events": "._events",
    "record_blocked": "._events",
    "record_outward_action": "._events",
    "record_worktree_span": "._events",
    "session_open_for": "._events",
    "session_started": "._events",
    "standing_blocks": "._events",
    "worktree_created": "._events",
    "compute_summary": "._timings",
    "load_branch_events": "._timings",
    "main_checkout_branch": "._timings",
    "read_open_worktrees": "._timings",
    "render_summary": "._timings",
    "MODE_NAME": "._mode",
    "ModeChange": "._mode",
    "auto_approve": "._mode",
    "grant_auto_approve": "._mode",
    "last_change": "._mode",
    "newest_is_grant": "._mode",
    "revoke_auto_approve": "._mode",
    "revoked": "._mode",
}

__all__ = [
    "StandingBlock",
    "identity",
    "last_session_id",
    "last_stop",
    "read_events",
    "record_blocked",
    "record_outward_action",
    "record_worktree_span",
    "session_open_for",
    "session_started",
    "standing_blocks",
    "worktree_created",
    "compute_summary",
    "load_branch_events",
    "main_checkout_branch",
    "read_open_worktrees",
    "render_summary",
    "MODE_NAME",
    "ModeChange",
    "auto_approve",
    "grant_auto_approve",
    "last_change",
    "newest_is_grant",
    "revoke_auto_approve",
    "revoked",
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
