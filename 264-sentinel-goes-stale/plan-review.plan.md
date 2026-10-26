# Implementation Plan: A new task reopens the `implement` step

**Branch**: `264-sentinel-goes-stale` | **Date**: 2026-10-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `spec.md` in this feature directory

## Summary

wfctl stops trusting the completion record just because it exists. When the
`implement` step finishes, the agent runs `wfctl step complete implement`,
which writes the completion record with a copy of `tasks.md` inside it. Each
time wfctl reports status, it compares the live task list against that copy,
and an incomplete task that was not incomplete in the copy reopens the step.

The change has four parts.

1. A new module, `wfctl/_completion.py`, owns the record's format. It renders
   the record, reads the copy back out of it, and says which incomplete tasks
   in a task list are new against a copy. The writer and the reader live
   together, so the format has one owner, as the level-3 record requires.
2. `_tasks_open` in `wfctl/_evidence.py` asks `_completion` instead of
   returning "closed" whenever the record exists. Nothing else in the
   inference changes: the `implement` reader, the `decompose` reader, and the
   routing in `next_step_content` already do the right thing once
   `tasks_open` is true. The `tasks` reader's `skipped` arm keeps reading the
   record by existence.

   That holds for a feature whose delivery plan has every row keyed, or whose
   repository declares no tracker. Without `delivery.md`, the `decompose` step
   is skipped only while the tasks read closed, so a story that reopens is
   sent to `/speckit.decompose` first, and `implement` waits behind it. A
   delivery plan with an unkeyed row under a configured tracker does the same.
   This change leaves that routing as it is. Every feature in this
   repository's spec store that holds a completion record also holds a
   delivery plan, so the case reaches new features, other repositories, and
   any feature whose delivery plan has an unkeyed row. The tests for Stories 1
   and 4 carry a keyed `delivery.md`, and one test pins the routing without
   it.
3. `wfctl/cli.py` gains `wfctl step complete implement` beside `step none` and
   `step sign-off`. It refuses any other step, a feature with no `tasks.md`,
   and a pipeline that has not reached `implement` yet.
4. `wfctl/agents/commands/speckit.implement.md` tells the agent to run the
   command in place of writing the file at step 9b, and adds it to
   `allowed-tools`. `speckit-implement/SKILL.md` is not edited.

Three existing tests and one snapshot row describe a record with no copy
closing a story that still has an open box. That was the point of the old
record, which stood in for work done outside the skill. Under the new rule the
same files reopen the step, so each of those tests changes to write a record
with a copy, which is how that case is expressed from now on. The snapshot is
regenerated, and the commit says which verdict moved. Test Plan lists them.

The level-2 decision is `docs/architecture/new-task-reopens-implement.md`,
still proposed. The level-3 decisions are
`docs/architecture/design/264-the-task-copy-lives-in-the-completion-record.md`
and `docs/architecture/design/264-the-completion-command-is-a-step-verb.md`,
both proposed.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `typer` and `rich`, already in use; `collections.Counter`
from the standard library for matching tasks by count; nothing added  
**Storage**: `checklists/implement-complete.md` in the feature directory. Its
first line is unchanged; a `## Tasks at completion` section and a fenced copy
of `tasks.md` follow it. A record written before this change still reads,
as a record with no copy.  
**Testing**: `uv run pytest -q`, with a new `tests/test_completion_record.py`
and changes to four existing tests and the payload snapshot;
`uv run ruff check wfctl/ tests/`; `uv run mypy wfctl/`  
**Target Platform**: macOS and Linux developer machines, CI on Python 3.11
and 3.13  
**Project Type**: CLI  
**Performance Goals**: N/A. One more small file is read per status call,
only when the record exists.  
**Constraints**: The reading never depends on a file's modification time
(FR-012). Every rule fails toward reopening the step: when wfctl cannot tell
whether a task is new, it treats it as new. Minimal-complexity bias: no
migration of old records, no tamper protection, and no change to the payload's
shape.  
**Scale/Scope**: One new module of about 80 lines, one changed function, one
new CLI verb, one command-file section, about 25 new tests, three changed
tests, and a regenerated snapshot.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repository has no `.specify/memory/constitution.md`. The gates below come
from `AGENTS.md` and the accepted records instead, and Complexity Tracking
records the substitution.

- [x] Validation plan exists: the three `AGENTS.md` commands, the tests in
      Test Plan, `uv run wfctl install-skills` followed by a read of the
      installed command file, and the two-arm reproduction in `quickstart.md`.
- [x] Complexity is justified: one module is added, and it exists because the
      level-3 record requires the format to have one owner. The alternative,
      the writer in `cli.py` and the reader in `_evidence.py`, splits the
      format across the two largest files in the package.
- [x] Ownership is stated: wfctl computes whether a task is new, by comparing
      the live list against the copy. The agent can't be asked, since it would
      be grading its own work, and a timestamp can't answer, since a restore
      from `specs-trunk` gives every file the same one. The copy itself is
      written by wfctl's command, at the one moment the old task list still
      exists.
- [x] `session-state-is-re-derived` holds: whether the step is open is
      computed from the two files at every read. The copy is a recorded fact
      that re-derivation can't reach, since previous versions of `tasks.md`
      are not preserved.
- [x] `wfctl-runs-the-verification` holds: the completion record still
      certifies nothing. Where a definition of done is configured, it still
      gets the last word once the tasks read closed.
- [x] `pipeline-state-is-one-payload` holds: no field is added. A reopened
      step is the existing `in_progress` state with its existing tally.
- [x] `vendor-upstream-skills` holds: the instruction change is in the
      command file, and `speckit-implement/SKILL.md` is untouched.
- [x] `layer-model` holds: the source is under `wfctl/agents/`, and nothing
      under `.agents/` or `.claude/` is edited by hand.
- [x] `a-rule-is-expressed-as-a-check` holds: the reopen rule is a check that
      runs on every status call, and the round trip and the no-definition-of-done
      arm each get a test.
- [x] `AGENTS.md` test conventions: new tests pin `NO_COLOR` where they assert
      on output, carry sentence names, and say in their docstrings which failure
      they catch.
- [x] `AGENTS.md` code style: no ruff rule change, and every new function is
      annotated for mypy.

Re-checked after Phase 1: unchanged. Phase 1 added the record's format and the
command's contract, both already decided at level 3.

## Project Structure

### Documentation (this feature)

```text
264-sentinel-goes-stale/
├── design.md            # brainstorm output
├── spec.md              # /speckit.specify output, with Clarifications
├── plan.md              # this file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli.md           # wfctl step complete
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks, not created here)
```

### Source Code (repository root)

```text
wfctl/
├── _completion.py                     # new: render, copy_of, new_incomplete, description
├── _evidence.py                       # _tasks_open asks _completion; RECORD shared with `tasks`
├── cli.py                             # step complete; step group help text
└── agents/commands/speckit.implement.md   # replaces step 9b; allowed-tools

tests/
├── test_completion_record.py          # new
├── test_pipeline_commands.py          # two tests write a record with a copy; new arms
├── test_storyctl.py                   # one test writes a record with a copy
├── test_pipeline_payload_snapshot.py  # one row gains a copy, one row added
└── pipeline_payload_snapshot.json     # regenerated
```

**Structure Decision**: The single-project layout the repository already has.
`_completion.py` sits beside `_verify.py` and `_plan_review.py`, which own the
other two records wfctl compares against a file's current state.

## Test Plan

Each row names the scenario it covers. New tests go in
`tests/test_completion_record.py` unless the row says otherwise. Every test
that expects `implement` to be current builds its feature with a keyed
`delivery.md`, the `KEYED_DELIVERY` text the snapshot test already uses, so
the `decompose` step does not stand in front of it.

| Test | Covers |
| --- | --- |
| A record round-trips a `tasks.md` holding ```` ``` ````, `~~~`, and `~~~~` fences | FR-004, SC-005, Story 2 #2 |
| A one-line record from before this change reads as having no copy | FR-007, level-3 Verification |
| No definition of done, copy with T001 ticked, live list adds T002: `implement` is current and the story is not complete | FR-005, FR-013, SC-002, Story 1 #1 |
| Same tree with a definition of done: `wfctl next` gives `/speckit.implement`, not `wfctl verify` (in `test_pipeline_commands.py`) | FR-010, SC-001, Story 1 #2 |
| T002 incomplete in the copy and in the live list, T003 added: only T003 is new | FR-005, Story 1 #3 |
| A new task inserted in the middle takes an old task's ID and still reads as new | FR-006, Story 1 #4 |
| `[P]` and `[USn]` tags change on an incomplete task: the step stays closed | FR-006, Clarification 1 |
| Ticking a box, adding a note under a task, and rewording a ticked task each leave the step closed | SC-003, Story 3 #1-3 |
| Rewording an incomplete task reopens the step | Story 3 #4 |
| A task ticked in the copy and incomplete now reopens the step | Edge case |
| Two incomplete tasks with the same description, one in the copy: one is new | FR-006, edge case |
| A task inside a code example, in the live list or the copy, is not counted | FR-009 |
| A task whose description holds an inline code span keeps the span's text | research R3 |
| Record with no copy and one incomplete task: `implement` is current | Story 4 #1 |
| Record with no copy and every task ticked: `implement` reads finished | Story 4 #2 |
| Record with or without a copy over a task list holding no task: `implement` finished, `tasks` `skipped` | FR-008, SC-004, Story 4 #3 |
| `decompose` agrees with `implement` on all three record shapes | SC-004 |
| No `delivery.md`, a record with a copy, and a new incomplete task: `decompose` is current and the next command is `/speckit.decompose` | Edge case, spec Edge Cases |
| `wfctl step complete implement` writes the record with a copy (in `test_pipeline_commands.py`) | FR-001, Story 2 #1 |
| `wfctl step complete plan` exits 1, names `implement`, writes nothing | FR-002, Story 2 #3 |
| `wfctl step complete implement` with no `tasks.md` exits 1, writes nothing | FR-003 |
| `wfctl step complete implement` while `analyze` is current exits 1, names `analyze`, writes nothing | FR-003a, Story 2 #4 |
| `wfctl step complete implement` with every box ticked and no definition of done writes the record | FR-003a, Story 2 #5 |
| A second run replaces the record and its copy | Edge case |
| The shipped implement command file names the command and lists it in `allowed-tools` (in `tests/test_skill_cross_references.py`, beside `test_implement_allows_the_commands_the_refactor_pass_needs`) | FR-011, Story 2 #6 |

The tests that change, and why each one still tests what it was written for:

| Test | Change |
| --- | --- |
| `test_storyctl.py::test_implement_done_when_sentinel_present` | Writes a record with a copy holding `t2` incomplete. It pins work done outside the skill, which now needs the copy to say `t2` was already open. |
| `test_pipeline_commands.py::test_the_sentinel_route_still_works_without_a_definition_of_done` | Same change, same reason. A new sibling pins the record with no copy reopening the step. |
| `test_pipeline_commands.py::test_the_sentinel_closes_the_tasks_even_with_a_box_left_open` | Same change. The routing it pins, `wfctl verify` with `auto: false`, is unchanged for a record with a copy. |
| `test_pipeline_payload_snapshot.py`, row `tasks-open-but-implemented` | Today the row has no analysis report or delivery plan, so it stops at `analyze` and the change cannot move it. It is rebuilt from `_ANALYZED` plus a keyed `delivery.md`, keeping its record with no copy, and its verdict moves from finished to `implement` in progress. A new row, `tasks-open-implemented-with-copy`, is built the same way with a copy holding the open box, and carries the old verdict. |
| `tests/pipeline_payload_snapshot.json` | Regenerated. The commit message names the one verdict that moved. |

`test_tasks_hold_a_task.py::test_the_implementation_sentinel_passes_by_a_task_free_tasks_step`
keeps passing unchanged, since a task list with no task still closes under
any record.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Gates drawn from `AGENTS.md` and the accepted records | The repository has no constitution | Borrowing another project's gates would be false, and dropping the gates would leave none |
