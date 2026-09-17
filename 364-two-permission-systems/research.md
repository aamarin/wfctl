# Research: two permission systems

**Feature**: `364-two-permission-systems` | **Date**: 2026-09-13
**Phase**: 0 — resolve unknowns before design

The structural questions were settled before this step, at design levels 2 and 3,
and those records bind here rather than being re-argued:

- `docs/architecture/the-agent-reports-the-block-wfctl-never-saw.md` (level 2,
  proposed) — who owns which half of the truth.
- `docs/architecture/design/364-the-block-report-is-its-own-verb.md` (level 3,
  proposed) — the verb, its release, and the four shapes rejected.

What is below is what those records left for this step: the code facts the plan
is written against, and the three unknowns the Technical Context raised.

## Decision: the event kind is `blocked`, written by a command that reads no grant

**Rationale**: The level-3 record's whole argument. `notify_cmd` calls
`action_grant` at `wfctl/cli.py:377` and exits 1 before either of its two
recording paths, deliberately and pinned by that feature's FR-011. A host-blocked
run is by construction one that may hold no grant, so the existing command
refuses exactly the report this feature exists to collect.

**Alternatives considered**: `--blocked` on `notify` (reopens that gate from
underneath), `--declined` (asserts authority the run did not hold), `--blocked`
on `end` (a killed run reports nothing), a `notify` sub-group (the spelling is
taken by the positional argument). Each is argued in full in the level-3 record.

## Decision: the hold is a new predicate, not a reuse of an existing reader

**Rationale**: Nothing reads any `notify-*` event back today. The readers of
`events.jsonl` are `_session.py:55` (`start`), `_session.py:360`
(`notify-resolved`), and `_stall.py:189`/`_stall.py:224`. Verified again for this
plan:

```
$ grep -rn "notify-action\|notify-declined\|notify-refused" wfctl/
wfctl/_session.py:406   append_event(... "notify-action" ...)     write
wfctl/_session.py:422   append_event(... "notify-declined" ...)   write
wfctl/_session.py:433   append_event(... "notify-refused" ...)    write
```

Three writes, no reads. So a predicate is needed whichever verb writes the event,
and its cost is not a difference between any of the options.

**Shape**: `verification_block(repo_root) -> str | None` at
`wfctl/_predicates.py:506` — first matching reason or `None`, read into the
payload at `wfctl/_pipeline.py:492`. The block predicate copies it.

**Alternatives considered**: computing the hold inside each step's own predicate.
Rejected on FR-011 and on the level-3 record's own verification list — a hold
wired as a rule `implement` alone consults fails the case the level-2 record is
about, which is a tracker write at the tail of *any* step.

## Decision: the hold is applied to the inferred list, after the per-step read

**Rationale**: FR-011 requires the hold to override a step that would otherwise
report `done`, and `_infer_steps` (`wfctl/_pipeline.py:177`) cascades: the first
`pending` step sets `cascade = True` and every later step is forced to `pending`
with no predicate run. A hold injected *inside* the loop would therefore be
computed against a step list still being built, and a held `done` step would
start cascading steps that are legitimately `done` today.

Applying it after the loop, in `build_report`, keeps one inference and leaves the
cascade rule untouched: the held step's `state` becomes `in_progress` and
`_current_step_name` — which already stops at the first `in_progress` — routes to
it with no change.

**Alternatives considered**: a `held` state name. Rejected at level 2 on
`pipeline-state-is-one-payload`, and restated by FR-018.

## Decision: `action` stays free text on both verbs

**Rationale**: `notify` takes it that way (`wfctl/cli.py:340`, a plain
`typer.Argument(str)`), and matching a clearing to a block by that string is what
the level-3 record's `--clear` escape exists for. An enum would be a change to
`notify`, which FR-019 forbids.

**Falsified by**: the first consumer that wants to branch on the value rather
than print it. Recorded as an assumption in both the spec and the level-3 record.

## Unknown resolved: how many grant states the two authority lines must be true in

`_NOTIFY_LINES` at `wfctl/cli.py:179` carries seven keys — `local`, `unset`,
`deny`, `unreadable`, `corrupt`, `trunk`, `unknown-trunk` — and `_notify_line`
builds an eighth rendering for `label` rather than looking it up, because that
line names the issue the label is on.

So SC-003's "seven grant states" is the dictionary, and the rendering count the
tests must cover is **eight**. Both new lines are keyed on nothing (FR-002), so
the coverage is a loop over the eight, not eight assertions.

## Unknown resolved: where the new lines print

`_IRREVERSIBLE_NOTICE` (`wfctl/cli.py:197`) prints at `wfctl/cli.py:478`, in the
console arm of `status_cmd`, immediately after `_notify_line`. It is a module
constant with one call site, so FR-004's rewording is a one-string change and its
test is a string assertion.

FR-001's new line joins it there. FR-018 forbids a new fact row, so it is a
console line beside the other two and not an entry in `report.facts`.

## Unknown resolved: whether the agent survives the refusal

Not resolved by research, and it cannot be — it is a property of the host, not of
this repository. Observed three times on 2026-09-13 (the classifier returns an
error and the run continues), including on the attempt to test the claim itself.

Carried into the plan as a stated assumption rather than a task. A host that
terminates the run on refusal leaves no witness, and makes this feature
unavailable rather than wrong.

## Unknown resolved: whether `permissions.deny` reaches a subagent's own calls

Never established — on the retest, the spawn itself was refused before the
command was reached. Out of scope for this feature, which reports what the host
did rather than modelling how the host decides. Recorded here so the plan does
not read as though the question was answered.
