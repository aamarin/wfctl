"""Architecture records: reading each decision record, keeping only the accepted
ones in force, and choosing which of them apply to a branch.

Other contexts and the wiring import from this package, never from a module
inside it (`docs/architecture/contexts-are-packages.md`). Every re-export loads
on first use, because the worktree guard imports wfctl before every shell
command an agent runs, and an eager import here would load the whole context
each time.

The brainstorm gate isn't here. It pairs these records with a branch's design
exceptions, which belong to evidence, and this context may not import evidence.
"""
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._contexts import Selection, listed, malformed, names, select
    from ._records import (
        DIAGRAM_KINDS,
        DOMAIN_MODEL_SECTION,
        IN_FORCE,
        LEVEL_2_SECTION,
        LEVEL_3_SECTION,
        RULED_ON,
        Finding,
        Record,
        accept,
        accept_blockers,
        acceptable,
        accepted_on,
        decision_text,
        excluded_by_status,
        in_force,
        load_records,
        parse_governs,
        parse_status,
        supersede,
        validate,
    )

_LAZY = {
    "Selection": "._contexts",
    "listed": "._contexts",
    "malformed": "._contexts",
    "names": "._contexts",
    "select": "._contexts",
    "DIAGRAM_KINDS": "._records",
    "DOMAIN_MODEL_SECTION": "._records",
    "IN_FORCE": "._records",
    "LEVEL_2_SECTION": "._records",
    "LEVEL_3_SECTION": "._records",
    "RULED_ON": "._records",
    "Finding": "._records",
    "Record": "._records",
    "accept": "._records",
    "accept_blockers": "._records",
    "acceptable": "._records",
    "accepted_on": "._records",
    "decision_text": "._records",
    "excluded_by_status": "._records",
    "in_force": "._records",
    "load_records": "._records",
    "parse_governs": "._records",
    "parse_status": "._records",
    "supersede": "._records",
    "validate": "._records",
}

__all__ = [
    "Selection",
    "listed",
    "malformed",
    "names",
    "select",
    "DIAGRAM_KINDS",
    "DOMAIN_MODEL_SECTION",
    "IN_FORCE",
    "LEVEL_2_SECTION",
    "LEVEL_3_SECTION",
    "RULED_ON",
    "Finding",
    "Record",
    "accept",
    "accept_blockers",
    "acceptable",
    "accepted_on",
    "decision_text",
    "excluded_by_status",
    "in_force",
    "load_records",
    "parse_governs",
    "parse_status",
    "supersede",
    "validate",
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
