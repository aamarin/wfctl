---
description: 'Task list for #293, runtime scripts recorded per file'
---

# Tasks: Mirror below recorded dir

**Input**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, and
`quickstart.md` in this feature directory
**Prerequisites**: plan.md and spec.md

**Tests**: Every acceptance scenario that names a command has a test, as the
plan's Test Plan maps them, and so do FR-006 and SC-004. The tests come first
and fail before the code change, except the ones for User Stories 2 and 3,
which describe behavior the change produces and so are written against it.

**Organization**: The code change is one entry in `_RUNTIME_TARGETS` and its
comment. Everything else is tests and the manual redo, so the phases below are
mostly test phases grouped by user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

## Design records

`design.md` records no level-3 decision. The level-2 decision this work is
built under is `docs/architecture/deletion-follows-recorded-files.md`, still
proposed. Its Consequences list the costs accepted while Andre is the only user
of wfctl, and no task below adds code to avoid them.

---

## Phase 1: Setup

**Purpose**: Nothing to set up. The project, its dependencies, and its lint and
type checks are already in place.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The autouse `bundle` fixture in `tests/test_install_skills.py`
builds no `specify/` tree, so every test below needs the three scripts added to
it first.

- [x] T001 Add a helper in `tests/test_install_skills.py` that writes the named
      scripts under the fixture bundle's `specify/scripts/bash/`, defaulting to
      `check-prerequisites.sh`, `common.sh`, and `setup-plan.sh`, and a second
      helper that writes a manifest whose base layer records
      `.specify/scripts/bash` as one folder entry, the way a pre-change install
      did; verify with T003 - T013, which use both
- [x] T002 Validate the helpers with `uv run pytest -q tests/test_install_skills.py`
      — merge gate

**Checkpoint**: The fixture bundle can carry the scripts, and a test can build
the old record.

---

## Phase 3: User Story 1 - A script wfctl stops shipping is reported and removed (Priority: P1) 🎯 MVP

**Goal**: A script dropped from the bundle is named by the next install,
removed by `--prune`, and reported by `doctor` beforehand.

**Independent Test**: Install, drop one script from the bundle, install again.
The install names the script, and an install with `--prune` deletes it and
leaves the other two.

**Verification**:

- Automated: T003 - T007 in `tests/test_install_skills.py` and
  `tests/test_bundle.py`
- Manual: `quickstart.md §2`, run at T020
- Evidence: the five tests fail before T008 and pass after it

### Tests for User Story 1 ⚠️

> Write these first, and confirm each fails before T008.

- [x] T003 [US1] Test in `tests/test_install_skills.py` that installing, then
      dropping one script from the bundle and installing again, warns that the
      script is no longer shipped and names it by its full path,
      `.specify/scripts/bash/<name>`. Pin `NO_COLOR`. (US1 scenario 1)
- [x] T004 [US1] Test in `tests/test_install_skills.py` that the same sequence
      with `--prune` deletes the dropped script and leaves the other two on
      disk. (US1 scenario 2)
- [x] T005 [US1] Test in `tests/test_install_skills.py` that `doctor`, run after
      the script is dropped and before reinstalling, reports it as no longer
      shipped and exits 1. Pin `NO_COLOR`. (US1 scenario 3)
- [x] T006 [US1] Test in `tests/test_install_skills.py` that a fresh install's
      manifest records each script by file and has no folder entry under
      `.specify/`, and that in a repository whose `.gitignore` covers nothing
      under `.specify/`, the install writes one ignore line per script and none
      for the folder. (SC-004, and the `.gitignore` change in the plan's
      Summary)
- [x] T007 [P] [US1] Test in `tests/test_bundle.py` that walks every source
      directory `_RUNTIME_TARGETS` names in the real package, not the fixture
      bundle, and asserts each holds only files. The docstring says it fails
      when a nested directory would bring a folder entry back. (FR-006)

### Implementation for User Story 1

- [x] T008 [US1] In `wfctl/cli.py`, change the first `_RUNTIME_TARGETS` entry
      from `("specify/scripts", ".specify/scripts")` to
      `("specify/scripts/bash", ".specify/scripts/bash")`, and extend the
      comment above the table to say why it names `bash/` and not its parent:
      the record has to name each script so a dropped one can be reported and
      removed, and a source that holds a directory records that directory whole.
      Leave `_scanned_dirs` and `_planned_dirs` alone, since they read the same
      table; verify with T003 - T007
- [x] T009 [US1] Validate with `uv run pytest -q tests/test_install_skills.py
      tests/test_bundle.py` — merge gate

**Checkpoint**: A script dropped upstream is reported and pruned.

---

## Phase 4: User Story 2 - An existing repository is redone once by hand (Priority: P1)

**Goal**: The manual redo takes a repository on the old record to the per-file
record, and the accepted cost of skipping it is pinned.

**Independent Test**: Build a repository whose record names
`.specify/scripts/bash` as one folder entry. Uninstall and install again, then
check the three scripts are on disk, the record names each, and `doctor` exits
0.

**Verification**:

- Automated: T010 - T012 in `tests/test_install_skills.py`
- Manual: `quickstart.md §1`, run on this worktree at T019
- Evidence: this worktree's manifest names each script and no folder after the
  redo

### Tests for User Story 2 ⚠️

- [x] T010 [US2] Test in `tests/test_install_skills.py` that a repository on
      the old record, uninstalled and installed again, has all three scripts on
      disk, a record naming each script and no folder, and a `doctor` that exits
      0. (US2 scenario 1, FR-003, FR-007)
- [x] T011 [US2] Test in `tests/test_install_skills.py` that `doctor` on the old
      record reports no dropped path, lists the three scripts as not on record
      and left alone, and exits 0. Pin `NO_COLOR`. (US2 scenario 2)
- [x] T012 [US2] Test in `tests/test_install_skills.py` that
      `install-skills --prune --yes` over the old record deletes the three
      scripts, and that a second install puts them back, recorded per file. The
      docstring says this pins a cost the record accepts, not a behavior anyone
      wants. (US2 scenario 3)
- [x] T013 [US2] Validate with `uv run pytest -q tests/test_install_skills.py`
      — merge gate

**Checkpoint**: The redo works from the old record, and the cost of skipping it
is pinned.

---

## Phase 5: User Story 3 - A developer's own script in the folder is left alone (Priority: P3)

**Goal**: No install, prune, or uninstall deletes a script the record does not
name, once a repository is on the per-file record.

**Independent Test**: Put an untracked script in the folder of a repository
installed with the per-file record. Run `install-skills --prune`, `doctor`, and
`uninstall-skills`, and check it survives all three.

**Verification**:

- Automated: T014 - T018 in `tests/test_install_skills.py`
- Evidence: the developer's script is on disk after every command

### Tests for User Story 3 ⚠️

- [x] T014 [US3] Test in `tests/test_install_skills.py` that `doctor` names an
      untracked developer script in the folder as not on record and left alone,
      and exits 0. Pin `NO_COLOR`. (US3 scenario 1)
- [x] T015 [US3] Test in `tests/test_install_skills.py` that
      `install-skills --prune` leaves the same script on disk. (US3 scenario 2)
- [x] T016 [US3] Test in `tests/test_install_skills.py` that `uninstall-skills`
      removes the three recorded scripts and leaves the developer's script.
      (US3 scenario 3)
- [x] T017 [US3] Test in `tests/test_install_skills.py` that `doctor` says
      nothing about a developer script committed to git in the folder.
      (US3 scenario 4)
- [x] T018 [US3] Validate with `uv run pytest -q tests/test_install_skills.py`
      — merge gate

**Checkpoint**: The developer's script survives every command.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: The checks a green suite does not make, and the definition of done.

- [x] T019 Redo this worktree by hand per `quickstart.md §1`. Before the
      uninstall, look for backups of the three scripts under
      `.wf-skills-backup/.specify/scripts/bash/` and delete only those three if
      present. Confirm the second `doctor` is green and
      `.wf-skills-manifest.json` names each script and no folder
- [x] T020 Run `quickstart.md §2` in a scratch repository: install, drop one
      script from a copy of the bundle, install again with `--from` that copy,
      and confirm `--prune` removes that script alone
- [x] T021 Validate the definition of done with `uv run pytest -q`,
      `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, and
      `uv run wfctl doctor` — merge gate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: Blocks every test below.
- **User Story 1 (Phase 3)**: T003 - T007 are written first and fail; T008
  makes them pass.
- **User Story 2 (Phase 4)** and **User Story 3 (Phase 5)**: Depend on T008,
  since their tests describe the per-file record. They are independent of each
  other.
- **Polish (Phase 6)**: Depends on all three stories. T019 changes this
  worktree's installed skills, so it runs after the suite is green.

### Parallel Opportunities

- T007 is in `tests/test_bundle.py` and can be written beside T003 - T006.
- Phases 4 and 5 can be written in parallel once T008 lands, although both touch
  `tests/test_install_skills.py`, so two agents would conflict on the file.

## Logical PR Boundaries

The whole feature is one pull request. The code change is one line, and every
test either drives it or pins a consequence of it, so no slice is reviewable on
its own.

---

## Parallel Example: User Story 1

```bash
Task: "Test in tests/test_bundle.py that every runtime source holds only files (T007)"
Task: "Tests in tests/test_install_skills.py for US1 scenarios 1 - 3 and SC-004 (T003 - T006)"
```

---

## Implementation Strategy

### MVP First

1. Phase 2, then Phase 3. Stop and confirm a dropped script is reported and
   pruned.
2. Phases 4 and 5 add no code; they pin the redo and the safety property.
3. Phase 6 runs the redo on this worktree and the definition of done.

---

## Notes

- Tests asserting on console output pin `NO_COLOR`, per `tests/conftest.py`.
- Test names are sentences, and each docstring says which failure it catches.
- The record stays proposed until Andre accepts it; no task here accepts it.
