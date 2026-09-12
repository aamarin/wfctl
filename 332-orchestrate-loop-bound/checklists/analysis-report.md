# Analysis report: orchestrate loop bound

**Date**: 2026-09-10 · **Issue**: #332
**Read**: spec.md, plan.md, tasks.md, data-model.md, design.md, and the one
level-3 record design.md lists.

## Requirement-to-task coverage

| Requirement | Task |
| --- | --- |
| FR-001 count consecutive passes | T002 |
| FR-002 progress is the artifacts changing | T001 |
| FR-003 stop after three | T002, T008 |
| FR-004 reset on progress | T002, exercised by T010 |
| FR-005 name the step and what did not change | T007, T008 |
| FR-006 hand to a person | T008 |
| FR-007 verdict outlives the output | T005, T007 |
| FR-008 count outlives the agent's memory | T002 |
| FR-009 nothing written solely to remember an attempt | — none |
| FR-010 tolerate older record shapes | T002, T003 |
| FR-011 skip an unreadable record | T002, T003 |

10 of 11 mapped — 91%.

## Findings

**E · Coverage gaps, MEDIUM — FR-009 maps to no task.**
It is a negative constraint: the requirement is that nothing be written. No task
can implement an absence, and a task asserting it would have to assert over the
whole diff rather than over a behaviour.
*Accepted.* It is checkable at review — the diff either adds a write of that kind
or it does not — and the level-2 record states the constraint for the reviewer to
check against. Adding a task to satisfy the coverage metric would raise the
number without adding evidence.

**C · Underspecification, MEDIUM — nothing says whether `wfctl resume` announces
a stall in its own output.**
T007 specifies the rendering for `wfctl status`. `resume` prints its own line and
already echoes a blocked reason, so an implementer has to decide.
*Accepted.* Orchestrate reads the verdict off the payload, never off `resume`'s
stdout, so this is cosmetic rather than behavioural — it changes what a human
watching sees, not what the loop does. Recorded here so the implementer knows it
is an open choice rather than an omission.

**B · Ambiguity, LOW — SC-001 says the run "stops within three passes" while
FR-003 says it stops "after three consecutive passes".**
Read strictly, "within three" could admit stopping on the second.
*Accepted.* The data model settles it without ambiguity: three or more passes
sharing a digest is the stall, so the third pass runs and the run then stops.
Both sentences describe that. Rewriting the spec to remove a tension the data
model already resolves would edit an artifact this step is read-only over.

## Passes finding nothing

- **A · Duplication** — the decision is restated in design.md, the spec, the plan
  and the record, each for a different reader, and the four agree. No conflicting
  duplicate.
- **D · Constitution alignment** — the repo ships no constitution; the plan
  substitutes its accepted records and says so in Complexity Tracking, which is
  what the template instructs.
- **F · Inconsistency** — the digest's inputs, the counting rule and the reset
  condition are stated the same way in the plan, the data model and the record.
- **G · Design-record contradiction** — the one record design.md lists was read.
  Its assumptions (a cosmetic edit masks a stall; one step's evidence sits outside
  the fingerprint) appear in the spec's Assumptions with the same meaning.
