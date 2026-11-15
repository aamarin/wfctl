# Analyze scan: 740-svg-drawings

## Session 2026-11-14

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 3 · Critical: 0 · Acted on: 3 · Accepted: 0
- Detail: /Users/andremarin/Development/wfctl-specs/740-svg-drawings/checklists/analysis-report.md

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Clear |
| C · Underspecification | Clear |
| D · Constitution alignment | Clear (no constitution file; checked the plan's substituted gates) |
| E · Coverage gaps | Resolved (1 HIGH, task fixed) |
| F · Inconsistency | Resolved (2 MEDIUM, fixed) |
| G · Design-record contradiction | Clear (2 records read) |
| Requirement-to-task coverage | 100% |

### Findings

- **E · Coverage gaps, HIGH** — FR-024 requires the terminal check before any write. The `redrawn` write on an accepted record (T043) had no task or test putting it behind that check, so an implementation could let an agent sign off a changed drawing from a non-terminal shell.
  → Fixed: T043 now puts the `redrawn` write behind the same `_at_terminal()` check T042 adds, and T034 tests both the proposed and the redraw path. Decided against a separate task, since FR-024 already says "before it writes anything" and the redraw is one more write.
- **F · Inconsistency, MEDIUM** — spec FR-011, the plan's Constraints, and `contracts/cli.md` said the reworded `no drawing` fix prints only under `wfctl arch accept`. `accept_problems` carries that line whole, so it also shows in the design gate's reason, as `tests/pipeline_payload_snapshot.json` shows. The tasks and research R-010 were already right.
  → Fixed: all three now say the `no drawing` wording shows in the design gate's reason, and that only the `_DRAWING_FIX` entries are confined to `arch accept`. Decided against fixing spec and plan alone, since leaving `contracts/cli.md` with the old sentence would recreate the drift.
- **F · Inconsistency, MEDIUM** — the dependency note said T045 depends only on Phase 2, but `redraw_only` matches `REDRAWN_LINE`, which T040 adds.
  → Fixed: the note now says T045 also needs T040, and T047 needs T045 and T046.

### Filing

No finding needed filing.
