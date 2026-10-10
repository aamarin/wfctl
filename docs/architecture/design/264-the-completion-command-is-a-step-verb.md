---
status: proposed
---

# The completion record is written by `wfctl step complete implement`

## Context

When the `implement` step finishes, a wfctl command now writes the completion
record, and the agent no longer writes the file itself. The architecture
record that lets a new task reopen the `implement` step decides that. This
record decides what the command is called and where it sits in the CLI.

The name matters because it's hard to change once it ships. Skill files and
agents in other repositories call wfctl by name, and a rename would break
them.

## Verified

- `wfctl/cli.py:1830-1833` creates the `step` group with the help text "Declare
  a pipeline pass inapplicable, or sign off the plan without a review."
- `wfctl/cli.py:1955`, `step sign-off`, records that the plan review pass is
  done without a review. It is the closest existing command: wfctl records a
  step's state on the caller's behalf.
- `wfctl/cli.py` registers 23 top-level commands with `@app.command`, beside
  the `arch`, `step`, `check`, `contract`, and `hook` groups.
- `step none` and `step sign-off` take a pass name such as
  `plan.plan-review`. `implement` is a step, not a pass.

## Assumed

- No other step is expected to need a completion command soon. If one does,
  it joins this verb with a new step name rather than adding a new command.

## Direct baseline

A top-level command named after the file it writes:

```
wfctl implement-complete
```

It takes no argument and is easy to guess from the file name.

## Decision

The command is a verb in the `step` group:

```
wfctl step complete implement
```

It accepts only `implement` for now and refuses any other step with a message
naming the one it supports. The group's help text grows to cover it.

## Diagram

```
          baseline                          decision

     ┌───────────────────────┐        ┌───────────────────────┐
     │ wfctl --help          │        │ wfctl --help          │
     │  23 commands          │        │  23 commands          │
     │  + implement-complete │        │  step                 │
     │  step                 │        └───────────────────────┘
     └───────────────────────┘                  │ lists
                 │ lists                        ▼
                 ▼                    ┌───────────────────────┐
     ┌───────────────────────┐        │ wfctl step --help     │
     │ wfctl step --help     │        │  none                 │
     │  none                 │        │  sign-off             │
     │  sign-off             │        │  + complete           │
     └───────────────────────┘        └───────────────────────┘
```

The two differ by where the new name appears. The baseline adds a 24th
top-level command, apart from the two commands that already record a step's
state. The decision adds one verb beside them, so a reader looking for how
to mark a step's state finds all three in one place.

## Considered

- `wfctl implement-complete`, the direct baseline. It is easier to guess and
  needs no argument. It was rejected because it adds to an already crowded
  top level, and it sits apart from `step sign-off`, which does the same kind
  of job for the plan.
- `wfctl step sign-off implement`. It reuses an existing verb, but sign-off
  means "accept this without a review" and requires `--reason`. Completing
  implementation is not a waiver, so sharing the verb would give one word two
  meanings.

## Consequences

The CLI keeps a group-then-action pattern, like `wfctl arch accept` or
`gh pr create`. The cost is an argument that accepts one value today, which
reads a little odd until a second step needs it. The command has to be added
to the `allowed-tools` line in `wfctl/agents/commands/speckit.implement.md`,
or the host will prompt for it.

## Verification

- A test that `wfctl step complete implement` writes the completion record
  with a copy, and that `wfctl step complete plan` exits 1 naming `implement`.
- A review that `wfctl step --help` reads as one family of commands.

## Log

- 2026-10-09  proposed  — #264 level 3. Andre chose the `step` group over a
  top-level command.
