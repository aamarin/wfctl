---
status: proposed
---

# The restart's sends run in a detached Python worker that records what each send did

## Context

`wfctl-performs-the-session-restart` (proposed, level 2) has `wfctl hook session-restart` decide
on each Stop and perform the sends itself through `workmux send`, "from a
detached process that starts after the hook has exited". It leaves the shape of
that process to level 3.

The pressure is a failure nobody saw. The personal recycle script that level 1 started
from sends from inside the running hook, and a send that exits 0 is not a send
that landed: on 2026-09-14 at 12:33:03 it sent `/clear` and `/start-session` to
`619-flexible-budget`, both `send exit=0`, and the same transcript went on
growing from 225k to 283k over the next day while every Stop logged "already
recycled this transcript". Level 1 now carries that as state F — the hook says
once, in the pane, that the clear it sent did not take (ledger entry 26).

Saying so needs the next Stop to know what the last send did. That is the
question this record answers.

## Verified

- `~/.claude/recycle-hook.log`, 2026-09-14 12:33:03–12:38:06 — two `send exit=0`
  lines for `619-flexible-budget`, followed by five Stops on the same transcript
  at 225500–244899 tokens, each "already recycled this transcript".
- `wfctl/_workmux.py:1-10` — "imports nothing from `wfctl.*` and never calls
  `subprocess`", stated as what keeps its tests fixture-free. The sender does not
  belong there.
- `wfctl/_hook.py:34-43` — a managed hook already shells out (`git`) through
  `subprocess.run`, catching `OSError` and `CalledProcessError`.
- `wfctl/_io.py:71-76` — `append_event` stamps `ts` and `event` and passes every
  other field through; a new event kind costs no change there.
- `wfctl/cli.py:2319` — the Stop entry is installed with `2>/dev/null || true`, so
  nothing the hook writes to stderr, and no exit it returns, reaches anyone.
- `workmux send --help` — `workmux send [OPTIONS] <NAME> [TEXT]`.
- The Claude Code Stop payload carries `session_id`, `transcript_path` and `cwd`
  (probe log `bfa026e1-…/scratchpad/clearprobe/probe.log`).

## Assumed

- **That a send started after the hook exits lands on Claude Code.** Observed on
  Codex only (ledger entry 16, where a send from a running Stop hook was refused
  as "a task in progress"). Falsified by a detached `/clear` that still leaves the
  session's transcript growing — which state F would then report, so the bet
  fails loudly rather than silently.
- **That the 619 failure was the in-hook send and not something else** — a person
  typing, a prompt already queued. The log cannot say. Falsified by a restart
  from a detached worker failing the same way; state F is built for either cause.
- **That a Python interpreter start per send is cheap enough.** It runs only on a
  restart, a few times a day per pane, never on the Stops that decide nothing.

## Direct baseline

The hook spawns a detached shell and returns:

```
subprocess.Popen(
    ["sh", "-c", f'sleep 4; workmux send {h} /clear; sleep 5; workmux send {h} /start-session'],
    start_new_session=True,
)
```

No new module, no new process entry point, the same two sends the personal
script already makes, moved out from under the hook. It removes the likely cause
of the 619 failure. The exit codes of the sends go nowhere.

## Decision

The hook spawns `python -m wfctl._restart_send` with `start_new_session=True`,
passing the handle, the session id and the send plan as arguments, and returns.
The worker waits for the hook's process to have exited, runs each `workmux send`
through `subprocess.run`, and appends one `session-restart-send` event per send carrying
`session`, the text sent, and the exit code.

The decision itself — nothing, send end, send clear and start, hold, skip,
report F — stays a pure function in `wfctl/_restart.py` over the payload, the
occupancy and the parsed events, with `hook session-restart` in `cli.py` as the thin
caller. The worker decides nothing.

## Diagram

```
             baseline                                decision

          ┌──────────────────┐                  ┌──────────────────┐
stable    │   events.jsonl   │                  │   events.jsonl   │
          └──────────────────┘                  └──────────────────┘
                ▲ reads                             ▲ reads   ▲ writes exit
          ┌─────┴────────────┐                ┌─────┴──────┐  │
          │ wfctl hook       │                │ wfctl hook │  │
          │ session-restart  │                │ session-   │  │
          │                  │                │ restart    │  │
          └─────┬────────────┘                └─────┬──────┘  │
                │ spawns                            │ spawns  │
          ┌─────▼────────────┐                ┌─────▼─────────┴──┐
          │ sh -c sleep; send│                │ _restart_send    │
          └─────┬────────────┘                └─────┬────────────┘
                │ calls                             │ calls
          ┌─────▼────────────┐                ┌─────▼────────────┐
          │  workmux send    │                │  workmux send    │
          └─────┬────────────┘                └─────┬────────────┘
════ agent harness (Claude Code owns the pane) ═══════════════════════════
                ▼ types into                        ▼ types into
volatile  ┌──────────────────┐                ┌──────────────────┐
          │       pane       │                │       pane       │
          └──────────────────┘                └──────────────────┘
```

The graphs differ by one arrow: the worker writes back to `events.jsonl`, the
shell does not. Without it the next Stop can see that a send was *planned* — the
hook's own `session-restart` event — and cannot tell a send that failed from one that ran
and did not take. State F needs only the second, but saying "sent /clear at
12:33Z" when `workmux` exited 1 would be the same lie the 619 log tells in
reverse. No divider is new: in both, wfctl stops at `workmux send` and the pane
is the harness's.

## Considered

- **The detached shell** — the baseline above. Sound, and it probably fixes the
  619 failure on its own. It loses on what the next Stop can know, and on reach:
  its sleep and send order sit in a string pytest can assert on but not run.
- **Send synchronously inside the hook**, as the personal script does — rejected
  on the evidence above and entry 16: the pane counts a running Stop hook as work
  in progress.
- **Re-invoke `wfctl hook session-restart --send …` as the worker** instead of a module
  entry point — no new entry point, but it loads `typer` and `rich` for a process
  that parses no options a person types, and adds a flag to a command whose
  argv is an installed interface (`_entry.py:1-12`).
- **The worker writes its outcome to a log file** beside `~/.claude/recycle-hook.log`
  — the personal script's shape. Rejected because the reader of the outcome is the
  next Stop, which already reads `events.jsonl`; a second file is a second format
  with one reader.

## Consequences

The next Stop can report F truthfully in both of its forms — sent and not taken,
or never sent — and the hook stays silent on the Stops that decide nothing.

A process outlives the hook that started it. If `workmux` hangs, so does the
worker, detached and unobserved; `subprocess.run` needs a timeout on each send.

`events.jsonl` gains two event kinds, `session-restart` from the hook and `session-restart-send`
from the worker, written by two processes that can interleave with a session's own
`wfctl` calls. `append_event` opens in append mode and writes one line, which is
what the existing readers already rely on; a torn line is skipped by them.

## Verification

- A test that the decision function, given a `session-restart` event for session S and a
  `session-restart-send` with exit 0 for `/clear`, and a payload from session S, returns
  *report F* — and returns *nothing* for a payload from any other session.
- A test that a `session-restart-send` with a non-zero exit produces the "never sent"
  wording, not "sent and did not take".
- A test that the hook returns before the worker sends: spawn with a stub
  `workmux` on `PATH` that records its parent pid and a timestamp.
- A live restart in a Claude pane, checked by transcript id changing after the
  send. The suite cannot reach this, and it is the assumption the record rests on.

## Log

- 2026-09-15  proposed  — #371 level 3; the personal recycle script's `send exit=0` on
  a `/clear` that never took showed the next Stop needs to know what a send did,
  which a detached shell cannot tell it. Chosen by the user (ledger entry 27).
