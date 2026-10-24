# Delivery Plan: Every change runs the design passes and records whether it needs a spec (628)

**Feature**: `628-design-passes-every-change` | **Date**: 2026-10-23
**Source**: `tasks.md` in this spec dir (39 tasks)
**Parent issue**: #628

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| One PR from `628-design-passes-every-change` | T001 - T039 | `wfctl/agents/skills/design-passes/SKILL.md` (created), `wfctl/_sections.py` (created), `tests/test_sections.py` (created), `changes/628.addition.md` (created), `wfctl/cli.py` (modified), `wfctl.json` (modified), `.github/pull_request_template.md` (modified), `AGENTS.md` (modified), `tests/test_skill_cross_references.py` (modified), `tests/test_pipeline_commands.py` (modified), `tests/test_shape.py` (modified), `tests/test_cli_status.py` (modified), and six skills under `wfctl/agents/skills/` (modified): `worktree-handoff`, `design-levels`, `architecture-design`, `model-the-domain`, `architecture-decisions`, `fanning-out-code-review` | L (19 files) | `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, and `uv run wfctl check config` all exit 0. The release note is committed. The PR body answers "Needs a spec?" with a reason, since T028 makes this repo require it. |

**Rationale**: Single PR. Andre chose one PR over splitting the check (US2) from the skills (US1 and US3). The two halves share only `AGENTS.md` and either could merge alone, but the feature needs both, and most of the 19 files are one-paragraph skill edits. The reviewer should expect two independent parts in one diff: the new check in `wfctl/_sections.py` and `wfctl/cli.py`, and the new skill with the pointers to it.

**PR closes**: `Closes #628`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #628 | T001 - T039 | `[628] Every change runs the design passes and records whether it needs a spec` | L | The PR from this branch, not yet opened |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the whole feature, so #628 is the only issue, and this run creates none.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 | All three commands exit 0, and five `check-body` outputs are saved before any US2 code exists. |
| 1 | Parallel | T017 → T018 → T019 ‖ T020 ‖ T021 ‖ T003 → T004 | Every new test fails on the current tree. |
| 2 | Parallel | T022 → T023 → T024 → T025 → T026 ‖ T005 → T006 ‖ T029 | T006 commits T003 - T005 alone, so the branch shows the failing tests first. |
| 3 | Parallel | T027 → T028 ‖ T007 ‖ T008 ‖ T009 ‖ T010 ‖ T011 | T008 - T011 each edit a different skill. |
| 4 | Sequential | T012 → T013 → T014 → T030 → T031 | T013 is the first `AGENTS.md` edit. T031 runs in a fresh-context subagent. |
| 5 | Sequential | T015 → T032 | Both need a throwaway worktree, which the worktree guard refuses, so ask Andre first. |
| 6 | Sequential | T016 → T033 → T034 → T035 | T034 edits `design-levels` after T008, and copies the wording T005 wrote. |
| 7 | Sequential | T036 → T037 → T038 → T039 | T036 is the second `AGENTS.md` edit. T039 is the merge gate. |

**Single-agent order** (recommended, with US2 first as tasks.md suggests):
T001 → T002 → T017 → T018 → T019 → T020 → T021 → T022 → T023 → T024 → T025 → T026 → T027 → T028 → T029 → T030 → T031 → T032 → T033 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T034 → T035 → T036 → T037 → T038 → T039

---

## Agent Fanning Instructions

A single agent is recommended. The two stories touch different code, but every task is short, and the waves above are mostly serial chains inside one story. Fanning out saves little and adds a merge of two edit streams on one branch.

If you do fan out, split by story after Wave 0, and keep `AGENTS.md` with the US1 agent until T013 is committed.

**Agent A prompt (US2, the check):**
```
Work in the 628-design-passes-every-change worktree. Run T017 - T033 from tasks.md
in that order (`wfctl feature-paths` prints the spec dir). Write each test first and
confirm it fails before the code it covers. Edit only wfctl/_sections.py, wfctl/cli.py,
wfctl.json, .github/pull_request_template.md, fanning-out-code-review under
wfctl/agents/skills/, and the three test files the tasks name. Load the writing-style
skill before any prose. Stop before T032 and ask Andre for the throwaway worktree.
```

**Agent B prompt (US1 and US3, the skills):**
```
Work in the 628-design-passes-every-change worktree. Run T003 - T016, then T034 and
T035, from tasks.md in that order (`wfctl feature-paths` prints the spec dir). Edit
only under wfctl/agents/skills/, AGENTS.md, tests/test_skill_cross_references.py, and
tests/test_pipeline_commands.py. Never edit .agents/ or .claude/. Load the
writing-style skill before any prose. Stop before T015 and ask Andre for the
throwaway worktree.
```

**Fan-in gate after both agents:** T036 - T039, ending with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/ && uv run wfctl check config`
