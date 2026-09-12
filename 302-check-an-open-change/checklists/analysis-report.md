# Specification Analysis Report: check an open change

**Date**: 2026-09-09
**Artifacts**: `spec.md`, `plan.md`, `tasks.md`
**Constitution**: none — this repository has no `.specify/memory/constitution.md`.
Gates were substituted from its accepted architecture records and the
substitution is recorded in `plan.md`'s Complexity Tracking, so no constitution
MUST could be violated and no finding below is CRITICAL on that basis.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| C1 | Coverage / Inconsistency | HIGH | tasks.md T003, T004, T005, T011, T012, T016, T025 | Five test files are named as verification paths and none exists: `tests/test_tracker_config.py`, `test_tracker_fields.py`, `test_change_cli.py`, `test_change_degrade.py`, `test_arch_cli.py`. The modules they would cover already have homes — `tests/test_tracker.py` and `tests/test_arch_check.py` | Point tracker tasks at `tests/test_tracker.py` and the #306 CLI task at `tests/test_arch_check.py`. Keep `test_change_check.py`, `test_change_config.py` and `test_arch_considered.py` as new files, since they cover a new module |
| U1 | Underspecification | HIGH | tasks.md T022 vs spec.md FR-015 | FR-015 requires the skill to **invoke** the check as a step. T022 says "document `change_check` in AGENTS.md and in Step 6", which is a weaker action and bundles two unrelated edits | Split T022: one task adding the invocation line to Step 6 with its own manual verification, one task documenting `change_check` in `AGENTS.md` |
| F1 | Format | MEDIUM | tasks.md T007, T008, T015 | All three carry `[P]` and all three write `tests/test_change_check.py`. The format rule reserves `[P]` for tasks touching a file no incomplete task also touches | Drop `[P]` from T007, T008 and T015, or split the file. The prose under Parallel Opportunities already says they collide, which the markers contradict |
| I1 | Inconsistency | MEDIUM | plan.md Source Code tree vs tasks.md | `plan.md` lists three test files; `tasks.md` names eight. A reader working from the plan would not expect five of them | Update the plan's tree once C1 settles which files actually exist |
| T1 | Terminology | MEDIUM | spec.md vs data-model.md, contracts/ | `spec.md` says "field" throughout; `data-model.md` and both contracts say "key"; `tasks.md` uses both interchangeably | Pick one. "Field" reads better for the sidebar and is what `opening-a-change` already says; "key" is accurate for the payload. Using "field" in prose and "key" only when describing the JSON mapping is defensible if stated once |
| A1 | Ambiguity | LOW | tasks.md T002 | "Record the pre-change test count" names no place to record it, and AGENTS.md's own count is a known-stale claim (#247) | Either drop the recording half and keep the green-baseline verification, or name where the number goes |

No duplication findings. No constitution alignment issues (no constitution).

## Coverage Summary

| Requirement | Has task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 report unset expected fields | yes | T009, T011 | yes | |
| FR-002 two expectation sources | yes | T009, T018 | yes | |
| FR-003 silence for unexpected keys | yes | T008 | yes | |
| FR-004 no tracker field name in source | yes | T009, T027 | yes | T027 is the grep that proves SC-004 |
| FR-005 declaration in a committed file | yes | T017 | yes | |
| FR-006 required key tracker never reports | yes | T015, T019 | yes | |
| FR-007 list set difference, extras not findings | yes | T007, T010 | yes | |
| FR-008 scalar empty-versus-set | yes | T010 | yes | |
| FR-009 exit codes | yes | T011, T016 | yes | |
| FR-010 verified vs could-not-check | yes | T012, T020 | yes | |
| FR-011 degrade paths | yes | T016, T020 | yes | |
| FR-012 malformed payload as config finding | yes | T005 | yes | |
| FR-013 config validation | yes | T003 | yes | verification path affected by C1 |
| FR-014 empty Considered, no text judgement | yes | T024, T025 | yes | verification path affected by C1 |
| FR-015 skill invokes the check | partial | T022 | manual | see U1 — the task says document, the requirement says invoke |
| FR-016 15s bound per read | yes | T004 | yes | |
| FR-017 failed read behaviour | yes | T016, T021 | yes | |
| SC-001 empty sidebar produces findings | yes | T029 | manual | live exercise, first half |
| SC-002 filled sidebar produces none | yes | T029 | manual | live exercise, second half — the one that shows the check can pass |
| SC-003 nothing required, nothing inherited | yes | T020 | yes | |
| SC-004 no tracker field name in source | yes | T027 | yes | |
| SC-005 every state terminates without a traceback | yes | T016 | yes | |
| SC-006 empty Considered reported | yes | T023–T026 | yes | |
| SC-007 unreachable tracker returns bounded | yes | T004 | yes | |

## Unmapped Tasks

None. Every task maps to at least one requirement, story, or the declared
definition of done.

## Verification Gaps

Every user story carries an `Independent Test` and a `Verification` block. Every
implementation task names a verification path. The gaps are in the *targets*, not
in their presence: C1's five nonexistent files, and U1's task whose verification
is a manual read of an edit that does not match its requirement.

## Metrics

| | |
| --- | --- |
| Total requirements (FR + SC) | 24 |
| Total tasks | 31 |
| Coverage (requirements with ≥1 task) | 100% — 24 of 24 |
| Ambiguity findings | 1 |
| Duplication findings | 0 |
| Critical issues | 0 |

## Next Actions

No CRITICAL issues, so nothing blocks `/speckit.decompose`.

C1 and U1 are worth settling before implementation begins rather than during it:
C1 sends seven tasks at files that do not exist, and U1 would produce an edit
that documents a check nothing calls — which is the exact failure #302 exists to
correct, reproduced inside its own fix.

F1, I1, T1 and A1 can be fixed in the same pass at no extra cost.

Suggested: edit `tasks.md` directly for C1, U1 and F1; edit `plan.md`'s tree for
I1 once C1 settles.

## Resolution — 2026-09-09

All six applied. `tasks.md` was rewritten and `plan.md`'s tree updated; the
findings above are kept as written rather than edited, so the record shows what
was found rather than what survived.

| ID | Applied |
| --- | --- |
| C1 | `test_tracker_config.py` and `test_tracker_fields.py` folded into the existing `tests/test_tracker.py`; `test_arch_cli.py` into `tests/test_arch_check.py`; `test_change_degrade.py` into `tests/test_change_cli.py`. Four new files remain, each for a genuinely new module or command |
| U1 | T022 split. It now adds the invocation to Step 6 and says explicitly not to rewrite the sidebar sentence; documenting `change_check` in `AGENTS.md` became T023 |
| F1 | `[P]` dropped from every task sharing `test_change_check.py` or `test_change_cli.py`; the Parallel Opportunities section now names the collisions rather than contradicting them |
| I1 | `plan.md`'s tree lists all six test files and says which two are extended rather than created |
| T1 | Convention stated once under Path Conventions — *field* for the sidebar, *key* for the JSON mapping. `spec.md` left untouched |
| A1 | T002 reduced to establishing a green baseline; the unactionable "record the count" half removed |

Task count went from 31 to 32 on the U1 split. Coverage is unchanged at 100%.

## Scope change — 2026-09-09, after decompose

`/speckit.decompose` surfaced a rule this analysis did not check against:
`speckit-delivery-plan` holds that **one PR closes exactly one issue, always**.
The plan at the time of this analysis had one PR closing #302 and #306.

#306 was split to its own branch off `main`. User Story 3 and its four tasks left
`tasks.md`, FR-014 and SC-006 left `spec.md`, and the remaining requirements
renumbered — FR-015/016/017 became FR-014/015/016, and SC-006 was reused for a
new criterion about a single run naming every missing field.

Task count is now 28. Requirement count is 22. Coverage is unchanged at 100%, and
none of the six findings above was affected: C1's test-file consolidation, U1's
T022 split, and the rest all survive in the reduced plan.
