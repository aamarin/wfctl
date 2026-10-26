# Specification Analysis Report: #635

This is the report after remediation. Analyze ran on 2026-10-26 against spec.md,
plan.md, tasks.md, and the two design records `design.md` lists. Eleven findings
were fixed, and two stand as accepted.

## Metrics

- Requirements: 23
- Tasks: 64 (T001 - T064)
- Requirement-to-task coverage: 100%
- Ambiguity: 0
- Duplication: 0
- Critical: 0
- Findings: 13 (1 HIGH, 3 MEDIUM, 9 LOW). Acted on: 11. Accepted: 2.

## Findings

| ID | Pass | Severity | Outcome | Summary |
|---|---|---|---|---|
| G1 | G | HIGH | Fixed | The level-2 record said `check-body` reports every missing exception reason in every repo, but FR-015, R12, and T035 skip a boundary exception a sub-issue inherits from its epic once the sub-issue changes a level-2 record. The record's Consequences now state that case. |
| C1 | C | MEDIUM | Fixed | The level-3 record said only `_design_exceptions` builds exception paths, but the worktree guard's refusal prints the boundary exception's file, and no module function returned it. The record, data-model.md, T002, and T003 add a fifth function, `path(spec_dir, name)`. T037 reads the exception with `boundary` and prints `path(spec_dir, BOUNDARY)`, and T052's grep now covers `_record_gate.py`. |
| E1 | E | MEDIUM | Fixed | No task covered how the agent responds to the guard's two new refusals. T040 updates the opening-a-change skill, and T056 updates AGENTS.md. |
| F1 | F | MEDIUM | Fixed | The `STEP_CLAIMS_DIR` removal came before four of its importers, so committing per task broke the suite. T027 is now last in its phase, and the US2 dependency line lists every importer. |
| E2 | E | LOW | Fixed | The `tests/test_skill_cross_references.py:204` docstring names the old path, and no task updated it. Added to T022. |
| E3 | E | LOW | Fixed | No test asserted the `step none` success line. T017 asserts it. |
| F2 | F | LOW | Fixed | The `tests/test_arch_records.py:476` docstring names the old folder. Added to T022. |
| F3 | F | LOW | Accepted | contracts/cli.md still shows `✗` where `check-body` prints `⚠`. T031 asserts `⚠`, so the tasks carry the correction. Editing the plan's contract would make the plan review stale. |
| F4 | F | LOW | Fixed | T037 said `_record_gate` doesn't import `rich`, but `resolve_spec_dir` loads it. T037 now says it doesn't import `rich` directly. |
| F5 | F | LOW | Fixed | The `check-body` tests were placed in a file that doesn't hold the other `check-body` tests. They moved to `tests/test_shape.py`. |
| F6 | F | LOW | Fixed | Two tests marked write-first passed on their first run. The old-declaration gate test is now T023 in Phase 4, failing before T027, and T048 and T049 are regression pins. |
| F7 | F | LOW | Accepted | Research R9 omits the `architecture-decisions` skill, and the plan says "three passages". T039 and T057 carry the correction, and editing plan.md would make the plan review stale. |
| D1 | D | LOW | Fixed | T064 didn't name the tracker verb, and AGENTS.md says not to route around `wfctl issue`. T064 posts with `uv run wfctl issue comment 382`. |

## Per-pass status

| Pass | Status |
|---|---|
| A · Duplication | Clear |
| B · Ambiguity | Clear |
| C · Underspecification | Resolved (1 MEDIUM) |
| D · Constitution alignment | Resolved (1 LOW) |
| E · Coverage gaps | Resolved (1 MEDIUM, 2 LOW) |
| F · Inconsistency | Outstanding (2 LOW; 1 MEDIUM and 4 LOW resolved) |
| G · Design-record contradiction | Resolved (1 HIGH, record fixed; 2 records read) |

## Next Actions

No CRITICAL or HIGH finding stands. The two remaining LOW findings are wording in
plan.md and its contract, and the tasks already carry the correct behavior. They
wait for the next plan revision on this branch, since any plan.md edit makes the
plan review stale. The next step is `/speckit.decompose`.
