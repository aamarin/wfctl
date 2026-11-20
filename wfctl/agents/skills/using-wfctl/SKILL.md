---
name: using-wfctl
description: Reference for wfctl, the session/pipeline state CLI these skills are built on. Use when calling wfctl directly, or when it is unclear which subcommand fits — session lifecycle, pipeline status, or installing/removing wf-skills itself.
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
| `wfctl start` | Initialize agent session context for the current worktree. Idempotent; pass `--force` to overwrite existing state. `--no-auto-approve` does what `wfctl auto-approve off` does. `--auto-approve` is refused, so use `wfctl auto-approve on`. |
| `wfctl auto-approve` | Set where this feature's design approval happens. `wfctl auto-approve on` moves it to the PR: design gates are answered into the record and review stops run through. `wfctl auto-approve off` hands both back to a person. With no argument, it prints the mode and whether this session, another session, or an unknown session last changed it. |
| `wfctl status` | Show pipeline progress inferred from spec artifacts on disk. |
| `wfctl resume` | Re-infer the pipeline step from the filesystem, write `next-step.md`, print current state. The thing to run after any spec/plan/tasks artifact changes underneath you. |
| `wfctl next` | Write the next actionable step to `next-step.md` without the full resume output — an automation shortcut. |
| `wfctl end [--continued]` | End the current session and write a summary scaffold — only if one is not already there; it says which happened and never overwrites. `--continued` records that the work carries on rather than that someone wrapped up, which is what lets the next session on a trunk branch read the handoff instead of asking. |
| `wfctl log` | Print the event timeline for the current session. |
| `wfctl state-dir` | Print the active state directory path (XDG-based, outside the repo — session artifacts never touch git). `--branch <name>` prints another branch's, which need not exist or be checked out. |
| `wfctl arch-root` | Print the directory this repo's architecture decision records live under. |
| `wfctl install-skills` | Clone wf-skills and copy skills (+ command wrappers, per `--agent`) into the current project. Lists and confirms before overwriting anything it didn't install itself. |
| `wfctl uninstall-skills` | Remove what `install-skills` put in place for `--agent`, restoring any pre-existing file it had backed up. |

Run `wfctl auto-approve on` only when a person in this conversation asked for
an unattended run. A worktree created with `WFCTL_AUTO_APPROVE=1` already got
its grant from the creation hook, so the variable is never a reason to run it,
least of all after the review cap turned the mode off. Never turn the mode on
because you judge the work ready to run without a person. wfctl can't tell a
grant someone asked for from one nobody did, so this rule is the only thing
between you and a grant nobody wanted. The `mode` event records which session
made the grant, and the user checks it at the PR. In Claude Code and Codex, the
user also approves a prompt before the command runs. `wfctl auto-approve off`
is always allowed, since it hands the decisions back to a person.

## Where state lives

The state dir (`wfctl state-dir`) is an XDG path outside the repo, not
inside it. It holds `events.jsonl`, `next-step.md`, the session
summaries and `mode.json` — the history of what happened, the prose a
session left behind, and the one choice someone made about this feature.
All of it is what cannot be recomputed.

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
  them. An earlier backup kept beside a newer one of the same path, such as
  `software-design-decisions` beside `software-design-decisions.2`, is not
  cleaned up, and the install that made the second copy lists it.

## install-config

`wfctl install-config <name>` seeds a project config file, such as
`.workmux.yaml`, from the template wfctl ships. It writes the file once and
never updates it. A later change to the template doesn't reach a repository
that was already seeded, since wfctl can't tell a stale copy from one the
repository edited. Running it again with `--force` replaces the file with the
current template, and your edits to it are lost.

So when a template gains something, add it to the repository's file by hand.
For example, `wfctl auto-approve` with no argument prints the `post_create`
line to add when `.workmux.yaml` doesn't have it.
