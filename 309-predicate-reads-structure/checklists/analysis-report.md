# Specification Analysis Report — #309

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`,
`design.md`, and `docs/architecture/required-sections-are-wfctls.md`.
**Read-only.** No artifact was modified by this pass.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| I1 | Inconsistency | MEDIUM | spec.md FR-005; tasks.md T012 | FR-005 requires the constants equal "the shipped template's **mandatory** set". `plan-template.md` marks nothing `_(mandatory)_`, so no such set exists on that side, and T012 already compensates by asserting against that file's `##` headings instead. The requirement generalizes over two artifacts that are not symmetric. | Amend FR-005 to name the two sources separately, as T012 and `data-model.md` already do. Do not change T012 — the task is right and the requirement is over-general. |
| C1 | Coverage gap | MEDIUM | spec.md FR-003; tasks.md T006 | FR-003 requires a shapeless-but-present artifact report `in_progress` **and not** `pending` — the distinction the requirement exists for. T006 asserts only "not `done`", which `pending` also satisfies. | Add the assertion to T006 and T009: the state is exactly `in_progress`. One word per test; the requirement is otherwise unproved. |
| C2 | Coverage gap | MEDIUM | spec.md FR-006, SC-005; tasks.md | FR-006 ("inference reads the spec directory and nothing else") and SC-005 ("a repo that never installed the templates reports the same verdicts") have no task. Both are the level-2 record's load-bearing claim. | Add a task asserting inference against a spec dir with no `.specify/` reachable returns identical states. Cheap — the existing fixtures already build a bare temp dir. |
| U1 | Underspecification | LOW | spec.md FR-009 | "No step's continuation flag changes" is stated as a requirement but is a property of the diff, not of a run. Nothing can observe it at test time except by asserting the `_STEPS` table's contents. | Either add a test pinning the eight flags, or move FR-009 to the PR body as a scope statement. A requirement nothing checks is the shape `a-rule-is-expressed-as-a-check` warns about. |
| T1 | Terminology | LOW | all artifacts | "section", "heading" and "stem" are used for the same thing; `data-model.md` is the only file that distinguishes stem from whole line. | Leave. The distinction that matters is drawn where it matters, and normalizing three words across six files buys nothing. |
| D1 | Duplication | — | spec.md FR-001 / FR-002 | Near-identical requirements for two artifacts. | Not a defect. #309 binds `specify` and `plan` to one decision precisely so the two do not drift; stating it twice is the point. |

## Coverage Summary

| Requirement | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 | yes | T004, T006 | automated | |
| FR-002 | yes | T007, T009 | automated | |
| FR-003 | partial | T004, T007 | **weak** | C1 — asserts "not done", not "in_progress" |
| FR-004 | yes | T005, T008, T006 | automated | |
| FR-005 | yes | T001, T012 | automated | I1 — requirement over-general vs the task |
| FR-006 | **no** | — | **none** | C2 |
| FR-007 | yes | T002, T006 | automated | |
| FR-008 | yes | T010, T011 | automated | |
| FR-009 | partial | T013 | **weak** | U1 — corpus test covers state, not the flags |
| SC-001 | yes | T006, T009 | automated | |
| SC-002 | yes | T013 | automated, skipped where the corpus is absent | |
| SC-003 | yes | T006 | automated | |
| SC-004 | yes | T012 | automated | |
| SC-005 | **no** | — | **none** | C2 |

## Constitution Alignment Issues

None. All seven gates in `plan.md` are checked, and each names its source —
three from the template, four from this repo's accepted records. The
substitution of repo conventions for an absent `.specify/memory/constitution.md`
is recorded in Complexity Tracking, as the template requires.

## Unmapped Tasks

None. T001–T003 are foundation for US1 and US2; T014 and T015 are documentation
and status, both traceable to the level-2 record.

## Verification Gaps

FR-006 and SC-005 (C2) are the only requirements with no verification path at
all. FR-003 and FR-009 have weak ones (C1, U1).

## Metrics

- Total requirements: 14 (9 FR, 5 SC)
- Total tasks: 15
- Coverage: 12 of 14 have ≥1 task — **86%**
- Ambiguity count: 1 (LOW)
- Duplication count: 0 defects (1 intentional)
- Critical issues: **0**

## Next Actions

1. Amend FR-005 per I1 — one sentence, names the two template sources apart.
2. Strengthen T006 and T009 per C1 — assert `in_progress`, not merely not-`done`.
3. Add the FR-006/SC-005 task per C2.
4. Decide U1: pin the flags in a test, or move FR-009 to the PR body.

Nothing here blocks implementation. All four are cheap and all four are cheaper
before the code exists than after.

## Disposition — 2026-09-09

All four applied in the same session that found them, before any code was
written.

| ID | Applied |
| --- | --- |
| I1 | FR-005 rewritten to name the two template sources apart, since only the specification template declares a mandatory set. T012 unchanged — the task was right. |
| C1 | T006 and T009 now assert `in_progress` exactly. `pending` also satisfies "not `done`", so the weaker assertion left FR-003 unproved. |
| C2 | T016 added: inference against a repo root with no `.specify/` reachable returns identical states. FR-006 and SC-005 now have a verification path. |
| U1 | T017 added, pinning the eight `_STEPS` entries. Chosen over moving FR-009 to the PR body — a requirement nothing checks is the shape `a-rule-is-expressed-as-a-check` warns about, and the table is cheap to pin. |

Coverage after: 14 of 14 requirements carry ≥1 task — **100%**. Two weak
verification paths (FR-003, FR-009) are now automated. Critical issues: 0,
unchanged.
