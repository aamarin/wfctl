# Clarify scan: #622

## Session 2026-10-22

- Verdict: satisfied
- Scanned: spec.md
- Asked: 2 · Answered: 2 · Outstanding: 0 · Deferred: 2
- Detail: /Users/andremarin/Development/wfctl-specs/622-security-review-panel/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Resolved |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Functional Scope & Behavior**: Each group keeps its own last reviewed
  commit, and the spec didn't say whether every group has to cover the newest
  commit before a pull request opens. When the code group's fixes add commits,
  the security group might never see them.
  Q: Does the security group have to review the code group's fix commits
  before the pull request opens? → A: Yes. Every group, custom groups
  included, has to review the newest commit, and three rounds of that is the
  cap before a person signs off.
  Basis: Andre chose option A in chat.
  Decided against **B**, where only the last group to run covers the newest
  commit: the security group would never review the code group's fixes, and a
  fix for a code finding can bring in a vulnerability.
  Decided against **C**, where only the code group gates the pull request:
  security findings would become advice, which undoes the reason the security
  group exists.
- **Edge Cases & Failure Handling**: The review check read the reviews of the
  branch the agent stands on. When the agent merges another branch's pull
  request from a worktree, such as `gh pr merge 630`, the check judged the
  wrong branch and could let an unreviewed pull request merge.
  Q: Whose reviews does the review check read for a command that names
  another pull request? → A: That pull request's own branch, looked up from
  GitHub. The check refuses when the lookup fails.
  Basis: Andre accepted the recommendation in chat.
  Decided against **B**, always judging the current branch: it gives the
  wrong answer for every other pull request.
  Decided against **C**, checking only `gh pr create` and leaving merges
  unchecked: a pull request could still merge after unreviewed commits were
  pushed to it.
- **Terminology & Consistency**: User Story 2 defined a round as one review
  of the new commits, while the Assumptions section defined it as one
  complete run of every group. User Story 2 now uses the Assumptions
  definition.
  Basis: the spec's own Assumptions section, and the first answer above.
  No options offered — short answer.

### Deferred

- **Functional Scope & Behavior**: How wfctl counts rounds, whether the
  three-round cap is configurable, and how a sign-off is recorded. #626 owns
  these, and the spec already says so in its Assumptions.
- **Constraints & Tradeoffs**: Whether a consuming repository can turn the
  review check off. Not asked because wfctl has one user today, and the
  required CI check in #627 is the change that brings review gating to other
  repositories on purpose.
