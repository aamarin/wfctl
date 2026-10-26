# Delivery Plan: Design exceptions live with specs (635)

**Feature**: `635-arch-folder-per-branch-notes` | **Date**: 2026-10-26
**Source**: `specs/635-arch-folder-per-branch-notes/tasks.md` (64 tasks)
**Parent issue**: #635

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (opened at the end) | T001 - T064 | `wfctl/_design_exceptions.py` (created), `wfctl/_record_gate.py` (created), `wfctl/cli.py`, `wfctl/_evidence.py`, `wfctl/_pipeline.py`, `wfctl/_paths.py`, `wfctl/_review_gate.py`, `wfctl/_arch.py`, `wfctl/_contract.py`, `wfctl/_declared.py` (modified); 6 skills under `wfctl/agents/skills/`; about 15 test files; `AGENTS.md`, `wfctl.json`, `.github/pull_request_template.md`; 3 records under `docs/architecture/`; `docs/architecture/declarations/` and `docs/architecture/step-claims/` (removed); `changes/635.change.md` | XL, about 40 files | CI green, the review groups run, and the user accepts `design-exceptions-live-with-specs.md` and `an-absent-artifact-is-claimed-not-inferred.md` |

**Rationale**: Single PR. The user chose one PR on 2026-10-26, although the file count is past the size where the decompose skill suggests discussing a split. About half the files are tests and skill text. The stories don't make safe increments either. If the move landed before the checks in US5, a branch could say "no new boundary" while adding a record, and nothing would stop it until a second PR merged. The migration in US4 needs the new locations from US1 and US2, so it can't stand alone.

**PR closes**: `Closes #635`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #635 | T001 - T064 | `[635] Design exceptions live with specs` | XL | the single PR |

**Grouping pattern**: Single issue
**Rationale**: One PR closes exactly one issue, and #635 already exists, so this plan creates no issues.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | No dependencies |
| 1 | Sequential | T002 → T003 → T004 → T005 | T005 is the merge gate. Every story needs the module and `feature_dir` |
| 2 | Sequential, one parallel task | T006 → T010, with T011 ‖, then T012 → T016 | T016 is the merge gate |
| 3 | Parallel, then sequential | T020 ‖ T021 ‖ T022, then T017 → T019, T023 → T026, T028 ‖, then T027 → T030 | T027 goes last, since it removes `STEP_CLAIMS_DIR` and four places still import it. T030 is the merge gate |
| 4 | Sequential | T031 → T041 | Needs waves 2 and 3. T041 is the merge gate |
| 5 | Sequential | T042 → T047 | Needs wave 1 only, but T045 edits the same skill file as T040, so it runs after wave 4 |
| 6 | Sequential, one parallel task | T048, T049 ‖, T050 → T054 | Needs waves 2 and 3. T053 asks the user before the first push. T054 is the merge gate |
| 7 | Parallel, then sequential | T055 ‖ T056, then T057 → T063 | T063 is the merge gate |
| 8 | Sequential | T064 | After the PR opens, and after asking the user |

**Single-agent order** (recommended): T001 → T064 in task order. The parallel tasks are small edits to separate files, so fanning them out saves little.

---

## Agent Fanning Instructions

A single agent is recommended. Most waves are one story's test-then-code sequence, and the parallel tasks in waves 3, 6, and 7 are small edits to different files, so a second agent costs more than it saves.
