# Runtime scripts recorded per file

## Problem Statement

How might wfctl remove a runtime script it stops shipping, without ever deleting
a file it cannot show it wrote?

wfctl installs three speckit scripts into a consuming repository, under
`.specify/scripts/bash/`. The install record lists that folder as one entry,
while it lists each template beside it by file name. So when a script is dropped
upstream, no entry names it. Nothing reports it, `--prune` has nothing to
remove, and `doctor` reports clean with the stale file still on disk.

## Recommended Direction

The scripts are recorded by file name, the same way the templates are. The
install already compares what it recorded last time against what it is writing
now, and a file on the old list and missing from the new one is a file wfctl
stopped shipping. Recording the scripts by name lets that comparison see them.

A repository installed before the change is redone by hand once: uninstall
every layer, agent layers first, then install again. The old record still names
the `bash` folder and the new plan does not, so an install over it treats the
folder as abandoned, and the prune `/start-session` runs unattended deletes it
along with the scripts that install just wrote. The redo clears the old entry
before that can happen. No code retires it, since wfctl is installed in a
handful of repositories, all Andre's.

## Behavior

Each state renders the string shown, and each string is true in that state.

1. **Upgraded wfctl, old record, not reinstalled yet.** `doctor` reports the
   layer current and names the three scripts in its informational block, exit 0.
   This is true: the bundle hash did not change, and the scripts are not on
   record by name yet.

   ```
   ✓ base: skills current (wfctl <next release>)
   ℹ 3 paths are not on record under a directory wfctl installs into:
       .specify/scripts/bash/check-prerequisites.sh
       .specify/scripts/bash/common.sh
       .specify/scripts/bash/setup-plan.sh
       Left alone — wfctl cannot tell yours from an old leftover.
   ```

2. **Redo: uninstall every layer, then install.** The uninstall removes the old
   folder entry and the folder with it. The install writes the three scripts and
   records each one. `doctor` then reports current with no informational block.

   A repository that is not redone loses the scripts at its next pruning install
   and gets them back at the one after. `doctor` does not notice in between.

3. **A script dropped upstream later.** The install names it and offers
   `--prune`, which removes that one file.

   ```
   ⚠ 1 path a previous install recorded is no longer shipped, and it is still on disk:
       .specify/scripts/bash/old.sh
       Re-run with --prune to delete it, once you've checked nothing needs it.
   ```

4. **A developer's own untracked script in `bash/`.** `doctor` names it in the
   informational block and leaves it alone, exit 0. `uninstall-skills` removes
   only the recorded scripts and leaves it in place, where today it removes the
   whole folder.

5. **A developer's own committed script in `bash/`.** Silent, since tracked
   paths are the repository's own.

## Boundaries and Ownership

The install record owns "did wfctl write this file, and does it still ship it?".
The disk cannot answer it, since a script wfctl dropped and a script a developer
added are the same bytes in `bash/`. The decision is
`docs/architecture/deletion-follows-recorded-files.md`, proposed.

## Structure

Two changes, both in `wfctl/cli.py` and its tests.

1. `_RUNTIME_TARGETS` names `specify/scripts/bash` and `.specify/scripts/bash`,
   so `_plan_source` yields one row per script. `_scanned_dirs` and
   `_planned_dirs` read the same table and move down with it.
2. A test asserts that every runtime source directory holds only files, so a
   nested directory added there later fails the suite instead of bringing the
   folder entry back.

| Checked against the code | Assumed |
|---|---|
| `doctor`'s dropped-path check skips the old `bash` entry, since its parent `.specify/scripts` is no longer in `_planned_dirs()` | |
| The scan lists the scripts as not on record before the redo, since `.specify/` is gitignored and only the folder is recorded | |
| `_remove_recorded` removes a recorded directory whole, which is why a repository not redone loses the scripts at its next prune | |

## Software design decisions

No level-3 record. With the upgrade done by hand, the structure weighed no
credible alternative: the target moves one level down.

## Key Assumptions to Validate

- [ ] The redo is safe end to end. Build a repository whose manifest records
      `.specify/scripts/bash` as a folder, uninstall every layer, install
      again, and check that all three scripts are on disk and `doctor` exits 0.
      Pin it as a test.

## MVP Scope

In: the target change, the runtime-source test, and the redo test.

Out: everything under Not Doing.

## Not Doing (and Why)

- Retiring the old folder entry in code. It needed a guard in the orphan diff
  and a special case in the backup step, kept forever, to spare a manual redo in
  a handful of repositories.
- A full migration of the old record. It smooths over one install in a handful
  of repositories.
- A `doctor` warning before a reinstall. The informational block already names
  the scripts, and the redo clears it.
- Skill folders. They share the same weakness and belong with the install
  revamp, #565.
- A hand-kept list of deprecated files. The record already gives the install
  the old list, and a hand-kept one brings this bug back the first time someone
  forgets to update it.

## Open Questions

None.
