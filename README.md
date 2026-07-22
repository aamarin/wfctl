# wfctl

Workflow state CLI for AI agent session and pipeline tracking.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

wfctl manages session and pipeline state for AI coding agents (Claude Code, Codex, Copilot). It tracks where you are in a feature development pipeline — specify → plan → implement → verify — and tells the agent what to do next.

## Why wfctl (spec-driven development)

wfctl operationalizes spec-driven development — keeping agents on the specify → plan → implement track instead of jumping straight to code:

- **Persistent by design** — session state on disk; step recoverable even if lost
- **Truth from artifacts** — step read from real spec files, so phases can't be faked or skipped
- **Enforced order** — always points to the next required step, blocking code before spec and plan
- **Scope-aware** — tracks your position in the pipeline
- **Ships with skills** — installs spec-kit skills + slash commands into the project

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Git

## Installation

```bash
# Recommended: uv tool (isolated, always up-to-date)
uv tool install git+https://github.com/aamarin/wfctl.git

# Upgrade an existing install
uv tool install --upgrade git+https://github.com/aamarin/wfctl.git

# Or pip
pip install git+https://github.com/aamarin/wfctl.git
```

Installs from the default branch, which always tracks the latest release. Append
`@<tag>` to either command if you need to pin a fixed version.

## Quickstart

```bash
# Start a session in the current git worktree
wfctl start

# Check pipeline progress
wfctl status

# Install wf-skills (agent skills + slash commands) into your project
wfctl install-skills

# Resume: re-infer pipeline step, write next-step.md
wfctl resume

# End the session
wfctl end
```

## How it works

wfctl is driven by your coding agent, not typed by hand. You install a set of
skills and slash commands into the repo once, then the agent runs the
spec-driven pipeline while wfctl tracks position and enforces order.

**One-time setup, per repo:**

```bash
wfctl install-skills           # skills + /speckit.* commands + the .specify/ runtime
wfctl install-config workmux   # optional: isolated worktree envs (see below)
```

**Then, inside your agent (e.g. Claude Code), drive the pipeline** with slash
commands:

```
/speckit.specify  "add manual transaction entry"   # write the spec
/speckit.plan                                       # design the implementation
/speckit.tasks                                      # break into ordered tasks
/speckit.implement                                  # build it
```

Each step reads and writes real files under `specs/<branch>/` (`spec.md`,
`plan.md`, `tasks.md`), so `wfctl status` infers where you are from artifacts on
disk — a step can't be faked or skipped. `wfctl resume` (or `/speckit.orchestrate`)
re-infers the current step and tells the agent the next command to run.

The pipeline, in order (not every step is required for every change — `wfctl
status` shows which are done):

| Step | Slash command | Produces |
|------|---------------|----------|
| specify | `/speckit.specify` | `specs/<branch>/spec.md` |
| clarify | `/speckit.clarify` | resolved ambiguities in the spec |
| plan | `/speckit.plan` | `plan.md` |
| tasks | `/speckit.tasks` | `tasks.md` |
| analyze | `/speckit.analyze` | cross-artifact consistency check |
| decompose | `/speckit.decompose` | PR / issue breakdown |
| implement | `/speckit.implement` | the code |

A `brainstorm` step (via the brainstorming skill) can precede `specify` for
fuzzy ideas.

### What lands in your repo

After `install-skills` (and optionally `install-config`):

| Path | What | Committed? |
|------|------|------------|
| `.agents/skills/`, `.claude/commands/` | installed skills + `/speckit.*` slash commands | no (gitignored) |
| `.specify/` | speckit runtime (scripts + templates the skills call) | no (gitignored) |
| `.wf-skills-manifest.json` | install record: pinned commit + backups | no (gitignored) |
| `specs/<branch>/` | your `spec.md` / `plan.md` / `tasks.md` | **yes** |
| `.workmux.yaml` | worktree config, from `install-config workmux` | **yes** |

The gitignored paths are install artifacts — regenerate them any time with
`install-skills`. Only your specs and `.workmux.yaml` are project source.

## Commands

| Command          | Description                                                              |
|------------------|--------------------------------------------------------------------------|
| `start`          | Initialize agent session context (idempotent)                            |
| `status`         | Show pipeline progress inferred from spec artifacts                      |
| `resume`         | Re-infer step from filesystem, write `next-step.md`, print current state |
| `next`           | Write next actionable step to `next-step.md` (automation shortcut)       |
| `end`            | End the current session and write summary scaffold                       |
| `checkpoint`     | Save a numbered checkpoint artifact (diff + md)                          |
| `log`            | Print color-coded event timeline for the current session                 |
| `state-dir`      | Print the active XDG state directory path                                |
| `feature-paths`  | Print the active feature's `spec.md`/`plan.md`/`tasks.md` paths (used by the installed speckit scripts) |
| `promote`        | Interactively promote memory candidates to permanent memory              |
| `issue`          | Run the active issue tracker for a verb (`list`/`view`/`close`/`comment`/`create`/`label`) |
| `change`         | List/view code changes — GitHub PRs, Gerrit patchsets — via the tracker's `changes` backend |
| `install-skills` | Clone wf-skills and copy skills + commands + the speckit `.specify/` runtime into the current project |
| `uninstall-skills` | Remove what `install-skills` installed for `--agent`, restoring anything it overwrote |
| `install-config` | Seed a standardized repo config from wf-skills into the project (v1: `workmux`) |
| `tracker-check`  | Validate a `.agents/trackers/<name>.json` tracker config                 |
| `doctor`         | Check installed wf-skills content against upstream for drift             |

`wfctl --version` prints the installed package version and exits.

## Example Session

```
$ wfctl start
✓ Session started — step: implement, next: /speckit.implement

$ wfctl status
#436  436-manual-transaction-entry
────────────────────────────────────
brainstorm   ●
specify      ●
plan         ●
tasks        ●
implement    ▶  ← current
verify       ○

$ wfctl checkpoint
✓ Checkpoint 1 saved

$ wfctl resume
↺ Resumed — step: implement, next: /speckit.implement (auto: true)

$ wfctl log
2026-07-15 09:12  start       step=implement
2026-07-15 09:14  checkpoint  n=1
2026-07-15 11:03  resume      step=implement  command=/speckit.implement

$ wfctl end
✓ Session ended. Summary written to ~/.local/state/wfctl/.../session-summary.md
```

Install skills into a project:

```
$ wfctl install-skills
✓ Installed 32 item(s) from https://github.com/aamarin/wf-skills@main

$ wfctl install-skills --repo https://github.com/your-org/wf-skills --ref v2.0
✓ Installed 18 item(s) from https://github.com/your-org/wf-skills@v2.0

$ wfctl install-skills --agent bob
✓ Installed 32 item(s) from https://github.com/aamarin/wf-skills@main
```

Defaults to `aamarin/wf-skills@main`. Rerun to update.

`--agent` selects where things land. Skills are agent-agnostic `SKILL.md` files;
only the destination changes:

| `--agent` | Installs |
|-----------|----------|
| `claude` (default) | skills → `.agents/skills/`, command wrappers → `.claude/commands/` |
| `bob` | skills → `.bob/skills/`, command wrappers → `.bob/commands/` (same source content as Claude's) |
| `none` | skills → `.agents/skills/` only |

**Overwrite safety:** if `install-skills` would overwrite a file it didn't
install itself — e.g. hand-authored speckit commands already in the
project — it lists them and asks for confirmation first. Pass `--yes`/`-y`
to skip the prompt (for scripts/CI). Whatever gets overwritten is backed up,
and:

```
$ wfctl uninstall-skills --agent claude
✓ Removed 31 item(s), restored 1 pre-existing file(s) for agent 'claude'
```

removes everything that install added and restores anything it overwrote to
its original content. Files installed fresh (nothing to restore) are just
deleted. State lives in `.wf-skills-manifest.json` and `.wf-skills-backup/` at
the repo root — both are cleaned up once nothing references them.

Known limitation: `--agent claude` and `--agent none` both write skills to
`.agents/skills/`. Installing both in the same repo works, but uninstalling
one will remove skill files the other's bookkeeping still points to — pick
one agent per repo.

`wfctl doctor` is the single "am I current?" check — it reports both the wfctl
tool (installed version vs latest release tag) and the installed skills (pinned
commit vs upstream tip). Colour-coded: **green ✓** current, **cyan ⬆** upgrade
available, **yellow ⚠** warning, **red ✗** error.

```
$ wfctl doctor
⬆ wfctl 0.9.0 → 0.10.0 available
    upgrade: uv tool install --upgrade git+https://github.com/aamarin/wfctl.git
⬆ claude: skills behind — dc24ff7 → 7f1c021
     .agents/skills/end-session/SKILL.md | 76 ++++++++++++++++++++++++++++++++++
    update: wfctl install-skills
```

`install-skills` pins the resolved commit SHA (not just the `--ref` name) so
skills staleness is detectable; the tool check assumes you installed wfctl from
its canonical repo. Exits non-zero when an upgrade is available or a repo is
unreachable — so `wfctl doctor` doubles as a freshness gate in scripts, and the
`start-session` skill runs it so you see freshness every session.

### Seeding project config (`install-config`)

`install-config` drops a standardized config file into your repo, sourced from
the same wf-skills repo. Unlike `install-skills` — a managed mirror it keeps in
sync — this is **seed-once**: the file becomes yours, committed and owned. No
manifest, no drift-check, no uninstall.

```
$ wfctl install-config workmux
✓ Seeded workmux config (1 file(s)) from https://github.com/aamarin/wf-skills@main
```

v1 ships `workmux` — a repo-agnostic [`.workmux.yaml`](https://github.com/aamarin/wf-skills/blob/main/.agents/configs/workmux/.workmux.yaml)
starter (worktrees under `wt/`, session mode, agent + term windows, an
issue-number `pre_create` branch guard; project-specific port/env hooks ship
commented). For `workmux` it also idempotently adds `wt/` to `.gitignore` and
sets the config's `agent:` to the resolved agent — `--agent` if given, else the
agent `install-skills` recorded, else `claude`.

It refuses to overwrite an existing file unless you pass `--force` (the file is
git-tracked, so git is your undo):

```
$ wfctl install-config workmux
✗ Would overwrite existing file(s): .workmux.yaml. Pass --force to overwrite (git is your undo).
```

(**workmux** runs each branch as an isolated git worktree + tmux session, so
agents work in parallel without stepping on each other. The seeded config makes
new worktrees come up ready.)

### Issue trackers

`wfctl issue <verb>` runs your project's issue tracker through a small backend,
so skills can reconcile work against real issues without knowing which tracker
you use:

```
wfctl issue list
wfctl issue view 71
wfctl issue close 71 --comment "Done in abc123"
```

Verbs: `list`, `view`, `close`, `comment`, `create`, `label`. The backend is
chosen at install time (`install-skills --tracker <name>`) and defined by
`.agents/trackers/<name>.json` — a map of verb → command. **GitHub ships built
in** (`--tracker github`, via the `gh` CLI). For anything else — a private
Jira/Linear CLI — author a config with the `scaffold-tracker` skill and validate
it with `wfctl tracker-check <name>`. Non-numeric issue keys (e.g. `PROJ-123`)
are supported via the config's `key_pattern`, which also drives how wfctl maps a
branch to its `specs/` folder.

**Code changes (`wfctl change`)** run through a parallel `changes` section of the
same config, so PRs/patchsets go through one abstraction regardless of forge:

```
wfctl change list        # your open PRs / patchsets
wfctl change view 128    # one change
```
```json
"changes": {
  "list": ["gh", "pr", "list", "--state", "open", "--author", "{me}"],
  "view": ["gh", "pr", "view", "{id}"]
}
```

**Scoping lists to you (`{me}`)** — set a top-level `"identity"` (e.g. `"@me"`, a
username, or an email) and use `{me}` in any command. wfctl substitutes it, so
`list` returns *your* items. Each backend keys on what it needs — GitHub
`--author @me`, Gerrit `owner:self` — configured once per adapter.

### `resume` vs `next`

`resume` is the primary automation entry point: it re-infers the pipeline step
from the filesystem, updates `current.json`, writes `next-step.md`, and logs a
resume event. Use it when returning to a session or when a skill needs to
advance the pipeline.

`next` is a lighter variant that writes `next-step.md` without requiring a prior
`wfctl start`. Useful for one-shot step queries.

Run `wfctl <command> --help` for all options.

## Environment Variables

| Variable                | Description                                                  |
|-------------------------|--------------------------------------------------------------|
| `WFCTL_STATE_DIR`       | Override XDG state directory for the current session         |
| `WFCTL_BRANCH`          | Override branch detection                                    |
| `WFCTL_SPEC_DIR`        | Override spec directory root                                 |
| `WFCTL_REPO_ROOT`       | Override git repo root detection                             |
| `WFCTL_CANDIDATES_FILE` | Override path to `memory-candidates.md`                      |
| `XDG_STATE_HOME`        | Base for XDG state path (default: `~/.local/state`)          |

## Development

```bash
git clone https://github.com/aamarin/wfctl.git
cd wfctl
pip install -e ".[dev]"
pytest
```

## Contributing

Issues and PRs welcome. Please open an issue first for significant changes.

## License

MIT — see [LICENSE](LICENSE).
