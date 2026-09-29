---
status: proposed
---

# Warnings reach the routing views as one list the report derives

## Context

`check-rework-loop` has a check that finds a problem after its gate report its
step or pass `done` or `skipped`, with the problem as its `reason`. That record
also requires every view that routes the pipeline to show the warning, and four
views route it: `wfctl next`, `wfctl resume`, `next-step.md`, and
`speckit-orchestrate`. Each of them reads the current step's reason and nothing
else, so a warning on a finished step reaches none of them today.

A warning can sit in two places. A step reader can return one, as `decompose`
does, and a pass reader can return one, as the drawing check will once it
follows the loop. The payload serializes a step's reason, and it does not
serialize a pass's reason at all.

`pipeline-state-is-one-payload` constrains the choice. Every view renders the
payload and computes nothing, so deciding what counts as a warning cannot happen
inside a view.

## Verified

- `wfctl/cli.py`, `next_cmd`: `blocked = next((s.reason for s in steps if
  s.name == step_name), None)`, which is the current step's reason only.
- `wfctl/cli.py`, `resume_cmd`: `blocked = next((s["reason"] for s in
  report.steps if s["name"] == step_name), None)`, the same read off the report.
- `speckit-orchestrate/SKILL.md` step 4 reads "the current step's `reason` and
  `remedy`" off `wfctl status --json`, and nothing from any other step.
- `_pipeline._PipelineSubStep` docstring: "the payload's `sub_steps` never
  serializes" the remedy, and the serializer in `build_report` writes no
  `reason` key for a pass either.
- `_evidence.decompose` returns `Assessment("in_progress" if ev.tasks_open else
  "done", reason)`, which is a finished step with a reason.
- `_evidence.implement` returns `Assessment("done", None, tally)`, which is a
  finished step with a `display` and no reason. A reason on a finished step and a
  display on one are already distinguishable.
- `_pipeline._current_step_name` skips every step whose state is `done` or
  `skipped`, so a finished step's reason never reaches `next_step_content`.
- `PipelineReport.attention` is derived in `build_report` from material that
  function has already read, and serialized as its own key. It is the precedent
  for a derived field on the report.
- `STATUS_PAYLOAD_VERSION` is `"1.1"`, and `_contract.py` treats a new path as a
  minor bump.

## Assumed

- No consumer outside this repository reads `steps[].reason` on a finished step
  and treats it as a held step. Falsified by any such reader; the payload is
  versioned, and a new key rather than a changed one is what keeps this cheap.
- A pass reader and its step reader will not both return a warning often enough
  for the list's length to matter. Falsified by a status view that becomes hard
  to read; nothing here caps the list.

## Direct baseline

Each view finds the warnings itself. The payload gains `reason` and `remedy` on
every pass, and `next`, `resume`, the console `status`, and the orchestrate
skill each walk `steps[]` and `steps[].sub_steps[]` and pick out the entries
whose state is `done` or `skipped` and whose reason is set. No new field is
added to the report.

## Decision

Inference derives the list once. A function in `_pipeline` walks the steps it
has already inferred, collects every step and pass that reads `done` or
`skipped` with a reason, and returns them in pipeline order. `build_report`
stores the result on the report as `warnings`, and `status --json` serializes it
as a top-level key: a list of objects carrying `step`, `pass` (null for a step's
own warning), `reason`, and `remedy`. `next` calls the same function on the
steps it infers, since it does not build a report. Every view renders the list
and decides nothing.

## Diagram

```
          baseline                                decision

stable    ┌───────────┐                          ┌───────────┐
          │ readers   │                          │ readers   │
          └─────┬─────┘                          └─────┬─────┘
                │ returns Assessment                   │ returns Assessment
          ┌─────▼─────┐                          ┌─────▼─────┐
          │ inference │                          │ inference │
          └─────┬─────┘                          │ warnings()│ (new)
                │ writes steps, passes           └─────┬─────┘
                │ (+ pass reason, remedy)              │ writes steps, warnings (new)
═══ pipeline-state-is-one-payload ══════════════════════╪═══════════════════
                │                                      │
volatile  ┌─────┴──────────────────────┐        ┌──────┴─────────────────────┐
          │ reads steps + passes,      │        │ reads warnings             │
          │ applies the rule, x4:      │        │ x4: next, resume,          │
          │ next, resume, status,      │        │ status, orchestrate        │
          │ orchestrate                │        │                            │
          └────────────────────────────┘        └────────────────────────────┘
```

The change the decision is built to absorb is a change to what counts as a
warning, such as a later check deciding that a `skipped` pass with a reason is
informational. In the baseline that touches four arrows, one per view, and one
of the four is prose in a skill that no test runs. In the decision it touches
one function above the line. The graphs differ by one function added to
inference and by the rule moving from below the divider to above it, which is
where `pipeline-state-is-one-payload` already says it belongs.

## Considered

- Each view finds the warnings, per **Direct baseline**. It adds no field to
  the report, and it puts the rule in four places, one of them a skill, which is
  the computation in a view that `pipeline-state-is-one-payload` rules out.
- The roll-up copies a finished pass's reason onto its finished step, the way it
  already copies an outstanding pass's reason onto a held step. It adds no key
  at all, and views could read `steps[]` alone. It loses which pass raised the
  problem, it collides with a step that carries a warning of its own, and it
  rewrites the step's annotation, so `wfctl status` prints the same text on the
  step row and the pass row.
- Carry warnings in `attention`. It is the one field the orchestrate skill
  already treats as "look here", and it is the wrong shape: `attention` holds at
  most one condition, and it means a person is wanted. A warning does not stop
  the run and does not need a person, and holding one would drop the rest.

## Consequences

`status --json` gains a key, and the payload version moves from 1.1 to 1.2.
`next-step.md` gains a line per warning, so an agent that reads only that file
sees them.

A check author adds a warning by returning a reason on a finished step or pass,
and does nothing to any view. That is what makes the drawing check's adoption a
change to one reader.

The list is recomputed on every read, like every other value in the payload, so
a warning disappears as soon as the fix lands, with nothing to clear.

## Verification

A test in wfctl's suite builds a feature whose `decompose` reads done with a
reason, and asserts that the warning appears in `status --json` under
`warnings`, in `next-step.md` after `wfctl next` and after `wfctl resume`, and
that `current` and `next_command` are identical to the same feature without the
warning. A second test does the same for a pass that reads done with a reason.
The contract test fails until `status-payload.json` records the new key at 1.2.

## Log

- 2026-09-29  proposed  — #532. The rework loop requires a warning to reach the
  views that route, and none of them read a finished step.
