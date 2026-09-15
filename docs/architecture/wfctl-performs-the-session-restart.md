---
status: proposed
---

# wfctl decides and performs a pane's session restart, from a Stop hook in the claude layer

## Context

A run that fills its context window gets one of two endings today. Harness
compaction summarises contents nobody chose, at a moment nobody picked. Or a
person's own Stop hook — `~/.claude/recycle-hook.sh`, in no repo — sends `/clear`
and `/start-session` to the pane, with no `/end-session` between them, so the
next session starts from whatever handoff an earlier one happened to leave
(#371). `~/.claude/recycle-hook.log` shows that second ending firing on this
branch twice in one afternoon, and taking two sessions' reasoning with it.

#188 asked the same question and both of its records were rejected, for reasons
that no longer hold:

```
wfctl-owns-the-recycle-verdict            rejected: the mechanism is agent-specific,
                                          so "there is no verdict for wfctl to own"
wfctl-names-the-reset-it-cannot-perform   rejected: wfctl declines subprocess by
                                          construction, and the classifier refuses
                                          an agent that drives its own pane
```

The first reason fell to scope. #371 is now Claude-only by the user's decision
(ledger entries 18, 21), and `install-modes` already puts a Claude hook schema in
the claude layer rather than the base — an agent-specific mechanism has an
accepted home inside wfctl.

The second fell to two facts checked since. The no-`subprocess` rule is
`_workmux.py`'s own docstring, stated as the reason *that module's* tests need no
fixture; `_hook.py` already shells to `git` from a managed hook. And the
classifier refusal is a gate on the agent's tool calls: a Stop hook is run by the
harness, not by the model, and the personal hook above has delivered both sends
from exactly that position. The "supervisor outside the run" the rejected record
went looking for is a hook.

What a hook cannot do is write prose — by the time any hook runs on `/clear`, the
model is gone (ledger entry 1). So the handoff has to be written *before* the
clear, by a turn the hook asks for: over the threshold, send `/end-session`; on
the Stop after that turn, send `/clear` and `/start-session` (entry 11).

## Direct baseline

Nothing ships in wfctl. The restart hook stays a personal script each developer
installs by hand into `~/.claude/`, amended per ledger entry 11 to send
`/end-session` first and to wait one Stop before clearing. wfctl's only
contribution is what `end-session` and `start-session` already do.

This works for the developer who wrote the script and for nobody else. The script
has to parse `events.jsonl` to know the handoff landed — a format wfctl owns and
changes (`stop-kind-is-a-field-not-an-event` added a key this month) — with no
test and no version tying the two together. And the classifier refuses an agent
that authors it (ledger entry 17), so every copy is placed by a person.

## Decision

`wfctl hook session-restart` is a managed Stop hook installed by `install-skills --agent
claude`. On each Stop it reads the window's occupancy from the transcript's last
usage record and the branch's `events.jsonl`, decides one of *nothing*, *send
`/end-session`*, *send `/clear` then `/start-session`*, *hold* or *skip*, and
performs any sends itself through `workmux send`, from a detached process that
starts after the hook has exited.

## Owns truth

wfctl owns **"is this pane due to restart, and has the handoff it asked for
landed yet?"**

The agent cannot own it. The restart destroys the context that would hold the
reading, so a session that comes back cannot tell a window cleared a minute ago
from one never cleared — the argument of `wfctl-owns-the-recycle-verdict`, which
was rejected for its scope and never for this. And the agent is refused the act
twice over: `/clear` by name, and driving its own pane by the classifier.

A script outside wfctl cannot own it either, and the second half of the question
is why. "Has the handoff landed" is answered only by an `end` event newer than the
`/end-session` send — a fact in wfctl's event log, in wfctl's format. Without it,
a `/end-session` turn that asked a question or errored is followed by a `/clear`
anyway, and `/start-session` quotes the previous handoff as current (ledger entry
18, state D). Reading that from outside wfctl is a contract with no test on either
side of it.

The harness keeps what it owns: the occupancy figure is Claude Code's, written
into the transcript, and wfctl only reads it.

## Considered

- **Ship the script as a managed claude-layer file** (entry 20, A) — the smallest
  step up from the baseline, and it breaks the one rule `install-modes` uses to
  find its own rows: every managed hook's command starts `wfctl hook `. It also
  leaves `events.jsonl` parsed from shell and the decision out of reach of pytest.
- **wfctl decides and prints, a shipped script sends** (entry 20, C; #188's split)
  — sound, and the split buys nothing now. Both halves ship from wfctl into the
  same layer, so the boundary between them is a second artifact rather than a
  second owner; it existed in #188 only because wfctl was declining the send.
- **Fire on Claude Code's idle notification instead of Stop** — would give the
  restart hook an event of its own and make "the pane is idle" free rather than a
  delay. It fires only after roughly a minute without input, so an attended
  session answered within the minute never restarts, which is not the level-1
  behavior agreed (entry 19). Not probed.

## Consequences

- Stop now carries two wfctl entries, which the installer's one-entry-per-event
  identity collapses as a hand-edit duplicate.
  `a-managed-hook-is-owned-by-its-subcommand` is that decision.
- The hook needs a memory between two Stops — that it sent `/end-session`, and
  when — so it writes its own line to `events.jsonl`. Its shape is level 3.
- The sends run in their own process session and begin after the hook returns. A
  send issued while the hook is still running lands in a pane that counts the hook
  as work in progress (ledger entry 16, observed on Codex; assumed of Claude Code
  until probed).
- The hook exits 0 on every path. Exit 2 on Stop blocks the stop, so a bug here
  would turn every turn's end into a loop.
- A pane that workmux cannot reach is *skip*, and says so in the pane rather than
  in a log nobody opens (ledger entry 18, state E). How it says so is unprobed.
- Cost per Stop, measured on this branch: 0.07–0.10 s to start wfctl, 0.02 s to
  read a 1.6 MB transcript. No model tokens on the turns it decides *nothing*.
- On by default at 200000 tokens in every repo with the claude layer.
- Risk, not boundary: the classifier may refuse the agent authoring the send code
  inside `wfctl/` as it did in a scratch directory (entry 17).

## Log

- 2026-09-15  proposed    — #371: an automated `/clear` discards the session's
  reasoning, and the decision to restart and the act of restarting needed one owner
  before a hook could be shaped. B chosen by the user in ledger entry 22.
