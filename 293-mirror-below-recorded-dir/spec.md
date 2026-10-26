# Feature Specification: Mirror below recorded dir

**Feature Branch**: `293-mirror-below-recorded-dir`  
**Created**: 2026-10-07  
**Status**: Draft  
**Input**: User description: "#293 — runtime scripts recorded per file; see design.md in FEATURE_DIR"

## Clarifications

### Session 2026-10-07

- No critical ambiguities detected.

## User Scenarios & Testing _(mandatory)_

wfctl installs three speckit scripts into every repository that uses it, and the
speckit skills run them by path. Each install writes down what it put on disk,
and the next install compares that list against what it is writing now, so a
file that stopped shipping can be reported and removed. Today the scripts are
written down as one folder rather than three files, so that comparison cannot
see a script that stopped shipping. These stories fix that without letting the
fix delete anything wfctl did not write.

### User Story 1 - A script wfctl stops shipping is reported and removed (Priority: P1)

A developer upgrades wfctl to a release that no longer ships one of the
scripts. The next install tells them the script is no longer shipped and still
on disk, and an install with `--prune` removes that one file. Before that
install, `doctor` names the file as one wfctl no longer ships.

**Why this priority**: This is the defect the issue exists for. A consuming
repository keeps executable files wfctl stopped shipping, and every check
reports clean over them.

**Independent Test**: Install into a repository, remove one script from the
bundle, and install again. The install names the script, and an install with
`--prune` deletes it and leaves the other scripts in place.

**Acceptance Scenarios**:

1. **Given** a repository installed with the per-file record, **When** a script
   is dropped from the bundle and the developer runs `install-skills`, **Then**
   the install warns that the script is no longer shipped and still on disk,
   and names it by its full path.
2. **Given** the same repository, **When** the developer runs
   `install-skills --prune`, **Then** the dropped script is deleted and the
   scripts still shipped remain on disk.
3. **Given** a repository whose record names a script the bundle no longer
   ships, **When** the developer runs `doctor` before reinstalling, **Then**
   `doctor` reports the script as no longer shipped and exits 1.

---

### User Story 2 - An existing repository is redone once by hand (Priority: P1)

A developer whose repository was installed by an older wfctl, with the scripts
written down as one folder, upgrades wfctl and redoes the install once:
uninstall every layer, agent layers first, then install again. The three
scripts are on disk afterwards, each recorded by name, and `doctor` is green.

**Why this priority**: Without the redo, the next pruning install deletes the
scripts the speckit skills run. The old folder entry is no longer something the
install writes, so it is reported as dropped, and the prune `/start-session`
runs unattended deletes the folder. The redo is the whole upgrade path; no code
retires the old entry.

**Independent Test**: Build a repository whose record names
`.specify/scripts/bash` as one folder entry. Uninstall and install again, then
check that all three scripts are on disk, the record names each one, and
`doctor` exits 0.

**Acceptance Scenarios**:

1. **Given** a repository whose record names `.specify/scripts/bash` as a
   folder, **When** the developer uninstalls every layer and installs again,
   **Then** all three scripts are on disk, the record names each script and no
   folder, and `doctor` exits 0.
2. **Given** the same repository before the redo, **When** the developer runs
   `doctor`, **Then** it does not report the folder entry as no longer shipped,
   lists the three scripts as not on record and left alone, and exits 0 unless
   something else in the release is behind.
3. **Given** the same repository, not redone, **When** the developer runs
   `install-skills --prune --yes`, **Then** the three scripts are deleted, and a
   second `install-skills` puts them back with each recorded by name. This pins
   the accepted cost and its recovery.

---

### User Story 3 - A developer's own script in the folder is left alone (Priority: P3)

A developer keeps a script of their own in `.specify/scripts/bash/`. No install,
prune, or uninstall deletes it, and `doctor` mentions it only as a path it is
leaving alone.

**Why this priority**: It is the safety property behind the whole change, and
it improves on today, where uninstall deletes the folder with the developer's
script in it. It is P3 because the case is rare and it falls out of User
Story 1's record without extra work.

**Independent Test**: Place an untracked script in the folder of a repository
installed with the per-file record. Run `install-skills --prune`, `doctor`, and
`uninstall-skills`, and check that the script survives all three.

**Acceptance Scenarios**:

1. **Given** an untracked developer script in the folder, **When** the
   developer runs `doctor`, **Then** it names the script as not on record and
   left alone, and exits 0.
2. **Given** the same script, **When** the developer runs
   `install-skills --prune`, **Then** the script remains on disk.
3. **Given** the same script, **When** the developer runs `uninstall-skills`,
   **Then** the three recorded scripts are removed and the developer's script
   remains on disk.
4. **Given** a developer script committed to git in the folder, **When** the
   developer runs `doctor`, **Then** it says nothing about the script.

### Edge Cases

- A repository that is not redone loses the three scripts at its next pruning
  install, and `doctor` does not notice. This is an accepted cost while Andre is
  the only user of wfctl; another install puts them back.
- An older wfctl that installs with `--prune` over the new record deletes the
  three scripts. This is an accepted cost, not a requirement; running the
  current wfctl again puts them back.
- A repository that is not redone and installs over the old record backs up
  wfctl's own three scripts and records a backup on each entry. Every later
  uninstall restores those stale copies. This is an accepted cost while Andre
  is the only user of wfctl.
- A pruning install over the old record deletes the whole scripts folder, so a
  developer's own script in it goes too. This is an accepted cost while Andre is
  the only user of wfctl.
- Uninstalling a repository that still carries the old folder entry and was
  never reinstalled removes the whole folder, as it does today.
- The redo uninstalls the base layer, which deletes the tracker files, and the
  next install fills them from the bundle. A project's edits under
  `.agents/trackers/` are replaced. This is an accepted cost while Andre is the
  only user of wfctl.
- A nested directory added later to the runtime script source would bring back
  a folder entry. A test fails when that happens.
- Skill folders under `.agents/skills/` keep recording each skill as one folder.
  They are out of scope and move to #565.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The install record MUST name each runtime script as its own
  entry, the same way it names each template.
- **FR-002**: An install MUST report a runtime script that a previous install
  recorded and the bundle no longer ships, and `--prune` MUST remove that one
  file.
- **FR-003**: Uninstalling every layer of a repository whose record names the
  scripts folder, then installing again, MUST leave a record that names each
  script and no folder.
- **FR-004**: In a repository that has been redone or freshly installed,
  `install-skills`, `--prune`, and `uninstall-skills` MUST NOT delete a file in
  the scripts folder that the record does not name.
- **FR-005**: `doctor` MUST report a file in the scripts folder that the record
  does not name only as a path it leaves alone, and MUST NOT exit 1 for it.
- **FR-006**: The test suite MUST fail when a runtime script source directory
  contains a subdirectory.
- **FR-007**: The test suite MUST pin the redo from a record that names the
  scripts folder as one entry, through uninstall and install, to all three
  scripts on disk and a clean `doctor`.

## Key Entities _(include if feature involves data)_

- **Install record**: The list of paths each install wrote, kept per layer in
  `.wf-skills-manifest.json`. It is the only evidence wfctl has that it wrote a
  file, and the only basis for deleting one.
- **Folder entry**: A record entry naming a directory rather than a file. After
  this change the runtime scripts produce none; skill folders still do.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A script dropped from the bundle is named by the next install and
  removed by the next pruning install, in 1 run each.
- **SC-002**: A redo of a repository on the old record leaves all 3 scripts on
  disk and `doctor` exiting 0, in 1 uninstall and 1 install.
- **SC-003**: In a repository that has been redone or freshly installed, no
  install, prune, or uninstall deletes an unrecorded file in the scripts folder,
  in any of the scenarios above.
- **SC-004**: The record for a fresh install contains 0 folder entries under
  `.specify/`.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/`
  all pass.
- New tests cover FR-001 through FR-007, each acceptance scenario above that
  names a command, and the redo in FR-007 in particular.
- This worktree's record still names the folder, so it is the live redo case.
  Uninstall every layer with `uv run wfctl`, install again, and check that the
  three scripts are on disk and `uv run wfctl doctor` is green.

## Assumptions

- Pre-specify design context loaded from `design.md` in the feature directory.
- wfctl is installed in a handful of repositories, all Andre's, so the upgrade
  is one manual redo in each and no code retires the old record.
