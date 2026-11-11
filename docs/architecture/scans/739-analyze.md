# Analyze scan for #739

## Session 2026-11-10

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md, all three present and read
- Findings: 4 · Critical: 0 · Acted on: 3 · Accepted: 1
- Detail: /Users/andremarin/Development/wfctl-specs/739-architecture-views/checklists/analysis-report.md

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Outstanding (1 LOW; 1 MEDIUM resolved) |
| C · Underspecification | Clear |
| D · Constitution alignment | Clear (no constitution; the plan's gates from `AGENTS.md` and the accepted records were checked instead) |
| E · Coverage gaps | Resolved (1 LOW, task fixed) |
| F · Inconsistency | Resolved (1 MEDIUM, task fixed) |
| G · Design-record contradiction | Clear (design.md lists none) |
| Requirement-to-task coverage | 100% |

### Findings

- **F · Inconsistency, MEDIUM.** T010 in User Story 1 read a view's `covers` line with the bracket parsing `Record.kinds` uses, but T032 adds `Record.kinds` in User Story 3, which runs independently.
  → Fixed: T010 and T032 now name one bracket-list helper beside `split_names` in `wfctl/arch/_records.py`, and whichever task lands first adds it. Decided against moving the helper into its own foundational task, since that would renumber every task after it for a one-function change.
- **B · Ambiguity, MEDIUM.** The tasks didn't say which `unchecked` reason prints for a view under an out-of-tree architecture root that has no `covers` line, while `plan.md §Validation Strategy` says every present view there prints `not in this repository's history`.
  → Fixed: T020 now tests that case, and T022 checks the history reason first for an out-of-tree root. Decided against leaving it to the implementer, since the plan already states the outcome.
- **E · Coverage gaps, LOW.** FR-007 says no command, pipeline step, or PR is refused because of a view, and only the exit code of `wfctl arch context` was tested.
  → Fixed: T025 now checks with `grep` that only `wfctl/arch/` and `arch_context_cmd` use `_views`. Decided against a test per gate, since none of them reads views and a test can't show that a module ignores a file.
- **B · Ambiguity, LOW.** For an in-tree view with no `covers` line in a directory that isn't a git repository, `spec.md §FR-006a` doesn't say which `unchecked` reason prints. Plan review PR-015 reports the same gap in `data-model.md`.
  → Accepted: choosing the order is a decision the three artifacts haven't made, and the fix belongs in `data-model.md`, which this step doesn't edit.
    Not filed: the session is attended, and the user decides whether to fix it in `data-model.md` or file it.

### Filing

- **The order of `unchecked` reasons is unstated** covers the B · Ambiguity LOW finding and plan review PR-015. Not filed: waiting on the user's decision in this session.
  Title: State which `unchecked` reason prints when two apply to a view
  Body: `data-model.md §Required view` lists three `unchecked` reasons for a present view: no `covers` line, a covered path that's missing, and no git history. Nothing says which one prints when two apply, such as an in-tree view with no `covers` line in a directory that isn't a git repository. The out-of-tree case is settled, since `plan.md` and `research.md §R-010` say every present view there takes the history reason. State the order in `data-model.md`, and add a test for the in-tree case to `tests/test_arch_views.py`.
