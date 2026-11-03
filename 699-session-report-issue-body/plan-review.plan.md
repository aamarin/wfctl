# Implementation Plan: Session report issue body

**Branch**: `699-session-report-issue-body` | **Date**: 2026-11-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from the branch's spec folder, `spec.md`

## Summary

When the session report prints a handoff, the console's `Issue (tracker text)` section prints the issue's header fields and one line naming `wfctl issue view <id>`, and leaves out the body. With no handoff, the section prints as it does today. The JSON payload is unchanged.

The code change is confined to the console renderer in `wfctl/_session_report.py`. `_trim_issue` already splits the tracker text at its `--` line to trim empty header fields, so it also drops the body when asked to, and tells the caller whether it did. `render_session_report` passes whether there is a handoff, and prints the pointer line only when the body was dropped.

The pointer line prints with `markup=False`, like every other line the report writes. It is flush left, and that is safe because its only variable is `payload["issue"]`, the key wfctl takes from the branch name and not from the tracker. No tracker text reaches a flush-left line.

The `start-session` skill changes too (FR-007). Its step 8 row for an issue branch whose summary names no first action reads the issue to choose the next command, and asks the user when the issue body is empty. A summary can exist and still name no first action, so that row now reads the issue with `wfctl issue view <id>` when the report left the body out. The row appears twice, in `wfctl/agents/skills/start-session/SKILL.md` and in `references/rationale.md`, and both copies change.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `rich`, already used by the renderer. Nothing new.  
**Storage**: N/A. The handoff and the issue text are already read by `build_session_report`.  
**Testing**: `uv run pytest -q`, with new and changed tests in `tests/test_session_report.py` that assert on console output from a non-terminal `Console`.  
**Target Platform**: Any platform wfctl runs on.  
**Project Type**: CLI  
**Performance Goals**: No new tracker or file reads. The report's latency is unchanged.  
**Constraints**: The JSON payload keeps its keys and values (FR-005). The pointer line is flush left, since it is wfctl's own text, and the tracker text above it stays indented. Minimal-complexity bias.  
**Scale/Scope**: One function's signature and one call site, one sentence in two copies of a skill row, plus tests and a release note.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repo has no `.specify/memory/constitution.md`. The gates below come from `AGENTS.md`'s Definition of done and its Testing conventions, and the substitution is recorded in Complexity Tracking.

- [x] Validation plan exists: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `uv run wfctl doctor`, plus the two manual runs of `uv run wfctl status --session` in `quickstart.md`. The skill edit is under `wfctl/agents/`, so it is also installed with `uv run wfctl install-skills` and read back in the installed `.agents/skills/start-session/SKILL.md`.
- [x] Complexity is justified: no new abstraction, module, or dependency. One keyword argument on an existing private helper.
- [x] Ownership is stated: the session report's console renderer decides whether the body prints, from `payload["handoff"]`, which the same renderer already uses to print the `Handoff` section. The tracker can't decide it, because it doesn't know whether a handoff exists. `build_session_report` shouldn't, because the JSON keeps the body. Recorded as `wfctl arch none --context session-continuity`.
- [x] A release note is committed: `changes/699.change.md`, category `change`, since every session start prints less (`change-carries-release-note`).
- [x] Tests that assert on output pin `NO_COLOR` or use a console with no color system. The existing `_render` helper uses `color_system=None`.
- [x] Imports stay within the Context Map: no new import is added (`contexts-are-packages`).

## Design records

Design records: none. `design.md` records no level-3 decision, and the `brainstorm.software-design` pass was claimed with a reason.

## Phase 0 and Phase 1 artifacts

- `research.md`: the three decisions, which are the handoff condition, the command in place of a URL, and where the cut happens.
- `data-model.md`: no new data. It describes the two inputs the renderer already reads.
- `contracts/console-issue-section.md`: the exact console output of the section in each of its four states.
- `quickstart.md`: the manual check on a branch with a handoff and a branch without one.

## Project Structure

### Documentation (this feature)

```text
<FEATURE_DIR>/
├── design.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── console-issue-section.md
└── tasks.md             # /speckit.tasks
```

### Source Code (repository root)

```text
wfctl/
├── _session_report.py   # _trim_issue gains keep_body; render_session_report passes it and prints the pointer line
└── agents/skills/start-session/
    ├── SKILL.md                  # step 8's issue-branch row reads the issue with `wfctl issue view` when the body was left out
    └── references/rationale.md   # the same row's copy

tests/
├── test_session_report.py
└── test_start_session_asks_conditionally.py   # pins the row's new sentence

changes/
└── 699.change.md
```

**Structure Decision**: The change stays in `wfctl/_session_report.py`, which already owns the console rendering of the session report (`session-start-reads-branch-progress`). No new module.

### Tests that change

The `_readers` fixture's default handoff is a non-empty summary, so after this change every default report hides the body. Two existing tests assert on body lines and need `handoff=lambda: None` to keep testing what they were written for:

1. `test_empty_issue_fields_are_left_out` asserts that `body text` and the body's own `labels:` line print.
2. `test_an_issue_body_cannot_print_a_line_that_reads_as_the_reports_own` asserts that the forged body's lines print indented. That protection still matters on a branch with no handoff, which is the only case where the body prints.

New tests, one per state in the contract, plus the JSON:

1. With a handoff and a `--` line, the header prints, the pointer line prints flush left with the issue key, and no body line prints.
2. With no handoff, the body prints and the pointer line doesn't.
3. With a handoff and no `--` line, the whole text prints and the pointer line doesn't.
4. With a handoff, the payload's `issue_view` still holds the body.
5. With an empty-string handoff, the body is still hidden, since the `Handoff` heading still prints. This catches the `is None` test turning into a truthiness test.
6. With a handoff and an empty body after the `--` line, the header and the pointer line print.
7. With a handoff and empty header fields, the empty fields are trimmed and the body is cut in the same output.
8. In `test_start_session_asks_conditionally.py`, the issue-branch row names `wfctl issue view` for a report that left the body out.

The reason-code case is covered by `test_every_reason_code_prints_on_its_line_and_none_is_left_out`, which is unchanged.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates taken from `AGENTS.md` rather than a constitution | The repo has no `.specify/memory/constitution.md` | A gate with no source is decorative, and `AGENTS.md`'s Definition of done is the documented bar for a code change here |
