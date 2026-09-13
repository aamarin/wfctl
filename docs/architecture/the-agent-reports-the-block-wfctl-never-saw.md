---
status: proposed
---

# The agent reports a block wfctl never saw, and wfctl decides what it means

## Context

Two permission systems decide whether an agent may take an outward action, and
wfctl can observe only one of them.

wfctl's own grant gates `comment`, `create` and `label`; when it refuses, it
prints a remedy and writes a `notify-refused` event, so the refusal survives the
session. The host agent's permission layer refuses whatever it reads as writing
to an outside system, and when it does, wfctl's process never starts. There is no
exit code, no stderr, and no invocation to record one. The refusal exists only in
the agent's transcript, which is cleared or compacted.

A step's completion is computed from artifacts. Where the blocked action left no
artifact — commenting a PR link on the issue, closing it — a run that was refused
and one that succeeded produce byte-identical state.

`decompose` is the one step that escapes this, and it escapes by accident rather
than by design. Since #8 it requires every issue row in `delivery.md` to name a
tracker key, and it reads that from the file's own text rather than from the
tracker — a pipeline read on every session start may not cost a network
round-trip. A blocked `create` produces no key to write, so the rows stay unkeyed
and the step does not read `done`. The check is aimed at a plan whose table was
never filled back in; it catches a refusal because the two leave the same mark.

So the pipeline can advance past a step whose outward half never happened, and
nothing on disk says so.

## Direct baseline

Print one more line in `wfctl status`'s authority block saying a second
permission layer exists and wfctl cannot see it. No new verb, no new event, no
change to any step state.

This is what #364 asks for in its own words — *"whether wfctl's own authority
reporting should acknowledge that a second layer exists, and if so in what
words"* — and it closes the half of the problem that is about the block reading
as complete when it is not. It costs one string.

What it leaves is every actual block still invisible after the fact. The line is
generic by construction: it prints identically on a run where nothing was refused
and on one where three things were, so a reader who comes back in the morning
learns that refusals are possible and nothing about whether any happened.

## Decision

The agent reports a blocked outward action to wfctl, and wfctl holds the step at
`in_progress` with the reason on its annotation.

No new step state. `in_progress` carrying a reason is the shape `implement`
already uses for a failed verification, and a blocked step is the same fact about
the pipeline: it may not advance, and here is why.

## Owns truth

wfctl owns *"may the pipeline advance past this step, and why not?"*.

The agent cannot own that. A step state an actor sets for itself is the claim the
state exists to check, and `wfctl-runs-the-verification` (accepted) already set
that ceiling for this repo — the agent never certifies its own completion.

The agent owns *"was an outward action refused, and which one?"*, and it owns it
because wfctl cannot compute it. The host refuses the command before the process
exists; there is no artifact, no exit status and no log line for wfctl to read,
and no host is obliged to offer a way to ask "would this be allowed" without
performing it. The agent is the only witness.

That is a deliberate exception to the no-self-report rule, and it is narrow
enough to state as one sentence: **the agent may report a failure it alone
witnessed; it may never report a success.** The asymmetry is what keeps it from
reopening what `wfctl-runs-the-verification` closed. A false report of failure
stops a pipeline that would otherwise have advanced, which costs a human one
glance; a false report of success is the thing that record exists to prevent.

## Considered

- **The direct baseline — one generic line in `status`.** Sound, far cheaper, and
  it is literally what the issue asked for. It loses on fit rather than on merit:
  it says a second layer exists in the abstract and can never say that one fired,
  so the morning-after question — *what did the run not do?* — is still answered
  only by a transcript that no longer exists.
- **A verdict channel marking each outward action survivable or fatal**, carried
  on the existing `stall` field. Designed in full and dropped. It requires wfctl
  to model what each step produces without its outward half, and the distinction
  turns out to have almost no members: once #297 moves the issue split to
  brainstorm, every outward action left in an unattended run's tail is survivable.
  Machinery for a partition with one side empty.
- **A new `failed` step state.** Rejected on `pipeline-state-is-one-payload`
  (accepted) and `readiness-is-not-a-step-state` (proposed): a step state answers
  whether the pipeline may advance, `in_progress` already answers that for a step
  blocked by a failed verification, and a second value meaning the same thing to
  the pipeline splits the branch in every consumer that reads the payload.
- **A `PreToolUse` hook wfctl installs into the assistant's config**, so wfctl
  answers before the host refuses. This is the successor
  `wfctl-classes-the-action-not-the-command` (proposed) names for itself, and it
  is the only option that prevents the block rather than recording it. Not chosen
  twice over: it rests on an unverified claim — that a hook's allow overrides the
  host's own classifier — and #364's Boundary puts installing a rule in the host's
  layer outside its scope, as a person's act.
- **Asking the host in advance whether an action would be permitted.** No host is
  obliged to offer it, and Claude Code, Gemini, Cursor and Copilot all match
  permission rules against command strings at call time. There is nothing to ask.

## Consequences

The report is tamper-evident, not unforgeable, and this record claims nothing
stronger. An agent that is blocked and stays quiet leaves the step exactly where
it was. That fails **safe** wherever the step's existing evidence happens to be
downstream of the blocked action — `decompose`, whose unkeyed rows are the same
mark a refused `create` leaves — and fails **silent** everywhere else, which is
every outward action at the tail of a run. The self-report is therefore worth most
precisely where wfctl has no independent check, which is also where nothing
verifies it.

The safe half is not a property this record can rely on continuing. It holds
because one step's evidence is a tracker key that a refusal prevents from
existing, which nobody chose for that reason and no test pins.

This record does not fix #364's wording defect, which is independent of it and
ships wrong today: the irreversible line prints *"will never merge or delete"*
where the class it implements
(`wfctl-classes-the-action-not-the-command`, proposed) names merging, closing an
issue, force-pushing, and deleting a branch or worktree. Two of four.

#297 bears on the scope. It moves the issue-splitting decision to brainstorm,
which removes the only outward action in an unattended run that genuinely cannot
be survived. If #297 lands first, this record's value is entirely the trace and
none of it is the stop.

## Log

- 2026-09-13  proposed    — #364 level 2; a refusal wfctl never observed left no
  trace anywhere, and the step read the same either way
