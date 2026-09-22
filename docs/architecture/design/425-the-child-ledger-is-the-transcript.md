---
status: proposed
---

# Outstanding children are read from the harness's transcript, not recorded in wfctl's log

## Context

`wfctl hook session-restart` clears a pane once its handoff has landed. It has no
idea whether the session it is clearing still has subagents out, so a review
panel that found six problems and a panel that never ran leave the same absence
behind (#425).

To hold on that the restart needs one fact: *did this session launch a child that
has not reported back?* Nothing in wfctl knows it. Two places could answer —
wfctl's own `events.jsonl`, if something wrote the launches there, or the
harness's transcript, which already records them for its own reasons and which
`occupancy` already opens on every reply end over the threshold.

`session-state-is-re-derived` (accepted) is the constraint in force on that
choice, and `a-run-cursor-is-execution-state-not-evidence` (proposed) is the
nearest neighbour: a persisted cursor of what executed is authoritative for
resuming a run and is not evidence that anything was satisfied. A child ledger
wfctl maintained would be exactly such a cursor.

## Verified

- `wfctl/_restart.py:98` — `occupancy` already opens the transcript named in the
  Stop payload on every reply end, so a second reader of the same file adds a
  pass and no new dependency.
- Across this repository's own Claude Code transcripts, 471 `toolUseResult`
  records carry `"status": "async_launched"` and 6 carry `"status": "forked"`;
  every one of the 477 also carries a string `agentId`, and no other record shape
  carries that key.
- A child's report reaches the transcript in two shapes, and which one depends on
  what the parent was doing. At its prompt, the parent gets a `"type": "user"`
  record whose `message.content` is a string beginning `<task-notification>` —
  483 of those. Mid-turn, the notification is absorbed into the running turn and
  the only record is a top-level `attachment` whose `prompt` carries the same
  tags. Reading the first alone left 200 of 489 launches looking outstanding when
  141 of them had reported; reading both leaves 57.
- A merely queued copy is not a report. The same notification also passes through
  `queue-operation` records, and an item can leave that queue unsent
  (`resume_failed`), so the queue is not read. The attachment is written as the
  item leaves the queue *into* the turn — `enqueue`, then `remove` with reason
  `absorbed_mid_turn`, then the attachment carrying the rendered text.
- Ten records mention the same tags inside a *list* of content blocks, and two
  more inside a `prompt_snapshot` attachment — an agent writing about
  notifications rather than receiving one. Requiring the tag to be the whole of
  the string, rather than anywhere in it, is what separates them.
- Across 320 of this repository's transcripts, 57 launches are still outstanding
  when their transcript ends. 51 of them reported into a *later* transcript in
  the same project — the pane was cleared between the launch and the report,
  which is the failure #425 describes, and the session that received those 51
  reports had no record that any of them were expected. The remaining 6 have no
  report anywhere on disk.
- The launch's own tool-result text: "never quote or paste any part of it,
  including the agentId below, into a user-facing reply."
- `docs/architecture/session-state-is-re-derived.md` — "no session file is
  treated as authoritative for a value that can be recomputed."

## Assumed

- **That `toolUseResult.agentId` and `<task-notification>` stay the harness's
  spelling for a child starting and a child reporting.** Neither is a documented
  interface. Falsified by a Claude Code release that renames either, which this
  reader would meet as "no children found" — the restart returns to today's
  behaviour rather than to a wrong one, which is why both readers treat absence
  as *nothing outstanding*.
- **That a child launched before a `/clear` never reappears as outstanding
  after it.** A clear starts a new transcript file, so the launch is not in it.
  Falsified by a harness that appends a cleared session's continuation to the
  same file, which would hold every later restart on a branch with nothing able
  to release it.

## Direct baseline

A verb — `wfctl restart child <id>` and its counterpart — that the agent calls
when it launches a child and again when the child reports, writing both to
`events.jsonl` beside every other restart event. `decide` then reads one log and
opens the transcript once, as it does today.

## Decision

`outstanding_children(transcript)` reads the harness's transcript. A launch is a
`toolUseResult` carrying a string `agentId`; the report is a later `"type":
"user"` record whose string content begins `<task-notification>` and names that
id. What is outstanding is the difference, re-derived on every reply end, and
wfctl records no child of its own.

The decision event carries the resulting descriptions so the log says which
children held the restart. That is a note about a decision already made, not the
ledger the decision was made from.

## Diagram

```
             baseline                             decision

          ┌────────────────────────┐          ┌────────────────────────┐
stable    │ decide()               │          │ decide()               │
          └────────────────────────┘          └────────────────────────┘
              ▲ reads  ▲ reads                    ▲ reads   ▲ reads
          ┌───┴────────┴───────────┐          ┌───┴────────┐│
          │ events.jsonl           │          │events.jsonl││
          │  + child-launched      │          │            ││
          │  + child-reported      │          └────────────┘│
          └────────────────────────┘                        │
              ▲ writes                                      │
          ┌───┴────────────────────┐                        │
          │ the agent, once per    │                        │
          │ launch and per report  │                        │
          └────────────────────────┘                        │
══ session-state-is-re-derived: wfctl's record │ the harness's ═══════════
                                                            │
          ┌────────────────────────┐          ┌─────────────┴──────────┐
volatile  │ transcript.jsonl       │          │ transcript.jsonl       │
          │ read for occupancy     │          │ read for occupancy     │
          │                        │          │ and for children       │
          └────────────────────────┘          └────────────────────────┘
```

The graphs differ by which side of the line the fact is read from. In the
baseline the launches cross upward into wfctl's own record and are written by the
one party that cannot be relied on to write them — an agent whose pane is about
to be cleared, and which forgets a call it did not make. In the decision nothing
crosses: the harness already writes both halves for its own purposes, and wfctl
reads them where they are.

## Considered

- **The verb** — the baseline. Sound in shape, and it loses on who does the
  writing. A launch the agent forgot to declare is a child the restart cannot
  see, and the agent most likely to forget is the one with a full window. It also
  makes a wfctl file authoritative for a value recomputable from the harness's
  own record, which `session-state-is-re-derived` forbids in those words.
- **Match `<task-id>` anywhere in the raw line** — one `in` instead of a parse,
  and it reads an agent's own reply as a report. This branch's session put
  `<task-id>` into a reply while building the scanner; the loose read would have
  let the session talk itself out of its own hold. The corpus splits 483 real
  against 10 quoted, so the difference is not hypothetical.
- **Treat any tool call with no result as an outstanding child** — no harness
  vocabulary at all. Wrong on the facts: an async launch gets its result
  immediately, and the completion arrives later as a notification, so this finds
  nothing in exactly the case it was built for.
- **Ask the harness** — there is no interface to ask. The Stop payload carries a
  session id, a transcript path and a cwd, and nothing about children.

## Consequences

The hold costs one extra pass over the transcript, taken only on reply ends over
the threshold with no restart already under way — the rest return before
`find_children` is called.

wfctl now reads two undocumented shapes from another program's file, and a rename
upstream turns the hold off silently. `outstanding_children` is the one place
that would have to change, and its docstring names both shapes so the search
starts there.

Descriptions reach the event log; ids reach neither the log nor the pane. A
person reading a held pane is told how many children are out and not which, which
is the trade the harness's own warning about internal metadata asks for.

## Verification

- `tests/test_restart_children.py` — a launch with no notification is
  outstanding, a notification for a launch this transcript never saw is ignored,
  and an agent quoting the tags does not release the hold.
- `tests/test_restart_hook_cli.py::test_a_fan_out_still_running_holds_the_restart_and_sends_nothing`
  fails when the hold is removed from `decide`, which is the check
  `a-rule-is-expressed-as-a-check` asks for.
- A live run: a pane over the threshold with a panel out holds, and restarts on
  the reply end after the last reviewer reports.

## Log

- 2026-09-22  proposed  — #425; the restart needed to know whether children were
  out, and the only two places that could answer sit on opposite sides of a
  boundary `session-state-is-re-derived` already draws.
