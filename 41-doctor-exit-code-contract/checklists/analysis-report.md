# Specification Analysis Report: doctor exit-code contract

**Date**: 2026-08-17
**Artifacts**: spec.md, plan.md, tasks.md, research.md, data-model.md, contracts/doctor-exit-code.md, quickstart.md
**Mode**: read-only analysis. Remediation was applied afterwards, on the user's
explicit approval — see Remediation Applied at the end.

## Findings

Severities and IDs below are as first reported. Resolution status is in the
right-hand column; the detail is in Remediation Applied.

| ID | Category | Severity | Location(s) | Summary | Status |
| --- | --- | --- | --- | --- | --- |
| C1 | Coverage Gap | HIGH | spec.md SC-001; tasks.md T012, T014–T016 | SC-001 claims exit-code behaviour is "verified for 100% of checks", but no task tests `_check_legacy_agent_dir` in both states. T014 covers the workmux hook, T015 the spec-root warning, T016 the unmeasurable layer. The `.agent/` check is converted by T012 and never asserted. | **Resolved** — T016a added |
| C2 | Coverage Gap | HIGH | spec.md FR-010; tasks.md T021 | FR-010 states the abandoned-entry report "MUST report only — never delete or move", but T021's test list contains no assertion that reported entries still exist afterwards. A destructive regression would pass every listed test. | **Resolved** — T021 extended |
| C3 | Coverage Gap | MEDIUM | spec.md FR-007; tasks.md T009 | FR-007 requires configurations naming the superseded command to stay recognised as protected — a property of `pre_remove_wired`. T009 preserves `pre_remove_uses_former_name`, a different function, for T003's benefit. FR-007 is covered only incidentally, by whichever existing tests in `test_workmux.py` T009 happens to run. | **Resolved** — T009 widened |
| C4 | Coverage Gap | MEDIUM | spec.md FR-003; tasks.md T016 | FR-003 has two halves: could-not-determine must not change the exit code, **and** must say so in the output rather than appearing to pass. T016 asserts only the exit code. A check that silently returned `False` would satisfy the test and violate the requirement. | **Resolved** — T016 extended |
| F1 | Inconsistency | MEDIUM | plan.md:118; tasks.md Dependencies | plan.md's Implementation Order says "Items 1–3 must land in sequence; 4 and 5 are independent of each other once 3 is in", making item 5 (the step-command test) depend on the contract. tasks.md correctly states US4 depends on nothing — it touches no production code. The two artifacts disagree about whether US4 can start immediately. | **Resolved** — plan.md corrected |
| F2 | Inconsistency | LOW | design.md (throughout); spec.md, plan.md, tasks.md, data-model.md | design.md calls this concept "orphan" / "orphan check"; every downstream artifact calls it "abandoned entry". The rename was deliberate — it followed the clarify answer that directories count too — but design.md was not revisited. | **Accepted** — design.md is a frozen upstream artifact and the drift is one-directional. Noted so a reader of both is not misled into thinking they are two mechanisms. |
| A1 | Ambiguity | LOW | spec.md FR-004; tasks.md T013 | FR-004 requires the convention be "recorded once, where the checks are defined" without naming a location. T013 says "in a comment where the checks are defined". Actionable, but two implementers could reasonably put it in `doctor_cmd`, above the first check, or in a module docstring. | **Accepted** — contracts/doctor-exit-code.md carries the authoritative statement; the in-code comment can point at it. |
| D1 | Duplication | LOW | spec.md FR-002, FR-003 | Both constrain the exit code for the could-not-determine case — FR-002 by "and zero otherwise", FR-003 explicitly. Mild redundancy, not conflict: FR-003 adds the output requirement that FR-002 lacks. | **Accepted** — deliberate emphasis on the rule most likely to be violated by a new check. |

## Coverage Summary

| Requirement | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 | yes | T010, T011, T012, T013 | yes | Three outcomes realised as `bool` + output |
| FR-002 | yes | T013, T014, T015 | yes | Includes the fixed-during-run case |
| FR-003 | yes | T013, T016 | yes | Both halves asserted after C4 |
| FR-004 | yes | T013, T028 | yes | Location unnamed — see A1 |
| FR-005 | yes | T002, T003, T004 | yes | Complete |
| FR-006 | yes | T007, T008 | yes | Complete |
| FR-007 | yes | T009 | yes | `pre_remove_wired` both-names behaviour named explicitly after C3 |
| FR-008 | yes | T019, T020, T021 | yes | Complete |
| FR-008a | yes | T021 | yes | Maps to SC-007 |
| FR-009 | yes | T019, T021 | yes | `.claude/commands/` exclusion asserted |
| FR-010 | yes | T019, T021 | yes | Non-destruction asserted after C2 |
| FR-011 | yes | T024, T025 | yes | Offline, nothing installed |
| FR-012 | yes | T024, T026 | yes | stdlib `difflib` |
| FR-013 | yes | T017 | yes | Explicit grep guard |
| SC-001 | yes | T014, T015, T016, T016a | yes | All four converted checks asserted in both states after C1 |
| SC-002 | yes | T029 | yes | conftest autouse stub |
| SC-003 | yes | T005 | yes | End-to-end probe |
| SC-004 | yes | T024, T026 | yes | Complete |
| SC-005 | yes | T022, T031 | yes | Both reference repositories |
| SC-006 | yes | T029 | yes | Complete |
| SC-007 | yes | T021 | yes | Complete |

## Constitution Alignment

This project has no `.specify/memory/constitution.md`. plan.md substitutes seven
gates from `pyproject.toml` and `.github/workflows/ci.yml` and records the
substitution in Complexity Tracking, as the plan template requires.

**No constitution violations can be reported, because there is no constitution to
violate.** The substituted gates are documented and CI-enforced, so they are a
sound basis — but they are project conventions, not ratified principles, and
nothing in this analysis treats them as non-negotiable.

## Unmapped Tasks

None that are unjustified. T001 (baseline), T006, T018, T023, T027, T030 (phase
merge gates), and T031 (whole-feature check) map to process rather than to a
single requirement, which is their intended role.

## Verification Gaps

None outstanding. Four were found (C1, C2 HIGH; C3, C4 MEDIUM) and all four are
closed — see Remediation Applied.

Every user story has an `Independent Test` and a `Verification` block. Every
implementation task carries a `verify with` clause or an adjacent verification
task.

## Metrics

| | At analysis | After remediation |
| --- | --- | --- |
| Total requirements | 21 (14 FR, 7 SC) | 21 |
| Total tasks | 31 | 32 |
| Coverage (≥1 task) | 100% | 100% |
| Verification completeness | 81% (17/21) | 100% (21/21) |
| Ambiguity count | 1 | 1 (accepted) |
| Duplication count | 1 | 1 (accepted) |
| Critical issues | 0 | 0 |

## Remediation Applied

Approved by the user after the read-only pass. Five edits across two files; no
re-run of `/speckit.specify` or `/speckit.plan` was needed.

| Finding | Edit |
| --- | --- |
| C1 | **tasks.md** — new task T016a: assert `_check_legacy_agent_dir` exits 1 with a `.agent/` directory present and 0 without. Added to the Phase 4 dependency graph. |
| C2 | **tasks.md** — T021 extended: every reported entry must still be on disk after `doctor` returns, with the reason stated (FR-010 is the one requirement whose violation destroys user data). |
| C3 | **tasks.md** — T009 widened: assert `pre_remove_wired` still treats both command names as wired, so deleting the stale-hook check cannot take FR-007's protection with it. |
| C4 | **tasks.md** — T016 extended: assert the could-not-determine case prints why, not only that the exit code is 0. |
| F1 | **plan.md** — Implementation Order corrected: item 4 depends on item 3; item 5 depends on nothing. tasks.md was right and plan.md was wrong. |

**On task numbering**: T016a uses a suffix rather than renumbering T017–T031.
Renumbering would invalidate every task reference in this report and in the
dependency graph, to no benefit. The spec sets the precedent with FR-008a.

**Not remediated, deliberately**: F2, A1, and D1 are accepted as-is with the
reasoning in the findings table. Each is either a frozen upstream artifact
(design.md's older "orphan" vocabulary), already resolved elsewhere (the contract
document carries FR-004's authoritative wording), or deliberate emphasis (FR-002
and FR-003 overlapping on the rule most likely to be got wrong).

## Next Actions

No CRITICAL issues, no outstanding verification gaps. Artifacts are consistent
across all seven documents.

Proceed to `/speckit.decompose`.
