# Clarify scan: #532

## Session 2026-09-29

- Verdict: satisfied
- Scanned: spec.md
- Asked: 3 · Answered: 3 · Outstanding: 0 · Deferred: 1
- Detail: /Users/andremarin/Development/wfctl-specs/532-rework-loop/spec.md § Clarifications

The run was unattended under auto-approve. Every question was put as the
workflow renders it, no answer arrived, and each took the recommendation it was
rendered with. The basis on each finding is that recommendation's reasoning.

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

- **Edge Cases & Failure Handling**: the spec did not say what happens to a
  step's own warning when a declared pass under it is outstanding and the
  roll-up holds the step.
  Q: Is the step's own warning listed while a pass holds the step? → A: No; it
  reappears once the pass clears.
  Basis: FR-003 already excludes a held step, and the list is derived on every
  read, so the warning is delayed rather than lost. Keeping the rule to the
  rolled-up state keeps it one line.
  Decided against **A, list it by reading the step's own state**: it makes the
  list read a state no view shows, so `wfctl status` would print a held step and
  a warning about the same step that claims its gate has passed.
  Decided against **C, list it with a note that the step is held**: it adds a
  third kind of entry to a list whose whole contract is "passed, and still
  carries a problem".
- **Interaction & UX Flow**: FR-006 said "after their existing output", and
  `wfctl resume` ends with the auto-approve or revocation notice.
  Q: Where do warning lines go in `wfctl resume`'s console? → A: Directly under
  the resumed line and its reason, before the notice.
  Basis: the resumed line, its reason, and the warnings are all pipeline facts,
  and the mode notice is about the session; keeping the notice last leaves it
  where readers find it today.
  Decided against **B, at the very end**: it separates the warnings from the
  pipeline line they qualify with a notice about something else.
  Decided against **C, above the resumed line**: the first line of `resume` is
  the one readers and tests anchor on, and a warning there displaces it.
- **Functional Scope & Behavior**: the spec's scope did not say whether `wfctl
  end`'s handoff carries warnings, which `design.md` settles under Not Doing.
  Q: Does `wfctl end`'s session handoff carry warnings? → A: No; out of scope.
  Basis: `design.md` Not Doing, since the session summary records the current
  step, and widening it is a separate question about what a handoff records.
  Decided against **B, one line per warning in the summary's observations**:
  it is a reasonable change, and it belongs to its own issue, since it changes
  what every handoff carries.

### Outstanding

None.

### Deferred

- **Integration & External Dependencies**: how the payload contract file is
  regenerated at 1.2, and whether `_contract.py` has a command for it. That is
  mechanism, and it belongs to the plan.
