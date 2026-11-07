# Delivery Plan: Reviewers check that each layer accepts the same input (724)

**Feature**: `724-cross-layer-review` | **Date**: 2026-11-06
**Source**: `specs/724-cross-layer-review/tasks.md` (16 tasks)
**Parent issue**: #621

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (opened at review) | T001 - T016 | `wfctl/agents/skills/code-review/SKILL.md` (modified), `wfctl/agents/commands/code-review.md` (modified), `wfctl/agents/skills/requesting-code-review/SKILL.md` (modified), `wfctl/agents/skills/fanning-out-code-review/SKILL.md` (modified), `tests/test_review_fanout_skill.py` (modified), `changes/724.change.md` (created) | M | The three checks pass, `doctor` reports no drift, and the PFMS and docs-only reviewer runs (T009, T012) pass |

**Rationale**: Single PR. All three stories edit `code-review/SKILL.md`, and the pass-count test only passes once both new passes exist, so no subset merges on its own.

**PR closes**: `Closes #724`

#724 is one of several children of #621, so this PR doesn't close the parent.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #724 | T001 - T016 | `[724] Reviewers check that each layer accepts the same input` | M | this branch's PR |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the whole feature, and the branch's own issue already exists, so no issue is created.

---

## File-touch matrix

| Task | Files |
|------|-------|
| T001 | read only (baseline test run and search) |
| T002 | MODIFY `code-review/SKILL.md`, `tests/test_review_fanout_skill.py` |
| T003, T004, T007, T008, T010 | MODIFY `code-review/SKILL.md` |
| T005 | MODIFY `code-review/SKILL.md` (frontmatter), `commands/code-review.md` |
| T006 | read only (pytest) |
| T009, T012 | read only (reviewer runs, after `install-skills`) |
| T011 | MODIFY `requesting-code-review/SKILL.md` |
| T013 | MODIFY `fanning-out-code-review/SKILL.md` |
| T014 | read only (`git diff --stat`) |
| T015 | CREATE `changes/724.change.md` |
| T016 | read only (definition of done) |

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | baseline, no edits |
| 1 | Sequential | T002 → T003 → T004 → T007 → T008 → T010 | all edit `code-review/SKILL.md` |
| 1 | Parallel | T005 ‖ T011 ‖ T013 ‖ T015 | other files; T005's frontmatter edit waits for the Wave 1 sequence to free `code-review/SKILL.md` |
| 2 | Sequential | T006 | pass-count test, needs passes 7 and 8 |
| 3 | Parallel | T009 ‖ T012 ‖ T014 | after `uv run wfctl install-skills` |
| 4 | Sequential | T016 | definition of done, merge gate |

**Single-agent order** (recommended):
T001 → T002 → T003 → T004 → T007 → T008 → T010 → T005 → T011 → T013 → T015 → T006 → T009 → T012 → T014 → T016

---

## Agent Fanning Instructions

A single agent is recommended. Most of the edits land in one file, and the two reviewer runs (T009, T012) are the only work worth fanning out, as fresh-context reviewers.
