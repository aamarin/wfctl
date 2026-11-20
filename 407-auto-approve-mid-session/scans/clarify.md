# Clarify scan — 407-auto-approve-mid-session

## Session 2026-11-19

- Verdict: satisfied
- Scanned: spec.md
- Asked: 1 · Answered: 1 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/407-auto-approve-mid-session/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Resolved |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Clear |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Interaction & UX Flow** — The spec had `wfctl doctor` warn on every run when
  `post_create` has no grant line. The line is opt-in, so a repository that
  never uses auto-approve would see the warning forever.
  Q: Who sees the reminder that `.workmux.yaml` has no grant line? → A: Only
  someone who runs `wfctl auto-approve` with no argument, as an `ℹ` note under
  the mode. `doctor` doesn't report it.
  Basis: the user gave this answer in place of the lettered options, after
  asking for a `doctor` subcommand and agreeing the note fits better under the
  command people already run to check the mode.
  Decided against **A** (warn on every `doctor` run, no way to turn it off): it
  nags every repository that chose not to use auto-approve.
  Decided against **B** (a one-time `ℹ` notice from `doctor`): wfctl would have
  to remember it was shown, and a repository that missed the one run never sees
  it again.
  Decided against **C** (warn until a comment opts out): every repository that
  doesn't want the mode has to edit its config to silence a warning.
  Decided against **D** (no reminder, documentation only): a repository seeded
  earlier has no way to find out the line exists unless someone reads the docs.

The other nine categories were read and found Clear. The issue's `envvar`
proposal is recorded as rejected under Assumptions, with the argument in the
accepted record, and the threat model's catch and let-through cases map to
acceptance scenarios and SC-002.

### Outstanding

None.

### Deferred

None.
