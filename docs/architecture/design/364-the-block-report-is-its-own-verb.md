---
status: proposed
---

# The block report is its own verb, because the grant gate stands in front of every other one

## Context

`the-agent-reports-the-block-wfctl-never-saw` (proposed, level 2) settles that
the agent reports a host-blocked outward action and wfctl holds the step at
`in_progress` with the reason on its annotation. It deliberately leaves the verb
to level 3, and says why: wfctl's CLI is reached by skill files and by agents
whose code is not in this repository, so whatever carries the report is a
compatibility promise from the day it ships.

The pressure is that wfctl already has a command for outward actions it did not
itself perform. `wfctl notify` covers three states — the run acted, the run held
the authority and declined, the run wanted to act and wfctl refused it. A fourth
state looks like it belongs beside them, and the whole question is whether it
does.

It does not, and the reason is a gate rather than a taxonomy. Every path through
`notify` runs behind `action_grant`, including the one that records a refusal —
and a run blocked by the host is, by construction, a run that may hold no grant.

`wfctl-runs-the-verification` (accepted) is the constraint in force: the agent
never certifies its own completion. The level-2 record carves the narrow
exception this verb exists to carry, and nothing here widens it.

## Verified

- `wfctl/cli.py:377-380` — `notify` calls `action_grant`, prints the refusal line
  and `raise typer.Exit(1)` before either the declined path or the action path is
  reached.
- `wfctl/cli.py:371-375` — the comment there states the gate covers both paths on
  purpose (FR-011): "filing one from a refused run overstates the grant in the
  flattering direction."
- `wfctl/_session.py:406,422,433` — `notify-action`, `notify-declined` and
  `notify-refused` are each a single `append_event` call and nothing more.
- Nothing reads any `notify-*` event back. The readers of `events.jsonl` are
  `_session.py:55` (`start`), `_session.py:360` (`notify-resolved`),
  `_stall.py:189` (`start`/`end`/`resume`) and `_stall.py:224`. Holding a step
  therefore needs a predicate that does not exist yet, whichever verb writes the
  event.
- `wfctl/_predicates.py:506` — `verification_block(repo_root) -> str | None`
  returns the first matching reason or `None`, and `_pipeline.py:492` reads it
  into the payload. That is the shape a block predicate copies.
- `wfctl/_io.py:71-77` — `append_event` stamps `ts` and `event` and passes every
  other field through, so a new event kind costs no change there.
- `@app.command("notify")` at `cli.py:338` is a flat command with a positional
  argument, not a `typer` group. `wfctl notify blocked …` would be a breaking
  change to the existing spelling, not an addition.

## Assumed

- **That an agent blocked by the host reaches a shell at all.** The level-2
  record checked this three times in one session — the classifier returns an
  error and the run continues. Falsified by a host that terminates the run on
  refusal, which leaves no witness and makes every option here unavailable.
- **That `action` strings stay free text.** `notify` takes them that way and this
  verb matches it. Falsified the first time a consumer wants to branch on the
  action rather than print it, which would want an enum in both places at once.
- **That matching a clearing event by action name is enough.** Two blocks of the
  same action in one session collapse to the later one. Falsified by a step whose
  outward half is two distinct calls that happen to share a name.

## Direct baseline

Add `--blocked` to `wfctl notify`, beside `--declined`:

```
wfctl notify issue-comment --blocked --reason "host classifier: External System Writes"
```

One flag on an existing command, one new event kind (`notify-blocked`), one
branch in `notify_cmd` before the declined branch. No new verb, no new entry in
`--help`, nothing added to the published surface. The predicate that reads it
back is needed either way and is not a difference between the two.

It requires one further change, and that change is the whole argument: the
`action_grant` check at the top of `notify_cmd` must be made conditional, so that
the blocked path runs when the declined and action paths would not.

## Decision

The block report is a separate command, `wfctl blocked`, which does not consult
`action_grant`:

```
wfctl blocked <action> --reason "<what the host said>"
```

It takes the action and the reason from the agent, and takes the step from
inference at call time rather than from the caller. The agent supplies the two
facts it alone witnessed; it does not get to say which step is held.

It writes one event, `blocked`, carrying `action`, `reason` and the inferred
`step`. A `block_reason` predicate shaped like `verification_block` reads the
branch's events, keeps the latest event per action, and returns the reason of any
`blocked` still standing for the step being asked about. A later `notify-action`
for the same action clears it, which is what an agent that retried and succeeded
already writes.

`wfctl notify` is unchanged. Its gate stays closed on both paths.

## Diagram

```
baseline

stable    ┌──────────────────┐
          │ status payload   │
          └──────────────────┘
                   │ reads
                   ▼
          ┌──────────────────┐
          │ block predicate  │
          └──────────────────┘
                   │ reads
                   ▼
          ┌──────────────────┐
          │  events.jsonl    │
          └──────────────────┘
                   ▲ writes
          ┌────────┴─────────┐
          │  wfctl notify    │
          │   action         │
          │   declined       │
          │   blocked        │
          └──────────────────┘
                   ▲ passed by
          ┌────────┴─────────┐
          │  action_grant    │
          └──────────────────┘
═══ verdict boundary (wfctl-runs-the-verification) ═══════════
                   ▲ calls
volatile  ┌────────┴─────────┐
          │      agent       │
          └──────────────────┘


decision

stable    ┌──────────────────┐
          │ status payload   │
          └──────────────────┘
                   │ reads
                   ▼
          ┌──────────────────┐
          │ block predicate  │
          └──────────────────┘
                   │ reads
                   ▼
          ┌──────────────────┐
          │  events.jsonl    │
          └──────────────────┘
              ▲ writes  ▲ writes
     ┌────────┘         └────────┐
┌────┴─────────┐          ┌──────┴───────┐
│ wfctl notify │          │ wfctl blocked│
│  action      │          │              │
│  declined    │          │              │
└──────────────┘          └──────────────┘
        ▲ passed by              ▲
┌───────┴──────┐                 │
│ action_grant │                 │
└──────────────┘                 │
═══ verdict boundary (wfctl-runs-the-verification) ═══════════
        ▲ calls                  ▲ calls
volatile│                        │
   ┌────┴────────────────────────┴────┐
   │              agent               │
   └──────────────────────────────────┘
```

The two differ by how many ways there are into `events.jsonl`. In the baseline
there is one, and `action_grant` stands in front of it — so the report filed by a
run nobody granted authority to, which is the run this whole feature exists for,
is the one the gate refuses. The decision gives the block report a second path
that never reaches the gate, and pays a permanent verb for it. No divider moves:
in both graphs the agent is below the verdict boundary and hands facts upward,
and in neither does it set a step state.

## Considered

- **`--blocked` on `wfctl notify`** — the direct baseline above, and the cheapest
  thing that works. It loses on what it has to do to the gate rather than on
  what it costs: `notify`'s grant check covers both existing paths deliberately,
  as a decision recorded in a comment and pinned by FR-011, and the baseline
  reopens it from underneath. A conditional gate also carries the reader an
  obligation the current one does not — to know which of three flags is exempt —
  where two commands say it by being two commands.
- **`wfctl notify --declined` with the host's message as the reason** — no new
  surface at all, not one flag. Rejected because it files the block in the
  channel FR-011 created to keep it out: `--declined` asserts the run held the
  authority, so a blocked run filing there overstates the grant in exactly the
  flattering direction that comment names, and the one event that should widen a
  grant is recorded as evidence the grant was already wide enough.
- **`--blocked` on `wfctl end`** — no new verb and no gate to touch, since `end`
  consults no grant. Sound, and it loses on timing rather than on shape: the
  report cannot be filed until the session stops, so a run killed between the
  block and the wrap-up reports nothing, and a run that is blocked mid-pipeline
  and carries on working holds no step until it ends. The failure it introduces
  is silence in the case the feature was written for.
- **A `notify` sub-group, `wfctl notify blocked …`** — reads best of any option
  and is not available. `notify` is a flat command taking a positional action, so
  the spelling is already taken by `wfctl notify blocked` meaning *the action
  named "blocked"*, and converting it to a group breaks every existing caller.
- **A `--by <layer>` argument on the new verb**, distinguishing the host's
  classifier from a static permission rule. Dropped as a constant: the agent is
  the only caller and the only layer it can witness is the host's. wfctl's own
  refusals already write `notify-refused` with a `source`, and the two events
  being different kinds is what tells them apart.

## Consequences

A verb on wfctl's published surface that can only ever report a failure, and
cannot be removed later without a breaking change. That is the price the level-2
record named, paid here deliberately rather than deferred.

The narrow exception is now enforceable by shape rather than by prose. There is
no spelling of `wfctl blocked` that records a success, so the rule *the agent may
report a failure it alone witnessed, never a success* is a property of the
command surface instead of a sentence an agent has to have read. The baseline
could not offer this: a `notify` that accepts `--blocked` also accepts the action
path, from the same call site, with the gate already negotiated.

`wfctl notify` and `wfctl blocked` are two commands where a reader might expect
one, and nothing in `--help` explains why. The grant is the reason and it is not
visible from the verb list.

The clearing rule is the new failure mode. A block is lifted by a later
`notify-action` for the same action, so a human who unblocks the work and takes
the action themselves leaves the step held until somebody records it. `status`
must print that remedy on the annotation, the way `verification_block` prints
`run \`wfctl verify\``.

## Verification

- A test that calls `wfctl blocked` on a branch with no grant and asserts exit 0
  and the event written — the case the baseline fails, stated as a test rather
  than as an argument.
- A test that calls `wfctl notify` on the same branch and asserts exit 1, pinning
  that this record did not widen the gate it declined to reopen.
- A test that writes `blocked` then `notify-action` for one action and asserts
  the step is no longer held, and one that writes them in the other order and
  asserts it is.
- A review question rather than a test: does `wfctl --help` read as though the
  two verbs are alternatives? If it does, the consequence above has landed and
  the help text owes the reader the grant.

## Log

- 2026-09-13  proposed  — #364 level 3; the level-2 record left the verb open as
  a published-interface commitment, and the deciding fact turned out to be that
  `notify`'s grant gate refuses exactly the run that needs to report.
