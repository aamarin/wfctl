# Tasks: Review step after implement

**Input**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/cli.md`, and `quickstart.md` in this feature folder, plus the level-3 records `docs/architecture/design/679-review-is-its-own-step.md` and `docs/architecture/design/679-no-spec-skips-spec-rows.md`
**Prerequisites**: `plan.md` and `spec.md`

**Tests**: Every phase writes its failing tests first, then the code that makes them pass. Run every command with `uv run`, so the working tree's code is the one under test.

**Organization**: The shared review function comes first, since both the review row and the no-spec route reach `review`. Then each user story gets its own phase, in priority order.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel, since it changes different files and depends on no unfinished task.
- **[Story]**: The user story the task belongs to (US1 - US4).

---

## Phase 1: Setup

**Purpose**: Confirm the starting point, so a later failure is known to come from this change.

- [X] T001 Confirm the baseline is green before any edit; verify with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy`, and note any failure that's already on `main`

---

## Phase 2: Foundational (one review function for the guard and status)

**Purpose**: Plan Phase A. Move the guard's four calls into `_review.pending_at_head`, with no visible change. The review row (US1) and the no-spec route's review step (US2) both read this function.

**⚠️ CRITICAL**: No user story work starts until this phase is complete.

### Tests for the shared function (write first, and see them fail)

- [X] T002 Add `pending_at_head` coverage tests to `tests/test_review.py`: each group's commits on a feature branch off a local `main`, none after `review check` writes `last-reviewed.json` at HEAD, none after a sign-off at HEAD, and one commit after one more commit; verify they fail with `uv run pytest tests/test_review.py -q`
- [X] T003 Add `pending_at_head` error tests to `tests/test_review.py`: an `error` for a branch with no commits; a config problem on the trunk and one on the branch each return an `error` naming that file and the remedy `fix review in the wfctl.json the error names, then run wfctl check config`; a missing trunk returns its message and no `remedy`; `trunk_ref` is the ref the trunk resolved to; verify they fail with `uv run pytest tests/test_review.py -q`
- [X] T004 Add `for_status` tests to `tests/test_review.py`: `capped` names a group after one round with `review.rounds` at 1, names every pending group at 0, and is empty once a sign-off covers HEAD; without the flag, `capped` and `since` are empty and the round-tally folder isn't created; verify they fail with `uv run pytest tests/test_review.py -q`
- [X] T005 Add `since` tests to `tests/test_review.py`, all with `for_status=True`: the last reviewed commit after a run, the signed-off commit with a sign-off and no completed run, the signed-off commit after a run at one commit and a sign-off at a later one, the last reviewed commit after a merge from the trunk, `None` after a rebase that drops the last reviewed commit, and `None` with no `error` when the last reviewed commit no longer exists; verify they fail with `uv run pytest tests/test_review.py -q`

### Implementation

- [X] T006 Add `HeadCoverage` (`pending`, `since`, `capped`, `trunk_ref`, `error`, `remedy`) and `pending_at_head(repo_root, branch, timeout=None, *, head=None, for_status=False)` to `wfctl/_review.py`, making the five calls plan Phase A step 1 lists, in that order, and returning every `ReviewError` as a value; verify with the T002 and T003 tests
- [X] T007 Add the `for_status` half to `pending_at_head` in `wfctl/_review.py`: `capped` from the count `review start` uses, with `resolve_round_dir(..., create=False)` and `trunk_rounds(...).cap`, and `since` as the newest of the last reviewed and signed-off commits still on the branch, with every git read best-effort; verify with the T004 and T005 tests
- [X] T008 Change `_judge` in `wfctl/_review_gate.py` to call `pending_at_head(..., head=head)` in place of its four calls, turn `error` into `_Failed(error)`, and pass `coverage.trunk_ref` to `_record_gate.refusal`; verify with `uv run pytest tests/test_review_gate.py -q`, which must pass with no edits to that file
- [X] T009 Validate the foundational phase with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: The guard reads coverage through the shared function and refuses exactly as before.

---

## Phase 3: User Story 1 - Status keeps a branch open until it is reviewed (Priority: P1) 🎯 MVP

**Goal**: After implement, `wfctl status` names the review panel as the next command, and reads the story complete only once every group has reviewed HEAD or a person's sign-off covers it.

**Independent Test**: On a branch whose tasks are complete and whose verification passed, run `wfctl status` before any review, after a complete review, and after one more commit. The three outputs match the first three states in `contracts/cli.md`.

### Verification

- `tests/test_evidence.py` covers the review reader's five readings and the display strings.
- `tests/test_pipeline_commands.py` covers User Story 1's five scenarios through `wfctl status --json`, including the guard agreeing with the row (FR-004, SC-001).
- `tests/test_status_contract.py` passes after the contract regenerates as a minor bump to 1.4.
- `uv run pytest -q` stays green, including the story-complete tests outside a git repository after T026.

### Tests for User Story 1 (write first, and see them fail)

- [X] T010 [P] [US1] Add review reader tests to `tests/test_evidence.py`: `pending` while implement isn't done; an error with its reason and remedy; a capped group with the reason naming it and the sign-off remedy, and `review.rounds is 0, so a person has to sign off` for a cap of 0; `done` with nothing pending; and `in_progress` with no reason and the display; verify they fail with `uv run pytest tests/test_evidence.py -q`
- [X] T011 [P] [US1] Add display string tests to `tests/test_evidence.py`: `security, code: not reviewed yet (4 commits)`, `security, code: 1 commit unreviewed since 3f2a1c9`, two groups in different states on two lines, and that `build_evidence` leaves the review field `None` while implement isn't done; verify they fail with `uv run pytest tests/test_evidence.py -q`
- [X] T012 [P] [US1] Add User Story 1's five scenarios to `tests/test_pipeline_commands.py`, each on a feature branch with its own commits off the local `main`; scenario 5 has no level-2 record and checks the row reads done exactly when the guard finds no unreviewed commits, with and without a sign-off; add the `review.rounds` 0 case, where `auto` is false and the remedy names `wfctl review sign-off`; verify they fail with `uv run pytest tests/test_pipeline_commands.py -q`
- [X] T013 [P] [US1] Add a test to `tests/test_declared.py` that a `steps.review` key in `wfctl.json` is a `check config` finding; verify it fails with `uv run pytest tests/test_declared.py -q`
- [X] T014 [P] [US1] Add tests to `tests/test_stall.py` that the digest changes when one group's last reviewed commit moves, and that a stall on `review` lists `review state` as unchanged; verify they fail with `uv run pytest tests/test_stall.py -q`
- [X] T015 [P] [US1] Add a test to `tests/test_report_block_holds_step.py` that a block filed on a complete story holds `implement`, and a test in `tests/test_pipeline_commands.py` that `step complete implement` succeeds while `review` is current and leaves `review` in progress, since only `wfctl review check` and `wfctl review sign-off` may mark it done (FR-007); verify they fail with `uv run pytest tests/test_report_block_holds_step.py tests/test_pipeline_commands.py -q`

### Implementation for User Story 1

- [X] T016 [US1] Add `review: _review.HeadCoverage | None = None` to `Evidence` in `wfctl/_evidence.py`, and have `build_evidence` fill it with `pending_at_head(repo_root, resolve_branch(repo_root), for_status=True)` only when `implement(ev).state == "done"`; verify with the T011 `build_evidence` test
- [X] T017 [US1] Add the `review(ev) -> Assessment` reader and its display builder to `wfctl/_evidence.py`, with the five readings and remedies from plan Phase B step 1; verify with the T010 and T011 tests
- [X] T018 [US1] Add `"review": Step("/fanning-out-code-review", _AUTOMATIC, _evidence.review)` after `implement` in `_STEPS`, and set `STATUS_PAYLOAD_VERSION` to `"1.4"`, in `wfctl/_pipeline.py`; verify with the T012 tests
- [X] T019 [P] [US1] Refuse `steps.review` in `wfctl/_declared.py` with the problem `'review' takes no declared passes; its groups are set under the review key`; verify with the T013 test
- [X] T020 [P] [US1] Hash `ev.review` as sorted JSON after the three artifacts in `digest`, and name `review state` in `unchanged` for a stall on `review`, in `wfctl/_stall.py`; verify with the T014 tests
- [X] T021 [US1] In `wfctl/cli.py`, let `step complete implement` accept `review` as the current step, and make `report-block` fall back to `"implement"` by name instead of `_STEP_NAMES[-1]`; verify with the T015 tests
- [X] T022 [US1] Grep `wfctl/` for every other `_STEP_NAMES[-1]` and every literal `"implement"` that means "the last step", and change each hit or note in the commit message why it's correct; verify with `grep -rn '_STEP_NAMES\[-1\]' wfctl/` and `uv run pytest -q`
- [X] T023 [US1] Add the `no_spec` key to `payload_of` in `tests/conftest.py`, and add a `no_spec` fixture state to `wfctl/_contract.py` that writes `exceptions/spec.md` with no spec artifacts; verify the fixture builds once US2's T034 lands, with `uv run pytest tests/test_status_contract.py -q`
- [X] T024 [US1] Add the ninth row to `tests/pipeline_payload_snapshot.json` and to every test that lists the step names; verify with `uv run pytest tests/test_pipeline_payload_snapshot.py tests/test_evidence.py tests/test_pipeline_commands.py -q`
- [X] T025 [US1] Confirm the story-complete tests that run in a git repository pass with no edit: `tests/test_pipeline_commands.py` (around lines 221, 897, and 1444), `tests/test_warnings_after_gate.py`, and `tests/test_report_verbs.py`; verify with `uv run pytest tests/test_pipeline_commands.py tests/test_warnings_after_gate.py tests/test_report_verbs.py -q`
- [X] T026 [US1] Give the four story-complete tests outside a git repository a repository and a feature branch name, with `git_repo(tmp_path)` and `monkeypatch.setenv("WFCTL_BRANCH", ...)`, in `tests/test_pipeline_state_names.py` (around line 235), `tests/test_decompose_issues.py` (around line 246), `tests/test_tasks_hold_a_task.py` (around line 138), and `tests/test_completion_record.py` (around line 442); verify with `uv run pytest tests/test_pipeline_state_names.py tests/test_decompose_issues.py tests/test_tasks_hold_a_task.py tests/test_completion_record.py -q`
- [X] T027 [US1] Grep `tests/` for `Story complete`, `current is None`, and `(None, None)`, and check each hit's repository root against T025 and T026; verify with `uv run pytest -q`
- [X] T028 [US1] Validate User Story 1 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: A spec-pipeline branch reaches `review` after implement and reads complete only once it's reviewed.

---

## Phase 4: User Story 2 - A change that needs no spec goes straight to implement and review (Priority: P2)

**Goal**: `wfctl spec none --reason "…"` records a "no", the seven spec rows read skipped, `implement` is judged by `wfctl verify` alone, and the branch then reaches `review`.

**Independent Test**: On a scratch issue branch, run `wfctl spec none --reason "…"`, then `wfctl status`, then `wfctl verify`, then `wfctl status` again.

### Verification

- `tests/test_design_exceptions.py` covers reading the answer and when `reasons` includes it.
- `tests/test_pipeline_commands.py` covers each `spec none` outcome, the skipped rows, the single console line, `no_spec` in the JSON, the route through `wfctl verify` to `review`, the skipped passes, and the `n/a` artifacts fact.
- `tests/test_design_exceptions.py` covers `check-body` asking for the reason in the body.
- `tests/test_status_contract.py` records the `no_spec` object.

### Tests for User Story 2 (write first, and see them fail)

- [X] T029 [P] [US2] Add tests to `tests/test_design_exceptions.py` that `spec` reads `exceptions/spec.md` and ignores an empty one, that `spec_in_effect` returns the reason only with no spec artifact, and that `reasons` includes `("spec", reason)` with no spec artifact and leaves it out with `design.md` present; verify they fail with `uv run pytest tests/test_design_exceptions.py -q`
- [X] T030 [P] [US2] Add `wfctl spec none` tests to `tests/test_pipeline_commands.py`: success prints the path and `Put the reason in the PR body.`, and it refuses an empty reason, a placeholder such as `<why>`, and a folder holding any of `design.md`, `spec.md`, `plan.md`, or `tasks.md`, naming the file and writing nothing; verify they fail with `uv run pytest tests/test_pipeline_commands.py -q`
- [X] T031 [P] [US2] Add no-spec pipeline tests to `tests/test_pipeline_commands.py`: the seven rows read `skipped` with the annotation `no spec`, the console prints the one line `brainstorm … decompose  –  skipped: no spec`, `--json` carries `no_spec` with `reason` and `path` (and `null` without a "no"), `implement` routes to `wfctl verify`, `review` is current once verified, every pass under the seven rows reads `skipped` including `plan-walkthrough` declared in `wfctl.json`, and the `artifacts written` fact reads `n/a`; verify they fail with `uv run pytest tests/test_pipeline_commands.py -q`
- [X] T032 [P] [US2] Add `check-body` tests that a body missing the no-spec reason fails with `the no-spec reason isn't in the body: "<reason>"`, a body carrying it passes, and nothing is asked once `design.md` exists, in `tests/test_design_exceptions.py`, which covers `check-body`'s exception reasons today; verify they fail with `uv run pytest tests/test_design_exceptions.py -q`

### Implementation for User Story 2

- [X] T033 [US2] Add `SPEC = "spec"`, `SPEC_ARTIFACTS`, `spec(spec_dir)`, and `spec_in_effect(spec_dir)` to `wfctl/_design_exceptions.py`, and have `reasons` add `("spec", reason)` through `spec_in_effect`; verify with the T029 tests
- [X] T034 [US2] In `wfctl/_evidence.py`, import `SPEC_ARTIFACTS`, add `no_spec` and `stale_no_spec` to `Evidence` and fill them in `build_evidence`, judge `implement` by the verification record alone when `no_spec` is set and `tasks.md` is missing, and make `fact_artifacts_written` read `n/a` with `no spec recorded`; verify with the T031 `implement`, `review`, and fact tests
- [X] T035 [US2] In `wfctl/_pipeline.py`, add `spec_step: bool = False` to `Step` and set it on the seven rows, read each `spec_step` row as `skipped` with `no spec` when `ev.no_spec` is set while keeping its passes through `_pass_states(name, passes, None, "skipped", claims)`, and add `NoSpec` and `PipelineReport.no_spec` filled by `build_report`; verify with the T031 row and pass tests
- [X] T036 [US2] In `wfctl/cli.py`, emit `no_spec` in `status --json`, print the one skipped line in the console view, and change `check-body`'s message for the `spec` label; verify with the T031 console and JSON tests and the T032 tests
- [X] T037 [US2] Add `wfctl spec none --reason "…"` to `wfctl/cli.py`, moving the empty and placeholder checks `arch none` uses into one shared helper, refusing when any of `SPEC_ARTIFACTS` exists, and writing through `_design_exceptions.write`; verify with the T030 tests and `uv run pytest tests/test_step_none.py -q`, which covers the checks `arch none` and `step none` share
- [X] T038 [US2] Regenerate `wfctl/contracts/status-payload.json` with the `no_spec` fixture state from T023, and confirm `bump` returns minor; verify with `uv run pytest tests/test_status_contract.py -q`
- [X] T039 [US2] Validate User Story 2 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: A no-spec branch goes from a recorded "no" through `wfctl verify` to `review` with no spec step run.

---

## Phase 5: User Story 3 - A changed answer can't leave the branch on the wrong route (Priority: P3)

**Goal**: A recorded "no" beside a spec artifact is ignored, and `wfctl status` warns with the file to delete.

**Independent Test**: Record "no", create `design.md`, then run `wfctl status`.

### Verification

- `tests/test_pipeline_commands.py` covers the full pipeline with `brainstorm` current and the warning naming `exceptions/spec.md`.

- [X] T040 [US3] Add a test to `tests/test_pipeline_commands.py` that a recorded "no" beside `design.md` reads the full pipeline with `brainstorm` current, `no_spec` `null`, and one warning `exceptions/spec.md says no spec, but design.md exists` with the remedy `rm <path>`; verify it fails with `uv run pytest tests/test_pipeline_commands.py -q`
- [X] T041 [US3] Append the `StepWarning("brainstorm", None, …, "rm <path>")` after `collect_warnings` in `build_report` in `wfctl/_pipeline.py` when `ev.stale_no_spec` is set; verify with the T040 test
- [X] T042 [US3] Validate User Story 3 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

---

## Phase 6: User Story 4 - The agent asks the spec question at session start (Priority: P3)

**Goal**: The `/start-session` and `design-passes` text already committed on this branch matches what `wfctl spec none` now prints.

**Independent Test**: Start a session on a scratch issue branch with no spec folder and read the step 7 report.

### Verification

- A manual run, by the user, since the worktree guard refuses running commands in a second worktree.

- [X] T043 [P] [US4] Check that the example output in `wfctl/agents/skills/design-passes/SKILL.md` and `wfctl/agents/skills/start-session/SKILL.md` matches what T037 prints, and fix any difference; verify with `uv run pytest tests/test_skill_cross_references.py tests/test_skill_commands.py -q`
- [X] T044 [P] [US4] Check that `wfctl/agents/skills/fanning-out-code-review/SKILL.md` reads the field name `no_spec` that T036 emits; verify with `grep -n no_spec wfctl/agents/skills/fanning-out-code-review/SKILL.md`
- [ ] T045 [US4] Ask the user to run the session-start walk in `quickstart.md` section 3 on a scratch issue branch, and record the result in the session summary; verify with the user's report of the step 7 output

---

## Phase 7: Polish and the real flow

**Purpose**: Docs, the release note, the install check, SC-004, and the real flow before the PR.

- [X] T046 [P] Name `review` as the ninth step, and list `spec none` beside `arch none`, in `README.md`; verify with `grep -n "review" README.md`
- [X] T047 [P] Make the story-complete branch of `wfctl/agents/skills/speckit-orchestrate/SKILL.md` say the story is complete only after `review`; verify with `uv run pytest tests/test_orchestrate_skill.py -q`
- [X] T048 [P] Add `→ review` to the pipeline line in "What this is" in `AGENTS.md`; verify with `grep -n "implement → review" AGENTS.md`
- [X] T049 Create `changes/679.addition.md` with `uv run towncrier create 679.addition.md --content "…"`, saying what a wfctl user notices; verify with `uv run wfctl verify`
- [X] T050 Run `uv run wfctl install-skills --prune --yes --agent claude` and `uv run wfctl doctor`, then exercise the changed skills; verify that `doctor` exits 0
- [ ] T051 Ask the user to run the no-spec walk in `quickstart.md` section 2 on a scratch issue branch, since the worktree guard refuses a second worktree; verify with the user's report of each step
- [ ] T052 Run the real flow on this branch from `quickstart.md` section 1 steps 1 - 4: finish implement, see `review` next, run `/fanning-out-code-review`, see it done, make one commit, and see it pending again after `uv run wfctl verify`; verify with the `uv run wfctl status` output at each step
- [ ] T053 Measure SC-004 from `quickstart.md` section 1 step 5 while `review` is current, and record both medians and `git rev-list --count origin/main..HEAD` in the session summary; verify that the medians differ by less than half a second
- [ ] T054 Validate the whole change with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `uv run wfctl verify`, and `uv run wfctl doctor` — merge gate

---

## Dependencies and execution order

### Phase dependencies

1. Setup (Phase 1) has no dependencies.
2. Foundational (Phase 2) depends on Setup, and blocks every user story.
3. US1 (Phase 3) depends on Phase 2.
4. US2 (Phase 4) depends on Phase 2. Its route ends at `review`, so its scenario 3 and T038 also depend on US1's T018 and T023.
5. US3 (Phase 5) depends on US2's T034, which sets `stale_no_spec`.
6. US4 (Phase 6) depends on US2's T036 and T037, whose output the skill text has to match.
7. Polish (Phase 7) depends on every story. T052 and T053 run last, since they need implement done on this branch.

### Within each story

The tests come first and fail before the code that makes them pass. Evidence fields come before the readers that use them, and readers before the step table.

### Parallel opportunities

- In Phase 2, the tests T002 - T005 all edit `tests/test_review.py`, so they run one after another.
- In US1, the tests T010 - T015 touch different files, except that T010 and T011 share `tests/test_evidence.py` and T012 and T015 share `tests/test_pipeline_commands.py`. T019 and T020 can run beside T016 - T018.
- In US2, T029, T032, and the pair T030 - T031 touch different files.
- In US4 and Polish, T043, T044, T046, T047, and T048 touch different files.

### Parallel example: User Story 1 tests

```text
Task: "T010 Add review reader tests to tests/test_evidence.py"
Task: "T013 Add a steps.review test to tests/test_declared.py"
Task: "T014 Add digest and stall tests to tests/test_stall.py"
Task: "T015 Add the report-block test to tests/test_report_block_holds_step.py"
```

## Implementation strategy

### MVP first

1. Complete Phases 1 and 2.
2. Complete US1. A spec-pipeline branch now stops at `review` after implement, which is the gap #679 was opened for.
3. Stop and validate with T028.

### Incremental delivery

1. US1 closes the review gap for every spec-pipeline branch.
2. US2 opens the no-spec route, which ends at the same review step.
3. US3 adds the warning for a stale answer.
4. US4 and Polish check the skill text, then run the real flow and SC-004 on this branch before the PR.

Design records: 2 listed in design.md
  docs/architecture/design/679-review-is-its-own-step.md
  docs/architecture/design/679-no-spec-skips-spec-rows.md
