# Clarify scan — #371

## Session 2026-09-15

- Verdict: satisfied
- Scanned: spec.md
- Asked: 3 · Answered: 3 · Outstanding: 0 · Deferred: 1
- Detail: /Users/andremarin/Development/wfctl-specs/371-write-state-before-clear/spec.md § Clarifications

Run unattended at the user's request ("run it unattended"). Every answer below is
the recommendation the question was rendered with; nobody picked it.

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Deferred |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Functional Scope & Behavior** — FR-003 said "a stop recorded after the send" without saying whether a wrapped-up stop, typed by hand in a held session, counts the same as the continued stop the restart turn asks for.
  Q: Which recorded stop counts as the handoff having landed? → A: Any stop, continued or not.
  Basis: brainstorm ledger entry 18 states the fix for state D as "clear only when events.jsonl carries an `end` newer than the over-threshold Stop", and `wfctl-performs-the-session-restart` repeats it as "an `end` event newer than the `/end-session` send". The lie D prevents is quoting an *older* handoff, and a wrapped-up stop is newer than every earlier one.
  Decided against **B — only a continued stop**: a person who ends a held session by hand would leave it held forever, over the threshold, with the hold message already spent.
  Decided against **C — any stop, but a wrapped-up one clears without `/start-session`**: it splits the restart into two sequences to protect a distinction `start-session` does not need on an issue branch, where both stop kinds take row 1.
- **Edge Cases & Failure Handling** — the spec covered a failed `/clear` send (FR-009) but not a failed `/end-session restart` send, which would otherwise leave the restart held with a message blaming the model turn that never ran.
  Q: What happens when the `/end-session restart` send itself fails? → A: Report once that it was never sent; do not resend.
  Basis: ledger entry 26 rejects retrying `/clear` because a retry types into a pane a person may be using, and that reason applies to any send; FR-009 already distinguishes "never sent" from "sent and did not take" for `/clear`.
  Decided against **B — resend on the next reply end over the threshold**: the retry entry 26 rejects, and a pane workmux could not reach once is likely unreachable again.
  Decided against **C — fall through to hold**: its message says the handoff turn recorded no stop, which blames a turn that never happened.
- **Edge Cases & Failure Handling** — the sender runs seconds after the hook exits, so a reply end from the same session can arrive after the decision event and before the send event; nothing said what that reply end decides.
  Q: What does a reply end decide while a planned send has not yet been recorded? → A: Nothing, and it shows nothing.
  Basis: `design/371-the-session-restart-sends-from-a-detached-worker` makes the send event the only evidence of what a send did; deciding before it exists would report on a guess.
  Decided against **B — report "never sent"**: false in the common case, where the sender is about to run.
  Decided against **C — decide again from occupancy as if nothing were planned**: could plan a second `/end-session restart` beside the pending one, which FR-004 forbids.

### Deferred

- **Integration & External Dependencies** — whether a Stop hook's message renders in the Claude pane, whether a detached send lands, and whether trailing text reaches the skill are platform behaviors no question can settle; they are listed as assumptions in `spec.md` and belong to the plan's probes and the live checks in its Validation Strategy.
