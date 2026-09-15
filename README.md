# wfctl

Workflow state CLI for AI agent session and pipeline tracking.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

wfctl manages session and pipeline state for AI coding agents (Claude Code, Codex, Copilot). It tracks where you are in a feature development pipeline — brainstorm → specify → clarify → plan → tasks → analyze → decompose → implement — and tells the agent what to do next.

## Why wfctl

wfctl operationalizes spec-driven development — keeping agents on the specify → plan → implement track instead of jumping straight to code:

- **Persistent by design** — session state on disk; step recoverable even if lost
- **Truth from artifacts** — step read from real spec files, not from an agent's report; `implement` additionally gates on a definition of done wfctl runs itself (`wfctl verify`), so "done" is a recorded verdict rather than a claim
- **Enforced order** — always points to the next required step, blocking code before spec and plan
- **Design before spec** — `design-levels` runs design as four gated passes, so who owns what is decided out loud, not buried in code
- **Ships with skills** — installs spec-kit skills + slash commands into the project
- **Accountable outward actions** — issue writes, and any other outward action you record with `wfctl notify` (a push, say), check the same explicit grant and refuse without it ([details](docs/reference.md#outward-facing-authority-notify-blocked))

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

## Quick start

**1. Install wfctl** (see [Installation](#installation) for pip and pinning):

```bash
uv tool install git+https://github.com/aamarin/wfctl.git
```

**2. Install the skills into your project.** Once per repo:

```bash
cd your-project
wfctl install-skills --agent claude   # drop --agent if you are not on Claude Code
```

The first interactive run asks two questions — which issue tracker to wire up,
and where specs should live — and records both, so it never asks again.

**3. Drive the pipeline from inside your agent**, with slash commands:

```
/start-session                                        # session context + freshness check
/speckit.brainstorm  "add manual transaction entry"   # design, gated in four levels
/speckit.specify                                      # turn the design into a spec
/speckit.plan                                         # design the implementation
/speckit.tasks                                        # break into ordered tasks
/speckit.implement                                    # build it
/end-session                                          # summary + memory candidates
```

Anywhere along the way, `wfctl status` shows your position and `wfctl resume`
says what to run next. Those two are the only commands you type by hand often.

## How it works

```mermaid
flowchart LR
    A[["① Install<br/>(once per repo)"]] --> B[["② Drive the pipeline<br/>(every feature)"]] --> C[["③ Open the change<br/>(every PR)"]]
```

You install the skills once per repo (①); everything after that runs from
inside your agent. ② is the mechanism wfctl actually adds: the agent doesn't
get to say where it is — the files on disk do.

```mermaid
flowchart LR
    subgraph Agent["your coding agent"]
        S1["/speckit.brainstorm"] --> S2["/speckit.specify"] --> S3["...plan → tasks → implement"]
    end
    subgraph Disk["specs/&lt;branch&gt;/"]
        F1["design.md"] --> F2["spec.md"] --> F3["...plan.md → tasks.md"]
    end
    Agent -.->|writes specs| Disk
    Agent -.->|writes code| Repo["your repo"]
    Disk -.->|reads| W["wfctl status / resume"]
    W -.->|"next: /speckit.____"| Agent
```

The agent writes artifacts; wfctl reads them back off disk to decide what's
done and what's next. It never takes the agent's word for it. The boxes shown
are spec-driven development specifically — that pipeline is hardcoded into
wfctl today, not configurable. The part that generalizes is the mechanism:
read artifacts, don't trust claims.

Full pipeline model, every command, environment variables, the issue-tracker
and architecture-record machinery, and how `install-skills`/`install-config`
lay files into your repo: **[docs/reference.md](docs/reference.md)**.

## Commands (most used)

| Command | Description |
|---------|-------------|
| `status` | Show pipeline progress inferred from spec artifacts |
| `resume` | Re-infer step from filesystem, write `next-step.md`, print current state |
| `install-skills` | Copy the skills, commands and speckit runtime into the current project |
| `doctor` | Check the installed skills against the ones this wfctl ships |
| `issue` | Run the active issue tracker for a verb (`list`/`view`/`close`/`comment`/…) |
| `change` | List/view/check code changes (PRs, patchsets) via the tracker's `changes` backend |
| `arch context` | Print the in-force architectural contract |

Full command reference, including `notify`/`blocked` and the `arch` lifecycle:
**[docs/reference.md#commands](docs/reference.md#commands)**. That table
summarizes each command; run `wfctl <command> --help` for its flags.

## Development

```bash
git clone https://github.com/aamarin/wfctl.git
cd wfctl
uv run pytest -q
```

Without uv: `pip install -e ".[dev]"` then `pytest`.

The skills, commands and speckit runtime `install-skills` writes are committed
here as package data under `wfctl/agents/` and `wfctl/specify/` — edit them in
place, then `wfctl install-skills` to try them in a repo. They carry no leading
dot on purpose: `.gitignore` ignores `.agents/` and `.specify/` unanchored, so a
dotted vendored copy would be silently untracked. The dotted directories at the
repo root are this repo's own install output, not the source.

See [AGENTS.md](AGENTS.md) for the fuller contributor context — session state,
worktrees, architectural constraints, and release mechanics.

## Contributing

Issues and PRs welcome. Please open an issue first for significant changes.

## License

MIT — see [LICENSE](LICENSE).
