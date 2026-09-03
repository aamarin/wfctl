# Delivery Plan: Merge install mode for hooks (#85)

**Feature**: `85-hook-merge-install-mode` | **Date**: 2026-09-01
**Source**: `specs/85-hook-merge-install-mode/tasks.md` (26 tasks)
**Parent issue**: #85

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| #1 | T001-T026 (all) | `wfctl/_settings.py` (created), `wfctl/cli.py` (modified), `tests/test_settings_merge.py` (created), `tests/test_install_hook_merge.py` (created), `tests/test_skill_cross_references.py` (modified) | S (5 files) | All 26 tasks complete; `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` green; every `quickstart.md` scenario confirmed |

**Rationale**: Single PR. The file-touch matrix lands at S (5 files), well under
the L threshold (8-12) where a split gets flagged for discussion. Applying the
four PR-boundary signals: file conflict risk is real but sequenceable (US2 and
US3 both extend `cli.py` functions US1 establishes, never edit the same lines
concurrently); reviewability favors bundling — US2's `_check_managed_hooks`
and US3's `_unmerge_hooks` only make sense next to the `_merge_hooks`/manifest
shape US1 introduces, so a reviewer seeing them apart would re-derive US1's
design twice; each story is a mergeable increment on its own, but nothing
requires shipping them separately since #85 was filed and estimated ("Medium")
as one feature, not an epic with sub-issues. Story independence (signal 4) is
real — see spec.md's three Independent Test blocks — but the framework treats
that as a split *candidate*, not a trigger, and the other three signals don't
corroborate a split here.

**PR closes**: `Closes #85`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #85 | T001-T026 | `feat(install): a merge install mode, so wfctl can manage hooks in a settings file the consumer owns` | Medium (matches #85's own estimate) | PR #1 |

**Grouping pattern**: Single issue.
**Rationale**: #85 already exists as one filed issue, not an epic — the
delivery unit the tracker expects is one PR closing it. No sub-issues to
create; nothing under "Getting this spec into a sub-issue worktree" applies.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | Baseline check, no edits — must be green before anything else starts |
| 1 | Parallel | T002 ‖ T004 | Different files (`_settings.py` vs. `cli.py` constants); both Foundational |
| 2 | Sequential | T003 | Tests T002; same file as T002, must follow it |
| 3 | Sequential | T005 | Foundational checkpoint — fan-in gate on T002, T003, T004 |
| 4 | Parallel | T006 ‖ T007 ‖ T008 | US1 tests; T006 and T008 append distinct functions to the same new file (`test_install_hook_merge.py`) — genuinely parallel-safe since neither edits the other's lines, but a single agent writing all three in sequence avoids even a merge-order question |
| 5 | Parallel | T009 ‖ T012 | `_read_settings`/`_write_settings`/`_json_indent` vs. the `hook user-prompt` command — independent functions, same file, no shared state |
| 6 | Sequential | T010 | Depends on T002, T004, T009 |
| 7 | Sequential | T011 | Depends on T010 |
| 8 | Sequential | T013 | US1 checkpoint — fan-in gate on T006-T012. **MVP boundary**: stop here to validate independently if desired |
| 9 | Parallel | T014 ‖ T015 ‖ T020 | US2 and US3 tests; all three append to `test_install_hook_merge.py` — same coordination note as Wave 4 |
| 10 | Parallel | T016 ‖ T017 ‖ T021 | Each depends only on T011/T004, not on one another — `tasks.md` lists no dependency between T016 and T017 despite both being US2. `_check_managed_hooks` (T017, US2) and `_unmerge_hooks` (T021, US3) touch different `cli.py` functions |
| 11 | Parallel | T018 ‖ T022 | T018 depends on T017 (doctor wiring); T022 depends on T021 and T011 (uninstall wiring) — independent of each other |
| 12 | Parallel | T019 ‖ T023 | US2 and US3 checkpoints — independent fan-in gates |
| 13 | Parallel | T024 ‖ T025 | Polish — quickstart pass and live-session check; both depend on all three stories complete, not on each other |
| 14 | Sequential | T026 | Full-suite gate — final fan-in, the whole feature's merge condition |

**Single-agent order** (recommended for this S-size feature): T001 → T002 →
T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 →
T014 → T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022 → T023 → T024 →
T025 → T026.

---

## Agent Fanning Instructions

Single agent recommended for this S-size feature (5 files, one PR). The wave
table above is provided for reference and for a team that wants to split
Wave 4 or Wave 9's test-writing across two people — it is not a fan-out this
feature needs to reach a reasonable timeline.
