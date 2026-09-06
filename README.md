# wfctl

Workflow state CLI for AI agent session and pipeline tracking.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

wfctl manages session and pipeline state for AI coding agents (Claude Code, Codex, Copilot). It tracks where you are in a feature development pipeline — design → specify → plan → tasks → implement — and tells the agent what to do next.

## Why wfctl (spec-driven development)

wfctl operationalizes spec-driven development — keeping agents on the specify → plan → implement track instead of jumping straight to code:

- **Persistent by design** — session state on disk; step recoverable even if lost
- **Truth from artifacts** — step read from real spec files, not from an agent's report; `implement` additionally gates on a definition of done wfctl runs itself (`wfctl verify`), so "done" is a recorded verdict rather than a claim
- **Enforced order** — always points to the next required step, blocking code before spec and plan
- **Design before spec** — `design-levels` runs design as four gated passes, so who owns what is decided out loud, not buried in code
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

wfctl is driven by your coding agent, not typed by hand. You install a set of
skills and slash commands into the repo once, then the agent runs the
spec-driven pipeline while wfctl tracks position and enforces order.

Setup is `install-skills` (plus an optional `install-config workmux` for
isolated worktree envs, below); everything after that runs from inside the
agent, as in the quick start above.

Each step reads and writes real files under `specs/<branch>/` (`spec.md`,
`plan.md`, `tasks.md`), so `wfctl status` infers where you are from artifacts on
disk — a step can't be faked or skipped. `wfctl resume` (or `/speckit.orchestrate`)
re-infers the current step and tells the agent the next command to run.

The pipeline, in order (not every step is required for every change — `wfctl
status` shows which are done):

| Step | Slash command | Produces |
|------|---------------|----------|
| brainstorm | `/speckit.brainstorm` | `specs/<branch>/design.md` |
| specify | `/speckit.specify` | `specs/<branch>/spec.md` |
| clarify | `/speckit.clarify` | a `## Clarifications` section in `spec.md` — written on every run, including one that finds nothing to ask, since that section is what marks the step done |
| plan | `/speckit.plan` | `plan.md` |
| tasks | `/speckit.tasks` | `tasks.md` |
| analyze | `/speckit.analyze` | cross-artifact consistency check |
| decompose | `/speckit.decompose` | PR / issue breakdown |
| implement | `/speckit.implement` | the code |

`brainstorm` is where the `design-levels` skill runs, and it is the step most
worth not skipping. It descends four levels — behavior, architecture, data and
ownership, implementation — presenting one per approval instead of a finished
design in one pass, and each has a gate that has to be answered out loud. Level
2 lands in `design.md`'s required **Boundaries and Ownership** section, and
`/speckit.plan`'s Constitution Check verifies it was stated. When a lower level
invalidates a boundary drawn above it, the rule is to go back up, not to work
around it in the spec.

### What lands in your repo

After `install-skills` (and optionally `install-config`):

| Path | What | Committed? |
|------|------|------------|
| `.agents/skills/`, `.agents/commands/` | installed skills + `/speckit.*` command wrappers, agent-agnostic | no (gitignored) |
| `.claude/`, `.bob/`, `.github/skills/` | one assistant's native paths, only if `--agent` asked for them | no (gitignored) |
| `.specify/` | speckit runtime (scripts + templates the skills call) | no (gitignored) |
| `.wf-skills-manifest.json` | install record: wfctl version + content hash + backups | no (gitignored) |
| `specs/<branch>/` | your `spec.md` / `plan.md` / `tasks.md` | your call — see below |
| `.workmux.yaml` | worktree config, from `install-config workmux` | **yes** |
| `.github/pull_request_template.md` | PR template, from `install-config github` | **yes** |

The gitignored paths are install artifacts — regenerate them any time with
`install-skills`. Only your specs and `.workmux.yaml` are project source.

`install-skills` never touches `specs/` either way, so committing it is a
project decision: commit it and the plan is reviewable in the PR, or gitignore
it and only the implementation ships. This repo does the latter.

## Commands

| Command          | Description                                                              |
|------------------|--------------------------------------------------------------------------|
| `start`          | Initialize agent session context (idempotent)                            |
| `status`         | Show pipeline progress inferred from spec artifacts                      |
| `resume`         | Re-infer step from filesystem, write `next-step.md`, print current state |
| `next`           | Write next actionable step to `next-step.md` (automation shortcut)       |
| `end`            | End the current session and write summary scaffold                       |
| `archive-specs`  | Rescue a story's spec artifacts before its worktree is deleted (wired into workmux's `pre_remove`) |
| `log`            | Print color-coded event timeline for the current session                 |
| `state-dir`      | Print the active XDG state directory path (`--branch` for another's)     |
| `feature-paths`  | Print the active feature's `spec.md`/`plan.md`/`tasks.md` paths (used by the installed speckit scripts) |
| `spec-root`      | Show, set, or clear the directory this repo's spec dirs live under       |
| `arch-root`      | Show the directory this repo's architecture records live under           |
| `arch context`   | Print the in-force architectural contract — accepted records only        |
| `issue`          | Run the active issue tracker for a verb (`list`/`view`/`close`/`comment`/`create`/`label`) |
| `change`         | List/view code changes — GitHub PRs, Gerrit patchsets — via the tracker's `changes` backend |
| `install-skills` | Copy the skills, commands and speckit `.specify/` runtime wfctl ships into the current project |
| `uninstall-skills` | Remove what `install-skills` installed for `--agent`, restoring anything it overwrote |
| `install-config` | Seed a standardized repo config wfctl ships into the project (`workmux`, `github`) |
| `tracker-check`  | Validate a `.agents/trackers/<name>.json` tracker config                 |
| `hook`           | Run an agent hook from a `settings.json` entry (`worktree-guard`, `user-prompt`, `response-shape`) — not for interactive use |
| `check-body`     | Check a PR description's drawings against `conversation-response-shape` |
| `doctor`         | Check the installed skills against the ones this wfctl ships            |

`wfctl --version` prints the installed package version and exits.

## Example Session

```
$ wfctl start
✓ Session started — step: analyze, next: /speckit.analyze

$ wfctl status
#436  436-manual-transaction-entry
────────────────────────────────────
brainstorm   ●
specify      ●
clarify      ●
plan         ●
tasks        ●
analyze      ○  ← current
decompose    ○
implement    ○

$ wfctl resume
↺ Resumed — step: analyze, next: /speckit.analyze (auto: false)

$ wfctl log
2026-07-15 09:12  start       branch=436-manual-transaction-entry  step=analyze
2026-07-15 11:03  resume      step=analyze  command=/speckit.analyze  auto=False

$ wfctl end
✓ Session ended. Summary written to ~/.local/state/wfctl/.../session-summary.md
```

Install skills into a project:

```
$ wfctl install-skills
✓ Installed from wfctl 0.16.0
  base  33 skills · 27 commands · 8 runtime

Installed to .agents/ — skills and commands in their canonical, agent-agnostic
form. If your agent needs its own native paths:
  claude   wfctl install-skills --agent claude
  bob      wfctl install-skills --agent bob
  copilot  wfctl install-skills --agent copilot

$ wfctl install-skills --agent claude
✓ Installed from wfctl 0.16.0
  base    33 skills · 27 commands · 8 runtime
  claude  10 skills · 20 commands
```

The skills ship inside wfctl, so an install copies from the wheel and needs no
network. Upgrade wfctl, rerun to update.

Installation is layered. The **base layer** always installs: skills and command
wrappers in their canonical, agent-agnostic form under `.agents/`, plus the
speckit `.specify/` runtime. `--agent` adds one assistant's native paths on top
— it never replaces the base.

| `--agent` | Adds on top of `.agents/` |
|-----------|---------------------------|
| *(omitted)* / `none` | nothing — the base layer only |
| `claude` | command wrappers → `.claude/commands/`, plus `.claude/skills/` for the skills `install-skills` names as natively discoverable. A wrapper whose skill is mirrored is skipped here — both would claim one `/name` — so this layer installs fewer commands than the base one |
| `bob` | skills → `.bob/skills/`, command wrappers → `.bob/commands/` |
| `copilot` | skills → `.github/skills/` (Copilot CLI reads these directly — no transform, the files are already `SKILL.md`) |
| `codex` | nothing. Codex reads no repo-local command path: its prompts live in `~/.codex/prompts` and its repo entry point is `AGENTS.md`. Says so and installs the base layer; exits 0 |

Every layer owns a unique root, so two assistants can coexist in one repo
without their bookkeeping colliding.

> **Breaking change in 0.12.0.** `--agent` used to default to `claude`, so every
> repo got `.claude/` shims whether or not Claude was in use. Bare
> `install-skills` now writes `.agents/` only; pass `--agent claude` for the old
> behavior. `uninstall-skills --agent` follows it, defaulting to `base` rather
> than `claude`. Existing repos upgrade silently — no prompt, no backups — and
> nothing needs to be run by hand.

**Installing from somewhere else:** `--from <path>` takes the skills from a
bundle root you name rather than from the wheel that is running — a branch, a
checked-out PR, or another worktree. Either a checkout (it finds the `wfctl/`
inside) or the bundle root itself works:

```
$ wfctl install-skills --from ../116-pr
✓ Installed from ../116-pr

$ wfctl doctor
✓ base: skills current (from /home/u/wt/116-pr/wfctl)
```

**Those two lines name the same source and do not match, on purpose.** The
install echoes the path you typed, because it is read beside the command you
just ran. Everything afterwards prints the recorded one, which is resolved —
absolute, so it means the same thing from any directory, and carrying the
`wfctl/` that `--from ../116-pr` found *inside* the checkout. Expect both
differences when matching `doctor` against what you typed.

The path is recorded, so `doctor` afterwards measures that layer against *that*
tree instead of against the wheel — without it, editing a skill and reinstalling
reported drift on every run. `--from` is one-shot: a later bare install replaces
the source with the wheel and says so before it copies.

**Overwrite safety:** if `install-skills` would overwrite a file it didn't
install itself — e.g. hand-authored speckit commands already in the
project — it lists them and asks for confirmation first. Pass `--yes`/`-y`
to skip the prompt (for scripts/CI). Whatever gets overwritten is backed up,
and:

```
$ wfctl uninstall-skills --agent claude
✓ Removed 30 item(s), restored 1 pre-existing file(s) for layer 'claude'
```

removes that layer and restores anything it overwrote to its original content.
Files installed fresh (nothing to restore) are just deleted. **Only the named
layer is touched** — uninstalling `claude` leaves `.agents/` intact, because the
base layer owns it. `--agent` defaults to `base`, mirroring `install-skills`, so
a bare install and a bare uninstall round-trip. State lives in
`.wf-skills-manifest.json` and `.wf-skills-backup/` at the repo root — both are
cleaned up once nothing references them.

`wfctl doctor` is the single "am I current?" check — it reports the wfctl tool
and the installed skills (the hash on record vs the bundle this wfctl ships).
Colour-coded: **green ✓** current, **cyan ⬆** upgrade available, **yellow ⚠**
warning, **red ✗** error, **dim ℹ** named but not a finding — wfctl cannot show
the path is its own, so it does not reach the exit code.

```
$ wfctl doctor
⬆ wfctl 0.14.0 → 0.15.0 available
    upgrade: uv tool install --upgrade git+https://github.com/aamarin/wfctl.git
⬆ claude: skills stale — installed by wfctl 0.14.0, running 0.15.0
    update: wfctl install-skills
```

The tool half asks **two** questions, because the version string alone cannot
answer the one that matters. A newer release tag gets the upgrade line above.
Separately, if your build is behind the tip of the branch it was installed from
— the ordinary case, since the install above tracks the default branch — you get:

```
✓ wfctl 0.15.0 — latest release
⬆ build behind main — d8688f6 → 271bb2c
    bundled skills are from this build too
    reinstall: uv tool install --force git+https://github.com/aamarin/wfctl.git
```

Without that second question a build could sit several merges behind and still
report `✓ latest`, since the version in `pyproject.toml` only changes at release
time. It matters more since skills became part of the package: stale build,
stale skills, and the skills check cannot see it because a bundle always matches
itself.

The build's commit comes from the install metadata Python already records, so
this costs no extra network call and nothing needs stamping at build time.
Installs that cannot drift are left alone — a pinned tag, an editable checkout,
or an install from a package index. Every printed command names the repository
you installed from, so a fork is never told to reinstall from upstream.

`install-skills` records the wfctl version, a hash of the whole bundle, and the
source it installed from, which is what makes staleness detectable without a
network call. Seven verdicts per layer. Against the running wheel: current;
stale across versions, as above; **stale at the same version** — `⬆ claude:
bundled skills changed since install`, which is what an editable checkout with
edited skills looks like; and, for a record written before hashing existed, `⚠
claude: installed before content hashing`, which warns without failing since the
layer may well be current. Against a source named with `--from` (above): current,
`✓ base: skills current (from /home/u/wt/116-pr/wfctl)`; changed, `⬆ base:
source changed since install`, whose printed remedy carries the same `--from` so
the repair does not silently swap the source out; and unreadable, `⚠ base:
installed from … — source is gone, can't check`, which warns rather than fails
because a checkout moved or deleted is not a defect in this repo. Each names the
recorded path, resolved — never the one typed at install. Only the tool check needs the
network, and it degrades to a single `⚠` line naming whichever comparison could
not run — `⚠ wfctl 0.15.0 — couldn't check releases or branch (offline?)` —
without weakening the skills verdict. A check that could not run always says so;
silence would be indistinguishable from a pass.

Exits non-zero when an upgrade is available or a layer is stale — so `wfctl
doctor` doubles as a freshness gate in scripts, and the `start-session` skill
runs it so you see freshness every session.

### Seeding project config (`install-config`)

`install-config` drops a standardized config file into your repo, from the same
bundle `install-skills` reads. Unlike `install-skills` — a managed mirror it
keeps in sync — this is **seed-once**: the file becomes yours, committed and
owned. No manifest, no drift-check, no uninstall.

```
$ wfctl install-config workmux
✓ Seeded workmux config (1 file(s)) from wfctl 0.15.0
```

`workmux` seeds a repo-agnostic [`.workmux.yaml`](wfctl/agents/configs/workmux/.workmux.yaml)
starter (worktrees under `wt/`, session mode, agent + term windows, an
issue-number `pre_create` branch guard; project-specific port/env hooks ship
commented). For `workmux` it also idempotently adds `wt/` to `.gitignore` and
sets the config's `agent:` to the resolved agent — `--agent` if given, else the
sole agent `install-skills` recorded. If the repo installed no agent layer, or
several, the key is left commented out rather than guessed: `.workmux.yaml` is
committed, so naming one would push a per-developer preference into everyone's
checkout. workmux then resolves `<agent>` from `~/.config/workmux/config.yaml`.

It refuses to overwrite an existing file unless you pass `--force` (the file is
git-tracked, so git is your undo):

```
$ wfctl install-config workmux
✗ Would overwrite existing file(s): .workmux.yaml. Pass --force to overwrite (git is your undo).
```

(**workmux** runs each branch as an isolated git worktree + tmux session, so
agents work in parallel without stepping on each other. The seeded config makes
new worktrees come up ready.)

`github` seeds [`.github/pull_request_template.md`](wfctl/agents/configs/github/.github/pull_request_template.md):
a summary that reads on its own, then issue links, implementation rationale and
what was actually verified. A config source keeps its own directory structure, so
this one lands inside the `.github/` your repo already has — the workflows beside
it are untouched, and only a template already at that path is a conflict.

### The cross-worktree guard (`hook worktree-guard`)

A worktree exists so one branch's work has one isolated home, with its own
environment, skills and agent. An agent reaching into a sibling worktree puts
changes somewhere its own checks never run — and `Bash` is where it gets
through, because a path inside a command string is just a string, so the
working-directory scoping on `Edit` and `Write` does not apply to it.

`wfctl hook worktree-guard` is a `PreToolUse` hook that refuses those calls.
Three verbs, three answers:

| | | |
|---|---|---|
| create | `workmux add`, `git worktree list` | allowed |
| read | `cat`, `head`, `grep`, `ls`, `diff`, `git -C <other> log\|show\|diff\|status` | allowed |
| mutate | `sed -i`, `tee`, `rm`, an editor — or *running* anything there: `uv run`, `pytest`, `make` | refused |

Reading a sibling is ordinary review work and cannot cause the failure, so it
stays allowed. Executing is not reading: `uv run pytest` over there writes a
`.venv`, builds the package, and reports on a branch this session is not on.

Wire it up in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "wfctl hook worktree-guard" }]
      }
    ]
  }
}
```

A refusal exits 2, which blocks the call *and* hands the reason to the agent, so
it hands off instead of retrying the same thing a different way:

```
Refused: /…/wt/105-mypy-cold-venv/wfctl/ is in another worktree (/…/wt/105-mypy-cold-venv),
and `uv` is not a read command.
This session is in /…/wt/129-cross-worktree-guard. Reading across worktrees is fine — cat,
grep, diff, `git -C <path> log`. Mutating or running there is not: it puts work on a branch
this session's own checks never run on.
Hand off instead: workmux send 105-mypy-cold-venv "…" — or ask the user, if that worktree
has no session.
```

It is a heuristic and says so. It reads the command as text, so a relative path
(`../105-mypy-cold-venv/…`), a path built in a variable, or a script that `cd`s
elsewhere all pass unseen — resolving those means parsing shell. `cd` itself is
not an allowlisted verb, and pairing this with `"deny": ["Bash(cd:*)"]` closes
most of the remainder. Nothing fires unless a path in the command belongs to a
worktree that already exists, so `git worktree add` to a fresh path outside every
one of them is invisible too. Worktrees outside `wt/` are *not* a gap: the roots
come from `git worktree list`. See `wfctl/_guard.py` for the full list of what it
cannot catch.

Not seeded by `install-config`, which is seed-once and would refuse a
`settings.json` the project already owns — `--force` would take the project's own
permissions with it. `install-skills --agent claude` does install a hook this
way, using the merge mode described below.

### The merge install mode

`install-skills --agent claude` adds two entries to `.claude/settings.json` and
edits nothing else in it. They are the two halves of the same skill — one before
the text is written, one after:

| Event | Command | What it does |
|---|---|---|
| `UserPromptSubmit` | `wfctl hook user-prompt` | prints the `digest.md` of each skill the manifest records as installed, so a skill loaded at session start is re-anchored on later turns instead of decaying as the context fills |
| `Stop` | `wfctl hook response-shape` | reads the finished reply back out of the transcript and warns when it broke a `conversation-response-shape` rule a machine can see — a markdown header, a counted lead-in, length nothing asked for |

The `Stop` entry warns and never blocks. It reports to the agent that wrote the
reply rather than to your terminal — `systemMessage` is the obvious channel and
is not wired for this event, so the finding rides
`hookSpecificOutput.additionalContext` and lands in the next turn's context. It
carries `|| true` because a non-zero exit on that event tells the agent to keep
going rather than stopping, so an older `wfctl` on `PATH` would loop at the end
of every turn instead of printing once. The same rules over a PR description are
`wfctl check-body <file>`, which is a command rather than a hook because a
description is a file on disk before `gh pr create` reads it.

Your own permissions, hooks and settings are left alone; `uninstall-skills`
removes just wfctl's own entries, and `doctor` reports one when it goes missing
or falls behind. The first install that adds the entry reflows the file (key order, array
layout and indent width are lost to the JSON round-trip; the trailing newline,
the file mode and any non-ASCII survive). Later installs leave it closed.

The file is deliberately not gitignored — committing it is what shares the hook
with everyone who clones. That is also why the hook reads the manifest rather
than the skills directory: a directory nobody installed can ride along in a
clone, and it must not be able to put text into your context.

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
in**: a repo's first interactive `install-skills` offers to install it, and
declining (or any non-interactive run — piped, CI, `--yes`) leaves the repo
without a tracker until you pass `--tracker`. Declining is remembered, so the
question is asked once and not on every upgrade. Once a repo has a tracker,
later installs leave the choice and your edits to its config alone — re-copy the
shipped one with an explicit `--tracker github`. `--tracker none` clears the
choice entirely, which also re-opens the question on the next interactive
install.
For anything else — a private
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

### Where your specs live (`spec-root`)

**The first interactive `wfctl install-skills` in a project asks this**, beside
the tracker question, and records that you answered so it is never asked again.
Keeping specs in the repo records no `spec_root` — the default is the absence of
that setting, so artifacts resolve exactly as they do in a project that predates
the question. Non-interactive installs, and `--yes`, never ask; nor does a
project that already ran `wfctl spec-root`.

Two setups. The first needs no configuration at all.

| You want | Do this | Survives `git worktree remove`? |
|---|---|---|
| Specs alongside the code | nothing — this is the default | only if you commit them |
| Specs in a durable location | `wfctl spec-root <dir>` | yes |

**If you commit your specs, you probably want the default.** The problem
`spec-root` solves is worktree teardown destroying *gitignored* specs; committed
specs survive by being in git. Moving them out would take them out of version
control for no gain.

`spec-root` takes any directory. Where you point it is your project's call — a
sibling directory, a specs repo cloned into the main checkout (which keeps them
in version control, on their own remote), or anywhere else durable. wfctl only
resolves the path; it never creates or clones anything.

#### Pointing it somewhere durable

By default a feature's artifacts live in `<repo>/specs/<branch>/`. In a worktree
that is a problem: `specs/` is conventionally gitignored, so removing the
worktree destroys the spec, plan, and tasks with it.

Point the project somewhere durable instead — once, from anywhere in it:

```bash
wfctl spec-root ~/Development/myproject-specs
wfctl spec-root            # show the current root and where it came from
wfctl spec-root --unset    # back to <repo>/specs
```

The value is stored as `spec_root` in `.wf-skills-manifest.json`. Because that
file is gitignored and regenerated in every fresh worktree, `spec-root` writes
the **main checkout's** manifest and tells you which file it wrote; worktrees
then inherit the setting with no per-worktree setup.

Resolution order:

1. `WFCTL_SPEC_DIR` — a per-invocation override, not configuration. It is
   process-global, so exporting it from a shell profile redirects *every* repo.
2. `spec_root` in this repo's manifest.
3. `spec_root` in the main checkout's manifest — how worktrees inherit it.
4. `<repo>/specs` — the default.

Paths are stored exactly as typed. `~` is expanded when read, so the manifest
stays portable across machines; a relative path anchors to the directory of the
manifest that declared it, never your shell's working directory.

**Recording a root does not move anything.** Existing `<repo>/specs/*` stop being
found, since the recorded root is the only one consulted — no fallback, so one
feature's artifacts can never split across two locations. Move them yourself;
`wfctl doctor` reports the leftovers until you do.

A repo in a bare-clone or separate-gitdir layout has no main checkout to inherit
from, and nothing outside the repository is read in that case.

### The architectural contract (`arch-root`, `arch context`)

An architecture record is one decision, written down: what was decided, what was
rejected, and — the field this exists for — **who owns the truth** it settles.
Records live in `docs/architecture/`, one file per decision, named by a slug
rather than a number so two worktrees never collide.

```bash
wfctl arch-root              # where this repo's records live
wfctl arch context           # the in-force set, for an agent to load
```

`arch context` is the one an agent reads. It prints only records whose
frontmatter says `status: accepted`, so a superseded decision cannot be mistaken
for a live one:

```
# Architectural contract — 5 accepted decisions

layer-model
  Source is committed package data under `wfctl/agents/` and
  `wfctl/specify/`. Every dotted directory at the repo root is generated,
  gitignored, and never edited by hand.
```

Anything other than `accepted` — `proposed`, `superseded`, an unrecognized
value, or no status at all — is left out. The default is deliberately the
conservative one: presenting an unreviewed decision as binding is the failure
the status field exists to prevent.

Resolution is the same four steps as `spec-root`: `WFCTL_ARCH_DIR`, then
`arch_root` in this repo's manifest, then the main checkout's manifest, then
`<repo>/docs/architecture`. `arch-root` is read-only — the root is declared in
`.wf-skills-manifest.json`, and the default needs no command to reach it.

Unlike specs, records are **committed**. They are the project's own
documentation rather than session state, so there is nothing to rescue before a
worktree is torn down.

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
| `WFCTL_SPEC_DIR`        | Override spec directory root for one invocation (default: unset — falls through to the repo's `spec_root`, then `<repo>/specs`; see [`spec-root`](#where-your-specs-live-spec-root)) |
| `WFCTL_ARCH_DIR`        | Override architecture record root for one invocation (default: unset — falls through to the repo's `arch_root`, then `<repo>/docs/architecture`) |
| `WFCTL_REPO_ROOT`       | Override git repo root detection                             |
| `XDG_STATE_HOME`        | Base for XDG state path (default: `~/.local/state`)          |

## Development

```bash
git clone https://github.com/aamarin/wfctl.git
cd wfctl
pip install -e ".[dev]"
pytest
```

The skills, commands and speckit runtime `install-skills` writes are committed
here as package data under `wfctl/agents/` and `wfctl/specify/` — edit them in
place, then `wfctl install-skills` to try them in a repo. They carry no leading
dot on purpose: `.gitignore` ignores `.agents/` and `.specify/` unanchored, so a
dotted vendored copy would be silently untracked. The dotted directories at the
repo root are this repo's own install output, not the source.

## Contributing

Issues and PRs welcome. Please open an issue first for significant changes.

## License

MIT — see [LICENSE](LICENSE).
