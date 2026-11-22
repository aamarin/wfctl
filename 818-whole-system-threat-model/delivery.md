# Delivery Plan: Whole-system threat model (818)

**Feature**: `818-whole-system-threat-model` | **Date**: 2026-11-22
**Source**: `tasks.md` in the feature's spec folder (45 tasks, T001 to T046 with T031 removed)
**Parent issue**: none

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (opened at the end of implement) | T001–T046 | `wfctl/agents/skills/threat-model/*` (created, vendored), `wfctl/agents/skills/_lib/checkpoint.py` (created, vendored), `wfctl/agents/skills/LICENSE-Apache-2.0` (created, vendored), `wfctl/agents/skills/NOTICES.md` (modified), `docs/architecture/vendor-upstream-skills.md` (modified), `wfctl/cli.py` (modified), `wfctl/_evidence.py` (modified), `wfctl/_pipeline.py` (modified), `wfctl/agents/skills/threat-baseline/SKILL.md` (created), `wfctl/agents/commands/threat-baseline.md` (created), `wfctl/agents/skills/design-levels/SKILL.md` (modified), `tests/test_skill_frontmatter.py`, `tests/test_skill_cross_references.py`, `tests/test_skill_attribution.py`, `tests/test_install_skills.py`, `tests/test_declared.py`, `tests/test_pipeline_needs_person.py`, `tests/test_threat_model_skills.py` (modified), `tests/test_claude_skill_paths.py`, `tests/test_pipeline_threat_baseline.py`, `tests/test_threat_baseline_skill.py` (created), `changes/818.addition.md` (created), `THREAT_MODEL.md` (created) | L | `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and `uv run wfctl verify` green; `uv run wfctl doctor` exits 0; both review groups have reviewed HEAD |

**Rationale**: Single PR. The pass's remedy names `/threat-baseline`, the skill depends on the vendored files and the mirror, and wfctl's own baseline needs all of it installed, so no subset merges as a working feature except the pass alone.

**Size flag**: By file count this is L (about 23 files). Most of the count is vendored upstream files, which the reviewer checks by the T005 diff rather than line by line, and test edits of a few lines each. The authored change is three modules, two skills, a wrapper, one paragraph in `design-levels`, and the tests. That's why this plan keeps one PR. The one credible split is the pass (Phase 3) as its own PR ahead of the rest, since it merges on its own and names a command that doesn't exist yet. We didn't choose it because a merged pass whose remedy names a missing skill sends every security branch to a dead command until the second PR lands.

**PR closes**: `Closes #818`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #818 (branch issue) | T001–T046 | `[818] Ship a skill that builds a whole-system threat model` | L | the branch's PR |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the whole feature, and the branch's own issue already exists, so no issue is created.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | Fetch upstream at `d3bea6b5`; everything in Phase 1 reads it |
| 1 | Parallel | T002 → T003 → T004 → T005 → T006 ‖ T018 → T019 → T020 | Vendoring and attribution run beside the pass's tests; different files |
| 2 | Parallel | T007 ‖ T008 ‖ T009 → T010 ‖ T021 → T022 → T023 → T024 → T025 | Vendored-file tests beside the pass implementation |
| 3 | Sequential | T011, T027 | Phase 1 and User Story 1 gates |
| 4 | Parallel | T012 ‖ T013 ‖ T014 ‖ T028 → T029 ‖ T036 | Install tests, skill text tests, and the `design-levels` test are all written first, in different files |
| 5 | Sequential | T015 → T016 → T030 → T032 → T033 → T037 | Mirror and ignore entries, then the skill, wrapper, grant check, and `design-levels` paragraph |
| 6 | Sequential | T017, T026, T034, T035, T038, T039 | Install, helper check, quickstart steps, design-time prompt, and phase gates |
| 7 | Sequential | T040 → T041 → T042 | `/threat-baseline` on wfctl from the installed tree, then confirm |
| 8 | Sequential | T043 → T044 → T045 → T046 | Release note, full suite, doctor, verify |

**Single-agent order** (recommended): T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022 → T023 → T024 → T025 → T026 → T027 → T028 → T029 → T030 → T032 → T033 → T034 → T035 → T036 → T037 → T038 → T039 → T040 → T041 → T042 → T043 → T044 → T045 → T046

T017's install tests need `threat-baseline/SKILL.md` to exist, so in the single-agent order a frontmatter-only stub goes in at T015 and T030 fills it.

---

## Agent Fanning Instructions

Single agent recommended. The parallel waves above save little time, because the slow steps (T034's install, T038's design-time prompt, and T040's bootstrap) are sequential. Two agents writing into `tests/` and `wfctl/` at once would also need a fan-in check after every wave. The wave table is kept for reference.
