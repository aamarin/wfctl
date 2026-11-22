# Analyze scan for #818

## Session 2026-11-22

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 5 · Critical: 0 · Acted on: 5 · Accepted: 0
- Detail: /Users/andremarin/Development/wfctl-specs/818-whole-system-threat-model/checklists/analysis-report.md

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Clear |
| C · Underspecification | Clear |
| D · Constitution alignment | Deferred (no constitution at .specify/memory/constitution.md) |
| E · Coverage gaps | Resolved (2 MEDIUM, 1 LOW fixed) |
| F · Inconsistency | Resolved (1 MEDIUM, 1 LOW fixed) |
| G · Design-record contradiction | Clear (1 record read) |
| Requirement-to-task coverage | 100% |

### Findings

- **E · Coverage gaps, MEDIUM** — FR-013's empty committed file had no test.
  → Fixed: T018 now checks that an empty committed `THREAT_MODEL.md` reads `done`. Decided against leaving it to the quickstart's manual step, which a later edit wouldn't re-run.
- **E · Coverage gaps, MEDIUM** — FR-014 had no state test with auto-approve on.
  → Fixed: T018 now checks the missing-file case reads the same `in_progress` with auto-approve on. Decided against relying on T024's `needs_person` flag alone, since that flag doesn't exercise the reader.
- **F · Inconsistency, MEDIUM** — T019 and T021 hold the pass with no trunk, while research R6 row 4 and `data-model.md` say skipped.
  → Fixed: T021 says it replaces that row, citing the spec's edge case that a git read which can't answer reads in progress. Decided against following R6 row 4, because nothing later catches a missing baseline the way `wfctl arch accept` catches a drawing.
- **F · Inconsistency, LOW** — T030 gives Claude upstream's own helper path, while research R2 names the relative path.
  → Fixed: T030 says it replaces R2 on Claude and still meets FR-005a. Decided against the relative path, which misses upstream's pre-granted call and prompts on Claude.
- **E · Coverage gaps, LOW** — T031 added a public-repository line to `threat-baseline` that no requirement asks for.
  → Fixed: T031 removed. Decided against keeping it, since it made a decision the spec doesn't make and sat uneasily with FR-007a's unattended commit. The question is filed as #852.

### Filing

- **Public-repository disclosure of `THREAT_MODEL.md`** — the question E3's removed task carried, first raised as plan review PR-011. Filed as #852.
