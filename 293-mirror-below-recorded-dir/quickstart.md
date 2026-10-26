# Quickstart: Mirror below recorded dir

These are the checks that show the change works, beyond the test suite.

## 1. This worktree's own redo

This worktree's record still names `.specify/scripts/bash` as a folder, so it is
the redo case.

```bash
uv run wfctl doctor
uv run wfctl uninstall-skills --agent claude
uv run wfctl uninstall-skills
uv run wfctl install-skills --agent claude
ls .specify/scripts/bash
uv run wfctl doctor
```

The first `doctor` lists the three scripts as not on record and left alone.
`ls` shows `check-prerequisites.sh`, `common.sh`, and `setup-plan.sh`. The
second `doctor` is green, with no informational block for the scripts, and
`.wf-skills-manifest.json` names each script and no folder.

A repository that installed over the old record before its redo already holds
backups of the three scripts, and the redo alone does not clear them. The
uninstall moves each backup back over its script, and the next install backs
the restored copy up again. Delete the backups of the three scripts before the
uninstall to break that cycle, and leave anything else in the folder alone:

```bash
rm .wf-skills-backup/.specify/scripts/bash/{check-prerequisites,common,setup-plan}.sh
```

Any other file under `.wf-skills-backup/.specify/scripts/bash/` is a script the
repository had before wfctl, and the uninstall restores it as before.

## 2. A script dropped upstream

In a scratch repository, install, delete one script from a copy of the bundle,
and install again with `--from` that copy. The install names the dropped script
as no longer shipped, and `--prune` removes it alone.

## 3. The definition of done

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
```
