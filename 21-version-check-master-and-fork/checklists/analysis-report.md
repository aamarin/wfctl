# Specification Analysis Report

**Feature**: version check — default branch and fork
**Analyzed**: 2026-08-17
**Artifacts**: spec.md, plan.md, tasks.md, data-model.md, contracts/, research.md, quickstart.md

**Status**: all 14 findings remediated on 2026-08-17, after the report was
written. The findings below are kept as the record of what was wrong; the
Remediation Log at the end states what each fix was.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| I1 | Inconsistency | HIGH | tasks.md T017-T018, T020 | T017 changes the warning string that `test_install_skills.py:638` asserts on; T018's gate runs the full `pytest` and would fail. The fix (T020) sits in Phase 6, two phases later, so Phase 5's merge gate cannot pass as ordered. | Move T020 into Phase 5, before T018. |
| I2 | Inconsistency | HIGH | spec.md:78-79 | US3's Independent Test says the offline report must be "identical to today's offline output". FR-009a deliberately changes that text — that is why T020 exists. The acceptance criterion contradicts the requirement it tests. | Reword to "one warning line naming what could not run, exit 0". |
| I3 | Inconsistency | HIGH | tasks.md T006 vs T020a | T006 changes the `ls-remote` invocation in Phase 2, but `_fake_ls_remote_tags` — which feeds the two existing unit tests — is not updated until T020a in Phase 6. Between them, those tests pass through the FR-009a warning path rather than the path they were written for: green for the wrong reason. | Move the `_fake_ls_remote_tags` update from T020a into T006, leaving T020a as a pure file move. |
| C1 | Coverage | MEDIUM | spec.md FR-012; US1-US3 | FR-012 (remedy commands name the recorded origin) has no acceptance scenario in any user story. US2's Verification mentions the reinstall line only; FR-012 also governs the pre-existing upgrade line. Tasks T014a/T014b cover it, so this is a spec gap, not an implementation gap. | Add an acceptance scenario to US2 covering the upgrade line's URL. |
| C2 | Coverage | MEDIUM | tasks.md T021; spec.md | T021 (`int`→`bool` return contract) traces to issue #41, not to any FR or SC. It is the one task with no requirement behind it in this feature's own spec. | Add an FR for the exit-code contract so it is traceable and verifiable, or record explicitly that it is inherited scope. |
| I4 | Inconsistency | MEDIUM | spec.md SC-003 vs data-model.md E1 | SC-003 enumerates "pinned, editable, package-index, and absent metadata" as four shapes, but package-index and absent-metadata are the same rule (E1 R-1), and malformed JSON (E1 R-4) is missing. T012 tests E1's four rules correctly, so SC-003's enumeration is the drifted one. | Restate SC-003 as E1's four rules: no metadata file, no `vcs_info`, pinned, malformed. |
| I5 | Inconsistency | MEDIUM | plan.md "Cross-Issue Scope" | The section still reads "Open question, not resolved here… needs a decision before US2", and the #35 B1 row points at FR-009 "but see the open question below". Clarifications Q3 resolved this and added FR-012. | Update the row to cite FR-012 and delete the open-question paragraph. |
| I6 | Inconsistency | MEDIUM | tasks.md "Parallel Opportunities" | The list omits T014a and T020a (both `[P]`) and still names T020, which is no longer `[P]`. | Regenerate the list from the actual markers. |
| U1 | Underspecification | MEDIUM | contracts/doctor-tool-freshness.md:23 | The upgrade-line example hardcodes the upstream URL and the notes only state that the *reinstall* URL follows the recorded origin. FR-012 governs both lines. | Note that the upgrade URL follows the recorded origin too. |
| I7 | Inconsistency | LOW | tasks.md T012-T015 | IDs run T012, T013, T014a, T014b, T014, T015 — T014 executes after T014b, so IDs are not in execution order. | Renumber, or reorder so T014 precedes T014a/T014b. |
| I8 | Inconsistency | LOW | spec.md:118-119 | FR-012 is placed between FR-009a and FR-010, out of numeric order. | Move FR-012 after FR-011. |
| A1 | Ambiguity | LOW | spec.md:71 | US3's opening still says "The comparison needs one network round trip"; FR-009 now permits two. | Say "one round trip, or two for a fork install". |
| U2 | Underspecification | LOW | spec.md FR-008 | The no-commit-count requirement has no dedicated test; it is covered only implicitly by T008's assertion on exact line shapes. | Acceptable as-is, or add an explicit negative assertion. |
| C3 | Coverage | LOW | spec.md SC-006 | Only half of SC-006 is verifiable: this session's incident is reproducible (T001, T023), PR #20's is historical and cannot be re-run. | Restate as the reproducible half, or mark the historical half as evidence rather than a test. |
| U3 | Underspecification | LOW | spec.md FR-011 | The enumerated minimum test set omits fork targeting and the FR-012 remedy URL, both of which do have tasks. | Add them to the list. |

## Coverage Summary

| Requirement | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 branch comparison | Yes | T006, T009 | Yes | |
| FR-002 local metadata read | Yes | T004 | Yes | |
| FR-003 branch resolved not assumed | Yes | T005, T006 | Yes | |
| FR-004 skip rules | Yes | T004, T012 | Yes | |
| FR-005 remedy verified to re-resolve | Yes | T009, T022 | Yes | T022 is the live gate |
| FR-006 drift exits non-zero | Yes | T009 | Yes | |
| FR-007 tag suppresses drift line | Yes | T010 | Yes | |
| FR-008 no commit count | Yes | T008 | Weak | implicit only — U2 |
| FR-009 query targeting | Yes | T013, T014 | Yes | |
| FR-009a one warning line | Yes | T016, T017 | Yes | ordering defect I1 |
| FR-010 documentation | Yes | T019 | Yes | |
| FR-011 offline test coverage | Yes | T002-T016 | Yes | list incomplete — U3 |
| FR-012 remedy URLs | Yes | T014a, T014b | Yes | no acceptance scenario — C1 |
| SC-001 stale build identifiable | Yes | T008, T009 | Yes | |
| SC-002 one action, drift clears | Yes | T022 | Yes | |
| SC-003 non-drifting shapes silent | Yes | T012 | Yes | enumeration drift — I4 |
| SC-004 fork reaches clean report | Yes | T013, T014 | Yes | |
| SC-005 round-trip count | Yes | T013 | Yes | |
| SC-006 historical incidents | Partial | T001, T023 | Partial | half unverifiable — C3 |

## Constitution Alignment

No `.specify/memory/constitution.md` exists. plan.md substitutes gates from the
repository's own conventions and records the substitution in Complexity
Tracking, as the template requires. All six substituted gates pass. No
violations.

## Unmapped Tasks

- **T021** — traces to issue #41, not to any FR/SC in this spec. See C2.

## Verification Gaps

- Every user story has an `Independent Test` and a `Verification` block.
- Every implementation task carries a `verify with` clause or an adjacent verification task.
- One acceptance criterion (US3's Independent Test) is **wrong** rather than missing — see I2.

## Remediation Log

| ID | Fix applied |
| --- | --- |
| I1 | The `test_install_skills.py:638` fix moved from Phase 6 into Phase 5 as T020, ahead of the phase gate. A new rule in "Within Each Story" makes this general: a task that invalidates an existing assertion fixes it in the same phase, before that phase's gate. |
| I2 | US3's Independent Test rewritten to assert one warning line naming what could not run, and to state outright that the text differs from today's — the opposite of what it previously claimed. |
| I3 | The `_fake_ls_remote_tags` update folded into T006, alongside the change that invalidates it. T023 is now a pure file move. T006's verification explicitly requires the two affected tests to assert a verdict rather than a warning. |
| C1 | US2 acceptance scenario 5 added, covering every printed remedy — upgrade line included. |
| C2 | FR-013 added for the exit-code contract, recording it as scope inherited from #41 so it is traceable. T024 and plan.md now cite it. |
| I4 | SC-003 restated as `data-model.md` E1's four actual rules: no metadata file, no source-control origin, deliberate pin, unreadable metadata. |
| I5 | plan.md's open-question paragraph replaced with "How B1 was resolved", recording the reasoning and pointing at FR-012. The table row cites FR-009 + FR-012. |
| I6 | Parallel Opportunities regenerated from the actual markers (T003, T005, T008, T012, T013, T014, T018, T022, T023) and labelled as exhaustive. |
| U1 | contracts/ now states that *every* remedy URL follows the recorded origin, with the upstream constant as fallback, and warns against conflating remedy URLs with tag sources. |
| I7 | Tasks renumbered T001-T026, strictly sequential in execution order; the T014a/T014b interleave is gone. |
| I8 | FR-012 moved after FR-011; FR-013 appended. |
| A1 | US3's opening now reads "one network round trip, or two for a fork install". |
| U2 | T008 gains an explicit negative assertion for FR-008 — no commit-count phrasing in the drift block. |
| C3 | SC-006 restated around the reproducible incident, with PR #20's recorded as history in issue #21 rather than as a test. |

Two consistency checks were run after the edits: task IDs are contiguous
T001-T026 in file order, and FR-001 through FR-013 appear in numeric order. A
stale `T021` reference in plan.md was found and corrected to `FR-013, T024`.

## Metrics

Before remediation:

- Total requirements: 19 (13 FR, 6 SC)
- Total tasks: 26
- Requirement coverage: 13/13 FR (100%), 6/6 SC (one partial)
- Ambiguity findings: 1
- Duplication findings: 0
- Critical issues: 0
- High issues: 3

After remediation:

- Total requirements: 20 (14 FR incl. FR-013, 6 SC)
- Total tasks: 26, contiguous T001-T026
- Requirement coverage: 14/14 FR (100%), 6/6 SC (SC-006 now fully verifiable)
- Open findings: 0
