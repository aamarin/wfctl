# Clarification scan — #307

## Session 2026-09-09

Two passes on one date, in one section: the second extends the first rather than
opening a second heading, which is the rule the fourth finding below settled.

- Verdict: satisfied
- Scanned: spec.md
- Asked: 4 · Answered: 4 · Outstanding: 0 · Deferred: 0
- Detail: `<spec-root>/307-clarify-findings-in-repo/spec.md` § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Resolved |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Resolved |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Resolved |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

Non-Functional was `Deferred` on the first pass — no bound stated on the size of
`analyze`'s scan file, whose upstream report runs to 50 findings rows. The plan
settled it by deciding the scan file carries what a pass concluded and points at
the full report, so there is no 50-row table to bound.

### Findings

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
- **Domain & Data Model**, second pass — the amended FR-011 keys a session by
  date, and two runs on one day collide. Q: does the second open a new section or
  extend that day's?
  → A: it extends that day's. Decided against *a timestamp or a counter*: the
  sessions a reviewer distinguishes are separated by the pipeline advancing, not
  by the clock, and `/speckit.clarify` already merges same-day runs into one
  `### Session YYYY-MM-DD` in `spec.md` — a second convention here would make the
  two documents disagree about what a session is. This file is the case: two
  passes, one heading. → FR-011.

### Notes

The second pass was the exercise `AGENTS.md` requires for a change under
`wfctl/agents/`, run against the installed wrapper rather than by hand. It is why
this file has sessions at all: under the rule as first written the step would have
replaced the first pass, deleting the three answers FR-013 through FR-015 were
written from.
