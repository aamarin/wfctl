# Specification Analysis Report

Feature: `264-sentinel-goes-stale`, a new task reopens the `implement` step.
Run: 2026-10-09, unattended. This report is written after remediation, so
every status, count, and percentage below describes the artifacts as they now
stand.

Scanned: `spec.md`, `plan.md`, and `tasks.md`, all three present and read.
Also read as context: `design.md`, `research.md`, `data-model.md`,
`contracts/cli.md`, `quickstart.md`, `plan-review.md`, the two level-3 design
records, the level-2 record `docs/architecture/new-task-reopens-implement.md`,
and the code the tasks name (`wfctl/_evidence.py`, `wfctl/_pipeline.py`,
`wfctl/cli.py`, `wfctl/_md.py`, `wfctl/agents/commands/speckit.implement.md`,
and the tests the plan changes).

Constitution: the repository has no `.specify/memory/constitution.md`.
`AGENTS.md` and the 13 accepted records from `uv run wfctl arch context` stand
in for it, as the plan's Constitution Check says.

Design records: 2 listed in `design.md`, both read, both `proposed`.

- `docs/architecture/design/264-the-task-copy-lives-in-the-completion-record.md`
- `docs/architecture/design/264-the-completion-command-is-a-step-verb.md`

## Findings

Every finding was fixed in `spec.md`, `plan.md`, or `tasks.md`. None stands.

| ID | Category | Severity | Location(s) | Summary | Disposition |
| --- | --- | --- | --- | --- | --- |
| F1 | Inconsistency | HIGH | spec.md FR-010; tasks.md T008; plan.md Test Plan | FR-010 required `/speckit.implement` whenever `implement` reads open, while T008 and a Test Plan row pin `/speckit.decompose` for a reopened story with no `delivery.md`. T028 deferred the qualification to Phase 7, so the conflict would have stood through `implement`. | Fixed in spec.md FR-010 |
| F2 | Inconsistency | MEDIUM | spec.md Edge Cases; plan.md Summary item 2 | Both stated the delivery-plan limit too narrowly (plan review PR-009): `decompose` is skipped while the tasks read closed, not while every box is ticked, and an unkeyed row under a configured tracker also routes to `decompose`. T028 carried the spec half and not the plan half. | Fixed in spec.md Edge Cases and plan.md Summary item 2 |
| F3 | Inconsistency | MEDIUM | spec.md FR-004; tasks.md T004 | FR-004 and the level-3 record size the fence one longer than the longest fence inside the copy. T004 sized it against tilde markers only, so a copy holding a six-backtick fence would get a four-tilde fence. | Fixed in tasks.md T004 and T029 |
| F4 | Inconsistency | MEDIUM | tasks.md T014 | T014 told the implementer to confirm the snapshot row moves from finished to `implement` in progress. The committed row stops at `analyze`, and T010 lands before T013, so the regenerated diff shows a different move. Each row also has a `(no tracker)` twin. | Fixed in tasks.md T014 |
| F5 | Inconsistency | LOW | tasks.md T028, T029, Parallel Opportunities | T028 and T029 were both marked `[P]` and both edit `research.md`, and the parallel note said they edit different files. | Fixed in tasks.md T029 and Parallel Opportunities |
| E1 | Coverage gap | MEDIUM | tasks.md T007; spec.md Story 1 #1, SC-001 | No automated test asserted the next command in the arm with no definition of done. Only the manual T031 checked it. | Fixed in tasks.md T007 |
| E2 | Coverage gap | LOW | tasks.md T016, T018 | T018 implements the contract's "no feature directory" refusal, and T016 had no test for it. | Fixed in tasks.md T016 |
| C1 | Underspecification | LOW | tasks.md T028 | T028 told the implementer to make two wording changes in `research.md` § R1, and neither phrase appears in R1. | Fixed in tasks.md T028 |
| C2 | Underspecification | LOW | tasks.md T019 | T019 named one paragraph that calls step 9b a sentinel. The command file does so in two passages. | Fixed in tasks.md T019 |

### What changed, finding by finding

- **F1**: FR-010 now reads "for a feature whose `decompose` step reads done
  or skipped", the condition the Edge Cases bullet and T008 already state.
  T028 no longer carries the spec edit. The alternative, leaving the edit in
  T028, was rejected because the requirement would contradict a planned test
  for the whole of `implement`.
- **F2**: The spec's Edge Cases bullet and plan.md § Summary item 2 now say
  "while the tasks read closed", name the unkeyed-row route, and say
  `implement` becomes current once a delivery plan exists and every row is
  keyed or no tracker is declared. The plan's claim that only new features
  reach the case now includes features whose plan has an unkeyed row. The
  alternative, adding plan.md to T028, was rejected because an edit to
  `plan.md` during `implement` would stale the plan review mid-implementation.
- **F3**: T004 now sizes the fence against every marker `_md.opens_fence`
  matches, backtick or tilde, which is what FR-004 and the level-3 record
  say. T029 now also brings `research.md` § R4 and `data-model.md` into line.
  The alternative, rewording FR-004 to the tilde rule, was rejected because
  it would move the spec away from the design record's Decision.
- **F4**: T014 now names both entries of each row, says the move is from all
  three later steps `pending` to `implement` `in_progress`, and says the
  commit message names the verdict the rebuilt fixture would have read under
  the old rule. This is the point plan review raised under Assumptions
  challenged.
- **F5**: T029 lost its `[P]` marker and now runs after T028. The parallel
  note now says so.
- **E1**: T007's first test now also asserts `/speckit.implement` as the next
  command, and cites FR-010 and SC-001.
- **E2**: T016 now tests that a branch with no feature directory exits 1 and
  writes nothing.
- **C1**: T028 now names what R1 actually says: the "holds for a feature with
  a delivery plan" sentence and the "22 of 22" sentence.
- **C2**: T019 now quotes both passages, "The step 9b sentinel is no later
  point" and "after the sentinel and after `wfctl verify`".

### Design-record contradiction (pass G)

No task reverses the Decision or Consequences of either record.

- The task copy lives in the completion record: T004 writes one file with the
  date line, the `## Tasks at completion` heading, and a fenced copy. The
  reader uses `_md.walk`, and T018 writes atomically, so the record never
  loses its copy. Before F3's fix, T004's tilde-only sizing read narrower than
  the Decision's "a fence longer than any fence in that text". It was not a
  reversal, since the Consequences name the binding constraint as a fence the
  copy can't close, and the tilde rule met it. After the fix it matches the
  Decision's wording too.
- The completion command is a step verb: T018 adds `wfctl step complete`,
  refuses any step but `implement` with a message naming it, and widens the
  group's help text. T019 adds the command to `allowed-tools`, as the
  Consequences require.

## Coverage Summary

| Requirement | Has task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 | Yes | T016, T018 | Yes | |
| FR-002 | Yes | T016, T018 | Yes | |
| FR-003 | Yes | T016, T018 | Yes | |
| FR-003a | Yes | T016, T018 | Yes | |
| FR-004 | Yes | T002, T004 | Yes | Fence rule aligned by F3 |
| FR-005 | Yes | T007, T010 | Yes | |
| FR-006 | Yes | T003, T005, T007 | Yes | |
| FR-007 | Yes | T002, T010, T012, T024 | Yes | |
| FR-008 | Yes | T010, T024, T025 | Yes | |
| FR-009 | Yes | T005, T007 | Yes | |
| FR-010 | Yes | T007, T009, T008 | Yes | Qualified by F1; T008 pins the exception |
| FR-011 | Yes | T017, T019, T020 | Yes | |
| FR-012 | Yes | T010 | Inspection | No modification time is read; no test can show an absence cheaply |
| FR-013 | Yes | T007 | Yes | |
| SC-001 | Yes | T007, T009, T031 | Yes | No-DoD arm asserted by E1's fix |
| SC-002 | Yes | T007 | Yes | |
| SC-003 | Yes | T022 | Yes | |
| SC-004 | Yes | T024, T025 | Yes | |
| SC-005 | Yes | T002 | Yes | |

**Constitution alignment issues**: none. The tasks keep the source under
`wfctl/agents/`, leave `speckit-implement/SKILL.md` unedited, add no payload
field, pin `NO_COLOR` where tests read output, and end on the three
`AGENTS.md` commands plus `uv run wfctl doctor` (T032). T020 runs
`install-skills` and reads the installed command, as `AGENTS.md` asks for a
change under `wfctl/agents/`.

**Unmapped tasks**: T001 is the baseline run. T006, T015, T021, T023, T026,
and T032 are merge gates. T027 to T030 bring the level-2 record, `research.md`,
`data-model.md`, and `quickstart.md` in line with plan review PR-003 to
PR-010. T031 is the Validation Strategy's hand reproduction. Each serves the
spec's Validation Strategy rather than a single requirement.

**Verification gaps**: none after remediation.

**Plan review carry-over**: each open MINOR finding in `plan-review.md` is
carried by a named task. PR-003 by T002 and T004, PR-004 by Phase 2's
dependency note, PR-005 by T003, T005, and T029, PR-006 by T019, PR-007 by
T018, PR-008 by F1's fix and T027, PR-009 by F2's fix and T028, and PR-010 by
T030.

## Metrics

- Total requirements: 19 (14 functional, 5 success criteria)
- Total tasks: 32
- Coverage: 100% (19 of 19 requirements have at least one task)
- Ambiguity count: 0
- Duplication count: 0
- Critical issues count: 0
- Findings: 9 · Critical: 0 · Acted on: 9 · Accepted: 0

## Next Actions

No CRITICAL finding stands, and no HIGH or MEDIUM finding stands. Every
finding was fixed in the artifacts.

This run edited `plan.md` § Summary item 2. The plan review in
`plan-review.md` was measured against the plan before that edit, so the
`plan` step reads stale until `/plan-review` runs again. The edit is a
wording correction that plan review itself asked for as PR-009, so a
re-review should find it closed rather than new.

Run `/plan-review`, then `/speckit.decompose`.
