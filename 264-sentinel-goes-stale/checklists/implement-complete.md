Implementation complete: 2026-10-09

## Tasks at completion

~~~~markdown
# Tasks: A new task reopens the `implement` step

**Input**: Design documents from `/Users/andremarin/Development/wfctl-specs/264-sentinel-goes-stale/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Every story carries tests. The suite is the definition of done, and
FR-013 asks for the no-definition-of-done arm by name. Tests that assert on
console output pin `NO_COLOR`, carry sentence names, and say in their
docstrings which failure they catch.

**Design records**: `docs/architecture/design/264-the-task-copy-lives-in-the-completion-record.md`
and `docs/architecture/design/264-the-completion-command-is-a-step-verb.md`.
The level-2 decision is `docs/architecture/new-task-reopens-implement.md`.

**Plan review**: no BLOCKER is open. The eight MINOR findings still open in
`plan-review.md` are carried here, each by the task that names it.

**Delivery plan in fixtures**: every test that expects `implement` to be
current builds its feature from `_ANALYZED` in
`tests/test_pipeline_payload_snapshot.py` plus `KEYED_DELIVERY`, so the
`decompose` step does not stand in front of it. Without a delivery plan, a
reopened story goes to `/speckit.decompose` first, and one test pins that.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US4)

---

## Phase 1: Setup

**Purpose**: Confirm the baseline the change starts from.

- [X] T001 Run `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` on the branch before any code change, and note the test count, so a later failure is known to be this change's

---

## Phase 2: Foundational (the completion record's format)

**Purpose**: `wfctl/_completion.py` owns the record's format, the writer and
the reader together, as the level-3 record requires. Stories 1, 2, 3, and 4
all depend on it.

**Dependency direction (plan review PR-004)**: `_evidence` imports
`_completion`. `_completion` imports `_md` and the standard library only, and
never `_evidence`. Where it needs the quoted-out text of a task list, the
caller passes it in as an argument alongside the raw text.

- [X] T002 [P] Write failing round-trip tests in `tests/test_completion_record.py`: render a record from a `tasks.md` holding ```` ``` ````, `~~~`, and `~~~~` fences and read the copy back byte for byte (FR-004, SC-005); a `~~~~~~` line inside a backtick block does not cut the copy short (PR-003); a `tasks.md` with no final newline reads back with one added (research R5); a one-line record from before this change reads as having no copy; a record whose heading has no fenced block after it reads as having no copy
- [X] T003 [P] Write failing description tests in `tests/test_completion_record.py`: the first checkbox, the ID right after it, and the `[P]` and `[USn]` tags right after the ID are removed; a later `T012` in the text is kept; whitespace collapses and the ends are stripped; an inline code span keeps its text, so "Add `foo`" and "Add `bar`" differ (research R3); a line whose first box is ticked and a later box is incomplete reads as incomplete (PR-005)
- [X] T004 Create `wfctl/_completion.py` with `RECORD = Path("checklists") / "implement-complete.md"`, `render(tasks_text, today)`, and `copy_of(record_text)`; the fence is tildes, at least four long, and one longer than the longest marker, backtick or tilde, that `_md.opens_fence` matches on any line of the copy (FR-004), read line by line rather than through a walk so a tilde line nested inside a backtick block still counts (PR-003); the opener carries the info string `markdown`; `copy_of` finds `## Tasks at completion` outside any fence with `_md.walk` and returns the next block's lines joined with one final newline, or `None`; verify with T002
- [X] T005 Add the task reading to `wfctl/_completion.py`: `description(raw_line)` per research R2 and R3, and `new_incomplete(live_raw, live_quoted, copy_raw, copy_quoted)` returning the `Counter` difference of incomplete descriptions, where a task is a line whose quoted-out form holds a box and it is incomplete when any box on the line is `[ ]` (PR-005); verify with T003
- [X] T006 Validate Phase 2 with `uv run pytest -q tests/test_completion_record.py`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: The format round-trips and tasks match by description.

---

## Phase 3: User Story 1 - A story that gains a task after it finished is sent back to implement (Priority: P1) 🎯 MVP

**Goal**: A new incomplete task reopens `implement`, with or without a
definition of done.

**Independent Test**: Build a feature whose completion record holds a copy
with T001 ticked, then add an incomplete T002 to `tasks.md`. `wfctl status`
and `wfctl next` give `implement` as current and `/speckit.implement` as next,
with a definition of done configured and without one.

**Verification**:

- Automated: `tests/test_completion_record.py`, `tests/test_pipeline_commands.py`, `tests/test_storyctl.py`, `tests/test_pipeline_payload_snapshot.py`
- Manual: quickstart.md § Without a definition of done, § With a definition of done
- Evidence: `implement ▶ 1/2 done ← current` and `next: /speckit.implement` in both arms

### Tests for User Story 1

- [X] T007 [US1] Write failing tests in `tests/test_completion_record.py`: with no definition of done, a copy with T001 ticked, and a live list adding an incomplete T002, `implement` is current with `1/2 done`, the story is not complete, and the next command is `/speckit.implement` (FR-005, FR-010, FR-013, SC-001, SC-002, Story 1 #1); with T002 incomplete in the copy and the live list and T003 added, only T003 is new (Story 1 #3); a new task inserted in the middle that takes an old task's ID reads as new (FR-006, Story 1 #4); a `[P]` or `[USn]` tag change on an incomplete task leaves the step closed (Clarification 1); two incomplete tasks sharing a description where the copy held one reopen the step (FR-006); a task inside a code example in the live list or the copy is not counted (FR-009)
- [X] T008 [US1] Write a failing test in `tests/test_completion_record.py` that pins the limit: with no `delivery.md`, a copy with T001 ticked, and a new incomplete T002, `decompose` is current and the next command is `/speckit.decompose`
- [X] T009 [P] [US1] Write a failing test in `tests/test_pipeline_commands.py`: the Story 1 tree with a definition of done configured gives `/speckit.implement` from `wfctl next`, not `wfctl verify` (FR-010, SC-001, Story 1 #2)

### Implementation for User Story 1

- [X] T010 [US1] Change `_tasks_open` in `wfctl/_evidence.py`: with no record, behave as today; with a record and no task in the list, return closed (FR-008); with a record and no copy, return whether any task is incomplete (FR-007); with a copy, return whether `_completion.new_incomplete` holds anything (FR-005); read no modification time (FR-012); replace the two `"checklists" / "implement-complete.md"` literals in `_tasks_open` and the `tasks` reader with `_completion.RECORD`; update the docstring to say the record now carries a copy; verify with T007 and T008
- [X] T011 [US1] Change `test_storyctl.py::test_implement_done_when_sentinel_present` in `tests/test_storyctl.py` to write a record whose copy holds `t2` incomplete, since work done outside the skill now needs the copy to say `t2` was already open; verify with `uv run pytest -q tests/test_storyctl.py`
- [X] T012 [US1] Change `test_the_sentinel_route_still_works_without_a_definition_of_done` and `test_the_sentinel_closes_the_tasks_even_with_a_box_left_open` in `tests/test_pipeline_commands.py` to write a record with a copy holding the open box, and add a sibling test that a record with no copy over the same tree reopens the step; verify with T009 and `uv run pytest -q tests/test_pipeline_commands.py`
- [X] T013 [US1] In `tests/test_pipeline_payload_snapshot.py`, rebuild row `tasks-open-but-implemented` from `{**_ANALYZED, "delivery.md": KEYED_DELIVERY, **SENTINEL}` so it reaches `implement`, and add row `tasks-open-implemented-with-copy` built the same way with a record whose copy holds the open box (plan review PR-002)
- [X] T014 [US1] Regenerate `tests/pipeline_payload_snapshot.json` with the command in the docstring of `tests/test_pipeline_payload_snapshot.py`, confirm the diff changes only the two `tasks-open-but-implemented` entries, the tracker one and the `(no tracker)` one, and adds the two entries of the new row. The committed snapshot holds the old row stopped at `analyze`, and T010 lands before T013, so those entries move from `analyze`, `decompose`, and `implement` all `pending` to `implement` `in_progress`, rather than from finished. Name in the commit message the verdict the rebuilt fixture would have read under the old rule, finished, and the one it reads now; verify with `uv run pytest -q tests/test_pipeline_payload_snapshot.py`
- [X] T015 [US1] Validate Phase 3 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: A copy-bearing record no longer hides new work. Records are
still written by hand until Phase 4.

---

## Phase 4: User Story 2 - The implement step writes its completion record through wfctl (Priority: P1)

**Goal**: `wfctl step complete implement` writes the record with a copy, and
the implement command tells the agent to run it.

**Independent Test**: In a feature with a `tasks.md`, run `wfctl step
complete implement`, then read `checklists/implement-complete.md`. It holds
the completion line and a copy of `tasks.md` that reads back byte for byte.

**Verification**:

- Automated: `tests/test_pipeline_commands.py`, `tests/test_skill_cross_references.py`
- Manual: `uv run wfctl install-skills`, then read `.agents/commands/speckit.implement.md` and confirm the instruction and the allowed tool; `uv run wfctl step --help` lists `complete` beside `none` and `sign-off`
- Evidence: the success line from contracts/cli.md, and exit 1 with nothing written for each refusal

### Tests for User Story 2

- [X] T016 [US2] Write failing tests in `tests/test_pipeline_commands.py`, each pinning `NO_COLOR`: `wfctl step complete implement` writes the record with a copy and prints the tally of the copy (FR-001, Story 2 #1); `wfctl step complete plan` exits 1, names `implement`, and writes nothing (FR-002, Story 2 #3); no feature directory for the branch exits 1 and writes nothing (contracts/cli.md); no `tasks.md` exits 1 and writes nothing (FR-003); `analyze` current exits 1, names `analyze`, and writes nothing (FR-003a, Story 2 #4); `decompose` current with no `delivery.md` exits 1 and names `decompose`; every box ticked with no definition of done writes the record (FR-003a, Story 2 #5); a second run replaces the record and its copy
- [X] T017 [P] [US2] Write a failing test in `tests/test_skill_cross_references.py`, beside `test_implement_allows_the_commands_the_refactor_pass_needs`, that the shipped `wfctl/agents/commands/speckit.implement.md` names `wfctl step complete implement` and lists `Bash(wfctl step complete*)` in `allowed-tools` (FR-011, Story 2 #6)

### Implementation for User Story 2

- [X] T018 [US2] Add `@step_app.command("complete")` in `wfctl/cli.py` per contracts/cli.md: refuse any step but `implement`; refuse when no feature directory resolves or it holds no `tasks.md`; call `build_report` and refuse unless `report.current` is `implement` or `None` (research R6); read `tasks.md` once and use that one text for the copy and the printed tally; write with `_io.write_atomic` (plan review PR-007); widen the `step_app` help text to the contract's wording; verify with T016
- [X] T019 [US2] In `wfctl/agents/commands/speckit.implement.md`, add `Bash(wfctl step complete*)` to `allowed-tools`, and add a section telling the agent to run `wfctl step complete implement` in place of writing the file at step 9b; on a refusal the agent stops and reports the message, and writing the file by hand is not a fallback (plan review PR-006); reword both passages that call step 9b a sentinel so they name the command, the one in the code-pass section ("The step 9b sentinel is no later point") and the one on spec-kit's `after_implement` hook ("after the sentinel and after `wfctl verify`"); do not edit `wfctl/agents/skills/speckit-implement/SKILL.md` (FR-011); verify with T017
- [X] T020 [US2] Run `uv run wfctl install-skills`, read the installed implement command, and run `uv run wfctl step --help` to check that `complete`, `none`, and `sign-off` read as one family
- [X] T021 [US2] Validate Phase 4 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: The record is written by wfctl, with its copy, at the one
moment the old task list still exists.

---

## Phase 5: User Story 3 - Ordinary edits leave a finished story finished (Priority: P2)

**Goal**: Ticking a box, adding a note, and rewording a ticked task leave
`implement` finished.

**Independent Test**: Start from a finished story whose copy matches
`tasks.md`, apply each edit in turn, and confirm `implement` still reads
finished after each one.

**Verification**:

- Automated: `tests/test_completion_record.py`
- Manual: quickstart.md § Ordinary edits
- Evidence: `implement` reads finished after each of the three edits

- [X] T022 [US3] Write tests in `tests/test_completion_record.py`: ticking a box that was incomplete in the copy, adding a note line under a task, and rewording a ticked task each leave the step closed (SC-003, Story 3 #1-3); rewording an incomplete task reopens it (Story 3 #4); a task ticked in the copy and incomplete now reopens it (edge case); verify with `uv run pytest -q tests/test_completion_record.py`, which passes on T010 with no further code
- [X] T023 [US3] Validate Phase 5 with `uv run pytest -q` — merge gate

---

## Phase 6: User Story 4 - Completion records written before this change still read safely (Priority: P2)

**Goal**: A record with no copy reads in a defined, safe way, and the `tasks`,
`decompose`, and `implement` readers agree on it.

**Independent Test**: Build a feature with a one-line completion record. Read
`wfctl status` with an incomplete task, with every task ticked, and with a
`tasks.md` holding no task.

**Verification**:

- Automated: `tests/test_completion_record.py`, `tests/test_tasks_hold_a_task.py`
- Evidence: `implement` current, finished, and finished with `tasks` `skipped`, in that order

- [X] T024 [US4] Write tests in `tests/test_completion_record.py`: a record with no copy and one incomplete task makes `implement` current with next `/speckit.implement` (Story 4 #1); a record with no copy and every task ticked reads finished (Story 4 #2); a record with or without a copy over a task list holding no task reads `implement` finished and `tasks` `skipped` (FR-008, SC-004, Story 4 #3); `decompose` agrees with `implement` on all three record shapes (SC-004); verify with `uv run pytest -q tests/test_completion_record.py`
- [X] T025 [US4] Confirm `test_tasks_hold_a_task.py::test_the_implementation_sentinel_passes_by_a_task_free_tasks_step` passes unchanged with `uv run pytest -q tests/test_tasks_hold_a_task.py`
- [X] T026 [US4] Validate Phase 6 with `uv run pytest -q` — merge gate

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Bring the written limit in line with the code, and reproduce
both arms by hand.

- [X] T027 [P] Add one sentence to § Consequences of `docs/architecture/new-task-reopens-implement.md` saying that a reopened story goes to `/speckit.decompose` first when its `decompose` step is not done, and that `implement` follows once it is (plan review PR-008); verify with `uv run wfctl arch check docs/architecture/new-task-reopens-implement.md` after the commit
- [X] T028 [P] In `research.md` § R1, bring the limit in line with `spec.md` § Edge Cases and `plan.md` § Summary item 2, which `/speckit.analyze` already corrected (PR-008, PR-009): replace "That claim holds for a feature with a delivery plan" with a feature whose delivery plan has every row keyed, or whose repository declares no tracker; say that a delivery plan with an unkeyed row under a configured tracker also sends a reopened story to `/speckit.decompose`; and stop the "22 of 22" sentence from implying that only new features reach the case; verify by reading it against the `decompose` reader in `wfctl/_evidence.py`
- [X] T029 After T028, since both edit `research.md`: in § R2, replace the sentence on lines with two boxes with the rule T005 implements, a line is incomplete when any of its boxes is (PR-005); in § R4 and in `data-model.md` § Completion record item 3, say the fence is one longer than the longest fence marker of either character, as T004 implements and FR-004 states; verify by reading them against T003 and T004
- [X] T030 [P] In `quickstart.md`, name the invocation as `uv run --project <worktree> wfctl` run from the scratch repository, and point the set-up step at `REVIEWED` and `_ANALYZED` in `tests/test_pipeline_payload_snapshot.py` rather than at `spec_tree` (PR-010); verify with T031
- [X] T031 Run every section of `quickstart.md` by hand in a scratch repository, both arms included, and record the `wfctl status` and `wfctl next` output for each in the PR's evidence
- [X] T032 Run `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, and `uv run wfctl doctor` — merge gate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none.
- **Foundational (Phase 2)**: after Setup. Blocks every story.
- **US1 (Phase 3)**: after Phase 2.
- **US2 (Phase 4)**: after Phase 2. Its tests read the record T010 reads, so
  it runs after US1 when one person does both.
- **US3 (Phase 5)** and **US4 (Phase 6)**: after T010. Both are tests over
  behavior US1 already built.
- **Polish (Phase 7)**: T027 to T030 any time after Phase 3; T031 after
  Phase 4; T032 last.

### Within Each Story

- Tests are written first and fail before the implementation task they name.
- T013 comes before T014, since the snapshot is regenerated from the new rows.
- T019 comes before T020, since the install reads the edited command file.

### Parallel Opportunities

- T002 and T003 are both in `tests/test_completion_record.py` but cover
  separate functions, so two people can write them if they merge carefully.
- T009 and T017 are in files no other task in their phase touches.
- T027, T028, and T030 each edit a different file. T029 follows T028,
  since both edit `research.md`.

## Parallel Example: User Story 1

```bash
Task: "T007 failing reopen tests in tests/test_completion_record.py"
Task: "T009 failing definition-of-done routing test in tests/test_pipeline_commands.py"
```

## Implementation Strategy

### MVP First (User Story 1 and User Story 2)

Stories 1 and 2 are both P1, and neither is useful alone: the reader has
nothing to compare against until the command writes a copy, and the copy
changes nothing until the reader uses it. So the MVP is Phases 2, 3, and 4
together. Stop after T021 and run quickstart.md's two arms.

### Incremental Delivery

1. Phase 2: the format and the matching, tested on their own.
2. Phase 3: the reader. A record written by hand still has no copy, so it
   reopens any story with an incomplete task, which is the safe direction.
3. Phase 4: the command and the instruction. From here a finished story
   carries a copy.
4. Phases 5 and 6: the edits that must not reopen, and the old records.
5. Phase 7: the written limit, the quickstart, and the full check.
~~~~
