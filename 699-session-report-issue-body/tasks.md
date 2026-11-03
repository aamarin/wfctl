---
description: 'Task list for the session report issue body'
---

# Tasks: Session report issue body

**Input**: The design documents in this branch's spec folder.
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, and `contracts/console-issue-section.md`.

**Tests**: Every task names the test or command that verifies it. Tests assert on console output from the existing `_render` helper, which uses `color_system=None`.

**Organization**: Both user stories are P1, and the change is only correct when both hold. Story 1 hides the body when the report prints a handoff. Story 2 keeps it when there's no handoff.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel, since it changes a different file and depends on no incomplete task.
- **[Story]**: The user story the task belongs to.

## Design records

Design records: none. `design.md` records no level-3 decision, and the `brainstorm.software-design` pass was recorded as not applying, with a reason.

---

## Phase 1: Setup

**Purpose**: The release note, which `wfctl verify` and the `release-note` CI job both require.

- [X] T001 Create `changes/699.change.md` with `uv run towncrier create 699.change.md --content "…"`, saying in one sentence that a session with a handoff no longer prints the issue body, and names `wfctl issue view` instead. Verify with `uv run wfctl verify`.

---

## Phase 2: Foundational

**Purpose**: Keep two existing tests testing what they were written for. The `_readers` fixture's default handoff is a non-empty summary, so once the body hides, both would fail on lines that no longer print.

- [X] T002 In `tests/test_session_report.py`, pass `handoff=lambda: None` in `test_empty_issue_fields_are_left_out` and `test_an_issue_body_cannot_print_a_line_that_reads_as_the_reports_own`. The second still matters, since a branch with no handoff is the only case where the body prints. Verify with `uv run pytest -q tests/test_session_report.py`, which passes before and after the change.
- [X] T003 Validate Phase 2 with `uv run pytest -q tests/test_session_report.py` — merge gate

---

## Phase 3: User Story 1 - A session with a handoff skips the issue body (Priority: P1) 🎯 MVP

**Goal**: When the report prints a handoff, the `Issue (tracker text)` section prints the header fields and one flush-left pointer line, and no body. The JSON keeps the body.

**Independent Test**: Build a report with a handoff and an issue whose text has a header, a `--` line, and a body. The console output carries the header and the pointer line, and none of the body's lines.

### Verification

- `tests/test_session_report.py`: the new tests in T004 - T009.
- `tests/test_start_session_asks_conditionally.py`: the new assertion in T013.
- `uv run wfctl status --session` in this worktree, per `quickstart.md`.

### Tests for User Story 1

Write these first and confirm they fail before T010.

- [X] T004 [P] [US1] In `tests/test_session_report.py`, add a test that a report with a handoff and a `--` line prints the header, prints ``Body left out, since the handoff below names the work. `wfctl issue view 699` prints it.`` flush left with the issue key, and prints no body line (contract state 1, FR-001, FR-002).
- [X] T005 [P] [US1] In `tests/test_session_report.py`, add a test that a report with a handoff and tracker text with no `--` line prints the whole text and no pointer line (contract state 3, FR-004).
- [X] T006 [P] [US1] In `tests/test_session_report.py`, add a test that with a handoff, the payload's `issue_view` still holds the body (FR-005).
- [X] T007 [P] [US1] In `tests/test_session_report.py`, add a test that an empty-string handoff still hides the body, since the `Handoff` heading still prints (FR-006). It fails if the `is None` check becomes a truthiness check.
- [X] T008 [P] [US1] In `tests/test_session_report.py`, add a test that with a handoff and an empty body below the `--` line, the header and the pointer line print.
- [X] T009 [P] [US1] In `tests/test_session_report.py`, add a test that with a handoff and empty header fields, the empty fields are trimmed and the body is cut in the same output.

### Implementation for User Story 1

- [X] T010 [US1] In `wfctl/_session_report.py`, give `_trim_issue` a `keep_body` keyword argument and return `(text, cut)`. When `keep_body` is false and the text has a `--` line, return the trimmed header without the `--` line or the body, and `cut=True`. Text with no `--` line returns whole with `cut=False`. Update the docstring to say why the body can be dropped. Verify with T004 - T009.
- [X] T011 [US1] In `render_session_report` in `wfctl/_session_report.py`, call `_trim_issue(payload["issue_view"], keep_body=payload["handoff"] is None)`, and when it cut, print the pointer line flush left with `markup=False`, using `payload["issue"]` as the id. Extend the comment above the section to say why the pointer line can be flush left: its only variable is the issue key wfctl takes from the branch name, not from the tracker. Verify with T004 - T009 and `uv run pytest -q tests/test_session_report.py`.

### Skill row for User Story 1 (FR-007)

- [X] T012 [P] [US1] In `wfctl/agents/skills/start-session/SKILL.md` (step 8, the issue-branch row whose summary names no first action, near line 106) and `wfctl/agents/skills/start-session/references/rationale.md` (the same row, near line 199), add one sentence: when the report left the body out, read the issue with `wfctl issue view <id>`. Both copies get the same sentence. Verify with T013.
- [X] T013 [US1] In `tests/test_start_session_asks_conditionally.py` (the tests that find that row by `_ISSUE_NO_ANSWER`), assert that the issue-branch row names `wfctl issue view` for a report that left the body out. Verify with `uv run pytest -q tests/test_start_session_asks_conditionally.py`.
- [X] T014 [US1] Validate User Story 1 with `uv run pytest -q tests/test_session_report.py tests/test_start_session_asks_conditionally.py` — merge gate

---

## Phase 4: User Story 2 - A session without a handoff still gets the body (Priority: P1)

**Goal**: A branch with no `session-summary.md` prints the issue section as it does today.

**Independent Test**: Build a report with no handoff. The console output carries the body, unchanged from today, and no pointer line.

### Verification

- `tests/test_session_report.py`: the new test in T015, and the two tests T002 changed.
- `test_every_reason_code_prints_on_its_line_and_none_is_left_out`, unchanged, covers contract state 4, where the issue read returned a reason code.
- `XDG_STATE_HOME="$(mktemp -d)" uv run wfctl status --session`, per `quickstart.md`.

- [X] T015 [US2] In `tests/test_session_report.py`, add a test that a report with no handoff prints the header, the `--` line, and the body, and no pointer line (contract state 2, FR-003). Verify with `uv run pytest -q tests/test_session_report.py`.
- [X] T016 [US2] Validate User Story 2 with `uv run pytest -q tests/test_session_report.py` — merge gate

---

## Phase 5: Polish and cross-cutting checks

**Purpose**: The Definition of done in `AGENTS.md`, and the manual checks that tests can't make.

- [X] T017 Run `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy`, and all three pass.
- [X] T018 Run `uv run wfctl install-skills`, then read the installed `.agents/skills/start-session/SKILL.md` and `.claude/skills/start-session/SKILL.md` and confirm the step 8 row carries the new sentence.
- [X] T019 Run the quickstart. `uv run wfctl status --session` in this worktree prints no body and prints the pointer line. `XDG_STATE_HOME="$(mktemp -d)" uv run wfctl status --session` prints the body. `uv run wfctl status --session --json` holds the body in `issue_view` in both runs.
- [X] T020 Run `uv run wfctl doctor` and `uv run wfctl verify`, and both pass — merge gate

---

## Dependencies and execution order

- Phase 1 has no dependencies.
- Phase 2 comes before T010 and T011, since those two tasks are what break the unpinned tests.
- In Phase 3, T004 - T009 come before T010, and T010 comes before T011. T012 and T013 don't depend on the renderer, so they can run beside T004 - T011.
- Phase 4's test, T015, passes before and after T010 and T011, so it can be written at any point. Its merge gate, T016, runs after T011.
- Phase 5 runs after every earlier phase.

### Parallel opportunities

- T004 - T009 are separate tests in one file, so one agent writes them together rather than in parallel.
- T012 changes the skill files, and T004 - T011 change the renderer and its tests, so the two can run at the same time.

## Implementation strategy

The whole change is one PR. Story 1 alone would hide the body on branches with no handoff only if T011 tested the wrong condition, which T007 and T015 catch, so the two stories ship together.

1. T001 - T003: release note and the two pinned tests.
2. T004 - T011: failing tests, then the renderer change.
3. T012 - T013: the skill row, in parallel with step 2.
4. T015 - T016: the no-handoff test.
5. T017 - T020: the full checks, install, and quickstart.
