Implementation complete: 2026-10-15

## Tasks at completion

~~~~markdown
---
description: 'Task list for storing a branch spec dir on its spec store remote'
---

# Tasks: wfctl stores a branch's spec dir on its spec store's remote

**Input**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/cli.md`, and `quickstart.md` in this feature directory, and the three
design records `design.md` lists.

**Tests**: Every story carries tests. The store is the first code path in the
suite that can push, so the test guard in T002 comes before any store code.
Tests that assert on console output pin `NO_COLOR`.

**Organization**: One phase per user story, in the spec's priority order. The
store itself is built once, in US1, and later stories add to it: US4 adds the
ways a merge can fail, and US5 adds the layouts with nowhere to push.

**Open plan-review findings**: The last plan review left 15 MINOR findings open.
Most have a suggested response an implementer can apply without a new design
decision, and those are folded into the tasks below, each naming its finding.
Two need Andre's call and are not tasks: PR-006, whether the default `wfctl
status` shows a `skipped` store-specs pass, and PR-024, what removal does when
the spec store is its own checkout inside the code worktree.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete
  task)
- **[Story]**: the user story the task belongs to (US1 to US5)

## Path Conventions

Single package: `wfctl/` and `tests/` at the repository root.

---

## Phase 1: Setup

**Purpose**: Confirm the one assumption the merge decision rests on, and make
sure no test can push to a real remote, before any store code exists.

- [X] T001 Write `test_merge_abort_leaves_another_branchs_edits_alone` in `tests/test_spec_store.py` against a hand-built fixture: a bare remote and two clones in `tmp_path`, the remote one commit ahead, a conflict in one folder, and another folder holding an edited tracked file and an untracked file. Run `git merge --abort` directly and assert the other folder is byte-for-byte unchanged. If it fails, stop and reopen `store-specs-merges-before-push.md` before any store code (T014); verify with `uv run pytest -q tests/test_spec_store.py`
- [X] T002 Add an autouse fixture in `tests/conftest.py`, in the style of the version-check stub, that makes any store refuse a remote URL that is not a local path under the test's `tmp_path`, so a test that forgets to set `WFCTL_SPEC_DIR` can't push the developer's real spec store (PR-004). Register a marker in `pyproject.toml` that opts out, following `real_version_check`; verify with a test in `tests/test_spec_store.py` that points a store at a non-local remote and expects the refusal
- [X] T003 Validate Phase 1 with `uv run pytest -q tests/test_spec_store.py` — merge gate

---

## Phase 2: Foundational

**Purpose**: The layout and "is it stored" reads that every story uses. Nothing
here writes to git.

**⚠️ CRITICAL**: No user story starts until this phase is done.

- [X] T004 Create `wfctl/_spec_store.py` with standard-library imports only at module scope (PR-012), and move the per-root half of `_hook.committable` into `owns_branch(root, here)` there (research R2). `owns_branch` keeps the guard's direction on an error: when git can't answer, the root is not a store; verify with T005 and T006
- [X] T005 Change `committable` in `wfctl/_hook.py` to import `_spec_store` inside the function and call `owns_branch` per root, with no change in behaviour; verify with `uv run pytest -q tests/test_worktree_guard.py tests/test_guard_entry.py tests/test_hook_user_prompt.py` unchanged
- [X] T006 Add a test to `tests/test_guard_entry.py` whose command contains `git commit`, so `committable` runs, and assert the guard still never imports `typer`, `rich`, or `wfctl.cli` (PR-012); verify with `uv run pytest -q tests/test_guard_entry.py`
- [X] T007 Add `Layout` (a `NamedTuple` of kind, root, remote, and upstream ref) and `layout(spec_root, repo_root)` to `wfctl/_spec_store.py`, returning `store`, `store_no_upstream`, `in_repo`, or `unmanaged` per `data-model.md §Layout`. The `store` kinds also require `git rev-parse --show-toplevel` in the root to name the root itself (FR-010); verify with T008
- [X] T008 [P] Test each layout kind in `tests/test_spec_store.py`, including a worktree on the code's own branch (`in_repo`) and a folder nested in another repository (`unmanaged`); verify with `uv run pytest -q tests/test_spec_store.py`
- [X] T009 Add `Unstored`, `unstored(root, paths)`, and `describe(unstored)` to `wfctl/_spec_store.py`, using the two git commands in research R3 and grouping output by each path's first component. `describe` renders `uncommitted: N files` or `committed, not pushed`, preferring the count when both hold (`data-model.md §Spec dir state`); verify with tests in `tests/test_spec_store.py` for an untracked new dir counted per file, an unpushed commit, both at once, and a stored dir returning nothing
- [X] T010 Validate Phase 2 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: The guard refactor is proven to move no behaviour, and the reads
the pass, `check specs`, and removal share are in place.

---

## Phase 3: User Story 1 - An unattended run stores its own spec dir (Priority: P1) 🎯 MVP

**Goal**: Once `implement` is done, `wfctl status` names `/store-specs` until
the spec dir is on its upstream, and `wfctl store specs` gets it there.

**Independent Test**: In a fixture whose spec store has an upstream, finish
`implement` with an uncommitted file in the spec dir. `wfctl status --json`
names `/store-specs`. Run `wfctl store specs`, and the commit is on the upstream
and the pass reads `done`.

**Verification**:

- Automated: `tests/test_spec_store.py`, `tests/test_store_specs_pass.py`,
  `tests/test_pipeline_payload_snapshot.py`
- Manual: `quickstart.md` steps 2, 3, and 5
- Evidence: the `specs(359): store …` commit on `origin/specs-trunk`, touching
  only `359-push-specs-to-trunk/`

### Tests for User Story 1 ⚠️

> Write these first and see them fail.

- [X] T011 [P] [US1] In `tests/test_spec_store.py`: the commit holds only this folder and another staged path stays staged (FR-001); a moved remote is merged and pushed; a deleted file is committed as a deletion; `already_stored` creates no commit (FR-009); the subject starts `specs(<issue>):` and names the files (FR-002); the success line counts files from an earlier unpushed commit too (research R9); the success output is the two lines `contracts/cli.md` gives, and the count's noun is "files" (FR-008). Assert on the noun rather than on "specs" being absent, because the same line names `origin/specs-trunk`
- [X] T012 [P] [US1] In `tests/test_spec_store.py`: an unreachable remote keeps the commit and reads `not_pushed`, exit 1 (FR-006); the next store from another branch with files of its own pushes both commits; a push refused after the merge keeps the merge commit (`push_refused`); an authentication failure reads `git_failed` with git's message, not "unreachable" (PR-010); every git call runs with `GIT_TERMINAL_PROMPT=0` and `GIT_SSH_COMMAND` carrying `-o BatchMode=yes` (PR-003)
- [X] T013 [P] [US1] In `tests/test_store_specs_pass.py`: `implement` done with uncommitted files names `/store-specs` and reads `in_progress`; committed and pushed reads `done` with no fetch; committed and not pushed reads `in_progress`; the pass never puts a `reason` on the reading, so it never routes to `wfctl verify`; `wfctl step none implement.store-specs` wins over the reader

### Implementation for User Story 1

- [X] T014 [US1] Add `StoreResult` and `store(spec_dir, branch, repo_root)` to `wfctl/_spec_store.py` for the `store` layout: `git add -A -- <dir>`, `git commit -- <dir>`, fetch only the upstream branch, `git merge --no-edit @{u}`, push (research R8, R9). Never rebase, stash, or force-push, and never name `specs-trunk` (FR-004, FR-005). Map failures per PR-010: a timeout or connection error reads `not_pushed`, a non-fast-forward push reads `push_refused`, anything else reads `git_failed`. Set `GIT_TERMINAL_PROMPT=0` and `GIT_SSH_COMMAND=ssh -o BatchMode=yes` on every call, and a 60-second timeout on fetch and push (research R7, PR-003); verify with T011 and T012
- [X] T015 [US1] Add `stops_removal` to `StoreResult`: false for every outcome when the spec dir is outside the worktree, true when it is inside and was not copied out, `not_applicable` included (research R6, `data-model.md §Store result`); verify with a test in `tests/test_spec_store.py` for both sides, which also asserts `not_applicable` still exits 0 by hand
- [X] T016 [US1] Word the `not_pushed` remedy line so it is true for a branch with nothing new: "the next `wfctl store specs` with files to push sends it" (PR-007). Update the example in `contracts/cli.md` to match; verify with the exact-text assertion in T012
- [X] T017 [US1] Add `store_app` and `wfctl store specs` to `wfctl/cli.py`. It reads the branch and spec dir as `wfctl feature-paths` does, prints the result per `contracts/cli.md`, picks the exit code from `data-model.md §Store result`, and on `stored` only records a `store-specs` action with `_session.record_outward_action` (research R15); verify with CLI tests in `tests/test_spec_store.py` for each exit code, for `already_stored` recording nothing, and for `no_spec_dir` on a branch with no spec dir and on `main`, which prints `ℹ no spec dir for <branch>`, exits 0, and commits nothing (spec §Edge Cases, `data-model.md §Store result`)
- [X] T018 [US1] Add `store_specs(ev)` to `wfctl/_evidence.py`, beside `plan_review`, returning `Assessment` with the text in `display` and `reason` always `None` (research R4, `data-model.md §The store-specs pass`). The "reason naming the layout" that FR-018 and `store-specs-implement-pass.md` ask for on a `skipped` reading is this `display` text; the payload's `reason` field is a different thing, the one that routes to `wfctl verify`; verify with T013
- [X] T019 [US1] Add `SubStep("store-specs", "/store-specs", _AUTOMATIC, _evidence.store_specs)` to `_STEPS["implement"]` in `wfctl/_pipeline.py` (FR-017); verify with T013
- [X] T020 [P] [US1] In `tests/test_store_specs_pass.py`, write the routing tests: a host block on `store-specs` routes to `/store-specs` with `auto: false`, not `wfctl verify`, in `status --json` and in the `next-step.md` that `wfctl next` writes (not the copy `resume` writes, which goes through `build_report`); a `push` or `issue-close` block on a finished `implement` with store-specs outstanding still routes to `wfctl verify`; a declared manual pass under `implement` with a block filed for its name returns the qualified pass name with `auto: false`; a successful `wfctl store specs` after the block records the action, lifts the hold, and the pass reads `done`
- [X] T021 [US1] Add the `block_action` argument to `next_step_content` in `wfctl/_pipeline.py`: a block whose action matches the outstanding pass's name routes to that pass before the `wfctl verify` fallback, and every other block routes as today. Update its docstring to name that one exception and why (research R15). Pass `block_action` from both callers, `build_report` and `next_cmd` in `wfctl/cli.py`, which stops discarding `_by_step`; verify with T020
- [X] T022 [US1] Create `wfctl/agents/commands/store-specs.md`. It runs `wfctl store specs` and nothing else that writes. When the host refuses it, it runs `wfctl report-block store-specs --reason "…"` and stops, and never tries another way to push (FR-019). On exit 1 it reports what the store printed and doesn't retry. Either way it then invokes `speckit-orchestrate`. Load `writing-style` before writing it; verify with `uv run pytest -q` (the suite's skill cross-reference checks) and by reading the installed copy after T051
- [X] T023 [US1] Run `tests/test_pipeline_payload_snapshot.py` and confirm the snapshot does not change. `_dump` records step rows only, and the pass moves no step row, so an unchanged snapshot is the check (PR-005). If it does change, stop and find out why before regenerating. This supersedes plan.md, whose Project Structure and Implementation order step 6 still say to regenerate it; plan.md is left as it is for the reason T049 gives; verify with `uv run pytest -q tests/test_pipeline_payload_snapshot.py`
- [X] T024 [US1] Validate User Story 1 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: An unattended run that follows `next_command` stores its spec
dir. This is the MVP.

---

## Phase 4: User Story 2 - Removal stores what is left and never says "durable" (Priority: P1)

**Goal**: Removing a worktree runs the store through the `archive-specs` line
every hook already calls, and a failed store warns instead of stopping removal.

**Independent Test**: Write a file into the spec dir after the last store, then
remove the worktree. The file is on the upstream afterwards, the output has no
"durable", and no `.workmux.yaml` changed.

**Verification**:

- Automated: `tests/test_archive_specs.py`
- Manual: `quickstart.md` step 7, with the network on and then off
- Evidence: the file on `origin/specs-trunk` after `wm remove`, and the "not
  pushed" warning with the worktree still removed when offline

### Tests for User Story 2 ⚠️

- [X] T025 [P] [US2] After T026's check of `origin/main`, which decides whether these tests land here or on `hook worktree-remove`, update `tests/test_archive_specs.py`: the old durable test now asserts the store ran and "durable" appears nowhere (FR-022); a fully stored spec dir at removal says it is stored and pushes nothing (US2 scenario 2); a failed push at removal warns and exits 0 (FR-021); a lock timeout and a merge refusal at removal warn and exit 0; the in-worktree archive path is unchanged (research R11)

### Implementation for User Story 2

- [X] T026 [US2] Before editing, check whether #40's `wfctl hook worktree-remove` is on `origin/main`. If it is, merge `main` in, skip T027, move T025's tests onto the hook starting from a clean worktree (because `archive unsaved` refuses a dirty one), check the hook reads `stops_removal` rather than the exit code, and check the merged `store` runs #40's copy-out before it would return `not_applicable` in the default layout (plan §Implementation order step 7, research R6, R11); verify with `git log origin/main --oneline -- wfctl/cli.py` and the moved tests
- [X] T027 [US2] Change `archive_specs_cmd` in `wfctl/cli.py`: where the spec dir is outside the worktree, call `_spec_store.store` as a function, print what it printed in place of the "durable" line, and read `stops_removal`, never the exit code, so every store failure there is a warning and removal goes ahead. Leave the in-worktree path as it is (research R6, R11); verify with T025
- [X] T028 [US2] Validate User Story 2 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: Removal stores the last files a branch wrote, and never calls an
unstored spec dir safe.

---

## Phase 5: User Story 3 - A person can list every spec dir that isn't stored (Priority: P2)

**Goal**: `wfctl check specs` lists unstored spec dirs, with those whose branch
still has a worktree under "In progress", and exits 1 only for the rest.

**Independent Test**: Leave one spec dir with an uncommitted file and one with
an unpushed commit, neither with a worktree, and `check specs` lists both under
"not stored" and exits 1. Store both and leave a third unstored whose branch has
a worktree, and it lists that one under "In progress" and exits 0.

**Verification**:

- Automated: `tests/test_check_specs.py`
- Manual: `quickstart.md` step 4
- Evidence: the 58 older untracked spec dirs under "not stored", and this
  branch's dir absent after step 3

### Tests for User Story 3 ⚠️

- [X] T029 [P] [US3] Create `tests/test_check_specs.py`: unstored dirs with no worktree are listed and exit 1; a dir a worktree resolves to goes under "In progress" and exits 0; a prunable worktree does not keep its dir in progress; all stored prints the one-line tick and exits 0; the "In progress" block is left out when empty; a non-store layout names the root and exits 0; no git call in the run fetches (FR-016, FR-023, FR-024)

### Implementation for User Story 3

- [X] T030 [US3] Add `wfctl check specs` to `wfctl/cli.py`. It runs `layout` and one `unstored` call over the whole root, builds the "In progress" set by running `resolve_spec_dir` on every branch `worktree_branches` returns, and prints per `contracts/cli.md` (research R3, R10); verify with T029
- [X] T031 [US3] Change `check_app`'s help in `wfctl/cli.py` to "Check a repository's configuration and its spec store." (FR-025); verify with a `wfctl check --help` assertion in `tests/test_check_specs.py`
- [X] T032 [US3] Validate User Story 3 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: The spec dirs the store missed stay visible.

---

## Phase 6: User Story 4 - The store picks up remote changes without touching other branches' files (Priority: P2)

**Goal**: Every way a merge can fail is told apart, backed out where needed,
and reported with a remedy that is true for it. Two stores never interleave.

**Independent Test**: With the remote one commit ahead, another branch's tracked
file edited, and another branch's folder untracked, `wfctl store specs` pushes,
and the edited and untracked files are exactly as they were.

**Verification**:

- Automated: `tests/test_spec_store.py`
- Evidence: byte-for-byte comparisons of other branches' files before and after
  each store (SC-005)

### Tests for User Story 4 ⚠️

- [X] T033 [P] [US4] In `tests/test_spec_store.py`: another branch's edited tracked file and untracked folder are unchanged after a merge-and-push, and neither is in the commit (US4 scenario 2, SC-005)
- [X] T034 [P] [US4] In `tests/test_spec_store.py`: a conflict in this folder reads `conflict`, not staged files, even though `git diff --cached` lists paths; it aborts, keeps the commit, names the folder, leaves no `MERGE_HEAD`, and prints a remedy line (FR-007, research R8, PR-011)
- [X] T035 [P] [US4] In `tests/test_spec_store.py`: another folder's file staged with the remote moved keeps the commit, refuses the merge, names the staged folder, exits 1; storing the branch that owns that folder clears the index and pushes the first branch's kept commit with its own, and the first branch's next store reads `already_stored`
- [X] T036 [P] [US4] In `tests/test_spec_store.py`: a merge blocked by an unstaged edit with nothing staged names the file (`merge_refused`); a merge blocked by an untracked file the upstream adds names that file and says it is untracked, not edited (PR-015)
- [X] T037 [P] [US4] In `tests/test_spec_store.py`: a store that finds `MERGE_HEAD` already present before it starts reports it with a remedy and does not commit (PR-011)
- [X] T038 [P] [US4] In `tests/test_spec_store.py`: a second store waits for the first, and fails with `another store is running in <root>` after the timeout (FR-027). Pass a short timeout so the test doesn't take 10 seconds

### Implementation for User Story 4

- [X] T039 [US4] In `store`, after a failed merge, tell the kinds apart in research R8's order: `MERGE_HEAD` first (read the unmerged paths with `git diff --name-only --diff-filter=U` before `git merge --abort`), then `git diff --cached --name-only`, then git's message. Parse file names from both the local-changes header and the untracked-files header, and give the untracked case its own text and remedy (PR-015); verify with T034, T035, T036
- [X] T040 [US4] Give the conflict output a remedy line naming the git commands a person runs in the spec store, and say that it blocks every branch's store until resolved. Before committing, check for a `MERGE_HEAD` a killed store left behind and report it the same way (PR-011). Add both texts to `contracts/cli.md`; verify with T034 and T037
- [X] T041 [US4] Add `_lock(git_dir, timeout=10.0)` to `wfctl/_spec_store.py`: `fcntl.flock` on `wfctl-store.lock` in the directory `git rev-parse --git-dir` names, polled every 0.2 seconds, covering the whole run from `git add` to the end of the push, and left in place after (research R5); verify with T038
- [X] T042 [US4] Validate User Story 4 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: The store survives more than one machine and more than one
branch sharing the spec store.

---

## Phase 7: User Story 5 - Layouts with nowhere to push say where the files are (Priority: P3)

**Goal**: In a layout with no upstream, inside the code repository, or a plain
folder, wfctl says where the files are and that nothing backs them up, and the
pass reads `skipped` so the pipeline finishes.

**Independent Test**: With the spec root set to a plain folder, finish
`implement`. The pass reads `skipped` with a reason naming the folder, and the
pipeline reads finished.

**Verification**:

- Automated: `tests/test_spec_store.py`, `tests/test_store_specs_pass.py`
- Evidence: exit 0 and the layout's sentence for each of the three layouts

### Tests for User Story 5 ⚠️

- [X] T043 [P] [US5] In `tests/test_spec_store.py`: a spec store with no upstream commits, reads `committed_not_backed_up`, and exits 0 when run by hand (FR-012, research R6, PR-029); a spec root inside the code repository commits nothing on the feature branch and exits 0 (FR-011); a plain folder commits nothing and prints "not backed up anywhere" with the path (FR-013)
- [X] T044 [P] [US5] In `tests/test_store_specs_pass.py`: each non-store layout reads `skipped` with its `display` text, no `reason`, and no warning on `status`

### Implementation for User Story 5

- [X] T045 [US5] Pick one string for `committed_not_backed_up`, `⚠ committed N files, not backed up — <branch> has no upstream branch`, and use it in `wfctl/_spec_store.py`, `data-model.md`, and `contracts/cli.md`. Drop "committed" from the pass's `store_no_upstream` display, since the pipeline never ran the store there: `no upstream branch; not backed up` (PR-009); verify with T043 and T044
- [X] T046 [US5] Implement the three non-store branches of `store` and the reader's `skipped` rows per `data-model.md`; verify with T043 and T044
- [X] T047 [US5] Validate User Story 5 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: No repository reads a green tick over a folder nothing backs up.

---

## Phase 8: Polish and cross-cutting

**Purpose**: The end-of-session instruction, the planning text the review found
stale, and the real run against this repository's spec store.

- [X] T048 [P] Change the "Report only" paragraph in step 7 of `wfctl/agents/skills/end-session/SKILL.md`: in a spec store with an upstream, the report line names `wfctl store specs` as the way to store the files and still says not to `git add` or `git commit` there by hand. Other layouts keep "report only" (FR-026, research R12). Load `writing-style` first; verify by reading the installed copy after T051
- [X] T049 [P] Correct the statement that wfctl writes nothing but git history in the opening of `data-model.md`: the store writes git history and one action event on `stored`, and the pass reads only git (PR-019). Leave the same claim in `plan.md` as it is, because any edit to `plan.md` makes the plan review stale and sends the pipeline back to `plan`. In research R15, say that a commit pushed by another branch's store, after a `not_pushed` run under a block, needs `wfctl report-action store-specs` to lift the hold (PR-018); verify by reading the edited sections
- [X] T050 [P] Replace `quickstart.md` step 6 with a timing of `wfctl status` with the pass, and again after `wfctl step none implement.store-specs`, and drop "exactly the two git commands" (PR-008); verify by running the new step 6
- [X] T051 Run `uv run wfctl install-skills --agent claude`, then `uv run wfctl doctor`, and read the installed `.claude/commands/store-specs.md` and end-session skill (`quickstart.md` step 1)
- [X] T052 Run the definition of done: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl doctor` — merge gate
- [ ] T053 Run every step of `quickstart.md`, including the real `wfctl store specs` of this branch's spec dir with the commit shown on `origin/specs-trunk` (it also pushes `ed3f5e8`, which plan §Risks accepts), `wfctl check specs` reporting an unstored dir, `/store-specs` from the installed wrapper, and removal of a throwaway worktree online and offline. The real push may be refused by the host; that is a `report-block`, not something to route around

---

## Dependencies and execution order

### Phase dependencies

- **Setup (Phase 1)**: none. T001 runs first; if it fails, nothing after it
  starts.
- **Foundational (Phase 2)**: after Setup. Blocks every story.
- **US1 (Phase 3)**: after Foundational. It builds `store`, which US2, US4, and
  US5 extend or call.
- **US2 (Phase 4)**: after US1, since removal calls `store`.
- **US3 (Phase 5)**: after Foundational only. It reads, never stores, so it can
  run beside US1.
- **US4 (Phase 6)**: after US1. It adds failure handling to `store`.
- **US5 (Phase 7)**: after US1. It adds layouts to `store` and the reader.
- **Polish (Phase 8)**: after every story. T049 and T050 edit only planning
  files and can run any time.

### Within each story

Tests are written first and fail before the implementation task they pair with.
`wfctl/_spec_store.py` and `wfctl/cli.py` are each touched by several stories,
so stories that share them run one after the other, not in parallel.

### Parallel opportunities

- T008 beside T009, once T007 is done.
- Within a story, the test tasks marked [P] write different test functions and
  can be drafted together, though several share `tests/test_spec_store.py`.
- US3's test task, T029, beside US1 (Phase 3), since `check specs` touches
  neither `store` nor the pipeline. T030 and T031 edit `wfctl/cli.py`, as T017
  does, so they wait for it.
- T048, T049, and T050 beside each other.

---

## Parallel example: User Story 1

```bash
# Draft the three test groups together:
Task: "T011 store commit and merge tests in tests/test_spec_store.py"
Task: "T012 store failure and environment tests in tests/test_spec_store.py"
Task: "T013 pass reader tests in tests/test_store_specs_pass.py"
```

---

## Implementation strategy

### MVP first

1. Phase 1, and stop if T001 fails.
2. Phase 2.
3. Phase 3 (US1). Stop and run `quickstart.md` steps 2 and 3 against the real
   spec store. At that point an unattended run stores its own specs.

### Incremental delivery

1. US1, then US2: the two P1 stories close the bug for new branches and at
   removal.
2. US3 and US4: the P2 stories make the gap visible and make the store hold up
   with more than one machine.
3. US5: the P3 layouts no repository uses today.
4. Polish, then the real run.

---

## Notes

- Commit after each task or logical group, with `docs(…)` or `feat(…)` subjects
  per `AGENTS.md`.
- The design records that bind this work are `store-specs-implement-pass.md`,
  `store-specs-at-removal.md`, and `store-specs-merges-before-push.md`. A task
  that reverses one of them is a defect.
- #40 is changing removal at the same time. T026 is where that is checked, not
  earlier.
~~~~
