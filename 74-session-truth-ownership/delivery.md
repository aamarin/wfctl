# Delivery Plan: session truth ownership (74)

**Feature**: `74-session-truth-ownership` | **Date**: 2026-08-30
**Source**: `74-session-truth-ownership/tasks.md` (34 tasks)
**Parent issue**: #74

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| PR 1 | T001-T020 (incl. T009a, T009b, T017a), T026-T028 | `wfctl/_pipeline.py` (modified), `wfctl/cli.py` (modified), `wfctl/_session.py` (modified), `wfctl/agents/skills/start-session/SKILL.md` (modified), `tests/conftest.py` (modified), `tests/test_pipeline_state_names.py` (created), `tests/test_pipeline_commands.py` (modified), `tests/test_agent_session.py` (modified), `tests/test_session_existence.py` (created), `tests/test_session_migration.py` (created) | L | T020 and T028 green: `pytest`, `ruff`, `mypy`, plus the manual `/start-session` check in T019 |
| PR 2 | T021-T025, T030-T032 | `wfctl/_session.py` (modified), `wfctl/cli.py` (modified), `wfctl/agents/skills/end-session/SKILL.md` (modified), `wfctl/agents/skills/using-wfctl/SKILL.md` (modified), `tests/test_end_reports_observations.py` (created) | M | T025 and T032 green, plus `wfctl doctor` clean |

**Rationale**: Two PRs. The four boundary signals split cleanly — #42 and #70
have separate acceptance criteria and separate runtime paths, and US1 alone
leaves the tool working, which is the stated MVP. They share `_session.py` and
`cli.py`, but sequentially rather than concurrently, so PR 2 stacks on PR 1
rather than racing it.

The alternative considered was a third PR carrying Foundational and US3 — the
state-name change — against a new issue. Rejected: it has no user-facing
behavior on its own and PR 1 needs it first, so it would exist only to be a
prerequisite. It rides in PR 1, where the tasks that depend on it are.

**PR 1 closes**: `Closes #42`
**PR 2 closes**: `Closes #70`

PR 2 is the final PR for the epic. If #74's acceptance is satisfied when it
merges, add the parent close separately: `Closes #74`.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #42 | T001-T020, T009a, T009b, T017a, T026-T028 | `[74] current.md is written once and never updated` | L | PR 1 |
| #70 | T021-T025, T030-T032 | `[74] wfctl end reports a completion it cannot observe` | M | PR 2 |

**Grouping pattern**: Sub-feature split under parent epic #74.
**Rationale**: Both sub-issues already exist and predate this plan; the tasks map
onto them one-to-one, so no issue was created. One PR closes exactly one issue.

### Getting this spec into a sub-issue worktree

This repo records a spec root outside the working tree
(`/Users/andremarin/Development/wfctl-specs`), so the epic's spec dir is already
at a stable absolute path every worktree can read. Nothing to copy.

`speckit-orchestrate` step 0 resolves it: it globs the spec root for
`*/delivery.md`, matches the sub-issue branch's key against the Issue column
above, and takes that row's Tasks column as the range.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 | The fixture everything else builds on; no edits to `wfctl/` |
| 1 | Sequential | T003 → T004 → T005 | One file, one rename, its test. Nothing parallelizes inside a single-file refactor |
| 2 | Parallel | T006 ‖ T008 | `cli.py` and `_session.py`, different files, no shared state |
| 3 | Parallel | T007 ‖ T009 ‖ T009a → T009b | Three test files; T009b reads T009a's structure so it follows it |
| 4 | Sequential | T010 | Fan-in: `pytest` + `mypy` — merge gate |
| 5 | Sequential | T011 → T012 → T013 → T014 | All `_session.py` and `cli.py`; T014 asserts the result of all three |
| 6 | Parallel | T015 ‖ T016 | `cli.py` and `_pipeline.py`; the [P] pair from tasks.md |
| 7 | Parallel | T017 ‖ T017a ‖ T018 | Three separate test files; T018 carries its own |
| 8 | Sequential | T019 → T020 | Skill edit then the manual check; T020 is the merge gate for PR 1 |
| 9 | Parallel | T026 ‖ T027 → T028 | US3's guard tests, one file, then its gate |
| 10 | Sequential | T021 → T022 → T023 → T024 → T025 | PR 2. Shares `_session.py` with PR 1, so it starts after PR 1 merges |
| 11 | Parallel | T030 ‖ T031 → T032 | Polish; T032 is the final gate including `wfctl doctor` |

**Single-agent order** (recommended): T001 → T002 → T003 → T004 → T005 → T006 →
T008 → T009 → T009a → T009b → T007 → T010 → T011 → T012 → T013 → T014 → T015 →
T016 → T017 → T017a → T018 → T019 → T020 → T026 → T027 → T028 → *(PR 1 merges)*
→ T021 → T022 → T023 → T024 → T025 → T030 → T031 → T032

---

## Agent Fanning Instructions

Single agent recommended. The parallel waves above are real but narrow — two or
three files each — and the coordination cost of fanning exceeds the saving on a
feature this size. The wave table stands as the dependency record: what it
actually pins down is that Wave 4 and Wave 8 are fan-in gates, and that Wave 10
cannot start until PR 1 has merged, because both waves edit `_session.py`.

**Fan-in gate after Wave 4**: `uv run --frozen pytest -q && uv run --extra dev mypy wfctl/`
**Fan-in gate after Wave 8**: `uv run --frozen pytest -q && uv run --frozen ruff check wfctl/ tests/`
