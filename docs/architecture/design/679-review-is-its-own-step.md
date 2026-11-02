---
status: proposed
governs: evidence-and-derivation
---

# Review is a ninth step, not a pass under implement

## Context

`review-step-reads-guard-state.md` decides that the pipeline shows whether every
review group has reviewed HEAD, and that it reads the same files as the PR
guard. This record decides where that reading sits in the step table, and how
the guard and the pipeline share the code that computes it.

Two shapes fit the table as it is. A step is a row with its own command and
reader. A pass is a sub-step that `wfctl status` checks once its step reads
done, and an outstanding pass holds its step at `in_progress`. `store-specs` is
a pass under `implement` today.

## Verified

- `wfctl/_pipeline.py:112-157` holds `_STEPS`, and its insertion order is the
  pipeline order. `_STEP_NAMES = list(_STEPS)` at line 159.
- `_infer_steps` (`_pipeline.py:357-491`) cascades `pending` to every later
  step once a step's own reading is `pending`, and rolls an outstanding pass
  up into its step's state and reason.
- `_review_gate._judge` (`_review_gate.py:850-891`) computes the guard's answer
  in four calls: `trunk_refs`, `_review_config.required_at`,
  `resolve_agent_dir`, then `_review.unreviewed` over
  `_review.coverage_from_state`. It formats the result with
  `_review.pending_lines`.
- `build_evidence` (`_evidence.py:1348`) reads every input once for all
  readers, and `verification_block(repo_root)` is the precedent for a
  git-reading value computed there.
- `wfctl step complete implement` refuses unless the current step is
  `implement` or the story is complete (`cli.py:2471`).
- `report-block` falls back to `_STEP_NAMES[-1]` when the pipeline is complete
  (`cli.py:596`), and that is `implement` today.

## Assumed

- The guard's computation is fast enough to run on every `wfctl status`. It is
  one `git rev-list` per group plus two `git show` reads of `wfctl.json`. A
  status that visibly slows on a branch with a long history would falsify it.

## Direct baseline

Add `review` as a pass under `implement`, beside `store-specs`, with a reader
that calls the four functions the guard calls. `implement` reads `in_progress`
until review is done, with the pass's reason, and `wfctl status` shows no new
row.

## Decision

`review` is a ninth row in `_STEPS`, after `implement`, with
`/fanning-out-code-review` as its command and `_AUTOMATIC` as its `on_finish`,
so an unattended run goes on into the panel. Its reader reads `pending` until
`implement` is done or skipped, and otherwise reads one new `Evidence` field.

The four calls the guard makes move into one function in `_review`, which
returns the unreviewed commits per group, or the reason the config can't be
read. `_review_gate._judge` and `build_evidence` both call it, so the guard and
the pipeline can't drift apart one edit at a time.

`step complete implement` also accepts `review` as the current step.
`report-block` names `implement` as its fallback instead of the last row, so a
block filed after the story is complete still holds `implement`, as it does
today.

## Diagram

```
            baseline                               decision

stable    ┌──────────────┐                       ┌──────────────┐
          │ _review      │                       │ _review      │
          │ coverage,    │                       │ pending_at_  │
          │ unreviewed   │                       │ head (new)   │
          └──────────────┘                       └──────────────┘
            ▲         ▲                            ▲         ▲
════ the review state files, written only by review check / sign-off ════
            │ calls   │ calls                      │ calls   │ calls
volatile  ┌─┴──────┐ ┌┴──────────────┐         ┌───┴────┐ ┌──┴──────────┐
          │ guard  │ │ implement     │         │ guard  │ │ evidence    │
          │ _judge │ │ review pass   │         │ _judge │ │ review field│
          └────────┘ └───────────────┘         └────────┘ └─────────────┘
                       │ holds                              │ read by
                     ┌─┴────────┐                         ┌─┴──────────┐
                     │implement │                         │review step │
                     │  row     │                         │ (new row)  │
                     └──────────┘                         └────────────┘
```

The divider is the line `review-step-reads-guard-state.md` already drew: only
`review check` and `review sign-off` write those files. Neither graph adds a
divider.

The change the decision is built to absorb is a change to how the guard
computes coverage, such as reading a new sign-off kind. In the baseline that
change touches two callers, since the guard and the pass each assemble the four
calls. In the decision it touches one function. The baseline also has one
arrow the decision lacks: the pass holds the `implement` row, so "implementation
is unfinished" and "review is outstanding" read as the same state.

## Considered

- **The direct baseline, a pass under `implement`.** It adds no row, and passes
  already roll up correctly. We didn't choose it because `implement` would read
  `in_progress` with the tasks all done and verify green. The reason line would
  then carry review's text under a row named for implementation, and a reader
  couldn't tell unfinished code from unreviewed code. Review also has its own command
  and its own place in the lifecycle: opening a PR depends on it, which
  `a-repo-concern-earns-a-step-hook-or-method.md` names as the test for a step.
- **The reader assembles the four calls itself, as the guard does.** It is
  equally correct today. We didn't choose it because the level-2 record's
  argument is that the guard and status give the same answer, and two copies of
  the computation keep that true only by convention.
- **A repo-declared pass in `wfctl.json`.** Ruled out at level 2: a declared
  pass reads done once its evidence file exists and stays done after later
  commits.

## Consequences

Every test that enumerates `_STEP_NAMES` gains a row, including
`tests/pipeline_payload_snapshot.json` and the step lists in `test_evidence.py`
and `test_pipeline_commands.py`. README.md's "eight steps" and
`speckit-orchestrate`'s story-complete handling change with it.

The status payload's shape doesn't change, since step names aren't enumerated in
`wfctl/contracts/status-payload.json`. A consumer that hardcoded eight steps or
treated `implement` as the last one sees a new row. That is a change of meaning
under the same keys, so the payload version moves from 1.3 to 1.4.

A review config that can't be read leaves the step `in_progress` with the
reason, never `done`, which matches the guard refusing on the same error.

## Verification

- A test where every group has reviewed HEAD reads `review` as done, and one
  commit later reads it `in_progress` with that group's count.
- A test that the guard and the review step give the same answer for the same
  fixture, with and without a sign-off.
- A test that `step complete implement` succeeds while `review` is current.
- The real flow from the handoff, run on this branch before the PR.

## Log

- 2026-10-31  proposed  — #679 level 3: where the review reading sits in the
  step table, and how the guard and status share it
