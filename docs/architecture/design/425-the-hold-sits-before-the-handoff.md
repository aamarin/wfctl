---
status: proposed
---

# The children's hold sits before the handoff, not before the clear

## Context

#425 states the rule as a condition on the clear: "A session may not clear while
it owns unfinished child work whose result has not been durably incorporated."
The restart has two points where it could enforce that, because it sends twice.
Over the threshold it sends `/end-session restart`; once a stop has been recorded
it sends `/clear` and `/start-session`.

Holding the second is the literal reading. Holding the first is a claim about
what the handoff is for: it is the artifact a child's result has to reach, and it
is written by the turn the first send asks for.

Nothing constrains the choice from above. `wfctl-performs-the-session-restart`
(proposed) puts the whole sequence in wfctl's hands and says nothing about where
inside it a condition sits.

## Verified

- `wfctl/_restart.py:331` — with an `end` already sent and no stop after it,
  `decide` returns `HOLD`; the send itself is never repeated.
- `tests/test_restart_decide.py::test_end_is_never_planned_twice_for_one_session`
  — "still over the threshold after a hold is still one request." There is no
  second `/end-session` turn to be had.
- `wfctl/_restart.py:423` — `amend_summary_for_late_events` exists because
  `wfctl end` writes `session-summary.md` mid-turn and anything the same turn
  records afterward has no later step that revisits the file. It folds in
  `notify-action` events and nothing else.
- #425's externalization list names "subagent results not yet folded into durable
  work" among what is lost if it does not reach disk before the clear.
- `wfctl/agents/skills/end-session/SKILL.md` is owned by #397 on a parallel
  branch, which is making the handoff record work in flight. Nothing on this
  branch edits it.

## Assumed

- **That a session does not fan out between the handoff request and the stop it
  waits for.** That window is not one turn. `/end-session` itself walks its steps
  and spawns nothing, but the restart sits in `hold` for as many reply ends as it
  takes for a stop to be recorded, and nothing bounds them — a person who comes
  back to a held pane can run a whole panel inside it, and the first stop after
  that clears the pane with no children check. Falsified by exactly that, and it
  is the case this decision accepts rather than the narrower one-turn version
  first written here.

## Direct baseline

Check for outstanding children in front of every decision that sends, the clear
included. One call site becomes two, and the rule reads exactly as #425 words it.

## Decision

The check runs only where `decide` would *begin* a restart — the branch reached
when no `end` has been planned for this session. A restart already under way runs
to its clear whatever the transcript then shows.

## Diagram

```
             baseline                             decision

          reply end over threshold            reply end over threshold
                   │                                   │
                   ├── children out? ──► hold          ├── children out? ──► hold
                   ▼                                   ▼
             send /end-session                   send /end-session
                   │                                   │
                   ▼                                   ▼
             handoff written ◄── children      children report ──► handoff
             (they are still out)                       │          written
                   │                                   ▼
                   ├── children out? ──► hold    stop recorded
                   ▼                                   │
             stop recorded                             ▼
                   │                              send /clear
                   ▼
              send /clear
```

The graphs differ by where the children's results sit relative to the handoff. In
the baseline the handoff is written while they are still out, so the second check
holds a clear over a summary that already cannot describe them, and there is no
second `/end-session` turn to correct it. In the decision the handoff is the last
thing written, after the reports have landed, so the artifact the next session
reads is the one that can carry them.

## Considered

- **Both points** — the baseline. It enforces #425's sentence as written, and it
  is the one alternative that closes the exposure this decision accepts: a child
  spawned *after* the handoff request has gone out is lost in the clear, and a
  second check on the clear path would catch it. What it costs is one more
  transcript pass per restart, 20–28 ms on the largest transcripts here. It was
  not taken because the child it would save is one this session chose to launch
  after asking to be restarted, and holding the clear for it reopens a restart
  already under way — the thing
  `test_a_restart_already_under_way_is_not_held_by_a_later_child` pins. If that
  exposure is ever met in practice, this is the bullet to reverse.
- **The clear only** — the most literal reading, and the weakest. It permits the
  exact sequence #425 is about, with the fan-out's results arriving after the
  summary and the clear merely delayed.
- **Hold the clear and amend the summary when the children land**, reusing
  `amend_summary_for_late_events`. It would work, and it is a durable-execution
  shape in miniature: wfctl would be deciding what a child's result means and
  where in someone's prose it belongs. #425's own scope rules that out, and
  holding earlier makes it unnecessary.
- **Let `end-session` refuse instead** — the handoff turn declining to write
  while children are out. That file is #397's on a parallel branch, and a refusal
  there leaves the pane over the threshold with no recorded stop, which `decide`
  already reads as `HOLD`: two holds for one condition, in two repositories of
  rules.

## Consequences

A fan-out that ends normally restarts one reply end later than it would have, and
its handoff can name what the panel found.

A session that spawns a child *after* its handoff request has gone out loses that
child in the clear. No check covers it, deliberately, and the assumption above is
where a later reader finds out.

The two hold conditions now share a name and differ by kind — `hold` for a
handoff that never landed, `hold-children` for children still out. A reader of
`events.jsonl` can tell which held a restart without reading the code.

## Verification

- `tests/test_restart_decide.py::test_a_restart_already_under_way_is_not_held_by_a_later_child`
  — a `CLEAR` with children outstanding still clears, which is the half of this
  decision that looks like a bug until the record is read.
- `tests/test_restart_decide.py::test_the_restart_begins_once_the_last_child_has_reported`
  — the hold's ordinary exit is the next reply end, not a retry.
- A live run: the handoff written after a held fan-out names the panel's
  findings, and the one written without the hold does not.

## Log

- 2026-09-22  proposed  — #425; the rule is worded as a condition on the clear
  and the artifact it protects is written a turn earlier, so enforcing it where
  it is written would have protected the wrong thing.
