---
status: rejected
---

# The recycle verdict is a field on the one report, shaped like `stall`

## Context

`wfctl-owns-the-recycle-verdict` puts the verdict in wfctl's hands and
`wfctl-names-the-reset-it-cannot-perform` puts the performing outside it.
Neither says what the verdict looks like on the wire, and the shape is a real
choice: the run reads it once per task boundary, in the same breath as
`next_command`, `auto` and `stall`, and every reader of pipeline state is a
rendering of one payload (`pipeline-state-is-one-payload`).

The pressure is that `speckit-orchestrate` step 5 is already a four-way branch —
story complete, stall, `auto: true`, `auto: false` — and each arm was ordered
against the others for a stated reason. A fifth condition has to slot into that
order rather than sit beside it.

## Verified

- `wfctl/_pipeline.py:357` — `PipelineReport` is a frozen dataclass whose
  `stall: "_stall.Stall | None" = None` field (414) carries #332's verdict, under
  the comment at 409-410: "A field on the one report rather than a second read by
  whoever runs the loop".
- `wfctl/_stall.py:210` — `find_stall(agent_dir, branch, current, covered)`
  reads `events.jsonl` and returns `Stall | None`; nothing about it touches the
  step table.
- `wfctl/_pipeline.py:62-71` — `_STEPS` is eight rows, each
  `Step(command, continuation, predicate)`; the module comment at 32-33 says a
  step "defined here carries both values or it does not parse".
- `wfctl/cli.py:4733` — the `Stop` hook reads `payload.get("transcript_path")`,
  so wfctl is already handed the file that carries occupancy.
- The transcript's last assistant message carries
  `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`, and
  read live in this session the three summed to 89,765. **What that sum is a
  proportion of is not verified.** The same run's statusline read 14%, which
  would put the window at roughly 641K — no published size — and #188's own
  comment reports 207,497 for the same pass. So the fields exist and can be
  added up; the step from that number to "the window is 14% full" is the one a
  threshold would rest on, and it was never taken.
- `speckit-orchestrate/SKILL.md` step 5 orders story-complete before `stall`
  before `auto`, and says both orderings are "load-bearing".

## Assumed

- That a `/clear` delivered by `workmux send` executes as a slash command rather
  than arriving as literal text. Delivery itself is verified (probe 7731 reached
  this pane and was surfaced as a user message); what is bet on is that a
  leading `/` at the prompt is parsed the way a typed one is. Falsified by a
  send that leaves `/clear` sitting in the transcript as text.
- That `workmux wait` can hold until the pane is idle and that a detached
  process surviving the agent's turn can then send. Falsified by `wait`
  returning while the agent is still mid-turn, which would reproduce probe
  7731's mid-turn arrival.
- That occupancy read from the last assistant message is stable enough to
  threshold on. Falsified by a run where the figure swings across the threshold
  between two adjacent task boundaries with no intervening work.
- That the summed usage fields correspond to what the statusline reports, so a
  threshold can be written as a fraction of the window rather than as a raw
  count. The one paired reading above does not support it, and nothing here
  establishes the denominator; a threshold shipped before this is settled would
  fire against a window size nobody checked.

## Direct baseline

Add no field. Put the reading on the existing `reason`/`remedy` pair that a
blocked step already carries: when occupancy is past the threshold, `resume`
marks the current step `in_progress` with reason "window full — recycle before
continuing" and a remedy naming the two commands. Orchestrate's `auto: false`
arm already displays a reason and its remedy, so no branch is added and no
consumer changes.

## Decision

The verdict is its own field — `recycle: Recycle | None` on `PipelineReport`,
built by a `_recycle.py` that reads occupancy the way `_stall.py` reads passes.
Orchestrate gains a fifth arm, between `stall` and `auto`.

## Diagram

```
             baseline                               decision
stable     ┌──────────────────┐                   ┌──────────────────┐
           │  PipelineReport  │                   │  PipelineReport  │
           └──────────────────┘                   └──────────────────┘
              │reads       │reads                │reads     │reads      │reads
              │            │                     │          │           │
════ pipeline-state-is-one-payload ═══════════════════════════════════════════════
         ┌────────┐ ┌─────────────┐         ┌────────┐ ┌────────┐ ┌──────────┐
volatile │ _stall │ │ _predicates │         │ _stall │ │ _pred. │ │ _recycle │
         └────────┘ └─────────────┘         └────────┘ └────────┘ └──────────┘
                     │           │                          │           │
                     │writes     │reads                     │writes     │reads
                     ▼           ▼                          ▼           ▼
                 ┌──────┐ ┌────────────┐                ┌──────┐ ┌────────────┐
                 │ step │ │ transcript │                │ step │ │ transcript │
                 └──────┘ └────────────┘                └──────┘ └────────────┘
```

The two differ by which existing component absorbs the new fact, and by nothing
else — both sides read the transcript, and both still write `step`. The baseline
routes the reading through `_predicates`, so "the window is full" becomes a
property of a *step* — and the step table's own module comment says a row carries
a command, a continuation and a predicate, all three of which are about how that
step is advanced. Window occupancy is true of the run, not of `plan` rather than
`tasks`. The decision gives it a sibling of `_stall`, which is the component
already shaped for a fact about the run that is read from outside the step
table. No divider moves in either graph; both sit under the same payload
boundary already in force.

The arrows across the divider point the way the imports run: `_pipeline.py:23`
imports `_stall` and `_predicates`, so the report reads them and neither reads
the report.

## Considered

- **Reason and remedy on the current step** — the direct baseline. It ships with
  no new field and no new orchestrate arm, and it is genuinely the cheapest
  thing that works. It loses because `reason` means "something re-entering this
  step has to supply", which orchestrate's own prose states, and a full window
  is supplied by nothing the step can do. It would also make every step's
  `reason` ambiguous for the one consumer that routes on it.
- **A ninth pipeline step, `recycle`** — considered and rejected on the same
  ground the baseline loses on, from the other side. A step is something the
  pipeline advances *through* once; a recycle can fire between any two steps and
  more than once per run, so it would need a predicate that is never satisfied
  and a row that never reports `done`.
- **Reuse `stall` with a widened reason** — equally sound at the wire level, and
  rejected on what it would cost the reader. Orchestrate's prose distinguishes a
  stall ("re-entering has already been tried") from a block ("something has to
  be supplied"), and a recycle is neither: the work is progressing fine and the
  window is the problem. Collapsing them would make the one field answer two
  questions that call for opposite actions — stop for a person, versus reset and
  carry on.
- **No field at all; the `Stop` hook injects the instruction** — option B's
  shape. Rejected in `wfctl-owns-the-recycle-verdict` for where the answer lands,
  and the same argument decides the shape: a fact that exists only in the
  agent's context cannot be rendered by `wfctl status` after the scrollback is
  gone.

## Consequences

`resume` records an occupancy reading per pass, joining the evidence digest it
already writes. That is history, not cached state, for the reason `_stall.py`
gives about its own digest — a past pass's window cannot be re-derived.

Orchestrate's step 5 grows to five arms, and the new one has to sit after
`stall` and before `auto` for the reason the existing order already encodes: a
run that has stalled needs a person, and recycling it would throw away the
context that person is about to be asked to look at.

The failure mode this introduces is a recycle loop. If the reading is taken
after the reset and the threshold is misread, the run recycles, comes back
reporting near-empty, and proceeds — but if the reading is taken from a
transcript that survives the clear, it could recycle immediately and forever.
The `Verification` below is written against that case specifically.

## Verification

- A run driven to the threshold recycles once, and the session that comes back
  reports its pipeline position from artifacts with no reference to anything
  that survived. That is the acceptance test #188 names, and it cannot be
  asserted in `pytest` — a marker asserted in a unit test and never fired has
  not tested the cycle.
- After a recycle, `wfctl status` on the same branch still answers "has this run
  recycled, and when?" from the event log. If it cannot, the field landed in
  orchestrate's output rather than in the payload.
- Two adjacent task boundaries with no work between them produce the same
  verdict. A differing pair falsifies the stability assumption above.
- `find_recycle` returns `None` for a branch whose transcript cannot be read, on
  the same posture `_hook_user_prompt` takes: a run that is otherwise fine is
  not stopped by an unreadable file.

## Log

- 2026-09-11  proposed  — #188: the verdict has an owner and a performer, and
  needed a shape before either could be built against it.
- 2026-09-11  rejected  — #188 closed as completed by `aamarin`, against the
  design pass's own recommendation rather than for lack of work. There is no
  payload field because there is no wfctl-side feature to carry one. The shape
  argument against a ninth step and against overloading `reason` still applies
  to whatever next wants a fact about the run rather than about a step.
- 2026-09-11  amended   — the `Verified` anchors were off by one to three lines
  and the diagram's arrows ran against the imports; both corrected, and the
  statusline correspondence moved out of `Verified` into `Assumed`, where the
  one paired reading puts it.
