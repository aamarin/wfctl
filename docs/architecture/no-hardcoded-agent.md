---
status: accepted
---

# Committed config never guesses an agent

## Context

`.workmux.yaml` is committed, and it drives commands that take an `--agent`
flag. The agent is per-developer — one clone runs Claude, the next runs
something else — and the file is shared by all of them.

A value written into the committed file on a hunch is correct for whoever wrote
it and wrong for everyone after, in a way that surfaces as someone else's agent
launching unexpectedly rather than as an error.

## Decision

Hooks in committed config never name an agent. They take it from the
environment:

```
${WFCTL_AGENT:+--agent "$WFCTL_AGENT"}
```

The `:+` form expands to nothing when `WFCTL_AGENT` is unset, so the flag is
omitted rather than passed empty.

The seeded `agent:` key is filled only from something that was actually chosen,
never inferred from a default (`_resolve_config_agent`, `cli.py:1724`):

| What is known | What gets written |
| --- | --- |
| `--agent` passed explicitly | that agent, active |
| exactly one agent layer installed | that agent, active — the choice `install-skills` recorded |
| none, or several | `# agent:` commented out |

Commented out is the fallback, not the goal. Where nothing was chosen, workmux
resolves the agent from `~/.config/workmux/config.yaml`, which is where a
per-developer preference belongs.

## Owns truth

The developer's environment owns which agent runs.

The repository holds a value only where an install recorded one, and then only
as a starting point a clone can override — `WFCTL_AGENT` and workmux's own
config both take precedence at the point the command runs.

The repository cannot own the choice outright: there is no value it could infer
that is right for the next clone, and unlike a wrong path or a wrong version, a
wrong agent produces no error to notice.

## Considered

- Default to the most common agent — wrong for everyone else, and wrong
  silently, which is worse than unset.
- Prompt at install and write the answer into the committed file — the answer is
  then committed, and the problem returns for the next clone.
- Require `WFCTL_AGENT` and fail without it — makes an agent mandatory for
  commands that do not need one. The `:+` form degrades to omitting the flag
  instead.
- Never write the key at all, even when one agent is installed — costs a repo
  set up for a non-default agent its matching config, and re-specifying it on
  every clone is the friction the mirror removes.

## Consequences

A command that would take an agent and finds none omits the flag and runs with
whatever default it has. Silence here is intended: an unset agent is the normal
state, not a misconfiguration.

That sentence governs the *flag*, not the report. `doctor` names an absent agent
layer (#178) without calling it wrong — dim, no repair line, exit code untouched
— and the flag is still omitted, no agent inferred, and none named by anything
wfctl prints.

The sole-agent mirror rests on a premise worth watching:
`.wf-skills-manifest.json` is gitignored (`cli.py:832`), so "one agent layer
installed" is the seeding developer's state, not the repo's. Mirroring it writes
a per-developer value into a committed file — the shape this record otherwise
rules out. It is accepted here because the value is a starting point rather than
an assertion, and every consumer of it can override. Should that stop being
true, this record is what has to change first.

## Log

- 2026-08-28  accepted    — relocated from `AGENTS.md`
- 2026-08-29  amended     — states the sole-agent mirror the code has always done, and the gitignored-manifest premise it rests on
- 2026-09-06  amended     — separates "no error" from "no mention"; `doctor` names an absent agent layer without it becoming a finding (#178)
