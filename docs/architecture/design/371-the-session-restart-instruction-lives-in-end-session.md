---
status: proposed
---

# What a restart asks of `/end-session` is written in the skill, and the hook sends one word

## Context

`wfctl-performs-the-session-restart` (proposed, level 2) sends `/end-session` to a pane
over the threshold, and `/clear` plus `/start-session` once the handoff has
landed. Two of `end-session`'s defaults are wrong for that turn, and the personal
restart hook this started from corrected both in the text it sent:

- it closes with a bare `wfctl end`, which records a wrapped-up stop — and a
  restarted session is the opposite, one the next session carries on without
  being asked (`start-session` step 8 reads exactly that field);
- it stops to ask before committing and before touching the tracker, with nobody
  at the prompt, and the `/clear` that follows would discard the question.

The pressure is where those corrections live once wfctl ships them.
`layer-model` (accepted) is the constraint: skill source is committed package
data under `wfctl/agents/`, and the dotted directories are generated from it.

## Verified

- `wfctl/agents/skills/end-session/SKILL.md:44` — step 3 runs `wfctl end` with no
  flag. `--continued` appears nowhere in the file.
- `wfctl/agents/skills/end-session/SKILL.md:168,173` — steps 6 and 7 ask the user
  before committing and before updating the tracker.
- `wfctl/cli.py:905-906` — `wfctl end --continued`, "The work carries on — the
  next session picks it up".
- `wfctl/agents/commands/end-session.md` — the wrapper's `allowed-tools` already
  covers `Bash(wfctl end*)`, so the flag needs no permission change.
- No wrapper under `wfctl/agents/commands/` reads `$ARGUMENTS`; none of them
  takes an argument today.
- The personal recycle script's `END_PROMPT` is 237 characters of instruction sent as
  pane input (`20a8241b-…/scratchpad/recycle/recycle-hook.sh`).

## Assumed

- **That text after `/end-session` reaches the skill on Claude Code.** Checked on
  Codex and Copilot with a stand-in skill that echoed its arguments (ledger entry
  15); not on Claude. Falsified by a restart turn that runs `end-session` and asks
  the commit question anyway — the decision survives it, since the skill section
  could key on something other than an argument, but the one-word send would not.
- **That the model follows a skill section as reliably as a sent instruction.**
  Both are prose in context; neither is a check. Falsified by a restart turn that
  records a wrapped-up stop, which the `end` event's `continued` field shows.

## Direct baseline

Keep the personal recycle script's shape: a module constant in `wfctl/_restart.py`
holding the full instruction, sent verbatim.

```
END_PROMPT = (
    "/end-session automatic session restart, not a wrap-up: nobody is at the "
    "prompt. Close with `wfctl end --continued`, write the summary in full, and "
    "skip the commit and tracker questions …"
)
```

No change to any skill. The instruction ships with the hook that sends it and is
tested as a string.

## Decision

`end-session` gains a section for an invocation carrying `restart`: close with
`wfctl end --continued`, fill the summary in full, skip steps 6 and 7 and say in
the summary that the tree was left as found. The hook sends
`/end-session restart` and nothing more.

## Diagram

```
             baseline                              decision

          ┌──────────────────────┐              ┌──────────────────────┐
stable    │ end-session SKILL.md │              │ end-session SKILL.md │
          │  (steps 3, 6, 7)     │              │  + restart section   │
          └──────────────────────┘              └──────────────────────┘
                     ▲ overridden by                       ▲ selects
          ┌──────────┴───────────┐              ┌──────────┴───────────┐
          │ _restart.END_PROMPT  │              │ _restart: "restart"  │
          │ (237-char literal)   │              │                      │
          └──────────┬───────────┘              └──────────┬───────────┘
═════ layer-model: committed source │ generated, and sent at runtime ═════════
                     ▼ sent as                             ▼ sent as
volatile  ┌──────────────────────┐              ┌──────────────────────┐
          │   pane input         │              │   pane input         │
          └──────────────────────┘              └──────────────────────┘
```

The graphs differ by what one arrow carries. In the baseline a string in
Python overrides three steps of a skill it does not live beside, so a change to
`end-session` — renumbering, a new question at step 6 — silently leaves the
override describing a skill that no longer exists. In the decision the skill
states its own exception and the hook only selects it. No divider is new: in
both, the instruction is committed source above `layer-model`'s line and pane
input below it.

## Considered

- **The constant** — the baseline. Sound, and it is what works today. It loses on
  who reads it: a reviewer changing `end-session` never opens `_restart.py`, and a
  person watching the pane gets 237 characters of instruction they did not type.
- **A separate `restart-session` skill** — no conditional inside `end-session`.
  Rejected because it would restate steps 1–5 and 8, which is the drift the
  decision exists to prevent, one file over.
- **An environment variable the hook sets for the turn** — no argument parsing.
  Not available: the worker types into a pane, it does not start the process the
  model's tool calls run in.

## Consequences

`end-session` has an argument for the first time, and a wrapper that has never
read one. The section has to say what happens on any other argument — ignored,
as today — so a typo does not quietly become a restart.

A person can type `/end-session restart` by hand and get an unattended close in
an attended session. That is the same outcome as sending it, and not a thing the
skill can tell apart.

## Verification

- A test in the skills suite that `end-session/SKILL.md` names `--continued`
  under the restart section, and that `_restart`'s send text is exactly
  `/end-session restart` — so the two halves cannot drift apart silently.
- A live restart on Claude Code whose `end` event carries `"continued": true`
  and whose tree is unchanged by the turn. This is the assumption above, checked.

## Log

- 2026-09-15  proposed  — #371 level 3; the restart turn needs `end-session`
  without its two questions and with `--continued`, and the personal recycle script
  said so in a string beside the hook rather than beside the skill. Chosen by the
  user (ledger entry 27).
