# Feature Specification: Move the old review scans into their spec folders

**Feature Branch**: `759-move-old-scans`
**Created**: 2026-11-13
**Status**: Draft
**Input**: `design.md` in this folder, written by `/speckit.brainstorm`. Issue #759: "Move the review scans already committed into their spec folders".

## User Scenarios & Testing _(mandatory)_

A review scan records what a clarify, plan review, or analyze step checked and
what it found. Since #598, new review scans are saved in the feature's spec
folder, next to the spec, plan, and tasks they review. The scans written before
#598 are still committed in the code repository, under `<arch-root>/scans/`.
In wfctl that is 114 files from 46 features. pfms has its own set, and its
spec folders are stored in a separate repository, `pfms-specs`.

This feature adds a command, `wfctl store scans`, that moves those old scans
into their spec folders and stores them, in whatever repository it runs in.

## Clarifications

### Session 2026-11-13

- Q: How does the command pick the folder name out of a scan's `Detail` path? → A: It takes the first path segment that starts with an issue key in the repository's tracker format followed by a hyphen, and refuses `..`. Spec folders whose names carry no issue key are out of scope here and tracked in #760.
- Q: When two scans in one run target the same file, which goes first? → A: The command handles scans in ascending issue-number order. In wfctl, `649-plan-review.md` is written first, and `656-plan-review.md` then appends to it with `--append 656-plan-review.md`, all in one run.

### User Story 1 - Move every old review scan in one run (Priority: P1)

A maintainer runs `wfctl store scans` in a repository that still has review
scans committed under its arch root. The command moves each scan to its
feature's spec folder as `scans/<step>.md`, stores the folders it changed, and
deletes the moved scans from the code repository's working tree. The
maintainer commits the deletion and opens a PR.

**Why this priority**: This is the whole feature. Without it, 114 scans in
wfctl stay in a folder nothing writes to anymore, and a reader can't tell which
convention is current.

**Independent Test**: In a test repository with a spec store and three review
scans for two features, run the command and check that each scan is in its
spec folder on the spec store's upstream and is gone from the code
repository's working tree.

**Acceptance Scenarios**:

1. **Given** `docs/architecture/scans/412-clarify.md` whose `Detail` line names
   `…/412-clean-code-skill/spec.md`, **When** the maintainer runs `wfctl store
   scans`, **Then** the spec store holds `412-clean-code-skill/scans/clarify.md`
   with the same content, pushed to its upstream, and the code repository's
   `412-clarify.md` is deleted.
2. **Given** `656-plan-review.md` whose `Detail` line names
   `649-design-checks-by-context`, **When** the command runs, **Then** it
   targets `649-design-checks-by-context/scans/plan-review.md`, not a folder
   starting with `656-`.
3. **Given** `121-clarify.md` whose `Detail` line names no spec folder, and one
   spec folder starting with `121-`, **When** the command runs, **Then** the
   scan moves to that folder.
4. **Given** `650-analyze.md` whose `Detail` line names
   `650-bob-pr-review-guard`, a folder the spec store doesn't have, **When**
   the command runs, **Then** it creates that folder holding only the scan, and
   stores it.
5. **Given** the arch root also holds `424-evaluation.md` and `426-spike.md`,
   **When** the command runs, **Then** both are left untouched.
6. **Given** every scan moved, **When** the command finishes, **Then** it
   prints a table with one row per spec folder, a column for each step
   showing whether that step's scan moved, and a column with the stored
   commit, followed by a one-line summary. It exits 0.

---

### User Story 2 - Decide what happens when a scan is already there (Priority: P2)

Two old scans can target the same file. In wfctl, `656-plan-review.md` is a
re-review of #649's plan, so it targets the file `649-plan-review.md` also
targets. A spec folder can also already hold a scan written after #598. The
command never chooses for the maintainer. It leaves the scan in place, says
which file is in the way, and prints the two commands that settle it.

**Why this priority**: Without it, the command either overwrites a review
silently or leaves a scan nobody decides about. It affects one scan in wfctl,
so it follows story 1.

**Independent Test**: In a test repository where a spec folder already holds
`scans/plan-review.md`, run the command with a second scan targeting it, then
run it again with `--append` and with `--overwrite`.

**Acceptance Scenarios**:

1. **Given** the destination file already exists, **When** the command runs
   with no flag for that scan, **Then** the scan stays in the code repository,
   the destination is unchanged, the output names both files and prints the
   `--append` and `--overwrite` commands for that scan, and the command exits 1.
2. **Given** the same state, **When** the maintainer runs `wfctl store scans
   --append 656-plan-review.md`, **Then** the destination file keeps its
   content and gains the old scan's dated sections at the end, without the old
   scan's title line, and the old scan is deleted once the folder is stored.
3. **Given** the same state, **When** the maintainer runs `wfctl store scans
   --overwrite 656-plan-review.md`, **Then** the destination holds the old
   scan's content, and the old scan is deleted once the folder is stored.
4. **Given** a scan appended this way, **When** `wfctl status` reads that spec
   folder's plan review step, **Then** it finds a `Verdict` line and a coverage
   row, and reads the step as having a scan.

---

### User Story 3 - Nothing is lost when something fails (Priority: P3)

A store can fail, for example when the remote is unreachable. A scan's folder
can be ambiguous. The spec root can be a plain folder inside the code
repository. In each case the command leaves every scan it couldn't finish
in the code repository, says why, and exits 1. A rerun picks up what's left.

A failed store stops storing for the rest of the run. Almost every store
failure, such as an unreachable remote, an unfinished merge, or a held lock,
would fail each folder after it the same way. Carrying on would print the same
failure for every folder, and with a remote that hangs, each one waits up to 60
seconds.

**Why this priority**: The command deletes files, so it must never delete a
scan whose new copy isn't stored. Story 1 can't be trusted without this.

**Independent Test**: In a test repository whose spec store remote is
unreachable, run the command, check that every scan is still in the code
repository, then restore the remote and rerun.

**Acceptance Scenarios**:

1. **Given** the second of three folders fails to store because the remote is
   unreachable, **When** the command runs, **Then** the first folder's scans
   move, the second folder's row shows the store's reason, the third folder's
   row shows it wasn't tried, the scans of the second and third folders stay in
   the code repository, and the command exits 1.
2. **Given** a scan whose `Detail` line names no folder, and its issue number
   matches two spec folders, **When** the command runs, **Then** the scan stays
   and is listed with both folder names, and the command exits 1.
3. **Given** a scan whose `Detail` line names no folder, and no spec folder
   matches its issue number, **When** the command runs, **Then** the scan stays
   and is listed as having no folder, and the command exits 1.
4. **Given** the spec root is inside the code repository, or is not a git
   repository with a branch, **When** the command runs, **Then** it moves
   nothing, prints why, and exits 1.
5. **Given** an earlier run left some scans, **When** the maintainer runs the
   command again after fixing the cause, **Then** it moves the rest, and the
   scans already moved are not touched again.
6. **Given** no review scans remain under the arch root, **When** the command
   runs, **Then** it prints `✓ no review scans in docs/architecture/scans/`
   with the repository's own arch root path, and exits 0.

---

### Edge Cases

- **A spec folder exists on disk but was never stored**, as for six features in
  wfctl (#412, #423, #497, #498, #501, #532). The command writes the scan there,
  and storing the folder stores everything in it, the spec included.
- **A scan names a folder at a path from another machine**, as #650's do. Only
  the folder's name is used, never the rest of the path.
- **The same issue's scans name different folders.** Each scan goes to the
  folder its own `Detail` line names. No scan in wfctl does this today.
- **Two scans in one run target the same file.** The command handles scans in
  ascending issue-number order, so the earlier issue's scan is written first.
  The later scan then meets an existing file and follows the conflict rule in
  FR-007, so `--append` on the later scan settles both in one run.
- **A `--append` or `--overwrite` flag names a file that has no conflict, or
  isn't a review scan.** The command says the flag had nothing to apply to, and
  carries on with the rest.
- **The spec store has another branch's uncommitted files.** The store already
  commits one folder at a time with a pathspec, so those files are left alone,
  as they are for `wfctl store specs`.
- **Scans are in the git index but edited in the working tree.** The command
  moves the working tree's content, since that is what the maintainer sees.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: wfctl MUST provide a `wfctl store scans` command, in the same
  command group as `wfctl store specs` and `wfctl store reviews`.
- **FR-002**: The command MUST treat a file under `<arch-root>/scans/` as a
  review scan only when its name is `<issue>-clarify.md`,
  `<issue>-plan-review.md`, or `<issue>-analyze.md`. It MUST leave every other
  file there untouched, evaluation and spike scans included.
- **FR-003**: The command MUST find a scan's spec folder from its `Detail`
  lines first. The folder is the first segment of the `Detail` path that starts
  with an issue key in the repository's tracker format followed by a hyphen,
  matched the way `extract_issue_key` matches a branch name. The command MUST
  use only that folder's name, never the rest of the path, and MUST NOT accept
  `..` as a folder name. Spec folders whose names carry no issue key are out of
  scope and tracked in #760.
- **FR-004**: When no `Detail` line names a folder, the command MUST fall back
  to the issue number in the file name, and MUST move the scan only when
  exactly one spec folder's name starts with `<issue>-`. Otherwise it MUST
  leave the scan and report why.
- **FR-005**: When a `Detail` line names a folder the spec root doesn't have,
  the command MUST create it.
- **FR-006**: The command MUST write each scan to `<folder>/scans/<step>.md`,
  where `<step>` is `clarify`, `plan-review`, or `analyze`.
- **FR-007**: The command MUST NOT write over an existing destination file
  unless the maintainer named that scan with `--overwrite`. With `--append`, it
  MUST add the old scan's content, less its first heading line, to the end of
  the existing file. Both flags MUST take a scan's file name and MAY be given
  more than once.
- **FR-008**: The command MUST store each folder it wrote to through the same
  spec store code `wfctl store specs` uses, so it works with any spec store a
  repository has configured.
- **FR-009**: The command MUST delete a scan from the code repository's working
  tree only after its folder is stored. It MUST NOT commit in the code
  repository.
- **FR-010**: If the spec root isn't a spec store with a branch, the command
  MUST move nothing and exit 1.
- **FR-014**: After the first folder whose store fails, the command MUST NOT
  try to store any other folder in that run. It MUST keep the scans of every
  folder it didn't store in the code repository, and a rerun MUST store them.
- **FR-011**: The command MUST print one table, grouped by spec folder, with a
  column for each step and a column for the stored commit or the store's
  failure reason, then a summary line with the counts moved, kept, and needing
  a choice, then one block for each scan that needs a choice or couldn't be
  placed.
- **FR-012**: The command MUST exit 0 when every review scan was moved and
  stored, or none were left, and exit 1 otherwise.
- **FR-013**: `scans-live-in-spec-folder` MUST say that the old review scans
  move to their spec folders, and `scans/` MUST stay on
  `_paths.non_record_subtrees`.

### Key Entities

- **Review scan**: a file under `<arch-root>/scans/` named for an issue and a
  review step. Its sections each open with a `Verdict` line and, in most
  scans, a `Detail` line naming the file the review wrote its detail to.
- **Spec folder**: one feature's folder in the spec store, named for its
  branch, such as `649-design-checks-by-context`. A moved scan lands in its
  `scans/` subfolder.
- **Spec store**: the git repository holding every spec folder, with a branch
  and usually an upstream to push to, such as `specs-trunk` in wfctl or the
  `pfms-specs` repository in pfms.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: After the move in wfctl, `docs/architecture/scans/` holds exactly
  three files: `424-evaluation.md`, `571-evaluation.md`, and `426-spike.md`.
- **SC-002**: All 114 of wfctl's review scans are on `origin/specs-trunk`
  under their feature's folder, #656's review included, appended to #649's
  plan review.
- **SC-003**: For three moved scans, including one plan review, `wfctl status`
  pointed at the scan's spec folder reads the scan as present.
- **SC-004**: No run of the command, failed or not, leaves a scan in neither
  the code repository nor a stored spec folder.
- **SC-005**: The same move in pfms needs one command after the release, with
  no pfms-specific code in wfctl.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, with new tests covering every acceptance scenario above
  against a temporary code repository and a temporary spec store with a bare
  remote, the same fixtures the `wfctl store specs` tests use.
- `uv run ruff check wfctl/ tests/` and `uv run mypy`.
- `python3 .github/scripts/check_imports.py`, since the command's module has to
  sit in the right context.
- `uv run wfctl doctor`.
- By hand in wfctl: run `uv run wfctl store scans --append 656-plan-review.md`,
  check SC-001 and SC-002 with `ls docs/architecture/scans` and `git ls-tree
  origin/specs-trunk`, and check SC-003 with `WFCTL_SPEC_DIR` and `wfctl
  status` on `412-clean-code-skill`, `40-save-uncommitted-on-remove`, and
  `649-design-checks-by-context`.

## Assumptions

- Pre-specify design context loaded from `design.md` in this spec folder.
- pfms's review scans use the same file names and `Detail` lines as wfctl's.
  This was checked during plan review: pfms's `dev` branch has 89 review
  scans, and each one
  either names its folder under `pfms-specs/` or falls back to the one folder
  with its issue number.
- Storing 46 folders one at a time, each with its own fetch and push, takes a
  few minutes at most. If it's much slower, the plan can batch the pushes.
- The command is removed in a later release, once pfms has run it. Its removal
  is not part of this feature.
