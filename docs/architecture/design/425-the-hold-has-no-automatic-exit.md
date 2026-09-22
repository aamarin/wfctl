---
status: proposed
---

# The children's hold has no automatic exit; the evidence releases it, or a person does

## Context

#425 asks for the hold's escape hatch by name: "a restart that waits forever is
its own failure, and a threshold that is already exceeded is the case where
waiting is most expensive", and it must be "a decision someone made rather than a
timeout nobody chose."

The pressure is that a child can fail to report. The harness drops a
notification, a subagent dies, a fork never lands — and the transcript then shows
a launch with no report for as long as the session lives. Whatever the hold does
about that, it does unattended: nobody is at the prompt when the restart fires,
which is the point of it.

## Verified

- `wfctl/_restart.py:279` — every reply end re-derives the decision from what it
  reads. There is no wait, no sleep and no retained state between reply ends;
  a held restart is a hook that returned, not a process blocked on anything.
- A held session produces no further reply ends until something happens to it, so
  an unresolved hold costs nothing until a person or a notification arrives.
- `wfctl/_restart.py:372` — `SKIP` already declines a restart wfctl cannot take
  safely, reports it once, and leaves the pane to the person. Its message tells
  them nothing to do because there is nothing they can do about a missing pane.
- `wfctl/_restart.py:373-384` — `NOT_TAKEN`'s two messages each end in an
  instruction: "run /clear yourself, or /end-session first", "run it yourself".
  The vocabulary for handing a restart back to a person is already here.
- `WFCTL_RESTART_THRESHOLD=0` turns the restart off for a shell
  (`371-the-session-restart-threshold-is-an-environment-variable`), and a hook
  reads the environment its pane was launched with — so a variable cannot be the
  release for a hold already in progress.

## Assumed

- **That a child failing to report is rare enough to be a person's problem.**
  Of 489 launches across 320 of this repository's transcripts, 6 have no report
  anywhere on disk — the case a person has to resolve, because nothing else can
  tell a slow child from a dead one. A further 51 reported only into a later
  transcript, the session having been cleared out from under them: those are the
  #425 failure rather than this assumption's risk, and the hold is what removes
  them.

  This number was wrong when the record was first written, and wrongly small.
  It said two, measured with a reader that knew one of the two shapes a
  notification arrives in, so a report absorbed into a running turn counted as no
  report at all. Measuring the hold's own risk with the instrument the hold
  depends on is the mistake worth naming here: the reader was not a detail below
  this decision, it was the decision's evidence.

  Falsified by a harness release that drops notifications routinely, which would
  make held panes the common case rather than the exception. At 6 in 489 that
  condition is not met; at the 200 the first reader reported, it would have been.

## Direct baseline

Hold for a bounded number of consecutive reply ends — three, say — and then
proceed with the restart, recording that the bound was reached.

## Decision

The hold has no automatic exit. It is released when the transcript stops showing
an outstanding child, and by nothing else. The pane message names the other way
out in the same sentence: `run /end-session restart then /clear yourself if they
never report`. Both commands, because the hook sends neither once a hold is on
record — a hand-typed stop records no *planned* end, so the branch that would
send the clear is never reached.

That is the decision #425 asks for. It is not "wait forever" — a held reply end
returns, and the next one re-derives from scratch — and it is not a timeout,
because no duration and no count is chosen on anyone's behalf.

## Diagram

```
             baseline                             decision

          ┌────────────────────────┐          ┌────────────────────────┐
stable    │ decide()               │          │ decide()               │
          │  holds ≤ 3, then sends │          │  holds while out       │
          └────────────────────────┘          └────────────────────────┘
              ▲ reads  ▲ counts                   ▲ reads
          ┌───┴────────┴───────────┐          ┌───┴────────────────────┐
          │ prior hold-children    │          │ outstanding children   │
          │ decisions in the log   │          │ in the transcript      │
          └────────────────────────┘          └────────────────────────┘
                                                  │ names the other exit
                                                  ▼
          ┌────────────────────────┐          ┌────────────────────────┐
volatile  │ the pane: a restart it │          │ the pane: "run         │
          │ did not ask for        │          │ /end-session restart   │
          │                        │          │ then /clear yourself"  │
          └────────────────────────┘          └────────────────────────┘
```

The graphs differ by what the third reply end means. In the baseline it is a
number wfctl picked, and reaching it destroys the context the hold existed to
protect — at the moment the evidence still says the children are out, which is
the one moment the rule forbids clearing. In the decision the same reply end
reads the same evidence and decides the same thing, and the exit is a sentence
addressed to whoever comes back.

## Considered

- **A bounded hold count** — the baseline, and the shape most likely to be
  reached for. It is a timeout with reply ends for units: nobody chose three, it
  correlates with nothing about the children, and it ends by doing the thing the
  hold was built to prevent.
- **A wall-clock bound** — worse on the same axis and worse on its own. A panel
  reviewing a large diff and a dead subagent look identical to a clock, and the
  restart would learn which only by clearing the wrong one.
- **An opt-out variable, `WFCTL_RESTART_CHILDREN=off`** — a standing decision, in
  the same place the threshold already lives, and it cannot release a hold in
  progress: the hook reads the environment the pane was launched with, so setting
  it means relaunching the pane, which clears the context anyway. It would also
  be a second off switch beside `WFCTL_RESTART_THRESHOLD=0`, which already turns
  the whole restart off for the person who never wants it.
- **A release verb, `wfctl restart release --reason "…"`** — the repository's own
  shape for a claim someone made (`wfctl arch none`, `wfctl step none`,
  `wfctl report-block`), and a real option. Rejected for now because the party in
  the pane is usually the agent, and an agent releasing the hold that protects
  its children's results is certifying its own completion — the arrangement
  `wfctl-runs-the-verification` exists to refuse. If a person ever needs it, it
  is an addition to this, not a replacement: they can already do by hand exactly
  what the verb would authorise.

## Consequences

A pane whose child never reports stays full until someone returns to it, and the
line in the pane tells them what to type. That is the same cost `SKIP` already
accepts, arrived at for the same reason: a restart that cannot be taken safely is
handed back rather than taken anyway.

Nothing in wfctl counts holds, so nothing can drift out of step with the
transcript. The absence is the feature.

The failure mode is a person who never reads the pane. The message is printed on
the reply end that first holds and again whenever the outstanding set grows, so a
second fan-out sent later carries its own copy of the escape hatch; a pane
scrolled past between two fan-outs does not. Repeating it on every *shrink*
instead would bury the first copy under a line per child reporting, which is the
one that matters.

## Verification

- `tests/test_restart_decide.py::test_the_children_hold_is_reported_once_and_then_says_nothing`
  and `::test_the_restart_begins_once_the_last_child_has_reported` — the hold
  reports once and ends on evidence.
- `tests/test_restart_decide.py::test_the_children_hold_names_the_escape_hatch_and_no_agent_id`
  — the escape hatch is in the string a person reads, which is the only place it
  exists.
- A live run of the case this record is about: a launch whose notification never
  arrives leaves the pane held, and a hand-typed `/end-session restart` followed
  by `/clear` restarts it.

## Log

- 2026-09-22  proposed  — #425 asked for the escape hatch to be decided rather
  than defaulted, and every automatic exit considered ends by clearing a pane
  whose evidence still says its children are out.
