# Feature Specification: Save unsaved work when a worktree is removed

**Feature Branch**: `40-save-uncommitted-on-remove`
**Created**: 2026-10-14
**Status**: Draft
**Input**: User description: "Spec for issue #40 from design.md in the feature dir"

## Clarifications

### Session 2026-10-15

- Q: When removal finds a separate git repository inside the worktree that the worktree's own git doesn't track, what should it do? → A: Copy it whole, history included, to `unsaved/` like any other untracked folder.
- Q: What should removal print about the files it saves? → A: The count, the `unsaved/` folder path, and the first 20 file paths, then how many more there are. A file you didn't expect to be saved, such as an un-ignored `.env`, shows up in the list. The other options were the count and folder only, and every file.
- Q: When removal finds an untracked symlink, should it copy the link or what the link points to? → A: Copy the link itself (FR-019). Following it could copy a large folder, or one outside the worktree, and the target isn't deleted with the worktree anyway.

## User Scenarios & Testing _(mandatory)_

Removing a worktree with `workmux remove --force` deletes everything in it that
was never committed, and workmux deletes the branch too. After this change,
removal either saves that work somewhere you can find it, or stops and tells
you why. Work wfctl can copy safely is copied. Work it shouldn't copy, such as
an edit you forgot to commit, stops the removal so you can deal with it while
it is still in place.

### User Story 1 - A forced removal stops when it would delete uncommitted edits or local commits (Priority: P1)

You run `workmux remove --force` on a worktree you think is finished. It still
has an uncommitted edit to a tracked file, or a commit you never pushed or
merged. Today both are deleted and nothing is printed. After this change, the
removal stops, the worktree stays where it is, and the output names what it
found and how to remove the worktree by hand if you really mean to.

**Why this priority**: This is the loss with no way back. An untracked file
can be copied out, but a forgotten edit or commit is usually work you meant to
finish, and a copy in a folder you never open would hide that from you.

**Independent Test**: Make a scratch worktree with a modified tracked file and
run the removal hook on it. The hook exits non-zero, the worktree is intact,
and the output names the file and prints `git worktree remove` followed by
`git branch -D`.

**Acceptance Scenarios**:

1. **Given** a worktree with an unstaged edit to a tracked file, **When** the
   removal hook runs, **Then** it stops the removal, names the file, and prints
   the manual route.
2. **Given** a worktree with a staged but uncommitted edit, **When** the
   removal hook runs, **Then** it stops the removal the same way.
3. **Given** a branch with a commit that is on no remote branch and isn't
   merged into trunk, **When** the removal hook runs, **Then** it stops the
   removal and names the commit.
4. **Given** a branch whose pull request was squash-merged and whose remote
   branch was deleted, **When** the removal hook runs, **Then** it lets the
   removal go ahead, because merging the branch into trunk would change
   nothing.
5. **Given** a branch whose merge into trunk would conflict, **When** the
   removal hook runs, **Then** it stops the removal, because a conflict means
   trunk doesn't hold the work.
6. **Given** a check that git can't answer, such as a trunk branch that can't
   be resolved, **When** the removal hook runs, **Then** it prints a warning
   naming the check and lets the removal go ahead.

---

### User Story 2 - Untracked files are saved where you can copy them back (Priority: P1)

You created a new module or a scratch notes file and never added it to git.
After this change, a removal that is otherwise clean copies every untracked
file to `unsaved/` in the branch's state dir, at the same relative path it had
in the worktree. Restoring a file is a plain copy back.

**Why this priority**: Untracked files are the most common thing a forced
removal deletes, and the issue was raised after three such files were nearly
lost.

**Independent Test**: Make a scratch worktree with an untracked file at
`src/new_module.py` and run the removal hook. The file appears at
`<state dir>/unsaved/src/new_module.py` with the same content, and the hook
exits 0.

**Acceptance Scenarios**:

1. **Given** a worktree with untracked files, **When** the removal hook runs,
   **Then** each one is copied to `unsaved/` at its original relative path, and
   the output says how many files were saved, where they went, and the first
   20 of their paths.
2. **Given** a worktree with no untracked files and nothing listed under
   `save_on_remove`, **When** the removal hook runs, **Then** no `unsaved/`
   folder is created.
3. **Given** an `unsaved/` folder left by an earlier removal of the same
   branch, **When** the removal hook saves files again, **Then** the earlier
   folder is moved aside under a timestamp and the new copy takes its place.
4. **Given** a copy that fails partway, such as a full disk, **When** the
   removal hook runs, **Then** it stops the removal and leaves no partial
   `unsaved/` folder in place.
5. **Given** a worktree with both untracked files and an uncommitted edit,
   **When** the removal hook runs, **Then** it stops the removal and copies
   nothing, because every check runs before any copy.

---

### User Story 3 - Spec files inside the worktree are copied to the spec dir (Priority: P2)

In a repository that uses the default layout, the branch's spec files live in
`specs/` inside the worktree. After this change, removal copies them to the
branch's spec dir in the main checkout, under their original names, which is
where every other wfctl command looks for them. The numbered archive in the
state dir is no longer written. If the spec dir already holds different files
for the branch, the removal stops and shows the differences, because only you
can know whether the older copy has something the newer one lacks.

**Why this priority**: Spec files already have a rescue today, so this changes
where they go rather than whether they survive. It matters less than the two
stories above, which cover work that has no protection at all.

**Independent Test**: In a repository with `specs/` inside the worktree, write
a `spec.md` for the branch and run `wfctl store specs`. The file appears in the
main checkout's spec dir, and the output says it was copied and that nothing
backs the copy up.

**Acceptance Scenarios**:

1. **Given** spec files inside the worktree and no copy in the main checkout,
   **When** the removal hook runs, **Then** they are copied to the spec dir and
   the removal goes ahead.
2. **Given** a spec dir that already holds identical files, **When** the
   removal hook runs, **Then** nothing is rewritten and the removal goes ahead.
3. **Given** a spec dir that holds a file that differs from the worktree's
   copy, **When** the removal hook runs, **Then** it stops the removal, lists
   each differing file, and shows the diff.
4. **Given** that stop, **When** you run `wfctl store specs --overwrite` by
   hand and then remove the worktree again, **Then** the worktree's copies
   replace the differing files and the removal goes ahead.
5. **Given** a file that exists only in the spec dir, **When** the copy runs,
   with or without `--overwrite`, **Then** that file is left untouched.
6. **Given** a spec dir inside the worktree that the store reports as not
   applicable instead of copying it out, **When** the removal hook runs,
   **Then** it stops the removal, because the worktree holds the only copy.
7. **Given** a repository with no main checkout, as in a bare layout, **When**
   the removal hook runs, **Then** the spec files are copied to `unsaved/`
   with the other unsaved work.

---

### User Story 4 - Existing repositories get the new behavior without editing their hook (Priority: P2)

Every repository that uses wfctl already has a `pre_remove` hook calling
`wfctl archive-specs`, and wfctl can't rewrite that hook once it has entries.
After this change, `archive-specs` is a hidden alias for the new removal
command, `wfctl hook worktree-remove`, so an existing repository gets all of
the above as soon as wfctl is updated. New repositories are seeded with
`wfctl hook worktree-remove` directly.

**Why this priority**: Without it, the feature reaches only repositories seeded
after the release, which today means none of the ones in use.

**Independent Test**: Run `wfctl archive-specs <worktree> <handle>` on a
scratch worktree with an untracked file and an uncommitted edit. The result is
the same as running `wfctl hook worktree-remove` on it.

**Acceptance Scenarios**:

1. **Given** a hook that calls `wfctl archive-specs`, **When** a worktree is
   removed, **Then** both jobs run, exactly as they do through
   `wfctl hook worktree-remove`, and no deprecation warning is printed.
2. **Given** a hook that calls the older `wfctl archive-story` name, **When**
   a worktree is removed, **Then** it still works as it does today.
3. **Given** a newly seeded repository, **When** you read its `.workmux.yaml`,
   **Then** `pre_remove` calls `wfctl hook worktree-remove`, and
   `install-config` reports the hook as wired.
4. **Given** `wfctl --help`, **When** you read it, **Then** `archive-specs` is
   not listed, `wfctl hook --help` lists `worktree-remove`, and
   `wfctl archive --help` lists `unsaved`.

---

### User Story 5 - A repository can name ignored folders worth keeping (Priority: P3)

Some repositories keep notes or research in a gitignored folder. git doesn't
report ignored files, so a removal deletes them without a word. wfctl can't
tell a notes folder from `node_modules/`, since both are just ignored files. So
after this change, a repository lists the folders it wants kept under
`save_on_remove` in `wfctl.json`, and removal copies those folders to
`unsaved/`. Every other ignored file is deleted with the worktree, as it is
today.

**Why this priority**: None of the live worktrees measured on 2026-10-12 held a
real note in an ignored folder, so this protects a case that is possible but
not yet seen.

**Independent Test**: Add `"save_on_remove": ["notes/"]` to `wfctl.json`,
write a file under `notes/` in a scratch worktree where `notes/` is
gitignored, and run the removal hook. The file appears under
`unsaved/notes/`, and `.venv/` does not.

**Acceptance Scenarios**:

1. **Given** `save_on_remove` lists `notes/`, **When** the removal hook runs on
   a worktree holding `notes/`, **Then** the folder is copied to
   `unsaved/notes/`.
2. **Given** an ignored folder that isn't listed, such as `.venv/`, **When**
   the removal hook runs, **Then** it is not copied.
3. **Given** `save_on_remove` lists a folder that doesn't exist in the
   worktree, **When** the removal hook runs, **Then** it skips that folder
   without a warning.
4. **Given** `save_on_remove` lists a path outside the repository, such as
   `../elsewhere` or an absolute path, **When** you run `wfctl check config`,
   **Then** it reports that entry as a finding.

---

### Edge Cases

- A worktree whose branch is kept with `--keep-branch` still stops on unmerged
  commits, because the hook can't see that flag. The manual route works for
  that case too.
- The removal hook runs the installed `wfctl`, not `uv run wfctl`, so removing
  an old worktree doesn't run that branch's old saving code.
- When `wfctl` is not on PATH, the seeded hook prints a warning and lets the
  removal go ahead, as it does today.
- A failed push to a spec store at removal prints the store's output as a
  warning and lets the removal go ahead, because the commit stays in the spec
  store on disk. That half of `store specs` belongs to #359.
- An untracked file inside the spec dir is saved once, by the spec file copy,
  and not again under `unsaved/`.
- An untracked symlink is copied as a link, not followed, so a link to a large
  folder outside the worktree doesn't pull that folder into the state dir.
- A separate git repository inside the worktree, such as a project cloned
  there for reference, is untracked as a single item. It is copied whole,
  history included, so local commits in it survive the removal. With no size
  cap, a large one makes the copy slow.
- A worktree left with a `.agent/` folder from an old wfctl layout gets no
  special handling. If git doesn't ignore it, it is saved to
  `unsaved/.agent/` like any other untracked file.
- Removal no longer prints that the spec dir is "durable" in any layout.

## Requirements _(mandatory)_

### Functional Requirements

**The removal command**

- **FR-001**: wfctl MUST provide `wfctl hook worktree-remove <worktree>
  <handle>`, which runs `wfctl store specs` and then `wfctl archive unsaved`
  for the worktree being removed.
- **FR-002**: `wfctl hook worktree-remove` MUST run every check from both
  commands before it copies anything, so a stopped removal leaves nothing
  half-copied.
- **FR-003**: `wfctl hook worktree-remove` MUST exit non-zero, stopping the
  removal, when `archive unsaved` refuses or when the store's result says the
  removal stops. It MUST decide from the store's result rather than from the
  exit code `store specs` would return when run by hand.
- **FR-004**: `archive-specs` MUST be a hidden alias for
  `wfctl hook worktree-remove`, MUST NOT appear in `wfctl --help`, and MUST NOT
  print a deprecation warning.
- **FR-005**: The hidden `archive-story` alias MUST keep working.
- **FR-006**: The seeded workmux template MUST call
  `wfctl hook worktree-remove "$WM_WORKTREE_PATH" "$WM_HANDLE"` in
  `pre_remove`, inside the existing block that falls back to a warning when
  `wfctl` is not on PATH.
- **FR-007**: The check that reports whether `pre_remove` is wired MUST accept
  `wfctl hook worktree-remove`, `archive-specs`, and `archive-story`.
- **FR-008**: The `hook` group's help text MUST describe workmux hooks as well
  as agent hooks.

**Stopping the removal**

- **FR-009**: `wfctl archive unsaved` MUST stop the removal when a tracked file
  has uncommitted edits, staged or not, and MUST name each file.
- **FR-010**: `wfctl archive unsaved` MUST stop the removal when the branch has
  commits that are on no remote branch and merging the branch into trunk would
  change trunk's tree. It MUST name the commits.
- **FR-011**: The "merged" check MUST treat a merge conflict as changing trunk.
- **FR-012**: Trunk MUST be the branch wfctl already resolves as trunk for
  `wfctl start`.
- **FR-013**: When git can't answer a check, the hook MUST print a warning
  naming the check and let the removal go ahead.
- **FR-014**: Every stop MUST print the manual route: `git worktree remove`
  followed by `git branch -D`. There MUST be no flag or environment variable
  that skips a stop.

**Saving unsaved work**

- **FR-015**: `wfctl archive unsaved` MUST copy every untracked, non-ignored
  file to `unsaved/` in the branch's state dir, at its original path relative
  to the worktree root.
- **FR-016**: `wfctl archive unsaved` MUST copy each folder listed under
  `save_on_remove` in `wfctl.json` to the same `unsaved/` folder, at its
  original relative path, and MUST skip a listed folder that doesn't exist.
- **FR-017**: `wfctl archive unsaved` MUST NOT copy any other ignored file.
- **FR-018**: `wfctl archive unsaved` MUST leave the spec dir out of the files
  it copies, so spec files are not saved twice.
- **FR-019**: `wfctl archive unsaved` MUST copy an untracked symlink as a link
  and MUST NOT follow it.
- **FR-019a**: `wfctl archive unsaved` MUST copy an untracked folder that is
  its own git repository whole, including its history, to `unsaved/` at its
  original relative path.
- **FR-020**: When `unsaved/` already exists for the branch, the earlier folder
  MUST be moved aside under a timestamp before the new copy is put in place.
- **FR-021**: The new copy MUST be written to a staging folder and renamed into
  place only once it is complete. A failed copy MUST stop the removal and
  leave no partial `unsaved/` folder.
- **FR-022**: When nothing needs saving, no `unsaved/` folder MUST be created.
- **FR-023**: The output MUST say how many files were saved and the path of
  the `unsaved/` folder, and list the relative paths of the first 20 saved
  files. When more than 20 were saved, the list MUST end with how many more
  there are, for example "and 34 more".

**Copying spec files out of the worktree**

- **FR-024**: In the default layout, with the spec dir inside the worktree,
  `wfctl store specs` MUST copy the branch's spec files to the branch's spec
  dir in the main checkout, under their original names.
- **FR-025**: The copy MUST leave identical files alone and MUST NOT touch a
  file that exists only in the destination.
- **FR-026**: When the destination holds a file that differs from the
  worktree's copy, `wfctl store specs` MUST refuse, list each differing file,
  and show the diff. Its result MUST say the removal stops.
- **FR-027**: `wfctl store specs --overwrite` MUST replace the differing files
  with the worktree's copies.
- **FR-028**: A failed copy MUST be a refusal whose result says the removal
  stops.
- **FR-029**: Any store result for a spec dir inside the worktree that isn't a
  finished copy-out MUST say the removal stops.
- **FR-030**: `wfctl store specs` run by hand MUST exit 1 for a copy-out
  refusal and exit 0 when it reports a spec dir as not applicable.
- **FR-031**: After a successful copy-out, the output MUST say the spec files
  were copied and that nothing backs the copy up. Removal MUST NOT print
  "durable" in any layout.
- **FR-032**: With no main checkout, the spec files MUST be copied to
  `unsaved/` with the other unsaved work.
- **FR-033**: The numbered archive in the state dir MUST no longer be written.
  Archives written by earlier removals MUST be left where they are.

**Configuration and cleanup**

- **FR-034**: `wfctl check config` MUST report a `save_on_remove` entry that
  is an absolute path or resolves outside the repository. It MUST NOT report a
  listed folder that doesn't exist.
- **FR-035**: The special rescue of a legacy `.agent/` folder, and the notice it
  prints, MUST be removed.

## Key Entities _(include if feature involves data)_

- **`unsaved/` folder**: One per branch, in the branch's state dir. It holds
  untracked files and listed ignored folders at their original relative paths.
  An earlier one is moved aside under a timestamp.
- **`save_on_remove`**: A list of folder paths in `wfctl.json`, relative to the
  repository root, naming ignored folders worth keeping at removal.
- **Store result**: What `store specs` reports for one branch, including
  whether the outcome stops a removal. `wfctl hook worktree-remove` reads it
  instead of an exit code. The type and its outcomes are shared with #359.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: In 100% of forced removals of a worktree with an uncommitted edit
  or an unpushed, unmerged commit, the worktree and branch are still present
  afterwards.
- **SC-002**: In 100% of forced removals of an otherwise clean worktree, every
  untracked file can be restored byte for byte from `unsaved/` with a plain
  copy.
- **SC-003**: Zero files from unlisted ignored folders, such as `.venv/`,
  `build/`, or `node_modules/`, appear in `unsaved/`.
- **SC-004**: A squash-merged branch whose remote branch was deleted is removed
  without a stop, unless trunk has since changed the same lines the branch
  touched. In that case the merge check reports a conflict, the removal stops,
  and the manual route is the way through.
- **SC-005**: Both repositories that use wfctl today get the new behavior with
  zero edits to their `.workmux.yaml`.
- **SC-006**: Zero removal messages contain "durable".

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/`
  all pass.
- An automated test builds a fixture worktree with an untracked file, a
  modified tracked file, an unpushed commit, a listed ignored folder, and an
  unlisted one, and asserts which ones are copied and which ones stop the
  removal.
- Automated tests cover the squash-merge case, the merge-conflict case, a
  check git can't answer, a re-run with an existing `unsaved/`, a failed copy,
  a differing spec dir with and without `--overwrite`, a spec dir reported as
  not applicable, and the seeded template's `pre_remove` line.
- An automated test runs `archive-specs` and `wfctl hook worktree-remove` on
  the same fixture and asserts the same result.
- `uv run wfctl check config` reports a `save_on_remove` entry outside the
  repository.
- Manual, with Andre: install wfctl from this branch with `uv tool install`,
  then run `wm rm --force` on a scratch worktree holding an untracked file, a
  tracked edit, and an unmerged commit. Run it once through the old
  `archive-specs` hook line and once through `wfctl hook worktree-remove`.

## Assumptions

- Pre-specify design context loaded from `specs/40-save-uncommitted-on-remove/design.md`.
- workmux 0.1.268 still runs `pre_remove` under `--force`. This was verified
  only on 0.1.211, and the manual test above checks it.
- workmux doesn't tell the hook whether `--force` or `--keep-branch` was
  passed. If it does, the unpushed-commit check could be skipped under
  `--keep-branch`.
- git is 2.38 or later, which the "merged" check needs. When it isn't, the
  check can't be answered, and the hook warns and goes ahead.
- Nobody calls `archive-specs` from anywhere except the removal hook.
- No size cap is needed, because the untracked sets measured across the live
  worktrees were small.

## Out of Scope

- Saving tracked edits as a patch. Stopping the removal shows you the edit
  while you can still commit it.
- An override for the stops.
- Moving or deleting numbered archives written by earlier removals.
- Committing and pushing spec files in a spec store, which is #359's half of
  `wfctl store specs`.
- A spec dir outside the worktree that is uncommitted or unpushed, which is
  #56.
- Changing workmux's own check, or discouraging `--force`.
