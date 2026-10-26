# Analyze scan for #635

## Session 2026-10-26

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 13 · Critical: 0 · Acted on: 11 · Accepted: 2
- Detail: /Users/andremarin/Development/wfctl-specs/635-arch-folder-per-branch-notes/checklists/analysis-report.md

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Clear |
| C · Underspecification | Resolved (1 MEDIUM, record and tasks fixed) |
| D · Constitution alignment | Resolved (1 LOW, task fixed) |
| E · Coverage gaps | Resolved (1 MEDIUM and 2 LOW, tasks fixed) |
| F · Inconsistency | Outstanding (2 LOW; 1 MEDIUM and 4 LOW resolved) |
| G · Design-record contradiction | Resolved (1 HIGH, record fixed; 2 records read) |
| Requirement-to-task coverage | 100% |

The repo has no constitution, so pass D checked the tasks against the gates in `AGENTS.md` and the in-force records. Pass G compared every task against the Decision and Consequences sections of the two proposed records `design.md` lists.

### Findings

- **G · Design-record contradiction, HIGH** — The level-2 record's Consequences said `check-body` reports every missing exception reason in every repo. FR-015, R12, and T035 skip a boundary exception a sub-issue inherits from its epic once the sub-issue changes a level-2 record.
  → Fixed: the record now states that case. Decided against changing the tasks instead, since the spec settled the skip in FR-015 and the record had fallen behind it. The user approved the record edit, since pass G against a proposed record is outside the auto-apply scope.
- **C · Underspecification, MEDIUM** — The level-3 record said only `_design_exceptions` builds exception paths. The worktree guard's refusal prints the boundary exception's file, and no module function returned it, so `_record_gate.py` would have built it.
  → Fixed: the record, data-model.md, T002, and T003 add a fifth function, `path(spec_dir, name)`. T037 reads the exception with `boundary` and prints `path(spec_dir, BOUNDARY)`, and T052's grep covers `_record_gate.py`. Decided against leaving the path in the guard, since the record exists to keep the folder layout in one module. The user approved it, since it adds to the module's API.
- **E · Coverage gaps, MEDIUM** — No task covered how the agent responds to the guard's two new refusals.
  → Fixed: T040 updates the opening-a-change skill, and T056 updates AGENTS.md.
- **F · Inconsistency, MEDIUM** — The `STEP_CLAIMS_DIR` removal came before four of its importers, so committing per task broke the suite.
  → Fixed: T027 is last in its phase, and the US2 dependency line lists every importer.
- **E · Coverage gaps, LOW** — The `tests/test_skill_cross_references.py:204` docstring names the old path, and no task updated it.
  → Fixed: added to T022.
- **E · Coverage gaps, LOW** — No test asserted the `step none` success line.
  → Fixed: T017 asserts it.
- **F · Inconsistency, LOW** — The `tests/test_arch_records.py:476` docstring names the old folder.
  → Fixed: added to T022.
- **F · Inconsistency, LOW** — T037 said `_record_gate` doesn't import `rich`, but `resolve_spec_dir` loads it.
  → Fixed: T037 says it doesn't import `rich` directly.
- **F · Inconsistency, LOW** — The `check-body` tests were placed apart from the other `check-body` tests.
  → Fixed: they moved to `tests/test_shape.py`.
- **F · Inconsistency, LOW** — Two tests marked write-first passed on their first run.
  → Fixed: the old-declaration gate test is now T023 in Phase 4, failing before T027, and T048 and T049 are regression pins.
- **D · Repo gates, LOW** — T064 didn't name the tracker verb, and `AGENTS.md` says not to route around `wfctl issue`.
  → Fixed: T064 posts with `uv run wfctl issue comment 382`.
- **F · Inconsistency, LOW** — contracts/cli.md shows `✗` where `check-body` prints `⚠`.
  → Accepted: T031 asserts `⚠`, so the tasks carry the correct behavior. Editing the plan's contract makes the plan review stale and sends the pipeline back to plan.
    Not filed: it's a one-character fix for the next plan revision on this branch.
- **F · Inconsistency, LOW** — Research R9 omits the `architecture-decisions` skill, and the plan says "three passages".
  → Accepted: T039 and T057 carry the correction, and editing plan.md makes the plan review stale.
    Not filed: same reason as the contract line.

### Filing

- **plan.md wording** — the contract's `✗` and R9's passage list. Not filed: the fix belongs to the next plan revision on this branch, and the user was present for this run.

### Deferred

- None. Every pass ran.
