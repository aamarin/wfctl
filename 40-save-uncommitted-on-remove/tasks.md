---
description: 'Task list for saving unsaved work when a worktree is removed'
---

# Tasks: Save unsaved work when a worktree is removed

**Input**: Design documents from `/Users/andremarin/Development/wfctl-specs/40-save-uncommitted-on-remove/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md
**Design record**: `docs/architecture/design/40-archive-is-a-command-group.md`. The removal hook calls `wfctl hook worktree-remove`, which runs `store specs` and then `archive unsaved`, and `archive-specs` stays as its hidden alias.

**Tests**: Every phase writes its tests first and checks they fail before the
code they cover exists. Tests build real git repositories and worktrees under
`tmp_path`, as `tests/test_archive_specs.py` already does, and any test that
reads console output pins `NO_COLOR`.

**Open review findings**: The plan review left 4 MAJOR and 9 MINOR findings
open in `plan-review.md`, and Andre skipped the walkthrough. These tasks follow
`plan.md` as written and don't resolve those findings.

**How the stories are tested before the hook exists**: Stories 1 and 2 are
checked through `wfctl archive unsaved`, and Story 3 through `wfctl store specs`.
Both print the same lines and return the same exit codes the hook does
(contracts/cli.md). Story 4 is where `wfctl hook worktree-remove` runs them
together, and it is the first point at which a real removal behaves differently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: Which user story the task belongs to (US1 - US5)

---

## Phase 1: Setup

**Purpose**: Check the two git behaviors research R5's copy rules rest on, before any copy code is written.

- [x] T001 Create `tests/test_archive_unsaved.py` with a fixture helper that builds a repository with a bare remote, a trunk branch, and a linked worktree under `tmp_path`. Add the two assumption tests: `git ls-files --others --exclude-standard -z` lists a nested git repository as one `dir/` entry, and lists an untracked symlink, including one that points at a folder, as a path. Verify with `uv run pytest tests/test_archive_unsaved.py -q`. If either test fails, stop and revisit research R5 before Phase 2.
- [x] T002 Validate Setup with `uv run pytest tests/test_archive_unsaved.py -q` — merge gate

---

## Phase 2: Foundational

**Purpose**: The result types and the `archive` command group that Stories 1, 2, and 5 all write into.

**⚠️ CRITICAL**: Stories 1, 2, and 5 can't start until this phase is complete. Story 3 doesn't depend on it.

- [x] T003 Add the `UnsavedCheck` dataclass (`edits`, `unmerged`, `trunk`, `warnings`, `untracked`, `folders`), the `SavedResult` dataclass (`dest`, `files`), and the `SaveFailed` exception to `wfctl/_archive.py`, as data-model.md describes them. Leave `ArchiveIncomplete` and the numbered archive in place, since `archive_specs_cmd` still uses them until T030. Verify with `uv run mypy wfctl/`.
- [x] T004 In `wfctl/cli.py`, add an `archive_app` typer group registered as `archive`, and an `archive unsaved [WORKTREE]` command that resolves `WORKTREE` from the argument, then `$WM_WORKTREE_PATH`, then the current repository. Add one helper that prints a removal stop: the `✗ removal stopped` header, each group of findings, and the `Remove anyway:` route with `git worktree remove --force` and `git branch -D`, quoted with `shlex.quote`, printed with `soft_wrap=True` and every path escaped (research R13). The command calls nothing else yet. Verify with a test in `tests/test_archive_unsaved.py` that `wfctl archive --help` lists `unsaved`.
- [x] T005 Validate Foundational with `uv run pytest tests/test_archive_unsaved.py -q` and `uv run mypy wfctl/` — merge gate

**Checkpoint**: The `archive` group exists, and Stories 1, 2, and 3 can begin.

---

## Phase 3: User Story 1 - A forced removal stops when it would delete uncommitted edits or local commits (Priority: P1) 🎯 MVP

**Goal**: A worktree with an uncommitted edit, or a commit on no remote that trunk doesn't hold, refuses removal and prints what it found and the manual route.

**Independent Test**: Make a scratch worktree with a modified tracked file and run `wfctl archive unsaved` on it. It exits 1, the worktree is intact, and the output names the file and prints `git worktree remove` followed by `git branch -D`.

**Verification**:

- Automated: `tests/test_archive_unsaved.py`, edit and merge-check cases
- Manual: none in this phase. The real removal is quickstart step 4, after Story 4.
- Evidence: exit 1 with the file or commit named, and exit 0 with a warning when git can't answer

### Tests for User Story 1 ⚠️

- [x] T006 [US1] In `tests/test_archive_unsaved.py`, add tests that an unstaged edit and a staged edit to a tracked file each make `archive unsaved` exit 1, name the file, print the manual route, and leave the worktree in place (spec US1 scenarios 1 and 2, FR-009, FR-014). Add a test that a failing `git status` prints a warning naming the uncommitted-edit check and lets the command exit 0 (FR-013, research R4).
- [x] T007 [US1] In `tests/test_archive_unsaved.py`, add the merge-check cases from research R3: a commit on no remote that isn't merged refuses and is named as `<short sha> <subject>`; a pushed commit that isn't merged passes; a squash-merged branch whose remote branch was deleted passes; a branch whose merge into trunk would conflict refuses; and with no trunk, the check warns, names itself, and passes (spec US1 scenarios 3 - 6, FR-010 - FR-013).

### Implementation for User Story 1

- [x] T008 [US1] Implement the uncommitted-edit half of `_archive.check(worktree, spec_dir)` in `wfctl/_archive.py`, using `git status --porcelain=v1 -z --untracked-files=no`. Any entry goes into `edits`, and a failed command adds a warning instead (research R4). Verify with T006.
- [x] T009 [US1] Implement the merge check in `_archive.check` in `wfctl/_archive.py`: `git rev-list HEAD --not --remotes`, then `git merge-tree --write-tree <trunk> HEAD`, then `git rev-parse <trunk>^{tree}`. Trunk is `_paths.trunk_branch(worktree)`. A conflict or a different tree fills `unmerged`. A None trunk, an older git, or any other failure adds a warning naming the check (research R3). Verify with T007.
- [x] T010 [US1] Make `archive unsaved` in `wfctl/cli.py` run `_archive.check`, print every warning, print all refusals in one stop block through the T004 helper, and exit 1 when `edits` or `unmerged` is non-empty and 0 otherwise (contracts/cli.md). Verify with T006 and T007 through `CliRunner`.
- [x] T011 [US1] Validate User Story 1 with `uv run pytest tests/test_archive_unsaved.py -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: `archive unsaved` refuses every case Story 1 names.

---

## Phase 4: User Story 2 - Untracked files are saved where you can copy them back (Priority: P1)

**Goal**: On an otherwise clean worktree, every untracked file is copied to `<state dir>/unsaved/` at its original relative path, and the output lists what was saved.

**Independent Test**: Make a scratch worktree with an untracked `src/new_module.py` and run `wfctl archive unsaved`. The file appears at `<state dir>/unsaved/src/new_module.py` with the same bytes, and the command exits 0.

**Verification**:

- Automated: `tests/test_archive_unsaved.py`, save cases
- Manual: none in this phase
- Evidence: byte-identical files under `unsaved/`, and no `unsaved/` or `unsaved.staging/` left behind after a failed copy

### Tests for User Story 2 ⚠️

- [x] T012 [US2] In `tests/test_archive_unsaved.py`, add the save cases from plan.md: an untracked file lands at the same relative path, byte for byte; a nested repository is copied whole with its `.git`; a symlink is copied as a link with the same target; the spec dir is never saved, even when it isn't ignored; an earlier `unsaved/` is moved aside under a timestamp; a failed copy raises `SaveFailed` and leaves no `unsaved/` or staging folder; nothing to save creates no folder; the output prints 20 paths and then `and N more`; and a worktree with both an untracked file and an uncommitted edit refuses and copies nothing (spec US2 scenarios 1 - 5, FR-015, FR-018 - FR-023).

### Implementation for User Story 2

- [x] T013 [US2] Fill `untracked` in `_archive.check` in `wfctl/_archive.py` from `git ls-files --others --exclude-standard -z`, dropping anything under the spec dir (research R5, FR-018). Verify with the spec-dir case in T012.
- [x] T014 [US2] Implement `_archive.save(check, state_dir, extra)` in `wfctl/_archive.py`. Clear a stale `unsaved.staging/` first, copy files with `shutil.copy2`, recreate symlinks with `os.readlink` and `os.symlink`, and copy folders, including `extra` and nested repositories, with `shutil.copytree(symlinks=True)`. When the copy is complete, rename an existing `unsaved/` to `unsaved-<UTC timestamp with microseconds>` and the staging folder to `unsaved/`. Any exception removes the staging folder and raises `SaveFailed`. Carry over the comments from the current `_archive.archive` that explain this pattern (research R5, FR-019 - FR-022). Verify with T012.
- [x] T015 [US2] Build `SavedResult.files` in `wfctl/_archive.py` by walking the finished staging folder, relative and sorted, and return None when there is nothing to save (data-model.md, FR-022). Verify with the count and 20-path cases in T012.
- [x] T016 [US2] Make `archive unsaved` in `wfctl/cli.py` call `_archive.save` after a passing check. Print `✓ saved N files → <dest>`, the first 20 paths, and `and N more` when there are more, or `ℹ no unsaved files to keep`. On `SaveFailed`, print `✗ couldn't save unsaved files (<cause>) — removal stopped, nothing lost` with the manual route and exit 1 (contracts/cli.md, FR-023). Verify with T012 through `CliRunner`.
- [x] T017 [US2] Validate User Story 2 with `uv run pytest tests/test_archive_unsaved.py -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: `archive unsaved` checks and saves on its own, which is everything except the spec files and the hook.

---

## Phase 5: User Story 3 - Spec files inside the worktree are copied to the spec dir (Priority: P2)

**Goal**: In the default layout, `wfctl store specs` copies the branch's spec files to the main checkout's spec dir, refuses when the destination differs, and reports a result the hook can read.

**Independent Test**: In a repository with `specs/` inside the worktree, write a `spec.md` for the branch and run `wfctl store specs`. The file appears in the main checkout's spec dir, and the output says it was copied and that nothing backs the copy up.

**Verification**:

- Automated: `tests/test_copy_out.py`, `tests/test_spec_store.py`, and the `is_main_checkout` cases in `tests/test_paths.py`
- Manual: none in this phase
- Evidence: the exit code and `stops_removal` for every outcome in data-model.md

### Tests for User Story 3 ⚠️

- [x] T018 [P] [US3] Create `tests/test_copy_out.py`: a missing file is copied and an identical one is left alone; a differing file refuses with its diff and nothing is written; `--overwrite` replaces only the differing files; a file only in the destination is untouched, with and without `--overwrite`; a non-UTF-8 file reports `binary file differs`; and a copy that raises returns `copy_failed` (research R6, FR-024 - FR-028).
- [x] T019 [P] [US3] Create `tests/test_spec_store.py`: `stops_removal` and `exit_code` for every outcome, inside and outside the worktree; `not_applicable` inside the worktree stops removal and still exits 0 by hand; the main checkout reads `not_applicable` and a bare layout reads `to_unsaved`; `copied` prints `nothing backs this copy up`; and no outcome's lines contain "durable" (research R7, FR-029 - FR-032, SC-006). Include `CliRunner` cases for `wfctl store specs` and `--overwrite` against contracts/cli.md.
- [x] T020 [P] [US3] In `tests/test_paths.py`, add tests that `_paths.is_main_checkout` is true in the main checkout and false in a linked worktree and in a bare layout.

### Implementation for User Story 3

- [x] T021 [P] [US3] Create `wfctl/_copy_out.py` with `plan(source, dest)`, which returns `missing`, `same`, and `different` with a `difflib.unified_diff` per differing file, destination first, and `apply(plan, overwrite)`, which copies with `shutil.copy2` and raises on failure (research R6, data-model.md). Verify with T018.
- [x] T022 [P] [US3] Add `is_main_checkout(repo_root)` to `wfctl/_paths.py`, using `git rev-parse --git-common-dir` compared with the worktree's own `.git` (data-model.md). Verify with T020.
- [x] T023 [US3] Create `wfctl/_spec_store.py` with `StoreResult` (`outcome`, `spec_dir`, `inside`, `lines`, and the `stops_removal` and `exit_code` properties) and `store(worktree, branch, overwrite)`, returning `copied`, `already_copied`, `differs`, `copy_failed`, `to_unsaved`, `not_applicable`, or `no_spec_dir` with the lines data-model.md gives. Keep the file to the result type and the dispatch, since #359 meets it as an add/add conflict (research R1, R7). Depends on T021 and T022. Verify with T019.
- [x] T024 [US3] In `wfctl/cli.py`, add a `store_app` typer group registered as `store`, and `store specs [--overwrite]`, which prints `StoreResult.lines` and exits with `exit_code` (contracts/cli.md). Verify with the `CliRunner` cases in T019.
- [x] T025 [US3] Validate User Story 3 with `uv run pytest tests/test_copy_out.py tests/test_spec_store.py tests/test_paths.py -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: `store specs` works by hand, and its result says whether a removal stops.

---

## Phase 6: User Story 4 - Existing repositories get the new behavior without editing their hook (Priority: P2)

**Goal**: `wfctl hook worktree-remove` runs every check, then the store, then the save. `archive-specs` and `archive-story` run the same function, the seeded template calls the new command, and the old archive code is gone.

**Independent Test**: Run `wfctl archive-specs <worktree> <handle>` on a scratch worktree with an untracked file and an uncommitted edit. The result is the same as running `wfctl hook worktree-remove` on it.

**Verification**:

- Automated: `tests/test_worktree_remove.py` and `tests/test_workmux.py`
- Manual: quickstart steps 1 and 3, and step 4 with Andre
- Evidence: the same output and exit code from all three command names on the same fixture, and a template `pre_remove` block with no `|| true`

### Tests for User Story 4 ⚠️

- [x] T026 [US4] Create `tests/test_worktree_remove.py` with the cases from plan.md: a clean worktree with untracked files copies the spec files out, writes `unsaved/`, and exits 0; differing spec files and an uncommitted edit are both listed, nothing is copied, exit is 1, and both routes are printed; a refusal from either check copies no spec files (FR-002); the bare layout saves the spec dir under `unsaved/`; `archive-specs` and `worktree-remove` give the same result on the same fixture and `archive-specs` prints no notice; `archive-story` prints its notice and still works; an unexpected exception warns and exits 0; a numbered archive written by an earlier removal is left where it was (FR-033); and `wfctl --help` lists neither alias while `wfctl hook --help` lists `worktree-remove` (FR-001 - FR-005, FR-008).
- [x] T027 [P] [US4] In `tests/test_workmux.py`, add tests that the template's `pre_remove` block contains `REMOVE_HOOK` with no `|| true`, and that `pre_remove_wired` accepts `hook worktree-remove`, `archive-specs`, and `archive-story` (FR-006, FR-007).

### Implementation for User Story 4

- [x] T028 [US4] Add `worktree-remove` to `hook_app` in `wfctl/cli.py`, taking `[WORKTREE] [HANDLE]` with the `$WM_WORKTREE_PATH` and `$WM_HANDLE` defaults. Phase 1 resolves the spec dir and layout, plans the copy-out, and runs `_archive.check`, then prints every refusal in one stop block, adding the `Keep the worktree's spec files` route only when spec files differ. Phase 2 runs `store()`, reads `stops_removal` and never `exit_code`, and then runs `_archive.save`, passing the spec dir as `extra` on `to_unsaved`. Any other exception prints `⚠ worktree-remove failed (<error>) — continuing so the removal is not blocked` and exits 0. Don't route it through `_entry.py`'s fast path (research R2, R7, R8). Verify with T026.
- [x] T029 [US4] Register the same function on the top-level app as hidden `archive-specs`, with no notice, and hidden `archive-story`, with the notice from contracts/cli.md that names `wfctl hook worktree-remove` (FR-004, FR-005). Delete `archive_specs_cmd`. Verify with the alias cases in T026.
- [x] T030 [US4] In the same commit as T028 and T029, delete `_SPEC_MAP`, `_render_index`, `_plan`, `archive`, `_LEGACY_DEST_PREFIX`, and `ArchiveIncomplete` from `wfctl/_archive.py`, keeping `is_inside`. Move the still-relevant cases from `tests/test_archive_specs.py` (escape routes with spaces and markup, explicit arguments over the environment, former-name dispatch) into `tests/test_worktree_remove.py`, and delete `tests/test_archive_specs.py` (research R11, FR-033, FR-035). Verify with `uv run pytest -q`.
- [x] T031 [US4] Widen `hook_app`'s help text in `wfctl/cli.py` to describe hooks that agent settings and workmux call (FR-008). Verify with the help case in T026.
- [x] T032 [US4] In `wfctl/_workmux.py`, rename `ARCHIVE_HOOK` to `REMOVE_HOOK`, change its command to `wfctl hook worktree-remove "$WM_WORKTREE_PATH" "$WM_HANDLE"` and its fallback warning to say unsaved work was not saved, and make `pre_remove_wired` accept all three names. Replace the `pre_remove` entry in `wfctl/agents/configs/workmux/.workmux.yaml` with the `REMOVE_HOOK` block, with no `|| true` (research R9). Rewrite the comment above that entry, which says a teardown hook must never stop a removal, so it describes the stops this feature adds. Make the same correction to the `pre_remove` comment in this repository's `.workmux.yaml`, which calls the hook a forensic snapshot, and leave its command line unchanged (SC-005). Verify with T027, and by reading both comments against contracts/cli.md.
- [x] T033 [US4] In `wfctl/cli.py`, make `_check_workmux_hook` name `wfctl hook worktree-remove` in its warning, and make `_archive_destination` point at `unsaved/` (research R9). Verify with `uv run pytest tests/test_workmux.py -q` and the existing doctor tests.
- [x] T034 [US4] Validate User Story 4 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: A removal through either hook line runs the new behavior, and nothing writes the numbered archive.

---

## Phase 7: User Story 5 - A repository can name ignored folders worth keeping (Priority: P3)

**Goal**: Folders listed under `save_on_remove` in `wfctl.json` are copied to `unsaved/`, and `check config` reports entries that can't be used.

**Independent Test**: Add `"save_on_remove": ["notes/"]` to `wfctl.json`, write a file under a gitignored `notes/` in a scratch worktree, and run the removal hook. The file appears under `unsaved/notes/`, and `.venv/` does not.

**Verification**:

- Automated: `tests/test_archive_unsaved.py` folder cases, and `save_on_remove` findings in `tests/test_paths.py`
- Manual: quickstart step 2
- Evidence: `unsaved/notes/` present and `unsaved/.venv/` absent, and a `check config` finding for an entry outside the repository

### Tests for User Story 5 ⚠️

- [x] T035 [P] [US5] In `tests/test_archive_unsaved.py`, add tests that a `save_on_remove` folder is copied and an unlisted ignored folder is not, that a listed folder that doesn't exist is skipped without a warning, and that an entry outside the repository is skipped with a warning (spec US5 scenarios 1 - 3, FR-016, FR-017).
- [x] T036 [P] [US5] In `tests/test_paths.py`, beside the trunk findings, add `check config` tests for an absolute entry, an entry resolving outside the repository, a non-string or empty entry, and a key that isn't a list, and a test that a missing folder is not a finding (FR-034).

### Implementation for User Story 5

- [x] T037 [US5] Add `declared_folders(repo_root)` to `wfctl/_archive.py`, returning the usable folders and a list of problems, the same shape as `_paths.declared_trunk` (research R10). Verify with T036.
- [x] T038 [US5] Add the `declared_folders` problems to `check_config_cmd` in `wfctl/cli.py`, worded as contracts/cli.md shows (FR-034). Verify with T036.
- [x] T039 [US5] In `_archive.check` in `wfctl/_archive.py`, read the worktree's own `wfctl.json` through `declared_folders`, put existing folders in `folders`, and put each problem in `warnings`. `_archive.save` already copies folders from T014 (research R5, R10). Verify with T035.
- [x] T040 [US5] Validate User Story 5 with `uv run pytest tests/test_archive_unsaved.py tests/test_paths.py -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: All five stories work.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [x] T041 [P] In `docs/reference.md`, replace the `archive-specs` row with rows for `hook worktree-remove`, `archive unsaved`, and `store specs` (research R11). Verify by reading the rendered table.
- [x] T042 [P] In `docs/ponytail-debt.md`, mark row 6 (the `.agent/` rescue) resolved and update row 5 (the `archive-story` alias) to point at the new notice (research R11). Also remove the inventory row for `_archive._plan`, which T030 deletes, and update the line locations in the `_FORMER_ARCHIVE_COMMAND` row and in rows 5 and 6. Verify by reading every row that names `_archive` or `archive-story` against `wfctl/cli.py` and `wfctl/_archive.py`.
- [x] T043 [P] Remove the comment in `wfctl/_completion.py` that says `_archive._SPEC_MAP` keeps its own copy of a path. Verify with `grep -n _SPEC_MAP wfctl/` returning nothing.
- [x] T044 Check whether #359 has merged into `main`. If it has, merge `main` in, resolve `wfctl/_spec_store.py` and the `store` group in `wfctl/cli.py`, and run the three checks in research R12: `store()` runs the copy-out before `not_applicable` for a spec dir inside a worktree with a main checkout, the hook reads `stops_removal` and never `exit_code`, and #359's removal tests start from a clean worktree. Verify with `uv run pytest -q`.
- [x] T045 Run the definition of done: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, then `uv run wfctl doctor` and `uv run wfctl check config` — merge gate
- [x] T046 Run quickstart.md steps 1 - 3 and record what each printed.
- [ ] T047 Hand quickstart.md step 4, the real forced removal, to Andre before the change is opened for review. It is the only check of whether workmux 0.1.268 still runs `pre_remove` under `--force`, and if it doesn't, the feature needs a different trigger (plan Risks).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup. Blocks Stories 1, 2, and 5.
- **Story 1 (Phase 3)**: Depends on Foundational.
- **Story 2 (Phase 4)**: Depends on Story 1, because both write `_archive.check` and `tests/test_archive_unsaved.py`, and scenario 5 needs the edit check.
- **Story 3 (Phase 5)**: Depends on Setup only. Its files are new apart from the `store` group in `wfctl/cli.py`.
- **Story 4 (Phase 6)**: Depends on Stories 1, 2, and 3, since the hook composes all three.
- **Story 5 (Phase 7)**: Depends on Story 2, since it fills `folders`, which `save` copies.
- **Polish (Phase 8)**: Depends on every story.

### Within Each Story

- Tests are written first and fail before the code exists.
- Data and helpers come before the command that prints them.
- Each phase ends at its merge gate.

### Parallel Opportunities

- Story 3 can run beside Stories 1 and 2, since it lives in `_copy_out.py`, `_spec_store.py`, and their own test files. The one shared file is `wfctl/cli.py`, where Story 3 adds the `store` group and Stories 1 and 2 edit the `archive` group.
- Inside Story 3, T018, T019, and T020 can run together, and so can T021 and T022.
- T027 can run beside T026.
- T035 and T036 can run together.
- T041, T042, and T043 can run together.

## Parallel Example: User Story 3

```bash
Task: "Create tests/test_copy_out.py"                      # T018
Task: "Create tests/test_spec_store.py"                    # T019
Task: "Add is_main_checkout tests to tests/test_paths.py"  # T020

Task: "Create wfctl/_copy_out.py"                          # T021
Task: "Add is_main_checkout to wfctl/_paths.py"            # T022
```

## Implementation Strategy

### MVP

Stories 1 and 2 together are the smallest useful slice, since they are the
losses with no protection today. They don't reach a real removal until Story 4
wires the hook, so in practice the first change that helps anyone is Stories 1 -
4 together.

### Incremental Delivery

1. Setup and Foundational, then Story 1, then Story 2. `archive unsaved` works by hand.
2. Story 3, which can run alongside. `store specs` works by hand.
3. Story 4. The hook runs both, and both live repositories pick it up through `archive-specs`.
4. Story 5. Listed ignored folders are saved.
5. Polish, then quickstart step 4 with Andre.

The plan deletes `archive_specs_cmd` and the numbered archive in the same commit
that adds the hook (T028 - T030), so Story 4 can't be split across two changes
without a window in which the removal hook calls a command that doesn't exist.

## Notes

- [P] tasks touch different files and depend on no incomplete task.
- Commit after each task or logical group, except T028 - T030, which are one commit.
- Run every check through `uv run`, as AGENTS.md requires.
