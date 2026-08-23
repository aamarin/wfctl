# Delivery Plan: Judgment rules section for conversation-response-shape (73)

**Feature**: `73-judgment-rules-section` | **Date**: 2026-08-23
**Source**: `wfctl-specs/73-judgment-rules-section/tasks.md` (12 tasks)
**Parent issue**: #73 (no parent epic — #73 is the issue itself)

---

## File-Touch Matrix

| Task | File | Mode |
|---|---|---|
| T001 | `wfctl/agents/skills/conversation-response-shape/SKILL.md`, `.agents/skills/conversation-response-shape/SKILL.md` | READ ONLY (baseline diff) |
| T002 | `wfctl/agents/skills/conversation-response-shape/SKILL.md` | MODIFY (insert section) |
| T003 | same | MODIFY (add rule + illustration) |
| T004 | same | MODIFY (add rule + illustration) |
| T005 | — | READ ONLY (validate) |
| T006 | same | MODIFY (add rule + illustration) |
| T007 | same | MODIFY (table row) |
| T008 | — | READ ONLY (validate) |
| T009 | same | MODIFY (retitle) |
| T010 | — | READ ONLY (validate) |
| T011 | same | READ ONLY (grep) |
| T012 | `wfctl/`, `tests/` | READ ONLY (full DoD sweep) |

**One file modified across the entire feature**: `wfctl/agents/skills/conversation-response-shape/SKILL.md`.

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| PR (this branch) | T001–T012 | `wfctl/agents/skills/conversation-response-shape/SKILL.md` (modified) | XS (1 file) | `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, `wfctl install-skills && wfctl doctor` all green (T012) |

**Rationale**: Single PR. One file, and the three rule additions plus the
retitle are one coherent, mutually-reinforcing change — a reviewer needs all of
it together to judge whether the retitle actually fixes what it claims to
(FR-006 exists *because* it made rule 3's architecture row wrong otherwise).
tasks.md's own "Logical PR Boundaries" note already rejected a 3-way split:
landing "the section exists" without its third rule and the title fix leaves
the feature inconsistent, not incrementally useful. File-conflict signal is
moot (one file); reviewability and mergeable-increment signals both say bundle;
story-independence is the only signal that could argue for a split, and even
there US2 has a hard dependency on US1 (appends into the section US1 creates),
so it doesn't clear the bar either.

**PR closes**: `Closes #73`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #73 | T001–T012 | Judgment rules section for conversation-response-shape | XS — single session | PR (this branch) |

**Grouping pattern**: Single issue (default).
**Rationale**: XS scope, one file, one existing issue (#73) that already names
the exact work — no new GitHub issue needed.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | Baseline check — no dependencies, must run first |
| 1 | Sequential | T002 → T007 → T009 | No dependency between these three, but all three edit the same file at disjoint regions (new section, table row, section title) — sequential to avoid clobbering each other's diff, order doesn't otherwise matter |
| 2 | Sequential | T003 → T004 → T006 | Each depends on T002 (append into the section it creates); same file/section, so sequential rather than [P] despite no task-to-task dependency among the three |
| 3 | Parallel | T005 ‖ T008 ‖ T010 ‖ T011 ‖ T012 | All read-only validation once every edit lands — safe to run together (grep/test/lint, no shared mutable state) |

**Single-agent order** (recommended for XS features):
T001 → T002 → T007 → T009 → T003 → T004 → T006 → T005 → T008 → T010 → T011 → T012

---

## Agent Fanning Instructions

Single agent recommended for this XS feature (one file, 12 tasks). Wave table
above provided for reference and template reuse — fanning to parallel agents
would add coordination overhead with no real speedup, since every edit task
touches the same file.
