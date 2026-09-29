# Delivery Plan: plan-walkthrough (500)

**Feature**: `500-plan-defense` | **Date**: 2026-09-28
**Source**: `/Users/andremarin/Development/wfctl-specs/500-plan-defense/tasks.md` (37 tasks)
**Parent issue**: #500

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (opened after implementation) | T001 - T037 | `wfctl/_pipeline.py` (modified), `wfctl/_declared.py` (modified), `wfctl/contracts/status-payload.json` (modified), `wfctl/agents/skills/plan-walkthrough/` (created: `SKILL.md` and five references), `wfctl/agents/commands/plan-walkthrough.md` (created), `docs/reference.md` (modified), `docs/architecture/vendor-upstream-skills.md` (modified), `wfctl.json` (modified), `tests/test_declared.py`, `tests/test_cli_status.py` (modified), `tests/test_pipeline_needs_person.py`, `tests/test_plan_walkthrough_skill.py` (created) | L | the definition of done green (T036), every `quickstart.md` section run (T037), and the review panel run before opening |

**Rationale**: Single PR, chosen by Andre over a two-PR split (2026-09-28). The
two halves, the `needs_person` skip and the walkthrough skill, share no file,
but this repository's own declaration (T030) uses both, and one PR keeps them
from landing out of order.

**PR closes**: `Closes #500`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #500 | T001 - T037 | `plan-defense: an adversarial ownership pass after plan and after implement` (the feature is now the plan walkthrough) | 1 - 2 days | the single PR above |

**Grouping pattern**: Single issue
**Rationale**: One PR closes exactly one issue, and #500 already exists, so no
issue is created.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | the suite, ruff, and mypy green on the branch head |
| 1 | Sequential | T002 → T003 → T004 → T005 | Phase 2 gate: `needs_person` reaches `SubStep`, no reading changes |
| 2 | Parallel | T006 - T015 (the skill) ‖ T016 - T023 (the skip) | no shared file; each ends on its own merge gate (T015, T023) |
| 3 | Sequential | T024 → T025 | needs both halves of Wave 2 |
| 4 | Parallel | T026 ‖ T027, then T028 → T029 → T030 → T031 | T030 needs the command installed in T014 |
| 5 | Sequential | T032 → T033 | change mode's manual run needs the declaration from T030 |
| 6 | Parallel, then sequential | T034 ‖ T035, then T036 → T037 | final definition of done and the full quickstart run |

**Single-agent order**: T001 → T005, then T016 → T023 (the skip, which touches
code a reviewer checks most closely), then T006 → T015, then T024 → T037.

---

## Agent Fanning Instructions

Wave 2 can be split across two agents, since the skill and the skip share no
file. One agent is recommended anyway: the skill's refusal text (T010) and the
skip's reason string (T020) must match the contracts word for word, and one
agent holding both is the cheaper way to keep them agreeing.

**Fan-in gate after Wave 2:** `uv run pytest -q && uv run mypy wfctl/`
