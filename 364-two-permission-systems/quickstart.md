# Quickstart: two permission systems

**Feature**: `364-two-permission-systems` | **Date**: 2026-09-13
**Phase**: 1

The three things this feature changes, as a reader meets them.

## An agent whose tracker write was refused

The host refuses `gh issue comment` before wfctl starts. There is no exit code to
read and no invocation to record one, so the agent reports it:

```bash
wfctl blocked issue-comment --reason "host classifier: External System Writes"
```

```
✓ recorded: issue-comment blocked — holding `decompose`
  Your host refused this, not wfctl. Re-running the step will be refused again.
```

No grant is consulted. A run blocked by its host is by construction a run that
may hold no grant, so a gate here would refuse exactly the report the feature
exists to collect.

## A person reading the run in the morning

```
#364  364-two-permission-systems
may notify people — you allowed it in this worktree
will never merge, force-push, close an issue, or delete a branch or worktree — those are yours, and no setting changes it
the agent has permission rules of its own — wfctl can't see them and says nothing about them
────────────────────────────────────
brainstorm   ●
specify      ●
clarify      ●
plan         ●
tasks        ●
analyze      ●
decompose    ▶  blocked: host refused issue-comment  ← current
implement    ○

  Your host refused this, not wfctl — re-running decompose will be refused again.
  Take the action yourself, then: wfctl blocked issue-comment --clear

next: /speckit.decompose
```

Before this feature, that run printed `decompose ●` and `next: /speckit.implement`.
The refused write and the successful one left byte-identical state.

## Releasing the hold

Two ways, and only one of them is reachable from the blocked run.

```bash
wfctl blocked issue-comment --clear      # a person, having taken the action
```

```bash
wfctl issue comment 364 --body "…"       # the agent, retrying with a grant
```

The second writes `notify-action` for the same action name and releases the hold
with nobody clearing it. It is the cheap path, not the only one — `notify` runs
behind the grant gate, so the run that most needs to lift a block is the one that
cannot write the event that lifts it.

**They match on the action's name, and the name is free text.** A block reported
as `issue-comment` and a success recorded as `comment` do not match. `--clear` is
the escape: it is the one spelling the person holding the problem can choose.

## What has not changed

```bash
wfctl notify issue-comment --declined --reason "…"
```

Unchanged, gate included. A run with no grant still exits 1 there. The two
commands are two commands precisely so that neither has to know about the
other's gate.
