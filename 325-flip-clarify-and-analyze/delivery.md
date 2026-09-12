# Delivery Plan: flip clarify and analyze (325)

**Feature**: `325-flip-clarify-and-analyze` | **Date**: 2026-09-10
**Source**: `specs/325-flip-clarify-and-analyze/tasks.md` (17 tasks)
**Parent issue**: #325

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| 1 | T001–T014 | `wfctl/_pipeline.py` (modified), `tests/test_pipeline_sections.py` (modified), `tests/test_pipeline_commands.py` (modified), `docs/architecture/scans/325-clarify.md` (created), `docs/architecture/scans/325-analyze.md` (created) | S | The repository's four commands green, and the review panel's disposition table in the body |

**Rationale**: Single PR. All four boundary signals point the same way. The two
table values and the tests that pin them edit the same three files, so a split
would create concurrent edits rather than avoid them. A reviewer cannot assess
either flip without the other — the argument is that these two steps are the same
shape of step, which is the whole reason #325 is one issue. No subset merges
usefully: flipping one leaves the pipeline still stopping once, which is neither
the old behaviour nor the new one. And the three user stories are not independent
— US2 is the property that makes US1 safe, and US3 is the evidence US1's claim
rests on.

**PR closes**: `Closes #325`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #325 | T001–T014 | `[325] Flip clarify and analyze to automatic` | S | PR 1 |

**Grouping pattern**: Single issue
**Rationale**: An S-sized change delivering one judgment; the default pattern,
and splitting would duplicate a single decision into issues that must resolve the
same way or contradict each other.

---

## Parallelization

| Wave | Tasks | Notes |
|------|-------|-------|
| 0 | T007, T008 | Baseline. Run the blocked-step tests before touching anything, so "still green after" means something. Read-only |
| 1 | T001, T002 | The two table values. Same file, same table, one edit |
| 2 | T003 | The pinning test. After wave 1 so its failure against the unflipped table can be demonstrated first if wanted |
| 3 | T004, T005 [P], T006, T006a [P], T010a [P] | Assertions. T005, T006a and T010a touch different concerns and can be written in any order; T004 and T006 both extend `test_pipeline_commands.py` and are sequenced to avoid stepping on each other |
| 4 | T009, T010, T011, T012, T013, T014, T006b | Validation sweep and the PR body. T009 and T010 are already satisfied — both scan files are committed |

Wave 0 exists because T007 and T008 assert that something did **not** change. A
test first run after the change cannot distinguish "still green" from "green for a
different reason".

---

## Out of scope, filed

Three issues opened while this feature was specified and clarified. None blocks
this PR; each is named here so the PR body can point at them rather than
rediscovering them.

| Issue | What |
|-------|------|
| #330 | A scan file's structure is required by prose and checked by nobody |
| #331 | Analyze step 8 asks for approval and waits — unattended, no rule says what to apply and what to file |
| #332 | speckit-orchestrate has no loop bound — a step that cannot make progress runs until something external stops it |

#331 is the one that matters for this feature's own acceptance: SC-002 needs a
real unattended `/speckit.orchestrate` run, and that run stops at analyze step 8
until #331 lands.
