# Analysis scan — #307

## Session 2026-09-09

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 6 · Critical: 0 · Acted on: 3 · Accepted: 3
- Detail: `<spec-root>/307-clarify-findings-in-repo/checklists/analysis-report.md`

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Resolved |
| B · Ambiguity | Resolved |
| C · Underspecification | Resolved |
| D · Constitution alignment | Clear |
| E · Coverage gaps | Resolved |
| F · Inconsistency | Deferred |
| Requirement-to-task coverage | 64% before, 100% after C1 |

### Findings

- **B · Ambiguity, MEDIUM** — FR-004 required a coverage table with "the status the
  scan assigned it" and named no vocabulary, while `speckit-clarify` carries two:
  Clear / Partial / Missing for the internal scan, and Resolved / Deferred / Clear /
  Outstanding for the report. Two implementers would have picked differently.
  → Fixed. FR-004 now fixes the reporting set, and says why the scanning set is not
  the one written down.
- **E · Coverage gaps, MEDIUM** — two tasks, "add the instruction", stood in for
  eight functional requirements. Nothing in `tasks.md` would have told an
  implementer that FR-011 or FR-014 existed.
  → Fixed. T007 and T008 now name one line per requirement they carry; requirement
  coverage moves from 64% to 100%.
- **A · Duplication, MEDIUM** — the same three assumptions were written out in
  `spec.md`, `design.md` and the level-3 record. Two of those three are gitignored,
  so any drift between them would be invisible to the only reader who could catch it.
  → Fixed. `spec.md` now names the record by path. Decided against keeping the
  spec's copy and deleting the record's: the record is the copy a reviewer opens,
  which is this whole feature's argument applied to itself.
- **C · Underspecification, LOW** — T009 (the AGENTS.md paragraph) has no
  requirement behind it.
  → Accepted. It is documentation carried by `knowledge-placement`, which is a
  record rather than a requirement, and inventing an FR to cover a convention would
  make the requirement set the place conventions live.
- **C · Underspecification, LOW** — FR-009 and FR-010 are negative requirements
  ("do not change the predicates", "do not add a gate") with no task and no new
  assertion.
  → Accepted. The existing suite fails on a predicate change, which is real
  coverage arrived at incidentally. Named here rather than left silent, because a
  requirement held by accident and one held on purpose read identically in a green
  run.
- **F · Inconsistency, LOW** — `design.md`'s MVP Scope predates FR-013 and does not
  mention committing the scan file.
  → Accepted, and deliberately not fixed. `design.md` is the upstream artifact;
  the spec supersedes it, and rewriting it would lose the level-1 walkthrough that
  generated the level-3 requirement. Deferred rather than clear, so the staleness
  is on record rather than discovered later.

### Deferred

- **F · Inconsistency** — as above. One known stale sentence in a gitignored
  upstream document, left where it is with the reason stated.
