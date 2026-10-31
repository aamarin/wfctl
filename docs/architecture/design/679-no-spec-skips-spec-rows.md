---
status: proposed
governs: evidence-and-derivation
---

# A no-spec branch skips the spec rows in the one step table

## Context

`every-change-answers-spec-question.md` decides that a "no" is written to
`exceptions/spec.md` in the branch's spec folder before any code, and that the
pipeline reads it to send the branch to `implement` and `review`. This record
decides how the step table expresses that route.

#382 asks the same question from the other side: whether a repository can run
a shorter pipeline than the eight spec steps. This record answers only the
no-spec route, and leaves #382's general question open.

## Verified

- `_infer_steps` (`_pipeline.py:411-420`) returns every step `pending` when
  `spec_dir` is None, so `brainstorm` is current on a branch with no spec
  folder.
- `_current_step_name` treats `skipped` like `done`, and
  `_pipeline.py:795` and `:967` both count `("done", "skipped")` as finished.
- `_evidence.implement` (`_evidence.py:1948-1981`) returns `pending` when
  `tasks.md` is missing, and otherwise lets `ev.verification` decide once the
  tasks are closed.
- `next_step_content` routes a blocked `implement` with no open tasks to
  `wfctl verify`.
- `_design_exceptions` (`_design_exceptions.py`) is the one module that writes
  and reads exception files. `wfctl arch none` writes `boundary.md` through it,
  and `_infer_steps` reads pass claims through it.
- `wfctl step none` creates the spec folder when it writes, so a branch with a
  claim always has a spec folder.

## Assumed

- No branch that already has spec artifacts needs to switch to the no-spec
  route. If one does, the person deletes the artifacts, since the pipeline
  ignores the "no" while any of them exist.

## Direct baseline

Each of the seven spec readers, `brainstorm` through `decompose`, checks a new
`Evidence` field and returns `skipped` with the recorded reason when it is set.
`implement` checks the same field and judges by verification alone when
`tasks.md` is missing.

## Decision

`build_evidence` reads `exceptions/spec.md` through `_design_exceptions` into
one `Evidence` field, holding the reason or None. It sets the field to None
when `design.md`, `spec.md`, `plan.md` or `tasks.md` exists, and `wfctl
status` then prints a warning naming the file to delete. The spec steps' own
artifacts outrank the claim, so a branch that flipped to yes and forgot the file
still runs the pipeline.

`Step` gains one field, `spec_step: bool`, set on the seven rows from
`brainstorm` to `decompose`. `_infer_steps` reads each of those rows as
`skipped`, with the reason as its annotation, without calling its reader or
evaluating its passes. That is one check in one place instead of seven.

`implement` reads the field too. With the field set and no `tasks.md`, it skips
the task tally and lets the verification record decide, so its next command is
`wfctl verify`. `store-specs` is unchanged, and it stores the spec folder with
the reason in it.

`wfctl spec none --reason "…"` writes the file through `_design_exceptions`
under the name `spec`, beside `boundary`. It refuses a placeholder reason, as
`arch none` does, and refuses when any of the four spec artifacts exists.

## Diagram

```
            baseline                               decision

stable    ┌───────────────┐                      ┌───────────────┐
          │ _STEPS table  │                      │ _STEPS table  │
          │ 8 rows        │                      │ spec_step flag│
          └───────────────┘                      │ (new)         │
                  ▲ reads                        └───────────────┘
                  │                                      ▲ reads
          ┌───────┴───────┐                      ┌───────┴───────┐
          │ _infer_steps  │                      │ _infer_steps  │
          └───────────────┘                      │ skips flagged │
             │ calls ×7                          │ rows (new)    │
             ▼                                   └───────────────┘
          ┌───────────────┐                         │ calls ×1
          │ 7 spec readers│                         ▼
          │ each checks   │                      ┌───────────────┐
          │ no_spec       │                      │ implement     │
          └───────────────┘                      │ reader        │
             │ reads ×8                          └───────────────┘
════ the spec folder: exceptions/ written only by wfctl ════════════
             ▼                                      │ reads ×2
          ┌───────────────┐                      ┌───────────────┐
          │ Evidence      │                      │ Evidence      │
          │ no_spec       │                      │ no_spec       │
          └───────────────┘                      └───────────────┘
```

The divider is the one `design-exceptions-live-with-specs.md` drew: the spec
folder holds a branch's exceptions, and only wfctl's commands write them.
Neither graph adds a divider.

The change the decision is built to absorb is a new spec step, or a step
removed, as #382 or Spec Kit may bring. In the baseline every new spec reader
has to remember the check, and one that doesn't would read `pending` and hold a
no-spec branch at a step it was told to skip. In the decision the new row sets
one flag. The baseline reads the field from eight readers, and the decision
reads it from two places, `_infer_steps` and `implement`.

## Considered

- **The direct baseline, a check in each reader.** It is correct today. We
  didn't choose it because a spec reader added later that forgets the check
  holds a no-spec branch with no error, and nothing would report that it was
  forgotten.
- **A second step table for the short route, as #382 proposes.** It would let
  `wfctl status` show two rows instead of nine with seven skipped. We didn't
  choose it here because #382 has to answer #100's objection to a registry
  first, and a no-spec branch still benefits from seeing the steps it skipped
  and why. If #382 lands, the flag is the list of rows its short table leaves
  out.
- **Infer the route from the missing spec folder.** Ruled out at level 2, by
  `an-absent-artifact-is-claimed-not-inferred.md`.

## Consequences

A no-spec branch shows seven skipped rows, each with the reason, then
`implement` and `review`. The reason is on screen for the reviewer to compare
with the diff.

A branch that records "no" and later starts brainstorm reads the full pipeline
again as soon as `design.md` exists, and the warning names the stale file.
Nothing stops an agent from recording "no" after the code is written. That gap
is stated in the level-2 record.

## Verification

- A test where `exceptions/spec.md` exists and no spec artifact does: seven
  rows read `skipped` with the reason, `implement` routes to `wfctl verify`,
  and once verified, `review` is current.
- A test where both `exceptions/spec.md` and `design.md` exist: the pipeline
  reads as if the claim were absent, and the warning names the file.
- A test that `wfctl spec none` refuses when `spec.md` exists, and refuses a
  placeholder reason.

## Log

- 2026-10-31  proposed  — #679 level 3: how the step table expresses the
  no-spec route the level-2 record decided
