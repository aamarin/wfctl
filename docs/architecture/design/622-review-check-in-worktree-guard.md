---
status: proposed
---

# The worktree guard hook also runs the review check

## Context

The accepted record on review coverage has an agent hook that wfctl installs.
The hook refuses to open or merge a pull request while the branch has commits
that no review covered. After three rounds, a person can sign off on the
remaining commits, and the hook then allows the pull request. The agent
shouldn't sign off, so the same hook refuses the sign-off command when the agent
runs it.

wfctl already installs a hook that runs before every shell command the agent
runs: the worktree guard. Every one of those commands pays for the guard,
including the many that could never trip it. Its cost has been measured and cut
before.

The proposed record on managed hooks says each wfctl feature on an event gets
its own hook entry. It rejects combining two features into one entry, because
on the `Stop` event the shared `|| true` hid one feature's failure, and the two
features had to merge their output into one JSON object.

## Verified

- `cli.py`, `MANAGED_HOOKS` holds one `PreToolUse` row, `GUARD_HOOK_COMMAND`,
  which runs `wfctl hook worktree-guard`. The comment above it reads "No
  `|| true` here, unlike `Stop`. A non-zero exit on `PreToolUse` is the guard
  refusing the call."
- The `_hook.py` docstring says the guard took 81.7 ms per call before the fast
  path, and that "27.1 ms of interpreter startup ... is the floor for a hook
  spawned per Bash call".
- `_entry.py` sends the exact arguments `hook worktree-guard` to
  `_hook.worktree_guard` without importing `typer` or `rich`.
- `_hook.worktree_guard` returns 0 right away for a command with no `/` in it.
  `gh pr create` has none, so the review check has to run before that line.
- `_hook.worktree_guard` writes its refusal to stderr and returns 2, and it
  prints nothing when it allows a command. Piping an `ls` payload into
  `wfctl hook worktree-guard` printed nothing and exited 0.

## Assumed

- Every pull request in this repository is opened and merged with `gh`. A pull
  request opened through a GitHub plugin or a browser isn't checked. Every pull
  request so far used `gh`, and one opened another way would break this
  assumption.
- Matching each command against a short list of strings adds well under a
  millisecond. Nobody has measured it yet, and the verification below does.

## Direct baseline

The simplest approach adds a second `PreToolUse` row on `Bash` to
`MANAGED_HOOKS`, which runs a new `wfctl hook review-check` subcommand.
`_entry.py` gets a third exact argument list for its fast path. Each feature
has its own entry, its own process, and its own exit code, as the proposed
record on managed hooks describes.

## Decision

The review check runs inside `wfctl hook worktree-guard`, before the worktree
check. It looks for four commands:

1. `gh pr create`.
2. `gh pr merge`.
3. A `gh api` call to the `merge-async` endpoint.
4. The sign-off command.

If a command matches none of them, it goes on to the worktree check with no
file read and no git call.

If a command matches one of the first three, the review check reads the
branch's last reviewed commit from the state directory and asks git for the
commits after it. If any commits are unreviewed and no sign-off covers them, it
prints those commits to stderr and returns 2. If the command is the sign-off
command, the review check refuses it every time, because the hook exists to
stop the agent from signing off.

Each check runs in its own `try` block, so an error in one doesn't skip the
other. The worktree check allows a command when it can't decide, as it does
today. The review check refuses a pull request when it can't read the record,
because those commands run only a few times per branch, and a wrong refusal
costs one retry. A branch with no review history isn't this case. No review has
run on it, so the branch is unreviewed, and the review check refuses it for that
reason. The record is unreadable only when a file was half-written, which is
rare enough that the choice costs almost nothing.

## Diagram

```
             baseline                                  decision

          ┌──────────────┐                          ┌──────────────┐
          │ Claude Code  │                          │ Claude Code  │
          └──┬────────┬──┘                          └──────┬───────┘
     spawns  │        │ spawns                     spawns  │
═══ install-modes: wfctl owns its rows in settings.json ═══╪═══════════════
             │        │                                    │
   ┌─────────▼───┐ ┌──▼────────────┐            ┌──────────▼──────────┐
   │ worktree-   │ │ review-check  │ (new)      │ worktree-guard      │
   │ guard       │ │               │            │  review check (new) │
   └─────────────┘ └──────┬────────┘            │  worktree check     │
                          │ reads               └──────────┬──────────┘
                   ┌──────▼────────┐                       │ reads, on a match
                   │ state dir     │            ┌──────────▼──────────┐
                   └───────────────┘            │ state dir           │
                                                └─────────────────────┘
```

The line marks the existing rule that wfctl owns only the rows it writes into
`settings.json`. In the baseline, Claude Code starts two processes before every
shell command, so every command pays the 27 ms startup cost twice. In the
decision, Claude Code starts one process, and the review check adds a string
match. The decision has one row and one process fewer. Adding a fifth command
to check means changing one list in either graph.

## Considered

- A second hook entry and subcommand, as the direct baseline describes. We
  didn't choose this because it doubles the startup cost on every shell command
  the agent runs. The proposed record on managed hooks argues for one entry per
  feature, but neither of its two problems applies here:
  1. Neither check swallows the other's exit code, since `PreToolUse` uses no
     `|| true`. Both refuse with exit code 2 and a message on stderr.
  2. Neither check writes JSON to stdout, so there is no output to merge.
- A git `pre-push` hook. The accepted record already rejects this, because an
  agent can skip it with `--no-verify`.
- An instruction in the `opening-a-change` skill. The accepted record already
  rejects this, because it runs only when the agent follows it.

## Consequences

- The hook's name, `worktree-guard`, no longer describes everything it checks.
  The name is written into every consumer's `settings.json`, so renaming it
  would break those files, and the name stays.
- The two checks share a process. A crash outside both `try` blocks, such as a
  payload that isn't valid JSON, skips both. The guard already reads every
  payload field defensively for that reason.
- A pull request opened without `gh` isn't checked, and neither is one opened
  by an agent without hooks. The follow-up issue on a required CI check covers
  both.
- A command that only mentions `gh pr create`, such as an `echo`, is refused on
  an unreviewed branch. The refusal lists the commits, so the cost is one
  confusing message.

## Verification

- A test pipes a `gh pr create` payload into the guard on a branch with an
  unreviewed commit, and checks for exit code 2 and the commit on stderr. The
  same test on a fully reviewed branch checks for exit code 0 and no output.
- A test pipes the sign-off command into the guard and checks for exit code 2.
- A test pipes a `gh pr create` payload into the guard with an unreadable
  record, and checks for exit code 2.
- A measurement of the guard on an `ls` payload, before and after this change,
  shows the added cost per call. The `_hook.py` docstring has the earlier
  numbers to compare against.

## Log

- 2026-10-21  proposed  — #622 level 3. Andre asked whether this added a hook on
  every prompt and cost tokens, and approved it once it ran inside the existing
  guard. He then approved refusing a pull request when the record can't be read.
