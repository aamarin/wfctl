# Delivery Plan: Session start loads only the branch's own context (432)

**Feature**: `432-start-session-loads-issue-context` | **Date**: 2026-11-02
**Source**: `tasks.md` in this folder (43 tasks)
**Parent issue**: #619

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (to open) | T001–T043 | `wfctl/_session_report.py` (created), `wfctl/cli.py` (modified), `wfctl/_session.py` (modified), `wfctl/_tracker.py` (modified), `wfctl/agents/trackers/github.json` (modified), `wfctl/agents/trackers/github-issue-parent.sh` (created), `wfctl/agents/trackers/github-change-branch.sh` (created), `wfctl/agents/skills/scaffold-tracker/SKILL.md` (modified), `wfctl/agents/skills/start-session/SKILL.md` (modified), `wfctl/agents/skills/start-session/references/doctor-repair.md` (created), `changes/432.change.md` (created), and 9 test files under `tests/` | L | T042's definition of done is green, the review groups have reviewed HEAD, and the user has made the two #432 issue-body edits from T040 |

**Rationale**: Single PR, which the user chose on 2026-11-02 over splitting the wfctl commands from the skill rewrite. The skill rewrite is the only caller of the new commands, and the token measurement the PR reports (SC-001, SC-002) needs both halves in place. We didn't choose the split because it adds a second issue and ships a PR whose commands nothing calls yet.

**PR closes**: `Closes #432`

#432 is one child of #619, so the PR doesn't close the parent.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #432 | T001–T043 | `[432] Session start loads only the branch's own context` | L | the one PR above |

**Grouping pattern**: Single issue
**Rationale**: The branch's own issue already exists and covers the whole feature, so this step creates no issue.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Parallel | T001 ‖ T002 ‖ T003 → T004 | Spec document fixes, no code |
| 1 | Parallel | T005→T006 ‖ T007→T008 ‖ T009→T010 ‖ T011→T012 ‖ T013 ‖ T014, then T015 → T016 | T015 needs T010, T013, and T014. Beside this wave, T028 → T029 → T030 (US4) |
| 2 | Sequential | T017 → T018 → T019 → T020 → T021 | US1, the MVP. Needs Wave 1 |
| 3 | Sequential | T022 → T023 → T024, then T025 → T026 → T027 | US2 and US5 both edit `_session_report.py`, so they run one after the other |
| 4 | Mixed | T031 → T032, then T033 ‖ T034, then T035 → T036 → T037 | US3. Needs Waves 2 and 3 and US4 |
| 5 | Mixed | T038, T039 ‖ T040, T041, then T042 → T043 | Polish and the definition of done |

**Single-agent order** (recommended):
T001 → T004, T005 → T016, T028 → T030, T017 → T027, T031 → T043

---

## Agent Fanning Instructions

A single agent is recommended. Most waves edit the same few files, `wfctl/_session_report.py`, `wfctl/_tracker.py`, and `wfctl/cli.py`, so parallel agents would conflict more than they would save. Wave 1's two GitHub scripts (T013, T014) and US4 (T028 to T030) are the only parts that touch separate files, and they're small enough to run inline.

**Fan-in gate after Wave 1:** `uv run pytest -q tests/test_tracker.py tests/test_session_stopped_not_finished.py tests/test_session_report.py`
