# Flip clarify and analyze to automatic — #325

## Problem Statement

Two of the pipeline's eight steps still stop and wait for a human: `clarify` and
`analyze`. They are the last two.

They waited because their only output used to be their own say-so — a pass that
found nothing and a pass that never ran produced the same evidence. That is no
longer true. `#307`/`#320` gave both steps a scan file committed into the
repository at `<arch-root>/scans/<issue>-<step>.md`, so a reviewer opening the PR
can see what was covered. `#286`/`#322` made `clarify` record the options it
rejected and why each lost, so its artifact is no longer a claim by the claimant.
`#299` made the payload say which of four facts a step answered, so a report can
now express what a step proved rather than collapsing it into one state.

Everything these two steps were waiting on has shipped. Nobody has flipped them.

## Recommended Direction

Change two values in `_STEPS`, from `_REVIEW_REQUIRED` to `_AUTOMATIC`, and
update the one test that pins the table. Nothing else.

### Level 1 — behavior

The flag reaches a reader only when `clarify` or `analyze` is the current step.
Three reachable current-states, which collapse to two rows: `clarify` at
`pending` and `clarify` at `in_progress` (markers still standing) render
identically, because neither predicate arm sets a `reason`.

```
clarify current  (pending, or in_progress with markers standing)

  before                                after
  → Next step: /speckit.clarify         → Next step: /speckit.clarify
    (auto: false)                         (auto: true)

  next-step.md                          next-step.md
    Next step: /speckit.clarify           Next step: /speckit.clarify
    auto: false                           auto: true
    Run this command to continue.         Run this command to continue.

  speckit-orchestrate                   speckit-orchestrate
    Next: run `/speckit.clarify`          EXECUTE_COMMAND: speckit.clarify
    when ready.            → stops                              → runs it
```

`analyze` renders the same three strings with `/speckit.analyze`, from its one
reachable current-state, `pending`.

Every string is true in its state. `auto: true` claims the loop may proceed past
this step without pausing, and that claim is now backed by a committed scan file
plus, for `clarify`, the rejected options and why each lost.

**The level-3 consequence this generates**, which is the test for whether level 1
finished: `auto` is computed at exactly one site, `_pipeline.py:345`. So the
change must be a table edit and no new branch. A per-step arm added to
`next_step_content` would make a second site compute the same fact, which
`pipeline-state-is-one-payload` forbids.

### Level 2 — architecture

```
step definition                 │  the run
────────────────────────────────┼───────────────────────────────
_STEPS table                    │
  clarify:  automatic       ────┼─►  next_step_content → (cmd, True)
  analyze:  automatic           │
                                │      speckit-orchestrate
                                │        EXECUTE_COMMAND
                                │
predicate sets a reason     ────┼─►  overrides to False
  (never, for these two)        │
```

Nothing crosses that did not cross before. Authority for *may the loop proceed
past a finished step* already sits in `_STEPS`; this changes a value inside that
authority rather than moving it.

**Gate answer: no boundary drawn, no record.** Declared with `wfctl arch none`.
The reason on record: `#100` decided what a gate proves and `#287` decided what a
gate's silence means; this applies both answers to two steps without moving
either, and introduces no new state, no derived value, and no second computer of
the `auto` flag.

### Level 3 — checked and assumed

```
checked                                    assumed
─────────────────────────────────────      ───────
next_step_content has one per-step         (none)
  arm, `implement`, firing only when
  `blocked` is truthy

clarify and analyze set `reason` in
  no arm, so `blocked` is always None
  for them; `_infer_steps` attaches
  no reason of its own

_AUTOMATIC has exactly one consumer,
  _pipeline.py:345

pipeline_payload_snapshot.json carries
  no `auto` key — 0 occurrences

both scan files are on `main`
```

The assumed column is empty because every claim was checked against the code
before this document was written, not from memory.

`#240` is the precedent that made the first row necessary: its opening diff was a
single table value, and that alone was wrong, because `next_step_content` has
per-step arms and a step with no arm is governed entirely by the table. The check
was made here and the answer is clean — for these two steps the table really is
the whole answer, in every reachable state.

## Boundaries and Ownership

No boundary is drawn or moved. `_STEPS` owns the continuation value before and
after; `next_step_content` remains its single reader; `speckit-orchestrate`
remains the single consumer of the resulting `auto` value.

A blocked step is never automatic whatever the table says — `next_step_content`
enforces that above the table lookup, and it is what stops an unattended run
walking past an unanswered gate. That guard already exists and is not duplicated
here.

## Key Assumptions to Validate

- **The two steps' artifacts are sufficient evidence to pass without a human.**
  This is the judgment the whole change rests on. It is not derivable from the
  code; it was made by a person and is recorded here as the thing to disagree
  with if the flip proves wrong.
- **No consumer outside `speckit-orchestrate` branches on `auto`.** Checked by
  grep; would be falsified by a future consumer reading the flag for a different
  question.

## MVP Scope

- `wfctl/_pipeline.py` — `clarify` and `analyze` move to `_AUTOMATIC`
- `tests/test_pipeline_sections.py` — the expected dict in
  `test_no_step_changed_the_flag_that_says_it_may_run_unattended`, and its
  docstring, which currently argues from `#309` and must now name `#325`
- one commit, because the evidence that earns each flip already sits on `main` in
  the scan files rather than in this diff; splitting would show a reviewer two
  halves of one judgment and no extra evidence

## Not Doing (and Why)

- **A per-step arm in `next_step_content`.** It would be a second site computing
  `auto`, which `pipeline-state-is-one-payload` forbids, and it is unnecessary:
  neither predicate ever sets a `reason`.
- **A runtime condition on one of the four facts `#299` added.** The flip is a
  property of the step, decided once. Conditioning it on branch state would make
  the pipeline's shape depend on branch state, which is a new boundary and a much
  larger change.
- **Regenerating `tests/pipeline_payload_snapshot.json`.** It pins `_infer_steps`
  output, which carries no `auto` key. If it needs regeneration, that is a
  finding to explain rather than a file to regenerate.
- **`analyze`'s remediation policy.** Filed as `#331`. Step 8 asks the user
  whether to apply remediation and waits; unattended, no rule says what to apply
  and what to file. The flip is a strengthening either way, but `#147`'s
  acceptance test is not meaningful while that pause stands.
- **A structural check on the scan file.** Filed as `#330`. `wfctl` calls these
  steps done on a heading and a filename; the scan file's required shape is
  enforced on the instruction, not on the artifact.

## Software design decisions

None. No structural choice here weighed a credible alternative — the change is
two values in an existing table, and the one alternative considered (a per-step
arm) is ruled out by an accepted record rather than chosen against.

## Open Questions

None outstanding. The commit boundary was the one open question the handoff
carried, and it is answered under *MVP Scope*.
