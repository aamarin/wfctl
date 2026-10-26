# Delivery Plan: A new task reopens the implement step (264)

**Feature**: `264-sentinel-goes-stale` | **Date**: 2026-10-10
**Source**: `264-sentinel-goes-stale/tasks.md` (32 tasks)
**Parent issue**: #264

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (to be opened) | T001 - T032 | `wfctl/_completion.py` (created), `wfctl/_evidence.py` (modified), `wfctl/cli.py` (modified), `wfctl/agents/commands/speckit.implement.md` (modified), `docs/architecture/new-task-reopens-implement.md` (modified), `tests/test_completion_record.py` (created), `tests/test_pipeline_commands.py` (modified), `tests/test_storyctl.py` (modified), `tests/test_pipeline_payload_snapshot.py` (modified), `tests/pipeline_payload_snapshot.json` (regenerated), `tests/test_skill_cross_references.py` (modified) | L | `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` pass, `uv run wfctl doctor` is green, both arms of `quickstart.md` are reproduced by hand, and the review panel has run |

**Rationale**: Single PR, although 11 files puts it at L by count. Four of
the files are source and seven are tests or the snapshot, so the change a
reviewer reads is four files. The reader (Story 1) and the command that writes
the copy (Story 2) cannot be reviewed apart, since the reader has nothing to
compare against until the command writes a copy, and the copy changes nothing
until the reader uses it. A PR holding only the reader would also reopen every
finished story with an incomplete task, because every record written by hand
has no copy. Stories 3 and 4 add only tests over behavior Story 1 builds.

The planning files `research.md`, `data-model.md`, and `quickstart.md` are
also edited (T028 - T030), but they sit in the spec store outside the working
tree and are not part of the PR's diff.

`wfctl/cli.py` is also being restructured by #293. T018 adds one new command
to `step_app` and touches nothing else in the file, and the PR says so.

**PR closes**: `Closes #264`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #264 | T001 - T032 | `[264] Nothing invalidates implement-complete.md, so a story that gains new tasks reports the old verdict` | L | the single PR |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the whole feature, and #264 already exists, so
there is nothing to create.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | Baseline suite, lint, and type check before any change |
| 1 | Parallel | T002 ‖ T003 | Both in `tests/test_completion_record.py` but for separate functions; each must fail before T004 and T005 |
| 2 | Sequential | T004 → T005 → T006 | The record format, then task matching, then the Phase 2 merge gate |
| 3 | Parallel | T007 → T008 ‖ T009 | T007 and T008 share `tests/test_completion_record.py`; T009 is in `tests/test_pipeline_commands.py` |
| 4 | Sequential | T010 → T011 → T012 → T013 → T014 → T015 | The reader change, the existing tests it moves, the snapshot rows, the regenerated snapshot, then the Phase 3 merge gate |
| 5 | Parallel | T016 ‖ T017 | T016 in `tests/test_pipeline_commands.py`, T017 in `tests/test_skill_cross_references.py` |
| 6 | Sequential | T018 → T019 → T020 → T021 | The command, the implement instruction, the install check, then the Phase 4 merge gate |
| 7 | Sequential | T022 → T023 → T024 → T025 → T026 | Stories 3 and 4 both add to `tests/test_completion_record.py`, so they run one after the other |
| 8 | Parallel | T027 ‖ T028 → T029 ‖ T030 | Each edits a different file, except T029, which follows T028 because both edit `research.md` |
| 9 | Sequential | T031 → T032 | The hand reproduction after the quickstart is corrected, then the final gate |

**Single-agent order** (recommended for this feature):
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 →
T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022 →
T023 → T024 → T025 → T026 → T027 → T028 → T029 → T030 → T031 → T032

---

## Agent Fanning Instructions

A single agent is recommended. `tests/test_completion_record.py` is written by
four phases and `tests/test_pipeline_commands.py` by two, so parallel agents
would conflict on both. The only waves with real parallelism are 1, 3, 5, and
8, and each is a few minutes of work, which costs less than reconciling two
agents' edits to the same test file. The wave table is kept for reference.
