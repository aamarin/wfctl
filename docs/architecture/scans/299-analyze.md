# Analysis scan — #299

## Session 2026-09-10

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 7 · Critical: 0 · Acted on: 6 · Accepted: 1
- Detail: `<spec-root>/299-four-facts-in-the-payload/checklists/analysis-report.md`

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Accepted |
| B · Ambiguity | Resolved |
| C · Underspecification | Resolved |
| D · Constitution alignment | Resolved |
| E · Coverage gaps | Resolved |
| F · Inconsistency | Resolved |
| Requirement-to-task coverage | 73% before, 100% after T024 |

### Findings

- **F · Inconsistency, MEDIUM** — the second fact was named `definition of done
  verified` in the spec and `definition of done` in the data model and contract,
  and a consumer keys on that name.
  → Fixed. The spec now carries the four wire spellings. Decided against the
  longer form: it sets the console column width, and 29 characters of
  justification pushed the detail past 80 columns.
- **B · Ambiguity, MEDIUM** — FR-004 described the three values in prose and
  never gave the literals, which the Clarifications section had already settled.
  → Fixed. FR-004 carries `met` / `unmet` / `n/a`.
- **C · Underspecification, MEDIUM** — the first derivation was specified as
  taking `Evidence`, which `_infer_steps` never builds when no spec dir resolves
  — the exact input the spec's own edge case names.
  → Fixed. It takes `Evidence | None`. Decided against an empty `Evidence`: three
  empty strings cannot be told from a directory of three empty files.
- **D · Constitution alignment, MEDIUM** — the complexity gate was passed
  against a cost statement naming only `wfctl status`, while T003 puts the two
  git calls on all five `build_report` call sites.
  → Fixed. Performance Goals names them. The gate still passes, now against what
  is being spent.
- **E · Coverage gaps, MEDIUM** — the four prohibitions (FR-005, FR-008, FR-014,
  FR-015) had no task, which is how a prohibition becomes an intention.
  → Fixed. T024 states each as an assertion. Decided against folding them into
  existing tests: a prohibition asserted incidentally disappears when that test
  is rewritten, and these four outlive the feature.
- **F · Inconsistency, LOW** — `design.md`'s mock said `verified at`, the
  contract says `passed at`.
  → Fixed in `design.md`. Decided against changing the contract: `passed` is the
  word `wfctl verify` already uses for this outcome.
- **A · Duplication, LOW** — the four facts and their owners appear in five
  documents.
  → Accepted. Four are gitignored and close when the feature ships; the record is
  the copy that outlives the branch. Each serves a different reader at a
  different moment, and one pointer would send a reader writing a test to an
  ownership argument.

### Deferred

- **Non-Functional Quality Attributes** — the timing measurement behind the
  performance assumption. It needs a real repository and belongs to
  implementation; the level-3 record already records what would falsify it.
