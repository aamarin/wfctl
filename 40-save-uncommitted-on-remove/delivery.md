# Delivery Plan: Save unsaved work when a worktree is removed (40)

**Feature**: `40-save-uncommitted-on-remove` | **Date**: 2026-10-15
**Source**: `/Users/andremarin/Development/wfctl-specs/40-save-uncommitted-on-remove/tasks.md` (47 tasks)
**Parent issue**: #40

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| Not opened yet | T001 - T047 | `wfctl/_archive.py` (modified), `wfctl/cli.py` (modified), `wfctl/_copy_out.py` (created), `wfctl/_spec_store.py` (created), `wfctl/_paths.py` (modified), `wfctl/_workmux.py` (modified), `wfctl/_completion.py` (modified), `wfctl/agents/configs/workmux/.workmux.yaml` (modified), `.workmux.yaml` (comment only), `docs/reference.md` (modified), `docs/ponytail-debt.md` (modified), `tests/test_archive_unsaved.py` (created), `tests/test_copy_out.py` (created), `tests/test_spec_store.py` (created), `tests/test_worktree_remove.py` (created), `tests/test_paths.py` (modified), `tests/test_workmux.py` (modified), `tests/test_archive_specs.py` (deleted) | L | T045 is green, Andre has run quickstart step 4 (T047), and the #600 choices are settled |

**Rationale**: Single PR. The change touches 18 files, which is past the size where a split is discussed, and Andre chose one PR on 2026-10-15. We didn't choose to split because every story is an acceptance criterion on #40, and none of them changes a real removal until Story 4 wires the hook. A PR that stopped short of Story 4 would add commands nobody calls. Seven of the 18 files are new or deleted, so most of the diff reads as additions rather than edits to existing code.

We also didn't choose to move Story 5 (`save_on_remove`) into its own issue. It is the only story the hook doesn't need, but splitting it would take a criterion off #40 and open a second issue for a small amount of work.

**PR closes**: `Closes #40`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #40 | T001 - T047 | `[40] Removing a worktree with --force deletes work that exists nowhere else` | L | The single PR above |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the whole feature, so it closes the issue the branch already exists for. There is nothing to create.

---

## Parallelization Waves

Before T007, T009, T013, T023, and T028 start, the matching items in #600 need Andre's answers. Each of those tasks implements a choice #600 leaves open, so starting one without the answer builds the version that may be rejected.

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 | If either git assumption test fails, stop and revisit research R5 |
| 1 | Parallel | (T003 → T004 → T005) ‖ (T018 ‖ T019 ‖ T020, then T021 ‖ T022) | Story 3 depends on Setup only, so its tests and helpers run beside Foundational |
| 2 | Parallel | (T006 → T007 → T008 → T009 → T010 → T011) ‖ (T023 → T024 → T025) | T024 and T004 both edit `wfctl/cli.py`. Add the `store` group after T004 has landed, and keep the two groups apart in the file |
| 3 | Sequential | T012 → T013 → T014 → T015 → T016 → T017 | Story 2 writes the same `_archive.check` and test file as Story 1 |
| 4 | Sequential | (T026 ‖ T027) → T028 + T029 + T030 → T031 → T032 → T033 → T034 | T028, T029, and T030 are one commit, since splitting them leaves a removal hook that calls a command that doesn't exist |
| 5 | Sequential | (T035 ‖ T036) → T037 → T038 → T039 → T040 | Runs after Story 4, because T030 deletes code from `_archive.py` and `cli.py` that Story 5 also edits |
| 6 | Parallel | T041 ‖ T042 ‖ T043 | Different files, all docs or comments |
| 7 | Sequential | T044 → T045 → T046 → T047 | T044 merges `main` in only if #359 has merged. T047 is Andre's |

**Single-agent order**:
T001 → T002 → T003 → T004 → T005 → T018 → T019 → T020 → T021 → T022 → T006 → T007 → T008 → T009 → T010 → T011 → T023 → T024 → T025 → T012 → T013 → T014 → T015 → T016 → T017 → T026 → T027 → T028 → T029 → T030 → T031 → T032 → T033 → T034 → T035 → T036 → T037 → T038 → T039 → T040 → T041 → T042 → T043 → T044 → T045 → T046 → T047

---

## Agent Fanning Instructions

The only real parallelism is the Story 3 track in waves 1 and 2, which lives almost entirely in new files. Every other wave is sequential, because the stories share `wfctl/_archive.py`, `wfctl/cli.py`, and `tests/test_archive_unsaved.py`. One agent on the main track and one on the Story 3 track is the most that helps.

**Wave 1 - 2 fanning (2 agents):**

**Agent A prompt:**
```
You are implementing #40 in the worktree at
/Users/andremarin/Development/wfctl/wt/40-save-uncommitted-on-remove.
Read tasks.md in the directory `uv run wfctl feature-paths` prints as FEATURE_DIR.
Do T003, T004, and T005, then T006 - T011, in order. Write each test first and
check that it fails before writing the code it covers. Don't touch
wfctl/_copy_out.py, wfctl/_spec_store.py, tests/test_copy_out.py,
tests/test_spec_store.py, or the store group in wfctl/cli.py, since another
agent owns them. Before T007 and T009, read #600 items 2 and 5 and follow
Andre's answers there. If an item has no answer yet, stop and say so.
Run every check through `uv run`. Commit after each task.
```

**Agent B prompt:**
```
You are implementing Story 3 of #40 in the worktree at
/Users/andremarin/Development/wfctl/wt/40-save-uncommitted-on-remove.
Read tasks.md in the directory `uv run wfctl feature-paths` prints as FEATURE_DIR.
Do T018 - T022, then T023 - T025. Write each test first and check that it fails
before writing the code it covers. Your files are wfctl/_copy_out.py,
wfctl/_spec_store.py, is_main_checkout in wfctl/_paths.py, and their tests. Wait
until T004 has landed before adding the store group to wfctl/cli.py (T024), and
add it apart from the archive group. Before T023, read #600 items 3 and 4,
since the store() signature must match #359's. If an item has no answer yet,
stop and say so. Run every check through `uv run`. Commit after each task.
```

**Fan-in gate after Wave 2:** `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/`
