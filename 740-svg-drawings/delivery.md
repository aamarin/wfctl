# Delivery Plan: SVG drawings (740)

**Feature**: `740-svg-drawings` | **Date**: 2026-11-14
**Source**: `wfctl-specs/740-svg-drawings/tasks.md` (64 tasks)
**Parent issue**: none

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| PR 1 | T001–T029 | `wfctl/_paths.py`, `wfctl/arch/_drawing.py` (created), `wfctl/arch/_records.py`, `tests/test_design_gate_drawing.py`, `tests/test_arch_labels.py`, `tests/test_arch_drawing_svg.py` (created), `tests/test_arch_diagram_kinds.py`, `tests/pipeline_payload_snapshot.json`, `changes/740.addition.md` (created) | M (9 files) | T008, T019, T024, and T029 pass, and the three records on the branch are accepted |
| PR 2 | T030–T048, T063 | `wfctl/arch/_drawing.py`, `wfctl/arch/_records.py`, `wfctl/arch/__init__.py`, `wfctl/_review_gate.py`, `wfctl/cli.py`, `wfctl/_paths.py`, `wfctl/_record_gate.py`, `wfctl/_evidence.py`, 10 test files (`test_arch_drawing_fingerprint.py`, `test_redraw_only.py`, and `test_paths_redraw.py` created), its release note | L (19 files) | PR 1 merged, T048 passes, and the user has run quickstart §6 (T063) |
| PR 3 | T049–T062, T064 | 12 files under `wfctl/agents/skills/` (`design-levels/references/drawing-style.md` created), `tests/test_drawing_style_links.py` (created), `docs/reference.md`, `docs/architecture/record-drawing-can-be-svg.md`, its release note | L (16 files, all prose but one test) | PR 2 merged, T057, T059, and T062 pass, and the user has run quickstart §7 (T064) |

**Rationale**: Multiple PRs. One PR would touch about 38 files, so the work is split by what a reviewer has to judge. PR 1 is the parser and the checks, PR 2 is the guard and git changes behind the sign-off, and PR 3 is skill and doc prose. Each PR leaves `main` working, and they merge in order: PR 2 needs PR 1's SVG reader, and PR 3's style file teaches the sign-off that PR 2 delivers.

Until PR 2 merges, a change to an accepted record's SVG isn't flagged. No record relies on an SVG alone until T058 removes this feature's mermaid copy, which is why T058 is in PR 3.

**PR closes**: PR 1 `Closes #740`, PR 2 `Closes #769`, and PR 3 `Closes #770`.

### Changes to tasks.md for the split

1. T002 writes PR 1's release note, so it leaves out the sign-off (FR-018). PR 2 and PR 3 each commit their own note, named for their issue.
2. T063 moves to PR 2, since quickstart §6 checks the sign-off.
3. The corpus script from T001 lives in a session scratchpad, so it doesn't survive into another worktree. PR 2 and PR 3 each recreate it and run `before` on their base before the first edit to `wfctl/arch/_records.py`. In PR 3, T061 then expects only the `record-drawing-can-be-svg` difference, since the `no drawing` wording changed in PR 1.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #740 | T001–T029 | `[740] Records and views can carry an SVG drawing that wfctl checks` | M | PR 1 |
| #769 | T030–T048, T063 | `[740] Accepting a record signs off its SVG drawing` | L | PR 2 |
| #770 | T049–T062, T064 | `[740] Skills and templates teach SVG drawings by default` | L | PR 3 |

**Grouping pattern**: Sub-feature split, in merge order, with no parent epic.
**Rationale**: #740 closes with PR 1, since PR 1 delivers what its title asks for, and the two new issues carry the rest.

### Getting this spec into a sub-issue worktree

This repo records a spec root outside the working tree, so `wfctl feature-paths` in each sub-issue worktree resolves this folder through the table above, and nothing has to be copied.

---

## Parallelization Waves

### PR 1

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Parallel | T001 ‖ T002 | T001 runs before any edit to `_records.py` |
| 1 | Sequential | T003 → T004 | test first |
| 2 | Sequential | T005 → T006 → T007 | the fence code moves before `_records.py` reads the summary |
| 3 | Sequential | T008 | merge gate, corpus unchanged |
| 4 | Sequential | T009, T010, T011, T012 | one test file, so one agent |
| 5 | Sequential | T013 → T014 → T015 → T016 → T017 → T018 | all but T013 edit `_records.py` |
| 6 | Sequential | T019 | merge gate |
| 7 | Sequential | T020, T021 → T022 → T023 → T024 | US2 |
| 8 | Sequential | T025, T026 → T027 → T028 → T029 | US3 |

**Single-agent order**: T001 → T029 in order. Almost every task edits `_drawing.py`, `_records.py`, or `test_arch_drawing_svg.py`, so fanning out buys nothing.

### PR 2

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | recreate the corpus script and run `before` | no edits yet |
| 1 | Parallel | T030, T031, T032 ‖ T033 ‖ T034 ‖ T035 ‖ T036 ‖ T037 ‖ T038 | tests, each lane its own file; T030–T032 share one |
| 2 | Parallel | T041 ‖ T046 ‖ T039 → T040 | the guard, the git side in `_paths.py`, and the fingerprint |
| 3 | Sequential | T042 → T043 → T044 | `cli.py` and `_records.py` |
| 4 | Sequential | T045 → T047 | needs T040 and T046; T047 edits `cli.py` after T042 |
| 5 | Sequential | T048 | merge gate |
| 6 | Sequential | T063 | the user runs quickstart §6 from their own terminal |

### PR 3

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T049 → T050 | the test, then the style file the skills link |
| 1 | Parallel | T051 ‖ T052 ‖ T053 ‖ T054 ‖ T055 ‖ T056 ‖ T060 | each edits a different file |
| 2 | Sequential | T057 | merge gate, including a fresh agent drawing one SVG |
| 3 | Sequential | T058 → T059 | the record drops its mermaid copy |
| 4 | Sequential | T061 → T062 | corpus check, then the full check run |
| 5 | Sequential | T064 | the user runs the phone check |

---

## Agent Fanning Instructions

PR 1 uses a single agent.

PR 2 can fan wave 1 to one agent per test file and wave 2 to three agents: one on `wfctl/_review_gate.py` (T041), one on `wfctl/_paths.py` (T046), and one on `wfctl/arch/_drawing.py` and `_records.py` (T039, T040). Fan-in gate after each wave: `uv run pytest -q`.

PR 3 can fan wave 1 to one agent per skill file. Each agent reads `drawing-style.md` and the plan's skill-prose table first. Fan-in gate: `uv run pytest tests/test_drawing_style_links.py -q`, then `uv run wfctl install-skills`.
