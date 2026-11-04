# Read review.commands from the trunk

Contexts: evidence-and-derivation

## Problem

`wfctl review start` reads `review.commands` from the branch's own `wfctl.json`.
A reviewer command is a shell command the review skill runs, so an agent on a
branch can change it and have its own review panel run the new command before
anything merges. This happened on #710, where the branch added a `codex` command
and its panel ran it. `review.rounds` and `trunk` already come from the trunk for
the same reason.

## Direction

`review start` reads the commands from `wfctl.json` on the trunk, the same trunk
`trunk_rounds` reads `review.rounds` from, and warns when the branch's copy sets
a different command. The groups and reviewer counts stay on the branch.

## Level 1: what the user sees

On a branch whose `wfctl.json` sets `"codex": "codex exec --sandbox none"` while
`main` sets `"codex": "codex exec --sandbox read-only"`, `wfctl review start
security` prints:

```
⚠ this branch sets review.commands.codex to `codex exec --sandbox none`, but wfctl runs `codex exec --sandbox read-only` from origin/main until the change merges
security run 001 · round 1 of 3 · 2 commits since 1a2b3c4 · head 5d6e7f8
reports: …/runs/001/
s1 claude
s2 claude
s3 codex  codex exec --sandbox read-only
```

When the branch adds a model the trunk has no command for, the warning says so,
and the roster leaves that model's reviewers out:

```
⚠ this branch sets review.commands.gemini to `gemini -p`, but origin/main sets no command for gemini, so its reviewers are left out until the change merges
…
s4 gemini ✗ unavailable
⚠ gemini: no command in wfctl.json on origin/main; s4 left out of this run
```

When the branch drops a command the trunk has, the trunk's still runs, and the
warning names it. A trunk with no `wfctl.json`, or no `review.commands`, has
no commands and needs no warning of its own. A trunk whose `wfctl.json` can't be
read, or whose commands aren't valid, is refused as it is today, since
`review start` checks the trunk's group list in the same file first.

The decision that the trunk's command runs and the branch's difference is a
warning comes from the #711 handoff. The handoff also asked for a warning and a
fallback when the trunk can't be read. The plan review found that path can't be
reached without changing the reader CI and the worktree guard share, so today's
refusal stays (spec User Story 3).

## Level 2: architecture

The source of truth for reviewer commands moves from the branch to the trunk.
That moves ownership, so it has a record.

## Level 3: design

No structural choice that a second module has to follow. `review start` swaps
each reviewer's command for the trunk's, and the rule that a model other than
Claude with no command can't run sits in the function that already decides
availability (`wfctl step none brainstorm.software-design`).

## Software design decisions

No level-3 record: the change makes no structural choice another module has to
follow.

## Architecture decisions

- docs/architecture/review-commands-from-trunk.md — wfctl reads reviewer commands from the trunk, and the groups stay on the branch

## Not doing

1. Moving the groups or reviewer counts to the trunk. A branch that adds a group
   only makes its own review stricter, and #709 lets a person try a group on a
   branch before it's enforced.
2. Changing `wfctl check config`, which keeps validating the working tree's
   commands so a bad command is caught before it merges.
3. Changing the worktree guard or CI, which read the groups and never run a
   command.

## Scope

`wfctl/_review.py`, `wfctl/_review_config.py`, and the `review start` command in
`wfctl/cli.py`, so this branch doesn't edit the functions #698, #700, and #707
change.
