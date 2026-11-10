# Delivery Plan: architecture views (739)

**Feature**: `739-architecture-views` | **Date**: 2026-11-10
**Source**: `739-architecture-views/tasks.md` (49 tasks)
**Parent issue**: none

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| #739 branch | T002 - T025, T041 - T049 | `changes/739.change.md` (created), `wfctl/_paths.py` (modified), `wfctl/arch/_contexts.py` (modified), `wfctl/arch/_views.py` (created), `wfctl/arch/_records.py` (modified, bracket-list helper only), `wfctl/arch/__init__.py` (modified), `wfctl/cli.py` (modified, `arch_context_cmd`), three templates under `wfctl/agents/skills/architecture-design/views/` (created), `architecture-design/SKILL.md` (modified), `start-session/SKILL.md` (modified), `model-the-domain/domain-model-template.md` (modified), `docs/architecture/views/system-context.md` and `container.md` (created), `docs/architecture/required-views-are-wfctls.md` (created), `tests/test_paths.py`, `tests/test_arch_views.py`, `tests/test_record_placement.py` | L | `wfctl verify` green, and `required-views-are-wfctls` accepted by the user |
| #738 branch | T001, T026 - T040 | `changes/738.addition.md` (created), `wfctl/arch/_records.py` (modified), `wfctl/cli.py` (modified, `arch_accept_cmd`), `architecture-decisions/record-template.md` (modified), `architecture-decisions/SKILL.md` (modified), `docs/reference.md` (modified, `diagram` field only), `docs/architecture/the-author-declares-the-diagram-kind.md` (modified), `tests/fixtures/one-kind-records/` (created), `tests/test_arch_diagram_kinds.py` (created), `tests/test_arch_sections.py` (modified) | M | `wfctl verify` green, and `the-author-declares-the-diagram-kind` accepted by the user |

**Rationale**: Two PRs. The spec covers two open issues, and a PR closes only one, so a single PR would leave #738 open with nothing to close it. The two stories share no state, and their only shared files are `wfctl/arch/_records.py` and `wfctl/cli.py`, where each PR changes a different function.

The #739 PR is L at about 19 files, and the user approved keeping it as one PR. A reviewer needs the views list, the session-start `Views` block, and wfctl's own two views together to judge whether the templates work. The domain template cleanup (User Story 4) touches two files and rides along, since it has no issue of its own.

**PR closes**: the #739 PR carries `Closes #739`, and the #738 PR carries `Closes #738`.

### Moving the #738 work off this branch

This branch already edited `docs/architecture/the-author-declares-the-diagram-kind.md` in commits 913b077 and a9f2c16, which also edited `required-views-are-wfctls.md`. That edit is the #738 decision, so it moves:

1. The #738 worktree applies this branch's diff of that one file as its first commit: `git diff main...739-architecture-views -- docs/architecture/the-author-declares-the-diagram-kind.md`.
2. This branch then restores the file to `main`'s copy with `git checkout main -- docs/architecture/the-author-declares-the-diagram-kind.md` and commits that.

The scan files under `docs/architecture/scans/` stay on this branch, since they record reviews of the shared spec.

### Order between the two PRs

Either PR can merge first. The bracket-list helper in `wfctl/arch/_records.py` is added by whichever PR lands first (T010 or T032), and the second PR rebases onto it rather than adding a second copy.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #739 (Issue A) | T002 - T025, T041 - T049 | `wfctl has a standard set of architecture views` | L | the #739 PR |
| #738 (Issue B) | T001, T026 - T040 | `A record can declare more than one diagram kind` | M | the #738 PR |

**Grouping pattern**: Sub-feature split, with no parent epic.
**Rationale**: Both issues were already open, so no issue is created. Each one gets one PR.

### Getting this spec into a sub-issue worktree

This repo records a spec root outside the working tree, so the spec folder is already at a fixed path every worktree can read, and nothing needs copying. In the #738 worktree, `wfctl feature-paths` finds this `delivery.md` because the map above names #738, and takes T001 and T026 - T040 as that branch's tasks.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Parallel | T001 (#738) ‖ T002 (#739) | Release notes, no dependencies |
| 1 | Sequential | T003 → T004 → T005 | #739 only. Keeps `views/` out of record readers before any view exists |
| 1 | Sequential | T026 | #738 only. Pins today's acceptance results before `_records.py` changes, and runs beside the #739 Wave 1 |
| 2 | Mixed | T006 → T007 → T008, then T009 → T010, with T011 ‖ T012 ‖ T013, then T014 → T015 | #739. The three templates are separate files |
| 2 | Mixed | T027 → T028 → T029 → T030, with T031 beside them, then T032 → T033 → T034 → T035 → T036 | #738. Tests share one file, so they run in order |
| 3 | Sequential | T016 → T020, then T021 → T022 → T023 → T024 → T025 | #739. Extends `_views.py`, so it follows Wave 2 |
| 3 | Parallel | T037 ‖ T039, then T038 → T040 | #738 |
| 4 | Sequential | T041 → T042 → T043 | #739. Can run any time after Wave 0 |
| 5 | Sequential | T044 → T045 → T046 → T047 → T048 → T049 | #739. Draws wfctl's views from the finished templates |

**Single-agent order, #739**: T002 → T003 - T005 → T006 - T015 → T016 - T025 → T041 - T043 → T044 - T049

**Single-agent order, #738**: T001 → T026 - T036 → T037, T039 → T038 → T040

---

## Agent Fanning Instructions

One agent for each PR, each in its own worktree. Within a PR, the only real parallel work is the three view templates (T011 - T013) and the two #738 docs tasks (T037, T039), and each is a single file a single agent writes in a few minutes, so fanning out costs more than it saves.
