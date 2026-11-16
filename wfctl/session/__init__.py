"""Session continuity: carry work from one agent session to the next.

This context holds the handoff a session leaves for the next one, the restart
hook, the check that a session's issue is open, the session-start report, and
saving the spec dir and unsaved work before a worktree is removed. Where the
pipeline stands and the event log belong to evidence, and this context reads
both from `wfctl.evidence`.

Other contexts and the wiring import from this package, never from a module
inside it (`docs/architecture/contexts-are-packages.md`). Each re-export loads
on first use, because the restart hook reaches `hook_main` through this package
on every reply end, and none of the other modules is used there.

A few names are re-exported under a longer name than the module gives them,
such as `check_unsaved` for `_archive.check`, since `check`, `save`, `decide`,
and `end` alone don't say which part of this context they belong to.
"""
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._archive import SaveFailed, UnsavedCheck, declared_paths, is_inside
    from ._archive import check as check_unsaved
    from ._archive import save as save_unsaved
    from ._issue_check import decide as decide_issue_check
    from ._issue_check import gather as gather_issue_facts
    from ._issue_check import names_no_issue
    from ._restart import hook_main
    from ._session import (
        Observations,
        in_flight_unfilled,
        names_no_first_action,
        presented_identity,
    )
    from ._session import end as end_session
    from ._session_report import (
        build_session_report,
        default_readers,
        render_session_report,
        trunk_label,
    )
    from ._spec_copy import CopyResult, copy_out, difference_rows

# Each public name, and the module and attribute it comes from.
_LAZY = {
    "SaveFailed": ("._archive", "SaveFailed"),
    "UnsavedCheck": ("._archive", "UnsavedCheck"),
    "check_unsaved": ("._archive", "check"),
    "declared_paths": ("._archive", "declared_paths"),
    "is_inside": ("._archive", "is_inside"),
    "save_unsaved": ("._archive", "save"),
    "decide_issue_check": ("._issue_check", "decide"),
    "gather_issue_facts": ("._issue_check", "gather"),
    "names_no_issue": ("._issue_check", "names_no_issue"),
    "hook_main": ("._restart", "hook_main"),
    "Observations": ("._session", "Observations"),
    "end_session": ("._session", "end"),
    "in_flight_unfilled": ("._session", "in_flight_unfilled"),
    "names_no_first_action": ("._session", "names_no_first_action"),
    "presented_identity": ("._session", "presented_identity"),
    "build_session_report": ("._session_report", "build_session_report"),
    "default_readers": ("._session_report", "default_readers"),
    "render_session_report": ("._session_report", "render_session_report"),
    "trunk_label": ("._session_report", "trunk_label"),
    "CopyResult": ("._spec_copy", "CopyResult"),
    "copy_out": ("._spec_copy", "copy_out"),
    "difference_rows": ("._spec_copy", "difference_rows"),
}

__all__ = [
    "SaveFailed",
    "UnsavedCheck",
    "check_unsaved",
    "declared_paths",
    "is_inside",
    "save_unsaved",
    "decide_issue_check",
    "gather_issue_facts",
    "names_no_issue",
    "hook_main",
    "Observations",
    "end_session",
    "in_flight_unfilled",
    "names_no_first_action",
    "presented_identity",
    "build_session_report",
    "default_readers",
    "render_session_report",
    "trunk_label",
    "CopyResult",
    "copy_out",
    "difference_rows",
]


def __getattr__(name: str) -> object:
    source = _LAZY.get(name)
    if source is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module, attribute = source
    value = getattr(import_module(module, __name__), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return list(__all__)
