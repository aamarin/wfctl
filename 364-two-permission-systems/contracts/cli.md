# CLI contract: the block report

The user-facing surface this feature adds or changes. Exact wording is
illustrative where marked; the states and exit codes are the contract.

This is a **published interface** from the day it ships — wfctl's CLI is reached
by skill files and by agents whose code is not in this repository, so removing
either spelling below is a breaking change rather than a rename. That cost was
argued and accepted at level 3.

## `wfctl blocked <action> --reason "<what the host said>"`

Records that the agent's own host refused an outward action wfctl never ran.

| | |
|---|---|
| `action` | Required positional, free text. `issue-comment`, `issue-create`, `push` |
| `--reason` | Required string. What the host said, quoted as given |
| Grant | **None consulted.** `action_grant` is never called (FR-006) |
| Exit | 0 on record, 1 when `--reason` is absent |

**There is no spelling of this command that reports a success** (FR-009). The
narrow exception the level-2 record carves — *the agent may report a failure it
alone witnessed; it may never report a success* — is a property of this surface,
not a sentence an agent has to have read.

### Success, with a step to hold

```
✓ recorded: issue-comment blocked — holding `decompose`
  Your host refused this, not wfctl. Re-running the step will be refused again.
```

Exit 0.

### Success, with no step to hold (FR-008)

A trunk branch, or any branch with no feature directory. The report is stored
anyway — the fact is about the run, not about the pipeline.

```
✓ recorded: issue-comment blocked — no step is being held
```

Exit 0. The `step` field of the stored event is `null`.

### Missing reason (FR-007)

```
✗ --reason is required — a block with no reason holds a step and says nothing
```

Exit 1, nothing stored.

### With no grant

The case the whole feature exists for, stated as behaviour rather than as an
absence: a run whose host refused it holds no grant by construction, and this
command records anyway. `wfctl notify` on the same branch still exits 1. Neither
is a change to the other.

## `wfctl blocked <action> --clear`

Releases a standing block. Asserts that a person took the action.

| | |
|---|---|
| `action` | Required positional, the string the block carried |
| `--clear` | Boolean. Mutually exclusive with `--reason` |
| Grant | **None consulted** (FR-013) — the row `wfctl issue close` occupies |
| Exit | 0 always |

Ungated for the reason `AGENTS.md` § Safety already gives for `close`: gating it
would refuse the human who is the only actor allowed to run it. Nothing prevents
an agent from running it, and the answer to that is the answer this repo already
gives for `close`.

### Released

```
✓ cleared: issue-comment — `decompose` reads from its own artifacts again
```

### Nothing standing (FR-014)

```
ℹ no block standing for issue-comment — nothing to clear
```

Exit 0, nothing written. Saying so rather than succeeding silently: a person who
mistypes the action name otherwise reads a clean exit as a release that did not
happen.

### Both flags

```
✗ --reason and --clear are opposites — pass one
```

Exit 1.

## `wfctl status` — the authority block

Two lines change. Both print in **every** grant state, keyed on nothing (FR-002).

### New line (FR-001)

```
the agent has permission rules of its own — wfctl can't see them and says nothing about them
```

**It names no command** (FR-003). An agent needs `wfctl blocked` mid-run, long
after it last read this block; naming it here would be the one place a reader is
guaranteed not to be looking when it matters. The instruction lives in the skills
(FR-017).

### Reworded line (FR-004)

```
- will never merge or delete — that is always yours, no setting for it
+ will never merge, force-push, close an issue, or delete a branch or worktree — those are yours, and no setting changes it
```

Two of the four actions in the class were missing. `wfctl/cli.py:197`, one
constant, one call site.

## `wfctl status` — a held step

Rendered through the fields every step already carries. No new payload key.

```
decompose    ▶  blocked: host refused issue-comment  ← current
```

| Payload field | Value |
|---|---|
| `state` | `in_progress` — not a new state (FR-018) |
| `reason` | the reason string the block carried |
| `remedy` | the three sentences below |
| `is_current` | true, by `_current_step_name`'s existing rule |

### Remedy (FR-015)

```
Your host refused this, not wfctl — re-running decompose will be refused again.
Take the action yourself, then: wfctl blocked issue-comment --clear
```

### Next action (FR-016)

```
next: /speckit.decompose
```

**The step's own command, never the clearing command.** The block is not the
step's work, and a `next` that names the release would tell an unattended agent
to clear its own hold — which is the one thing the asymmetry exists to prevent.
The release is in the remedy, which is addressed to a person.
