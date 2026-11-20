# Auto-approve has its own command

Contexts: evidence-and-derivation, session-continuity, install-and-drift

## Problem Statement

A person turns auto-approve on or off at any point in a session, from inside the
workflow, and a scripted run starts in the mode when its worktree is created.

Previously, `wfctl start --auto-approve` was the only way to set the mode, and
`/start-session` can't pass the flag. In the #799 unattended run, the agent ran
`wfctl start --auto-approve` a second time to get the grant. The grant worked,
but `start` then printed "Already initialized", which reads like a failure.

## Recommended Direction

A new command sets the mode:

```
wfctl auto-approve on
wfctl auto-approve off
wfctl auto-approve
```

The last form prints the mode and who turned it on, as "this session", "another
session", or "an unknown session". It never prints the session's ID, the same
way `wfctl status` reports who holds a branch.

The agent runs `wfctl auto-approve on` only when a person asked, either in the
conversation or by starting the run with the creation flag below. It never turns
the mode on by its own judgment. wfctl can't tell a grant someone asked for from
one nobody did, so the `mode` event names the session that made the grant, and
the reviewer sees it there.

`wfctl auto-approve on` is refused in two cases:

1. Another session holds the branch. The refusal points at `/start-session`,
   which takes the branch over first.
2. `wfctl start` would refuse a session on the branch, such as when its issue
   is closed. The refusal is the one `start` prints, with its fix line.

`wfctl auto-approve off` is never refused, since turning the mode off raises
the bar and needs no person.

A scripted run gets the grant when its worktree is created. Both `.workmux.yaml`
files, this repository's and the seed wfctl ships, gain a `post_create` line
that runs `wfctl auto-approve on` once, and only when `WFCTL_AUTO_APPROVE` is
exactly `1`:

```bash
WFCTL_AUTO_APPROVE=1 workmux add 812-foo
```

wfctl itself never reads the variable. A pane restart runs `wfctl start` again,
and if `start` read the variable, it would turn the mode back on right after the
review cap turned it off.

`install-config` writes the seed once and never updates it, so a repository
seeded earlier doesn't get the new line. If you run `install-config workmux
--force` to get it, your edits to the file are replaced. So `wfctl auto-approve`
with no argument prints an `ℹ` note with the line to add when `post_create` has
no grant line. The line is opt-in, so the note goes where someone interested in
the mode looks. `wfctl doctor` doesn't report it, because a repository that
never uses auto-approve would otherwise see a warning on every run.

## Boundaries and Ownership

wfctl stores the mode and writes the grant event, since nothing on disk implies
the mode and the agent shouldn't be the witness to its own grant. The full
argument is in `docs/architecture/approval-mode-is-stored-intent.md`.

The evidence package writes the mode file and the `mode` event. It can't import
session continuity, so the CLI looks up the caller's session identity and passes
it in.

The creation hook is the only reader of `WFCTL_AUTO_APPROVE`, and it reads it
once, when the worktree is created.

In Claude Code, the person approves a prompt before the agent's `wfctl
auto-approve on` runs, from two `permissions.ask` rules wfctl installs. The
argument is in `docs/architecture/auto-approve-grant-asks-first.md`.

## Key Assumptions to Validate

- [ ] workmux hooks inherit the shell's environment. The shipped hook already
  relies on this for `WFCTL_AGENT`, and the binary does no `env_clear`. Test it
  by running `WFCTL_AUTO_APPROVE=1 workmux add` on a throwaway issue.
- [ ] A refused grant in `post_create` leaves the worktree attended and still
  comes up. The line ends in `|| true`. Test it with a closed issue.
- [ ] The note finds the grant line only inside `post_create`, not a
  commented-out copy or a line elsewhere in the file. Cover it with the same
  cases `doctor`'s skills-install warning has.

## MVP Scope

1. The `wfctl auto-approve [on|off]` command in `cli.py`, beside `start`.
2. One grant helper shared by `start --auto-approve` and the new command. Only
   the new command refuses when another session holds the branch.
3. A `session` field on the `mode` event, written through a new argument in
   `evidence/_mode.py`, and a reader for the last grant. Events written before
   this change read as "an unknown session".
4. The creation line in both `.workmux.yaml` files.
5. An `ℹ` note under `wfctl auto-approve`'s output when `post_create` has no
   grant line, which prints the line to add and never changes the exit code.
6. The skills `using-wfctl` and `plan-walkthrough` name `wfctl auto-approve on`
   in place of `wfctl start --auto-approve`, and `plan-walkthrough`'s refusal
   names `wfctl auto-approve off`.
7. `using-wfctl` explains that `install-config` writes a file once and never
   updates it, so a template change doesn't reach a repository already seeded,
   and that `--force` replaces the repository's edits.

`start --auto-approve` and `--no-auto-approve` keep working, since scripts and
handoffs already use them.

## Not Doing (and Why)

- `start` reading `WFCTL_AUTO_APPROVE` — a pane restart would turn the mode back
  on after the review cap turned it off, a `0` in a shell profile would turn off
  a grant made mid-session, and it can't reach a session already running.
- Patching an existing `.workmux.yaml` automatically — every seeded
  `post_create` already has entries, and wfctl would be guessing where the line
  belongs in a file it doesn't parse.
- Granting from `install-skills` or `issue start` — `install-skills` runs at
  every session start and would re-grant after the review cap, and `issue
  start` only moves the issue on the tracker's board.
- Tying the mode to the `claude-auto` launcher — auto permission mode only stops
  Claude asking before it runs commands, and attended sessions use it too.
- A worktree guard refusal of an agent's grant — the user asked for an
  agent-driven grant, and the guard can't tell a grant someone asked for from
  one nobody did.
- A `doctor` warning about the missing line — the line is opt-in, so a
  repository that never uses auto-approve would see it on every run, and a
  one-time notice would need wfctl to remember it was shown.
- Clearing the mode in `pre_remove` — a worktree recreated for the same open
  issue is usually the same run continuing.

## Open Questions

None. The record `approval-mode-is-stored-intent` is proposed and waits on the
user to accept it.

## Software design decisions

No level-3 record was written. Each piece extends an existing structure, and no
credible alternative structure was weighed. A `wfctl step none
brainstorm.software-design` exception is filed for each of the three contexts.
