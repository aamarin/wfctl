Implementation complete: 2026-10-26

## Tasks at completion

~~~~markdown
---
description: 'Task list for the CI review check (#627)'
---

# Tasks: A required CI check fails a PR while a review group has unreviewed commits

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, and `contracts/` in this feature directory
**Prerequisites**: plan review 4 (0 BLOCKER, 0 MAJOR). Three of its open MINOR findings are written in here as tasks rather than as plan edits: PR-009 (T026, T029), PR-024 (T025, T030), and PR-026 (T036, T041, T051). PR-025's example is corrected in T018 and T019.

**Tests**: Every story carries its own tests, written first. Tests that touch output pin `NO_COLOR`, and test names are sentences whose docstrings say which failure the test catches (`AGENTS.md`, Testing conventions).

Design records read before these tasks (via `reading-design-records`):

```
Design records: 3 listed in design.md
  docs/architecture/design/627-unreviewed-takes-coverage.md
  docs/architecture/design/627-review-note-line-per-event.md
  docs/architecture/design/627-guard-blocks-note-writes.md
```

No task reverses one of them. T006 follows `627-unreviewed-takes-coverage.md`, T027 follows `627-review-note-line-per-event.md` with the duplicate check research R6 adds, and T049 follows `627-guard-blocks-note-writes.md`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel with the other [P] tasks in its phase, since it touches different files and depends on no incomplete task.
- **[Story]**: the user story in `spec.md` the task serves.

## Order of the stories

All three P1 stories are needed before the check can pass a PR, and they depend on each other in one direction. US3 builds the counting function and the group list that US2 and US1 both use. US2 writes the notes that US1 reads. So the phases run US3, US2, US1, then the two P2 stories, US4 and US5, which are independent of each other.

---

## Phase 1: Setup

**Purpose**: the release note the `release-note` CI job requires.

- [x] T001 Create `changes/627.addition.md` with `uv run towncrier create 627.addition.md --content "…"`, saying in one sentence that a required `review` check on GitHub now fails a PR while a review group has unreviewed commits, and that wfctl records each completed review as a git note; verify with `uv run wfctl verify`, whose release note check passes.

---

## Phase 2: Foundational

**Purpose**: the two pieces every story builds on. `unreviewed` takes what was reviewed as arguments instead of reading the state directory, and one function computes which groups a branch must review.

**⚠️ CRITICAL**: US1, US2, and US3 all need this phase.

### Tests

- [x] T002 [P] Add tests to `tests/test_review.py` for `unreviewed` with coverage passed in: a group review covers every commit up to it; a commit after it is unreviewed; a sign-off covers the signed-off commit and its ancestors and no commit after it; two signed-off commits each cover their own ancestors; a signed-off commit that isn't in the repository is dropped.
- [x] T003 [P] Add tests to `tests/test_review.py` for `trunk_refs` and `commit_range` with the new `trunk` keyword (research R14): `trunk="main"` uses `origin/main` and ignores a `trunk` key in `wfctl.json`; it skips the single-branch clone refusal; it raises `ReviewError` when `origin/<branch>` doesn't exist, and when it names the branch under review. With `trunk=None`, every existing test passes unchanged.
- [x] T004 [P] Add tests to `tests/test_review_config.py` for the group list (research R13): the trunk's groups come first, then each group the head adds, joined by name; a missing file, or one with no `review` key, gives the default groups for that side; each file is validated on its own, so a trunk group `money-rules` and a head group `mutation` aren't reported as a clash; a problem in either file's `review` key is reported and names which side it came from.

### Implementation

- [x] T005 Add a `trunk` keyword to `trunk_refs` and `commit_range` in `wfctl/_review.py`. With a value, the trunk is `origin/<trunk>`, `_paths.trunk_branch` isn't called, and the single-branch refusal is skipped, but a trunk that names the branch under review is still refused. Verify with T003.
- [x] T006 Change `unreviewed` in `wfctl/_review.py` to the research R10 signature: drop `agent_dir`, take `last_reviewed` and `signed_off`, and pass `trunk` down to `commit_range`. A commit is covered when it is any signed-off commit or an ancestor of one. Add `coverage_from_state(agent_dir, groups)`, which returns each group's `last_reviewed` and the one sign-off as a tuple of zero or one commit. Verify with T002.
- [x] T007 Update the two callers of `unreviewed`, `_judge` in `wfctl/_review_gate.py` and `review_sign_off_cmd` in `wfctl/cli.py`, to build their arguments with `coverage_from_state`. Their group lists stay as they are until T016. Verify with `uv run pytest -q tests/test_review_gate.py tests/test_review_cli.py`, which passes with no test changed.
- [x] T008 Add `parse(text)` beside `load` in `wfctl/_review_config.py`, returning the same groups and problems from a file's text, and `required(trunk, head)`, which joins two parsed configs as research R13 describes and reads no files. Add `required_at(repo_root, head, trunk_ref)`, which reads both files with `git show <ref>:wfctl.json` and calls the two. The module keeps importing neither `typer` nor `rich`, since the guard imports it. Verify with T004.
- [x] T009 Validate the phase with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate.

**Checkpoint**: the counting function takes coverage as input, and the group list exists. Nothing a user sees has changed yet.

---

## Phase 3: User Story 3 - The local check and CI agree on which commits are unreviewed (Priority: P1)

**Goal**: the notes reader builds coverage for CI, and the guard and sign-off require the same groups CI requires, so a PR that passes locally passes in CI.

**Independent Test**: in a scratch repository, build one branch history and record the same reviews and sign-offs in the state directory and in the notes. Both readers produce the same arguments, and `unreviewed` returns the same commits for each.

**Verification**:

- Automated: `tests/test_review_notes.py`, `tests/test_review_gate.py`, `tests/test_review_cli.py`, `tests/test_review.py`
- Manual: none
- Evidence: the readers-agree test passes, including the history where the branch removed a group.

### Tests

- [x] T010 [P] [US3] Create `tests/test_review_notes.py` with tests for `coverage_from_notes` (research R3): each group's last reviewed commit is the nearest noted ancestor of the head; a line wfctl doesn't recognize is skipped; a group line for a group neither list names is ignored; every commit with a sign-off line is returned; notes on trunk commits are never read; a note git can't read raises `ReviewError` naming the commit.
- [x] T011 [P] [US3] Add a test to `tests/test_review_notes.py` that records the same events in the state directory and in the notes, over a history with a group review, a later commit, a sign-off, and a group the branch's committed `wfctl.json` removed, and checks that both readers give `unreviewed` the same arguments and get the same result (SC-004).
- [x] T012 [P] [US3] Add tests to `tests/test_review_gate.py` for FR-010's three changed cases: the guard refuses a branch whose committed `wfctl.json` drops a group the trunk lists, and names that group; it doesn't require a group that's only in the uncommitted `wfctl.json`; it reports a `review` key problem from the trunk's or the head's committed file, not from the working tree.
- [x] T013 [P] [US3] Add tests to `tests/test_review_cli.py` for FR-010a: `wfctl review start` runs a group the branch removed, with the trunk's skill and reviewers; `wfctl review groups` lists it; `review start` runs a group that's only in the working tree, with the working tree's skill and reviewers; a name in neither list prints `✗ no review group named '<group>'` and exits 1.
- [x] T014 [P] [US3] Add tests to `tests/test_review_cli.py` that `wfctl review sign-off` requires the FR-010 list: on a branch that removed a group, it lists that group's unreviewed commits.

### Implementation

- [x] T015 [US3] Create `wfctl/_review_notes.py` with `NOTES_REF = "refs/notes/wfctl-review"` and `coverage_from_notes(repo_root, head, groups, timeout, *, branch, trunk)`, which runs the one `git log` call in research R3 and returns the same two values as `coverage_from_state`. Update reader rule 3 in `contracts/review-note.md` to say a group line counts when the trunk's or the head's `wfctl.json` lists the group, matching `data-model.md`. Verify with T010 and T011.
- [x] T016 [US3] Have `_judge` in `wfctl/_review_gate.py` and `review_sign_off_cmd` in `wfctl/cli.py` take their groups from `_review_config.required_at`, with the head commit and the first entry of `trunk_refs`, instead of `_review_config.load`. A problem in either file stays a refusal naming the cause (research R13). Verify with T012 and T014.
- [x] T017 [US3] Replace `_review_groups_or_exit` in `wfctl/cli.py` with a function returning the FR-010a list for `review start`, `review groups`, and `relay`: the `required_at` list, plus each group the working tree's `wfctl.json` lists. A group's skill and reviewers come from the working tree when it lists the group, and from the trunk's file otherwise. `review check` doesn't use it (T030). Verify with T013.
- [x] T018 [US3] Add tests to `tests/test_review.py` and `tests/test_review_cli.py` for `relay` with two groups sharing a first letter. The case that can arise is a group renamed on the branch: the trunk lists `money-rules`, and the branch renames it to `money`, so the joined list holds both and both use `m1`, `m2`, and so on (PR-025). The tests check that `relay m2` exits 1 with the message in T019, naming both groups and telling the user to rename `money`, and that a relay whose letter matches one group saves as it does today.
- [x] T019 [US3] Change `relay` in `wfctl/_review.py` to find every group whose letter matches the id. When two groups match, it raises `RelayRefused` and exits 1 naming both, as FR-010a requires. The message tells the user to rename the group the branch added, since the trunk still requires the other one:
      ```
      ✗ reviewer m2 matches two groups, money-rules and money.
        main still requires money-rules, so rename money in wfctl.json to start with a different letter.
      ```
      The CLI passes it which group came from the trunk. Update the example in `contracts/cli.md` §Which groups the local commands use to match. Verify with T018.
- [x] T020 [US3] Validate the phase with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate.

**Checkpoint**: both readers exist and agree, and every local command uses the group list CI will use.

---

## Phase 4: User Story 2 - wfctl records each completed review on GitHub (Priority: P1)

**Goal**: a completed run and a sign-off each add a line to the head commit's note, push the notes ref to `origin`, and rerun the PR's failed `review` job.

**Independent Test**: on a branch with one commit, run the security group to completion. `git notes --ref=wfctl-review show HEAD` prints `reviewed by security`, and `git ls-remote origin refs/notes/wfctl-review` shows the ref.

**Verification**:

- Automated: `tests/test_review_notes.py`, `tests/test_review_cli.py`
- Manual: quickstart step 1, after the implementation is complete
- Evidence: the note on `HEAD` and the ref on the scratch repository's bare `origin`.

### Tests

- [x] T021 [P] [US2] Add tests to `tests/test_review_notes.py` for `record`: it creates a note holding the line; it appends a second group's line to an existing note; it skips a line the note already holds (research R6).
- [x] T022 [P] [US2] Add tests to `tests/test_review_notes.py` for the plain push in `send`, against a bare `origin`: the ref arrives; a missing `origin` raises naming it; each successful push is recorded as the outward action `store-reviews`.
- [x] T023 [P] [US2] Add tests to `tests/test_review_notes.py` for `rerun`, with `gh` stubbed (research R8): a failed `review` check is rerun with `gh run rerun <run> --job <job>`, the ids read from its link; no open PR, no `review` check, or a check that didn't fail reruns nothing; `gh` not installed, or an `origin` that isn't on GitHub, reruns nothing and prints nothing; any other `gh` failure prints the warning in `contracts/cli.md`, which doesn't name `store reviews`, and is never retried.
- [x] T024 [P] [US2] Add tests to `tests/test_review_cli.py` for `wfctl review check`: a complete run records `reviewed by <group>` on the run's head and pushes it, and still writes the state directory's `last-reviewed.json` as it does today (FR-005); an incomplete run records nothing; a failed push prints the failed-send warning and exits 0; a failed local write prints the failed-write warning and exits 0, and a second `review check` records the note.
- [x] T025 [P] [US2] Add tests to `tests/test_review_cli.py` that `wfctl review check` doesn't depend on the trunk's config (PR-024). It completes the run and records the note when the trunk's `review` key is broken, when the repository has no trunk ref, and for a group that has a run but that neither list names any more.
- [x] T026 [P] [US2] Add tests to `tests/test_review_cli.py` for `wfctl review sign-off` (PR-009), with `_at_terminal` patched to true: a sign-off records `signed off by a person` on the head and pushes it; a failed push warns and names `wfctl store reviews`; a failed local write warns and tells the user to run the sign-off again. With nothing unreviewed, if the state directory's sign-off is the head and the head's note lacks the line, the sign-off records and sends the note. If the note already holds the line, it prints `nothing unreviewed; no sign-off needed` as it does today and writes nothing.

### Implementation

- [x] T027 [US2] Add `record(repo_root, sha, line)` to `wfctl/_review_notes.py`. It reads the commit's note and runs `git notes --ref=wfctl-review append` only when the note doesn't hold the line. Verify with T021.
- [x] T028 [US2] Add `send(repo_root)` and `rerun(repo_root, branch)` to `wfctl/_review_notes.py`. `send` pushes the ref with the spec store's 60-second network timeout and records the outward action. The rejected-push path comes in T046. `rerun` follows research R8. Verify with T022 and T023.
- [x] T029 [US2] In `review_sign_off_cmd` in `wfctl/cli.py`, after `✓ signed off through <sha>`, record `signed off by a person` on the head, then send and rerun, printing the lines and warnings in `contracts/cli.md`. When nothing is unreviewed, the state directory's sign-off is the head, and the head's note lacks the line, record and send it, so a sign-off whose note write failed can be repeated (PR-009). Add the failed-write warning for the sign-off to `contracts/cli.md` §review sign-off. Verify with T026.
- [x] T030 [US2] In `review_check_cmd` in `wfctl/cli.py`, when the run is complete, record `reviewed by <group>` on the run's head, then send and rerun, with the lines and warnings in `contracts/cli.md`. Keep today's name check, which accepts any name `PLAIN_NAME` matches that has a run, and don't load the group list. As a result, a broken trunk config or a missing trunk can't stop a completed run from recording its note (PR-024). FR-010a still holds, since every group on the list is accepted. Remove `review check` from the "A name in neither" sentence in `contracts/cli.md` §Which groups the local commands use. Verify with T024 and T025.
- [x] T031 [US2] Validate the phase with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate.

**Checkpoint**: every completed run and sign-off reaches `origin` as a note.

---

## Phase 5: User Story 1 - A PR with unreviewed commits can't merge (Priority: P1) 🎯 MVP

**Goal**: `wfctl check reviews` reports the unreviewed commits from the notes, a `review` job on GitHub runs it from `main`'s code, and the ruleset requires that job.

**Independent Test**: in a scratch repository, a branch with one unreviewed commit makes `wfctl check reviews --base main` print the failure and exit 1. After both groups' notes are added, it prints the pass line and exits 0. The GitHub half runs after merge (quickstart steps 2 - 5).

**Verification**:

- Automated: `tests/test_review_cli.py`, `tests/test_review_workflow.py`, `tests/test_ruleset.py`, `tests/test_release_script.py`
- Manual: quickstart steps 2 - 5, after merge, on a throwaway PR
- Evidence: the pass and failure output, and the workflow and ruleset tests.

### Tests

- [x] T032 [P] [US1] Add tests to `tests/test_review_cli.py` for `wfctl check reviews`, with `NO_COLOR` pinned: the pass line; the failure for one commit and for two, each commit listed once, oldest first, with its groups and the closing line from FR-014; each cause line in `contracts/cli.md` (a shallow clone, no trunk, `origin/<branch>` missing, a base that is the branch under review, an unreadable note, a `review` key problem); an uncommitted `wfctl.json` edit that changes nothing; and a reviewed branch with a clean merge of `main` on top, which passes with no new review (SC-003).
- [x] T033 [P] [US1] Add a test to `tests/test_review_cli.py` where the head's `wfctl.json` sets `trunk` to the branch under review: `wfctl check reviews --base main` still lists the branch's unreviewed commits (FR-015a).
- [x] T034 [P] [US1] Add a test to `tests/test_review_cli.py` that `wfctl check reviews` requires a group the PR's committed `wfctl.json` adds, listing every commit under it, and still requires a group the PR removed.
- [x] T035 [P] [US1] Create `tests/test_review_workflow.py`, reading `.github/workflows/review.yml` with `yaml`, with tests that the job: is named `review`; triggers on `pull_request_target` with types `opened`, `synchronize`, `reopened`, and `edited`; has a `concurrency` group keyed by the PR number with `cancel-in-progress: true`; has `permissions` of `contents: read` and nothing else; checks out `github.event.pull_request.head.sha` into `pr/` with `fetch-depth: 0`; fetches `refs/notes/wfctl-review` into `pr/` from `origin`; passes the base branch through `env:`, with no `${{ }}` expression inside any `run:`; and executes nothing from `pr/`, meaning no `uv sync`, `pip install`, script path, or local action there. Add a test that `.github/workflows/ci.yml` has top-level `permissions: contents: read` and that its `tag` job keeps `contents: write`.
- [x] T036 [P] [US1] Update `tests/test_ruleset.py` (PR-026): `reported_check_names` reads job names from `review.yml` as well as `ci.yml`; the required set adds `review`; and the `review` entry is exactly `{"context": "review", "integration_id": 15368}`, so a commit status someone posts by hand under that name doesn't satisfy it. The docstring names PR-010 as the failure the id prevents.
- [x] T037 [P] [US1] Add a test to `tests/test_release_script.py` that after opening the release PR, the script prints `git switch release/v<version>` and then `wfctl review sign-off`, and never runs the sign-off itself (FR-024).

### Implementation

- [x] T038 [US1] Add `wfctl check reviews` to `check_app` in `wfctl/cli.py`, with `--base <branch>`. It gets the trunk ref from `trunk_refs`, the groups from `required_at`, and the coverage from `coverage_from_notes`, then calls `unreviewed` with `trunk` set and prints the output in `contracts/cli.md`. The shallow-clone, no-trunk, and missing-branch causes reuse `ShallowClone`, `NoTrunk`, and `ReviewError`. Verify with T032, T033, and T034.
- [x] T039 [US1] Create `.github/workflows/review.yml` per `contracts/review-job.md`: check out the base branch into `trusted/` and the PR's head into `pr/`, fetch `+refs/notes/wfctl-review:refs/notes/wfctl-review` into `pr/` and continue when `origin` has none, set up uv, and run `uv run --project ../trusted wfctl check reviews --base "$BASE_REF"` with `pr/` as the working directory. Verify with T035.
- [x] T040 [US1] Add top-level `permissions: contents: read` to `.github/workflows/ci.yml`, leaving the `tag` job's own `contents: write`. Verify with T035 and `uv run pytest -q tests/test_tag_release.py`.
- [x] T041 [US1] Add `{ "context": "review", "integration_id": 15368 }` to the required checks in `.github/rulesets/main.json` (FR-018, PR-026). Applying it to GitHub stays the maintainer's step after quickstart step 3. Verify with T036.
- [x] T042 [US1] Have `.github/scripts/release.py` print the two sign-off commands in its closing output, beside the `--cleanup=verbatim` hint (research R12). Verify with T037.
- [x] T043 [US1] Validate the phase with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate.

**Checkpoint**: the check runs locally and the job is ready to run once it reaches `main`.

---

## Phase 6: User Story 4 - A user resends review notes that didn't reach GitHub (Priority: P2)

**Goal**: `wfctl store reviews` sends the notes ref, joining it with `origin`'s when the push is rejected.

**Independent Test**: write a note in two clones of one repository and push from the first. `wfctl store reviews` in the second has its first push rejected, joins the notes, and pushes. `origin`'s note holds both clones' lines.

**Verification**:

- Automated: `tests/test_review_notes.py`, `tests/test_review_cli.py`
- Manual: none
- Evidence: the two-clone test passes.

### Tests

- [x] T044 [P] [US4] Add tests to `tests/test_review_notes.py` for `send` with two clones of one bare `origin`: a rejected push fetches the remote ref into `refs/notes/wfctl-review-remote`, merges it with `cat_sort_uniq`, deletes the temporary ref, and pushes once more; `origin`'s note then holds every line from both clones; a second rejection raises naming git's message.
- [x] T045 [P] [US4] Add tests to `tests/test_review_cli.py` for `wfctl store reviews`, covering each row of the table in `contracts/cli.md`: sent; joined and sent; nothing to send when the local and remote refs match or there's no local ref; no `origin`; and a second rejection, exit 1. A successful send reruns a failed job, with `gh` stubbed.

### Implementation

- [x] T046 [US4] Extend `send` in `wfctl/_review_notes.py` with the rejected-push path in research R7, and add the `git ls-remote` comparison that reports nothing to send. Add `wfctl store reviews` to `store_app` in `wfctl/cli.py`, next to `store specs`, printing the output in `contracts/cli.md` and calling `rerun` after a successful send. Verify with T044 and T045.
- [x] T047 [US4] Validate the phase with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate.

---

## Phase 7: User Story 5 - An agent can't write review notes by hand (Priority: P2)

**Goal**: the worktree guard refuses an agent's `git notes` writes and its pushes of any notes ref, and allows reads.

**Independent Test**: with the guard installed, `git notes --ref=wfctl-review add -m "reviewed by code" HEAD` is refused, and `git notes --ref=wfctl-review show HEAD` runs.

**Verification**:

- Automated: `tests/test_review_gate.py`
- Manual: the independent test above in this worktree, after `uv run wfctl install-skills`
- Evidence: the refusal text in `contracts/cli.md` §Guard refusals.

### Tests

- [x] T048 [P] [US5] Add tests to `tests/test_review_gate.py`: each of `add`, `append`, `edit`, `copy`, `merge`, `remove`, and `prune` is refused, on any ref and with `--ref x`, `-c core.notesRef=x`, or `GIT_NOTES_REF=x` before or between the words; `git push` with an argument holding `refs/notes/`, and `git push --mirror`, are refused; `git notes show`, `git notes list`, `git log --notes`, and a plain `git push` are allowed; the refusal prints the text in `contracts/cli.md`. Add a test that the hook's quick text test loads the review check for a command holding `notes` or `--mirror`.

### Implementation

- [x] T049 [US5] Add the two text rules in research R9 to `read` in `wfctl/_review_gate.py`, in the same first pass as the sign-off refusal, each reading one command between the separators `_SEPARATOR` already splits on. Add `"notes" in command` and `"--mirror" in command` to the quick text test in `wfctl/_hook.py` (FR-022). Verify with T048.
- [x] T050 [US5] Validate the phase with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [x] T051 [P] Update quickstart step 4 in `quickstart.md` in this feature directory so the read-back checks that the `review` entry carries `integration_id` 15368, as `contracts/review-job.md` says it does (PR-026). Verify by reading the step against the contract.
- [x] T052 [P] Update `AGENTS.md` (FR-025): the ruleset requires six checks, `review` among them, and the read-back shows its `integration_id`; `wfctl store reviews` resends notes that didn't reach `origin`; the guard refuses hand-written notes; a release needs the maintainer's sign-off on the release commit; and the recovery from a broken `review` key on `main` (research R13). Verify with `grep -n -E 'store reviews|integration_id|review' AGENTS.md` and a read of the Releasing and Safety sections.
- [x] T053 [P] Add `wfctl check reviews` and `wfctl store reviews` to `docs/reference.md`. Verify by reading the entries against `contracts/cli.md`.
- [x] T054 Run quickstart step 1 on this branch: run both review groups, check that `git notes --ref=wfctl-review show HEAD` prints both lines, and that `uv run wfctl check reviews` prints the pass line.
- [x] T055 Validate the feature with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `uv run wfctl verify`, and `uv run wfctl doctor` — merge gate.

**After merge** (the maintainer, not a task for this branch): quickstart steps 2 - 5 on a throwaway PR. Step 2 checks that a `pull_request_target` job reports on the PR's head (research R4), step 3 checks the rerun's link shape (R8), step 4 applies the ruleset and reads back `integration_id` 15368, and step 5 checks that a retarget sends `edited` (R14). The ruleset is applied only after step 3 passes.

---

## Dependencies & Execution Order

### Phase dependencies

1. Setup (Phase 1) has no dependencies.
2. Foundational (Phase 2) blocks every story.
3. US3 (Phase 3) needs Phase 2. US2 (Phase 4) needs `_review_notes.py` from T015. US1 (Phase 5) needs `coverage_from_notes` from US3 and the notes US2 writes.
4. US4 (Phase 6) needs `send` from T028. US5 (Phase 7) needs only Phase 2, and can run beside US3, US2, or US1.
5. Polish (Phase 8) needs every story.

### Within each story

Tests come first and fail before the implementation. T019 needs T017, since the CLI tells `relay` which group came from the trunk. T029 and T030 both edit `wfctl/cli.py` and `contracts/cli.md`, so they run one after the other.

### Parallel opportunities

- In Phase 2, T002, T003, and T004 run together.
- In Phase 3, T010 - T014 run together.
- In Phase 4, T021 - T026 run together.
- In Phase 5, T032 - T037 run together, and T039 - T042 touch different files and run together once T038 is done.
- US5 can run beside US3, US2, and US1.
- In Phase 8, T051 - T053 run together.

## Parallel Example: User Story 1

```bash
Task: "Tests for wfctl check reviews output in tests/test_review_cli.py"
Task: "Workflow tests in tests/test_review_workflow.py"
Task: "Ruleset test with integration_id in tests/test_ruleset.py"
Task: "Release script sign-off lines in tests/test_release_script.py"
```

## Implementation Strategy

The check can't pass any PR until US3, US2, and US1 are all in, so those three are the minimum useful slice. US4 is the repair path the failure message points to, and US5 closes the plain route of an agent writing a note by hand. Both are small and ship in the same PR unless decompose splits them.

This feature's own PR gets no `review` job, since GitHub reads the job from `main`. It relies on the local guard, and the post-merge steps decide when the ruleset is applied.
~~~~
