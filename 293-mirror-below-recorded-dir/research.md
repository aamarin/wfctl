# Research: Mirror below recorded dir

The plan had no open unknowns. Each entry below is a claim the plan rests on,
checked against the code on this branch.

## 1. What each reader of the record does with the old folder entry

- Decision: no reader needs a change; the manual redo removes the entry.
- Rationale: the record's `items` are read in five places. The orphan diff in
  `install_skills_cmd` reports the folder as no longer shipped, and `--prune`
  deletes it, which is the cost the record accepts for a repository not redone.
  The dropped-path check in `_check_abandoned_entries` skips the folder entry,
  since it judges only entries whose parent is in `_planned_dirs()`, and
  `.specify/scripts` is no longer one. `uninstall-skills` removes what the
  record names, which is how the redo clears the entry.
  `_installed_skill_names` reads paths under `.agents/` only.

  The stale `none`-layer cleanup compares every path, not only `.agents/` ones.
  It drops a `none` entry from before the layer split once every path it holds
  is also in base's record. A `none` entry naming `.specify/scripts/bash` would
  then never be dropped, since base no longer records that folder. No such entry
  survives in practice: base recorded `.specify/scripts/bash` from the layer
  split until this change, so any install since the split has already dropped
  it. Only a repository never reinstalled since 2026-08-01 could carry one, and
  the redo removes it.
- Alternatives considered: a guard in the orphan diff that retires the entry
  when the same install wrote files below it. Rejected for the manual redo; see
  the record's Considered.

## 2. How the redo runs

- Decision: uninstall every layer, agent layers first, then install with the
  agent layer named.
- Rationale: `uninstall-skills` warns before removing the base layer while an
  agent layer still reads it, names the agent layers to remove first, and asks
  whether to go on. Removing the agent layers first avoids the question.
  Uninstall restores any backup the old entries carried, and the fresh install
  backs up anything it overwrites that is not on record, so a file a developer
  had before wfctl is kept. One thing is lost: the base uninstall deletes the
  tracker files under `.agents/trackers/`, and the install fills them from the
  bundle, so a project's edits to them are replaced. A project that edited them
  copies them aside before the redo.
- Alternatives considered: deleting the folder by hand. Rejected, since the
  entry stays on record and the next prune deletes the reinstalled scripts.
  Editing the manifest by hand. Rejected as easier to get wrong than two
  commands.

## 3. What `doctor` says before the redo

- Decision: no new check.
- Rationale: `_scanned_dirs` reads `_RUNTIME_TARGETS`, so the scan moves to
  `.specify/scripts/bash` and lists the three scripts in the informational block,
  since only the folder is recorded and `.specify/` is gitignored. That block
  leaves the exit code alone. The redo records the scripts and the block
  clears.
- Alternatives considered: a warning naming the folder entry, which exits 1.
  Dropped with the fuller migration.

## 4. What the test fixtures need

- Decision: tests that touch the runtime scripts add `specify/scripts/bash/*.sh`
  to the autouse `bundle` fixture's root themselves.
- Rationale: the fixture builds only `agents/skills/test-skill` and
  `agents/commands/test-cmd.md`, and the installer skips a missing runtime source
  with a warning. The bundle-shape test reads the real package tree under
  `wfctl/specify/`, since the fixture repoints `BUNDLE_ROOT`.
- Alternatives considered: adding the scripts to the shared fixture. Rejected,
  since every test that does not care would then install them.
