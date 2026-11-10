# Tasks: issue edit verb

**Input**: Design documents from the `445-issue-edit-verb` spec folder
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Every story writes its tests first and watches them fail. Tests that
touch output pin `NO_COLOR`, as `tests/conftest.py` explains.

**Design record**: `docs/architecture/design/issue-edit-one-field-per-call.md`
(still `status: proposed`). No task below changes the verb's shape: one `edit`
verb taking `{id}`, `{field}`, and `{value}`, called once per field, title first.

**Plan review**: the findings in `plan-review.md` are folded in where they
apply. PR-001 is T020 and T021, PR-002 is T003 and T004, PR-003 is T008, PR-004
is T023, and PR-005 is T026. PR-006 needs no task, since accepting the record
is the user's call.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: which user story the task belongs to (US1, US2, US3)

---

## Phase 1: Setup

**Purpose**: the one file every change in this repo carries.

- [X] T001 Create the release note with `uv run towncrier create 445.addition.md --content "wfctl issue edit changes an issue's title, its body, or both, and records each write as issue-edit."` in `changes/445.addition.md`; verify with `uv run wfctl verify` reporting the release-note check passing

---

## Phase 2: Foundational

**Purpose**: split `dispatch` so the edit can check the tracker once and then
run one write per field, without a second copy of the notices or of the
recording rule. Behaviour doesn't change in this phase.

**⚠️ CRITICAL**: every story builds on these helpers.

- [X] T002 Add `"edit": {"id", "field", "value"}` to `ALLOWED` and `"edit"` to `_RECORDED_VERBS` in `wfctl/_tracker.py`, with a comment beside each saying why (one field per call, per the design record; recorded because a block can be filed against `issue-edit`); verify with `uv run pytest -q tests/test_tracker.py`
- [X] T003 Pull the first half of `dispatch` into a helper in `wfctl/_tracker.py` that resolves the tracker name and config, checks the verb is declared, and prints the existing "No tracker configured", invalid-config, and unsupported-verb notices. It returns the verb map and tracker name, or an exit code to stop with (research.md section 2); verify with `uv run pytest -q tests/test_tracker.py tests/test_tracker_records_issue_verbs.py` passing unchanged
- [X] T004 Pull the second half of `dispatch` into a second helper in `wfctl/_tracker.py` that substitutes, runs, passes stdout and stderr through, appends the `issue` event, and records the outward action for a verb in `_RECORDED_VERBS`. `dispatch` becomes the first helper followed by the second (research.md section 3); verify with `uv run pytest -q tests/test_tracker.py tests/test_tracker_records_issue_verbs.py` passing unchanged
- [x] T005 Validate Phase 2 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: `dispatch` behaves as before, and the edit can call the two halves separately.

---

## Phase 3: User Story 1 - Change an issue's body or title (Priority: P1) 🎯 MVP

**Goal**: `wfctl issue edit <id>` with `--title`, `--body`, or both changes the
issue and records one `issue-edit` per field written.

**Independent Test**: run `wfctl issue edit <id> --body "…"` against a stub
backend and confirm one call with `field=body` and one `issue-edit` record.

**Verification**:

- Automated: the new tests in `tests/test_tracker.py` and `tests/test_tracker_records_issue_verbs.py`
- Manual: quickstart.md steps 2 and 3, against a real GitHub issue, in Phase 6
- Evidence: the backend argv each test captures, and the `notify-action` events in the session log

### Tests for User Story 1 ⚠️

> Write these first, and confirm they fail before T010.

- [X] T006 [P] [US1] Add tests in `tests/test_tracker.py` that a title-only edit makes one backend call with `--title`, that a body-only edit makes one call with `--body`, and that a two-field edit makes two calls with the title first, using the `captured_argv` fixture
- [X] T007 [P] [US1] Add a test in `tests/test_tracker.py` that a body with several lines, backticks, quotes, and `$(...)` reaches the backend as one unchanged argv token
- [X] T008 [P] [US1] Add a test in `tests/test_tracker.py` that `--title ""` is sent to the backend as an empty value and doesn't hit the "needs a field" error, so the field check tests `is None` rather than truthiness (spec Edge Cases)
- [X] T009 [P] [US1] Add tests in `tests/test_tracker_records_issue_verbs.py` that a one-field edit records one `issue-edit` and a two-field edit records two

### Implementation for User Story 1

- [X] T010 [US1] Add the edit function in `wfctl/_tracker.py`. It calls the T003 helper once, then the T004 helper once per field given, title before body, with `field` and `value` set, and stops at the first non-zero exit; verify with T006, T007, and T009
- [X] T011 [US1] Route `edit` in `issue_cmd` in `wfctl/cli.py` to the edit function, passing `--title` and `--body` as given (`None` when absent). Add `edit` to the verb help, the `issue_id` help, and the `--title` and `--body` option help (FR-012); verify with T006 and with `uv run wfctl issue --help` listing `edit <id> --title T --body TEXT`
- [X] T012 [P] [US1] Add `"edit": ["gh", "issue", "edit", "{id}", "--{field}", "{value}"]` to `wfctl/agents/trackers/github.json` (FR-010); verify with a test in `tests/test_tracker.py` that the shipped GitHub config passes `validate_config` and declares `edit`
- [x] T013 [US1] Validate Phase 3 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: an edit with either field or both works against a stub backend and is recorded.

---

## Phase 4: User Story 2 - Know what happened when an edit goes wrong (Priority: P2)

**Goal**: every failure says which call failed and what wasn't sent, and a usage
error sends nothing.

**Independent Test**: use a stub backend whose body call fails, run an edit with
both fields, and check the output, the exit code, and the recorded writes.

**Verification**:

- Automated: the new tests in `tests/test_tracker.py` and `tests/test_tracker_records_issue_verbs.py`
- Evidence: the printed lines, the exit codes, and the count of `issue-edit` events

### Tests for User Story 2 ⚠️

- [X] T014 [P] [US2] Add a test in `tests/test_tracker.py` that a two-field edit whose body call fails prints the backend's error and then `✗ title changed, body write failed`, exits with the backend's code, and that `tests/test_tracker_records_issue_verbs.py` sees one `issue-edit`
- [X] T015 [P] [US2] Add a test in `tests/test_tracker.py` that a two-field edit whose title call fails prints the backend's error and then `✗ title write failed, body was not sent`, exits with the backend's code, never calls the backend a second time, and records nothing
- [X] T016 [P] [US2] Add a test in `tests/test_tracker.py` that a one-field edit whose call fails prints the backend's error alone, with no `✗` summary line
- [X] T017 [P] [US2] Add tests in `tests/test_tracker.py`, through `runner.invoke(app, ["issue", "edit", ...])`, that `wfctl issue edit 445` prints `✗ 'edit' needs --title, --body, or both` and exits 2, and that `wfctl issue edit --body "B"` on a branch with an issue key prints `✗ 'edit' requires an issue id` and exits 2, both with no backend call

### Implementation for User Story 2

- [X] T018 [US2] Print the two summary lines in the edit function in `wfctl/_tracker.py` after a failed call when both fields were given (FR-005, FR-005a), and add the id and field checks to `issue_cmd` in `wfctl/cli.py` before any tracker call, without adding `edit` to `_BRANCH_SCOPED_VERBS` (FR-007, FR-008); verify with T014 through T017

- [x] T019 [US2] Validate Phase 4 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: every case in `contracts/cli.md` from "both, body fails" to "no id" has a passing test.

---

## Phase 5: User Story 3 - Author a backend that supports edit (Priority: P3)

**Goal**: `tracker-check` accepts a correct `edit` entry and refuses a wrong one,
a backend without `edit` gets one notice, and `scaffold-tracker` asks about the verb.

**Independent Test**: run `wfctl tracker-check` on a config with a correct `edit`
entry, one with an extra placeholder, and one missing `{value}`, then run
`wfctl issue edit` against a config with no `edit`.

**Verification**:

- Automated: the new tests in `tests/test_tracker.py`
- Manual: `uv run wfctl install-skills --tracker github` then `uv run wfctl tracker-check`, in Phase 6
- Evidence: the `tracker-check` findings, and one notice line per edit

### Tests for User Story 3 ⚠️

- [X] T020 [P] [US3] Add tests in `tests/test_tracker.py` that `validate_config` accepts an `edit` entry using `{id}`, `{field}`, and `{value}`, reports one using `{title}` as not allowed, and reports one that leaves out `{field}` or `{value}`. Without the last check, `["jira","edit","{id}","--summary","{value}"]` passes and a two-field edit writes the body over the title (plan-review PR-001)
- [X] T021 [US3] Make `_check_section` in `wfctl/_tracker.py` report an `edit` entry missing any of `{id}`, `{field}`, or `{value}`, with the reason in a comment; verify with T020
- [X] T022 [P] [US3] Add tests in `tests/test_tracker.py` that a two-field edit against a backend with no `edit`, against no configured tracker, and against an invalid config each prints its notice once, makes no backend call, and exits 0 (FR-009, clarify Q1)

### Implementation for User Story 3

- [X] T023 [US3] Add an `edit` row with `{id}`, `{field}`, and `{value}` to the verb table in `wfctl/agents/skills/scaffold-tracker/SKILL.md`, and a note that a tracker whose flags aren't `--title` and `--body` points the verb at a script (FR-011). Extend `test_scaffold_skill_documents_every_verb_the_contract_allows` in `tests/test_tracker.py`, or add a test beside it, so it checks the `edit` row names its three placeholders and the script note, not only that `` `edit` `` appears (plan-review PR-004); verify with that test, and with `uv run wfctl install-skills` followed by reading the installed skill
- [x] T024 [US3] Validate Phase 5 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: a backend author is asked about `edit`, and a wrong template is a finding instead of a silent overwrite.

---

## Phase 6: Polish and end-to-end checks

- [X] T025 [P] Refresh the GitHub tracker and check it with `uv run wfctl install-skills --tracker github` and `uv run wfctl tracker-check`, confirming `edit` is in the verb list (quickstart step 1)
- [X] T026 [P] Add `edit` to the verb list and the list of recorded writes in `docs/reference.md` under Issue trackers, and to the list of recorded writes in the Safety section of `AGENTS.md` (plan-review PR-005); verify by reading both sections against `ALLOWED` and `_RECORDED_VERBS`
- [X] T027 Run quickstart steps 2 to 4 against a real GitHub issue the user names, with a body holding several lines, backticks, and quotes. Confirm the body on GitHub, one `issue-edit` line in the session's `events.jsonl`, and that both usage errors send nothing. The edit writes to the tracker, so ask the user before running it
- [x] T028 Validate the feature with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `uv run wfctl verify`, and `uv run wfctl doctor` — merge gate

---

## Dependencies and execution order

### Phase dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: T003 before T004, since both reshape `dispatch`. Blocks every story.
- **US1 (Phase 3)**: depends on Phase 2.
- **US2 (Phase 4)**: depends on T010 and T011, since it adds failure handling to the edit function and to `issue_cmd`.
- **US3 (Phase 5)**: T020 to T022 depend on Phase 2 only, and T022 also needs T010. T023 is independent of the code.
- **Polish (Phase 6)**: depends on every story.

### Within each story

- Tests first, and they fail before the implementation task.
- `wfctl/_tracker.py` tasks run in order (T010, T018, T021), since they edit one file.

### Parallel opportunities

- T006 to T009 are separate tests and can be written together.
- T012 (`github.json`) and T023 (`scaffold-tracker`) touch package data only, and can run beside any code task.
- T025 and T026 can run together.

## Parallel example: User Story 1

```text
Task: "T006 tests for one-field and two-field calls in tests/test_tracker.py"
Task: "T009 tests for issue-edit records in tests/test_tracker_records_issue_verbs.py"
Task: "T012 edit entry in wfctl/agents/trackers/github.json"
```

## Implementation strategy

### MVP first

1. Phases 1 and 2.
2. Phase 3. An edit works and is recorded, and the GitHub backend declares it.
3. Stop and validate with T013.

### Incremental delivery

1. US1 gives the agent a way to edit an issue without `gh`.
2. US2 makes a failed edit report what changed.
3. US3 makes the verb safe for other backends to declare.
4. Phase 6 checks the real tracker and the docs.
