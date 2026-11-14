# Clarify scans — #412

## Session 2026-09-17

- Verdict: satisfied
- Scanned: spec.md
- Asked: 2 · Answered: 2 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/412-clean-code-skill/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Resolved |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Clear |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Resolved |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Non-Functional Quality Attributes** — the router is loaded on every
  invocation and the references are not, so the router's length is the one cost
  this feature pays unconditionally. The spec bounded the reference side
  (SC-004) and said nothing about the router. `design.md` carries the matching
  assumption — *"eleven references is not itself a cost; falsified if the
  routing table outgrows what an agent reads before choosing"* — with nothing in
  the spec answering it.
  Q: What bounds the cost of the always-loaded router? → A: A stated discipline
  in the router itself — the routing table is the only thing an agent must read
  before choosing, and the rest is reachable after. No line ceiling. Landed as
  FR-013.
  Basis: `a-rule-is-expressed-as-a-check`, accepted — a rule is a check when a
  violation of it is visible in an artifact the work already produces. A
  structural discipline is visible in the router; an unchecked *number* is the
  case that record puts on the wrong side of its own test. The one shipped
  length cap in this tree,
  `test_no_shipped_digest_is_truncated_by_the_hook_that_reads_it`, exists
  because a `UserPromptSubmit` hook silently truncates `digest.md` past 500
  characters. Nothing truncates a `SKILL.md`, so the consumer that makes a
  number meaningful is absent here.
  Decided against **no bound at all**: it is the status quo and leaves
  `design.md`'s assumption unanswered, so the first reference added later has
  nothing to weigh the addition against.
  Decided against **a line ceiling in a test**: checkable, and the right answer
  if something truncated the router — which is exactly why the digest has one.
  Absent that consumer the number would be chosen by taste and then defended by
  a test, which is worse than no bound because it looks settled.

- **Terminology & Consistency** — the spec called what `clean-code` provides a
  *method* in two places, inherited from the issue's title. `design-levels` and
  `architecture-design` already use "method" for `architecture-design`'s
  driver-to-structure loop — its own text reads *"Project instructions and
  accepted architecture records outrank this method"* — and level 3 is the one
  place both skills are reachable.
  Q: What does the shipped text call what `clean-code` provides? → A:
  "Heuristics". "Method" stays `architecture-design`'s word. Landed as FR-014,
  and the two spec occurrences were rewritten.
  Basis: `docs/architecture/level-3-owns-structural-heuristics.md`, this
  feature's own level-2 record — *"A method that ends in a record is a design
  loop... Heuristics that end in nothing are guidance."* The distinction is the
  entire decision, so a word that collapses it undoes the record in the text
  that ships.
  Decided against **"method"**: it is the word `architecture-design` uses for
  itself throughout its own file, so reusing it reopens the collision the record
  closed. The issue's use of it sits in a problem statement describing the gap,
  not in a name for the fix.
  Decided against **"guidance"**: true, neutral, and carries no distinction —
  `architecture-design` provides guidance too. A term that does not separate the
  two cannot do the work the record needs it to do at the one point both are
  reachable. It stays usable as an ordinary word; what it cannot be is the term
  that draws the line.

No category was left Outstanding and none was Deferred. The eight rows marked
Clear were each read against the spec rather than passed over: Domain & Data
Model against the Key Entities section, Edge Cases against its five entries,
Completion Signals against SC-001 to SC-006 — including SC-002, whose
untestability is stated in the spec rather than hidden, which is why it is Clear
and not Partial.
