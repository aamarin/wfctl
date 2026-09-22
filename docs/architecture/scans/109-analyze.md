# Analyze scans — #109 record leads with drawing

## Session 2026-09-16

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 6 · Critical: 0 · Acted on: 5 · Accepted: 1
- Detail: `/Users/andremarin/Development/wfctl-specs/109-record-leads-with-drawing/checklists/analysis-report.md`

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Clear |
| C · Underspecification | Clear |
| D · Constitution alignment | Clear (no constitution; plan.md substitutes gates from AGENTS.md and records the substitution) |
| E · Coverage gaps | Resolved (1 MEDIUM, task added) |
| F · Inconsistency | Resolved (1 HIGH, 1 MEDIUM, 2 LOW; all four fixed in spec.md) |
| G · Design-record contradiction | Outstanding (1 HIGH; 1 record read) |
| Requirement-to-task coverage | 100% |

### Findings

- **F · Inconsistency, HIGH** — `spec.md` FR-008 required reporting "a drawing
  label that appears in no other section of the same record". Run over the
  corpus that rule reports **43 findings across 4 records** — every label —
  because authors draw in phrases and prose does not repeat a phrase.
  `plan.md` and `research.md` R-004 carry the narrowed mechanism; `spec.md` did
  not, so the two artifacts specified different checks.
  → Fixed: FR-008 now states the content-word unit and cites R-004. Decided
  against filing it: the narrowing was already decided in `plan.md` and
  `research.md`, so amending `spec.md` makes one artifact say what the others
  say rather than deciding anything.

- **F · Inconsistency, MEDIUM** — `spec.md` SC-004 measured the label check over
  "the 22 records that already carry drawings". Four records carry a
  `## Boundary`; the other 18 draw under `## Context` and `## Decision`, which
  the spec's own Drawing entity excludes.
  → Fixed: SC-004's denominator corrected to the records in range, with the
  split cited to R-006. Decided against widening the check to any fence
  anywhere: clarification Q2 settled that content is never classified, so a
  check that cannot tell a picture from a code sample has to be told where to
  look.

- **F · Inconsistency, LOW** — the "three kinds are enough" assumption named a
  validation — classify the 22 existing drawings — that cannot run for the
  reason above.
  → Fixed: the assumption now says why it stays open. Decided against dropping
  it: an unvalidated assumption recorded as open is a different claim from one
  nobody made.

- **F · Inconsistency, LOW** — `spec.md` said "eleven proposed records that
  carry no drawing" in two places; the corpus now holds 24.
  → Fixed: both sites carry the current count and why it moved. Decided against
  leaving it: a stale count in an Assumptions section reads as a measurement
  rather than as a date.

- **E · Coverage gap, MEDIUM** — FR-013, that the rule binds every repository
  with no per-repository opt-in, had no task. A negative requirement with no
  test naming it breaks invisibly the first time somebody adds an opt-in.
  → Fixed: T039 added, asserting nothing in the checks reads `wfctl.json`, the
  tracker config or the manifest. Decided against filing it: `spec.md` set the
  scope when it stated the requirement, and sending the feature into
  `implement` without it books the omission as separate work.

- **G · Design-record contradiction, HIGH** — T029 reverses part of a proposed
  decision.
  Record: `docs/architecture/design/109-traceability-is-label-agreement.md`
  Decision: "Every label in the `## Boundary` block must appear somewhere in
  `## Owns truth` or `## Decision`; a label that appears nowhere else is the
  finding."
  Task: "T029 [US3] Add VR-007 to `_arch.validate` — a `warning` `Finding` for a
  label none of whose content words appears elsewhere in the record"
  → Accepted: the record is `proposed`, and only a human moves a record past
  `proposed` (`a-human-accepts-a-decision`). Rewriting `tasks.md` to conform
  would ratify the record by acting on it; rewriting the record would do the
  same from the other side. The record's own Verification is what falsified its
  rule — it named the test, Phase 0 ran it, and the counts are in R-004.
  Filed as https://github.com/aamarin/wfctl/issues/401.

### Filing

- **The level-3 record's label rule versus the mechanism the tasks implement** —
  covers finding G1. Filed as
  [#401](https://github.com/aamarin/wfctl/issues/401).

### Deferred

- Nothing. Every pass reached an answer.
