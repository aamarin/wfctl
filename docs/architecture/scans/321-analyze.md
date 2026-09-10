# Analyze scans — #321

## Session 2026-09-09

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 5 · Critical: 0 · Acted on: 2 · Accepted: 3
- Detail: /Users/andremarin/Development/wfctl-specs/321-promote-a-decision/checklists/analysis-report.md

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Resolved |
| B · Ambiguity | Clear |
| C · Underspecification | Clear |
| D · Constitution alignment | Clear |
| E · Coverage gaps | Resolved |
| F · Inconsistency | Resolved |
| Requirement-to-task coverage | 82% |

### Findings

- **F · Inconsistency, HIGH** — the command contract gave exit 0 when nothing was
  promotable, while FR-007 requires the request to report as unsuccessful and
  draws no exception for an empty backlog.
  → Fixed: the contract now exits 1 in both no-slug cases, with the empty-backlog
  reason on its own line. Decided against carving an exception into FR-007: a
  caller that asked to accept and accepted nothing reading 0 is green over a
  no-op, which this repository refuses in `doctor`, `verify` and `arch none`.

- **F · Inconsistency, MEDIUM** — User Story 2 scenario 1 requires the
  already-accepted refusal to say *when*; the contract allowed the date to be
  dropped for a record carrying no `accepted` `Log` line, which is seven of this
  repository's ten accepted records.
  → Fixed: the message answers the question instead of dropping it —
  `(no acceptance logged)`. Decided against reading a date from git history: the
  record's `Log` is the durable answer this feature exists to create, and a
  message asserting what the file does not say is the failure in miniature.

- **E · Coverage gaps, LOW** — FR-008, "MUST NOT infer acceptance", is carried by
  no task.
  → Accepted: it is a prohibition on code that does not exist, and no test asserts
  the absence of an inference nobody wrote. The form it actually takes is the
  module boundary — `_arch` importing `_pipeline` would be the violation — so it
  is carried into review as a question rather than added to `tasks.md`, which this
  step does not edit.

- **E · Coverage gaps, LOW** — FR-010, acceptance survives the branch, is carried
  by no task.
  → Accepted, same shape: it is a consequence of the fact being stored in a
  committed file rather than the state dir. A later change that cached acceptance
  in the state dir would violate it silently, which is the review question.

- **A · Duplication, LOW** — the command's output strings exist in both
  `design.md` § Level 1 and `contracts/arch-accept.md`.
  → Accepted: T009 names the contract as the one to follow, so a drift has a
  stated winner. The level-1 copy is the design gate's recorded answer, not a
  second specification, and deleting it would remove the gate's evidence.

### Deferred

- **B · Ambiguity** — whether `--agreed` should be spelled `--agreed-on` or
  `--citation`. Not ambiguous in the artifacts, which say `--agreed` throughout;
  left to review, where a name is cheap to change and expensive to argue about in
  advance.
