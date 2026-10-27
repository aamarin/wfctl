---
status: proposed
---

# The local check and CI count unreviewed commits with one function, each passing in its own record of what was reviewed

## Context

The accepted record `review-record-in-git-notes.md` has CI work out which
commits on a PR no review covers, using the same range rules as the local
check. It also keeps the local record in the state directory and has the guard
keep reading it. So two callers now ask the same question from two different
records:

1. The guard and `wfctl review sign-off` read each group's last reviewed commit
   and the sign-off from the branch's state directory.
2. The CI check reads them from the notes under `refs/notes/wfctl-review`.

Currently, the `unreviewed` function answers that question, and it reads the
state directory itself. CI has no state directory, so it can't call
`unreviewed` as it is. If the two callers count differently, a PR can pass on
one side and fail on the other, which is the disagreement the accepted record's
test exists to catch.

## Verified

- `_review.py:609` `unreviewed(repo_root, agent_dir, groups, head, timeout)`
  reads the sign-off with `signed_off(agent_dir)` at line 624, and each group's
  last reviewed commit with `last_reviewed(agent_dir, group.name)` at line 639.
- `unreviewed` has two callers: `_review_gate.py:780` in the guard, and
  `cli.py:6213` in `review sign-off`.
- A sign-off covers a commit when the commit is the signed-off one or one of its
  ancestors (`_review.py:633`). The state directory holds one sign-off, and a new
  one replaces it (`_review.py:596`).
- `commit_range` (`_review.py:178`) takes the last reviewed commit as an
  argument and reads nothing from disk.
- #642 adds a `branch` keyword argument to `commit_range`, `unreviewed`, and
  `start`, defaulting to None (`origin/642-review-range-hidden-commits`, design
  record `642-commit-range-takes-judged-branch.md`).

## Assumed

- From the notes, a group's last reviewed commit is the nearest ancestor of the
  head that carries that group's line. That holds because a run starts where the
  last complete run ended, so a note on commit C means the group reviewed every
  commit from where the branch left `main` up to C. If wfctl ever starts a run
  somewhere else, such as a run that covers only part of a branch, the nearest
  note no longer covers everything before it, and this breaks.
- Several sign-off notes can reach the head, one from each sign-off. Treating any
  of them as covering its ancestors is safe, since each one is a person's
  sign-off of those commits.

## Direct baseline

CI gets its own function. A new `unreviewed_from_notes` in a CI module reads the
notes, finds each group's last reviewed commit and the sign-offs, and repeats
the loop in `unreviewed`: call `commit_range`, drop the commits a sign-off
covers, and collect what's left. `unreviewed` stays as it is.

## Decision

`unreviewed` takes what was reviewed as arguments instead of reading it: a
mapping from each group's name to its last reviewed commit, and the list of
signed-off commits. It no longer takes `agent_dir`.

Two small readers build those arguments:

1. The state directory reader returns `last_reviewed(agent_dir, g)` for each
   group, and the one sign-off as a list of zero or one commit. The guard and
   `review sign-off` call it.
2. The notes reader walks the head's ancestors once, and returns each group's
   nearest noted commit and every signed-off commit it finds. The CI check calls
   it.

This lands after #642 merges, since #642 changes the signature of the same
function.

## Diagram

```
baseline

stable    ┌──────────────┐
          │ commit_range │◄──────────── calls ────────────┐
          └──────▲───────┘                                │
                 │ calls                                  │
          ┌──────┴───────┐                     ┌──────────┴─────────────┐
          │  unreviewed  │                     │ unreviewed_from_notes  │
          │  reads state │                     │ (new)  reads notes     │
          └──────▲───────┘                     └──────────▲─────────────┘
                 │ calls                                  │ calls
volatile  ┌──────┴───────┐                     ┌──────────┴─────────────┐
          │    guard     │                     │       CI check         │
          └──────────────┘                     └────────────────────────┘

decision

stable    ┌──────────────┐
          │ commit_range │
          └──────▲───────┘
                 │ calls
          ┌──────┴───────┐
          │  unreviewed  │◄──────────── calls ────────────┐
          └──────▲───────┘                                │
                 │ calls                                  │
          ┌──────┴───────┐                     ┌──────────┴─────────────┐
          │    guard     │                     │       CI check         │
          └──────┬───────┘                     └──────────┬─────────────┘
                 │ calls                                  │ calls
volatile  ┌──────▼───────┐                     ┌──────────▼─────────────┐
          │ state reader │                     │ notes reader (new)     │
          └──────────────┘                     └────────────────────────┘
```

No boundary in force runs through either graph. The local machine and CI are
the two sides of `review-record-in-git-notes.md`, but each side here only reads
a record and calls shared code.

The change this is built to absorb is a change to how a range is counted, such
as a new rule for which merges need review. In the baseline, two functions each
call `commit_range` and each drop the commits a sign-off covers, so that change
touches two arrows into `commit_range` and two copies of the sign-off rule. In
the decision, it touches one arrow and one copy. Both graphs add one new box.
The baseline adds a second counting function, and the decision adds a reader
that only finds commits.

## Considered

- A separate CI function, as the direct baseline describes. We didn't choose
  this because the sign-off rule and the loop over groups would exist twice, and
  the accepted record's test would be the only thing keeping them the same.
- CI writes the notes out as a fake state directory, with a
  `last-reviewed.json` per group and a `sign-off.json`, then calls `unreviewed`
  unchanged. It needs no change to `unreviewed`. We didn't choose it because the
  state directory holds one sign-off, and the notes can hold several, so CI would
  have to pick one and could drop a real sign-off.
- Pass a reader object, with a class per record. We didn't choose it because two
  plain values cover everything `unreviewed` needs, and a class per record adds
  a hierarchy with one method.

## Consequences

- Both callers count with the same function, so a change to the range rules
  reaches CI and the guard together.
- The guard and `review sign-off` each make one extra call to build the
  arguments.
- #627 can't land this part before #642 merges, or the two branches conflict in
  `unreviewed`.

## Verification

- The accepted record's scratch repository test runs both readers over the same
  history and checks that `unreviewed` returns the same commits for each.
- A test puts two sign-off notes on a branch and checks that commits under
  either one count as covered.

## Log

- 2026-10-24  proposed  — #627 level 3. Andre approved the direction in the
  627-ci-review-check session.
