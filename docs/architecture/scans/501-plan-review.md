# Plan review scan for #501

This file records four plan reviews of #501's own spec and plan, run with the
candidate method this change ships, each by one reviewer with a fresh context.
The file format is part of what this change ships (research R10), so it takes
one `## Review` section per run rather than one section per day. None of the
four runs wrote a section at the time. The first three are dated by the commit
that followed each one, so each heading is the latest the run could have
finished; the fourth is dated by its report.

The first two reports were replaced by the runs after them, as FR-014 requires,
so the detail path below holds only the fourth. Each section here carries what
its report found and what happened to it.

## Review 2026-09-27T18:40Z

- Verdict: satisfied
- Scanned: spec.md, plan.md, research.md, data-model.md, quickstart.md, contracts/, design.md, the design records design.md lists, AGENTS.md; no constitution
- Review type: full, since no earlier report existed (FR-025)
- Findings: BLOCKER 0 · MAJOR 5 · MINOR 6
- Detail: /Users/andremarin/Development/wfctl-specs/501-plan-review/plan-review.md

### Coverage

This report did not attribute findings to a lens, so each lens row carries the
run's outcome.

| Check | Status |
| --- | --- |
| Plan identity recorded | Clear |
| Requirements and traceability | Resolved (5 MAJOR fixed across the three lenses) |
| Architecture and boundaries | Resolved |
| Adversarial implementation and verification | Resolved |
| Security and reliability | Deferred (security: no trust boundary is added; the risk lens was applied to the revise mode, the sign-off source, and the plan copy) |

### Findings

- **PR-001, MAJOR.** The wrapper's mode table dropped the `done` and `pending`
  runs the spec requires. → Fixed: only "N BLOCKER findings open" revises, and
  every other reading reviews.
- **PR-002, MAJOR.** The revise mode loaded the method that forbids editing what
  it reviews, and extended a proposed record without amending it. → Fixed: a
  revise run does not load the skill, and the wrapper-split record names the
  revise mode. Decided against a separate `/plan-revise` command, since the
  pipeline names one command per pass.
- **PR-003, MAJOR.** A sign-off was read from the scan file, which the bounded
  agent writes, so a typed line escaped the cap. → Fixed: the reader takes
  sign-offs from `sign-off` events in `events.jsonl`. The cost is that a clone
  on another machine reviews once more, which is an extra review and never a
  skipped one.
- **PR-004, MAJOR.** Flipping `tasks` to `review_required` reversed #325's rule
  that a step's flag does not depend on the grant, without naming it. → Fixed:
  the reversal is named in the plan, research R4, and Complexity Tracking, and
  the test is rewritten rather than updated. Andre accepted the reversal.
- **PR-005, MAJOR.** The plan copy could not be made byte-identical with the
  tools the wrapper was granted. → Fixed: the copy is made with `cp`, hashed
  afterwards, and retried once.
- Six MINOR findings, PR-006 to PR-011, were carried to the next run unworked.

## Review 2026-09-27T18:49Z

- Verdict: satisfied
- Scanned: the same inputs; re-review of the plan at `0f7a589`, eight inputs changed
- Review type: re-review (FR-024)
- Findings: BLOCKER 0 · MAJOR 1 · MINOR 11
- Detail: /Users/andremarin/Development/wfctl-specs/501-plan-review/plan-review.md

### Coverage

This report did not attribute findings to a lens, so each lens row carries the
run's outcome.

| Check | Status |
| --- | --- |
| Plan identity recorded, copy matched | Clear |
| Earlier findings re-graded | Resolved (PR-001, 003, 004, 005 fixed; PR-002 narrowed to MINOR) |
| Requirements and traceability | Resolved |
| Architecture and boundaries | Resolved |
| Adversarial implementation and verification | Resolved |
| Security and reliability | Deferred (no trust boundary is added) |

### Findings

- **PR-012, MAJOR.** While a BLOCKER was open, `/plan-review` always revised, so
  a person who fixed the cause in `spec.md` and ran the command to have the fix
  reviewed got an agent edit to `plan.md` instead. → Fixed after the run, on
  Andre's call: before revising, the wrapper compares the report's recorded
  input identities with the files now, and reviews when one has changed.
  Decided against a `/plan-review review` argument, since it helps only a person
  who remembers to type it and never an unattended run.
- Four slips the run traced to the earlier fixes (the review's hand-back, the
  level-2 record's store sentence, the spec's Sign-off entity, and a copy path
  that needed an ungranted `rm`) were fixed in `452f7e4`.
- PR-013 to PR-016 were new MINOR findings, carried with PR-006 to PR-011.

## Review 2026-09-27T19:22Z

- Verdict: satisfied
- Scanned: the same inputs plus tasks.md; re-review of the plan at `d8a4fb4`
- Review type: re-review (FR-024)
- Findings: BLOCKER 0 · MAJOR 1 · MINOR 10
- Detail: /Users/andremarin/Development/wfctl-specs/501-plan-review/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Plan identity recorded, copy matched | Clear |
| Earlier findings re-graded | Resolved (PR-002, 011, 012, 013, 015, 016 fixed) |
| Requirements and traceability | Resolved (PR-020, PR-021 fixed) |
| Architecture and boundaries | Outstanding (PR-014 narrowed, carried) |
| Adversarial implementation and verification | Resolved (PR-017, PR-018 fixed; PR-019 carried) |
| Security and reliability | Deferred (no trust boundary is added) |

### Findings

- **PR-017, MAJOR.** The input check hashed the plan copy's row, which every
  review overwrites, so the first `/plan-review` after a re-review reviewed
  again instead of revising, and under auto-approve spent the third counted
  review on a repeat. → Fixed: the check skips the copy's row.
- **PR-010, PR-018, PR-020, PR-021, MINOR.** Who commits a sign-off, the input
  rows' spelling left untested, a review with no scope when only `spec.md`
  changed, and four passages stating the old revise rule. → Fixed after
  verifying each against the files. For PR-010, decided against granting
  `wfctl step sign-off` to the wrapper, since the wrapper never signs off.
- **PR-019, MINOR.** A revise run can edit only `plan.md`, and a BLOCKER whose
  fix lies elsewhere loops until the cap. → Carried to implement, since the cap
  bounds it at three reviews.

## Review 2026-09-27T19:36Z

- Verdict: satisfied
- Scanned: the same inputs; re-review of the plan at `ba0a0f0`
- Review type: re-review (FR-024)
- Findings: BLOCKER 0 · MAJOR 0 · MINOR 8
- Detail: /Users/andremarin/Development/wfctl-specs/501-plan-review/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Plan identity recorded, copy matched | Clear |
| Earlier findings re-graded | Resolved (PR-010, 017, 018, 020, 021 fixed) |
| Requirements and traceability | Resolved (PR-022 fixed) |
| Architecture and boundaries | Outstanding (PR-014 carried) |
| Adversarial implementation and verification | Resolved (PR-022, PR-023 fixed) |
| Security and reliability | Deferred (no trust boundary is added; the risk lens was applied to the copy exclusion, the new FR-024 sentence, and the sign-off's commit path) |

### Findings

- **PR-022, MINOR.** FR-024's new sentence skipped `plan.md` but not the plan
  copy, so the method would review the whole plan on every run. → Fixed: one
  section of the report contract now lists the rows a comparison skips, and the
  wrapper, the skill, FR-024, and FR-025 cite it.
- **PR-023, MINOR.** Nothing said whether a report records a row for itself,
  which could never match and would stop revising for good. → Fixed: a report
  records no row for itself. No report had written one.
- **Carried to implement:** PR-006 (a skipped pass hides later declared passes),
  PR-007 (the mode is chosen from a display string no test holds), PR-008
  (`mode` events carry no branch), PR-009 (the revocation reason never reaches
  the payload), PR-014 (the level-2 record omits the other-machine cost), and
  PR-019. Each is a MINOR whose fix lands in code or a test the implement step
  writes, so fixing it in the plan now would only describe that code twice.
- PR-022 and PR-023 were fixed after this run and have not been reviewed.

## Sign-off 2026-09-28T13:59Z

- Signed off: plan.md 08a006bc9f46edcb0eacba14ccedbcd710039c31
- Reason: record renames only (plan-review-boundaries, plan-edit-requires-new-review); no technical decision changed since the last clean review
- Reviewed copy: compared
