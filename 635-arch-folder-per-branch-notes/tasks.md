---
description: 'Task list for moving design exceptions to the spec folder'
---

# Tasks: Design exceptions move to the spec folder

**Input**: Design documents in this feature's spec folder
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Every story writes its tests first and watches them fail. The suite
runs with `uv run pytest -q`, and every test that asserts on output pins
`NO_COLOR`. Each phase ends with the three repo checks:
`uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy`.

**Organization**: Tasks are grouped by user story, in priority order: US1 (P1),
then US2 and US5 (both P2), then US3 (P3), then US4 (P4). US4 comes last
because the cleanup only makes sense once US1 and US2 stop new files from
arriving.

**Design records**: 2 listed in design.md. Every task follows both as written.

- `docs/architecture/design-exceptions-live-with-specs.md`
- `docs/architecture/design/design-exceptions-module.md`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel, since it touches different files and depends on no incomplete task
- **[Story]**: The user story the task belongs to (US1 to US5)

## Path Conventions

Single project: `wfctl/` and `tests/` at the repository root. The spec folder is
the path `uv run wfctl feature-paths` prints as `FEATURE_DIR`.

---

## Phase 1: Setup

**Purpose**: The release note, which `wfctl verify` and the `release-note` CI job both require.

- [X] T001 Create `changes/635.change.md` with `uv run towncrier create 635.change.md --content "…"`. It says `wfctl arch none` and `wfctl step none` now write into the branch's spec folder, the reason goes in the PR body, and you need to upgrade wfctl before writing an exception (research R4). Verify by loading the `writing-style` skill before writing it, then running `uv run wfctl verify` in T063

**Checkpoint**: The branch carries its release note.

---

## Phase 2: Foundational

**Purpose**: The one module that owns the exceptions folder, and the helper that names the spec folder before it exists. Every story writes or reads through these two.

**⚠️ CRITICAL**: No user story work starts until this phase is done.

- [X] T002 Write `tests/test_design_exceptions.py`, failing. Cover the five functions in `data-model.md §_design_exceptions module`:
  1. `folder(spec_dir)` returns `spec_dir / "exceptions"`, and `path(spec_dir, "boundary")` returns `spec_dir / "exceptions" / "boundary.md"` without creating anything.
  2. `write` creates the spec folder and the exceptions folder when missing, and returns the path it wrote.
  3. `write(spec_dir, "boundary", r)` writes `# No new boundary\n\n<r>\n`, and `write(spec_dir, "brainstorm.ui-design", r)` writes ``# `brainstorm.ui-design` does not apply\n\n<r>\n`` (research R2).
  4. A second `write` with the same name replaces the reason.
  5. `boundary` returns the reason or `None`, and `passes` returns `{"<step>.<pass>": reason}` and never the boundary exception.
  6. `boundary` and `passes` return `None` and `{}` on a missing folder, without raising.
- [X] T003 Create `wfctl/_design_exceptions.py` with `BOUNDARY`, `folder`, `path`, `write`, `boundary`, and `passes`, writing through `write_atomic`. The title for each exception is chosen inside `write`, so the header format and the parser that strips it are in one file. Verify with `uv run pytest -q tests/test_design_exceptions.py`
- [X] T004 Add `_paths.feature_dir(branch, repo_root)` to `wfctl/_paths.py`. It returns `resolve_spec_dir(branch, repo_root)` when that finds a folder, and `spec_root(repo_root) / branch` otherwise. Move `feature_paths_cmd`'s inline computation in `wfctl/cli.py` onto it (research R1). Verify with the existing `feature-paths` tests, `uv run pytest -q tests/test_paths.py -k feature`
- [X] T005 Validate the foundation with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: The module and the helper exist, and nothing calls the module yet.

---

## Phase 3: User Story 1 - Record a boundary exception without touching the architecture folder (Priority: P1) 🎯 MVP

**Goal**: `wfctl arch none` writes `exceptions/boundary.md` in the spec folder, and the brainstorm gate counts it.

**Independent Test**: On a branch with `design.md` and no record, run `arch none` with a reason. `wfctl status` shows `brainstorm.architecture` done, the exception is in the spec folder, and `git status` shows nothing new under `docs/architecture`.

**Verification**:

- Automated: `tests/test_pipeline_commands.py`, `tests/test_end_reports_observations.py`, and `tests/test_design_gate_drawing.py` unchanged
- Manual: `quickstart.md` §1 and §4
- Evidence: the success line from `contracts/cli.md`, and an empty `git status --short docs/architecture`

### Tests for User Story 1 ⚠️

> Write these tests first, and check that they fail before implementing.

- [X] T006 [US1] Rewrite the `arch none` tests in `tests/test_pipeline_commands.py` (lines 364 - 400 and 512 - 553) to assert on `<spec folder>/exceptions/boundary.md` and the new success line, "Put the reason in the PR body." Drop the assertions on `declarations/` and on the old not-in-the-diff refusal (research R8 item 3). Rewrite the docstring at line 341, which explains its test by `step-claims/`
- [X] T007 [US1] Add scenario 1.2 to `tests/test_pipeline_commands.py`: `arch none` on a branch with no spec folder creates the folder and the exception, and brainstorm is still the current step. Also pin that brainstorm's state changes from `pending` to `in_progress`, since brainstorm now rolls up behind the `design-doc` pass (research R8 item 10.1)
- [X] T008 [US1] Add scenario 1.3 to `tests/test_pipeline_commands.py`: a second `arch none` replaces the first reason (research R8 item 10.2)
- [X] T009 [US1] Add scenario 1.4 to `tests/test_pipeline_commands.py` if the existing refusal tests don't already cover it: an empty reason and a `<why>` placeholder both refuse, and nothing is written in the spec folder
- [X] T010 [US1] Add the gate test for the exception-before-git order to `tests/test_pipeline_commands.py`: a branch with `design.md`, a boundary exception, and git unable to answer reads `brainstorm.architecture` as answered. Today the same branch with a declaration reads `inconclusive`, which also releases it, so the test pins the order (research R8 item 9.1)
- [X] T011 [P] [US1] Add a test to `tests/test_end_reports_observations.py`: with a boundary exception and no record, `wfctl end` writes `**Boundary**: answered`. With no exception and git unable to tell, it still writes `unknown` (contracts/cli.md §wfctl end)

### Implementation for User Story 1

- [X] T012 [US1] In `wfctl/cli.py`, change `arch_none_cmd` to keep both reason checks, then call `_design_exceptions.write(feature_dir(branch, repo_root), BOUNDARY, reason)` and print the two success lines. Remove the `touched_on_this_branch` check and its warning (research R5). Verify with T006 - T009
- [X] T013 [US1] In `wfctl/_evidence.py`, change `_architecture_answered` to return `None` after its `spec.md` escape when `_design_exceptions.boundary(spec_dir)` is set, before the git call (research R3). Verify with T010 and `tests/test_design_gate_drawing.py` unchanged (SC-003)
- [X] T014 [US1] In `wfctl/cli.py`, change `_observe` to take `spec_dir` from `end_cmd` and read "answered" when `_design_exceptions.boundary(spec_dir)` is set. Otherwise it maps `touched_on_this_branch` as it does today (research R6, FR-014). Verify with T011
- [X] T015 [US1] Rewrite `arch_none_cmd`'s docstring in `wfctl/cli.py` (about lines 2013 - 2025), which Typer prints as `--help`. It says the exception goes in the spec folder and the reason goes in the PR body (research R9 item 8). Load `writing-style` first. Verify with `uv run wfctl arch none --help`
- [x] T016 [US1] Validate User Story 1 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: `arch none` writes to the spec folder, and the gate and the session summary read it there.

---

## Phase 4: User Story 2 - Record pass exceptions beside the boundary exception (Priority: P2)

**Goal**: `wfctl step none` writes `exceptions/<step>.<pass>.md`, and the pipeline reads each one as a skipped pass.

**Independent Test**: Run `step none` on two passes and `arch none` once. The pipeline reports exactly those two passes as skipped, with their reasons, and never `boundary`.

**Verification**:

- Automated: `tests/test_step_none.py`, `tests/test_warnings_after_gate.py`, `tests/test_paths.py`
- Manual: `quickstart.md` §2
- Evidence: three files under `exceptions/`, and `wfctl status --json` listing two skipped passes

### Tests for User Story 2 ⚠️

- [X] T017 [US2] In `tests/test_step_none.py`, replace `test_a_claim_no_reviewer_can_see_is_not_left_on_disk` and `test_a_refused_claim_does_not_settle_the_pass` with one test: an exception lands in the spec folder when the arch root is outside the working tree, and the command prints "Put the reason in the PR body." (FR-005). Move the path assertions to the spec folder (research R8 item 2)
- [X] T018 [US2] Add scenario 2.2 to `tests/test_step_none.py`: `step none` on two passes and `arch none` once, then `wfctl status --json` reports exactly the two passes as claimed and never `boundary`. This is also the verification `design-exceptions-module.md` names (research R8 item 10.3)
- [X] T019 [US2] Add scenario 2.1 to `tests/test_step_none.py` if not already covered: two declared passes each get an exception, both read skipped, and neither replaces the other
- [X] T020 [P] [US2] In `tests/test_warnings_after_gate.py` (about line 271), write the exception through `_design_exceptions.write` rather than by hand under the arch root, so no test builds an exception path itself (FR-009, research R8 item 8)
- [X] T021 [P] [US2] In `tests/test_paths.py`, drop the `STEP_CLAIMS_DIR` import at line 12. Replace `test_non_record_subtrees_names_step_claims` (about line 1005) with a test that `DECLARATIONS_DIR` is in `non_record_subtrees`, keeping its reason: a fourth reader of the arch root inherits the exclusion from one place (research R8 item 8)
- [X] T022 [P] [US2] Rewrite the docstrings at `tests/test_pipeline_state_names.py:318 - 324` and `tests/test_declared.py:90 - 91` for `exceptions/` (research R8 item 8). Also rewrite the docstring at `tests/test_skill_cross_references.py:204`, which names `declarations/<branch>.md` (research R8 item 7), and the docstring of the test at `tests/test_arch_records.py:476`, which says `arch none` files its declaration under the arch root. That test's assertion stays (research R8 item 4)
- [X] T023 [US2] Add the gate test for SC-003's first change to `tests/test_pipeline_commands.py`, failing until T027: a branch with `design.md` and only an old declaration under `declarations/` reads `brainstorm.architecture` unanswered (scenario 4.2, research R8 item 9.2)

### Implementation for User Story 2

- [X] T024 [US2] In `wfctl/cli.py`, change `step_none_cmd` to keep its reason checks and pass resolution, then call `_design_exceptions.write(feature_dir(...), qualified_name, reason)` and print the two success lines. Remove the unlink and `_refuse_unseen` block. `_refuse_unseen` stays, since `step sign-off` still calls it (research R5). Verify with T017 - T019
- [X] T025 [US2] In `wfctl/_pipeline.py`, delete `_step_claims`. At about line 393, pass `_design_exceptions.passes(spec_dir)` when `spec_dir` is set and `{}` otherwise (research R7). Verify with T018 and T020
- [X] T026 [US2] In `wfctl/_contract.py`, change the `nested` fixture to write its exception through `_design_exceptions.write`, and drop its `STEP_CLAIMS_DIR` import (research R8 item 6). Verify with `uv run pytest -q` on the contract tests
- [X] T027 [US2] In `wfctl/_paths.py`, add `DECLARATIONS_DIR = "declarations"` to `non_record_subtrees`, and remove `STEP_CLAIMS_DIR` from the list and the code (research R4). Four other files import it today, `cli.py`, `_pipeline.py`, `_contract.py`, and `tests/test_warnings_after_gate.py`, so this lands after T020, T024, T025, and T026. Verify with T021, T023, and `grep -rn STEP_CLAIMS wfctl/ tests/` printing nothing
- [X] T028 [P] [US2] Rewrite the comments that name the old folders, at `wfctl/cli.py` (about line 7507) and `wfctl/_declared.py` (about line 139) (research R9 item 7). Load `writing-style` first. Verify with `grep -n "step-claims\|declarations/" wfctl/cli.py wfctl/_declared.py`
- [X] T029 [US2] Rewrite `step_none_cmd`'s docstring in `wfctl/cli.py` (about lines 2124 - 2130), which Typer prints as `--help`. It says the exception goes in the spec folder and the reason goes in the PR body (research R9 item 8). Load `writing-style` first. Verify with `uv run wfctl step none --help`
- [x] T030 [US2] Validate User Story 2 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: Both commands write to the spec folder, and nothing in wfctl's code reads `step-claims/`.

---

## Phase 5: User Story 5 - A wrong boundary answer doesn't reach the reviewer (Priority: P2)

**Goal**: `check-body` reports an exception whose reason isn't in the PR body, and the worktree guard holds a PR whose record contradicts its own "no new boundary" or isn't accepted.

**Independent Test**: On a branch with a boundary exception, run `check-body` against a body without the reason. Then add a proposed level-2 record, commit it, and run `gh pr create` through the guard.

**Verification**:

- Automated: `tests/test_shape.py`, `tests/test_record_gate.py`, `tests/test_review_gate.py` and `tests/test_worktree_guard.py` unchanged
- Manual: none beyond the automated tests
- Evidence: the `check-body` and guard lines in `contracts/cli.md`

### Tests for User Story 5 ⚠️

- [X] T031 [US5] Add scenarios 5.1 and 5.2 to `tests/test_shape.py`, beside the other `check-body` CLI tests (about line 289). A body without the boundary exception's reason gets one finding, in a repo that doesn't list "Moves a boundary?". A body that has the pass exception's reason rewrapped across two lines gets none. Assert the `⚠` marker `check-body` already prints, not the `✗` shown in `contracts/cli.md`. `_exception_findings` returns bare lines, as `_section_findings` does (plan review PR-021)
- [X] T032 [US5] Add the sub-issue test to `tests/test_shape.py`: on a sub-issue that reads the epic's folder, with a level-2 record on the branch, `check-body` reports nothing for the epic's boundary exception. Without the record, it reports the missing reason (FR-015, research R12)
- [X] T033 [US5] Write `tests/test_record_gate.py`, failing, for scenarios 5.3 - 5.6:
  1. 5.3: the branch's own spec folder holds a boundary exception and the branch touches a level-2 record. `gh pr create` is refused, and the refusal names the record and prints the `rm` command for the exception.
  2. 5.4: a sub-issue inherits the epic's boundary exception and touches an accepted level-2 record. `gh pr create` isn't refused for the exception.
  3. 5.5: a branch touches a `proposed` level-2 record. Both `gh pr create` and `gh pr merge` are refused, naming the record.
  4. 5.6: run from the `main` checkout, `gh pr merge` reads the record's status at the PR's head commit, not from the `main` working tree.
  5. When git can't list the records or show one, the guard refuses (FR-018).
- [X] T034 [US5] Add the three branches the existing guard tests don't reach to `tests/test_record_gate.py` (plan Order of work step 8):
  1. A branch that writes only a level-3 record under `design/` passes both checks, with and without a boundary exception.
  2. A branch that deletes a file under the arch root, at the top level and under a subdirectory, passes.
  3. A branch whose trunk gains a proposed record after the branch point passes, since the record isn't the branch's.
  4. On each fixture branch, the guard's list matches the slugs `_evidence._branch_records` returns.

### Implementation for User Story 5

- [X] T035 [US5] In `wfctl/cli.py`, add `_exception_findings(body)` and compose it in `check_body_cmd` beside `_section_findings`. It resolves the spec folder with `resolve_spec_dir`, reads `_design_exceptions.boundary` and `_design_exceptions.passes`, and returns one bare line per reason missing from the body after collapsing whitespace in both. It skips the boundary exception when the folder isn't named after the branch and `_evidence._branch_records` returns a record. Outside a wfctl repo, or with no spec folder, it returns nothing (research R12). Verify with T031 and T032
- [X] T036 [US5] Move `_RULED_ON` from `wfctl/_evidence.py` to `wfctl/_arch.py` as `RULED_ON`, and import it in `_evidence.py` from there. Verify with `uv run pytest -q` on the "architecture accepted" fact tests
- [X] T037 [US5] Create `wfctl/_record_gate.py` with `refusal(session, branch, head, trunk)`. It lists the level-2 records with `git diff --name-only --diff-filter=d <trunk>...<head> -- <arch>`, keeping a path only when its parent is the arch root and it ends in `.md`. It reads each status from `git show <head>:<path>` with `_arch`'s frontmatter parser. It refuses first when the branch's own spec folder (`resolve_spec_dir(branch, root) == spec_root(root) / branch`) holds a boundary exception, read with `_design_exceptions.boundary(spec_dir)`, and the list isn't empty (R13). That refusal's `rm` line prints `_design_exceptions.path(spec_dir, BOUNDARY)`, so the guard builds no exception path itself. It refuses next when a listed status is outside `RULED_ON` (R14). It shares `_review_gate`'s `TIMEOUT`, refuses on any error, and imports neither `typer` nor `_evidence`. It doesn't import `rich` directly, though `rich` still loads through `resolve_spec_dir`. An arch root outside the working tree passes both checks. Verify with T033 and T034
- [X] T038 [US5] In `wfctl/_review_gate.py`, have `_judge` keep the value `_paths.trunk_branch` returns before stripping `origin/`, and call `_record_gate.refusal(session, branch, head, trunk)` once the review check finds nothing pending, returning its refusal (plan caller 7). Verify with T033 - T034, and with `tests/test_review_gate.py` and `tests/test_worktree_guard.py` green unchanged
- [X] T039 [US5] Add the pause step to `wfctl/agents/skills/architecture-decisions/SKILL.md` (research R15). When the agent writes a record on a branch with a boundary exception, own or inherited, it reads `auto_approve` from `wfctl status --json`. When `auto_approve` is false, it stops after writing the record as `proposed` and waits for the user to accept or reject it. When it's true, it finishes the `Considered` section and carries on. The skill finds the exception by asking `wfctl feature-paths` for `FEATURE_DIR` and checking for `exceptions/boundary.md` there, so this skill joins the texts in research R9 that name the folder (plan review PR-022). Load `writing-style` first. Verify by reading the installed text after T058
- [X] T040 [US5] Add a bullet to Step 5 of `wfctl/agents/skills/opening-a-change/SKILL.md` for a `check-body` mismatch. The agent works out which copy is wrong from the code, the plan, and the domain model. In an attended session it recommends which copy to fix and the user decides. In an unattended run it fixes the wrong copy and carries on (research R12). Add two bullets under its "When the guard refuses" section for the guard's new refusals. When a record contradicts the branch's own "no new boundary", the agent runs the printed `rm` and changes the PR body's answer to yes. When a record isn't accepted, the agent stops and asks the user to accept or reject it, and doesn't run `wfctl arch accept` itself (research R13, R14). Load `writing-style` first. Verify by reading the installed text after T058
- [x] T041 [US5] Validate User Story 5 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: A PR body missing an exception's reason gets a finding, and the guard holds a PR with a contradicting or unaccepted record.

---

## Phase 6: User Story 3 - The reviewer reads exceptions in the PR body (Priority: P3)

**Goal**: This repo requires a "Moves a boundary?" section in every PR body, and wfctl's code never names it.

**Independent Test**: In this repo, run `check-body` against a body with no "Moves a boundary?" section, then against one that answers it with a reason.

**Verification**:

- Automated: `uv run wfctl check config`
- Manual: `quickstart.md` §5
- Evidence: `check config` green, and `check-body` reporting the section missing

### Implementation for User Story 3

- [X] T042 [US3] Add `## Moves a boundary?` and its comment to `.github/pull_request_template.md`, right after "Needs a spec?", with the text in `contracts/cli.md §PR template section`. Load `writing-style` first. Verify with T044
- [X] T043 [US3] Add "Moves a boundary?" to `change_sections` in `wfctl.json`. Verify with T044
- [X] T044 [US3] Run `uv run wfctl check config` and check it's green, which confirms the template carries the heading (scenario 3.4). Then run `uv run wfctl check-body` on a body without the section and on one answering "No. Copy fix in one help string; nothing moves." Expect a finding for the first and none for the section on the second (scenarios 3.1 and 3.2)
- [X] T045 [US3] Add a bullet to Step 4 of `wfctl/agents/skills/opening-a-change/SKILL.md` telling the agent to copy the branch's design exceptions from the spec folder into the PR body. It names no section, since the skill must never carry a section list (FR-013, research R9 item 4). Load `writing-style` first. Verify by reading the installed text after T058
- [X] T046 [US3] Confirm FR-011 with `grep -rn "Moves a boundary" wfctl/`, which prints nothing
- [x] T047 [US3] Validate User Story 3 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: This repo's PRs answer "Moves a boundary?", and `check-body` enforces it.

---

## Phase 7: User Story 4 - The architecture folder holds no exceptions (Priority: P4)

**Goal**: The 15 declarations are deleted, the 5 step claims move to their branches' spec folders, and an old declaration no longer releases the gate.

**Independent Test**: List the architecture folder. Then, on a scratch branch with `design.md`, add a file under `declarations/` and check that `brainstorm.architecture` still reads unanswered.

**Verification**:

- Automated: the gate test from T023, and the assertion at `tests/test_arch_records.py:476` unchanged
- Manual: `quickstart.md` §3
- Evidence: no `declarations/` or `step-claims/` content under `docs/architecture`

### Tests for User Story 4

Scenario 4.2's gate test is T023, in Phase 4, since it has to fail before T027. These pin behavior that already holds, so they pass on their first run.

- [X] T048 [US4] Run `uv run pytest -q tests/test_pipeline_commands.py -k declaration` and check T023 still passes after the files under `declarations/` are deleted in T050
- [X] T049 [P] [US4] Add the two epic sub-issue regression tests to `tests/test_design_exceptions.py` (research R8 item 11). A sub-issue branch with no folder of its own, listed in the epic's `delivery.md`, reads the epic's boundary and pass exceptions. The same sub-issue with its own spec folder reads none

### Implementation for User Story 4

- [X] T050 [US4] Delete the 15 files under `docs/architecture/declarations/` with `git rm`. Verify with `ls docs/architecture/declarations` failing
- [X] T051 [US4] Move the 5 step claims under `docs/architecture/step-claims/` into `exceptions/` in their branches' spec folders, rewriting each through `_design_exceptions.write` so the old header naming the branch is dropped (research R10). Then `git rm -r docs/architecture/step-claims`. Verify by reading each new file, and with `grep -rn "step-claims\|STEP_CLAIMS" wfctl/ tests/` printing nothing
- [X] T052 [US4] Run the level-3 record's check, `grep -rn '"exceptions"\|boundary\.md' wfctl/cli.py wfctl/_pipeline.py wfctl/_evidence.py wfctl/_record_gate.py`. A hit passes when it's a call into `_design_exceptions`, or sits in a docstring or comment. A hit that builds a path or parses a file is a finding to fix before moving on (plan review PR-015)
- [x] T053 [US4] Ask the user before the first push, then store each of the 5 spec folders with `WFCTL_BRANCH=<branch> uv run wfctl store specs`: `359-push-specs-to-trunk`, `40-save-uncommitted-on-remove`, `571-release-automation`, `264-sentinel-goes-stale`, and `293-mirror-below-recorded-dir`. The last two reach `specs-trunk` for the first time. Each run logs its push in that branch's state directory, not this one's, so record the pushes on this branch afterwards with `uv run wfctl report-action push` (plan review PR-014). Verify with `git log origin/specs-trunk --oneline -5`
- [x] T054 [US4] Validate User Story 4 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: The architecture folder holds no design exceptions (SC-001).

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: The text that still names the old location, and the final checks.

- [X] T055 [P] Update `wfctl/agents/skills/design-levels/SKILL.md` (about line 204), `wfctl/agents/skills/model-the-domain/SKILL.md` (about line 203), `wfctl/agents/skills/writing-a-scan-file/SKILL.md` (about line 40), and `wfctl/agents/skills/architecture-design/SKILL.md` (lines 69 - 71) so each names the spec folder and says the reviewer reads the PR body (research R9 items 1, 2, 3, 9). Load `writing-style` first. Verify with T058
- [X] T056 [P] Update `AGENTS.md` at about line 174 (the arch root exclusions), lines 287 - 291 (the `step none` paragraph), and the Safety section at about line 430, which says the review check is the one refusal wfctl makes. The guard now also refuses for a contradicting or unaccepted record. Check `README.md:107`, leaving it alone if it names no path (research R9 items 5 and 6). Load `writing-style` first. Verify by reading both files back
- [X] T057 Rewrite the two passages left in `docs/architecture/an-absent-artifact-is-claimed-not-inferred.md`: §Decision ("writes a committed sentence into the change under review") and §Owns truth ("a sentence committed to the branch", "that it reached the reviewer"). §Considered was already rewritten in 767a050, so `research.md R9` item 10's third passage is done (plan review PR-029). Load `writing-style` first. Verify with `uv run wfctl arch check docs/architecture/an-absent-artifact-is-claimed-not-inferred.md`
- [X] T058 Run `uv run wfctl install-skills --agent claude`, then read `design-levels` level 2, `opening-a-change` Steps 4 and 5, and the new `architecture-decisions` step in the installed tree. Run `grep -rn "declarations/" .agents .claude` and expect no match (quickstart §6)
- [X] T059 Run the hand checks in `quickstart.md` §1 - §5 on a scratch branch, using `uv run` for every wfctl command
- [X] T060 Update `docs/architecture/design-exceptions-live-with-specs.md` only if implementation changed a fact it states. Verify with `uv run wfctl arch check docs/architecture/design-exceptions-live-with-specs.md`
- [X] T061 Run `uv run wfctl doctor` and check it's green
- [x] T062 Run `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy`, all green
- [x] T063 Run `uv run wfctl verify` and check it records a pass, including the release note check — merge gate
- [ ] T064 After the PR opens, ask the user, then post with `uv run wfctl issue comment 382` a comment saying its short track now reads the boundary exception from the spec folder, not a committed `arch none` file (plan Order of work step 12)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none.
- **Foundational (Phase 2)**: needs Setup. Blocks every story.
- **US1 (Phase 3)**: needs Foundational.
- **US2 (Phase 4)**: needs Foundational. T027 removes `STEP_CLAIMS_DIR`, so T020, T021, T024, T025, and T026 land before it or in the same commit.
- **US5 (Phase 5)**: needs US1, since its tests write a boundary exception through `arch none`. T035 also reads pass exceptions, so it runs after US2.
- **US3 (Phase 6)**: needs Foundational only. T045 and T040 edit the same skill file, so they don't run in parallel.
- **US4 (Phase 7)**: needs US1 and US2. T051 writes through `_design_exceptions.write`.
- **Polish (Phase 8)**: needs every story.

### Within Each Story

- Tests are written and fail before the implementation.
- The module and `feature_dir` come before any command change.
- Each phase ends on its merge gate task.

### Parallel Opportunities

- T011 runs beside T006 - T010, since it's a different test file.
- T020, T021, and T022 touch different test files.
- T028 runs beside T024 - T026.
- T049 runs beside T050 - T052.
- T055 and T056 touch different files.
- US3 (Phase 6) can run beside US5 (Phase 5) once Foundational is done, except for the shared `opening-a-change` file.

## Parallel Example: User Story 2

```bash
# The three test-file edits that don't share a file:
Task: "T020 tests/test_warnings_after_gate.py writes through _design_exceptions.write"
Task: "T021 tests/test_paths.py drops STEP_CLAIMS_DIR, asserts DECLARATIONS_DIR"
Task: "T022 docstrings in tests/test_pipeline_state_names.py and tests/test_declared.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Finish Phase 1 and Phase 2.
2. Finish Phase 3. `arch none` now writes to the spec folder, and the gate reads it.
3. Stop and validate with `quickstart.md` §1 and §4.

### Incremental Delivery

1. US1, then US2: both commands stop writing into the architecture folder.
2. US5: the two copies of the answer are checked against each other and against the records.
3. US3: this repo's PR template carries the reviewer's copy.
4. US4: the old files go, and an old declaration stops counting.
5. Polish: the text, the installed skills, and the final checks.

## Notes

- The open plan review findings PR-020, PR-023, PR-024, and PR-030 change no task. PR-020's renamed-branch case fails open the same way in both checks, and it's rare.
- This PR waits for the user to accept `design-exceptions-live-with-specs.md` and `an-absent-artifact-is-claimed-not-inferred.md` before it opens (research R14).
- Commit after each task or logical group.
