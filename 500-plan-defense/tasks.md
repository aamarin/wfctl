---
description: 'Task list for plan-walkthrough (#500)'
---

# Tasks: plan-walkthrough

**Input**: Design documents from `/Users/andremarin/Development/wfctl-specs/500-plan-defense/`
**Prerequisites**: plan.md, spec.md, research.md (R1 - R9), data-model.md, contracts/declaration-and-payload.md, contracts/plan-walkthrough-command.md, quickstart.md

**Tests**: Every change to `wfctl/` code has a unit test written first. The
skill's behavior is not covered by the suite (`AGENTS.md`), so Stories 1, 3,
and 4 each end with the manual run named in `quickstart.md`.

**Organization**: One phase per user story, in the spec's priority order. The
core change (`needs_person`) and the skill are independent of each other, so
Story 1 and Story 2 can proceed in parallel after Phase 2.

**Design records**: `design.md` lists one,
`docs/architecture/design/autonomous-skip-is-a-claim.md`, whose status is
`rejected`. No task implements it. The level-2 records that bind this work are
`autonomous-agent-skips-human-checks` and `plan-walkthrough-is-private`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: which user story the task belongs to (US1 - US5)

## Path Conventions

Single project: `wfctl/` and `tests/` at the repository root
(`/Users/andremarin/Development/wfctl/wt/500-plan-defense`). Every command runs
through `uv run`.

---

## Phase 1: Setup

**Purpose**: Confirm the branch starts green, so a later failure is this
feature's.

- [X] T001 Run `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` on the branch head and record the pass count in the session summary; verify all three exit 0

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Carry `needs_person` from a declaration to the pass objects, with no
change to any reading yet. Stories 2, 3, and 5 depend on this phase.

- [X] T002 Write failing tests in `tests/test_declared.py`: a declared pass with `"needs_person": true` loads with `SubStep.needs_person is True`; a pass without the key loads with `False`; every built-in pass has `False`
- [X] T003 Add `needs_person: bool = False` to `SubStep` in `wfctl/_pipeline.py:49` and to `_PipelineSubStep` in `wfctl/_pipeline.py:225`, passing it through every place `_pass_states` constructs a `_PipelineSubStep` (`wfctl/_pipeline.py:400-419`); verify with `uv run mypy wfctl/`
- [X] T004 Parse `needs_person` in `_declared._load_step` (`wfctl/_declared.py:109-207`) and pass it to the `SubStep` constructed at `wfctl/_declared.py:201-203`; verify with the T002 tests
- [X] T005 Validate Phase 2 with `uv run pytest -q tests/test_declared.py tests/test_pipeline*.py` and `uv run mypy wfctl/` — merge gate

**Checkpoint**: a declaration carries `needs_person` into the pipeline, and no
pass reads differently yet.

---

## Phase 3: User Story 1 - A person walks through their plan in private (Priority: P1) 🎯 MVP

**Goal**: wfctl ships the `plan-walkthrough` skill and the `/plan-walkthrough`
command. An attended run asks one question per turn, writes the answers to the
state directory, and writes evidence with no answers to the feature directory.

**Independent Test**: Run `/plan-walkthrough` in plan mode on a scratch branch
with a `plan.md`, answer the questions, and confirm the answers file exists
under `$(wfctl state-dir)/walkthrough/`, `plan-walkthrough.md` exists in the
feature directory, and it holds only `Mode`, `Walked through`, and `Date`.

**Verification**:

- Automated: `tests/test_plan_walkthrough_skill.py`, `tests/test_skill_cross_references.py`
- Manual: `quickstart.md` § "A person comes back"
- Evidence: the answers file and the three-field marker (the evidence file)

### Tests for User Story 1

- [X] T006 [P] [US1] Write failing tests in `tests/test_plan_walkthrough_skill.py`: `wfctl/agents/skills/plan-walkthrough/SKILL.md` exists with `name: plan-walkthrough`; the skill directory holds no `agents/` subdirectory (FR-017); `references/` holds `artifact-contract.md`, `interrogation-lenses.md`, `question-quality.md`, `examples.md`, and `source-map.md`; `wfctl/agents/commands/plan-walkthrough.md` exists and points at the skill

### Implementation for User Story 1

- [X] T007 [US1] Copy `SKILL.md` and `references/*.md` from `/Users/andremarin/Development/wfctl/docs/plan-defense/` (read with Read or cat; never edit or run anything in that worktree) into `wfctl/agents/skills/plan-walkthrough/`, and do not copy `agents/openai.yaml`; verify with T006
- [X] T008 [US1] Rename throughout the copied skill: `plan-defense` to `plan-walkthrough`, "plan defense" to "plan walkthrough", "implementation ownership defense" to "change walkthrough", the `IMPLEMENTATION` mode to `CHANGE`, and "defend" to "explain" where it names what the person does; verify with `grep -rni "defen" wfctl/agents/skills/plan-walkthrough/` returning nothing
- [X] T009 [US1] Rewrite `wfctl/agents/skills/plan-walkthrough/references/artifact-contract.md` into two artifacts per `data-model.md`: the answers file at `$(wfctl state-dir)/walkthrough/<mode>-<YYYY-MM-DDTHH-MM-SS>.md` with every challenge, answer, disposition, and gap, and `Status: incomplete` when cut short; and the marker (the evidence file a declared pass reads) `plan-walkthrough.md` or `change-walkthrough.md` in the feature directory with exactly `Mode`, `Walked through`, and `Date`; verify by reading the file against `data-model.md` § Answers file and § Marker
- [X] T010 [US1] Rewrite the workflow in `wfctl/agents/skills/plan-walkthrough/SKILL.md` per `contracts/plan-walkthrough-command.md`: run `wfctl status --json` first and refuse while `auto_approve` is `true` with the contract's exact refusal text; resolve the mode (argument, then the current pass's step, then plan); get the destinations from `wfctl feature-paths` and `wfctl state-dir`; stop with no writes when plan mode has no `plan.md`; hash `plan.md` with `sha256sum`, or `shasum -a 256` where that is missing (R7); never answer a question for the person (FR-006) and never edit the plan, code, or records (FR-016); end by printing the outcome counts and the answers file's path; verify by reading the skill against the contract
- [X] T011 [US1] Replace the skill's "Route the result" and "Integration intent" sections, which describe gating `tasks` and a fixed place in the lifecycle, with one paragraph saying wfctl places the check nowhere by default and pointing to the `docs/reference.md` section that T029 writes (FR-003, FR-018); verify with `grep -n "stop advancement\|do not convert the plan\|\"evidence\": \"plan-walkthrough.md\"" wfctl/agents/skills/plan-walkthrough/SKILL.md` returning nothing, which also confirms the skill does not repeat the snippet (FR-018); the refusal text from T010 still names `needs_person`, which is expected
- [X] T012 [US1] Rewrite lenses 2, 3, 4, and 7 in `wfctl/agents/skills/plan-walkthrough/references/interrogation-lenses.md` to ask the person to explain what the architecture records, the `Considered` sections, the checked and assumed split, and verification already decided, without reopening those decisions, and move lens 11 (comprehension) to lead (FR-015); verify by reading the file against FR-015
- [X] T013 [US1] Write `wfctl/agents/commands/plan-walkthrough.md` in the shape of `wfctl/agents/commands/model-the-domain.md`, with `disable-model-invocation: true`, a one-line description, and the pointer to `.agents/skills/plan-walkthrough/SKILL.md`; verify with T006
- [X] T014 [US1] Run `uv run wfctl install-skills --prune --yes --agent claude`, then `uv run wfctl doctor`; verify doctor reports both layers current and `.agents/commands/plan-walkthrough.md` exists
- [X] T015 [US1] Validate Story 1 with `uv run pytest -q tests/test_plan_walkthrough_skill.py tests/test_skill_cross_references.py tests/test_install_skills.py` and the manual run in `quickstart.md` § "A person comes back" on a scratch branch — merge gate

**Checkpoint**: a person can run the walkthrough end to end, and the answers
never reach the feature directory.

---

## Phase 4: User Story 2 - An autonomous run skips the check and says so (Priority: P1)

**Goal**: While auto-approve is on and the evidence is absent, a pass declared
with `needs_person` reads `skipped` with the reason "needs a person;
auto-approve is on", and wfctl writes nothing.

**Independent Test**: With the pass declared and `auto_approve` on, `wfctl
status --json` shows the pass `skipped` with the reason, `next_command` names
the step after the pass, `attention` is `null`, and `git status` shows no new
file.

**Verification**:

- Automated: `tests/test_pipeline_needs_person.py`, `tests/test_status_contract.py`
- Manual: `quickstart.md` § "Unattended skip"
- Evidence: the `status --json` payload in `contracts/declaration-and-payload.md`

### Tests for User Story 2

- [X] T016 [P] [US2] Write failing tests in `tests/test_pipeline_needs_person.py` for `data-model.md` § Pass reading row 5: a `needs_person` pass with no evidence reads `skipped` with annotation "needs a person; auto-approve is on" when `auto_approve=True`; the pass after it is still read (no cascade, R1); `_outstanding_pass` returns `None` for it, so `next_command` moves past it
- [X] T017 [P] [US2] Write a failing test in `tests/test_pipeline_needs_person.py` that `build_report` emits `"needs_person": true` on the declared pass and `false` on every built-in pass

### Implementation for User Story 2

- [X] T018 [US2] Add a keyword argument `auto_approve: bool = False` to `_infer_steps` (`wfctl/_pipeline.py:264`) and `_pass_states` (`wfctl/_pipeline.py:365`), threading it from the first to the second at each call site (`wfctl/_pipeline.py:305`, `:325`, `:333`); verify with `uv run mypy wfctl/`
- [X] T019 [US2] In `build_report` (`wfctl/_pipeline.py:869`), read the approval mode once before `_infer_steps`, pass it in, and reuse the same value where `granted` is read today (`wfctl/_pipeline.py:922`) (R2); verify with the existing `tests/test_cli_status.py`
- [X] T020 [US2] In `_pass_states`, after `reading = sub.reads(ev)`: when the reading is not `done`, `sub.needs_person` is true, and `auto_approve` is true, append a `skipped` pass with the annotation "needs a person; auto-approve is on" and `continue` without setting `cascade` (R1); verify with T016
- [X] T021 [US2] Emit `"needs_person": sub.needs_person` beside `"manual"` in the sub-step dict in `build_report` (`wfctl/_pipeline.py:968-977`); verify with T017
- [X] T022 [US2] Add `"steps[].sub_steps[].needs_person": "boolean"` to `wfctl/contracts/status-payload.json` and bump the version from `1.0` to `1.1` with `uv run wfctl contract regenerate`, which also moves `STATUS_PAYLOAD_VERSION` (`wfctl/_pipeline.py:12`) (R5); verify with `uv run pytest -q tests/test_status_contract.py tests/test_contract_regenerate.py`
- [X] T023 [US2] Validate Story 2 with `uv run pytest -q` and `uv run mypy wfctl/` — merge gate

**Checkpoint**: an autonomous run passes the check by, says why, and leaves
nothing on disk.

---

## Phase 5: User Story 3 - A person comes back to a branch an autonomous run passed (Priority: P2)

**Goal**: With auto-approve off the pass is outstanding again, a person who
runs the walkthrough with auto-approve on is refused, evidence reads `done` in
both modes, and a claim wins in both modes.

**Independent Test**: After Story 2's test, run `wfctl start
--no-auto-approve`, confirm the pass reads `in_progress`, run
`/plan-walkthrough` attended, and confirm the pass reads `done`.

**Verification**:

- Automated: `tests/test_pipeline_needs_person.py`
- Manual: `quickstart.md` § "Refusal while auto-approve is on" and § "The marker holds after auto-approve returns"
- Evidence: the pass's state in `status --json` across both modes

### Tests for User Story 3

- [X] T024 [US3] Add tests to `tests/test_pipeline_needs_person.py`: with `auto_approve=False` and no evidence the pass reads `in_progress`; with evidence it reads `done` under both values of `auto_approve` (row 4 precedes row 5); with a claim from `wfctl step none` it reads `skipped` with `claimed` set under both values; verify each passes against the Phase 4 code, and fix the reading if one fails

### Implementation for User Story 3

- [X] T025 [US3] Run the manual checks in `quickstart.md` § "Refusal while auto-approve is on" and § "The marker holds after auto-approve returns" on a scratch branch; verify the refusal text matches `contracts/plan-walkthrough-command.md` exactly and nothing is written — merge gate

**Checkpoint**: switching auto-approve changes the pass's state with no file
created or deleted.

---

## Phase 6: User Story 5 - A repository places the pass where it wants it (Priority: P3)

Ordered before Story 4 because Story 4's manual run needs the declaration this
phase adds.

**Goal**: A maintainer can copy one snippet from `docs/reference.md` into
`wfctl.json`, and `check config` validates it, including the two `needs_person`
findings.

**Independent Test**: Paste the reference snippet into a scratch repository's
`wfctl.json`, run `wfctl check config`, and confirm no finding and that `wfctl
status` lists the pass under `plan`.

**Verification**:

- Automated: `tests/test_declared.py`, `tests/test_cli_status.py`
- Manual: `quickstart.md` § "Install and declare"
- Evidence: `uv run wfctl check config` exits 0 on this repository

### Tests for User Story 5

- [X] T026 [P] [US5] Write failing tests in `tests/test_declared.py`: `"needs_person": "yes"` yields `plan.plan-walkthrough has a 'needs_person' that is not a boolean`; `"manual": true, "needs_person": true` yields `plan.plan-walkthrough declares 'manual' and 'needs_person' — a manual pass already stops an autonomous run`; each drops the pass (R4)
- [X] T027 [P] [US5] Write a failing test in `tests/test_cli_status.py` that `wfctl check config` prints each finding and exits 1, following `test_check_config_exits_nonzero_on_a_finding`

### Implementation for User Story 5

- [X] T028 [US5] Add the two findings to `_declared._load_step` right after the `command` and `manual` block (`wfctl/_declared.py:153-162`), in the existing `f"{qualified} ..."` form; verify with T026 and T027
- [X] T029 [US5] Write a section in `docs/reference.md` after `## The pipeline` and before `## What lands in your repo`, titled for declaring your own passes, covering `steps`, `name`, `command`, `manual`, `evidence`, `before`, `after`, and `needs_person`, with the snippet from `contracts/declaration-and-payload.md` as its example (FR-018, R9); load the `andres-voice` skill first, since this is reader-facing prose; verify by pasting the snippet into a scratch repository's `wfctl.json` and running `uv run wfctl check config`
- [X] T030 [US5] Add the declaration from `contracts/declaration-and-payload.md` to this repository's `wfctl.json` under `plan` (FR-020); verify with `uv run wfctl check config` exiting 0 and `uv run wfctl status --json` listing `plan-walkthrough` under `plan`
- [X] T031 [US5] Validate Story 5 with `uv run pytest -q tests/test_declared.py tests/test_cli_status.py` and `uv run wfctl check config` — merge gate

**Checkpoint**: this repository declares the walkthrough, and a consuming
repository can copy the same snippet.

---

## Phase 7: User Story 4 - A person walks through a finished change (Priority: P2)

**Goal**: The change walkthrough asks about the diff against the plan that was
walked through, and writes `change-walkthrough.md` naming the `HEAD` commit.

**Independent Test**: On a branch with commits, run `/plan-walkthrough change`,
answer, and confirm the answers file carries `change` in its name and
`change-walkthrough.md` names the commit.

**Verification**:

- Automated: none; skill behavior is outside the suite
- Manual: `quickstart.md` § "Change mode (Story 4)"
- Evidence: `change-walkthrough.md` with `Mode: change` and the commit id

### Implementation for User Story 4

- [X] T032 [US4] Confirm `wfctl/agents/skills/plan-walkthrough/SKILL.md` describes change mode per `contracts/plan-walkthrough-command.md`: questions about the diff against the plan and spec, the evidence file names `HEAD`, and a dirty tree gets one line saying the evidence covers the last commit only; verify by reading the skill against Story 4's acceptance scenarios
- [X] T033 [US4] Run the manual check in `quickstart.md` § "Change mode (Story 4)" on a scratch branch — merge gate

**Checkpoint**: both modes work, and this repository declares only plan mode
(#505).

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T034 [P] Add one line to `docs/architecture/vendor-upstream-skills.md`, beside the `clean-code` and `model-the-domain` paragraphs, saying `plan-walkthrough` is wfctl's own, cites its sources in `references/source-map.md`, and vendors no upstream text (FR-019); load `andres-voice` first; verify with `uv run pytest -q tests/test_arch_records.py`
- [X] T035 [P] Confirm `plan-walkthrough` has no `_MIRRORED_SKILLS` entry in `wfctl/cli.py` (R8); verify with `grep -n "plan-walkthrough" wfctl/cli.py` returning nothing
- [X] T036 Run the full definition of done: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl check config`, and `uv run wfctl doctor`; verify every one exits 0
- [X] T037 Run every section of `quickstart.md` on one scratch branch in order, and record the outcome of each in the session summary — merge gate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Phase 1; blocks Stories 2, 3, and 5
- **Story 1 (Phase 3)**: depends on Phase 1 only; the skill does not need the core change
- **Story 2 (Phase 4)**: depends on Phase 2
- **Story 3 (Phase 5)**: depends on Phases 3 and 4
- **Story 5 (Phase 6)**: depends on Phases 2 and 3 (the declaration needs the installed command)
- **Story 4 (Phase 7)**: depends on Phases 3 and 6
- **Polish (Phase 8)**: depends on every story

### Within Each Story

- Tests are written and fail before the code they cover
- `_pipeline.py` edits run in task order, since T018 - T021 touch the same file

### Parallel Opportunities

- Phase 3 (the skill) and Phase 4 (the core reading) touch no common file after Phase 2
- T016 and T017 share a new test file but no test; T026 and T027 touch different files
- T034 and T035 touch different files

## Parallel Example: Stories 1 and 2

```text
Task: "T006-T015 skill and command under wfctl/agents/"
Task: "T016-T023 needs_person reading in wfctl/_pipeline.py"
```

---

## Implementation Strategy

### MVP First

1. Phase 1 and Phase 2.
2. Phase 3: a person can run the walkthrough by typing the command.
3. Stop and validate with `quickstart.md` § "A person comes back".

### Incremental Delivery

1. Add Phase 4: an autonomous run passes the check by.
2. Add Phase 5: coming back works in both modes.
3. Add Phase 6: this repository declares the check, and the reference documents it.
4. Add Phase 7: the change walkthrough.

---

## Notes

- `[P]` means a different file and no dependency on an incomplete task.
- Prose written into `docs/` loads the `andres-voice` skill first (T029, T034).
  Skill text under `wfctl/agents/` is read by an agent, so it stays exact.
- The branch and feature directory keep the name `500-plan-defense`; wfctl
  derives the state directory from it.
- Commit after each task or logical group, with `(#500)` in the subject.
