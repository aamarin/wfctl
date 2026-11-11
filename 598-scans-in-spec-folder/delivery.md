# Delivery Plan: Scan files in the spec folder

## PR Boundary

One PR. The step readers, the sign-off, and the skill text change together:
readers that require a spec-folder scan, shipped before the wrappers write one,
would hold every feature's clarify step. The change is about 6 code files, 4
skill files, AGENTS.md, and their tests, which is an M.

## File-touch matrix

| Task | Files |
|---|---|
| T001 | MODIFY `wfctl/_paths.py` |
| T002 | MODIFY `tests/conftest.py` |
| T003, T004 | MODIFY `wfctl/_evidence.py` |
| T005 | MODIFY tests that stage clarify, analyze, or plan review by hand |
| T006, T007 | CREATE `tests/test_scan_reader.py` |
| T008 | MODIFY `wfctl/_plan_review.py` |
| T009 | MODIFY `wfctl/cli.py` |
| T010 | MODIFY `tests/test_plan_review_signoff.py` |
| T011 | MODIFY `wfctl/agents/skills/writing-a-scan-file/SKILL.md` |
| T012 | MODIFY `wfctl/agents/commands/speckit.clarify.md`, `speckit.analyze.md` |
| T013 | MODIFY `wfctl/agents/commands/plan-review.md` |
| T014 | MODIFY `wfctl/agents/skills/opening-a-change/SKILL.md` |
| T015 | MODIFY `tests/test_scan_files.py`, `tests/test_plan_review_skill.py` |
| T016 | MODIFY `AGENTS.md` |
| T017 | CREATE `changes/598.change.md` |
| T018, T019 | READ ONLY |

## Issue Grouping Map

| Issue | Tasks | PR |
|---|---|---|
| #598 Store scan files in the spec folder, not the code repository | T001 - T019 | 1 |

## Parallelization

| Wave | Tasks |
|---|---|
| 1 | T001, T002 |
| 2 | T003 - T007, T008 - T010 |
| 3 | T011 - T017 |
| 4 | T018, T019 |
