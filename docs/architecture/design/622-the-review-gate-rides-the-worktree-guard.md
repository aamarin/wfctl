---
status: proposed
---

# The review gate runs inside the worktree guard hook

## Context

The accepted record on review coverage has an agent hook that wfctl installs
refuse to open or merge a pull request while the branch has commits no review
covered. A person's sign-off after three rounds lifts the refusal. The agent
shouldn't sign off, so the same hook refuses the sign-off command when the
agent runs it.

wfctl already installs a hook that runs before every shell command the agent
issues: the worktree guard. Its cost is paid on every one of those commands,
and most of them could never trip it. That cost has been measured and cut
before.

The proposed record on managed hooks says each wfctl feature on an event gets
its own entry, identified by its subcommand. It rejects folding two features
into one subcommand, because on `Stop` the shared `|| true` hid one feature's
failure and the two had to merge their output into one JSON object.

## Verified

- `cli.py`, `MANAGED_HOOKS` holds one `PreToolUse` row, `GUARD_HOOK_COMMAND`,
  which runs `wfctl hook worktree-guard`. The comment above it reads "No
  `|| true` here, unlike `Stop`. A non-zero exit on `PreToolUse` is the guard
  refusing the call."
- `_hook.py` docstring: the guard was 81.7 ms per call before the fast path,
  and "27.1 ms of interpreter startup ... is the floor for a hook spawned per
  Bash call".
- `_entry.py` sends the exact argv `hook worktree-guard` to
  `_hook.worktree_guard` without importing `typer` or `rich`.
- `_hook.worktree_guard` returns 0 at once for a command with no `/` in it.
  `gh pr create` has none, so the review check has to run before that line.
- `_hook.worktree_guard` writes its refusal to stderr and returns 2, and prints
  nothing when it allows a command. Piping an `ls` payload into
  `wfctl hook worktree-guard` printed nothing and exited 0.

## Assumed

- Every pull request in this repository is opened and merged through `gh`. A PR
  opened through a GitHub plugin or a browser gets past the gate. Today's
  history is all `gh`, and a PR opened another way would falsify this.
- A substring check on each command stays well under a millisecond. This is a
  claim about cost without a measurement, and the verification below measures
  it.

## Direct baseline

Add a second `PreToolUse` row on `Bash` to `MANAGED_HOOKS`, running a new
subcommand, `wfctl hook review-gate`. `_entry.py` gains a third exact argv for
its fast path. Each feature has its own entry, its own process, and its own
exit code, as the proposed record on managed hooks describes.

## Decision

The review check runs inside `wfctl hook worktree-guard`, ahead of the worktree
check. It first looks for one of three commands in the payload: `gh pr create`,
`gh pr merge`, or a `gh api` call to the `merge-async` endpoint. It also looks
for the sign-off command. A command that matches none of them goes on to the
worktree check with no file read and no git call.

When a command matches, the review check reads the branch's last reviewed
commit from the state directory and asks git for the commits after it. If any
are unreviewed and no sign-off covers them, it prints the commits to stderr and
returns 2. It refuses the sign-off command outright, since a sign-off the agent
runs is the one the gate exists to stop.

Each check runs in its own `try`, so an error in one doesn't skip the other.
The worktree check allows a command when it can't decide, as it does today. The
review check refuses one of its commands when it can't read the record, since
those commands run a few times per branch and a wrong refusal costs one retry.

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
   │ worktree-   │ │ review-gate   │ (new)      │ worktree-guard      │
   │ guard       │ │               │            │  review check (new) │
   └─────────────┘ └──────┬────────┘            │  worktree check     │
                          │ reads               └──────────┬──────────┘
                   ┌──────▼────────┐                       │ reads, on a match
                   │ state dir     │            ┌──────────▼──────────┐
                   └───────────────┘            │ state dir           │
                                                └─────────────────────┘
```

The divider is the install-modes rule that wfctl owns only the rows it writes
into `settings.json`. In the baseline Claude Code spawns two processes before
every shell command, so each one pays the 27 ms interpreter floor twice. In the
decision it spawns one, and the review check adds a substring match. The graphs
differ by one managed row and one spawn arrow fewer. The change the decision is
built to absorb is a fourth gated command, which touches one match list in
either graph.

## Considered

- A second managed row and subcommand, as the direct baseline describes. We
  didn't choose this because it doubles the process cost on every shell command
  the agent runs. The proposed record on managed hooks argues for one entry per
  feature, and its two harms don't arise here. Both checks block with exit 2
  and stderr, neither swallows the other's exit with `|| true`, and neither
  writes JSON to stdout, so there is no output to merge.
- A git `pre-push` hook. The accepted record already rejects it, because an
  agent can skip it with `--no-verify`.
- An instruction in the `opening-a-change` skill. The accepted record already
  rejects it, because it runs only when the agent follows it.

## Consequences

- The guard's name no longer describes everything it checks. The command name
  is written into every consumer's `settings.json`, so renaming it would strand
  those files, and the name stays.
- The review check and the worktree check share a process. A crash outside both
  `try` blocks, such as a bad payload, skips both, and the guard's existing
  defensive reads cover that case.
- A PR opened without `gh` isn't gated. An agent without hooks isn't gated
  either, and the follow-up issue on a required CI check is where both close.
- A command that only mentions `gh pr create`, such as an `echo`, is refused on
  an unreviewed branch. The refusal names the commits, so the cost is one
  confusing message.

## Verification

- A test pipes a `gh pr create` payload into the guard on a branch with an
  unreviewed commit and asserts exit 2 and the commit on stderr. The same test
  on a fully reviewed branch asserts exit 0 and no output.
- A test pipes the sign-off command into the guard and asserts exit 2.
- A test pipes a `gh pr create` payload with no state directory and asserts
  exit 2.
- A measurement of the guard on an `ls` payload, before and after, shows the
  added cost per call. The `_hook.py` docstring carries the existing numbers to
  compare against.

## Log

- 2026-10-21  proposed  — #622 level 3. Andre asked whether this added a hook on
  every prompt and cost tokens, and approved it once it ran inside the existing
  guard.
