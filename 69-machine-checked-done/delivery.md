# Delivery Plan: Machine-checked done (69)

**Feature**: `69-machine-checked-done` | **Date**: 2026-08-25
**Source**: `specs/69-machine-checked-done/tasks.md` (46 tasks)
**Parent issue**: #69

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| 1 | T001–T046 | `wfctl/_verify.py` (created), `wfctl.json` (created), `tests/test_verify.py` (created), `wfctl/_pipeline.py` (modified), `wfctl/cli.py` (modified), `wfctl/agents/skills/speckit-implement/SKILL.md` (modified), `README.md` (modified), `tests/test_pipeline_commands.py` (modified), `tests/test_install_skills.py` (modified), `tests/test_remaining_commands.py` (modified) | L | T046 green: `uv run --frozen --extra dev pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/ && wfctl doctor` |

**Rationale**: Single PR. Ten modified files puts this at L, where the skill
requires flagging rather than auto-splitting. The scope was presented with a
mechanism/adoption split as the recommended alternative and the single PR was
chosen deliberately.

The split line that was rejected is worth recording, because it is where this
would be cut if the PR proves unreviewable:

```
Phases 1–5  ─►  the mechanism      _verify.py  _pipeline.py  cli.py + 3 test files
                 inert until adopted                                   ~40 tasks

Phase 6     ─►  the adoption       SKILL.md  README.md  wfctl.json  cli.py
                 one-way door                                            6 tasks
```

**Reviewer note, from signal 4.** Phase 6 commits `wfctl.json` to this
repository, so wfctl's own `implement` step gates on its own build from that
commit onward. That is the intent of T045 and it is not undone by reverting the
PR alone — anyone already running the new build reads the committed config. Call
it out in the PR description rather than leaving a reviewer to find it in a
six-task phase at the end.

**PR closes**: `Closes #69`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #69 | T001–T046 | `Completion is self-certified: implement is done when the agent says a file exists` | L | PR #1 |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the whole feature, so one issue closes it. No new
issues are created; #69 already exists and the branch is named for it.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 | Baseline. T002 confirms the suite is green before anything changes. |
| 1 | Sequential | T003 → T004 → T005 → T006 → T007 → T008 → T009 | All in `_verify.py` and `test_verify.py`; each test follows the function it covers. Blocks both lanes below. |
| 2 | Parallel | **A**: T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019  ‖  **B**: T020 → T021 → T022 → T023 → T024 → T025 → T026 | Lane A owns `_verify.py` + `test_verify.py`; lane B owns `_pipeline.py` + `test_pipeline_commands.py`. B reads the record loader from Wave 1, not the runner from lane A, so the lanes are genuinely independent. |
| 3 | Sequential | T027 → T028 | Fan-in. T027's manual contract walk needs both lanes complete. T028 is the US1 merge gate. |
| 4 | Parallel | **A**: T032 → T033  ‖  **B**: T029 → T030 → T031 → T034 | Same two lanes, US2. Lane B extends the arm lane A's `inconclusive` flag feeds. |
| 5 | Sequential | T035 | US2 merge gate. |
| 6 | Parallel | T036 ‖ T037 ‖ T038 ‖ T039 | US3. Four different files, no shared state — the only wave where every task is independent. |
| 7 | Sequential | T040 | US3 merge gate. |
| 8 | Parallel | (T041 → T042) ‖ T043 ‖ T044 | Phase 6. T041/T042 share `SKILL.md` and are ordered; README and `doctor` are independent. |
| 9 | Sequential | T045 → T046 | T045 adopts the feature here and needs everything above. T046 is the final gate. |

**Single-agent order** (recommended — see fanning note below):
T001 → T002 → … → T046, in numeric order. The numbering is already execution
order, so a single agent needs no wave table.

---

## Agent Fanning Instructions

**Recommended: single agent.** The wave table is real — waves 2, 4, 6 and 8
carry genuine parallelism — but fanning is not recommended here, for one reason
the wave table cannot show:

```
lane A  _verify.py          writes the record
lane B  _pipeline.py        reads the record

        both against contracts/verify-record.md, which no test enforces
        until T021 (lane B) and T019 (lane A) have both landed
```

The lanes share a data contract, not a file. Two agents drafting against it
concurrently will agree on the field names and disagree on the edge cases —
whether `failed` is absent or `[]` on success, whether `inconclusive` is written
when false. That is the "Coordinate" row of the parallelization table: draft
together, type-check together. The coordination cost exceeds the wall-clock
saving on a 46-task feature that is mostly small edits.

**If fanning anyway**, fan only Wave 6 (T036 ‖ T037 ‖ T038 ‖ T039). Those four
tasks touch four different files, share no contract, and each has its own
verification command.

**Fan-in gate after any wave**: `uv run --frozen --extra dev pytest -q`
