---
description: 'Task list for #649: the design checks match records to the contexts a branch changes'
---

# Tasks: The design checks match records to the contexts a branch changes

**Input**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/cli.md`, and `quickstart.md` in this feature folder, and the level-3 record `docs/architecture/design/649-contexts-module.md`
**Prerequisites**: #635 (`635-arch-folder-per-branch-notes`) merges before Phase 3, and #648 (`648-design-gate`) merges before Phase 9. Phases 1, 2, and 8 and most of Phase 10 need neither.

**Tests**: Every phase writes its tests first and runs them red before writing the code. Tests that check output pin `NO_COLOR` (`conftest.py`). Test names are sentences, and each docstring names the failure the test guards against.

**Organization**: Phases follow the spec's story priorities. The plan's Phase A (names, the `governs` field, and the doctor finding) is spread across Phases 2, 8, and 10, and those three can merge before #635 does. See Implementation Strategy.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: the spec's user story (US1 to US7)
- Every checkpoint passes `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy`

## Review findings these tasks settle

The third plan review left six MINOR findings open. Each one is settled in the task named here, so the implementer doesn't have to reopen it.

1. PR-012, what git's silence means: T017 and T018. The `context_gap` function returns the git verdict beside the gap and runs the FR-007 and FR-008 checks before it asks git. Each reader then hands the verdict to #648's `blocks`.
2. PR-013, the joined display wraps under the step table: T003.
3. PR-014, Project Structure leaves out files: the tasks name every file, including `_pipeline.py`, `_design_exceptions.reasons`, `test_pipeline_state_names.py`, `design/design-exceptions-module.md`, `context_gap`, `architecture-design`, `model-the-domain/SKILL.md`, and `commands/speckit.brainstorm.md`. The `design-passes` skill isn't edited (T035).
4. PR-015, the guard's details: T028 and T032.
5. PR-016, how a level picks its records: T017.
6. PR-017, the contract and data model don't match the plan: T001 and T002.

Where a task and `plan.md` disagree, the task wins. `plan.md` isn't edited to match, because an edit makes the third plan review stale and sends the pipeline back to `plan` (`plan-edit-requires-new-review`). Besides the six findings above, the tasks differ from the plan in four places:

1. `plan.md` Phase A item 5 puts the `--context` skill text in Phase A. T035 and T051 add it in Phases 5 and 9 instead, alongside the option it teaches, so no skill teaches an option or a refusal before it exists.
2. The same item says the `allowed-tools` line in `speckit-brainstorm` changes, and lists `design-passes` among the skills that teach `arch none --reason`. Neither changes (T035).
3. The Constitution Check says the `Level` constants are the one addition beyond `649-contexts-module.md`. The tasks also add `_arch.split_names` (T008), `_contexts.malformed` (T009), `pause` and `answers` (T016), and `_evidence.context_gap` (T018).
4. `plan.md` Phase B item 7 puts the guard's per-context check under "with a name list". T032 lists the per-context files instead, so the check still runs after the list goes away. The user chose this for #653 on 2026-10-27, and FR-002 and FR-021 now say so.

---

## Phase 1: Setup

**Purpose**: bring the feature folder's contract and data model in line with the plan, settle the display question, and commit the release note.

- [x] T001 [P] Add two sections to `contracts/cli.md` in this feature folder, in the form #635 uses (`../635-arch-folder-per-branch-notes/contracts/cli.md`, sections `wfctl end` and `Worktree guard`). The first is a `wfctl end` table for the Boundary line when the repo has a name list and the branch has a `design.md`: no gap reads `answered`, a gap reads `unanswered`, and a gap git couldn't check reads `unknown`, whether or not `spec.md` exists. The second is the per-context guard refusal, written out in full. It names the record and the context, and prints the `rm` command for `exceptions/<context>/boundary.md`. Verify by reading both against `plan.md` Phase B item 7, FR-020, and FR-021.
- [x] T002 [P] Update `data-model.md` in this feature folder. List `_record_gate` and `_observe` as readers of a per-context "no", and move the git-unanswered row in the Check outcome table below the missing-line and unknown-name rows, to match the order in T017. Verify by reading the table against T017.
- [x] T003 Keep the `<context>: no — <reason>` lines on the pass row, joined by `; ` as `plan.md` Phase B item 5 says, and print the pass row in `wfctl/cli.py` with `soft_wrap=True`, with a comment saying why (PR-013). The row can't carry only the context names, for three reasons in the current code:
  1. The row and the JSON `annotation` are the same field. A done `Assessment`'s `display` becomes the pass's `annotation`, and the `sub_steps` entries in the payload carry no `reason`.
  2. A done pass can't move the reasons into `reason`, because a pass with a reason makes its step read as held (`_PipelineSubStep` in `wfctl/_pipeline.py`).
  3. `--all` prints no line for a pass beyond its row. It only brings back skipped passes.

  So a names-only row would drop the reasons from `--all` and `--json`, which FR-010a requires, or need a new field in the payload, which research R6 rejected. Write the choice into the `wfctl status` section of `contracts/cli.md`, not into `plan.md`, since an edit to `plan.md` makes the plan review stale (see T012). Verify with a test that a pass row longer than the console width prints as one line.
- [x] T004 Create `changes/649.change.md` with `uv run towncrier create 649.change.md --content "…"`, in the `change` category. The note says that in a repo whose domain page lists its contexts, brainstorm now pauses until each context a branch lists has a record or a per-context "no" (FR-019). Verify with the release-note check in `uv run wfctl verify`.

---

## Phase 2: Foundational, part 1: names and `governs` (needs neither #635 nor #648)

**Purpose**: the readers every later phase calls. No check changes its behavior yet.

**⚠️ CRITICAL**: every user story depends on this phase.

- [ ] T005 [P] Write failing tests in `tests/test_arch_records.py`. `_arch.split_names` splits on commas, trims each entry, and drops empty ones. `parse_record` reads a `governs` field into `Record.governs`, and a record with no `governs` field gets `()`.
- [ ] T006 [P] Write failing tests in `tests/test_contexts.py` (new) for `_contexts.names(arch)`:
  1. The `Contexts` and `Outside parties` lines of an accepted domain page are read and combined.
  2. A `proposed` page is ignored.
  3. Two accepted pages are combined, and a name on both counts once.
  4. With no accepted page carrying a `Contexts` key, it returns `None`.
  5. An entry that doesn't match `[a-z0-9]+(-[a-z0-9]+)*`, such as `session continuity` or `../x`, is left off the list. `_contexts.malformed(arch)` returns it as `(page stem, entry)`.
- [ ] T007 [P] Write failing tests in `tests/test_contexts.py` for `_contexts.listed(spec_dir)`:
  1. The header line is read.
  2. A `Contexts:` line inside a code block below the first `## ` heading is ignored. This repo's own `design.md` has one.
  3. With no `design.md`, or no `Contexts` key, it returns `None`.
  4. An empty value returns `()`.
  5. Duplicates are removed, and the order is kept.
- [ ] T008 Add `split_names(value) -> tuple[str, ...]` and `Record.governs: tuple[str, ...] = ()` to `wfctl/_arch.py`, and have `parse_record` read `front.get("governs", "")` through `split_names`. Verify with T005.
- [ ] T009 Create `wfctl/_contexts.py`. A private `_header(path) -> dict[str, str]` scans the lines before the first `## ` heading with `_arch._key_value`, and `names`, `listed`, and `malformed` are built on it. The module imports `split_names` from `_arch`. Its docstring says why only the header is read (research R1), and why the name shape is checked, since each name becomes a folder in Phase 3. Verify with T006 and T007.
- [ ] T010 Add the `Contexts` and `Outside parties` lines to `docs/architecture/domain/wfctl.md` after `State: accepted`, with the names from the Decision section of `649-contexts-module.md` (FR-014). Verify that `uv run python -c "from pathlib import Path; from wfctl import _contexts; print(sorted(_contexts.names(Path('docs/architecture'))))"` prints all twelve names, and that `uv run wfctl doctor` exits 0.
- [ ] T011 Validate Phase 2 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate.

**Checkpoint**: Phase 8 (doctor) and T054 to T057 (skill text) can start now, before #635 merges.

---

## Phase 3: Foundational, part 2: per-context answers (after #635 merges)

**Purpose**: the per-context "no" on disk, the matcher, and the one function that both the check and the Boundary line call.

**⚠️ CRITICAL**: US1 to US4 and US6 depend on this phase.

- [x] T012 After #635 merges, fetch and rebase onto `origin/main`. Re-read `wfctl/_design_exceptions.py`, `wfctl/_record_gate.py`, `_review_gate._judge`, the claim lookup in `wfctl/_pipeline.py`, `_observe` in `wfctl/cli.py`, and `_exception_findings` in `check_body_cmd`. Wherever the merged code differs from `../635-arch-folder-per-branch-notes/plan.md`, edit Phase B of `plan.md` here before writing code, since this work follows #635's code, not its plan. An edit to `plan.md` makes the plan review stale, and wfctl then routes the pipeline back to `plan` until `/plan-review` runs on the revised plan or `wfctl step sign-off plan.plan-review --reason "…"` accepts it (`plan-edit-requires-new-review`). Verify with `git merge-base --is-ancestor <#635's merge commit> HEAD`.
- [x] T013 [P] Write failing tests in `tests/test_design_exceptions.py`, which #635 adds:
  1. `write`, `boundary`, `passes`, and `path` with `context=` use `exceptions/<context>/`.
  2. The title lines are `# No new boundary for <context>` and `# <step>.<pass> does not apply to <context>`.
  3. `passes` without a context reads one level and never reads a subfolder.
  4. `reasons(spec_dir)` returns each label and reason across the branch-wide and per-context files.
- [x] T014 Add a keyword-only `context: str | None = None` to `write`, `boundary`, `passes`, and `path` in `wfctl/_design_exceptions.py`, and add `reasons(spec_dir) -> list[tuple[str, str]]`. Without a context, each function behaves as #635 wrote it. Verify with T013.
- [x] T015 [P] Write failing tests in `tests/test_contexts.py` for `unanswered`, `pause`, and `answers`:
  1. `unanswered` returns the first listed context, in listed order, that has no governing record and no "no".
  2. A record that governs several contexts answers each of them.
  3. A "no" for one context doesn't answer another.
  4. `pause` checks for a missing or empty line first (`design.md lists no contexts`), then for an unknown name (`<name> is not a context on the domain page`), and then calls `unanswered` (`no <noun> governs <context>`).
  5. Each remedy matches the `wfctl status` section of `contracts/cli.md`, for both `ARCHITECTURE` and `SOFTWARE_DESIGN`.
  6. `answers` returns `<context>: no — <reason>` for each context answered with a "no".
- [x] T016 Add the `Level` `NamedTuple` (the record noun, the pass name, and the "no" command) with the `ARCHITECTURE` and `SOFTWARE_DESIGN` constants, and add `unanswered`, `pause`, and `answers` to `wfctl/_contexts.py` (research R2). `pause` returns `(reason, remedy)` or `None`, and says whether the result came from `unanswered`, so that T018 applies the git verdict only there. Verify with T015.
- [x] T017 Write failing tests in `tests/test_design_gate_drawing.py` for `_evidence.context_gap(repo_root, arch, spec_dir, level)`:
  1. It gathers level-2 records from `records_on_this_branch(repo_root, arch, exclude=[*non_record_subtrees(arch), arch / DESIGN_DIR])`, and level-3 records from `records_on_this_branch(repo_root, arch / DESIGN_DIR)`, read under `arch / DESIGN_DIR`. It skips a slug whose file the branch deleted. A mapping in `_evidence`, keyed by `Level`, picks the folder for each level, since `_contexts` doesn't call git (PR-016).
  2. It returns `None` when every listed context is answered, and otherwise the reason, the remedy, and the git verdict.
  3. A missing `Contexts` line or an unknown name is reported as such, even when git can't list the branch's records (PR-012, item 3).
  4. It decides that git can't list the branch's records when `_paths.trunk_branch` returns `None` or the arch root is outside the working tree, and not from `touched_on_this_branch`. With no trunk, one uncommitted change, and a governing record committed earlier on the branch, it doesn't report that context as unanswered (PR-012, item 2).
- [x] T018 Implement `context_gap` in `wfctl/_evidence.py`, applying the git verdict only to a result from `unanswered`. It doesn't call `blocks`, since each reader does that (PR-012, item 1). Keep the word `Contexts` out of its docstring and out of every other line of `_evidence.py` and `_arch.py`, because SC-005's grep would read it as a second reader. Verify with T017.
- [x] T019 Validate Phase 3 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate.

---

## Phase 4: User Story 1 - A record about the wrong context doesn't pass brainstorm (Priority: P1) 🎯 MVP

**Goal**: when the repo has a name list, a branch whose records govern a different context than the one it lists stays in brainstorm, and the pause names the context.

**Independent Test**: on a branch with `Contexts: session-continuity` and a level-2 record with `governs: install-and-drift`, `wfctl status` shows brainstorm as current, with the reason naming `session-continuity`.

**Verification**:

- Automated: `tests/test_design_gate_drawing.py`, User Story 1 scenarios 1 to 3
- Manual: `quickstart.md` step 2
- Evidence: the `architecture` row reads `no architecture record governs session-continuity`, and `--json` has `state: in_progress` and a remedy naming both answers

### Tests for User Story 1 ⚠️

- [x] T020 [US1] Write failing tests in `tests/test_design_gate_drawing.py` for User Story 1 scenarios 1 to 3: the row text, the `state` and `remedy` in `--json`, and a two-context line where only the second context is governed, which names the first.

### Implementation for User Story 1

- [x] T021 [US1] In `wfctl/_evidence.py`, make the per-context branch step 3 of `_architecture_answered`. It runs after the `spec.md` exit and #648's exit for `design_record_checks` set to `"off"`, ahead of #635's boundary exit and #648's git verdict, and only when `_contexts.names` returns a list and `design.md` exists. It calls `context_gap(..., ARCHITECTURE)` and hands the verdict to `blocks(verdict, "repo-declared")` (PR-012). Widen the return type to carry the remedy, and have `brainstorm_architecture` pass the remedy into its `Assessment`. Verify with T020.
- [x] T022 [US1] Validate User Story 1 with `uv run pytest -q tests/test_design_gate_drawing.py`, then the full suite, ruff, and mypy — merge gate.

**Checkpoint**: at level 2, a record about the wrong context no longer passes brainstorm, which is the gap #649 describes.

---

## Phase 5: User Story 2 - A matching record or a per-context "no" passes brainstorm (Priority: P1)

**Goal**: each listed context is answered by one record edit or one command, and every reader that saw a branch-wide "no" under #635 now sees the per-context ones too.

**Independent Test**: on User Story 1's branch, add `session-continuity` to the record's `governs` field and confirm brainstorm passes. On a fresh copy, run `wfctl arch none --context session-continuity --reason "…"` and confirm the same.

**Verification**:

- Automated: `tests/test_design_gate_drawing.py`, `tests/test_pipeline_commands.py`, `tests/test_step_none.py`, `tests/test_pipeline_state_names.py`, `tests/test_end_reports_observations.py`, `tests/test_record_gate.py`, and the `check-body` tests #635 adds
- Manual: `quickstart.md` steps 3 to 5
- Evidence: the row reads done with the display from T003, and the bare form refuses and names `--context`

### Tests for User Story 2 ⚠️

- [x] T023 [P] [US2] Write failing tests in `tests/test_design_gate_drawing.py` for User Story 2 scenarios 1 to 4. Scenario 3 writes `boundary.md` directly with `_design_exceptions.write`, since the CLI now refuses the bare form. Scenario 4 commits the governing record on trunk before the branch starts. Also test the done display from T003, with the drawing text first when `_judge_drawings` returns one (FR-010a).
- [x] T024 [P] [US2] Write failing tests in `tests/test_pipeline_commands.py` for `wfctl arch none --context`: the success line, and each refusal in `contracts/cli.md`, which are no name list, a name not on the list, and the bare form in a repo with a list. #635's empty-reason and placeholder-reason refusals still run first.
- [x] T025 [P] [US2] Write failing tests in `tests/test_step_none.py`. In a repo with a name list, `step none brainstorm.architecture` without `--context` gets the branch-wide refusal. `--context` on any pass other than `brainstorm.software-design` gets `--context applies only to brainstorm.software-design…`.
- [x] T026 [P] [US2] Write failing tests in `tests/test_pipeline_state_names.py`. A whole-pass claim on `brainstorm.architecture` or `brainstorm.software-design` that is already on disk doesn't mark the pass skipped when the repo has a name list, and still does without one (FR-011, SC-001).
- [x] T027 [P] [US2] Write failing tests in `tests/test_end_reports_observations.py`. With a name list, the Boundary line reads `answered` for a branch that answered every listed context with a "no" and changed no record. It reads `unanswered` for a branch whose only record governs a different context, and `unknown` for a gap git couldn't check. Without a name list, the line reads as #635 left it (FR-020).
- [x] T028 [P] [US2] Write failing tests in `tests/test_record_gate.py`, which #635 adds. With `exceptions/session-continuity/boundary.md` in the branch's own spec folder, `gh pr create` is refused when a level-2 record the branch changes governs `session-continuity`. It's allowed when the record governs only `install-and-drift`. The record in the allowed case is `accepted`, so #635's check for unaccepted records (R14) doesn't refuse it first (FR-021).

### Implementation for User Story 2

- [x] T029 [US2] Add `--context <name>` to `wfctl arch none` and `wfctl step none` in `wfctl/cli.py`, with the refusals and success lines in `contracts/cli.md`, run after #635's reason checks. `step none` accepts `--context` only for `brainstorm.software-design`. Verify with T024 and T025.
- [x] T030 [US2] In the claim lookup in `wfctl/_pipeline.py`, when `_contexts.names` returns a list, drop `brainstorm.architecture` and `brainstorm.software-design` from the dict `_design_exceptions.passes(spec_dir)` returns, before `_pass_states` reads it. Verify with T026.
- [x] T031 [US2] In `wfctl/_evidence.py`, give `brainstorm_architecture`'s done `Assessment` the display from T003 when at least one context was answered with a "no". Verify with T023.
- [x] T032 [US2] Add the per-context contradiction check to `wfctl/_record_gate.py`, so the guard refuses for the first of these that holds: the branch-wide contradiction, then the per-context one, then an unaccepted record. The check lists the `exceptions/*/boundary.md` files in the branch's own spec folder instead of reading the name list, since the working tree can hold another branch (#635 R13). For each level-2 record the branch changes, it reads the `governs` field from `git show <head>:<path>` with `_arch`'s frontmatter parser, the same way #635 reads the status. When a record governs a context that has a "no", the guard refuses, names the record and the context, and prints the `rm` command for `_design_exceptions.path(spec_dir, "boundary", context=<context>)`. Verify with T028 and with the refusal in `contracts/cli.md` from T001.
- [x] T033 [US2] In `wfctl/cli.py`, have `_exception_findings` in `check_body_cmd` read every reason through `_design_exceptions.reasons`. #635's R12 skips an inherited boundary exception when a sub-issue branch changes any level-2 record. An inherited per-context "no" is skipped only when a level-2 record the branch changes governs that same context, the same rule research R8 gives the guard (FR-018, #653). Verify with a test beside #635's `_exception_findings` tests.
- [x] T034 [US2] In `_observe` in `wfctl/cli.py`, when the repo has a name list and the branch has a `design.md`, read the Boundary line from `_evidence.context_gap(..., ARCHITECTURE)`. `None` reads `answered`, a gap reads `unanswered`, and a gap git couldn't check reads `unknown`, with no `spec.md` exit (research R7). `_observe` reports and doesn't gate, so it reads the verdict without calling `blocks`. Verify with T027.
- [x] T035 [US2] Wherever a skill teaches `wfctl arch none --reason`, add that a repo with a name list answers once per context with `--context <name>`, and that the bare form is refused there (FR-016). The places are:
  1. `wfctl/agents/skills/design-levels/SKILL.md`, the level-2 declaration block.
  2. `speckit-brainstorm/SKILL.md`, the re-entry paragraph.
  3. `architecture-design/SKILL.md`, in both places it teaches the command.
  4. `model-the-domain/SKILL.md`, each line that teaches the command, not the lines that only name it.

  The `allowed-tools` lines in `speckit-brainstorm/SKILL.md` and `wfctl/agents/commands/speckit.brainstorm.md` already grant `wfctl arch none*`, which covers `--context`, so they don't change. `design-passes/SKILL.md` tells the agent not to run `arch none` on its route, so it doesn't change either. Verify with `grep -rn "arch none" wfctl/agents/`, checking that each hit either has the note or only names the command.
- [x] T036 [US2] Validate User Story 2 with the full suite, ruff, and mypy — merge gate.

**Checkpoint**: level 2 is complete. Every reader of a level-2 "no" (the check, the claim lookup, the Boundary line, the guard, and `check-body`) reads the per-context form.

---

## Phase 6: User Story 3 - A bad or missing `Contexts` line pauses brainstorm (Priority: P1)

**Goal**: a misspelled name or a missing line doesn't let a branch skip the check.

**Independent Test**: with `Contexts: session-continuty`, the pause names the misspelled entry. With the line removed, the pause says `design.md lists no contexts`.

**Verification**:

- Automated: `tests/test_design_gate_drawing.py`, User Story 3 scenarios 1 to 3
- Manual: `quickstart.md` steps 6 and 7
- Evidence: each reason and remedy matches `contracts/cli.md`

### Tests for User Story 3 ⚠️

- [x] T037 [US3] Write tests in `tests/test_design_gate_drawing.py` for User Story 3 scenarios 1 to 3: the misspelled name with the name list as its remedy, a missing line, an empty line, and an outside party (`workmux`) accepted as a name. Add a test where git can't list the branch's records and the line is missing, which still reads `design.md lists no contexts` (PR-012, item 3).

### Implementation for User Story 3

- [x] T038 [US3] No new code is expected, since `pause` (T016) and `context_gap` (T018) handle these cases. If a T037 test fails, fix it in those functions rather than in the reader. Verify with T037.
- [x] T039 [US3] Validate User Story 3 with the full suite — merge gate.

---

## Phase 7: User Story 4 - A repo with no name list sees no change (Priority: P1)

**Goal**: SC-003 and SC-004. A repo that never modeled its domain, and every branch past specify, report the same position as before.

**Independent Test**: in a repo with no name list, a branch with `design.md` and one record passes brainstorm, with or without a `Contexts` line.

**Verification**:

- Automated: `tests/test_design_gate_drawing.py`, User Story 4 scenarios 1 to 3 and FR-013
- Evidence: the reason is `no architecture record for this change`, as it is today

### Tests for User Story 4 ⚠️

- [x] T040 [US4] Write tests in `tests/test_design_gate_drawing.py` for User Story 4 scenarios 1 to 3: no accepted page with a `Contexts` key, any record passing whatever its `governs` field says, and a `proposed` page ignored. Add FR-013: with a name list and `spec.md` present, neither check pauses.

### Implementation for User Story 4

- [x] T041 [US4] No new code is expected, since T021's branch runs only with a name list and a `design.md`. If a T040 test fails, fix that condition in `_architecture_answered`. Verify with T040.
- [x] T042 [US4] Validate User Story 4 with the full suite — merge gate.

---

## Phase 8: User Story 5 - `wfctl doctor` reports a `governs` name that isn't on the list (Priority: P2)

**Goal**: a typo in a level-2 record's `governs` field is found before a branch relies on the record. This phase needs only Phase 2.

**Independent Test**: commit a level-2 record with `governs: sesion-continuity` and confirm `wfctl doctor` reports it and exits 1.

**Verification**:

- Automated: `tests/test_remaining_commands.py` and `tests/test_arch_records.py`
- Manual: `quickstart.md` step 8
- Evidence: `✗ <slug>: governs sesion-continuity, which isn't on the domain page's name list`

### Tests for User Story 5 ⚠️

- [ ] T043 [P] [US5] Write failing tests in `tests/test_arch_records.py`. `validate(records, names)` reports one error finding per unknown `governs` name, and reports nothing when `names` is `None` or left out.
- [ ] T044 [P] [US5] Write failing tests in `tests/test_remaining_commands.py`. `wfctl doctor` reports an unknown `governs` name and exits 1. It reports a malformed domain-page entry in the form `contracts/cli.md` gives. It stays clean in a repo with no name list, even when a record has a `governs` field.

### Implementation for User Story 5

- [ ] T045 [US5] Add `names: frozenset[str] | None = None` to `validate` in `wfctl/_arch.py`, with the finding text from `contracts/cli.md`. Existing callers pass nothing and see no change. Verify with T043.
- [ ] T046 [US5] In `_check_arch_records` in `wfctl/cli.py`, pass `_contexts.names(root)` to `validate`, and report each entry `_contexts.malformed(root)` returns as a finding on its domain page. Verify with T044.
- [ ] T047 [US5] Validate User Story 5 with the full suite, ruff, and mypy, then run `uv run wfctl doctor` on this repo — merge gate.

---

## Phase 9: User Story 6 - The software design check matches the same way (Priority: P2, after #648 merges)

**Goal**: the level-3 check answers the same way the level-2 check does, counting only level-3 records.

**Independent Test**: on a branch that lists `session-continuity` and has a level-2 answer for it, a level-3 record that governs `install-and-drift` pauses the `software-design` row on `session-continuity`.

**Verification**:

- Automated: `tests/test_software_design_pass.py`, User Story 6 scenarios 1 to 3, and `tests/test_step_none.py` for the level-3 `--context` refusals
- Manual: `quickstart.md` step 9
- Evidence: the row reads `no software design record governs session-continuity`, then done after `wfctl step none brainstorm.software-design --context session-continuity --reason "…"`

- [ ] T048 [US6] After #648 merges, fetch and rebase onto `origin/main`. Re-read `brainstorm_software_design`, `blocks`, and the `design_record_checks` exit in `wfctl/_evidence.py`, and edit Phase C of `plan.md` wherever they differ from `../648-design-gate/plan.md`. The edit makes the plan review stale, as in T012. Verify with `git merge-base --is-ancestor <#648's merge commit> HEAD`.

### Tests for User Story 6 ⚠️

- [ ] T049 [US6] Write failing tests in `tests/test_software_design_pass.py`, which #648 adds, for User Story 6 scenarios 1 to 3. In scenario 3, a level-2 record governs the context and no level-3 record does, and the row still pauses. Also test the done display, and that a per-context "no" never hides the row. In `tests/test_step_none.py`, test `step none brainstorm.software-design` the way T024 tests `arch none`: the `--context` success line, the refusal with no name list, the refusal for a name not on the list, and the refusal of the bare form in a repo with a list (FR-010, FR-011). T025 can't test these, since the pass doesn't exist until #648 merges.

### Implementation for User Story 6

- [ ] T050 [US6] In `brainstorm_software_design` in `wfctl/_evidence.py`, call `context_gap(..., SOFTWARE_DESIGN)` and hand the verdict to `blocks`, in the same position as T021, ahead of #648's exit for `blocks` returning false. Give the done `Assessment` the display from T003. Verify with T049.
- [ ] T051 [US6] Wherever #648 taught `wfctl step none brainstorm.software-design --reason`, in `design-levels`, `speckit-brainstorm`, and `software-design-decisions`, add the `--context` note the same way T035 does at level 2. #648's narrow grant, `Bash(wfctl step none brainstorm.software-design *)`, already covers `--context`. Verify with `grep -rn "step none brainstorm.software-design" wfctl/agents/`.
- [ ] T052 [US6] Edit #635's level-3 record, `docs/architecture/design/design-exceptions-module.md`. Add a Log line and a short paragraph saying that `exceptions/` now has one subfolder per context, pointing at `649-contexts-module.md`. If that record is `accepted` by then, write a new record that supersedes it instead. Verify with `uv run wfctl arch check`.
- [ ] T053 [US6] Validate User Story 6 with the full suite, ruff, and mypy — merge gate.

---

## Phase 10: User Story 7 - The skills write the names the checks read (Priority: P2)

**Goal**: an agent learns the format from the skill before it meets a pause. T054 to T057 need only Phase 2. T058 needs #635, whose PR template adds the "Moves a boundary?" section.

**Independent Test**: after `uv run wfctl install-skills --agent claude`, each installed skill and template names the line or field it writes.

**Verification**:

- Automated: `uv run pytest -q tests/test_skill_cross_references.py tests/test_skill_commands.py`, and `uv run wfctl check config` for the PR template
- Manual: read each installed file named below
- Evidence: User Story 7 scenarios 1 to 4

- [ ] T054 [P] [US7] In `wfctl/agents/skills/model-the-domain/domain-model-template.md`, offer `accepted` as a `State` value and add the `Contexts` and `Outside parties` lines under it. In `model-the-domain/SKILL.md`, tell the agent to fill them from the Bounded Contexts table and the outside parties list as kebab-case short names, since each name becomes a folder name (FR-015). Verify by reading the installed copies.
- [ ] T055 [P] [US7] Add `governs: <names from the domain page's Contexts or Outside parties line>` to the frontmatter of `wfctl/agents/skills/architecture-decisions/record-template.md`, and say in `architecture-decisions/SKILL.md` what the field is for (FR-017). Verify by reading the installed copies.
- [ ] T056 [P] [US7] Make the same change to `wfctl/agents/skills/software-design-decisions/design-record-template.md` and `software-design-decisions/SKILL.md`. Verify by reading the installed copies.
- [ ] T057 [P] [US7] In `wfctl/agents/skills/design-levels/SKILL.md`, have the agent decide at level 2, before writing any record, which contexts the branch changes. In `speckit-brainstorm/SKILL.md`, have it write that list as the `Contexts` line under the title of `design.md` (FR-016). Verify by reading the installed copies.
- [x] T058 [US7] After #635 merges, add a `Contexts:` line to the placeholder of the "Moves a boundary?" section in `.github/pull_request_template.md`. In `wfctl/agents/skills/opening-a-change/SKILL.md`, have the agent copy the `Contexts` line from `design.md` into whichever section of the template has a `Contexts` line, and list each per-context "no" with its reason under it. The skill names the line, not the section (FR-018, PR-006). Verify with `uv run wfctl check config` and by reading the installed skill.
- [ ] T059 [US7] Run `uv run wfctl install-skills --agent claude`, and read each installed file that T035, T051, and T054 to T058 changed. Run `grep -rn -e "arch none" -e "step none" .agents/ .claude/` to confirm no instruction teaches the bare form without the `--context` note. Then validate with the full suite — merge gate.

---

## Phase 11: Polish and cross-cutting concerns

- [ ] T060 Run `grep -n "Contexts" wfctl/_evidence.py wfctl/_arch.py` and confirm it finds nothing (SC-005).
- [ ] T061 After `uv run wfctl install-skills --agent claude`, run the scratch-branch check in `quickstart.md`, steps 1 to 9. Delete the scratch branch and its spec folder afterwards.
- [ ] T062 Run the definition of done: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `uv run wfctl verify`, and `uv run wfctl doctor`.

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 (Setup)**: no dependencies. T003 decides the display that T031 and T050 build.
- **Phase 2 (Foundational, part 1)**: no dependencies. Every story depends on it.
- **Phase 3 (Foundational, part 2)**: Phase 2, and #635 merged. US1 to US4 and US6 depend on it.
- **US1 (Phase 4)**: Phase 3.
- **US2 (Phase 5)**: US1, since T031 extends the reader T021 changes.
- **US3 and US4 (Phases 6 and 7)**: US1. They don't depend on each other or on US2.
- **US5 (Phase 8)**: Phase 2 only.
- **US6 (Phase 9)**: Phase 3, US1 for the position T021 sets, and #648 merged.
- **US7 (Phase 10)**: T054 to T057 need Phase 2 only. T058 needs #635. T059 runs last, after T035 and T051.
- **Polish (Phase 11)**: every other phase.

### Within each story

Tests are written and seen to fail before the code. `_design_exceptions` and `_contexts` come before `_evidence`, and `_evidence` comes before the CLI and the guard.

### Parallel opportunities

- T001, T002, and T003 change different files.
- T005, T006, and T007 are three groups of tests. T006 and T007 share `tests/test_contexts.py`, so write them one after the other.
- Phase 8 and T054 to T057 can run beside Phase 3 and later phases, since they need only Phase 2.
- In Phase 5, T023 to T028 are each in their own test file.
- US3 and US4 can run beside US2.

## Parallel Example: User Story 2

```bash
Task: "Write failing tests for arch none --context in tests/test_pipeline_commands.py"
Task: "Write failing tests for step none --context in tests/test_step_none.py"
Task: "Write failing tests for the claim drop in tests/test_pipeline_state_names.py"
Task: "Write failing tests for the Boundary line in tests/test_end_reports_observations.py"
Task: "Write failing tests for the per-context guard in tests/test_record_gate.py"
```

## Implementation Strategy

### Before #635 merges

Phases 1 and 2, then US5 (Phase 8) and T054 to T057. This is the plan's Phase A, and it changes no check's behavior. The domain page gets its name list, doctor checks `governs` names against it, and the skills start writing the names. The `--context` skill text waits for Phase 5, so no skill teaches an option before it exists.

### MVP

Phase 3, then US1. That fixes the gap #649 describes at level 2. US2 has to follow before a release, because without it a paused branch can only answer with a record, and #635's readers can't see a per-context "no".

### Incremental delivery

1. Phase A: Phases 1, 2, and 8, and T054 to T057.
2. Level 2: Phases 3 to 7, and T058.
3. Level 3: Phase 9, after #648 merges.
4. T059 and Phase 11.

`/speckit.decompose` decides the PR boundaries. These slices are the ones whose verification works on its own.

## Notes

- `tests/test_design_exceptions.py`, `tests/test_record_gate.py`, and `tests/test_software_design_pass.py` don't exist yet. #635 and #648 add them, and these tasks extend them.
- The plan puts the guard test in `tests/test_worktree_guard.py`, but that file tests `_guard.py`, the check on writes into other worktrees. The record checks belong to `_record_gate.py` and are tested in `tests/test_record_gate.py` (PR-015), so T028 goes there.
- Commit after each task or logical group, with a `feat(649):`, `test(649):`, or `docs(649):` subject.
