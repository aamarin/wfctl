# Analyze scans — #497

## Session 2026-09-27

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 11 · Critical: 0 · Acted on: 11 · Accepted: 0
- Detail: /Users/andremarin/Development/wfctl-specs/497-start-refuses-untracked-branch/checklists/analysis-report.md

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Clear |
| C · Underspecification | Resolved (1 MEDIUM, 1 LOW) |
| D · Constitution alignment | Clear |
| E · Coverage gaps | Resolved (2 MEDIUM, 2 LOW) |
| F · Inconsistency | Resolved (3 MEDIUM, 1 LOW) |
| G · Design-record contradiction | Resolved (1 HIGH, task fixed) |
| Requirement-to-task coverage | 100% |

The repository has no `.specify/memory/constitution.md`. Pass D read the gates
plan.md substitutes from `AGENTS.md` and the in-force records.

### Findings

- **G · Design-record contradiction, HIGH** — T005 reversed a proposed decision.
  Record: `docs/architecture/design/497-issue-check-is-a-pure-verdict.md`
  Decision: "`start_cmd` calls both, prints the verdict, and exits 1 on a
  refusal before anything else in the command runs."
  Task: "Call `gather` and `decide` at the top of `start_cmd` in
  `wfctl/cli.py`, immediately after `_resolve_context()`".
  `_resolve_context()` calls `resolve_agent_dir(create=True)` and
  `_remove_session_fossils`, so a refusal on a new branch left a state
  directory behind.
  → Fixed: T005 and research R8 move the check before `_resolve_context()`,
  taking `repo_root` and `branch` from the read-only `get_repo_root()` and
  `resolve_branch()`. The fix rests on SC-003, which the spec had already
  decided ("a refused `start` leaves the state directory byte-identical"), so it
  ratifies nothing the record alone asked for; Andre was attending, and the fix
  is reported here for him to overrule. Decided against making
  `_resolve_context()` take `create=False` for `start`: it changes a helper
  every command shares to serve one caller, and still leaves the fossil
  deletion ahead of the check.

- **F · Inconsistency, MEDIUM** — FR-006a had the bare `HEAD` read unguarded,
  while research R3 and T015 gate it on `core.bare`.
  → Fixed: FR-006a states the guard and that a normal layout's shared `HEAD` is
  the main checkout's current branch.

- **F · Inconsistency, MEDIUM** — FR-009 and SC-002 cited design.md for the
  refusal lines, which has no detached HEAD line, and FR-009 required "a remedy
  command" where the closed and missing remedies are not commands.
  → Fixed: both cite `contracts/start-output.md`; FR-009 says "its remedy" and
  names the state directory among what a refusal must not write.

- **F · Inconsistency, MEDIUM** — the spec's Assumptions counted "ten outcomes
  plus detached", omitting the trunk exemption that data-model.md and SC-002
  count.
  → Fixed: the assumption counts eleven and names both clarify additions.

- **F · Inconsistency, LOW** — US1's closed-issue example used #488, which is
  open.
  → Fixed: #495, which is closed, matching quickstart.md.

- **E · Coverage gaps, MEDIUM** — no task asserted SC-003.
  → Fixed: T008 asserts the state directory absent on a new branch and its files
  byte-identical on an existing one.

- **E · Coverage gaps, MEDIUM** — FR-001a's order had a test per row and none on
  facts that satisfy two rows.
  → Fixed: T021 adds three precedence tests.

- **E · Coverage gaps, LOW** — the timeout case of FR-012 and SC-004 was missing
  from `read_state`'s tests.
  → Fixed: T003 adds it through a monkeypatched `subprocess.run`.

- **E · Coverage gaps, LOW** — SC-006 had no task.
  → Fixed: T038 runs `/start-session` in the main checkout.

- **C · Underspecification, MEDIUM** — T010 skipped the tracker "when rows 1 - 6
  have not decided", leaving open whether the order lived in `gather` as well as
  `decide`, against the record's Consequences ("a new outcome is a branch in
  `decide` and a row in its tests").
  → Fixed: T010 has `gather` ask `decide` over the local facts before calling
  the tracker. Decided against a second copy of the order in `gather`: two
  copies drift, and the record names `decide` as the one place a row is added.

- **C · Underspecification, LOW** — the level-3 record's fact list predates
  clarify's `bare`, `on_trunk`, and `detached`.
  → Fixed: T035 brings the list up to data-model.md's, with a Log line.

Two fixes reached past the three artifacts the policy names: research.md R8
carried the same placement as T005, and `contracts/start-output.md` now lists
the state directory among what a refusal does not write. Both were corrected
with their source rather than left to contradict it.

### Filing

None. Every finding was fixed.

### Deferred

None.
