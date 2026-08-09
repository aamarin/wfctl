# Spec: `wfctl install-config` — seed standardized repo config

**Status:** Draft
**Date:** 2026-07-21
**Branch:** install-config-workmux

## Problem

Setting up a repo to run agents in isolated worktrees means hand-writing a
`.workmux.yaml` — worktree naming, tmux window layout, and lifecycle hooks
(`pre_create`/`post_create`). The same conventions get copy-pasted (and drift)
across repos. We want one command to drop a known-good, repo-agnostic
`.workmux.yaml` into a project, sourced from a single canonical copy in
`wf-skills`.

This is **seed config, not a managed mirror.** Unlike skills — which `wfctl
install-skills` copies into gitignored per-agent dirs and keeps in sync via a
manifest — a repo's `.workmux.yaml` is committed and owned by the repo once
seeded. So this command does *not* reuse the install-skills machinery (per-agent
fan-out, manifest, backup, `doctor` drift-check). It seeds once; git is the undo.

## User Scenarios

1. **Fresh repo, no config.** `wfctl install-config workmux` writes
   `.workmux.yaml` at the repo root and ensures `wt/` is in `.gitignore` (the
   worktree dir lives inside the repo). `wm add 359-foo -b` then creates
   `wt/359-foo` with the standard window layout and the issue-number branch
   guard, and git ignores it.
2. **Config already exists.** `.workmux.yaml` is present. The command **refuses**
   with a visible red error naming the file and the `--force` hint; it exits
   non-zero and changes nothing.
3. **Deliberate reseed.** `wfctl install-config workmux --force` overwrites the
   existing `.workmux.yaml`. No backup is written — the file is git-tracked, so
   git is the undo.
4. **Unknown config name.** `wfctl install-config nope` errors, listing the
   available config names (v1: just `workmux`), exit non-zero.
5. **Not in a git repo.** Errors like the other repo-scoped commands, exit
   non-zero.

## Functional Requirements

- **Command:** `wfctl install-config <name> [--force] [--agent NAME] [--repo URL] [--ref REF]`.
  `<name>` is a positional argument so future configs are additive (a new name),
  never a new subcommand. v1 recognizes only `workmux`.
- **Agent substitution (workmux):** the shipped `.workmux.yaml` runs `<agent>` in
  its agent pane. After seeding, wfctl rewrites the `agent:` line to the resolved
  agent: `--agent` if given, else the sole installed agent from the manifest
  (what `install-skills --agent` recorded), else `claude`. So a repo set up for a
  non-default agent gets a matching config without re-specifying it.
- **Source:** `wf-skills` ships `.agents/configs/<name>/`. Installing copies the
  **contents of that directory** into the repo root. A directory (not a single
  file) so a config that later needs sidecar files (e.g. hook scripts) works
  under the same model; `workmux/` contains just `.workmux.yaml` today.
- **Clobber policy:** if *any* destination file already exists, refuse and print
  a red error listing the conflicting path(s) and the `--force` hint; exit 1.
  With `--force`, overwrite. Never write a backup.
- **`.gitignore` (workmux only):** because `worktree_dir: wt` places worktrees
  inside the repo, installing `workmux` also ensures `wt/` is ignored — an
  **idempotent append** of a `wt/` line to `.gitignore` (create the file if
  absent, skip if the line is already present). This is a config-specific
  post-step, not a copied file (so it never trips the clobber rule), and not a
  generic per-config hook framework.
- **No persistence:** no manifest entry, no backup dir, no uninstall, no
  `doctor` integration. The command's only side effect is writing files.
- **Repo/ref:** default to the same wf-skills repo/ref defaults as
  `install-skills`; `--repo`/`--ref` override (so a local checkout can be used,
  as `install-skills` already supports).

## The shipped `workmux/.workmux.yaml`

Repo-agnostic skeleton derived from the PFMS config, with fullstack/PFMS
specifics removed. **Kept** (conventions): `worktree_dir: wt`,
`worktree_naming: full`, `mode: session`, two windows (`agent` with `<agent>`
focused, `term` empty), `agent: claude`, the `pre_create` issue-number branch
guard, `pre_remove: []`. **Removed** (project-specific): `main_branch`/
`base_branch: dev` (let workmux auto-detect), the `deploy` window, and the
`post_create` port/env/db rewrites + `files.copy` (server/client `.env`) — these
become **commented examples** showing where a user's own port/env logic goes.
**Commented, not dropped:** `window_prefix` — the tmux session/window name prefix
is per-project (`pfms__`, `wfctl__`), with no generic way to template the project
name, so it ships as `# window_prefix: "<project>__"` for the user to set.
Omitted, workmux uses its `wm-` default.

The `pre_create` issue-number guard is retained deliberately: it enforces
`359-my-feature` branch names, matching wfctl's own issue-number branch model.

## Out of Scope (deferred)

- **Per-repo customization** of the seeded config beyond "edit it after" or
  `--force` to reseed. Tracked as a follow-up issue; the intended answer is
  "provide your own `.workmux.yaml`."
- **Additional config types** (editorconfig, gitignore, etc.). The positional
  `<name>` leaves room; none ship in v1.
- **Drift-checking / updating** a previously seeded config.

## Testing

- `install-config workmux` into a clean temp repo writes `.workmux.yaml`; content
  matches the shipped source.
- `install-config workmux` ensures `wt/` in `.gitignore`: creates it when absent;
  appends when present without the line; **no duplicate** when the line already
  exists (idempotent).
- Existing `.workmux.yaml` → refuses, exits non-zero, file unchanged, error names
  the path.
- `--force` overwrites an existing file.
- Unknown name → non-zero, lists available names.
- Not-a-git-repo → non-zero.
