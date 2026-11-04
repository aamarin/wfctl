# Delivery Plan: Session start loads the records for the branch's contexts (700)

**Feature**: `700-session-start-relevant-records` | **Date**: 2026-11-04
**Source**: `/Users/andremarin/Development/wfctl-specs/700-session-start-relevant-records/tasks.md` (26 tasks)
**Parent issue**: none

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| one PR, not yet opened | T001 - T026 | `wfctl/_contexts.py` (modified), `wfctl/_evidence.py` (modified), `wfctl/cli.py` (modified, `arch_context_cmd` only), `wfctl/_session_report.py` (modified), `.github/scripts/check_imports.baseline` (modified, one line removed), `wfctl/agents/skills/start-session/SKILL.md` (modified), `wfctl/agents/skills/architecture-decisions/SKILL.md` (modified), `changes/700.change.md` (created), `tests/test_contexts.py`, `tests/test_evidence.py`, `tests/test_remaining_commands.py`, `tests/test_session_report.py`, `tests/test_cli_status.py` (all modified) | M | T026 green, every review group run, and `branch-contexts-select-records` accepted |

**Rationale**: Single PR. The file count reaches 13, but 5 of those are test
files paired with the source change they check, and 3 more are two skill
paragraphs and a release note. The code change is two new functions and edits
to two existing ones.

The four boundary signals all point to one PR:

1. **File conflict risk**: US1, US2, and the `--all` half of US3 all edit
   `arch_context_cmd`, and they have to land in order.
2. **Reviewability**: FR-010 says `arch context` and the session report get
   their counts from one function. A reviewer can only check that with both
   readers in the same diff.
3. **Mergeable increment**: Merging US1 without US3 would leave the session
   report counting every record while `arch context` prints fewer, which is the
   disagreement FR-010 exists to prevent.
4. **Story independence**: The three stories share `_contexts.select` and
   `_evidence.records_for_branch`, so none of them is independent.

**PR closes**: `Closes #700`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #700 | T001 - T026 | `Session start loads only the records a branch's changes bear on` | M | the one PR above |

**Grouping pattern**: Single issue
**Rationale**: One PR closes exactly one issue, and #700 already exists, so
there's nothing to create.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 → T003 → T004 → T005 | T005: `select` and `records_for_branch` pass their tests, and the import check is green |
| 1 | Parallel | T013 ‖ T021 ‖ T022 ‖ T023 | four separate files: the session report test needs only Wave 0, and the three prose edits depend on nothing in the code |
| 2 | Sequential | T006 → T007 → T008 → T009 → T010 → T011 | all edit `arch_context_cmd`, so they run one after another |
| 3 | Sequential | T012 → T016, then T014 → T015 → T017 → T018 → T019 → T020 | `--all` needs T007; T017 removes the `_arch` import that T019's baseline deletion depends on |
| 4 | Sequential | T024 → T025 → T026 | final sweep: install, the check by hand, then the full definition of done |

**Single-agent order** (recommended for this M feature):
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 →
T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022 →
T023 → T024 → T025 → T026

---

## Agent Fanning Instructions

We recommend a single agent for this feature. Most tasks edit
`arch_context_cmd` or `_session_report.py` in sequence, and the only work that
could run in parallel is the three prose edits in Phase 6, each a paragraph
long. Splitting that work across agents would cost more to coordinate than it
saves.
