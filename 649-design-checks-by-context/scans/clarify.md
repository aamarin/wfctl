# Clarify scan for #649

## Session 2026-10-26

- Verdict: satisfied
- Scanned: spec.md
- Asked: 3 · Answered: 3 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/649-design-checks-by-context/spec.md § Clarifications

This run was unattended. Each answer is the recommendation the question was rendered with, and its basis is the record or issue it came from.

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Resolved |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Functional Scope & Behavior**: the spec didn't say whether today's general check still applies in a repo with a name list.
  Q: In a repo with a name list, does a branch still have to pass the general check as well as the per-context one? → A: No, the per-context check replaces it (FR-005a).
  Basis: `domain-page-names-contexts.md` keeps the general check for a repo without a name list, and FR-007 pauses a branch that lists no contexts, so every branch in a repo with a list has at least one context that needs an answer.
  Decided against **B, both checks apply**: a branch that answered every context with a per-context "no" would also need a bare `arch none`, which says the same thing a second time.
- **Edge Cases & Failure Handling**: the spec didn't say whether the software design check matches outside parties.
  Q: Does the software design check match outside parties on the `Contexts` line, or only wfctl's own contexts? → A: Every name on the line, at both levels (FR-006).
  Basis: `649-contexts-module.md` runs one match for both checks, which differ only in which records they pass in.
  Decided against **B, level 3 matches only wfctl's own contexts**: the two checks would need different matching rules, which the level-3 record exists to avoid. A branch that changes only how wfctl talks to workmux would also have no level-3 question to answer.
- **Interaction & UX Flow**: the spec didn't say how a per-context "no" is shown.
  Q: How does a per-context "no" show in `wfctl status` and in the PR body? → A: The row reads done only once every listed context is answered, `wfctl status --all` lists each "no" with its context and reason, and the PR body lists them under "Moves a boundary?" (FR-010a, FR-018).
  Basis: #648 shows a claimed pass as `claimed: <reason>` under `--all`, and #635 puts pass exceptions in that PR section so the reviewer reads the reason.
  Decided against **B, a per-context "no" hides the row like a whole-pass claim**: the row would disappear after the first context was answered while others were still open.
  Decided against **C, show nothing beyond the row reading done**: the reviewer would have no way to read why a context needed no record.

### Outstanding

- None.

### Deferred

- None. Three spec choices were made without a question, since a default exists and each is recorded under the spec's Assumptions: the pause wording, `--context` refusing a name not on the list, and `--context` refusing in a repo with no list.
