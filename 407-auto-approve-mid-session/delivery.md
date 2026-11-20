# Delivery Plan: Auto-approve has its own command (407)

**Feature**: `407-auto-approve-mid-session` | **Date**: 2026-11-19
**Source**: `tasks.md` in the feature's spec folder (37 tasks)
**Parent issue**: #147

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| (opened at review) | T001 - T037 | `wfctl/cli.py` (modified), `wfctl/evidence/_mode.py` (modified), `wfctl/evidence/__init__.py` (modified), `wfctl/install/_settings.py` (modified), `wfctl/install/_workmux.py` (modified), `wfctl/install/__init__.py` (modified), `wfctl/agents/configs/workmux/.workmux.yaml` (modified), `.workmux.yaml` (modified), `wfctl/agents/skills/using-wfctl/SKILL.md` (modified), `wfctl/agents/skills/plan-walkthrough/SKILL.md` (modified), `docs/reference.md` (modified), `changes/407.addition.md` (created), plus tests: `tests/test_auto_approve_command.py` and `tests/test_skills_reference_auto_approve.py` (created), `tests/test_auto_approve_mode.py`, `tests/test_settings_merge.py`, `tests/test_install_hook_merge.py`, and `tests/test_workmux.py` (modified) | L | CI green, review groups cleared, `auto-approve-grant-asks-first` accepted by the user, and the two manual checks (T025, T034) recorded |

**Rationale**: Single PR. Every story goes through the one `auto-approve`
command in `wfctl/cli.py`, and the Claude Code ask rules (Phase 4) have to ship
with the command. Without them, the command would land without the prompt that
the proposed record `auto-approve-grant-asks-first` describes.

The file count puts this at L, which the sizing table flags for discussion. It
stays one PR for three reasons:

1. Twelve source files sounds large, but half of them change by a line or a
   paragraph: the two YAML files, the two skills, `docs/reference.md`, the two
   `__init__.py` exports, and the release note.
2. The only real split candidate is Phase 4, the ask rules. Merging the command
   first would ship an agent-run grant with no prompt in front of it, which
   reverses the order the record sets.
3. A reviewer judges the grant, its refusals, and its prompt together, since
   they answer one threat model.

**PR closes**: `Closes #407`

#407 isn't the last child of #147, so the PR doesn't close the parent.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #407 | T001 - T037 | `/start-session cannot pass --auto-approve, so granting a feature autonomy happens outside the workflow` | L | the #407 PR |

**Grouping pattern**: Single issue
**Rationale**: One PR closes exactly one issue, and #407 already exists, so
there's nothing to create.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | No dependencies |
| 1 | Parallel | T002 ‖ T003 | Tests in one file; write together |
| 2 | Sequential | T004 → T005 → T006 → T007 → T008 → T009 | T004 calls `newest_is_grant` from T005; gate: T009 |
| 3 | Parallel | T010 ‖ T011 | Tests in one file |
| 4 | Sequential | T012 → T013 | Gate: T013 |
| 5 | Parallel | (T014 ‖ T015 → T016 → T017 → T018 → T019) ‖ (T022 → T023 → T024) ‖ (T029 → T030 ‖ T031 → T032) | Different files, except T017, T018, and later T021 all edit `wfctl/cli.py`, so run the `cli.py` tasks one at a time |
| 6 | Sequential | T020 → T021 | Needs T012; edits `wfctl/cli.py` |
| 7 | Sequential | T026 → T027 → T028 | Needs T021 for the bare form and T023 for the shipped line |
| 8 | Parallel | T033 ‖ T025 (user) ‖ T034 (user) | T034 needs Phase 4 installed |
| 9 | Sequential | T035 → T036 → T037 | Final sweep |

**Single-agent order** (recommended):
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 →
T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022 →
T023 → T024 → T026 → T027 → T028 → T029 → T030 → T031 → T032 → T033 → T025 →
T034 → T035 → T036 → T037

---

## Agent Fanning Instructions

Single agent recommended. Phases 3 to 7 all edit `wfctl/cli.py`, so parallel
agents would collide on that file, and the remaining parallel work is small:
two skill edits, two YAML lines, and a docs pass. T025 and T034 need the user
at the keyboard, so hand them over as soon as Phases 6 and 4 are done.

**Fan-in gate before review:** `uv run pytest -q`, `uv run ruff check wfctl/
tests/`, `uv run mypy`, and `uv run wfctl verify`
