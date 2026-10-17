# Analyze scan: #359

## Session 2026-10-15

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md, all three present and read
- Findings: 8 · Critical: 0 · Acted on: 8 · Accepted: 0
- Detail: /Users/andremarin/Development/wfctl-specs/359-push-specs-to-trunk/checklists/analysis-report.md

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Resolved (1 LOW, task fixed) |
| C · Underspecification | Clear (no new finding; PR-006 and PR-024 wait on Andre, see Deferred) |
| D · Constitution alignment | Clear (no constitution.md; the plan's gates from AGENTS.md and accepted records were read) |
| E · Coverage gaps | Resolved (3 MEDIUM, 1 LOW, tasks fixed) |
| F · Inconsistency | Resolved (1 MEDIUM, 3 LOW, tasks fixed) |
| G · Design-record contradiction | Clear (3 records read) |
| Requirement-to-task coverage | 100% |

### Findings

Every fix below is an edit to `tasks.md`. Each one makes the tasks say what
`spec.md`, `plan.md`, `data-model.md` or a design record already says. Nothing
in `spec.md` or `plan.md` was edited, because an edit to `plan.md` makes the
plan review stale and sends the pipeline back to `plan`.

- **E · Coverage gaps, MEDIUM**: no task asserted FR-008's success output, the
  two lines with the count, upstream and short id, and the count's noun.
  → Fixed: T011 now asserts the two lines from `contracts/cli.md` and that the
  noun is "files". Decided against adding a separate task: T011 already owns the
  success-path tests.
- **B · Ambiguity, LOW**: FR-008 says the output says "files", never "specs".
  Read literally, that fails on the success line, which names
  `origin/specs-trunk`.
  → Fixed: T011 asserts on the noun rather than on "specs" being absent.
  Decided against rewording FR-008 in `spec.md`: the example in US1 already
  shows what it means, and the test is where the literal reading would bite.
- **E · Coverage gaps, MEDIUM**: the spec's edge cases for a branch with no spec
  dir, and for a store on `main`, had no test. `data-model.md` defines the
  outcome as `no_spec_dir`, exit 0.
  → Fixed: T017 now tests `no_spec_dir` on both, including that it commits
  nothing. Decided against a test in T011: this is a CLI outcome, and T017
  carries the CLI tests.
- **E · Coverage gaps, MEDIUM**: FR-016 says reading whether a spec dir is
  stored never touches the network. T013 tested that for the pass, and nothing
  tested it for `check specs`.
  → Fixed: T029 asserts that no git call in a `check specs` run fetches.
- **E · Coverage gaps, LOW**: US2 scenario 2, a fully stored spec dir at
  removal, had no test.
  → Fixed: T025 covers it.
- **F · Inconsistency, MEDIUM**: FR-018 and `store-specs-implement-pass.md` say
  a `skipped` reading carries "a reason naming the layout". T018 says the
  reading's `reason` is always `None`. The payload's `reason` is the field that
  routes to `wfctl verify`, so the two documents use one word for two things.
  → Fixed: T018 says the reason FR-018 asks for is the `display` text, and that
  the payload field stays `None`. Decided against changing the spec's wording:
  "reason" is the right word for a reader of the spec, and the task is where the
  field name matters.
- **F · Inconsistency, LOW**: `plan.md` says to regenerate the payload snapshot,
  and T023 says it must not change (PR-005).
  → Fixed: T023 says it supersedes the plan, and that the plan is left unedited
  for the reason T049 gives.
- **F · Inconsistency, LOW**: the parallel opportunities listed US3 beside US1,
  but both edit `wfctl/cli.py`, and the same section says stories sharing it run
  in sequence.
  → Fixed: only T029 runs beside US1, and T030 and T031 wait for T017.
- **F · Inconsistency, LOW**: T025 edited `tests/test_archive_specs.py` before
  T026 checked whether #40 had moved removal onto `hook worktree-remove`, which
  decides where those tests belong.
  → Fixed: T025 starts after T026's check.

Pass G read all three records' Decision and Consequences sections against every
task, and no task reverses one. The implement-pass record says the orchestrate
skill is the first place to check once `implement` reads done with a pass
outstanding. The skill decides "story complete" from `next_command` being
`null`, and T013 asserts the pass sets it to `/store-specs`, so no task was
needed there.

### Deferred

- **C · Underspecification**: PR-006 and PR-024 are open plan-review findings
  that wait on Andre. `tasks.md` records both as his call. This scan doesn't
  raise them again, because filing them would duplicate a question already put
  to him.
