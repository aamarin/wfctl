# Clarify scan for #725

## Session 2026-11-05

- Verdict: satisfied
- Scanned: spec.md
- Asked: 1 · Answered: 1 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/725-sign-off-round-window/spec.md § Clarifications

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

- **Interaction & UX Flow** — the spec said the header reports the count in the window, but not whether it says why the count dropped after a sign-off.
  Q: After a sign-off, how do `review start`'s header and refusal describe the count? → A: They say the count is since the sign-off and name its short commit, such as "round 1 of 3 since the sign-off at abc1234". With no sign-off, the wording is unchanged.
  Basis: the user asked for the run to go to completion without pauses, so the recommended option was taken. The count dropping from 3 to 0 needs a reason on screen, and the sign-off is that reason.
  Decided against **B, only "round N of cap"**: a branch that read "round 3 of 3" and then "round 1 of 3" looks like the count was lost.
  Decided against **C, the branch total and the window together**: the total isn't what the cap is checked against, so it adds a number the reader has to work out how to ignore.

The other nine categories were read and found Clear. The level-2 and level-3 records settle the data model, the old sign-off file, renames, and the cap's source. The edge cases list covers stacked sign-offs, a cap of 0, and a sign-off with nothing unreviewed.
