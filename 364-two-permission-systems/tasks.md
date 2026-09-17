# Tasks: two permission systems

**Input**: Design documents from `specs/364-two-permission-systems/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md

**Tests**: Required. This feature changes what the pipeline reports about a run's
completeness, which is critical-path logic, and adds a command whose whole
correctness claim is that it consults no authority gate. Every task below names
a verification path.

**Organization**: Grouped by user story. Phase 2 is the shared event layer both
P1 and P2 read; P3 touches nothing either of them touch and can be built in any
order relative to them.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3 — maps to the user stories in `spec.md`
- Exact file paths in every description
- Every implementation task names a verification path or is paired with one

## Path Conventions

Single project, flat package: `wfctl/` and `tests/` at the repository root. The
skills tree under `wfctl/agents/` is package data — installed, not imported.

All commands run through `uv run`, per `AGENTS.md`: the dev deps are pinned on
purpose and `uv run` is what applies the pin.

---

## Phase 1: Setup

**Purpose**: Establish the baseline this change is measured against.

- [X] T001 Record the pre-change baseline: run `uv run pytest -q`, `uv run ruff check wfctl/ tests/` and `uv run mypy wfctl/`, and note the passing test count; verify by all three exiting 0 before any file is edited

No project initialization. The package, its dependencies and its test suite all
exist; this feature adds no dependency and creates no module.

**Checkpoint**: Baseline green and its count written down. A suite that was
already red would otherwise be attributed to this change.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The event layer both US1 and US2 read and write. Neither story can
be built without it.

**⚠️ CRITICAL**: US1 and US2 are blocked on this phase. US3 is not — it touches
no event and can proceed in parallel from T001.

- [X] T002 [P] Add `record_blocked(agent_dir, action, reason, step)` to `wfctl/_session.py`, a single `append_event(agent_dir, "blocked", action=…, reason=…, step=…)` call placed beside the three `notify-*` writers it matches; verify with `tests/test_blocked_events.py::test_a_block_event_carries_the_step_it_was_reported_on`
- [X] T003 [P] Add `record_block_cleared(agent_dir, action)` to `wfctl/_session.py`, a single `append_event(agent_dir, "block-cleared", action=…)` call; verify with `tests/test_blocked_events.py::test_a_clearing_event_carries_no_reason_and_no_step`
- [X] T004 Add `standing_blocks(agent_dir, branch)` to `wfctl/_session.py`, keeping the last event per `action` across `blocked`, `block-cleared` and `notify-action` and returning only the actions whose latest event is a `blocked` (FR-012); skip malformed lines rather than raising, as `resolved_notify` does; verify with `tests/test_blocked_events.py::test_the_most_recent_event_for_an_action_is_the_one_that_stands`
- [X] T005 Scope `standing_blocks` to the branch it is asked about (FR-021), following `resolved_notify`'s rule that a state dir shared across worktrees holds every branch's events; verify with `tests/test_blocked_events.py::test_a_block_on_one_branch_does_not_hold_a_step_on_another`
- [X] T006 Write `tests/test_blocked_events.py` covering T002–T005, including a truncated final line that must be skipped rather than crash the reader; verify with `uv run pytest -q tests/test_blocked_events.py`
- [X] T007 Validate Phase 2 with `uv run pytest -q tests/test_blocked_events.py && uv run mypy wfctl/` — merge gate

**Checkpoint**: The event layer reads and writes correctly. Nothing in the CLI or
the pipeline knows about it yet, and `wfctl status` is unchanged.

---

## Phase 3: User Story 1 — The refusal leaves a trace, and the step stops (Priority: P1) 🎯 MVP

**Goal**: An agent whose tracker write was refused by its host can record that
fact with no grant, and the step that owned the write stops reporting as
finished.

**Independent Test**: Record a block for an action belonging to a completed step,
then read the pipeline. The step reports held with the reason attached, and the
event survives a new session.

**Verification**:

- Automated: `tests/test_blocked_cli.py`, `tests/test_blocked_holds_step.py`
- Manual: on this worktree, `uv run wfctl blocked issue-comment --reason "host classifier: External System Writes"`, then `uv run wfctl status` — `plan` reports held; then `uv run wfctl blocked issue-comment --clear` to restore
- Evidence: a `blocked` line in `$(wfctl state-dir)/events.jsonl`, and a `status` payload whose held step carries `state: in_progress` with the reason

### Tests for User Story 1 ⚠️

> Write these first and confirm they fail before implementing T011–T015.

- [X] T008 [P] [US1] Write `tests/test_blocked_cli.py::test_a_run_holding_no_grant_can_still_report_a_block` — the case the rejected `--blocked`-on-notify baseline fails, stated as a test rather than as an argument; asserts exit 0 and the event written
- [X] T009 [P] [US1] Write `tests/test_blocked_cli.py::test_notify_still_refuses_a_run_holding_no_grant` — pins that this feature did not widen the gate it declined to reopen; asserts `wfctl notify` exits 1 on the same branch
- [X] T010 [P] [US1] Write `tests/test_blocked_holds_step.py::test_a_block_holds_a_step_whose_own_artifacts_read_done` — the whole claim of the level-2 record, and the assertion that fails if the hold is ever wired as a predicate `implement` alone consults; asserted on the `--json` payload
- [X] T010a [P] [US1] Write `tests/test_blocked_cli.py::test_no_spelling_of_blocked_records_a_success` — FR-009, which is the narrow exception to `wfctl-runs-the-verification` stated as a property of the surface rather than as prose an agent has to have read; assert against the command's own parameter set that the only outcomes it can record are a block and a clearing, so a success-shaped mode added later fails this test instead of shipping quietly. Lettered rather than appended: every later ID is cross-referenced from the dependency graph and the phase checkpoints

### Implementation for User Story 1

- [X] T011 [US1] Add `@app.command("blocked")` to `wfctl/cli.py` with positional `action`, `--reason` and `--clear`, resolving context the way `notify_cmd` does but **never calling `action_grant`** (FR-006); verify with `tests/test_blocked_cli.py::test_a_run_holding_no_grant_can_still_report_a_block`
- [X] T012 [US1] In that command, take the held step from `build_report` at call time rather than from the caller (FR-010) — the agent supplies the two facts it witnessed and never names the step; verify with `tests/test_blocked_cli.py::test_the_step_comes_from_inference_not_from_the_caller`
- [X] T013 [US1] Refuse the report with exit 1 and store nothing when neither `--reason` nor `--clear` is given (FR-007), and refuse the two together — the requirement is on the reporting mode only, and a literal reading that demands `--reason` in every mode breaks the `--clear` mode T023 builds, which `contracts/cli.md` gives exit 0 always; verify with `tests/test_blocked_cli.py::test_a_block_with_no_reason_is_refused_and_stores_nothing`
- [X] T014 [US1] Store the report and say plainly that no step is held when the branch has no feature (FR-008), writing `step: null`; verify with `tests/test_blocked_cli.py::test_a_branch_with_no_feature_still_stores_the_report`
- [X] T015 [US1] Add `block_reason(agent_dir, branch, step) -> str | None` to `wfctl/_predicates.py`, shaped after `verification_block` at `wfctl/_predicates.py:506` — first matching reason or `None`; verify with `tests/test_blocked_holds_step.py::test_block_reason_answers_for_the_step_the_block_named`
- [X] T016 [US1] Apply the hold in `build_report` (`wfctl/_pipeline.py`) **after** `_infer_steps` returns, never inside its loop — that loop sets `cascade = True` on the first `pending` step, so a hold injected mid-loop would force legitimately-`done` later steps to `pending`; verify with `tests/test_blocked_holds_step.py::test_holding_a_done_step_does_not_cascade_the_steps_after_it`
- [X] T017 [US1] Set the held step's `state` to `in_progress` with the reason on its `annotation` and `reason` fields, adding no new state name and no new payload key (FR-018); verify with `tests/test_blocked_holds_step.py::test_a_held_step_adds_no_new_state_name_and_no_new_payload_key`
- [X] T018 [US1] Assert the payload snapshot in `tests/pipeline_payload_snapshot.json` is unchanged for a run with no block (SC-006); verify with `uv run pytest -q tests/test_pipeline_payload_snapshot.py`
- [X] T019 [US1] Add the instruction to report a block to the skills that drive the pipeline, under `wfctl/agents/skills/` (FR-017); verify by running `uv run wfctl install-skills` from this working tree and reading the installed instruction as an agent would — `AGENTS.md` states the suite checks that skills ship and cross-reference, not that they read well
- [X] T020 [US1] Validate Phase 3 with `uv run pytest -q tests/test_blocked_cli.py tests/test_blocked_holds_step.py && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` — merge gate

**Checkpoint**: A refused run leaves a trace and stops the pipeline. Releasing the
hold is possible only through a later successful `notify-action`, which is the
gap US2 closes.

---

## Phase 4: User Story 2 — A person reads what the run did not do, and releases it (Priority: P2)

**Goal**: The pipeline tells a person what was refused, that re-running will not
help, and what only they can do about it — and that release is reachable from a
run holding no grant.

**Independent Test**: With a block standing, read the pipeline and follow only
what it printed. The reader can name the refused action, understands that
re-running the step will not help, and can release the hold.

**Verification**:

- Automated: `tests/test_blocked_holds_step.py` (release paths), `tests/test_blocked_cli.py` (`--clear` mode)
- Manual: the two-command loop in `quickstart.md` — block, read `status`, clear, read `status` again
- Evidence: a `block-cleared` line in `events.jsonl`, and a `status` payload whose previously-held step reports from its own artifacts again

### Tests for User Story 2 ⚠️

- [X] T021 [P] [US2] Write `tests/test_blocked_cli.py::test_clearing_works_for_a_run_holding_no_grant` — the path `notify-action` cannot reach, and the one the level-3 record's first shape left unreachable
- [X] T022 [P] [US2] Write `tests/test_blocked_holds_step.py::test_a_later_success_for_the_same_action_releases_the_hold` and its reverse-order sibling `test_a_block_after_a_success_holds_again` (FR-012, FR-020)

### Implementation for User Story 2

- [X] T023 [US2] Implement the `--clear` mode of `wfctl blocked` in `wfctl/cli.py`, ungated for the reason `AGENTS.md` § Safety gives for `wfctl issue close` — a gate there would refuse the only actor allowed to run it (FR-013); verify with `tests/test_blocked_cli.py::test_clearing_works_for_a_run_holding_no_grant`
- [X] T024 [US2] Say there was nothing to clear, change nothing and exit 0 when no block stands for that action (FR-014) — a person who mistypes the action otherwise reads a clean exit as a release that did not happen; verify with `tests/test_blocked_cli.py::test_clearing_an_action_with_no_block_standing_says_so`
- [X] T025 [US2] Build the held step's `remedy` in `wfctl/_pipeline.py` beside `_design_remedy`, stating that the host refused it rather than wfctl, that re-running will be refused again, and that a person takes the action then records it (FR-015); verify with `tests/test_blocked_holds_step.py::test_the_remedy_names_the_host_and_the_clearing_command`
- [X] T026 [US2] Keep the held step's `next_command` as the step's own command, never the clearing command (FR-016) — a `next` naming the release would tell an unattended agent to clear its own hold; verify with `tests/test_blocked_holds_step.py::test_the_next_action_for_a_held_step_is_the_steps_own_command`
- [X] T027 [US2] Render the remedy in the console arm of `status_cmd` (`wfctl/cli.py`) the way the design block's remedy is rendered, with `escape()` applied for the reason the existing remedy escapes; verify with `tests/test_console_plaintext.py` extended for a held step, `NO_COLOR` pinned as `conftest.py` requires
- [X] T028 [US2] Validate Phase 4 with `uv run pytest -q tests/test_blocked_cli.py tests/test_blocked_holds_step.py tests/test_console_plaintext.py && uv run mypy wfctl/` — merge gate

**Checkpoint**: A held run is both legible and recoverable. US1 and US2 together
are the feature; US3 is independent of both.

---

## Phase 5: User Story 3 — The authority report stops overstating what it knows (Priority: P3)

**Goal**: Every run says that a second permission layer exists and that wfctl
neither sees it nor speaks for it, and the irreversible line names the whole class
it implements rather than half of it.

**Independent Test**: Read the authority report in each grant state. The new line
is present and true in every one, and the irreversible line names every action in
its class.

**Verification**:

- Automated: `tests/test_notify_status.py`, extended
- Manual: `uv run wfctl status` on this worktree — both lines print under the branch header
- Evidence: the two strings in all eight renderings, asserted by a loop rather than eight separate assertions

### Tests for User Story 3 ⚠️

- [X] T029 [P] [US3] Write `tests/test_notify_status.py::test_the_second_permission_layer_is_named_in_every_grant_state` — a loop over the seven `_NOTIFY_LINES` keys plus the `label` rendering `_notify_line` builds rather than looks up, which `research.md` establishes is eight renderings, not seven
- [X] T030 [P] [US3] Write `tests/test_notify_status.py::test_the_new_line_names_no_command` (FR-003) — an agent needs `wfctl blocked` mid-run, long after it last read this block, so naming it here puts it in the one place the reader is guaranteed not to be looking

### Implementation for User Story 3

- [X] T031 [P] [US3] Reword `_IRREVERSIBLE_NOTICE` at `wfctl/cli.py:197` to name merging, force-pushing, closing an issue, and deleting a branch or worktree (FR-004) — two of the four were missing; verify with `tests/test_notify_status.py::test_the_irreversible_line_names_every_action_in_its_class`
- [X] T032 [US3] Add the new module constant for FR-001 beside `_IRREVERSIBLE_NOTICE` and print it unconditionally at the same call site (`wfctl/cli.py:478`), keyed on nothing (FR-002) — it is true in every grant state, and a console line rather than a fact row, which FR-018 forbids; verify with `tests/test_notify_status.py::test_the_second_permission_layer_is_named_in_every_grant_state`
- [X] T033 [US3] Confirm no `facts` row and no payload key was added by this phase (FR-018, SC-006); verify with `uv run pytest -q tests/test_four_facts.py`
- [X] T034 [US3] Validate Phase 5 with `uv run pytest -q tests/test_notify_status.py tests/test_four_facts.py && uv run ruff check wfctl/ tests/` — merge gate

**Checkpoint**: All three stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T035 [P] Run the `quickstart.md` walkthrough end to end on this worktree and correct any wording that does not match what the commands actually print; verify by the printed output matching the document line for line
- [X] T036 Answer the level-3 record's review question: does `uv run wfctl --help` read as though `notify` and `blocked` are alternatives? If it does, the consequence the record names has landed and the help text owes the reader the grant; verify by reading the output and recording the answer in the PR description
- [ ] T037 [P] Move `docs/architecture/the-agent-reports-the-block-wfctl-never-saw.md` and `docs/architecture/design/364-the-block-report-is-its-own-verb.md` from `proposed` to `accepted` with `uv run wfctl arch accept <slug> --agreed "<where the human agreed>"` — the citation is a person's, and this task is theirs to run rather than the implementing agent's; verify with `uv run wfctl arch check` green and the `architecture accepted` fact reading met in `uv run wfctl status`
- [X] T038 Run the definition of done: `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/`, then `uv run wfctl verify` to record the verdict against the tree it ran on — merge gate
- [X] T039 Run `uv run wfctl doctor` from this working tree and confirm green; `AGENTS.md` requires `uv run` here specifically, because a bare `wfctl` compares against a different bundle and the two never both report clean

---

## Dependencies & Execution Order

```
T001  Setup
  │
  ├──────────────────────────────────────────┐
  ▼                                          ▼
Phase 2  Foundational (T002-T007)      Phase 5  US3 (T029-T034)
  │                                      independent of the event layer
  ├───────────────┐
  ▼               │
Phase 3  US1      │
(T008-T020)       │
  │               │
  ▼               │
Phase 4  US2 ◄────┘
(T021-T028)
  │
  ▼
Phase 6  Polish (T035-T039)
```

### Phase dependencies

- **Setup (T001)**: no dependencies
- **Foundational (T002–T007)**: depends on T001; blocks US1 and US2
- **US1 (T008–T020)**: depends on Foundational
- **US2 (T021–T028)**: depends on US1 — its release paths are asserted against the hold US1 builds
- **US3 (T029–T034)**: depends on T001 only. It touches `_IRREVERSIBLE_NOTICE` and one new constant, neither of which the event layer reads
- **Polish (T035–T039)**: depends on every story intended for the change

### Within each story

- Tests written and failing before the implementation tasks they verify
- Writers before readers: `record_blocked` before `standing_blocks` before `block_reason`
- The predicate before the hold; the hold before the remedy that renders it

### Parallel opportunities

- T002 and T003 — two independent functions in `_session.py`
- T008, T009, T010, T010a — three test files, no shared fixture
- T021 and T022 — different test files
- T029, T030, T031 — two test additions and one constant reword
- T035 and T037 — a walkthrough and a record status change, touching nothing in common
- **US3 in parallel with everything.** It is the one story that shares no file
  region with the other two, and it is what the issue asked for in its own words

## Logical PR boundaries

Three coherent slices, and the phases were sized to them:

| Slice | Phases | Why it stands alone |
|---|---|---|
| The event layer and the honest stop | 1, 2, 3 | Delivers User Story 1 whole. Merging it leaves a feature that records and holds but can only be released by a successful retry — incomplete, not broken |
| The release and the remedy | 4 | Closes the gap above. Depends on the first and cannot be demonstrated without it |
| The two authority lines | 5 | Touches one constant and adds another, in one file, with one test file. Independently demonstrable and independently revertible |

`/speckit.decompose` decides whether these become one PR or three. This section
is the signal it reads, not the decision.

## Implementation strategy

**MVP is Phases 1–3.** User Story 1 is the failure this feature exists for: a
refused run and a successful one leave byte-identical state on disk. Everything
after it makes that stop legible and recoverable, which is worth having and is
not what was broken.

**US3 first if the change needs to ship something today.** It is what #364 asked
for in its own words, it is true whether or not any of the rest is built, and it
costs one reworded string and one new one.

**#297 changes what this is worth, not whether it works.** It moves the
issue-splitting decision to brainstorm, which removes the only outward action in
an unattended run that genuinely cannot be survived. If it lands first, this
feature's value is entirely the trace and none of it is the stop.
