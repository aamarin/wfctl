# Specification Analysis Report: Sweep the one-time migration checks

**Date**: 2026-08-17
**Artifacts**: spec.md, plan.md, tasks.md (+ research.md, data-model.md, contracts/cli.md, quickstart.md)
**Mode**: read-only cross-artifact consistency analysis
**Status**: all 8 findings remediated in `tasks.md` on 2026-08-17 (see Remediation Log)

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| C1 | Underspecification | MEDIUM | spec.md FR-006; tasks.md T022 | FR-006 ("MUST continue to rescue every file") is a regression-protection requirement whose only direct task is a diff read. Its real coverage is the pre-existing `test_archive_specs.py` legacy cases, which no task names. | Add an explicit task in Phase 4 asserting the existing legacy-rescue tests still pass unmodified, or name them in T022. |
| E1 | Coverage Gap | MEDIUM | spec.md Edge Cases (durable spec dir + rescue); tasks.md Phase 4 | The edge case "worktree whose spec directory lives outside it — durable-spec-dir notice and rescue line are independent and may both appear" has no test task. T016 covers rescue + rename, not rescue + durable. | Extend T016, or add a sibling task, covering the durable-spec-dir and rescue notices co-occurring. |
| E2 | Coverage Gap | MEDIUM | spec.md SC-005; tasks.md T023 | SC-005 is qualitative ("a developer can decide ... without inspecting code"). Its only evidence is the T023 quickstart walkthrough, which is a subjective read rather than a pass/fail check. | Accept as judgment-based, or strengthen T023 to require that the follow-up trigger in `quickstart.md` be restated from the emitted output alone, without opening source. |
| F1 | Inconsistency | MEDIUM | tasks.md Dependencies block | The graph places the arrow into Phase 6 beneath Phase 5's chain only, so Phase 6 reads as depending on Phase 5 alone. T024's full-gate comparison against the T001 baseline actually requires all three story phases complete. | Redraw so Phase 6 depends on the join of Phases 3, 4, and 5. |
| C2 | Underspecification | LOW | tasks.md T011 vs T012 | T011 explicitly requires the notice be emitted inside the existing `try`; T012 omits the same constraint though it carries the same risk under FR-012. | Mirror the constraint into T012 for symmetry. Behavior is already correct — the call site sits inside the `try` — so this is wording, not a defect. |
| F2 | Inconsistency | LOW | tasks.md Implementation Strategy vs phase numbering | Phases are numbered 3 → 4 → 5 (US1, US2, US3) but the recommended execution order is 3 → 5 → 4. A reader following the numbering gets a different order than the stated recommendation. | Keep both — the rationale is sound — but state the deviation at the top of Phase 4 so it is visible where the work happens. |
| F3 | Terminology | LOW | spec.md throughout vs tasks.md throughout | spec.md deliberately uses abstractions ("health check", "archive command", "superseded artifact directory"); tasks.md uses concrete symbols (`wfctl doctor`, `archive-specs`, `.agent/`). | No action. Intentional and documented in `checklists/requirements.md` under "Deliberate deviations". Recorded here so a future reader does not mistake it for drift. |
| E3 | Coverage Gap | LOW | tasks.md T023; quickstart.md | T023 and the quickstart cite `~/Development/pfms/wt/440-editable-table-row`, a path that exists only on this machine. The step becomes unrunnable once that worktree is torn down. | Acceptable given a single-developer install base, but note in T023 that the synthetic `/tmp` construction in `quickstart.md` is the portable fallback. |

## Coverage Summary

| Requirement | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 | Yes | T002, T008 | Automated + orphan grep | |
| FR-002 | Yes | T007, T009 | Automated | Behavior unchanged; T007 is documentation |
| FR-003 | Yes | T003, T008 | Automated + orphan grep | |
| FR-004 | Yes | T009 | Automated | |
| FR-005 | Yes | T004, T005, T006 | Orphan grep | Grep is the gate; ruff will not flag an orphaned function |
| FR-006 | Yes | T016b, T022 | Automated + diff read | Resolved by C1 remediation — the four inherited tests are now named |
| FR-007 | Yes | T012, T015 | Automated | |
| FR-008 | Yes | T015 | Automated | Silent-state coverage |
| FR-009 | Yes | T011, T014 | Automated | Alias invocation implies it still works |
| FR-010 | Yes | T011, T014 | Automated | |
| FR-011 | Yes | T014 | Automated | Silent-state coverage |
| FR-012 | Yes | T016 | Automated | Exit code asserted in the combined case |
| FR-013 | Yes | T018, T019, T020 | Automated + bundle scripts | |
| FR-014 | Yes | T013 | Read against quickstart | Documentation requirement |
| FR-015 | Yes | T005, T006, T008, T009, T014, T015, T016 | Automated | |
| SC-001 | Yes | T008, T009, T010 | Automated + manual | |
| SC-002 | Yes | T019 | Automated | |
| SC-003 | Yes | T015 | Automated | |
| SC-004 | Yes | T015, T016 | Automated | |
| SC-005 | Yes | T013, T023 | Manual, with a stated failure condition | Resolved by E2 remediation — T023 now fails if the trigger cannot be restated from output alone |
| SC-006 | Yes | T016, T022 | Automated + diff read | Reinforced by inherited archive tests |

## Constitution Alignment Issues

No `.specify/memory/constitution.md` exists in this repository. `plan.md`
substitutes gates drawn from `pyproject.toml`'s enforced lint and type settings
and from conventions the codebase applies consistently, and records the
substitution in Complexity Tracking as the template requires. No conflicts.

## Unmapped Tasks

| Task | Reason |
| --- | --- |
| T001 | Setup — establishes the baseline the T024 comparison needs |
| T022, T023, T024 | Polish — cross-cutting validation, map to SC-006 and SC-005 indirectly |
| T025 | Process — records the reclassification on the tracker; maps to no FR by design |

None are orphaned in the problematic sense; all four serve a stated purpose.

## Verification Gaps

None remaining. The three gaps found — FR-006's inherited coverage, SC-005's
subjective evidence, and the untested notice co-occurrence — are closed by T016b,
the strengthened T023, and T016a respectively.

Every user story carries an `Independent Test` and a `Verification` block. Every
implementation task carries a verification path in its text or an adjacent
verification task.

## Remediation Log — 2026-08-17

Applied to `tasks.md`. Task count 25 → 27; no scope change, no new requirements.

| ID | Applied |
| --- | --- |
| C1 | New **T016b** names the four inherited legacy-rescue tests that are FR-006's actual coverage (`tests/test_archive_specs.py:73, 95, 112, 413`) and requires they pass unmodified, with a `git diff` check that additions land only in the ranges T014–T016a touch. FR-006's coverage is now explicit rather than inherited. |
| E1 | Narrower than first reported — the scenario already has a test. New **T016a** extends `test_durable_spec_root_is_not_copied:413` with assertions that the rescue and durable-spec-dir notices co-occur, rather than adding a redundant test. |
| E2 | **T023** now closes by requiring the follow-up trigger be restated from emitted output alone, without opening source, and states the failure condition explicitly: if that cannot be done, SC-005 is not met and the notices need rewording. Converts a subjective read into a pass/fail check. |
| F1 | Dependency graph redrawn — Phase 6 now joins all three story phases, with the reason inline (T024 compares the full suite against the T001 baseline). |
| C2 | **T012** now carries T011's "inside the existing `try`" constraint, citing FR-012. Wording only; the call site was already correct. |
| F2 | Phase 4 gained an **Ordering note** explaining why the recommended execution order runs Phase 5 first, placed where the work happens rather than only in the Implementation Strategy section. |
| F3 | No action — intentional and already documented. Recorded so a future reader does not mistake it for drift. |
| E3 | **T023** now names the `/tmp` construction in `quickstart.md` as the portable fallback for when the live legacy worktree is gone. |

### Correction to the original analysis

E1 was reported as "no test task covers this edge case". The scenario is in fact
already covered by `test_durable_spec_root_is_not_copied`, which constructs a
durable spec root alongside a legacy `.agent/spec.md` and asserts the rescue
still happens. What was missing was assertion of the *notices'* co-occurrence,
not of the behavior. The remediation extends that test rather than duplicating
it.

## Metrics

- Total requirements: 21 (15 FR + 6 SC)
- Total tasks: 27 (25 + T016a, T016b)
- Coverage: 21/21 have ≥1 task (100%); 0 rated Weak after remediation
- Ambiguity count: 0 — no placeholders, no unquantified vague adjectives
- Duplication count: 0 — FR-007/008, FR-010/011 and SC-003/004 are deliberate fire/silent pairs, not duplicates
- Critical issues: 0
- High issues: 0
- Medium issues: 4
- Low issues: 4
