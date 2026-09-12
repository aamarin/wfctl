# Specification Analysis Report: flip clarify and analyze

**Feature**: 325-flip-clarify-and-analyze
**Date**: 2026-09-10
**Artifacts**: spec.md, plan.md, tasks.md — all three present and read

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| F1 | Inconsistency | HIGH | tasks.md T006, T014 | Both claimed FR-006 and FR-007. T006 said "a review task with no diff of its own"; T014 said "state each as an assertion … rather than as a comment". Two tasks, one requirement pair, contradictory methods | Fixed — T006 became one property assertion over the whole table; T014 keeps only FR-009 |
| E1 | Coverage gap | MEDIUM | spec.md SC-001, SC-002, SC-003; tasks.md | Three of five success criteria had no traceable task. SC-003 was substantively covered by T004/T005 but named nowhere | Fixed — T006a covers SC-001, T006b records why SC-002 cannot be covered here, Phase 1 verification names SC-003 |
| E2 | Coverage gap | MEDIUM | spec.md Edge Cases; tasks.md | Three of four edge cases had no task | Fixed — T010a asserts two; the third is subsumed by T006's whole-table property |
| C1 | Underspecification | MEDIUM | tasks.md T014 | "Assert FR-007 (the flip is unconditional — no branch reads a fact, a grant, or branch state)" named no assertable shape. A negative over unwritten code is not a test | Fixed — T006's property holds with no argument but the step's own name, so any such branch breaks it |
| F2 | Inconsistency | MEDIUM | tasks.md Phase 1, Dependencies | Numeric order put T003 after T001/T002; Dependencies said "write it first if that ordering is easier". A reader could not tell which was the instruction | Fixed — numeric order is execution order, and the failing-first demonstration is stated as a check rather than a reordering |
| F3 | Inconsistency | MEDIUM | spec.md, plan.md, tasks.md, design.md | Four names for one thing: continuation value, continuation flag, unattended flag, `auto` | Fixed — Key Entities declares the three legitimate names and which surface each belongs to; "continuation flag" normalised out of prose |
| A1 | Duplication | LOW | spec.md FR-006, FR-007 | Both prohibit a branch, and overlap enough that a reader may take them for one requirement | Accepted, not fixed — see below |

## Accepted without change

**A1.** FR-006 and FR-007 overlap and are not duplicates. FR-006 constrains
*where* `auto` is computed — one site, no per-step arm. FR-007 constrains *what
it may depend on* — nothing, because the flip is a property of the step. A branch
could satisfy either while violating the other: a single-site computation that
reads one of the payload's four facts satisfies FR-006 and breaks FR-007; a
per-step arm returning an unconditional `True` does the reverse. Merging them
would lose whichever half the merged wording dropped.

Both are now carried by one assertion, which is the right economy — one test, two
requirements, because the property really is one property. That is not a reason
to make them one requirement.

## Coverage Summary

| Requirement | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 | yes | T001 | test_pipeline_sections | |
| FR-002 | yes | T002 | test_pipeline_sections | |
| FR-003 | yes | T004 | test_pipeline_commands | two states, one test |
| FR-004 | yes | T005 | test_pipeline_commands | |
| FR-005 | yes | T007, T006 | existing blocked-step test, plus T006's property | |
| FR-006 | yes | T006 | test_pipeline_commands | prohibition, asserted over the whole table |
| FR-007 | yes | T006 | test_pipeline_commands | prohibition, same assertion |
| FR-008 | yes | T003 | test_pipeline_sections | |
| FR-009 | yes | T003, T014 | the eight-row dict | |
| SC-001 | yes | T006a | test_pipeline_sections | count is zero, not "two fewer" |
| SC-002 | no | T006b | none possible here | blocked on #331; recorded rather than claimed |
| SC-003 | yes | T004, T005 | test_pipeline_commands | three reachable states, each asserted once |
| SC-004 | yes | T013 | manual file check | |
| SC-005 | yes | T011 | snapshot unchanged | |

**Constitution Alignment Issues:** none. The repository ships no constitution;
plan.md substitutes gates from its own accepted records and `AGENTS.md`, and
records the substitution in Complexity Tracking as the template requires.

**Unmapped Tasks:** T009 and T010 belong to US3, which describes behaviour that
already shipped (#307/#320) and carries no functional requirement of its own.
That is correct rather than a gap — US3 is stated so the evidence this feature's
claim rests on is named, and its tasks verify the scan files exist rather than
implement anything.

**Verification Gaps:** one, stated rather than closed. SC-002 — an unattended
run executing both steps with no prompt — cannot be asserted by this suite. It
needs a real `/speckit.orchestrate` run, which is blocked on #331.

**Terminology note:** one instance of "continuation flag" remains, in spec.md's
Clarifications section, inside the verbatim text of a question that was asked.
Editing it would falsify a record of what was asked and answered. Left standing
deliberately.

## Metrics

- Total requirements: 14 (9 functional, 5 success criteria)
- Total tasks: 17
- Coverage: 13/14 traceable to a task = 93%; 11/14 = 79% before remediation
- Ambiguity count: 1 (C1, fixed)
- Duplication count: 1 (A1, accepted)
- Critical issues: 0
