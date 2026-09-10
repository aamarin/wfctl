# Clarification scan — #307

- Verdict: satisfied
- Scanned: spec.md
- Asked: 3 · Answered: 3 · Outstanding: 0 · Deferred: 1
- Detail: `<spec-root>/307-clarify-findings-in-repo/spec.md` § Clarifications

## Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Resolved |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Deferred |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Resolved |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

## Findings

- **Edge Cases & Failure Handling** — the spec required the file to be written and
  said nothing about whether it lands somewhere a reviewer reads.
  Q: does a scan step verify reachability, or only write?
  → A: it commits the file and runs `wfctl arch check` on it. Decided against
  *write only, check at PR time*: `arch check` refuses an uncommitted file by
  design (`cli.py` — "staging it is not committing it"), so a step that writes
  without committing can never use the check that exists for this. Follows
  `/speckit.brainstorm`, which already commits its records mid-pipeline. → FR-013.
- **Domain & Data Model** — two features claiming one issue key would write one
  filename. Q: key by issue or by branch?
  → A: by issue. Decided against *key by branch slug*: `<arch-root>/design/` and
  `declarations/` are both `<issue>-`, and a third convention for a fourth
  sibling buys nothing. The collision is a condition `wfctl doctor` reports today
  — it named three of them on this branch — so restating it here would be a
  second owner for one finding. → FR-014.
- **Terminology & Consistency** — "scan file", "scan receipt" and "attestation"
  were all in use across the design document and the two records.
  Q: which is canonical?
  → A: "scan file" for the artifact. Decided against *receipt*, which
  `136-the-receipt-is-a-sibling-of-merged` uses for a manifest entry, and against
  *record*, which is an architecture record. "Attestation" is kept for the fact
  the file carries, which is how the level-2 record uses it. → FR-015.

## Deferred

- **Non-Functional Quality Attributes** — no bound is stated on the size of
  `analyze`'s scan file, whose upstream report runs to 50 findings rows. Plan-level:
  it decides a format, not a boundary, and `/speckit.plan` is where the format is
  written. Recorded rather than dropped, because a deferred question and one nobody
  asked read the same in a spec.
