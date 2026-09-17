---
description: 'Task list for #384 — strip allow-notify'
---

# Tasks: Strip allow-notify

**Input**: Design documents from `specs/384-strip-allow-notify/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Every phase ends with the suite green. Tests that checked the refusal
are deleted rather than flipped (spec, Validation Strategy).

**Organization**: Stories 1 and 2 are both P1. Story 1 removes the refusal.
Story 2 replaces the reporting verbs. Story 3 takes the grant out of `status`
and `start`, which is where the rest of the grant code lives. Story 4 brings the
skills and docs in line. The order matters, because each story deletes code the
next one would otherwise have to work around.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: which user story the task belongs to

## Design records

Design records: 2 listed in design.md
  docs/architecture/design/384-an-action-is-named-by-the-verb-that-takes-it.md
  docs/architecture/design/384-the-agent-reports-through-two-flat-verbs.md

---

## Phase 1: Setup

**Purpose**: confirm the starting point is green, so any later failure belongs to this change.

- [X] T001 Run `uv run pytest -q`, `uv run ruff check wfctl/ tests/` and `uv run mypy wfctl/` on the branch as it stands, and note the test count

---

## Phase 2: Foundational

**Purpose**: none. No shared infrastructure is added, and each story below
starts from the code as it is.

---

## Phase 3: User Story 1 - A person says "file it" and the issue gets filed (Priority: P1) 🎯 MVP

**Goal**: `wfctl issue comment | create | label` reach the tracker on any branch with no grant.

**Independent Test**: on a branch with no grant, the three verbs call a stubbed tracker and exit with its result.

### Verification

- `uv run pytest -q tests/test_tracker.py tests/test_tracker_records_issue_verbs.py`
- `grep -n "_refuse_notifying\|action_grant" wfctl/_tracker.py` returns nothing

### Implementation

- [X] T002 [US1] Delete `_refuse_notifying` and its call in `wfctl/_tracker.py` (the `if section == "verbs" and verb in _NOTIFYING_VERBS: refused = …` block); verify with T004
- [X] T003 [US1] Delete the tests that assert a refusal: `tests/test_notify_dispatch.py`, and the grant-refusal cases in `tests/test_tracker.py`; verify with `uv run pytest -q tests/test_tracker.py`
- [X] T004 [US1] Add `tests/test_tracker_records_issue_verbs.py`: on a branch with no grant (and on trunk), `wfctl issue create`, `comment` and `label` against a stubbed tracker print no refusal and exit 0; verify with `uv run pytest -q tests/test_tracker_records_issue_verbs.py`
- [X] T005 [US1] Validate Phase 3 with `uv run pytest -q` — merge gate

---

## Phase 4: User Story 2 - A restarted session can see what the last run did and what it was stopped from doing (Priority: P1)

**Goal**: `report-action` and `report-block` replace `notify` and `blocked`. A successful `wfctl issue` write lifts its own hold.

**Independent Test**: `report-block push --reason x` holds the step, `report-action push` lifts it and says so, and the restart summary lists the push.

### Verification

- `uv run pytest -q tests/test_report_verbs.py tests/test_report_block_holds_step.py tests/test_report_events.py tests/test_tracker_records_issue_verbs.py tests/test_restart_hook_cli.py`
- `uv run wfctl --help` lists `report-action` and `report-block`, and neither `notify` nor `blocked`

### Tests

- [X] T006 [P] [US2] Rewrite `tests/test_blocked_cli.py` as `tests/test_report_verbs.py` against `contracts/cli.md`: `report-block` requires `--reason`; it holds the inferred step; with no spec dir it holds nothing; `report-action` prints `✓ recorded:` and, when a hold matched, the `lifted the hold on <step>` line; neither command refuses; `--help` lists neither removed command
- [X] T007 [P] [US2] Rename `tests/test_blocked_holds_step.py` to `tests/test_report_block_holds_step.py` and switch it to the new verbs. Drop the `--clear` cases and keep the case where the pipeline is complete and the last step is held
- [X] T008 [P] [US2] Rename `tests/test_blocked_events.py` to `tests/test_report_events.py`. Keep one test where an old log's `blocked` then `block-cleared` for the same action leaves no standing hold
- [X] T009 [P] [US2] Extend `tests/test_tracker_records_issue_verbs.py`: a successful `issue create` records `issue-create`, `issue close` records `issue-close`, `issue start` and `issue stop` record nothing, and a `report-block issue-create` followed by a successful `issue create` leaves no hold
- [X] T010 [P] [US2] Delete `tests/test_notify_declined.py`, and in `tests/test_restart_hook_cli.py` drop the `notify-declined` cases

### Implementation

- [X] T011 [US2] In `wfctl/cli.py`, replace `notify_cmd` with `report_action_cmd` (`@app.command("report-action")`: read `standing_blocks` for the branch, call `record_notify_action`, print per `contracts/cli.md`). Replace `blocked_cmd` with `report_block_cmd` (`@app.command("report-block")`: the body of `blocked_cmd` without the `--clear` branch or its option). Verify with T006–T008
- [X] T012 [US2] In `wfctl/_session.py`, delete `record_notify_declined` and `record_block_cleared`. Keep `block-cleared` in `standing_blocks`'s event filter, and rewrite its docstring to say the event is no longer written but is still honoured. Verify with T008
- [X] T013 [US2] In `wfctl/_tracker.py`, rename `_NOTIFYING_VERBS` to `_RECORDED_VERBS = {"comment", "create", "label", "close"}`, and record `f"issue-{verb}"` after a verb exits 0. Rewrite the comment above it for what it now means (research R3). Verify with T009
- [X] T014 [US2] In `wfctl/_restart.py`, set `_LATE_EVENTS = ("notify-action",)` and update the comment that names `record_notify_declined`; verify with `uv run pytest -q tests/test_restart_hook_cli.py`
- [X] T015 [US2] In `wfctl/_pipeline.py`, make `_block_remedy` print `wfctl report-action <action>` (still `shlex.quote`d) instead of `wfctl blocked <action> --clear`, and rewrite its docstring; verify with T007
- [X] T016 [US2] Validate Phase 4 with `uv run pytest -q` and `uv run mypy wfctl/` — merge gate

---

## Phase 5: User Story 3 - The status output stops talking about a permission that no longer exists (Priority: P2)

**Goal**: no notify line, no `notify` or `notify_source` keys, three facts. `wfctl start` makes no tracker call. The host line is reworded.

**Independent Test**: on a fresh branch, `wfctl status --json` has no `notify` key and three facts, and `wfctl status` prints the irreversible line and the reworded host line.

### Verification

- `uv run pytest -q tests/test_status_facts.py tests/test_pipeline_payload_snapshot.py tests/test_agent_session.py tests/test_console_plaintext.py`
- `grep -rn "on_trunk\|read_issue_labels\|NotifyGrant\|notify_source" wfctl/` returns nothing

### Tests

- [X] T017 [P] [US3] Rename `tests/test_four_facts.py` to `tests/test_status_facts.py`: assert three facts in a fixed order, and delete the outward-actions cases
- [X] T018 [P] [US3] Delete `tests/test_notify_flag.py`, `tests/test_notify_grant.py` and `tests/test_notify_status.py`
- [X] T019 [P] [US3] Update `tests/test_pipeline_payload_snapshot.py` to the payload in `contracts/status-payload.md`
- [X] T020 [P] [US3] Add a case (in `tests/test_agent_session.py`) that `wfctl start` makes no tracker call: stub the tracker to fail loudly if it is invoked. Add a case that `wfctl status` prints the new host line from research R1 and still prints `_IRREVERSIBLE_NOTICE`. Add a case where a leftover `notify.json` holding `{"state": "denied"}` in the state dir changes nothing: `wfctl issue create` still reaches the stubbed tracker, and `status` output is identical with and without the file (spec, Edge Cases)

### Implementation

- [X] T021 [US3] In `wfctl/cli.py`, remove `--allow-notify/--deny-notify`, `report_notify` and its calls, `_GRANT_LINES`, `_notify_line`, and the `notify` and `notify_source` keys and their print in `status_cmd`. Set `_HOST_AUTHORITY_NOTICE` to the wording in research R1. Verify with T019 and T020
- [X] T022 [US3] In `wfctl/_pipeline.py`, remove the `notify` and `notify_source` fields from `PipelineReport`, delete `_corrected_grant`, and stop calling `resolved_notify` in `build_report`; verify with T019
- [X] T023 [US3] In `wfctl/_predicates.py`, delete `fact_outward_actions_authorized`, `_GRANT_DETAIL` and `_UNREADABLE_GRANT`. Make `facts()` take no grant and return three. Rewrite the two comments that name the grant (`_unkeyed_issues`' docstring, and the automatic-rung comment near line 695) so that what unkeyed rows wait on is the issues being created. Verify with T017
- [X] T024 [US3] In `wfctl/_session.py`, delete `NOTIFY_NAME`, `NOTIFY_LABEL`, `NotifyGrant`, `_read_notify_file`, `notify_grant`, `action_grant`, `grant_notify`, `record_notify_resolved`, `resolved_notify` and `record_notify_refused`; verify with `uv run mypy wfctl/` and T020
- [X] T025 [P] [US3] Delete `on_trunk` from `wfctl/_paths.py` and `read_issue_labels` from `wfctl/_tracker.py`. Fix the docstring at `_tracker.py:476` that refers to it. Verify with `uv run ruff check wfctl/` and the grep in this phase's Verification
- [X] T026 [US3] Fix the remaining single-mention tests, reading each one first: `test_auto_approve_mode`, `test_change_cli`, `test_console_plaintext`, `test_decompose_issues`, `test_pipeline_commands`, `test_pipeline_sections`, `test_pipeline_state_names`, `test_session_is_open`, `test_stall`, `test_tasks_hold_a_task`, `test_unattended_pause_rules`, `test_worktree_guard`; verify with `uv run pytest -q`
- [X] T027 [US3] Update the comment at `wfctl/_stall.py:133` so it no longer describes a live grant; verify with `uv run ruff check wfctl/`
- [X] T028 [US3] Validate Phase 5 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/` and `uv run mypy wfctl/` — merge gate

---

## Phase 6: User Story 4 - Skills and docs describe how things work now (Priority: P2)

**Goal**: no installed skill reads the grant or calls a removed verb. Skills ask as written, a run where nobody answers tries the action, and a host refusal is reported with `report-block`.

**Independent Test**: after `install-skills`, a search of the installed tree for the removed names finds nothing, and each changed skill reads correctly as installed.

### Verification

- `uv run pytest -q tests/test_skill_cross_references.py`
- `uv run wfctl install-skills --prune --yes --agent claude`, then `uv run wfctl doctor` exits 0
- Read `.claude/` and `.agents/` copies of every file changed below

### Tests

- [X] T029 [US4] Extend `tests/test_skill_cross_references.py`: fail when any file under `wfctl/agents/` contains `wfctl notify`, `wfctl blocked`, `--allow-notify`, `notify_source` or `authority:notify` (`a-rule-is-expressed-as-a-check`). In the same file, rewrite `test_decompose_allows_the_commands_its_notify_gate_needs` to require `wfctl report-block` in place of `wfctl notify`, and rename it and its docstring so they no longer describe a grant. T035 breaks it otherwise

### Implementation

- [X] T030 [P] [US4] Rewrite step 5 of `wfctl/agents/skills/end-session/SKILL.md` per research R5 (ask as written; unanswered → try the action; `wfctl report-action push` after a push; no `--declined`). In step 7, use `wfctl report-block issue-close --reason …` and say that a later successful `wfctl issue close` or `wfctl report-action issue-close` lifts the hold. In step 8, stop reporting "what the grant allowed". Verify with T029 and by reading it as installed
- [X] T031 [P] [US4] Rewrite step 6 of `wfctl/agents/skills/speckit-delivery-plan/SKILL.md` per research R5. Remove the decline section, and point the unkeyed-rows paragraph at a host refusal. In step 7, drop "wfctl refuses a notifying verb the run was never granted", keep the `gh` prohibition with its remaining reason (wfctl records the write), and use `report-block issue-create`. Fix line ~271's `--declined` mention. Verify with T029
- [X] T032 [P] [US4] In `wfctl/agents/skills/scaffold-tracker/SKILL.md`, rewrite the `labels` verb prose at line ~46 so it no longer ties the verb to a grant; verify with T029
- [X] T033 [P] [US4] In `wfctl/agents/commands/speckit.analyze.md`, rewrite the "Filing" section (lines ~220–256) per research R5, and replace `Bash(wfctl blocked*)` with `Bash(wfctl report-block*)` in `allowed-tools`; verify with T029
- [X] T034 [P] [US4] In `wfctl/agents/commands/speckit.implement.md`, switch to `wfctl report-block <action>`, and to `wfctl report-action <action>` for a person who took the action by hand, in the body (lines ~48–56) and in `allowed-tools`; verify with T029
- [X] T035 [P] [US4] In `wfctl/agents/commands/end-session.md` and `wfctl/agents/commands/speckit.decompose.md`, replace `Bash(wfctl notify*) Bash(wfctl blocked*)` in `allowed-tools` with `Bash(wfctl report-action*) Bash(wfctl report-block*)`. Also fix the `description` in `speckit.decompose.md` if it names the grant. Verify with T029
- [X] T036 [P] [US4] In `README.md` line 19, describe accountable outward actions as recorded, not gated, and link to the renamed reference section. Rewrite `docs/reference.md` lines ~540–630: remove the grant and document `report-action` and `report-block` per `contracts/cli.md`. Verify with the grep in T039
- [X] T037 [P] [US4] Rewrite the Safety section of `AGENTS.md`: tracker writes are not gated by wfctl, the host's permission layer decides, `close` stays the human's, and no "refuse by default" wording remains. Verify by reading the section and with the T039 grep
- [X] T038 [US4] Validate Phase 6 with `uv run pytest -q`, `uv run wfctl install-skills --prune --yes --agent claude` and `uv run wfctl doctor` — merge gate

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T039 Run `grep -rnE "allow.notify|notify_source|outward actions authorized|authority:notify|wfctl notify|wfctl blocked" wfctl README.md docs AGENTS.md`. Every match must be a superseded record or a history log line (SC-003)
- [X] T040 [P] Add a log line pointing to `wfctl-records-outward-actions-and-never-gates-them` on `docs/architecture/the-agent-reports-the-block-wfctl-never-saw.md`, `docs/architecture/wfctl-classes-the-action-not-the-command.md` and `docs/architecture/design/364-the-block-report-is-its-own-verb.md`. Read `readiness-is-not-a-step-state.md`, `the-repo-names-the-fields-a-change-must-carry.md`, `design/299-facts-render-as-a-block.md` and `design/200-session-id-rides-on-the-start-event.md`, and add a line only where one states the grant as current. Change no status. Verify with `uv run wfctl arch check` on each changed record
- [X] T041 Run `quickstart.md` steps 1–6
- [X] T042 Validate the feature with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl verify` and `uv run wfctl doctor` — merge gate

---

## Dependencies & Execution Order

```
Phase 1 ─► US1 (Phase 3) ─► US2 (Phase 4) ─► US3 (Phase 5) ─► US4 (Phase 6) ─► Polish
```

- US2 depends on US1: `_tracker.py` is edited by both, and the refusal has to be gone before recording is reshaped.
- US3 depends on US2: `notify_cmd` was the last caller of `action_grant` outside `_tracker`, so the grant can't be deleted until it's gone.
- US4 depends on US2: skills can't name `report-block` until it exists. It is independent of US3 in code, but ordered after it so the docs describe the final status output.
- **Phases 4–6 land in one commit.** `384-the-agent-reports-through-two-flat-verbs` says in its Consequences: "Every skill call site and both docs change in the same commit as the CLI." A commit that removes `notify` and `blocked` while the skills still call them installs a broken tree. The per-phase "merge gate" lines are validation checkpoints inside that commit, not separate merges.

## Parallel Opportunities

- Phase 4: T006–T010 are separate test files.
- Phase 5: T017–T020 are separate test files. T025 is independent of T021–T024.
- Phase 6: T030–T037 each touch a different file.

## Implementation Strategy

US1 alone is the MVP: the refusal is gone and nothing else changes. The whole
feature ships as one change, though, because the level-2 record requires the
payload and its views to change together, and a branch with US1 alone would
leave the skills reading a grant that never refuses.
