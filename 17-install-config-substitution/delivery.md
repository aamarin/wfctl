# Delivery Plan: install-config substitution (17)

**Feature**: `17-install-config-substitution` | **Date**: 2026-08-03
**Source**: `specs/17-install-config-substitution/tasks.md` (30 tasks)
**Parent issue**: #17

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| PR 1 | T001–T029 (all 30, incl. T015a) | `wfctl/_workmux.py` (created), `tests/test_workmux.py` (created), `wfctl/cli.py` (modified), `wfctl/_paths.py` (modified), `tests/test_paths.py` (modified), `tests/test_remaining_commands.py` (modified), `tests/test_install_config.py` (modified) | M (7 files) | T029 green — `uv run pytest -q && uv run ruff check . && uv run mypy` |

**Rationale**: Single PR. Seven files is M, which the sizing table maps to one PR.
US2 and US3 are independent stories, but both edit `wfctl/_workmux.py` **and**
`wfctl/cli.py` — splitting them guarantees a rebase on two files and would leave a
reviewer assessing a module holding two of its four functions. The four boundary
signals split 2-2 (conflict risk and reviewability say bundle; mergeable increment
and story independence say a split is possible), and the framework's default on a
tie is to bundle.

Considered and rejected: shipping US2 first as the MVP, since it is what protects
`pfms`. That would land the retrofit perhaps two hours earlier on a 3-4 hour
feature — not worth a second PR and a guaranteed conflict.

**PR closes**: `Closes #17`

User Story 1 produces no PR in this repository. Its implementation is
`aamarin/wf-skills#8`; tasks T006–T008 verify it once that lands.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #17 | T001–T029 | `[17] install-config: substitute the <project> placeholder, and surface unwired repos in doctor` | 3-4 h | PR 1 |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the full in-repo feature, and #17 was narrowed on
2026-08-03 to describe exactly this scope — the template edit moved to
wf-skills#8, leaving #17 owning the prefix substitution, the `project_name`
promotion, and the doctor lint. No new issues created; issue count equals PR
count.

**External dependency**: `aamarin/wf-skills#8` — the template edit behind US1. No
file in this repository changes for it, and this PR does not close it.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 | Creates `_workmux.py` and `tests/test_workmux.py`. Both later waves add to these files, so this must land alone first to avoid a create/create race. |
| 1 | Parallel | (T003 → T004) ‖ (T009 ‖ T010) ‖ (T018 ‖ T019) | Three independent tracks: `_paths.py`+`test_paths.py`; `pre_remove_wired`; `tmux_safe`. T009/T018 both append to `_workmux.py` — different functions, but coordinate or sequence the write. |
| 2 | Sequential | T005 · T011 → T012 · T020 → T021 | Each depends on its Wave 1 sibling in the same file: `wire_pre_remove` after `pre_remove_wired`, `patch_seed` after `tmux_safe`. |
| 3 | Parallel | (T013 → T014) ‖ (T022 → T023) | The two `cli.py` call sites. Independent commands (`doctor_cmd` vs `install_config_cmd`) but the **same file** — sequence the writes or expect a merge. |
| 4 | Parallel | (T015 ‖ T015a) ‖ T024 | Integration tests in two different files; genuinely parallel. |
| 5 | Sequential | T017 · T026 | Phase merge gates for US2 and US3. |
| 6 | Sequential | T006 → T007 → T008 · T016 · T025 | Manual verification. T006–T008 blocked on wf-skills#8; T016 touches `~/Development/pfms`, T025 needs a scratch worktree. |
| 7 | Parallel | T027 ‖ T028, then T029 | Polish greps are independent; T029 is the final fan-in gate. |

**Single-agent order** (recommended — see below):
T001 → T002 → T003 → T004 → T005 → T009 → T010 → T011 → T012 → T013 → T014 →
T015 → T015a → T016 → T017 → T018 → T019 → T020 → T021 → T022 → T023 → T024 →
T025 → T026 → T006 → T007 → T008 → T027 → T028 → T029

---

## Agent Fanning Instructions

**Single agent recommended**, despite this being an M feature.

The wave table shows real parallelism, but it is not worth fanning here. Every
implementation task lands in one of just two source files — `_workmux.py` (5
tasks) and `cli.py` (4 tasks) — so two agents working "in parallel" would spend
their time coordinating writes to the same files rather than working
independently. The feature is 3-4 hours total; coordination overhead would exceed
the saving.

The wave table is retained for ordering and for template reuse.

**If fanning anyway**, the only genuinely conflict-free split is Wave 4:

**Agent A prompt:**
```
In specs/17-install-config-substitution/, implement T015 and T015a from tasks.md.
Add integration tests to tests/test_remaining_commands.py only. Do not modify any
other file. Contracts for the exact output strings are in contracts/cli.md §2.
Verify with: uv run pytest -q tests/test_remaining_commands.py -k doctor
```

**Agent B prompt:**
```
In specs/17-install-config-substitution/, implement T024 from tasks.md.
Add integration tests to tests/test_install_config.py only. Do not modify any
other file. Contracts for the exact output strings are in contracts/cli.md §1.
Verify with: uv run pytest -q tests/test_install_config.py
```

**Fan-in gate after Wave 4:** `uv run pytest -q && uv run ruff check . && uv run mypy`

---

## Notes

- **Build order is bottom-up**: pure transforms first (no dependencies), then the
  `project_name` promotion, then the two `cli.py` call sites, then integration.
  `quickstart.md` carries the same order with the runnable checks.
- **T015a exists because `/speckit.analyze` found five requirements asserted by no
  test** — four of them negative or output-content requirements, which regress
  without failing anything. FR-013b had zero tasks before remediation. See
  `checklists/analysis-report.md`.
- **US1's verification is manual only.** Its implementation is external, so no
  automated test in this repo can cover it. T006 gates on wf-skills#8 having
  landed.
