---
status: proposed
---

# The restart threshold is read from the environment, and zero turns the restart hook off

## Context

`wfctl-performs-the-session-restart` (proposed, level 2) puts the restart hook on by default
at 200000 tokens in every repo with the claude layer. It says nothing about how a
person moves that number or turns the restart hook off, and both are needed on day
one: a default that cannot be changed is a hook people uninstall.

The pressure is what the number depends on. It is a fraction of a model's context
window, and the window belongs to the model a person runs — not to the repo the
pane happens to be in.

`no-hardcoded-agent` (accepted) is the constraint in force on the same axis:
committed hook config names no agent, and takes it from the environment, because
which agent runs is the person's fact rather than the repo's.

## Verified

- `~/.claude/recycle-hook.log`, 2026-09-14 — one transcript in
  `619-flexible-budget` reached 283068 tokens, so at least one of this user's
  panes runs a window larger than 200000. One default cannot fit every pane on
  one machine, let alone every repo.
- `wfctl/_paths.py:252-255` — `spec_root`'s docstring: the env var is "a
  per-invocation escape hatch: it is process-global, so exporting it from a shell
  profile would redirect every repo wfctl touches. The manifest is already
  per-repo, which is why the persistent setting lives there."
- `WFCTL_STATE_DIR`, `WFCTL_SPEC_DIR`, `WFCTL_ARCH_DIR`, `WFCTL_BRANCH` and
  `WFCTL_AGENT` are all read from the environment (`grep -rn WFCTL_ wfctl/`).
- `AGENTS.md` § Declaring what a change must carry — `change_check` lives in
  `wfctl.json` because it is repo policy, and `.agents/` is regenerated.
- The personal recycle script reads `RECYCLE_THRESHOLD` from the environment with a
  default (`20a8241b-…/scratchpad/recycle/recycle-hook.sh:32`).

## Assumed

- **That the environment a person's shell exports reaches the Stop hook.** Claude
  Code runs hooks as child processes of its own, and `WFCTL_AGENT` from a shell
  profile reaches workmux's `post_create` the same way. Falsified by a pane
  launched from something other than a login shell — a desktop app, a service —
  where the variable is unset and the default applies silently.
- **That the threshold is a person's choice more often than a repo's.** Falsified
  by a repo that needs the restart hook off for everyone — a repo whose sessions must
  never be cleared unattended — which this shape cannot express.

## Direct baseline

A module constant, `RESTART_THRESHOLD = 200000` in `wfctl/_restart.py`, and no
setting. Changing it means editing wfctl; turning the restart hook off means removing
the Stop entry from `.claude/settings.json` by hand, which the next
`install-skills` puts back.

## Decision

`wfctl hook session-restart` reads `WFCTL_RESTART_THRESHOLD`. Unset or unparseable, it is
200000. `0` turns the restart hook off: every Stop decides *nothing*. The constant
stays as the default and is the only place 200000 is written.

## Diagram

```
             baseline                            decision

          ┌────────────────────────┐          ┌────────────────────────┐
stable    │ _restart               │          │ _restart               │
          │ THRESHOLD = 200000     │          │ default 200000         │
          └────────────────────────┘          └────────────────────────┘
                   ▲ reads                         ▲ reads  ▲ falls back to
          ┌────────┴───────────────┐          ┌────┴────────┴──────────┐
          │ wfctl hook             │          │ wfctl hook             │
          │ session-restart        │          │ session-restart        │
          └────────────────────────┘          └────────────────────────┘
                                                        ▲ reads
═══ no-hardcoded-agent: committed config │ the person's environment ═══════
                                                        │
volatile  ┌────────────────────────┐          ┌─────────┴──────────────┐
          │ shell profile          │          │ shell profile          │
          │ (nothing read)         │          │ WFCTL_RESTART_THRESHOLD│
          └────────────────────────┘          └────────────────────────┘
```

The graphs differ by one arrow across the line `no-hardcoded-agent` already
draws. In the baseline nothing below the line is read, so the only way to change
the number is to change wfctl, and the only way to stop the restart hook is an edit
`install-skills` reverts. The decision reads one value from the side that owns the
model choice, and leaves the committed config naming nothing.

## Considered

- **A `restart` key in `wfctl.json`** — the house place for persistent settings,
  per `_paths.py`'s own reasoning, and the only option that lets a repo turn the
  restart hook off for everyone. Sound, and it loses on fit: the number follows the
  model, and two people on one repo with different windows would fight over one
  committed value. If a repo-wide off switch is ever needed it is an addition to
  this, not a replacement.
- **Both, the env var overriding the manifest** — the `spec_root` precedence
  order. Rejected for now as two sources for a value with one real owner; the
  repo half has no caller yet.
- **Derive the threshold from the model's window** as a fraction — no setting at
  all. Not available: the transcript's usage records carry token counts and no
  window size, and wfctl would be hard-coding a table of models.
- **The constant only** — the baseline. Rejected because the 283k pane shows the
  default is already wrong for some of this user's own panes.

## Consequences

A person tunes or disables the restart hook without editing wfctl or fighting
`install-skills`, and nothing committed says anything about their model.

Every pane on a machine shares one threshold. The 619 pane and a 200k pane
started from the same shell get the same number, so a person running both model
sizes sets it for the smaller one or exports it per pane.

The failure mode is silence: a pane whose environment lacks the variable runs the
default with nothing saying so. `wfctl doctor` is the place to print the
threshold in force, so the question has somewhere to be answered.

## Verification

- A test that the decision function treats unset, empty and `abc` as 200000, and
  `0` as off — including a payload at 10 million tokens returning *nothing*.
- A test that 200000 appears once in `wfctl/`, so a second copy of the default
  cannot drift from the first.
- A live check that a value exported in the shell profile reaches the hook in a
  workmux pane: the restart fires at the exported value, not the default.

## Log

- 2026-09-15  proposed  — #371 level 3; on-by-default needed a way to move the
  number and to turn it off, and the number follows a person's model rather than
  the repo. Chosen by the user (ledger entry 27).
