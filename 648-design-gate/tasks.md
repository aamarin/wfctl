# Tasks: Brainstorm holds until the software design question is answered

**Input**: Design documents from the `648-design-gate` feature folder
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Every user story names its tests, and they're written first. The new
tests are numbered as in `plan.md` §Project Structure, so "test 8d" means the
same thing in both files.

**Organization**: One phase per user story, in the spec's priority order. Phase
1 corrects the planning artifacts the last plan review flagged, so the agent
building from them doesn't follow a wrong sentence. The plan review's MINOR
findings (PR-013 to PR-019, PR-023 to PR-028) are folded into the task that
fixes each one, and the task names the finding.

Design records read: 1 listed in `design.md`,
`docs/architecture/design/software-design-none-is-a-claim.md`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an
  incomplete task)
- **[Story]**: the user story the task belongs to (US1 to US5)

---

## Phase 1: Setup (planning artifact corrections)

**Purpose**: Fix the sentences in the planning artifacts that the plan review
found wrong, before any code is written from them. None of these edits
`plan.md`, so the plan review stays current.

- [x] T001 [P] Correct `research.md` §R10 in the feature folder (PR-024, PR-026, PR-028):
      1. Replace "a held architecture check would have no way out" with the true
         reason for the key. `wfctl step none brainstorm.architecture` does
         release the check, but it costs one claim per branch, and a claim
         written under an arch root outside the project is never committed, so
         the PR reviewer never sees it.
      2. Add `test_design_gate_drawing.py`
         `test_a_failing_record_under_an_arch_root_outside_the_repository_is_not_judged`
         (line 584) and `test_pipeline_commands.py`
         `test_an_unreadable_arch_root_advances_the_design_step` to the list of
         affected tests, and say each one needs rewriting, not a flipped
         assertion (T050, T051).
      3. Reword item 3: `test_every_inconclusive_verdict_goes_through_blocks`
         still passes and still finds a reader that never calls `blocks`, and
         test 8d is what checks that `blocks` is asked before the reason is
         chosen.
      Verify by reading the section back against PR-024, PR-026, and PR-028 in
      `plan-review.md`.
- [x] T002 [P] Correct `research.md` §R9 in the feature folder (PR-014): add
      `tests/test_pipeline_state_names.py`
      `test_a_written_record_with_no_design_doc_leaves_exactly_one_pass_outstanding`,
      which stages no `design.md`, and say its setup gains a claim on
      `brainstorm.software-design` so it still proves `design-doc` is reported
      when it's the last thing missing (T020). Verify by reading R9 back.
- [x] T003 [P] Update `spec.md` FR-006a, User Story 5's Independent Test, and
      its acceptance 3 in the feature folder to say the turned-off checks read
      `skipped` (PR-023). Applied by `/speckit.analyze`. Verified:
      `grep -n "read done" spec.md` matches only FR-002.
- [x] T004 [P] Fix `quickstart.md` in the feature folder (PR-018, PR-027):
      1. Step 6 gives the claim's path in the `rm`:
         `rm docs/architecture/step-claims/1-scratch/brainstorm.software-design.md`.
      2. Step 7 reads the skills from the worktree's absolute path,
         `/Users/andremarin/Development/wfctl/wt/648-design-gate/.claude/skills/`,
         since nothing is installed in the scratch repository.
      3. A new step 8 for User Story 5. It sets `WFCTL_ARCH_DIR` to a
         directory outside the scratch repository, removes `wfctl.json` if
         present, runs `$WFCTL check config` and expects exit 1 with the
         outside-the-project finding, runs `$WFCTL status` and expects
         brainstorm held with the git reason and the remedy naming `trunk` and
         `design_record_checks`. It then writes
         `{ "design_record_checks": "off" }` to `wfctl.json` and expects
         `$WFCTL status --all` to show both checks turned off.
      Verify by checking the claim path against `_paths.STEP_CLAIMS_DIR` and
      `step_none_cmd` in `wfctl/`.
- [x] T005 [P] Correct the Verification section of
      `docs/architecture/design/software-design-none-is-a-claim.md`: the
      remedy prints under `next:` in `wfctl status`, not `how:` (PR-019).
      `how:` is where `next-step.md` carries it. The record is still proposed,
      so this is an edit to this branch's own record. Verify with
      `uv run wfctl arch check docs/architecture/design/software-design-none-is-a-claim.md`
      after committing.

**Checkpoint**: The planning artifacts agree with `plan.md` and with each
other.

---

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: The shared readers and constants every story uses.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T006 Move `arch_location(root, repo_root)` from `wfctl/_pipeline.py` to
      `wfctl/_paths.py`, unchanged and with its docstring, and import it back
      into `_pipeline` so `_pipeline.arch_location` keeps working (plan
      §`_paths.py` item 1, research R4). Verify with
      `uv run pytest -q tests/ -k arch_location` and `uv run mypy`.
- [x] T007 Add `DESIGN_RECORD_CHECKS_KEY` and
      `design_record_checks(repo_root) -> tuple[bool, list[str]]` to
      `wfctl/_paths.py`, beside `TRUNK_KEY` and shaped like `declared_trunk`.
      A missing key or a missing `wfctl.json` is on, `"on"` and `"off"` are the
      only valid values, and any other value is a problem and reads as on (plan
      §`_paths.py` item 2). Verify with T009.
- [x] T008 Add `design_record_checks_problems(repo_root)` to `wfctl/_paths.py`.
      It returns the value problems plus the outside-the-project problem when
      the arch root isn't in the tree and the setting isn't `"off"`, with the
      exact text in `contracts/cli.md` §`wfctl check config` (plan §`_paths.py`
      item 3). Verify with T009.
- [x] T009 Write unit tests for T007 and T008 in
      `tests/test_software_design_pass.py`: missing file, missing key, `"on"`,
      `"off"`, a typo that reads as on with one problem, and the outside-root
      problem with the setting on and absent with it off. Verify with
      `uv run pytest -q tests/test_software_design_pass.py`.
- [x] T010 Add `SOFTWARE_DESIGN_REASON`, `SOFTWARE_DESIGN_HELP`,
      `GIT_UNANSWERED_REASON`, `GIT_UNANSWERED_HELP`, and `CHECKS_OFF_REASON`
      to `wfctl/_evidence.py` beside `DESIGN_BLOCK_REASON`, each with a comment
      in the style of its neighbours (plan §`_evidence.py` items 1 to 4). The
      two help texts match `contracts/cli.md` line for line. Verify with
      `uv run ruff check wfctl/` and the remedy assertions in T014 and T040.
- [x] T011 Validate Phase 2 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`,
      and `uv run mypy` — merge gate.

**Checkpoint**: The readers and constants exist, and nothing reads them yet, so
the suite is still green.

---

## Phase 3: User Story 1 - A branch that skipped software design is held (Priority: P1) 🎯 MVP

**Goal**: A branch with `design.md` and an architecture answer, but no software
design answer, is held at brainstorm on a new `software-design` row, with both
answers printed.

**Independent Test**: On such a branch in a repository with a `main` trunk,
`wfctl status` shows brainstorm current and the `software-design` row held, with
the remedy from `contracts/cli.md` under `next:`.

**Verification**:

- Automated: tests 1, 4, 9, 10, and 12 in `tests/test_software_design_pass.py`;
  `tests/test_cli_status.py`; `tests/test_declared.py`;
  `tests/test_pipeline_payload_snapshot.py`; the full suite.
- Manual: `quickstart.md` steps 1 to 3.
- Evidence: the held row and the remedy in `wfctl status`, and
  `"state": "in_progress"` with the pass's reason in `wfctl status --json`.

### Tests for User Story 1 ⚠️

> Write these first and confirm they fail before T016.

- [x] T012 [P] [US1] Test 1 in `tests/test_software_design_pass.py`: held with
      `design.md`, an architecture declaration, and nothing under `design/`.
      Brainstorm is current, the pass is `in_progress`, and the payload carries
      the reason and the remedy with the repo-relative `design/` location. Use
      the git setup `tests/test_design_gate_drawing.py` uses.
- [x] T013 [P] [US1] Test 4 in `tests/test_software_design_pass.py`: a record
      under the arch root outside `design/` releases `architecture` and not
      `software-design`.
- [x] T014 [P] [US1] Test 12 in `tests/test_software_design_pass.py`: under
      `auto_approve`, the held pass writes `auto: false` to `next-step.md`, so
      an autonomous run stops at brainstorm (US1 acceptance 3).
- [x] T015 [P] [US1] Test 10 in `tests/test_software_design_pass.py`: a
      `software-design` pass declared under brainstorm in `wfctl.json` is a
      `check config` finding and is dropped (research R6).

### Implementation for User Story 1

- [x] T016 [US1] Add `brainstorm_software_design(ev)` to `wfctl/_evidence.py`
      after `brainstorm_architecture`, in the order plan §`_evidence.py` item 5
      gives: `spec.md` returns done, the setting off returns
      `Assessment("skipped", display=CHECKS_OFF_REASON)`, then
      `touched_on_this_branch` maps to a verdict, `blocks(verdict,
      "repo-declared")` false returns done, and only then the verdict picks the
      reason and remedy. The docstring says why it mirrors
      `_architecture_answered`, why it builds its own remedy, and why its source
      is `repo-declared`. Verify with T012 and T013.
- [x] T017 [US1] Register `SubStep("software-design", "/speckit.brainstorm",
      _AUTOMATIC, _evidence.brainstorm_software_design)` between `architecture`
      and `design-doc` in `wfctl/_pipeline.py`, and extend the comment above the
      passes to say why it sits there (plan §`_pipeline.py` item 2, research
      R1). Verify with T012, T014, and T015.
- [x] T018 [US1] Size the pass column in `status_cmd` in `wfctl/cli.py`:
      compute `pass_width = 2 + longest + 2` from every pass name in the
      payload, hidden ones included, use it in place of `.ljust(16)`, and
      rewrite the comment above it to say why the width is computed (plan
      §`cli.py, status_cmd`, research R7). Verify with T019.
- [x] T019 [US1] Test 9 in `tests/test_software_design_pass.py` (PR-017): every
      pass glyph has at least two spaces before it with `plan-walkthrough` and
      `software-design` shown, and a second case declares a pass whose name is
      longer than 16 characters and asserts its glyph is separated too, so a
      hard-coded `.ljust(20)` fails. Update `tests/test_cli_status.py:56` to the
      new width.
- [x] T020 [US1] Update the existing tests the new pass breaks (research R9,
      PR-014): the pass lists in `tests/test_declared.py:25`, `:388`, and
      `:395`;
      `test_a_written_record_with_no_design_doc_leaves_exactly_one_pass_outstanding`
      in `tests/test_pipeline_state_names.py`, whose setup gains a
      `brainstorm.software-design` claim so it still expects exactly
      `["design-doc"]`; and every test the suite finds that stages `design.md`
      and an architecture answer in a repository with a trunk and expects
      specify to be current, which gets a `design/` record or a claim in its
      setup. Verify with `uv run pytest -q`.
- [x] T021 [US1] Test 15 in `tests/test_pipeline_payload_snapshot.py`: the
      `recorded` repository gains a record under `design/`, so
      `design-with-record` still reads done and
      `test_the_matrix_reaches_both_design_states` keeps its meaning, and a new
      row records a branch held on `software-design`. Regenerate
      `tests/pipeline_payload_snapshot.json` only after the setup change, and
      read the diff to confirm only the expected rows moved.
- [x] T022 [US1] Validate User Story 1 with `uv run pytest -q`,
      `uv run ruff check wfctl/ tests/`, `uv run mypy`, and `quickstart.md`
      steps 1 to 3 — merge gate.

**Checkpoint**: A branch with no software design answer is held, and the suite
is green.

---

## Phase 4: User Story 2 - A design record releases the hold (Priority: P1)

**Goal**: A file under `<arch-root>/design/` that this branch added or changed
releases the pass, and a record already on `main` doesn't.

**Independent Test**: On a held branch, commit one file under
`docs/architecture/design/`, and the row reads `●` with specify current.

**Verification**:

- Automated: tests 2, 3, and 11 in `tests/test_software_design_pass.py`.
- Manual: `quickstart.md` step 4.
- Evidence: `software-design   ●` in `wfctl status`.

### Tests for User Story 2 ⚠️

- [x] T023 [P] [US2] Test 2 in `tests/test_software_design_pass.py`: an
      uncommitted file under `design/` releases the pass.
- [x] T024 [P] [US2] Test 3 in `tests/test_software_design_pass.py`: a
      committed file under `design/` releases the pass.
- [x] T025 [P] [US2] Test 11 in `tests/test_software_design_pass.py`: a design
      record committed to `main` before the branch was cut leaves the pass held
      (US2 acceptance 2).

### Implementation for User Story 2

- [x] T026 [US2] No new code: T016 already reads `design/` through
      `touched_on_this_branch`. Confirm T023 to T025 pass against it, and fix
      T016 if one doesn't. Verify with
      `uv run pytest -q tests/test_software_design_pass.py`.
- [x] T027 [US2] Validate User Story 2 with `uv run pytest -q` and
      `quickstart.md` step 4 — merge gate.

**Checkpoint**: Both a record and the lack of one behave as the spec says.

---

## Phase 5: User Story 3 - A claim releases the hold (Priority: P1)

**Goal**: `wfctl step none brainstorm.software-design --reason "…"` releases the
pass with no `wfctl.json`, and brainstorm's unattended agent can run it and
nothing broader.

**Independent Test**: On a held branch, run the claim. The row is hidden from
`wfctl status`, `--all` shows `claimed: <reason>`, and specify is current.

**Verification**:

- Automated: tests 5 and 6 in `tests/test_software_design_pass.py`;
  `test_brainstorm_allows_the_commands_its_records_need` in
  `tests/test_skill_cross_references.py`.
- Manual: `quickstart.md` steps 5 and 6.
- Evidence: `claimed: no new module` under `wfctl status --all`.

### Tests for User Story 3 ⚠️

- [x] T028 [P] [US3] Test 5 in `tests/test_software_design_pass.py`: the claim
      releases the pass with no `wfctl.json`. The row is hidden, and `--all`
      shows `claimed: <reason>`. A second case has both a claim and a record
      under `design/`, and the claim wins (spec Edge Cases).
- [x] T029 [P] [US3] Test 6 in `tests/test_software_design_pass.py`: a branch
      with `spec.md` isn't held (FR-005, SC-003).
- [x] T030 [US3] Test 14 in `tests/test_skill_cross_references.py`, extending
      `test_brainstorm_allows_the_commands_its_records_need` for both surfaces
      (PR-015). Match two command lines against the grants with `fnmatchcase`,
      as `tests/test_provenance.py` does:
      `wfctl step none brainstorm.software-design --reason x` must match a
      grant, and `wfctl step none plan.plan-review --reason x` must match none.
      That fails `Bash(wfctl step none *)` and `Bash(wfctl*)` as well as
      `Bash(wfctl step none*)`. Keep the existing check that the two
      surfaces' grants are equal.

### Implementation for User Story 3

- [x] T031 [US3] Add `Bash(wfctl step none brainstorm.software-design *)` to
      the `allowed-tools` frontmatter of
      `wfctl/agents/skills/speckit-brainstorm/SKILL.md` and
      `wfctl/agents/commands/speckit.brainstorm.md` (plan §`allowed-tools`).
      Verify with T030.
- [x] T032 [US3] No new code for the claim itself (research R5). Confirm T028
      and T029 pass, and verify with
      `uv run pytest -q tests/test_software_design_pass.py tests/test_step_none.py`.
- [x] T033 [US3] Validate User Story 3 with `uv run pytest -q` and
      `quickstart.md` steps 5 and 6 — merge gate.

**Checkpoint**: Both answers release the hold, and an unattended run can give
the "no" answer.

---

## Phase 6: User Story 4 - The skills ask the question the gate checks (Priority: P2)

**Goal**: `design-levels`, `speckit-brainstorm`, and `software-design-decisions`
lead level 3 with module ownership and pattern choice, and name the claim as the
"no" answer.

**Independent Test**: After `uv run wfctl install-skills --agent claude`, each of
the three installed skills names `wfctl step none brainstorm.software-design`
where it covers a change with no structural choice.

**Verification**:

- Automated: test 13 in `tests/test_skill_cross_references.py`.
- Manual: `uv run wfctl install-skills --prune --yes --agent claude`, then
  `quickstart.md` step 7, and read the three changed passages for sense.
- Evidence: the claim command in each installed skill.

### Tests for User Story 4 ⚠️

- [x] T034 [US4] Test 13 in `tests/test_skill_cross_references.py`, beside
      `test_the_no_boundary_exit_names_its_command`: `design-levels`,
      `speckit-brainstorm`, and `software-design-decisions` each contain
      `wfctl step none brainstorm.software-design` (SC-004).

### Implementation for User Story 4

Load the `writing-style` skill before editing any skill text.

- [x] T035 [P] [US4] Edit `wfctl/agents/skills/design-levels/SKILL.md` as plan
      §`design-levels` gives it: the level-3 Form cell (line 39), the level-3
      gate's claim block (lines 233 - 239), the level-3 row of where each
      answer is written (line 88), the Where the levels land bullet (line 410),
      and the Verification item (line 487). Verify with T034.
- [x] T036 [P] [US4] Edit `wfctl/agents/skills/speckit-brainstorm/SKILL.md` as
      plan §`speckit-brainstorm` items 1 to 3 give it: the re-entry paragraph,
      the "answered with no record" sentence, and the auto-approve sentence.
      State that the grant limits the command line the agent may run, and that
      the PR review of the committed claim is the control, since the skill also
      grants `Write` with no path limit (PR-016). Verify with T034.
- [x] T037 [P] [US4] Edit `wfctl/agents/skills/software-design-decisions/SKILL.md`
      "Not for" as plan §`software-design-decisions` gives it. Verify with T034.
- [x] T038 [US4] Validate User Story 4 with `uv run pytest -q`,
      `uv run wfctl install-skills --prune --yes --agent claude`,
      `uv run wfctl doctor`, and `quickstart.md` step 7 — merge gate.

**Checkpoint**: The skills ask for a structural choice and name the claim.

---

## Phase 7: User Story 5 - A repo where git can't answer is held until it says why (Priority: P2)

**Goal**: Both brainstorm checks hold when git can't answer, with a remedy
naming `trunk` and `design_record_checks`. `"off"` turns both off, and `check
config` reports a bad value or an arch root outside the project.

**Independent Test**: In a repository whose arch root is outside the project,
`wfctl status` holds brainstorm with the git reason and remedy. With
`design_record_checks` set to `"off"`, `wfctl status --all` shows both checks
turned off.

**Verification**:

- Automated: tests 7, 8, 8a, 8b, 8c, and 8d in
  `tests/test_software_design_pass.py`; the rewritten tests in
  `tests/test_design_gate_drawing.py`, `tests/test_pipeline_state_names.py`, and
  `tests/test_pipeline_commands.py`;
  `test_every_inconclusive_verdict_goes_through_blocks`.
- Manual: `quickstart.md` step 8 (T004), and `uv run wfctl check config` in
  this repository.
- Evidence: the git reason and remedy in `wfctl status`; exit 1 from
  `check config` in a repo with no `wfctl.json` and an outside arch root.

### Tests for User Story 5 ⚠️

- [x] T039 [P] [US5] Test 7 in `tests/test_software_design_pass.py`: held with
      no trunk, with `GIT_UNANSWERED_REASON` and a remedy naming `trunk` and
      `design_record_checks` (FR-006). A second case runs in a directory that
      isn't a git repository, where the git command fails, and expects the same
      hold. A third case names the base branch with `trunk` in `wfctl.json`, and
      both checks then compare against it: held with nothing under the arch
      root, and released by a record (US5 acceptance 2).
- [x] T040 [P] [US5] Test 8 in `tests/test_software_design_pass.py`: held with
      the arch root outside the tree, with the same reason and remedy.
- [x] T041 [P] [US5] Test 8a in `tests/test_software_design_pass.py`: with
      `"off"`, both checks read `skipped` with `CHECKS_OFF_REASON` as their
      display, in a repo with no trunk and in one with an outside arch root.
      The payload's `warnings` list is empty and `status` prints no warning
      line. Under `--all`, both rows show the text.
- [x] T042 [P] [US5] Test 8b in `tests/test_software_design_pass.py`: a value
      other than `"on"` or `"off"` is a `check config` finding and leaves both
      checks on. An outside arch root with the setting on is a finding both
      with a `wfctl.json` and with none, where `check config` exits 1 and
      doesn't print `no configuration to check`.
- [x] T043 [P] [US5] Test 8c in `tests/test_software_design_pass.py`: the
      architecture check holds with no trunk, where it used to let the branch
      through.
- [x] T044 [P] [US5] Test 8d in `tests/test_software_design_pass.py`: with
      `_evidence.blocks` patched to return false, both checks read done when
      git can't answer, so each reader lets `blocks` decide what git's silence
      means.
- [x] T045 [P] [US5] Test the two `brainstorm` step readings PR-025 found, in
      `tests/test_software_design_pass.py`: with no `design.md` and git unable
      to answer, brainstorm reads `pending`; with the checks off and nothing
      on the branch, brainstorm reads `in_progress` on `design-doc`, as an
      out-of-tree repo does today.

### Implementation for User Story 5

- [x] T046 [US5] Change `_architecture_answered` in `wfctl/_evidence.py` (plan
      item 6.1 and 6.2): after the `spec.md` escape, return `None` when the
      setting is off; pass `"repo-declared"` to `blocks`; return `None` when
      `blocks` is false; and only then pick `GIT_UNANSWERED_REASON` or
      `DESIGN_BLOCK_REASON` from the verdict. Rewrite the comment at the
      `blocks` call to say why this check is an exception. Verify with T039,
      T043, and T044.
- [x] T047 [US5] Change `brainstorm_architecture` in `wfctl/_evidence.py`
      (plan item 6.3, PR-025): check the setting first, before
      `_architecture_answered` and `_judge_drawings`, and return
      `Assessment("skipped", display=CHECKS_OFF_REASON)`, so no git read runs
      with the checks off, including the drawing check past specify. Attach
      `GIT_UNANSWERED_HELP` as the remedy when the reason is
      `GIT_UNANSWERED_REASON`. Verify with T040 and T041.
- [x] T048 [US5] Rewrite the comments that argue the old let-through (plan item
      6.4, PR-026): the "ambient evidence proceeds" paragraph of the `blocks`
      docstring, and the `DRAWINGS_UNCHECKED` comment at
      `wfctl/_evidence.py:161-167`. Each says the two brainstorm checks are now
      `repo-declared` and why, and `decompose` is the remaining ambient caller.
      Update `brainstorm`'s docstring for the two readings in T045 (PR-025).
      Verify by reading the comments against
      `docs/architecture/promised-evidence-blocks-on-silence.md`.
- [x] T049 [US5] Change `check_config_cmd` in `wfctl/cli.py` (plan
      §`check_config_cmd` items 1 to 3): call
      `_paths.design_record_checks_problems` before the early return for a
      missing `wfctl.json`; with no `wfctl.json`, print its problems under
      `✗ wfctl.json:` and exit 1, or print `no configuration to check` when
      there are none; with a `wfctl.json`, add them beside
      `declared_trunk_problems`. Update the docstring's key list. Verify with
      T042.
- [x] T050 [US5] Rewrite the existing tests whose premise is the old
      let-through (research R10 as corrected by T001, PR-026):
      `test_design_gate_drawing.py`
      `test_a_failing_record_under_an_arch_root_outside_the_repository_is_not_judged`,
      `test_with_no_trunk_a_committed_failing_record_finishes_the_step_and_says_so`,
      and `test_with_no_trunk_an_arch_root_outside_the_repository_carries_no_unchecked_line`;
      `test_pipeline_state_names.py` `test_a_step_with_its_artifact_present_is_done`
      and `test_the_architecture_pass_and_the_design_doc_pass_read_independently`.
      Each keeps the rule it proves by giving its setup a trunk, an in-tree
      arch root, or `"off"`, or asserts the hold where the hold is now the
      rule. Rewrite each docstring to match. Verify with `uv run pytest -q`.
- [x] T051 [US5] Rewrite `tests/test_pipeline_commands.py`
      `test_an_unreadable_arch_root_advances_the_design_step` to assert the
      hold and the remedy, and point its "the ambient rule end to end"
      docstring at `decompose`, the remaining ambient caller (PR-026). Verify
      with `uv run pytest -q tests/test_pipeline_commands.py`.
- [x] T052 [US5] Add a "Turning off the design record checks
      (`design_record_checks`)" section to `docs/reference.md` after "Declaring
      your trunk (`trunk`)", as plan §`docs/reference.md` gives it. Load
      `writing-style` first. Verify by reading it against
      `contracts/cli.md` §held because git can't answer.
- [x] T053 [US5] Validate User Story 5 with `uv run pytest -q`,
      `uv run ruff check wfctl/ tests/`, `uv run mypy`,
      `uv run wfctl check config`, and `quickstart.md` step 8 — merge gate.

**Checkpoint**: No branch leaves brainstorm without an answer or a repo-level
setting that says why.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [x] T054 [P] Update every comment and docstring that counts brainstorm's
      passes as two (plan item 7, PR-013): `brainstorm`'s docstring,
      `brainstorm_architecture`'s docstring (both "two built-in passes" and
      "`design.md` is the other pass's business" / "then both passes run"),
      `brainstorm_design_doc`'s docstring, and the `Step` docstring in
      `wfctl/_pipeline.py`; `tests/test_declared.py:21`,
      `tests/test_cli_status.py:44`, and
      `tests/test_pipeline_state_names.py:249`. Verify that
      `grep -rnE "two (built-in )?passes|other (built-in )?pass|both passes" wfctl/ tests/`
      finds none left about brainstorm.
- [x] T055 [P] Update the `wfctl status` example in `README.md` (lines 45 - 47):
      add the `software-design` row as `●` between `architecture` and
      `design-doc`, and widen the pass rows to the new column. Verify against
      `uv run wfctl status` output in a scratch repository.
- [x] T056 [P] Write the release note with
      `uv run towncrier create 648.change.md --content "…"`, using the text in
      plan §`changes/648.change.md`. Load `writing-style` first. Verify with
      `uv run wfctl verify`.
- [x] T057 Run the full definition of done: `uv run pytest -q`,
      `uv run ruff check wfctl/ tests/`, `uv run mypy`, `uv run wfctl verify`,
      `uv run wfctl doctor`, `uv run wfctl check config`, and every step of
      `quickstart.md` — merge gate.

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1** has no dependencies and can run alongside Phase 2.
- **Phase 2** blocks every user story.
- **US1 (Phase 3)** comes first, since it registers the pass every later story
  reads.
- **US2 and US3** depend on US1 and are independent of each other.
- **US4** depends only on Phase 2 for its text, but test 13 and the grant test
  read the same file as T030, so run it after US3.
- **US5** depends on US1, since it changes the reader T016 adds and the
  architecture check beside it. Its test rewrites (T050, T051) depend on T001.
- **Phase 8** depends on every story.

### Within each story

Tests first, and confirm they fail. Then the implementation, then the merge
gate.

### Parallel opportunities

- T001 to T005 are separate files.
- Within each story, every test task marked [P] writes a separate test
  function in the same new file, so they can be drafted together and committed
  as one.
- T035 to T037 are separate skill files.
- T054 to T056 are separate files.

## Parallel Example: User Story 5

```bash
Task: "Test 7 in tests/test_software_design_pass.py"
Task: "Test 8 in tests/test_software_design_pass.py"
Task: "Test 8a in tests/test_software_design_pass.py"
Task: "Test 8d in tests/test_software_design_pass.py"
```

## Implementation Strategy

### MVP first

Phases 1 and 2, then US1. A branch with no software design answer is held,
which is the defect #635 showed. Stop and run `quickstart.md` steps 1 to 3.

### Incremental delivery

1. US1, then US2 and US3, gives both ways out of the hold. Shipping US1 alone
   would hold branches with only a record as the way out.
2. US4 steers the agent toward a structural answer.
3. US5 closes the silent let-through when git can't answer.

The stories share `_evidence.py` and the new test file, so whether they ship as
one PR or several is `/speckit.decompose`'s call.
