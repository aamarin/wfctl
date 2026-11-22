Implementation complete: 2026-11-21

## Tasks at completion

~~~~markdown
# Tasks: Whole-system threat model

**Input**: Design documents in the feature's spec folder: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/threat-baseline-pass.md`, `quickstart.md`
**Prerequisites**: `plan.md` and `spec.md`, both present

**Design records**: 1 listed in `design.md`, `docs/architecture/design/818-threat-baseline-layers-over-upstream.md`. No task below reverses it. Upstream's files stay unedited except the attribution line, and every wfctl addition lives in `threat-baseline`, `design-levels`, or tests.

**Tests**: Every test task is written to fail first, against the vendored files or the missing reader, before the task that makes it pass. All commands run through `uv run` from the worktree root.

**Plan review leftovers folded in here**: The second plan review left six minor findings open. Five of them are handled by tasks below, so the plan didn't need a third review round:

1. PR-008: T024 names `tests/test_pipeline_needs_person.py` as the test the new pass breaks. `tests/pipeline_payload_snapshot.json` holds step rows only.
2. PR-010: T036 adds a text test for the `design-levels` lines, and T005 diffs the vendored files against `d3bea6b5`.
3. PR-013: T019 and T021 hold the pass when there's no trunk and the record listing can't see committed records.
4. PR-014: T033 checks that no shipped `allowed-tools` grants `step none brainstorm.threat-baseline`, and T029 checks that `threat-baseline` carries FR-007a's, FR-007b's, and FR-015a's lines.
5. PR-009: T030 has `threat-baseline` give Claude upstream's own path, so the pre-granted helper call matches.

PR-011, about committing the threat map to a public repository, is a decision no requirement makes, so it's tracked as its own issue rather than as a task here. The analyze step removed the task that first carried it, which is why the IDs skip T031.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel, since it touches different files and depends on no incomplete task
- **[Story]**: The user story the task belongs to (US1 to US4)

---

## Phase 1: Setup (vendored files and attribution)

**Purpose**: Put upstream's files in the tree, unedited, with their attribution, so every later phase has the real files to test against.

- [X] T001 Fetch `anthropics/defending-code-reference-harness` at `d3bea6b5` into a scratchpad directory, outside the repository, and copy `threat-model/{SKILL.md,README.md,bootstrap.md,interview.md,schema.md}` to `wfctl/agents/skills/threat-model/` and `_lib/checkpoint.py` to `wfctl/agents/skills/_lib/checkpoint.py`, byte for byte; verify with T005
- [X] T002 Append `Derived from [anthropics/defending-code-reference-harness](https://github.com/anthropics/defending-code-reference-harness) (Apache-2.0, © 2026 Anthropic PBC).` as the last line of `wfctl/agents/skills/threat-model/SKILL.md`, after checking that upstream's copyright line reads "2026 Anthropic PBC" (research R8.1); verify with T009
- [X] T003 Copy upstream's `LICENSE` to `wfctl/agents/skills/LICENSE-Apache-2.0` byte for byte (research R8.3); verify with T010
- [X] T004 Add an `## anthropics/defending-code-reference-harness` section to `wfctl/agents/skills/NOTICES.md` naming `threat-model` and `_lib/checkpoint.py` with upstream's copyright line, give every section a licence line, and change both the opening paragraph and the "Every upstream licence above is the MIT licence" sentence at line 59 to cover an Apache-2.0 upstream (research R8.3, R8.4); verify with T009 and T010
- [X] T005 Diff `wfctl/agents/skills/threat-model/` and `wfctl/agents/skills/_lib/` against the scratchpad copy from T001 and confirm the only difference is the attribution line in `SKILL.md`; record the command and its output in the PR body's verification section (spec User Story 2 AC1)
- [X] T006 Add a `threat-model` row to the first table and an `agents/skills/_lib/checkpoint.py` row to the second table in `docs/architecture/vendor-upstream-skills.md` (FR-004, research R8.2); verify with T009

### Tests for the vendored files (write first, see each fail against T001's files)

- [X] T007 [P] Add `argument-hint` to `ALLOWED_KEYS` in `tests/test_skill_frontmatter.py:19`, with a comment saying it's a Claude Code key upstream carries; confirm the test fails on `threat-model/SKILL.md` before the change and passes after (FR-018, research R10.1)
- [X] T008 [P] Widen `_OWN_FILE` in `tests/test_skill_cross_references.py:94` to also match "Read `X` in this directory"; confirm it fails when `interview.md`, `bootstrap.md`, or `schema.md` is removed from the vendored folder (FR-017, research R10.2)
- [X] T009 Change `tests/test_skill_attribution.py` so `_ROW` accepts `_`, `_sections` reads each section's licence from the notice instead of `_licence_the_notices_carry()`, and a `_lib/` claim pattern joins `_reference_claims` so the notice naming `_lib/checkpoint.py` is checked against the record's row; confirm `test_every_attribution_line_agrees_with_its_notice_entry` fails on the Apache-2.0 line before the change (research R8, test-fix items 1, 2, and 4)
- [X] T010 Add a test in `tests/test_skill_attribution.py` that checks the Apache-2.0 section of `NOTICES.md` against `wfctl/agents/skills/LICENSE-Apache-2.0`, the way the MIT block is checked against `LICENSE` (research R8, test-fix item 3)
- [X] T011 Validate Phase 1 with `uv run pytest -q tests/test_skill_frontmatter.py tests/test_skill_cross_references.py tests/test_skill_attribution.py` and `uv run ruff check tests/` — merge gate

**Checkpoint**: Upstream's files ship unedited, attributed, and noticed, and the three vendored-file tests plus the attribution test are green.

---

## Phase 2: Foundational (install and mirror)

**Purpose**: Make the vendored files and the new skill reach every agent's skills folder. User Story 2's helper check and User Story 4's run both depend on this.

- [X] T012 [P] Write a failing test in `tests/test_install_skills.py` that `install-skills --agent claude` mirrors `threat-model`, `threat-baseline`, and `_lib` into `.claude/skills/` (FR-002)
- [X] T013 [P] Write a failing test in `tests/test_install_skills.py` that `install-skills` adds `.threat-model-state/` to the ignore entries it writes (FR-003)
- [X] T014 [P] Write a failing test, in a new `tests/test_claude_skill_paths.py`, that reads every `.claude/skills/<path>` a shipped skill names and checks that `<path>`'s first segment is a mirrored item that ships (FR-016, research R10.3)
- [X] T015 Add `threat-model`, `threat-baseline`, and `_lib` to `_MIRRORED_SKILLS` in `wfctl/cli.py`; verify with T012 and T014
- [X] T016 Add `.threat-model-state/` to the paths `install-skills` passes to `_ensure_gitignored` near `wfctl/cli.py:6080` (research R9); verify with T013
- [X] T017 Validate Phase 2 with `uv run pytest -q tests/test_install_skills.py tests/test_claude_skill_paths.py` and `uv run mypy` — merge gate

**Checkpoint**: The mirror and ignore entry are in place. T012 and T014 pass only once T030 has created `threat-baseline/SKILL.md`, so stub that file with frontmatter and a one-line body here if Phase 4 hasn't run yet.

---

## Phase 3: User Story 1 - Brainstorm pauses until the baseline is committed (Priority: P1) 🎯 MVP

**Goal**: A branch that adds or edits a level-2 record with a `## Threat model` section can't leave brainstorm until `THREAT_MODEL.md` is committed at the repository root, or until the user records that the pass doesn't apply.

**Independent Test**: In a scratch repository, add a level-2 record with a `## Threat model` heading on a branch and run `wfctl status`. The pass reads in progress with `/threat-baseline` as the next command. Commit a `THREAT_MODEL.md` at the root, and the pass reads done.

**Verification**:

- Automated: `tests/test_pipeline_threat_baseline.py`, plus the updated pass-order assertions in `tests/test_declared.py` and `tests/test_pipeline_needs_person.py`
- Manual: `quickstart.md` steps 2 and 3 in a scratch repository
- Evidence: `wfctl status` shows `threat-baseline ▶` with `next: /threat-baseline`, then `●` after the commit, and `skipped` on a branch with no threat-model record

### Tests for User Story 1 (write first, see them fail)

- [X] T018 [P] [US1] Write state tests in a new `tests/test_pipeline_threat_baseline.py` for the rows of research R6 that need no git failure: checks off reads `skipped`; arch root outside the tree reads `skipped` with "records are kept outside this repository"; no threat-model record reads `skipped`; file committed reads `done`; file committed on the trunk before the branch reads `done`; file missing reads `in_progress` with the reason naming `THREAT_MODEL.md` and a remedy naming `/threat-baseline`; file present but uncommitted reads `in_progress`; file staged but not committed reads `in_progress`; an empty committed `THREAT_MODEL.md` reads `done`, since wfctl never reads its contents (FR-013); and the missing-file case reads the same `in_progress` with auto-approve on as off (FR-014)
- [X] T019 [P] [US1] Add git-failure and no-trunk tests to `tests/test_pipeline_threat_baseline.py`: `touched_on_this_branch` returning `None` reads `in_progress` with `GIT_UNANSWERED_REASON` and `GIT_UNANSWERED_HELP`; a failed `HEAD` read reads `in_progress` with `BASELINE_UNANSWERED_REASON`; with no trunk, an uncommitted record and a committed threat-model record reads `in_progress` with `GIT_UNANSWERED_REASON` rather than `skipped` (PR-013)
- [X] T020 [P] [US1] Add matching and fold tests to `tests/test_pipeline_threat_baseline.py`: a `## Threat model` heading inside a fenced code block doesn't count; `## Threat model (revised)` counts, matching `reviewing-security`'s `^## Threat model` grep; past `spec.md`, each `in_progress` row reads `done` and its reason appears in `collect_warnings`; a `step none brainstorm.threat-baseline` claim reads `skipped` with the claim's reason; the remedy text labels the `step none` line as the user's decision

### Implementation for User Story 1

- [X] T021 [US1] Add `brainstorm_threat_baseline` and `BASELINE_UNANSWERED_REASON` to `wfctl/_evidence.py`, checking conditions in research R6's order. Ask `touched_on_this_branch(repo_root, arch, exclude=non_record_subtrees(arch))` before `branch_records(repo_root, arch)`. Match `^## Threat model` outside fenced code in each `Record.body`. Read `HEAD` with `subprocess.run(["git", "ls-tree", "--name-only", "HEAD", "--", "THREAT_MODEL.md"])`. When `trunk_branch` returns `None` and the listing finds no threat-model record, read `in_progress` with `GIT_UNANSWERED_REASON`, since committed records weren't listed. This replaces research R6 row 4's `skipped` with `DRAWINGS_UNCHECKED` and the matching row in `data-model.md`: with no trunk, git can't say what the branch committed, and the spec's edge case reads that as in progress, not skipped. The drawing check can skip there because `wfctl arch accept` catches a bad drawing later, and nothing later catches a missing baseline. Fold every `in_progress` result to `done` with its reason and remedy once `spec.md` exists. Give the function a docstring stating the no-`design.md` limit (research R6). Verify with T018, T019, and T020
- [X] T022 [US1] Write the remedy constant in `wfctl/_evidence.py` to match `contracts/threat-baseline-pass.md`, with `/threat-baseline` first and the `step none` line labeled "This is the user's decision, not the agent's"; verify with T020
- [X] T023 [US1] Register `SubStep("threat-baseline", "/threat-baseline", _AUTOMATIC, brainstorm_threat_baseline)` between `architecture` and `software-design` in `wfctl/_pipeline.py:126`; verify with T018 and T024
- [X] T024 [US1] Update the brainstorm pass lists in `tests/test_declared.py:25`, `:399`, and `:406`, and the `needs_person` map in `tests/test_pipeline_needs_person.py:210-214`, to include `threat-baseline` with `needs_person` false; check `tests/pipeline_payload_snapshot.json` and update it only if it names the pass (FR-008, FR-014, PR-008)
- [X] T025 [US1] Confirm `wfctl check-body` asks for a `step none brainstorm.threat-baseline` reason in the PR body with a test in `tests/test_pipeline_threat_baseline.py` that writes the claim and runs the check against a body that omits it (FR-012)
- [ ] T026 [US1] Run `quickstart.md` steps 2 and 3 in a scratch repository outside the worktree and record what `wfctl status` printed for each state
- [X] T027 [US1] Validate User Story 1 with `uv run pytest -q tests/test_pipeline_threat_baseline.py tests/test_declared.py tests/test_pipeline_needs_person.py`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: The pass holds a branch with a threat-model record and no committed baseline, holds on a git failure instead of skipping, and reads `done` with a warning past `spec.md`.

---

## Phase 4: User Story 2 - `/threat-baseline` builds the whole-system threat model (Priority: P2)

**Goal**: `/threat-baseline` runs upstream's `threat-model` against the repository root, adds wfctl's opening line and rejected-fixes section, and commits `THREAT_MODEL.md`.

**Independent Test**: After `uv run wfctl install-skills --agent claude` in a repository with no threat model, run `/threat-baseline`. `THREAT_MODEL.md` is committed at the root with upstream's eight sections, the rejected-fixes section, and the opening line.

**Verification**:

- Automated: `tests/test_threat_baseline_skill.py` (text checks on the shipped skill and wrapper), `tests/test_install_skills.py`, `tests/test_claude_skill_paths.py`
- Manual: `quickstart.md` step 1, and the helper check `python3 .claude/skills/_lib/checkpoint.py load ./.threat-model-state` printing `{"status": "absent"}`
- Evidence: the installed `.claude/skills/` lists `threat-model`, `threat-baseline`, and `_lib`; `git status` after a bootstrap doesn't list `.threat-model-state/`

### Tests for User Story 2 (write first, see them fail)

- [X] T028 [P] [US2] Write a new `tests/test_threat_baseline_skill.py` that pins, by text, the lines `threat-baseline/SKILL.md` must carry: its opening says upstream's `threat-model` does the work (FR-006); it reads `auto_approve` from `wfctl status --json` (research R1); it runs `bootstrap-then-interview` when the flag is off and `bootstrap` plus the self-walkthrough when it is on (FR-005); it places the rejected-fixes section after upstream's eight (FR-007); it names the helper by the `_lib` folder beside the loaded skill (FR-005a)
- [X] T029 [P] [US2] Extend `tests/test_threat_baseline_skill.py` to pin that `threat-baseline/SKILL.md` ends by committing `THREAT_MODEL.md` alone with `git commit ... -- THREAT_MODEL.md` (FR-007a), re-reads an existing `## Threat model` section against the new baseline (FR-015a), and says, as does `wfctl/agents/commands/threat-baseline.md`, that `wfctl step none brainstorm.threat-baseline` is the user's to run (FR-007b)

### Implementation for User Story 2

- [X] T030 [US2] Write `wfctl/agents/skills/threat-baseline/SKILL.md` per research R1 and R2: frontmatter with `name`, `description`, and `allowed-tools: Bash(wfctl status*) Bash(git add THREAT_MODEL.md) Bash(git commit*) Bash(python3 .claude/skills/_lib/checkpoint.py *)`; an opening saying upstream's skill does the work; the mode choice from `auto_approve`; the helper path, telling the agent to use `.claude/skills/_lib/checkpoint.py`, upstream's own path, when loaded from `.claude/skills/`, and `<folder this skill was loaded from>/../_lib/checkpoint.py` otherwise (PR-009). On Claude this replaces research R2's relative path, which doesn't match upstream's pre-granted call, and still meets FR-005a, since `.claude/skills/_lib/` is the `_lib` folder beside the loaded skill; the opening line and rejected-fixes section; the self-walkthrough through Shostack's four questions; the re-read of an existing `## Threat model` section; the commit; and the line saying `step none` is the user's. Verify with T028 and T029
- [X] T032 [US2] Write `wfctl/agents/commands/threat-baseline.md`, the wrapper for layers other than Claude, pointing at the skill and saying `step none` is the user's (research R7, FR-007b); verify with T029, and confirm `_mirror_supersedes_wrapper` suppresses it in the Claude layer by running `uv run wfctl install-skills --agent claude` and checking that `.claude/commands/threat-baseline.md` isn't written
- [X] T033 [US2] Add a test in `tests/test_threat_baseline_skill.py` that reads every shipped skill's `allowed-tools` and fails on any grant that would cover `wfctl step none brainstorm.threat-baseline`, such as `Bash(wfctl *)` or `Bash(wfctl step none *)` (FR-007b, PR-014)
- [X] T034 [US2] Run `uv run wfctl install-skills --prune --yes --agent claude`, list `.claude/skills/threat-model`, `.claude/skills/threat-baseline`, and `.claude/skills/_lib`, and run `python3 .claude/skills/_lib/checkpoint.py load ./.threat-model-state`, which prints `{"status": "absent"}` (quickstart step 1, SC-003)
- [X] T035 [US2] Validate User Story 2 with `uv run pytest -q tests/test_threat_baseline_skill.py tests/test_install_skills.py tests/test_claude_skill_paths.py` and `uv run wfctl doctor` — merge gate

**Checkpoint**: The skill and wrapper ship, install for Claude, and run the helper from the installed path without a prompt.

---

## Phase 5: User Story 3 - A design session on one control doesn't load the whole-system skill (Priority: P3)

**Goal**: `design-levels` sends the agent to `/threat-baseline` before a control's threat model when no baseline is committed, and tells it not to load `threat-model` while writing one control's section.

**Independent Test**: A design-time prompt about one control, run against the installed tree, writes a `## Threat model` section in a level-2 record and doesn't load `threat-model`.

**Verification**:

- Automated: the `design-levels` text test in `tests/test_threat_model_skills.py`
- Manual: `quickstart.md` step 4, the design-time prompt
- Evidence: the session transcript shows no `threat-model` skill load, and the record carries the section

- [X] T036 [P] [US3] Add a test to `tests/test_threat_model_skills.py` that pins, by text, the `design-levels` lines naming `threat-baseline` as the whole-system skill, saying not to load `threat-model` for one control, and saying to run `/threat-baseline` first when no `THREAT_MODEL.md` is committed (FR-015, PR-010); see it fail
- [X] T037 [US3] Add the paragraph to the security-control part of `wfctl/agents/skills/design-levels/SKILL.md`, near line 215; verify with T036
- [ ] T038 [US3] After `uv run wfctl install-skills --prune --yes --agent claude`, run a design-time prompt about one security control in a Claude Code session on the installed tree and confirm it writes a `## Threat model` section and doesn't load `threat-model` (quickstart step 4, SC-004); record the result in the PR body
- [X] T039 [US3] Validate User Story 3 with `uv run pytest -q tests/test_threat_model_skills.py` — merge gate

**Checkpoint**: The primary route sends the agent to the baseline first, and the pass from User Story 1 catches a run that skips it.

---

## Phase 6: User Story 4 - wfctl has its own whole-system threat model (Priority: P4)

**Goal**: wfctl's own repository has a committed `THREAT_MODEL.md` at its root, built by `/threat-baseline` from the installed tree.

**Independent Test**: `THREAT_MODEL.md` exists at the repository root on this branch, committed, with the opening line and the rejected-fixes section.

**Verification**:

- Automated: `git ls-tree --name-only HEAD -- THREAT_MODEL.md` prints the name
- Manual: read the file's first line and last section
- Evidence: `wfctl status` on a scratch branch with a threat-model record reads the pass `done` on the first read

- [X] T040 [US4] Run `/threat-baseline` on wfctl from the installed tree. With auto-approve on, that's `bootstrap` plus the self-walkthrough, and the skill commits `THREAT_MODEL.md` itself (FR-019, SC-005); verify with `git ls-tree --name-only HEAD -- THREAT_MODEL.md`
- [X] T041 [US4] Confirm `THREAT_MODEL.md` opens with the working-map line and ends with the rejected-fixes section after upstream's eight, and that `git status` doesn't list `.threat-model-state/` (quickstart step 5, User Story 2 AC3 and AC6)
- [ ] T042 [US4] Validate User Story 4 by running `uv run wfctl status` on this branch and confirming the `threat-baseline` pass reads `done` — merge gate

**Checkpoint**: wfctl's own baseline is committed, and later security branches find it.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T043 Create the release note with `uv run towncrier create 818.addition.md --content "..."`, saying in plain words what a user of wfctl will notice: a `/threat-baseline` skill, and a brainstorm pass that waits for a committed `THREAT_MODEL.md` when a branch writes a security record; verify with `uv run wfctl verify`
- [x] T044 Run the full suite with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy`
- [x] T045 Run `uv run wfctl install-skills --prune --yes --agent claude` and then `uv run wfctl doctor`, which exits 0
- [x] T046 Validate the branch with `uv run wfctl verify` — merge gate

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 (Setup)**: no dependencies.
- **Phase 2 (Foundational)**: needs Phase 1's vendored files for T014. T012 needs `threat-baseline/SKILL.md` to exist, so a stub is fine until T030.
- **Phase 3 (US1)**: needs nothing from Phases 1 and 2. It touches `_evidence.py`, `_pipeline.py`, and pipeline tests, so it can run in parallel with Phases 1 and 2.
- **Phase 4 (US2)**: needs Phases 1 and 2.
- **Phase 5 (US3)**: needs T030 to exist so the paragraph names a real skill. Its test can be written any time.
- **Phase 6 (US4)**: needs Phases 1 to 5 installed.
- **Phase 7 (Polish)**: needs every earlier phase.

### Within each story

Tests are written and seen to fail before the implementation task that makes them pass. The validation task closes each phase.

## Parallel Opportunities

- Phase 1: T007 and T008 touch different test files and can run together once T001 is done.
- Phase 2: T012, T013, and T014 can be written together.
- Phase 3 can run alongside Phases 1 and 2, since it touches different files. Within it, T018, T019, and T020 are one file written in three passes, so they run in order. They're marked [P] only against other phases.
- Phase 4: T028 and T029 extend the same file and run in order; both can run alongside T036 in Phase 5.

### Parallel example: User Story 1 alongside Setup

```text
Agent A: T001 → T002 → T003 → T004 → T005 → T006 → T007/T008 → T009 → T010 → T011
Agent B: T018 → T019 → T020 → T021 → T022 → T023 → T024 → T025 → T026 → T027
```

## Implementation Strategy

### MVP first

The pass (User Story 1) is the MVP, since it's the check that makes the skill run at the right time. It can merge on its own: a branch with a threat-model record is held, and the remedy names `/threat-baseline` before the skill ships. That's why Phase 3 doesn't wait on the vendoring.

### Incremental delivery

1. Phase 3 alone gives the check.
2. Phases 1, 2, and 4 give the skill the check names.
3. Phase 5 adds the primary route, which sends the agent to the baseline before the per-control threat model.
4. Phase 6 builds wfctl's own baseline, the first real run.

`/speckit.decompose` decides PR boundaries. These phases are a suggestion, not a commitment.
~~~~
