# Delivery Plan: promote a decision to accepted (321)

**Feature**: `321-promote-a-decision` | **Date**: 2026-09-09
**Source**: `specs/321-promote-a-decision/tasks.md` (22 tasks)
**Parent issue**: #321

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| #1 | T001–T022 | `wfctl/_arch.py` (modified), `wfctl/cli.py` (modified), `tests/test_arch_records.py` (modified), `tests/test_arch_commands.py` (created), `docs/architecture/a-human-accepts-a-decision.md` (created), `docs/architecture/design/321-one-status-mutation.md` (created), `docs/architecture/scans/321-clarify.md` (created), `docs/architecture/scans/321-analyze.md` (created) | S | definition of done green: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl doctor` |

**Rationale**: Single PR. The change is one decision and its mechanism, and they
are mutually dependent in the direction that matters — the record states a rule
whose only expression is the command, and the command is arbitrary without the
record. Splitting them would put a reviewer in front of a mechanism with no
argument, which is exactly what the issue says a PR here must not be.

The extraction of `_set_status` could physically ship first as a pure refactor.
It is kept in the same PR because on its own it is a rename with no reason a
reviewer could evaluate: the reason is the second caller.

**PR closes**: `Closes #321`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #321 | T001–T022 | `[321] Nothing promotes an architecture decision from proposed to accepted` | S | PR #1 |

**Grouping pattern**: 1:1 explicit
**Rationale**: One issue, one decision, one PR. No issue is created by this run —
the row names #321, which already exists, so nothing here reaches anyone outside
the repository.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | definition of done green before any change, so a later failure is attributable |
| 1 | Sequential | T002 → T003 | the shared mutation; the existing supersede tests must pass **unedited** |
| 2 | Sequential | T004 | `accept` and its `proposed`-only guard |
| 3 | Parallel | T005 ‖ T006 ‖ T007 ‖ T008 | four module tests, one file, no shared fixture state |
| 4 | Sequential | T009 → T010 | the command, then its end-to-end check |
| 5 | Parallel | T011–T015 ‖ T016–T018 | story 2 and story 3 depend on T009 and on nothing from each other |
| 6 | Sequential | T019 → T020 → T021, T022 | definition of done, the manual walkthrough, then the two closing checks |

**Single-agent order** (recommended for this S feature):
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 →
T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022

---

## Agent Fanning Instructions

Single agent. The feature is S, every wave but two is sequential, and the two
parallel waves are tests in one or two files — the coordination costs more than
the wall-clock it saves.

**T021 is not an agent's to do.** It accepts this change's own record, which
requires a human to have agreed. The record says so in its own Consequences and
the `auto_approve` mode explicitly does not reach it. Left for the maintainer,
after review.
