# wfctl

Workflow state CLI for AI agent session and pipeline tracking.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

wfctl manages session and pipeline state for AI coding agents (Claude Code, Codex, Copilot). It tracks where you are in a feature development pipeline — specify → plan → implement → verify — and tells the agent what to do next.

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
| `promote`        | Interactively promote memory candidates to permanent memory              |
| `install-skills` | Clone wf-skills and copy skills + commands into the current project      |

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

Defaults to `aamarin/wf-skills@main`. Files of the same name are overwritten —
rerun to update, but local edits to installed skills are lost. Commit the result
if you want the skills pinned for your team.

`--agent` selects where things land. Skills are agent-agnostic `SKILL.md` files;
only the destination changes:

| `--agent` | Installs |
|-----------|----------|
| `claude` (default) | skills → `.agents/skills/`, command wrappers → `.claude/commands/` |
| `bob` | skills → `.bob/skills/`, command wrappers → `.bob/commands/` |
| `none` | skills → `.agents/skills/` only |

Both Claude and Bob have their own slash-command layer that wraps the shared
skills — `.claude/commands/` and `.bob/commands/` respectively, in each
platform's own frontmatter format.

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
