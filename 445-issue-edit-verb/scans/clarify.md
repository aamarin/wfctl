# Clarify scan: #445

## Session 2026-11-09

- Verdict: satisfied
- Scanned: spec.md
- Asked: 2 · Answered: 2 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/445-issue-edit-verb/spec.md § Clarifications

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

- **Interaction & UX Flow**: wfctl sends one write per field, so the spec left
  open how many notices a two-field edit prints when the tracker has no `edit`
  verb or no tracker is set up.
  Q: How many notices print in that case? → A: One. wfctl checks once before
  any write, prints the notice once, sends nothing, and exits 0.
  Basis: the user chose A after seeing both outputs for a Jira backend.
  Decided against **B** (each field prints its own notice): the command is
  skipped as a whole, so a second identical line reports nothing new and looks
  like a bug.
- **Edge Cases & Failure Handling**: the spec covered a failed body write but
  not a failed title write, where the body is never sent.
  Q: What prints after the backend's error in that case? → A:
  `✗ nothing changed, body was not sent`, with the backend's exit code.
  Basis: the user chose A after seeing both outputs.
  Decided against **B** (the backend's error alone): it leaves the agent unable
  to tell whether the body went through, and it doesn't match the line the
  body-failure case prints.
