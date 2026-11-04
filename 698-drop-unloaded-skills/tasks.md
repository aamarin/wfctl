# Tasks: Drop unloaded skills

**Input**: Design documents from `specs/698-drop-unloaded-skills/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md, plan-review.md

Design records read before generating these tasks:
`docs/architecture/design/698-brainstorm-listed-once.md` (found, `proposed`).
T006 and T011 implement its Decision, and no task reverses it.

The plan review left 2 MAJOR and 5 MINOR findings open and no BLOCKER. The tasks
below carry them rather than editing `plan.md`, and each task names the finding
it settles.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [x] T001 Confirm the baseline is green before any edit: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`; verify with all three exiting 0

## Phase 2: Foundational

No foundational tasks. Both stories edit the same bundle, and Phase 3 does the
deletions they share.

## Phase 3: User Story 1 - A new session loads a shorter listing (Priority: P1) 🎯 MVP

**Goal**: The Claude listing loses `using-superpowers`,
`verification-before-completion`, `brainstorm`, and `speckit-brainstorm`, and
nothing wfctl ships points at a dropped skill.

**Independent Test**: A fresh `install-skills --agent claude` in a clone leaves
none of the four under `.claude/skills/`, and `claude -p hi` there loads fewer
tokens than 39,789.

### Tests for User Story 1

- [x] T002 [US1] Replace `test_brainstorm_is_mirrored_onto_the_native_discovery_path` with a test asserting `speckit-brainstorm` is not in `_MIRRORED_SKILLS` and `speckit.brainstorm.md` carries no `disable-model-invocation`, in tests/test_skill_cross_references.py; verify it fails before T006 and T010
- [x] T003 [US1] Add a test that no file under `wfctl/agents/` names a dropped skill, in tests/test_skill_cross_references.py. It matches `using-superpowers`, `verification-before-completion`, `skills/brainstorm/`, and a `/brainstorm` command token not preceded by `.` or a word character, and nothing else, so the `brainstorm` step's name is left alone (PR-002). Verify it fails before T004 and T007
- [x] T004 [US1] Remove `brainstorm`, `using-superpowers`, and `verification-before-completion` from `_SUPPRESSED_ON_A_MIRRORING_LAYER` in tests/test_install_skills.py; verify `test_the_pinned_set_is_the_whole_intersection` passes after T005 and T006

### Implementation for User Story 1

- [x] T005 [US1] Delete wfctl/agents/skills/{using-superpowers,verification-before-completion,brainstorm}/ and wfctl/agents/commands/{using-superpowers,verification-before-completion,brainstorm}.md; verify with T003 and `test_every_declared_mirror_names_a_shipped_skill`
- [x] T006 [US1] Remove `brainstorm`, `speckit-brainstorm`, `using-superpowers`, and `verification-before-completion` from `_MIRRORED_SKILLS` in wfctl/cli.py, with the comments that defended them, and change `_mirror_supersedes_wrapper`'s `/brainstorm` example to `/design-levels`; verify with T002 and T004, and that `model-the-domain`, `receiving-code-review`, `python-pattern-selection`, and `python-package-layout` are still in the set (FR-008)
- [x] T007 [US1] Repoint `design-levels` §4 at `wfctl verify` in wfctl/agents/skills/design-levels/SKILL.md, and the overview sentence and diagram line in wfctl/agents/skills/python-pattern-selection/SKILL.md; verify with T003 and tests/test_skill_cross_references.py
- [x] T008 [P] [US1] Drop the two superpowers names from wfctl/agents/skills/NOTICES.md and their rows from docs/architecture/vendor-upstream-skills.md, with a Log line in the record; verify with tests/test_skill_attribution.py
- [x] T009 [P] [US1] Add a Log line to docs/architecture/level-4-owns-pattern-selection.md and docs/architecture/mirror-supersedes-the-wrapper.md saying #698 stopped shipping the skills their Context names (PR-006); verify with `uv run wfctl check config` and `uv run pytest -q tests/test_arch*.py`
- [x] T010 [US1] Widen `/speckit.brainstorm`'s description in wfctl/agents/commands/speckit.brainstorm.md to name a new feature or major change that needs design thinking before code, keeping `speckit-brainstorm` and `design.md` in it; verify with tests/test_skill_cross_references.py
- [x] T011 [US1] Change the comment in tests/test_architecture_design_skill.py that names `verification-before-completion` as a PASS/FAIL source; verify with `uv run ruff check tests/`

## Phase 4: User Story 2 - A project that already has a dropped skill loses it (Priority: P1)

**Goal**: An upgrade over an existing install reports the dropped paths, and
`--prune` removes them from both layers without touching the project's own
files.

**Independent Test**: The scratch-repo upgrade in quickstart.md.

### Tests for User Story 2

- [x] T012 [US2] Add a test in tests/test_install_skills.py. It builds a bundle with a mirrored skill, its wrapper, and the github tracker files (PR-005), and installs it with `--agent claude --tracker github`. Then it adds a hand-authored `.claude/skills/my-own` and installs a bundle without that skill, using `--agent claude` (PR-001). Assert the run reports the `.agents/skills/`, `.agents/commands/` and `.claude/skills/` paths and removes nothing, that `--prune --agent claude` removes all three, and that `my-own` and `.agents/trackers/github.json` remain. Verify with `uv run pytest -q tests/test_install_skills.py`
- [x] T013 [US2] In the same file, add the unmirrored case: a skill that stays in the bundle but leaves `_MIRRORED_SKILLS`. After `--prune --agent claude`, the `.claude/skills/` copy is gone, the `.agents/skills/` copy stays, and the wrapper now lands in `.claude/commands/` (PR-004); verify with `uv run pytest -q tests/test_install_skills.py`

### Implementation for User Story 2

No code change. The orphan rule in `install_skills_cmd` already handles both
cases (research.md §2). PR-003, a hand-authored `speckit-brainstorm` restored
from backup that `doctor` then reports, is accepted as is and named in the PR.

- [ ] T014 [US2] Run the quickstart upgrade by hand with this branch's bundle, and record the output for the PR; verify against quickstart.md steps 3 - 5

## Phase 5: Polish

- [x] T015 Commit the release note changes/698.change.md, which names the bob and copilot layers' copies going the same way (PR-007); verify with `uv run wfctl verify`
- [x] T016 Run `uv run wfctl install-skills --agent claude --prune --yes` and `uv run wfctl doctor` in this worktree; verify `doctor` exits 0
- [x] T017 Measure the "hi" baseline in a fresh clone of this branch with the Claude layer installed; verify it is below 39,789 and record both numbers for the PR

## Dependencies

- T001 first.
- T002, T003, and T004 are written before T005 and T006 and fail until those land.
- T005 before T006, since `test_every_declared_mirror_names_a_shipped_skill` fails while the set names a deleted skill.
- T007, T008, T009, T010, and T011 after T005. T008 and T009 touch different files and run in parallel.
- Phase 4 after Phase 3, since T012 and T013 run against the trimmed bundle.
- T015 to T017 last.

## Parallel Example

```text
T008 NOTICES.md and vendor-upstream-skills.md
T009 level-4-owns-pattern-selection.md and mirror-supersedes-the-wrapper.md
```

## Implementation Strategy

Phase 3 alone delivers the shorter listing for fresh installs. Phase 4 adds no
code, only tests and a by-hand check, so both stories ship in one PR.
