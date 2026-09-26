---
status: proposed
---

# The fix for a failing drawing is handed back by the check that found it, beside its reason

## Context

The design step's architecture pass now asks `_arch.accept_blockers` about every
proposed level-2 record on the branch. When a record fails, `wfctl status` shows
two things:

1. The reason, such as `my-record: a sequence drawing with no step that fails: …`.
2. The fix, which is `wfctl arch accept my-record --check`.

The fix has to name the record, and only the check knows which record failed.
Today the fix for the design step is built after the walk by `_design_remedy`,
which recognises the one reason it knows by comparing it against a constant. That
works for a fixed sentence and does not work for a reason that carries a slug.

`pipeline-state-is-one-payload` constrains where the fix is built: in inference,
not in a view. `session-state-is-re-derived` constrains how often: once per read,
with nothing carried between reads.

## Verified

- `_pipeline.py:558` returns no fix unless `step.reason` equals
  `DESIGN_BLOCK_REASON`, a string comparison against a constant.
- `_pipeline.py:347` copies the outstanding pass's `annotation` into the step's
  `reason`; nothing else about the pass reaches the step.
- `_evidence.py:61` `Assessment` carries `state`, `reason`, and `display`, and no
  fix.
- `cli.py:831` reads the reason already computed rather than recomputing it, and
  its comment names the failure a second read causes: two reads of one question
  that can disagree.
- `status-payload.json` types `steps[].remedy` as `string | null` and says nothing
  of its content, so a new value is not a contract change.

## Assumed

- No declared pass (from `wfctl.json`) needs a fix of its own today. If one does,
  it uses the same field, and this record is the reason it can.

## Direct baseline

`_design_remedy` gains a second branch. When the reason matches
`^([a-z0-9-]+): `, it reads the slug out of the reason and returns
`wfctl arch accept <slug> --check`. No type changes, and the check returns only a
reason, as every pass does today.

## Decision

`Assessment` carries an optional `remedy`. The architecture pass returns the
reason and the fix together, since it holds both the slug and the blocker at the
moment it decides. The roll-up copies the outstanding pass's fix to the step
beside its reason, and falls back to `_design_remedy` when the pass gave none, so
the "no architecture record" fix is built exactly as before.

## Diagram

```
           baseline                                decision

  ┌─────────────────┐                     ┌─────────────────┐
  │ accept_blockers │                     │ accept_blockers │
  └─────────────────┘                     └─────────────────┘
           ▲ calls                                 ▲ calls
  ┌────────┴──────────┐                   ┌────────┴──────────┐
  │ architecture pass │                   │ architecture pass │
  └───────────────────┘                   └───────────────────┘
           │ returns reason                        │ returns reason + remedy (new)
           ▼                                       ▼
  ┌───────────────────┐                   ┌───────────────────┐
  │ roll-up           │                   │ roll-up           │
  └───────────────────┘                   └───────────────────┘
           │ reads reason                          │ reads remedy; none given ──┐
           ▼                                       │                            ▼
  ┌───────────────────┐                            │                  ┌───────────────────┐
  │ _design_remedy    │── parses the slug          │                  │ _design_remedy    │
  │                   │   out of the reason        │                  │ (unchanged)       │
  └───────────────────┘   text                     │                  └───────────────────┘
           │ remedy                                │ remedy
═══════════╪══ pipeline-state-is-one-payload ══════╪════════════════════════════════
           ▼                                       ▼
    status, next, resume                    status, next, resume
```

The graphs differ by one dependency. In the baseline, `_design_remedy` depends on
the wording of the reason `accept_blockers` produces, an arrow that exists in the
code and in no signature. The change this is built to absorb is a blocker
reworded in `_arch`: in the baseline it touches that hidden arrow and breaks the
fix with no test failing at the site of the change; in the decision it touches
none, since the slug never passes through text.

## Considered

- Parse the slug back out of the reason (the baseline). It is the smallest
  change, and it couples the fix to the wording of a message that `_arch` owns
  and edits freely, as #495 did.
- Run the check a second time in `_pipeline` to build the fix. It needs no new
  field, and it is two reads of one question in one inference, which `cli.py:831`
  and `next_step_content` were each changed to stop.

## Consequences

A pass can now say how it is cleared, which only the design step could do
before. `_design_remedy` stays as the fallback for its one fixed reason, so there
are two places a design fix comes from. Moving the "no architecture record" fix
into the pass too would leave one, and it is not done here because it needs
`DESIGN_BLOCK_HELP` and `arch_location` moved out of `_pipeline` to avoid an
import cycle.

## Verification

- A branch with a failing proposed record reports `steps[].remedy` as
  `wfctl arch accept <slug> --check` in `status --json`.
- A branch with no record still reports the existing two-way fix, byte for byte,
  against the payload snapshot.
- Rewording a blocker in `_arch.accept_blockers` changes no remedy.

## Log

- 2026-09-26  proposed  — written at the level-3 gate of #498, when the gate started asking the drawing rules
