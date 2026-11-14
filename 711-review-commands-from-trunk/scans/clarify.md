# Clarify scan: #711 review commands from the trunk

## Session 2026-11-03

- Verdict: satisfied
- Scanned: spec.md
- Asked: 2 · Answered: 2 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/711-review-commands-from-trunk/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
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

- **Interaction & UX Flow**: The spec didn't say which models the difference
  warning compares.
  Q: Every model either side's `review.commands` sets, or only the models in
  the group being started? → A: Every model either side sets.
  Basis: nobody answered, so the answer comes from the issue, which asks for a
  warning whenever the branch's copy sets a different command, and from the
  `review.rounds` warning, which prints whichever group starts.
  Decided against **only the group's models**: a branch that adds a command
  ahead of the reviewers that use it would never see a warning.
- **Edge Cases & Failure Handling**: The spec didn't say whether a trunk whose
  commands can't be read also gets a difference warning per model.
  Q: Print the fallback warning alone, or the fallback and a difference
  warning per model? → A: The fallback warning alone.
  Basis: nobody answered, so the answer comes from spec FR-004. Comparing
  against a file wfctl couldn't read would say the trunk sets no command,
  which may be false.
  Decided against **both warnings**: each difference line would claim the
  trunk sets nothing for a model it may well set.
