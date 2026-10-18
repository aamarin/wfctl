Implementation complete: 2026-10-16

## Tasks at completion

~~~~markdown
# Tasks: release automation

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`,
and `contracts/` in this folder.

**Design records**: `docs/architecture/change-carries-release-note.md` and
`docs/architecture/design/571-towncrier-builds-release-notes.md`, both accepted
on 2026-10-16. No task below departs from either. Where this list says "the
check" it means `.github/scripts/check_release_note.py`, and "the release
script" means `.github/scripts/release.py`.

**Tests**: every story has a verification path. User Stories 1, 2, 4, and 5 are
covered by pytest. User Story 3 changes a CI job that only runs on `main`, so it
is checked locally against a scratch repository and confirmed on the first
release after merge, as the spec's Validation Strategy says.

**Paths**: repository paths are relative to the repository root. Paths under
`contracts/` and the other spec files are in this feature folder, which sits
outside the working tree.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel, because it touches different files and depends
  on no unfinished task.
- **[Story]**: the user story the task belongs to, US1 to US5.

---

## Phase 1: Setup

**Purpose**: bring the branch up to date and add towncrier, which the check and
the release script both read.

- [X] T001 Merge `origin/main` into `571-release-automation` if `main` has moved
      since `52bd76e`, with a merge commit rather than a rebase. Verify with
      `git merge-base --is-ancestor origin/main HEAD` exiting 0.
- [X] T002 Add `towncrier>=26.9,<27` to the `dev` extra in `pyproject.toml`,
      keeping the comment style of the ruff pin, and say why the pin spans a year
      (towncrier uses calendar versions, research 9). Run `uv lock` in the same
      commit. Verify with `uv lock --check` and `uv run towncrier --version`
      printing 26.9 or later.
- [X] T003 Add `[tool.towncrier]` to `pyproject.toml` with `directory =
      "changes"`, `filename = "CHANGELOG.md"`, `issue_format = "#{issue}"`, and
      four `[[tool.towncrier.type]]` tables in this order: `change` "Behaviour
      changes", `addition` "Additions", `fix` "Fixes", `none` "Nothing to
      notice". Add a comment saying the file named by `filename` is never
      written and only selects the markdown template (research 5). Verify by
      loading the table with `tomllib` and seeing the four types in that order,
      and by running `uv run towncrier build --draft --version 0.0.0 --dir
      <scratch folder holding one note>` and seeing its section and no file
      written.
- [X] T004 Validate Phase 1 with `uv run pytest -q`, `uv run ruff check wfctl/
      tests/`, and `uv run mypy wfctl/` — merge gate.

---

## Phase 2: Foundational

**Purpose**: one scratch-repository helper for both new test files, so the check
and the release script are tested against repositories built the same way.

- [X] T005 Add `init_release_repo(path, version)` to `tests/conftest.py`. It runs
      `git init -b main`, since CI sets `init.defaultBranch master` (research
      10), creates a bare repository beside it as `origin`, writes a
      `pyproject.toml` holding `[project].version` and this repository's
      `[tool.towncrier]` table read from the real `pyproject.toml`, commits it,
      and pushes `main`. Its docstring says why the table is copied rather than
      written out: a second copy of the category list is the drift the level 3
      record exists to prevent. Verify with a test in
      `tests/test_release_note_check.py` that the helper's repository has
      `origin/main` and the four categories.
- [X] T006 Validate Phase 2 with `uv run pytest -q tests/test_release_note_check.py`
      — merge gate.

**Checkpoint**: Phases 3 and 4 can now proceed in parallel.

---

## Phase 3: User Story 1 - A change isn't done until it commits its release note (Priority: P1) 🎯 MVP

**Goal**: `wfctl verify` and CI fail a branch that adds no release note for its
own issue, and the message says which file to add.

**Independent Test**: on a branch with no note, `uv run wfctl verify` records a
failure and `uv run wfctl status` shows the definition of done as unmet. Adding
`changes/571.none.md` and running it again records a pass.

**Verification**:

- Automated: `uv run pytest -q tests/test_release_note_check.py`, covering User
  Story 1 scenarios 1 - 6, 8, and 9, and the edge cases for a missing base and an
  unrecognised file name.
- Manual: `uv run wfctl verify` on this branch with and without
  `changes/571.none.md`, and `uv run wfctl check config`.
- Evidence: on this branch's pull request, the `release-note` job's pass line
  names `#571` rather than "this branch" (plan, Risks).

### Tests for User Story 1

> Write these first and confirm they fail before T014.

- [X] T007 [P] [US1] In `tests/test_release_note_check.py`, add an autouse
      fixture that clears `GITHUB_HEAD_REF` and `GITHUB_REF_NAME`, with a
      docstring naming why: GitHub sets both for every step of a pull request
      run, the suite's own included (research 10). Load the check with
      `importlib` from `.github/scripts/check_release_note.py`. Verify by
      running the file and seeing every test collected.
- [X] T008 [P] [US1] Add tests for the note-presence cases to
      `tests/test_release_note_check.py`: no note on `571-release-automation`
      fails and names `changes/571.<category>.md`, the four categories, and the
      `uv run towncrier create` example (scenario 1, FR-007), `changes/571.change.md` passes (scenario 2), a stacked
      `580-child` carrying only `571.change.md` fails and asks for `580`
      (scenario 4), a branch with no issue passes with `+bump-ruff.fix.md`
      (scenario 5) and fails with no note, and `main` passes (scenario 6).
      Verify they fail against an empty script.
- [X] T009 [P] [US1] Add tests for malformed notes to
      `tests/test_release_note_check.py`: `571.feature.md` fails naming
      `feature` (scenario 3), `changes/notes.md` fails as not a note name, a
      note holding "Add your info here" fails as unwritten (scenario 8), and an
      empty or whitespace-only note fails with "the file is empty". One test adds
      two bad files and asserts both findings print before the exit. Verify they
      fail against an empty script.
- [X] T010 [P] [US1] Add tests for the release branch rule to
      `tests/test_release_note_check.py`, with the base at 0.23.0:
      `release/v0.24.0` at 0.24.0 passes, the same branch at 0.23.1 fails naming
      both versions, `release/v0.23.0` at 0.23.0 fails saying the version isn't
      higher than `main`'s (scenario 9), and `0.10.0` counts as higher than
      `0.9.0`. A branch named `release/foo` follows the ordinary rules. Verify
      they fail against an empty script.
- [X] T011 [P] [US1] Add tests for how the check finds its inputs to
      `tests/test_release_note_check.py`: with `GITHUB_HEAD_REF` set on a
      detached `HEAD`, the branch name comes from it; an empty `GITHUB_HEAD_REF`
      counts as unset; with no `origin/main` and no `main`, the check fails with
      "can't find main to compare this branch against"; a branch that merged
      `main` in is judged only on what it added since the merge base; and a
      renamed note counts as added (`--no-renames`). Verify they fail against an
      empty script.

### Implementation for User Story 1

- [X] T012 [US1] Create `.github/scripts/check_release_note.py` using the
      standard library only. Resolve the branch name from `GITHUB_HEAD_REF`,
      then `git rev-parse --abbrev-ref HEAD`, then `GITHUB_REF_NAME`; the base
      from `git merge-base origin/main HEAD`, falling back to `main`; and the
      added notes from `git diff --name-only --no-renames --diff-filter=A <base>
      HEAD -- changes/` (research 3). Read the categories and the notes folder
      from `[tool.towncrier]` with `tomllib` on every run, as
      `contracts/check-release-note.md` §Category list requires. A missing
      `changes/` folder counts as no notes rather than an error, because git
      keeps no empty folder and every release leaves `changes/` empty. Verify
      with T011, plus a case in T008 where `changes/` doesn't exist.
- [X] T013 [US1] In the same file, parse each added note's name into issue,
      category, and optional counter, accepting `<issue>.<category>.md`,
      `<issue>.<category>.<n>.md`, and `+<name>.<category>.md`
      (`data-model.md` §Release note), and fail an empty, whitespace-only, or
      placeholder note. Verify with T009.
- [X] T014 [US1] In the same file, require a note for the issue at the front of
      the branch name, or any note for a branch with no issue, pass `main`, and
      apply the release branch rule, comparing versions as three integers. Read
      the version at `HEAD` and at the base with `git show
      <rev>:pyproject.toml` and `tomllib`. Collect every finding before exiting
      1, and print each message exactly as `contracts/check-release-note.md`
      §Messages gives it. Verify with T008 and T010.
- [X] T015 [US1] Add `["uv", "run", "--frozen", "--extra", "dev", "python",
      ".github/scripts/check_release_note.py"]` to `verify` in `wfctl.json`,
      after the three entries already there (research 2). Verify with `uv run
      wfctl check config`.
- [X] T016 [US1] Commit `changes/571.none.md` saying that how wfctl is released
      changed and nothing an installed wfctl does is different (plan,
      Structure Decision). Whether it should be `571.addition.md` instead is
      still open, and the plan settles it at review: if the release page
      carrying written notes reads as an addition to the reviewer, the file is
      renamed before merge. Verify with
      `uv run wfctl verify` passing, then failing with the file removed, then
      passing again once it is restored.
- [X] T017 [US1] Add the `release-note` job to `.github/workflows/ci.yml` as
      `contracts/tag-job.md` §Contract: the CI `release-note` job gives it: pull
      requests only, `fetch-depth: 0`, and `python3
      .github/scripts/check_release_note.py` with no `uv sync`. Add a comment
      saying its job name is one of the checks the ruleset requires, so a
      rename means editing `.github/rulesets/main.json`. Verify with `uv run
      python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`,
      and on this branch's pull request by the pass line naming `#571`.
- [X] T018 [US1] Validate User Story 1 with `uv run pytest -q`, `uv run ruff
      check wfctl/ tests/`, `uv run mypy wfctl/`, and `uv run wfctl verify` —
      merge gate.

**Checkpoint**: the check runs locally and in CI, and this branch passes it.

---

## Phase 4: User Story 2 - Andre cuts a release with one script (Priority: P2)

**Goal**: one script run proposes the version, lists merges with no note, drafts
the release notes, and opens a release pull request, and stopping at either
prompt changes nothing.

**Independent Test**: on a scratch repository holding a few notes, with a bare
`origin` and the lock, editor, and pull request commands stubbed, run the
script, accept the proposal, and check the pushed branch: the new version, a
matching lock, no files under `changes/`, and a commit body equal to the draft.

**Verification**:

- Automated: `uv run pytest -q tests/test_release_script.py`, covering User
  Story 2 scenarios 1 - 10 and the rollback when `changes/` holds no tracked file
  (PR-019).
- Manual: a dry run on a scratch clone of `main` with notes copied in from
  0.23.0's changes, stopped at the version prompt, after which `git status` and
  `git branch` show nothing changed.
- Evidence: the draft from the dry run lists behaviour changes first and has no
  `none` section.

### Tests for User Story 2

> Write these first and confirm they fail before T026.

- [X] T019 [P] [US2] In `tests/test_release_script.py`, load the script with
      `importlib` and build each scratch repository with `init_release_repo`,
      tagged `v0.23.0`, with merges made as `Merge pull request #<n> from
      aamarin/<branch>` merge commits. Stub the lock command and the pull request
      command to record their arguments, and set the editor to a command that
      leaves or rewrites the draft (research 10). Verify by running the file
      and seeing every test collected.
- [X] T020 [P] [US2] Add tests for the proposal and the draft to
      `tests/test_release_script.py`: a `change` and a `fix` propose a minor and
      say "minor: 1 behaviour change" (scenario 1), `fix` and `none` propose a
      patch (scenario 2), `none` notes leave no section or line (scenario 3),
      the draft drops towncrier's `# ` title line, and two notes with one
      sentence render as one line linking both issues. Verify they fail against
      an empty script.
- [X] T021 [P] [US2] Add tests for merges with no note to
      `tests/test_release_script.py`: a merge that added no file under
      `changes/` is listed under "Merged with no release note" before the draft
      (scenario 4), a `bump-ruff` merge with `+bump-ruff.fix.md` is not listed
      (scenario 5), a merge of `origin/main` into a branch is ignored, and a
      merge that added two notes counts as having one. Verify they fail against
      an empty script.
- [X] T022 [P] [US2] Add tests for nothing to release to
      `tests/test_release_script.py`: only `none` notes, or none, with every merge
      noted, prints "Nothing to release", exits 0, and changes nothing
      (scenario 7); no notes with unnoted merges lists them, proposes a patch,
      drops "No significant changes.", and opens an empty draft (scenario 8).
      Verify they fail against an empty script.
- [X] T023 [P] [US2] Add tests for the prompts and refusals to
      `tests/test_release_script.py`: each precondition in
      `contracts/release-script.md` §Preconditions refuses with its message and
      changes nothing; a typed version is used for the commit and the branch
      (scenario 6); a version not above the current one is asked again; end of
      input, an empty saved draft, and an editor exiting non-zero each leave the
      tree and branches as they were (scenario 9); and an existing
      `release/v0.24.0`, local or on `origin`, is refused by name (scenario 10).
      Verify they fail against an empty script.
- [X] T024 [P] [US2] Add tests for the release commit and its failures to
      `tests/test_release_script.py`: the pushed branch holds one commit with the
      subject `chore(release): cut 0.24.0`, the draft as its body with its `#`
      headings intact, the new version, the stubbed lock's change, and no files
      under `changes/`; the pull request stub got `--base main --head
      release/v0.24.0 --fill`; the script ends on `main`; and `origin`'s `main`
      is at the same commit it was before the run, since the script never pushes
      `main` and never merges (FR-013). A failing lock
      step restores `pyproject.toml`, `uv.lock`, and `changes/`, deletes the
      branch, and leaves `main` clean, and the same failure with `changes/`
      holding no tracked file does too (PR-019). A failing push or pull request
      step leaves the branch and prints the command to run again. Verify they
      fail against an empty script.

### Implementation for User Story 2

- [X] T025 [US2] Create `.github/scripts/release.py` with the preconditions,
      the merge listing from `git log --merges --format='%H %s' <last tag>..HEAD`
      and `git diff --name-only --no-renames --diff-filter=A <merge>^1 <merge>
      -- changes/` (research 7), and the version proposal from the categories,
      holding only the fact that `change` and `addition` propose a minor
      (`data-model.md` §Category). The lock command, the editor, and the pull
      request command are parameters. Verify with T021 and T023's precondition
      cases.
- [X] T026 [US2] Build the draft by copying `changes/` without the `none` notes
      into a temporary directory outside the repository, running
      `sys.executable -m towncrier build --draft --version <v> --config
      <repo>/pyproject.toml --dir <copy>`, keeping the text after "What is seen
      below is what would be written.", and dropping the first `# ` line and a
      line reading exactly "No significant changes." (research 4 and 5). Handle
      nothing to release as `contracts/release-script.md` §Nothing to release
      says. A missing `changes/` folder is the ordinary state after a release,
      since git keeps no empty folder, so the copy starts empty rather than
      failing. Verify with T020 and T022, with one T022 case run where
      `changes/` doesn't exist.
- [X] T027 [US2] Add the two prompts in the contract's order: the version, then
      the branch-exists refusal, then the draft in `git var GIT_EDITOR`, aborting
      on end of input, Ctrl-C, an empty saved file, or a non-zero editor exit
      with "Stopped, nothing was changed." Verify with T023.
- [X] T028 [US2] Make the release commit as `contracts/release-script.md`
      §After both prompts lists it, writing the message file with the subject,
      a blank line, and the draft, and committing with `--cleanup=verbatim`
      (research 6). On a failure in steps 1 to 5, restore with `git restore
      --staged --worktree --source=HEAD -- pyproject.toml uv.lock`, and name
      `changes/` in that restore only when step 4 ran, since git refuses the
      whole command over a pathspec that matches nothing (PR-019). Then switch to
      `main` and delete the branch. On a failure in step 6 or 7, keep the branch
      and print the command. Print the closing lines from §The release text lives
      in the commit. Verify with T024.
- [X] T029 [US2] Update `contracts/release-script.md` §After both prompts to say
      `changes/` is named in the restore only when step 4 ran, and why, so the
      contract matches T028. Mark PR-019 fixed in `plan-review.md` with the
      commit that fixed it. Verify by reading the contract against T028's code.
- [X] T030 [US2] Dry-run the release script on a scratch clone of `main` with
      notes copied in from 0.23.0's changes, and stop at the version prompt.
      Verify that the draft lists behaviour changes first with no `none`
      section, and that `git status --short` and `git branch` match what they
      showed before the run.
- [X] T031 [US2] Validate User Story 2 with `uv run pytest -q`, `uv run ruff
      check wfctl/ tests/`, `uv run mypy wfctl/`, and `uv run wfctl verify` —
      merge gate.

**Checkpoint**: a release can be cut end to end against a scratch repository.

---

## Phase 5: User Story 3 - The GitHub release carries the confirmed release notes (Priority: P3)

**Goal**: the tag job publishes the release commit's body, and fails before
tagging when it can't find that commit or its body is empty.

**Independent Test**: after the first release that runs through this feature,
the GitHub release page shows the same text as the release commit's body.

**Verification**:

- Automated: the YAML parses, and `grep -c generate-notes
  .github/workflows/ci.yml` prints 0.
- Manual: the job's lookup, run by hand in a scratch repository holding a
  release commit and its merge, finds the release commit, not the merge, and
  fails on an empty body.
- Evidence: the first release after merge, per the spec's Validation Strategy.

### Implementation for User Story 3

- [X] T032 [US3] Rewrite the "Tag the version if it is new" step in
      `.github/workflows/ci.yml` as `contracts/tag-job.md` §Contract: the CI
      `tag` job gives it: exit early when both the tag and the release exist;
      find the release commit with `git log -1 --no-merges --format=%H
      --fixed-strings --grep "chore(release): cut $v" HEAD`; check its subject,
      its version through `tomllib`, and a non-empty body before tagging; then
      tag as today and run `gh release create "v$v" --notes-file`. Keep the
      existing comments that still hold, and add one saying why `--no-merges`
      is load-bearing. Verify with the YAML parse and the `generate-notes` grep.
- [X] T033 [US3] Replace the comment above the `tag` job, which says the bump
      belongs in the pull request that makes the change, with one saying what the
      job publishes and why the version call is a person's
      (`change-carries-release-note`, Consequences). Verify by reading it against
      the record.
- [X] T034 [US3] Run T032's lookup and checks by hand in a scratch repository
      holding a `chore(release): cut 0.24.0` commit merged as `Merge pull
      request #1` with that title in its body. Verify four cases: the lookup
      returns the release commit rather than the merge; with the tag already
      present and no release, the steps skip tagging and still reach the release
      (scenario 3); a commit with no body fails with the empty-body message; and
      a release commit whose `pyproject.toml` carries another version fails
      before tagging (scenario 4).
- [X] T035 [US3] Validate User Story 3 with `uv run pytest -q` and the YAML parse
      — merge gate.

---

## Phase 6: User Story 4 - The repository's own docs describe the new process (Priority: P4)

**Goal**: AGENTS.md, the tag job's comment, and this repository's pull request
template describe the new process, and the template wfctl ships is unchanged.

**Independent Test**: read the three places and confirm none describes the old
process, and `git diff origin/main -- wfctl/agents/` is empty.

**Verification**:

- Automated: `uv run pytest -q tests/test_install_config.py tests/test_shape.py`.
- Manual: read AGENTS.md's Releasing section against `quickstart.md`.
- Evidence: `git diff origin/main --stat -- wfctl/` prints nothing.

### Tests for User Story 4

- [X] T036 [US4] Change
      `tests/test_install_config.py::test_shipped_github_config_matches_this_repos_own_copy`
      so that, for `.github/pull_request_template.md` only, it compares the two
      copies with the "Type of Change" section removed from each, from its `##`
      heading to the next one. Add a test that the shipped copy still carries
      that section (scenario 3). Update the docstrings to say why the
      exception exists. Verify that both tests pass after T037, and that the
      test as it stands on `main` fails after T037, which is why it had to change.

### Implementation for User Story 4

- [X] T037 [US4] Remove the "Type of Change" section from
      `.github/pull_request_template.md`, and leave
      `wfctl/agents/configs/github/` untouched. Verify with T036 and `git diff
      origin/main -- wfctl/agents/` printing nothing.
- [X] T038 [P] [US4] Change the comment above `_TEMPLATE` in
      `tests/test_shape.py` so it no longer says the two templates are
      byte-identical. Verify with `uv run pytest -q tests/test_shape.py`.
- [X] T039 [US4] Rewrite AGENTS.md's Releasing section: every change commits a
      note under `changes/`, how to pick its category, cutting a release with
      `uv run python .github/scripts/release.py`, merging the release pull
      request, and amending the commit rather than the description to change the
      text. Add the two commands that protect `main` and the four that read it
      back, as `contracts/tag-job.md` lists them, and say to read them back after
      applying. Add a line under Conventions that every change carries a note.
      Load `writing-style` first. Verify by reading it against `quickstart.md`.
- [X] T040 [US4] Validate User Story 4 with `uv run pytest -q`, `uv run ruff
      check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate.

---

## Phase 7: User Story 5 - `main` refuses a change whose checks failed (Priority: P5)

**Goal**: a committed ruleset protects `main` with no bypass, requiring the five
checks and merge commits only.

**Independent Test**: read `main`'s protection back from GitHub after Andre
applies it, and confirm the required checks, an empty bypass list, and merge
commits as the only method.

**Verification**:

- Automated: `uv run pytest -q tests/test_ruleset.py`.
- Manual: the four read-back commands, after merge, run by Andre.
- Evidence: the next pull request after the ruleset is applied merges only once
  its checks pass.

### Tests for User Story 5

- [X] T041 [P] [US5] Add `tests/test_ruleset.py` asserting that every
      `required_status_checks` context in `.github/rulesets/main.json` is a job
      name `.github/workflows/ci.yml` reports, with the `test` matrix expanded to
      `test (3.11)` and `test (3.13)`, and that `bypass_actors` is empty. Its
      docstring names the risk: a required check whose name never reports blocks
      every merge into `main` (plan, Risks). Verify it fails before T042.

### Implementation for User Story 5

- [X] T042 [US5] Create `.github/rulesets/main.json` exactly as
      `contracts/tag-job.md` §Contract: `.github/rulesets/main.json` gives it.
      Verify with T041.
- [X] T043 [US5] Validate User Story 5 with `uv run pytest -q` — merge gate.
- [ ] T044 [US5] After this feature merges, Andre applies the ruleset and the
      merge setting with the two commands in AGENTS.md, then runs the four
      read-back commands. This is Andre's to run, not the agent's, and it has to
      wait for merge because `release-note` reports on no pull request before
      then. Verify with the read-back output.

---

## Phase 8: Polish

**Purpose**: close the last plan-review finding and run the full definition of
done.

- [X] T045 [P] Fix PR-020 in this feature folder: add "and higher than
      `main`'s" to the release branch sentence in `design.md` §Behaviour and to
      the checks row in `data-model.md` §Release pull request, and make the
      count in `contracts/release-script.md` §Nothing to release agree with the
      seven merges `git log --merges v0.23.0..origin/main` gives. Mark PR-020
      fixed in `plan-review.md`. Verify by reading each sentence against
      `spec.md` FR-004.
- [X] T046 Run `quickstart.md` §Verifying this feature, steps 1 - 4. Verify each
      command's output matches what the step says.
- [X] T047 Run `uv run wfctl doctor` and `uv run wfctl check config`. Verify both
      exit 0.
- [X] T048 Validate the feature with `uv run wfctl verify` — merge gate.

---

## Dependencies and execution order

### Phase dependencies

- Phase 1 has no dependencies. T003 depends on T002.
- Phase 2 depends on T003, since the helper copies the towncrier table.
- Phases 3 and 4 depend on Phase 2 and not on each other (plan, Implementation
  order).
- Phase 5 depends on nothing in Phases 3 and 4 for its code, but T034 is easier
  once T028 can make a real release commit.
- Phase 6 depends on Phases 3 and 4, because AGENTS.md describes both scripts.
- Phase 7 depends on T017, since the ruleset requires the `release-note` job.
- Phase 8 depends on every phase before it. T044 happens after merge and is not
  a dependency of anything in this list.

### Within each story

- Tests come first and fail before the implementation task they name.
- T012 to T014 build one file in order, and so do T025 to T028.
- T016 commits `571.none.md`, and the category question is answered at review.

### Parallel opportunities

- T007 to T011 are separate test groups in one new file, so they can be written
  together and committed as one.
- T019 to T024 likewise.
- Phase 3 and Phase 4 can run side by side.
- T038, T041, and T045 touch files nothing else in their phase touches.

## Parallel example: Phases 3 and 4

```text
Task: "T008 note-presence tests in tests/test_release_note_check.py"
Task: "T020 proposal and draft tests in tests/test_release_script.py"
```

## Implementation strategy

### MVP first

1. Phases 1 and 2.
2. Phase 3. Every later story reads the notes this one requires, and without
   the check notes go missing the way the "Breaking change" checkbox did.
3. Stop and validate: `uv run wfctl verify` fails without a note and passes with
   one.

### Incremental delivery

1. Phase 3 alone is useful: notes start accumulating under `changes/` even
   before the release script exists.
2. Phase 4 lets a release be cut from those notes.
3. Phase 5 makes the GitHub release carry them.
4. Phases 6 and 7 describe the process and protect `main`, and the ruleset is
   applied only after everything else has merged.

## Notes

- `tests/test_ruleset.py` is not in the plan's file list. It is added because
  the plan names the risk it checks, a required check whose name never reports,
  and that risk is visible in two committed files.
- No task changes anything under `wfctl/`, which is SC-005.
- Never push, merge, or close as part of these tasks without asking Andre first.
~~~~
