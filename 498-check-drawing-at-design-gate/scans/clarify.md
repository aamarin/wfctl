# Clarify scan: #498

## Session 2026-09-26

- Verdict: satisfied
- Scanned: spec.md
- Asked: 2 · Answered: 2 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/498-check-drawing-at-design-gate/spec.md § Clarifications

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
| Terminology & Consistency | Resolved |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Interaction & UX Flow**: the spec said the one-record check prints the blockers "and the `doctor` warnings", and `doctor` also reports errors about a record that `accept` never refuses on, so what the check prints and when it fails was open.
  Q: Beside the blockers, which of `doctor`'s findings does the check print, and do any of them fail it? → A: none of them; the check is a rehearsal of `accept`, so it prints what `accept` would print and fails only when `accept` would.
  Basis: Andre, in session, choosing `--dry-run` in the question below, whose convention settles this one.
  Decided against **A. print errors and warnings, fail only on a blocker**: it was the recommendation, and it lost because a dry run that prints more than the real command is no longer a rehearsal of it.
  Decided against **B. print warnings only**: the same reason, and it would also show a record's softer findings while hiding its harder ones.
  Decided against **C. print both and fail on an error**: it makes the check stricter than `accept`, so a record could fail the check and still be accepted.
- **Terminology & Consistency**: the flag was named `--check`, and `wfctl arch check` already exists and asks whether a record file is committed, so two unrelated checks would share one name.
  Q: What is the one-record check called? → A: `wfctl arch accept <slug> --dry-run`, with `--agreed` optional and validated when given.
  Basis: Andre, in session: "switch to --dry-run".
  Decided against **B. keep `--check`**: it matches the issue as first written, and it keeps the collision with `arch check`; `--check` is also less universal than `--dry-run` for "show what this would do".
  Decided against **C. a separate `wfctl arch lint <slug>` verb**: it reads clearly as "inspect this record", and it adds a verb for what is a rehearsal of an existing one.

Every other category was read against `design.md` and found Clear, since the level-1, level-2, and level-3 gates were each answered and approved before the spec was written.
