# The refusal wfctl never saw

## Problem Statement

How might wfctl stop reporting an authority it does not hold, and stop letting a
step read as finished when the tracker write inside it was refused by a system
wfctl cannot observe?

## Recommended Direction

Two things ship together, and they answer two different halves of the same
misreading.

The **static half** is a third line in `wfctl status`'s authority block, printed
in every state and keyed on nothing. Today that block has two lines and both
speak for wfctl's own grant, so a reader who takes it as an account of what the
run may do is wrong in a way the block itself cannot reveal. The new line says
the second layer exists and that wfctl neither sees it nor speaks for it. This is
what #364 asked for in its own words, and on its own it can never say that a
refusal actually happened.

The **dynamic half** is `wfctl blocked <action> --reason "…"`, a new ungated verb
the agent calls when the host refuses an outward action. It writes one event; a
predicate reads it back and holds the step at `in_progress` with the reason on
its annotation. The agent is the only witness to a command that never ran, so the
report is a self-report — narrowed by shape to a report of *failure only*, which
is the exception the level-2 record carves out of `wfctl-runs-the-verification`.

A third, smaller thing rides along because it is in the lines being rewritten:
the irreversible notice is wrong today and is corrected here.

## Behavior — what each state renders

### The authority block, every run

Before:

```
#364  364-two-permission-systems
may notify people — you allowed it in this worktree
will never merge or delete — that is always yours, no setting for it
```

After:

```
#364  364-two-permission-systems
may notify people — you allowed it in this worktree
will never merge, force-push, close an issue, or delete a branch or worktree — those are yours, and no setting changes it
your agent has its own rules — wfctl cannot see them, and says nothing about them
```

Read the third line in each of the seven grant states and it is true in all of
them, which is why it is keyed on nothing. Read the second line as it ships
today and it is false in two of the four cases it covers: the class it implements
names merging, closing an issue, force-pushing, and deleting a branch or
worktree, and the line names two of those four.

The third line does **not** name `wfctl blocked`. An agent that needs the verb
needs it mid-run, having already read `status` long before; the channel that
reaches it there is the skill it is following and `wfctl blocked --help`, not a
line at the top of a command it is not about to run again.

### A block standing

```
────────────────────────────────────
brainstorm   ●
specify      ●
clarify      ●
plan         ●
tasks        ●
analyze      ●
decompose    ▶  blocked — your agent refused issue-create: External System Writes  ← current
implement    ○
────────────────────────────────────
artifacts written          ●  spec.md, plan.md, tasks.md
definition of done         ●  passed at c004eaf
architecture accepted      ●  the-agent-reports-the-block-wfctl-never-saw
outward actions authorized ●  you allowed it in this worktree
next: /speckit.decompose
  Re-running this step will be refused again — your agent blocked it, not wfctl.
  A person takes the action, then records that it happened:
      wfctl blocked issue-create --clear
```

Two strings in that block are worth reading in this state specifically.

`outward actions authorized ●` stays met, and that is correct rather than a
lie: the fact is named for wfctl's own grant and a human did allow it. The third
authority line above is what stops the pair from reading as a claim about the
host, and it is the reason no fifth fact is added here.

`next: /speckit.decompose` is the step's own command, unchanged. It is not the
remedy, and the remedy's first line says so before the reader can act on it.
Naming `wfctl blocked --clear` on the `next:` line instead was rejected: that line
is what an unattended agent follows, and `--clear` is the one command in this
feature that cannot fail, so putting it there hands the agent a one-line way to
release its own block. `wfctl verify` can be named on `next:` for a blocked
`implement` precisely because running it can fail.

### The verb

```
$ wfctl blocked issue-create --reason "host classifier: External System Writes"
✓ recorded: blocked issue-create — decompose is held until a person takes it

$ wfctl blocked issue-create
✗ wfctl blocked requires --reason

$ wfctl blocked issue-create --clear
✓ cleared: issue-create — decompose is no longer held

$ wfctl blocked issue-create --clear      # nothing was blocked
ℹ nothing recorded for issue-create — no block to clear
```

On a trunk branch, where there is no feature and no step to hold, the report is
still recorded — the trace is most of what this verb is worth, and refusing it
would discard the one artifact of a refusal:

```
$ wfctl blocked issue-comment --reason "host classifier: External System Writes"
✓ recorded: blocked issue-comment — no feature branch, so no step is held
```

### A held step whose own artifacts say it finished

This is the state the whole feature exists for, and the one that looks wrong
until it is read:

```
decompose    ▶  blocked — your agent refused issue-create: External System Writes  ← current
implement    ●  12/12 done
```

`decompose` holds while a later step reads done. That is the honest rendering of
a run that wrote every artifact and never reached the tracker. The hold therefore
cannot live inside a step's own predicate — it is applied after inference, to
whichever step the event names, and it overrides `done`.

## Boundaries and Ownership

wfctl owns *"may the pipeline advance past this step, and why not?"*. The agent
cannot own it: a step state an actor sets for itself is the claim the state
exists to check.

The agent owns *"was an outward action refused, and which one?"*, because wfctl
cannot compute it. The host refuses the command before wfctl's process exists —
no exit code, no stderr, no invocation to record one — and no host offers a way
to ask whether an action would be permitted without performing it.

The exception that buys is one sentence wide: **the agent may report a failure it
alone witnessed; it may never report a success.** A false report of failure stops
a pipeline that would have advanced, which costs a human one glance. A false
report of success is the thing `wfctl-runs-the-verification` exists to prevent.

`--clear` asserts a success, so it is a person's command, not the agent's — the
row `wfctl issue close` already occupies.

## Software design decisions

- `docs/architecture/design/364-the-block-report-is-its-own-verb.md` — the block
  report is a separate ungated verb rather than a flag on `wfctl notify`, because
  every path through `notify` runs behind `action_grant` and a host-blocked run
  is by construction one that may hold no grant; `--clear` is its release, for
  the same reason one step later.

The level-2 ownership decision is
`docs/architecture/the-agent-reports-the-block-wfctl-never-saw.md`. It is not
listed as an entry above because it is a level-2 record and binds as one; read it
through `wfctl arch context`, not as a structural choice for this feature.

## Checked and assumed

| checked — opened and read | assumed — a bet this design rests on |
| --- | --- |
| `cli.py:377-380` — `notify` calls `action_grant` and exits 1 before either its declined or its action path | That an agent blocked by the host reaches a shell at all. Observed three times on 2026-09-13; falsified by a host that kills the run, which leaves no witness and makes every option here unavailable |
| `cli.py:371-375` — the gate covers both paths deliberately (FR-011) | That `action` stays free text on both verbs. Falsified the first time a consumer wants to branch on it rather than print it |
| `_tracker.py:350-358` — a successful `wfctl issue comment\|create\|label` writes `notify-action` with the *verb's* spelling | That matching a clearing event by action name is enough. Two blocks of one action in a session collapse to the later one |
| `_predicates.py:506` — `verification_block` returns the first reason or `None`; `_pipeline.py:492` reads it into the payload | That a human who unblocks the work will record it. Nothing observes the action, so an unrecorded one leaves the step held |
| `_pipeline.py:347-351` — `next_step_content` routes a blocked step to itself with `auto=False`, `implement` to `wfctl verify` | |
| `_pipeline.py:140-145, 267-269` — the remedy is a two-space-indented block keyed on the reason, resolved in inference rather than in a view | |
| `cli.py:198` — `_IRREVERSIBLE_NOTICE` is keyed on nothing and prints in every state | |
| Nothing reads any `notify-*` event back today; holding a step needs a predicate that does not exist yet, whichever verb writes the event | |
| `wfctl blocked` collides with no existing command | |

## Key Assumptions to Validate

- [ ] A host-blocked agent survives the refusal and can still run a command —
      re-probe once, on a second host, before the verb is relied on unattended.
- [ ] An agent following the skills actually calls `wfctl blocked` when refused.
      Test by blocking a real outward action in an unattended run and reading the
      event log afterwards.
- [ ] The action spelling an agent reports matches the one a later success
      records. Test with `gh issue comment` blocked, then `wfctl issue comment`.

## MVP Scope

In:

1. The third authority line, printed in every state, keyed on nothing.
2. The irreversible notice corrected to name all four of its class.
3. `wfctl blocked <action> --reason "…"` and `wfctl blocked <action> --clear`.
4. A `blocked` event, and a predicate that reads the latest event per action and
   holds the named step at `in_progress`, overriding `done`.
5. The remedy block on a held step.
6. The skills that tell an agent to call the verb when it is refused.

Out:

- Any new fact row, any new step state, any new top-level JSON key.
- Any change to `wfctl notify`, including its gate.

## Not Doing (and Why)

- **A `PreToolUse` hook wfctl installs into the host's config** — the only option
  that prevents the block rather than recording it. It rests on an unverified
  claim, that a hook's allow overrides the host's own classifier, and #364's
  Boundary puts writing a rule into the host's layer outside scope, as a person's
  act.
- **Asking the host in advance whether an action would be permitted** — Claude
  Code, Gemini, Cursor and Copilot all match permission rules against command
  strings at call time. There is nothing to ask.
- **A survivable/fatal verdict channel on `stall`** — designed in full and
  dropped. It needs wfctl to model what each step produces without its tracker
  write, and once #297 moves the issue split to brainstorm the partition has one
  side empty.
- **Closing the reach problem** — the probes showed wfctl's gate catches the
  well-behaved agent and nothing else; `gh issue comment` walks around it in one
  line. The fix is a rule in the host's layer, which this issue's Boundary puts
  outside scope. Applied by hand at the user level on 2026-09-13. Worth its own
  issue for the part wfctl could own: saying out loud that its gate is not a
  boundary.
- **An enum for `action`** — it would have to land in `notify` and `blocked` at
  once, on a guess about a consumer that does not exist yet.

## Open Questions

- Does `permissions.deny` reach a subagent's own Bash calls? Unverified — on
  retest the spawn itself was refused, so the question could not be reached. Do
  not assume it does.
- Why was `wfctl issue close` blocked in #364's original transcript when
  `wfctl issue comment` passed freely four times on 2026-09-13? Still
  unexplained, and the instruction not to build on that observation without
  reproducing it stands.
- Does `wfctl --help` read as though `notify` and `blocked` are alternatives? A
  review question rather than a test; if it does, the help text owes the reader
  the grant.
