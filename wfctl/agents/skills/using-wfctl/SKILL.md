---
name: using-wfctl
description: Reference for wfctl, the session/pipeline state CLI these skills are built on. Use when you need to call wfctl directly, or aren't sure which subcommand fits — session lifecycle, pipeline status, or installing/removing wf-skills itself.
compatibility: 'Requires wfctl to be installed'
---

# Using wfctl

wfctl tracks agent session and pipeline state for a git worktree. Other
skills already call it for you at the right moments (`start-session` runs
`wfctl start`, `speckit-orchestrate` runs `wfctl status`/`wfctl resume`,
`end-session` runs `wfctl end`) — reach for this skill when you need a
command those don't cover, or when picking the right one isn't obvious.

## Commands

| Command | What it does |
|---------|--------------|
| `wfctl start` | Initialize agent session context for the current worktree. Idempotent; pass `--force` to overwrite existing state. |
| `wfctl status` | Show pipeline progress inferred from spec artifacts on disk. |
| `wfctl resume` | Re-infer the pipeline step from the filesystem, write `next-step.md`, print current state. The thing to run after any spec/plan/tasks artifact changes underneath you. |
| `wfctl next` | Write the next actionable step to `next-step.md` without the full resume output — an automation shortcut. |
| `wfctl end` | End the current session and write a summary scaffold. |
| `wfctl log` | Print the event timeline for the current session. |
| `wfctl state-dir` | Print the active state directory path (XDG-based, outside the repo — session artifacts never touch git). `--branch <name>` prints another branch's, which need not exist or be checked out. |
| `wfctl arch-root` | Print the directory this repo's architecture decision records live under. |
| `wfctl install-skills` | Clone wf-skills and copy skills (+ command wrappers, per `--agent`) into the current project. Lists and confirms before overwriting anything it didn't install itself. |
| `wfctl uninstall-skills` | Remove what `install-skills` put in place for `--agent`, restoring any pre-existing file it had backed up. |

## Where state lives

The state dir (`wfctl state-dir`) is an XDG path outside the repo, not
inside it. It holds `events.jsonl`, `next-step.md` and the session
summaries — the history of what happened and the prose a session left
behind, which is everything about a session that cannot be recomputed.

Where the feature stands is not in there. The pipeline step, the next
command, the issue and the branch are derived from artifacts on every
read, so `wfctl status` is true whatever has happened since the last
command. Nothing needs committing, and running any wfctl command never
touches your git history on its own.

## install-skills / uninstall-skills

These two are the odd ones out — they don't touch session state, they manage
the skill files themselves:

- `install-skills` clones `aamarin/wf-skills` (override with `--repo`/`--ref`)
  and copies its contents in for the target `--agent` (`claude`, `bob`, or
  `none`). If that would overwrite a file it didn't install before — e.g. a
  project's own hand-authored speckit commands — it lists them and asks
  first, unless `--yes`/`-y` is passed.
- `uninstall-skills --agent <agent>` reverses exactly that: deletes what was
  freshly installed, and restores anything overwritten to its original
  content. State for this lives in `.wf-skills-manifest.json` and
  `.wf-skills-backup/` at the repo root, cleaned up once nothing references
  them.
