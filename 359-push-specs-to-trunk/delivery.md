# Delivery Plan: wfctl stores a branch's spec dir on its spec store's remote (359)

**Feature**: `359-push-specs-to-trunk` | **Date**: 2026-10-15
**Source**: `tasks.md` in this feature directory (53 tasks)
**Parent issue**: #359

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (opened at the end of `implement`) | T001–T053 | `wfctl/_spec_store.py` (created), `wfctl/_hook.py` (modified), `wfctl/_evidence.py` (modified), `wfctl/_pipeline.py` (modified), `wfctl/cli.py` (modified), `wfctl/agents/commands/store-specs.md` (created), `wfctl/agents/skills/end-session/SKILL.md` (modified), `tests/test_spec_store.py` (created), `tests/test_store_specs_pass.py` (created), `tests/test_check_specs.py` (created), `tests/test_archive_specs.py` (modified), `tests/test_guard_entry.py` (modified), `tests/conftest.py` (modified), `pyproject.toml` (modified) | XL by file count, 7 of the 14 being tests and test config | The definition of done is green, every step in `quickstart.md` has run, and the review panel has run |

**Rationale**: Single PR. Andre chose it on 2026-10-15 over splitting
`wfctl check specs` into its own issue. The stories all build on one new
module and edit `wfctl/cli.py` one after another, so a split would put pieces
in front of a reviewer without the store they depend on. Half the file count is
tests.

**PR closes**: `Closes #359`

Once this merges, #56 is likely done too. Flag it to Andre then, and don't
close it without his say.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #359 | T001–T053 | `[359] wfctl stores a branch's spec dir on its spec store's remote` | XL | the one PR above |

**Grouping pattern**: Single issue
**Rationale**: One PR closes exactly one issue, and #359 is the issue this
branch was cut for.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 → T003 | T001 confirms the merge decision. If it fails, stop and reopen `store-specs-merges-before-push.md`. T002 must exist before any store code can push |
| 1 | Mixed | T004 → T005 → T006; T007 → T008 ‖ T009; then T010 | T005 and T006 prove the guard refactor moved no behaviour. T010 is the merge gate |
| 2 | Mixed | T011 ‖ T012 ‖ T013 ‖ T029, then T014 → T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022 → T023 → T024 | The four test tasks are drafted together. The implementation runs in order, because `_spec_store.py`, `_pipeline.py` and `cli.py` are each edited by several tasks. T024 is the merge gate |
| 3 | Sequential | T030 → T031 → T032 | `check specs` edits `cli.py`, so it waits for T017 |
| 4 | Sequential | T026 → T025 → T027 → T028 | T026 checks whether #40's `hook worktree-remove` is on `origin/main`, and that decides where T025's tests land |
| 5 | Mixed | T033 ‖ T034 ‖ T035 ‖ T036 ‖ T037 ‖ T038, then T039 → T040 → T041 → T042 | Merge-failure tests are drafted together, and all of them extend `store` |
| 6 | Mixed | T043 ‖ T044, then T045 → T046 → T047 | The layouts with nowhere to push |
| 7 | Mixed | T048 ‖ T049 ‖ T050, then T051 → T052 → T053 | T053 is the real store of this branch's spec dir, and the host may refuse the push. That refusal is a `report-block`, not something to route around |

**Single-agent order** (recommended): the waves above in order, with each
`‖` group written one after the other.

---

## Agent Fanning Instructions

Single agent recommended. Every wave after Wave 0 edits `wfctl/_spec_store.py`
or `wfctl/cli.py`, so the parallel groups above would collide in the same
files. The one place fanning pays is drafting the test tasks inside a wave, and
even there most of them write into `tests/test_spec_store.py`. One agent
drafting them in sequence costs less than reconciling several.
