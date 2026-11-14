# Clarify scan: #626 review round cap

## Session 2026-10-25

- Verdict: satisfied
- Scanned: spec.md
- Asked: 3 · Answered: 3 · Outstanding: 0 · Deferred: 1
- Detail: /Users/andremarin/Development/wfctl-specs/626-review-round-cap/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Resolved |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Deferred |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Edge Cases & Failure Handling**: The spec didn't say what `review start`
  does with an invalid `review.rounds` in the branch's own `wfctl.json`, since
  the cap is read from the trunk.
  Q: Should `review start` refuse on an invalid branch value? → A: Yes, like
  any other invalid `review` setting, and `check config` reports it too.
  Basis: the user chose the recommended option. `review start` already refuses
  on any `review` finding (`_review_groups_or_exit` in `wfctl/cli.py`).
  Decided against **Warn and continue**: it treats one `review` key
  differently from the rest, and the agent gains nothing from an invalid value
  that would justify the exception.
  Decided against **Ignore it**: an invalid value would then be reported only
  by `check config`, which an unattended run doesn't run before a review.
- **Functional Scope & Behavior**: design.md set the minimum cap at 1. While
  answering the previous question, the user asked whether 0 is a meaningful
  value, meaning the repository doesn't want review runs.
  Q: Should `review.rounds` accept 0? → A: Yes. No review run starts, and
  every change goes through the user's sign-off. The guard doesn't change.
  Basis: the user chose the recommended option.
  Decided against **1 or more only**: a repository that doesn't want agent
  reviews would have no setting for it, and supporting 0 costs one wording of
  the refusal.
  Decided against **0 turns the gate off**: it would let a PR open with no
  review and no sign-off. That reverses the PR check in
  `review-covers-unreviewed-commits.md` and is outside this issue.
- **Interaction & UX Flow**: The refusal text assumed the count equals the cap.
  After the trunk lowers the cap, a branch can have run more rounds than the
  new cap allows.
  Q: What does `review start` do when the count is above a lowered cap? →
  A: It refuses and names the real count, such as "security has run 4 rounds
  on this branch, more than the 3 review.rounds allows".
  Basis: the user chose the recommended option.
  Decided against **Refuse, show cap**: "3 of 3 rounds" would misstate the
  count when 4 rounds ran.
  Decided against **Keep the old cap**: the cap would then depend on when the
  branch started, which wfctl would have to store, and
  `session-state-is-re-derived.md` rules out storing it.
- **Completion Signals**: FR-013 named only Step 1 of `opening-a-change`, but
  the guard-refusal bullet later in that skill repeats the three-round
  instruction. FR-013 now covers both. No question was needed, since leaving
  the bullet out would leave the skill contradicting itself.

### Deferred

- **Integration & External Dependencies**: design.md assumes the panel skill
  reads the `review start` header as prose. The `_say` docstring in
  `wfctl/cli.py` says the panel skill parses these lines. Whether
  `fanning-out-code-review` depends on the header's exact shape is a plan
  question about the existing skill, not a choice for the user, so the spec
  records it as an assumption for the plan to check.
