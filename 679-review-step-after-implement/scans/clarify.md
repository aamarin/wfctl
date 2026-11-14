# Clarify scan: #679 review step after implement

## Session 2026-10-31

- Verdict: satisfied
- Scanned: spec.md
- Asked: 2 · Answered: 2 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/679-review-step-after-implement/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Resolved |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Resolved |
| Edge Cases & Failure Handling | Clear |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Resolved |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Integration & External Dependencies** — the spec didn't say whether
  `wfctl check-body` treats a recorded "no spec" the way it treats a pass
  exception.
  Q: Should `check-body` require the recorded reason in the PR body? → A: Yes,
  it fails a body whose "Needs a spec?" section doesn't carry the reason
  (option A, now FR-017).
  Basis: Andre chose the recommendation.
  Decided against **B, check only that the section is answered**: the file and
  the PR could then give different reasons, and every other recorded exception
  already reaches the reviewer through `check-body`.
  Decided against **C, check yes or no but not the reason**: it finds a flipped
  answer but not a reason rewritten between the file and the PR.
- **Interaction & UX Flow** — the spec said the seven skipped steps each carry
  the reason, which read as seven terminal rows repeating it, while the level-1
  state approved in `design.md` showed one line.
  Q: How does `wfctl status` show a branch with a recorded "no"? → A: The
  terminal shows one line, "skipped: no spec", without the reason. The JSON
  marks each step skipped with "no spec" and carries the reason once, in a
  top-level `no_spec` field with the file's path (FR-010).
  Basis: Andre chose option A after seeing it rendered, then asked why the
  reason needed showing in the terminal at all. The reason's readers are the
  review panel, which reads JSON, and the human reviewer, who reads the PR
  body, so the terminal drops it.
  Decided against **B, seven rows each with the reason**: seven identical lines
  bury `implement` and `review`, the two rows a no-spec branch acts on.
  Decided against **C, seven rows with the reason once under the last**: it
  keeps the noise of seven rows and still prints a reason nobody judges in the
  terminal.
- **Terminology & Consistency** — rendering the reason showed that its labels,
  "Test 1:" to "Test 3:", read as code tests to run and mean nothing without the
  `design-passes` skill open.
  Q: none asked separately; it came up while answering the display question. →
  A: the three are called the spec questions, and a reason answers each by name:
  "No behavior change: …", "No significant design decision: …", "No ownership
  change: …". The skills, AGENTS.md and the spec-question record now use that
  wording.
  Basis: Andre's question "why are the test labels there?" and his approval of
  the rendered example.
  No options offered — short answer.
