---
status: accepted
---

# `install-skills` is a managed mirror; `install-config` is seed-once

## Context

wfctl writes two kinds of file into a project, and they have opposite lifetimes.
Skills are wfctl's to keep current — a fix should reach every repo. Config files
like `.workmux.yaml` become the repo's own the moment they exist; the next
developer edits them, and wfctl must not undo that.

Treating both the same picks one failure or the other: overwrite always, and
hand-tuned config is destroyed on every install; overwrite never, and a fixed
skill never reaches a repo that already has the broken one.

## Decision

Two install modes, chosen per path rather than per run.

| Mode | Command | Re-run behaviour | Removable |
| --- | --- | --- | --- |
| managed mirror | `install-skills` | rewrites from source, tracked by content hash in `.wf-skills-manifest.json` | yes, `uninstall` |
| seed-once | `install-config` | writes only if absent, then never touches the file again | no |

## Owns truth

For a managed path, wfctl owns the content, and the manifest hash is what
distinguishes wfctl's output from a hand edit.

For a seeded path, the repo owns the file from the moment it is written. wfctl
cannot own it: it has no record of what the repo intended to change, so any
rewrite is a guess that silently discards local intent.

## Considered

- One mode, always overwrite — destroys the hand-tuned config the seed exists to
  start.
- One mode, never overwrite — a corrected skill reaches only fresh installs, so
  every existing repo keeps the bug.
- Three-way merge on every file — needs a stored base version per path, which is
  what the manifest hash deliberately is not. Tracked separately as #85 for the
  narrow case of managing hooks inside a file the consumer owns.

## Consequences

A fix to a seeded template reaches only repos seeded afterwards. That is the
accepted cost of the repo owning the file, not an oversight.

## Log

- 2026-08-28  accepted    — relocated from `AGENTS.md`
