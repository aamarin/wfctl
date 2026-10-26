# Data Model: Mirror below recorded dir

No schema changes. The install record keeps its shape; what changes is which
paths it holds.

## Install record entry

One entry per path an install wrote, under its layer in
`.wf-skills-manifest.json`: `path`, `backup`, and `orphaned` when an install
stopped shipping it and was not run with `--prune`.

| Path | Before | After |
| --- | --- | --- |
| `.specify/scripts/bash` | one folder entry | not recorded |
| `.specify/scripts/bash/check-prerequisites.sh` | not recorded | one entry |
| `.specify/scripts/bash/common.sh` | not recorded | one entry |
| `.specify/scripts/bash/setup-plan.sh` | not recorded | one entry |

## Lifecycle of the old folder entry

1. The developer uninstalls every layer of a repository whose record names
   `.specify/scripts/bash`. Uninstall removes the folder and the entry.
2. A fresh install writes the three scripts and records each one.

A repository that skips the redo keeps the entry. Its next pruning install
reports the folder as no longer shipped and deletes it, and the install after
that writes and records the scripts again.
