# Clarify scan — #501

## Session 2026-09-27

- Verdict: satisfied
- Scanned: spec.md
- Asked: 4 · Answered: 4 · Outstanding: 0 · Deferred: 1
- Detail: /Users/andremarin/Development/wfctl-specs/501-plan-review/spec.md § Clarifications

Attended. Andre answered every question. The first two were settled in the same
session just before `/speckit.clarify` was invoked, and are recorded here because
the first of them is what resolved the spec's one `[NEEDS CLARIFICATION` marker.

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Resolved |
| Interaction & UX Flow | Resolved |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Resolved |
| Terminology & Consistency | Clear |
| Completion Signals | Resolved |
| Misc / Placeholders | Deferred |

### Findings

- **Functional Scope & Behavior** — the spec's one marker asked whether a stale review still moves the current step once the pipeline is past `tasks`.
  Q: Once the pipeline is past `tasks`, should a stale review route back to `/plan-review`? → A: Always route back, and let a harmless edit be signed off with a reason instead of reviewed.
  Basis: Andre chose it in session, after asking whether `tasks.md` existing is a good proxy for the review's moment having passed. It is not: it misses a plan edited and then expanded by a hand-run `/speckit.tasks`, and a `tasks.md` regenerated after a later plan edit.
  Decided against **B — route back only until `tasks.md` exists**: it reads a file's presence as a state, and treats a stale review as harmless in both cases above.
  Decided against **C — route back only until implementation starts**: the same proxy, one step later, with the same two misses.
- **Domain & Data Model** — the review recorded only a hash of the plan it read, which says the plan changed and never what changed.
  Q: Should a re-review start from scratch, or build on the earlier report? → A: Build on it. The review keeps a copy of the plan it read, marks each earlier finding fixed or open, and reviews the changed parts with the parts that refer to them.
  Basis: Andre chose it in session, having first accepted a full review each time and then weighed the risk of a re-review that does not know what changed.
  Decided against **A — a full review from scratch every time**: it cannot say whether an earlier finding was fixed, and a fresh review tends to surface unrelated findings on every lap, which feeds the loop the cap exists for.
- **Edge Cases & Failure Handling** — FR-022 capped reviews per sitting, but an unattended run is restarted automatically when its context fills, which starts a new sitting, and the agent could clear its own cap with a sign-off.
  Q: What clears the review cap? → A: Count reviews and sign-offs since auto-approve was last granted. At 3, auto-approve turns off for the feature, and only granting it again resumes. A session restart changes neither.
  Basis: Andre chose C after asking for its flow drawn out, and added sign-offs to the count once it was shown that an agent signing off every edit never reaches a reviews-only cap. The restart keeps auto-approve on deliberately (`cli.py`, `start_cmd`), since it fires because the context filled and not because a person is needed.
  Decided against **A — count per sitting**: every automatic restart resets it, so the unattended loop gets three more reviews each time.
  Decided against **B — count per feature, cleared by a sign-off**: the agent may sign off, so it could clear its own cap.
- **Constraints & Tradeoffs** — FR-003 always stopped after a review, while the code makes a `review_required` pass automatic under auto-approve, and #501 had placed a hard gate on findings out of scope.
  Q: Under auto-approve, does the pipeline continue to `tasks` after a review with open BLOCKERs? → A: No. The agent revises the plan and the review runs again until no BLOCKER is open, and a run that reaches the cap first stops rather than continuing.
  Basis: Andre, in session: "I want the agent to autonomously try to get through it and if it hits its cap we will want to stop, meaning it couldn't do it." The answer mapped to C and extends it with the agent acting on the findings. It reverses #501's out-of-scope line on a hard gate, and the spec's Assumptions say so. Only BLOCKER holds the pipeline; he said "blockers and such", and MAJOR is left non-blocking because the attestation verdict already keys on BLOCKER alone (FR-016).
  Decided against **A — stop only when auto-approve is off, and otherwise continue**: an unattended run would carry open BLOCKERs through to completion.
  Decided against **B — always stop after a review, even under auto-approve**: an unattended run could never get through plan review on its own.

### Outstanding

None. No question was withdrawn, and the spec has no `[NEEDS CLARIFICATION` markers.

### Deferred

- **Misc / Placeholders** — the names of the sign-off command and of the command that drives a plan revision under auto-approve (FR-023, FR-026). Both are output and command-surface choices with no effect on the behaviour the spec states, and `plan.md` is where command names get settled.
