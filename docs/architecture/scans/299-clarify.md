# Clarification scan — #299

## Session 2026-09-10

- Verdict: satisfied
- Scanned: spec.md
- Asked: 3 · Answered: 3 · Outstanding: 0 · Deferred: 1
- Detail: `<spec-root>/299-four-facts-in-the-payload/spec.md` § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Resolved |
| Interaction & UX Flow | Resolved |
| Non-Functional Quality Attributes | Deferred |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Clear |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Resolved |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Domain & Data Model** — the spec described a fact's three values in prose
  ("met, unmet, or does not arise") and named no wire vocabulary, while FR-007
  requires a consumer to key on them. Two implementers would have picked
  differently, and one of the available sets already means something else in this
  codebase.
  Q: What three values does a fact carry, in the payload a consumer reads? →
  A: `met`, `unmet`, `n/a`.
  Decided against **`yes` / `no` / `n/a`**: equally sound, and it loses on fit
  only — `unmet` names something a reader must act on, where `no` names the
  absence of an answer and reads as the negative half of a boolean.
  Decided against **reusing `satisfied` / `unsatisfied` / `inconclusive`**: that
  is `_predicates.Verdict`, whose `inconclusive` means the evidence could not be
  read. This feature's third value means the question was never asked. One
  vocabulary over both would make `blocks(verdict, source)` look applicable to a
  question it does not answer, which FR-014 exists to prevent.
  Decided against **a boolean with a nullable reason**: a bool carries two of the
  three states, and the third would have to be inferred from the reason string.
  #280's own FR-004 spent this argument already — `notify` is present and false
  rather than absent, because a consumer cannot tell a missing key from a
  refusal.

- **Interaction & UX Flow** — the spec required the console to render all four
  facts (FR-006) and did not say where, or whether the block appears when nothing
  is unmet. The design record settles the block's existence, not its position.
  Q: Where in `wfctl status` does the block render, and in which states? →
  A: Between the step table and the `next:` line, in every state.
  Decided against **rendering only when a fact is unmet**: quieter, and it makes
  the block's absence carry meaning — which a reader cannot tell from a wfctl too
  old to know the question. Same argument as the first finding, met from the
  console side.
  Decided against **above the step table**: three of the four facts are about the
  branch and one is about the steps, but the step table is what the reader opened
  `status` for, and putting a summary above it displaces the thing being
  summarised.
  Decided against **after `next:` and its remedy**: `next:` is the action and is
  last by design. A reader who has reached the next command has stopped reading.

- **Terminology & Consistency** — `_predicates.py` documents seven "rungs" and
  this feature introduces four "facts". A reader of both would ask whether they
  are the same thing, and the answer is not obvious from either.
  Q: Are the four facts the same thing as the seven rungs? →
  A: No. Separate vocabularies; the rung commentary stays as it is, with one
  cross-reference added where it names rungs 6 and 7.
  Decided against **stating a mapping between them**: it holds for two rows and
  not the other five. Rungs 1 through 5 all grade evidence that one step's
  artifacts were written, which is a single fact here; only rungs 6 and 7 line up
  one-to-one with facts 3 and 4. A mapping asserted for all seven would be wrong
  about most of it.
  Decided against **renaming the rungs to facts**: the rung comment accurately
  describes what each predicate proves about its own step, which is a per-step
  question the facts do not replace. Renaming would lose that reading to gain a
  consistency the two vocabularies do not have.

### Deferred

- **Non-Functional Quality Attributes** — whether resolving the architecture root
  and asking git for this branch's records on every `wfctl status` is fast enough
  to leave unconditional. It needs a measurement against a real repository, which
  belongs to implementation rather than to the spec. Carried as an assumption in
  `docs/architecture/design/299-facts-render-as-a-block.md`, where what would
  falsify it is written down.
