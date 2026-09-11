---
status: proposed
---

# A pass made progress when the artifacts changed, not when the step line changed

## Context

`wfctl-counts-the-passes` puts the loop bound in wfctl and says the verdict is
computed from the event log. It does not say what makes two passes comparable.
That is this record.

Something has to stand for "what the last pass left behind", cheap enough to
write into an event on every `resume` and precise enough that a pass which
genuinely advanced the work is never mistaken for one that did not. A bound that
fires on healthy work is worse than no bound: the loop exists to run unattended,
and a false stop breaks that at the hour nobody is watching.

## Verified

- `cli.py:648` — `resume` appends one event carrying `step`, `command` and
  `auto`. Nothing about what the step left behind. Confirmed by running
  `wfctl resume` on this branch and reading the line it wrote.
- The same line shows the fingerprint is not in the log today, so whatever is
  chosen here is a field being added rather than one being read.
- `_predicates.py:1166` — `implement`'s annotation is
  `f"{ev.tasks_done}/{ev.tasks_total} done"`, so its progress across passes is
  visible in the rendered line.
- `_predicates.py:1030` — `clarify` with markers standing returns
  `Reading("in_progress")`: no reason, no annotation. `_predicates.py:1006` —
  `specify` does the same. Neither carries how many markers remain.
- `_predicates.py:63,77` — `annotation` defaults to `None` and `rendered` falls
  back to `reason`, so a step with neither renders an empty line in every state
  it can reach.
- `_predicates.py:201-214` — `Evidence` already holds `spec_text`, `plan_text`
  and `tasks_text`, read once per report. `_pipeline.py:472` takes that one read
  for two consumers, so digesting it adds no file read.
- `_pipeline.py:452` — `build_report(spec_dir, repo_root, agent_dir)` already
  receives the state dir, so the log is reachable with no signature change.
- Legacy logs carry two `resume` lines per pass with identical timestamps
  (`59-deployment-key-metadata`); current wfctl writes one.

## Assumed

- That an artifact edit which changes bytes without advancing the work is rare
  enough to ignore. Falsified by a step that rewrites a timestamp or reflows a
  heading on every pass — the digest would move each time and the bound would
  never fire.
- That the three artifact texts cover every step whose progress matters. The
  exposure runs the other way from the assumption above, and is the sharper of
  the two: a step whose evidence lives outside `spec`/`plan`/`tasks` leaves the
  digest unchanged **while it is working**, so consecutive productive passes read
  as a stall. `decompose` opens `delivery.md` inside its own predicate, and
  `implement`'s definition-of-done reaches a verification record and git. What
  those steps risk is a false stop on real work, not a missed one.
- That a pass with no digest is never compared, which puts a branch with no
  resolved spec directory outside the bound entirely. Correct rather than a gap —
  there is nothing to compare — but wider than the `decompose` hole above, and
  worth naming because a loop wedged before any feature directory exists is
  unbounded.

## Direct baseline

Fingerprint the pass with what the payload already renders: the current step's
name, its state, and its rendered line. `resume` has all three in hand at
`cli.py:614-621` — `step_name`, and `blocked`/`remedy` off the report — so the
event gains three strings and the comparison is string equality. No digest, no
new read, no dependency on file contents.

## Decision

A pass's fingerprint is a digest over the artifact text `Evidence` already holds
— `spec_text`, `plan_text`, `tasks_text` — taken during the same inference that
builds the report, and recorded in the `resume` event beside the step name. Three
consecutive passes on one step with an unchanged digest is the bound.

## Diagram

```
          baseline                          decision

stable    ┌────────────┐                    ┌────────────┐
          │  Evidence  │                    │  Evidence  │
          │ spec/plan/ │                    │ spec/plan/ │
          │ tasks text │                    │ tasks text │
          └─────┬──────┘                    └─────┬──────┘
                │ read by                         │ digested by
          ┌─────▼──────┐                    ┌─────▼──────┐
          │  Reading   │                    │   digest   │
          │ state +    │                    │  of bytes  │
          │ rendered   │                    └─────┬──────┘
          └─────┬──────┘                          │
                │ rendered into                   │ written into
          ┌─────▼──────┐                    ┌─────▼──────┐
          │   resume   │                    │   resume   │
          │   event    │                    │   event    │
          └─────┬──────┘                    └─────┬──────┘
                │                                 │
════ wfctl owns the payload ══════════════════════════════════
                │ reads                           │ reads
volatile  ┌─────▼──────┐                    ┌─────▼──────┐
          │ orchestrate│                    │ orchestrate│
          └────────────┘                    └────────────┘
```

Both graphs carry the same components and the same divider; they differ only in
where the fingerprint is taken. The baseline takes it after `Reading` has
collapsed the evidence into a state and a line for a human to read, and that
collapse is lossy in the one direction that matters here — `clarify` renders the
same empty line whether five markers remain or one. The decision takes it before
that collapse, from the bytes the predicates themselves read, so a pass that
resolved two of six markers is distinguishable from one that resolved none.

## Considered

- **The rendered step line** — the direct baseline. It is cheaper, needs no
  digest and no new read, and it is right for `implement`, whose tally moves with
  its progress. It loses on the step the issue was actually filed about: `clarify`
  and `specify` return `Reading("in_progress")` with no reason and no annotation
  while markers stand, so resolving markers one pass at a time is indistinguishable
  from resolving none, and the bound would stop a run that was working.
- **The step name alone**, which #332's own sketch implies — same failure, wider.
  It cannot see `implement` ticking off four tasks either, because the name and
  state are unchanged across every pass of a healthy implementation.
- **An iteration cap on the whole run** — #332's cheapest sketch. Sound, and it
  needs none of this: no fingerprint, no comparison, one integer. It loses because
  a long legitimate pipeline and a stuck one are the same number, so the cap has
  to be set high enough to never fire on real work, which is high enough to be
  most of a night.

## Consequences

Gained: a stall is detected from the evidence rather than from a rendering of it,
so a step that exposes nothing useful in its status line is covered without that
step having to change.

Harder: the fingerprint is now sensitive to edits that do not advance anything.
The failure mode this introduces is a bound that stays quiet — an artifact
rewritten cosmetically each pass resets the count. That is the direction chosen
deliberately: a missed stop is still caught by a person, while a false stop
breaks unattended work.

Also harder: a step whose evidence is a file `Evidence` does not hold advances
without moving the digest, so `decompose` and `implement` can read as stalled
while they are working. That is a false stop, which is the direction this record
otherwise argues against — it is accepted here only because those two steps write
`spec`/`plan`/`tasks` often enough in practice that the case is narrow, and
naming it is what lets a later reader disagree.

## Verification

- A test driving `clarify` across three passes that resolve one marker each, and
  asserting the run does not stop.
- A test driving three passes that resolve none, and asserting it stops and names
  `clarify`.
- A test asserting `implement` at 7/12 then 9/12 does not trip.
- A real unattended run against a repeating step, watched — a test that asserts
  the bound triggers without a run that watched it trigger has not tested this.

## Log

- 2026-09-10  proposed  — #332: `wfctl-counts-the-passes` left open what makes
  two passes comparable, and the obvious answer is wrong for the step the issue
  was filed about.
