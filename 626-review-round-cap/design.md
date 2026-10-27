# Review round cap

## Problem statement

wfctl stops a review group after a set number of rounds on one branch, so an
unattended run can't loop through panels with nobody watching, and the user can
still let a change through with a sign-off.

## Recommended direction

A review round is one run of every review group, in order: security, then code,
then any group the repository adds. Each group runs once per round. Security no
longer runs again over its own fixes before code starts. Code reviews those
fixes in the same round, and security reviews them in its next run, which
covers every commit since its last review as before.

Because each group runs once per round, a group's run count on the branch is
the branch's round count. `wfctl review start <group>` counts the runs the
group has started and refuses to start one past the cap. The refusal tells the
agent to stop and ask the user to run `wfctl review sign-off`, which is still
the only way past the cap on one branch.

The cap is `review.rounds` in `wfctl.json`, and the default is 3. wfctl reads it
from the trunk's copy of `wfctl.json`, not the branch's, since the agent writes
the branch and the cap exists to stop the agent. Raising the cap is a change
merged to the trunk.

### Example

Five commits of implementation on one branch, with a cap of 3:

1. Round 1: security run 001 reviews the 5 commits, and the agent commits fix
   A. Code run 001 reviews all 6, and the agent commits fixes B and C.
2. Round 2: security run 002 reviews A, B, and C. Code run 002 reviews B and C.
   Both are clean, so the guard allows `gh pr create`.

Under the old instruction, the same change took five runs, since security ran
again over A before code started.

## Behavior (level 1)

`wfctl review start <group>` has four outcomes. Each line below is what the
command prints in that state.

Nothing to review. This is unchanged, and the cap doesn't apply, since no run
is written:

```
security is up to date at 9f8e7d6
```

Under the cap. The header gains the round, so the agent and the user see how
close the cap is:

```
security run 002 · round 2 of 3 · 3 commits since a1b2c3d · head 9f8e7d6
reports: <state>/reviews/security/runs/002/
s1 claude
...
```

At the cap, with a sign-off covering the head. No run is needed, and exit 0, so
the agent goes on to the next group and then to the PR:

```
security has run 3 of 3 rounds; a sign-off covers 9f8e7d6, so nothing is left to review
```

At the cap, with commits no sign-off covers. Exit 1, and nothing is written:

```
✗ security has run 3 of 3 rounds on this branch, the most review.rounds allows
  Ask the user to run `wfctl review sign-off` in their own terminal.
```

Two warnings sit beside those outcomes:

```
⚠ this branch sets review.rounds to 5, but wfctl reads 3 from origin/main until the change merges
⚠ review.rounds on origin/main isn't a number of 1 or more; wfctl uses the default of 3
```

Each state was read for whether it tells the truth:

- The "up to date" line stays true at the cap. Refusing there would tell the
  agent to ask for a sign-off when nothing needs one.
- Without the signed-off state, the refusal would ask for a sign-off the user
  already gave. `unreviewed()` already treats a commit covered by the sign-off
  as reviewed, so the guard allows the PR, and `review start` has to agree with
  it.
- The refusal names `review.rounds`, so a reader knows the cap is a setting and
  where it lives.

Level-3 consequences of these states:

1. `review start` has to read the sign-off, not only the run records, before it
   refuses.
2. `review start` has to read `wfctl.json` twice, from the trunk and from the
   working tree, so it can warn when they disagree.
3. The panel skill's example header in `fanning-out-code-review` gains the round.

## Structure (level 3)

1. `_review_config` parses `review.rounds` from a loaded `wfctl.json` object
   and validates it as an integer of 1 or more. `rounds` joins `_REVIEW_KEYS`,
   so `wfctl check config` reports a bad value on the working tree like any
   other `review` finding.
2. `_review` reads the trunk's `wfctl.json` with `git show <ref>:wfctl.json`,
   using the first ref `trunk_refs` returns. That is `origin/<trunk>` when it
   exists, the same ref `commit_range` measures from. A missing file or missing
   key gives the default. An invalid value on the trunk also gives the default,
   with the `⚠` line, since refusing would block every review on every branch
   until someone fixes `main`.
3. `_review.start` counts the group's run folders that hold a `run.json`, the
   same folders `latest_run` reads. A folder from an interrupted start isn't a
   run and isn't counted. The count is derived on every call and isn't stored
   (`session-state-is-re-derived.md`).
4. `start` decides in this order: the commit range first, so a group with
   nothing to review is up to date whatever its count. Then the count against
   the cap, then the sign-off.
5. The worktree guard doesn't change. It already refuses `gh pr create` and
   `gh pr merge` while a group has unreviewed commits that no sign-off covers.

| checked | assumed |
|---|---|
| `latest_run` counts only folders holding `run.json` (`_review.py:451`) | `git show origin/main:wfctl.json` works from every worktree, including one whose `origin/main` is stale |
| `unreviewed()` treats commits the sign-off covers as reviewed (`_review.py:747`) | the panel skill reads `review start`'s header as prose, so adding the round breaks no parser |
| `_REVIEW_KEYS` rejects an unknown key under `review` (`_review_config.py:34`) | no consumer repository relies on security re-running over its own fixes |
| the guard loads the review module only for a command holding `gh`, `merge`, or `sign`, so `review start` never reaches it (`_review_gate.py:7`) | |
| `opening-a-change` Step 1 is where security's extra run and "doesn't count rounds yet (#626)" are written | |

No level-3 choice here weighed a credible alternative that draws no boundary,
so this design has no record under `design/`. Storing the count in a file was
the one alternative, and `session-state-is-re-derived.md` already rules it out.

## Key assumptions to validate

- [ ] The trunk read works from a worktree with a stale `origin/main`. Test it
      by running `review start` after a local edit to `wfctl.json` on the
      branch and checking the `⚠` line.
- [ ] Reaching the cap end to end. Run `uv run wfctl install-skills`, take a
      test branch through three rounds, confirm the fourth `review start`
      refuses, then sign off and confirm the guard allows `gh pr create`.

## MVP scope

In:

1. The `review.rounds` key, validated by `check config`, with a default of 3.
2. The count and the refusal in `wfctl review start`, with the four outcomes
   above.
3. The trunk read and the two warnings.
4. `opening-a-change` Step 1 rewritten: one run per group per round, and the
   cap enforced by wfctl rather than counted by the agent.
5. The `fanning-out-code-review` example header, and a paragraph on
   `review.rounds` in `AGENTS.md` under "Declaring reviewers".
6. A release note for #626.

Out: see below.

## Not doing (and why)

- A command that grants more rounds on one branch, such as `wfctl review
  extend`. Sign-off already lets a change through, and Andre wasn't convinced
  a second command earns its place.
- A per-group cap. Every group runs once per round, so one number covers them
  all.
- Making the 20-reviewer limit configurable. It catches a typo, such as a count
  of 2,000,000, and in the same file as the counts it would stop catching one.
- Reusing an incomplete run when `review start` runs again at the same head.
  A restarted run counts as a round. That costs a round in a rare case, and
  changing how runs are numbered is outside this issue.
- Resetting the count after a sign-off. A commit added after the sign-off is
  unreviewed again, and once the cap is reached it needs another sign-off.

## Open questions

- Should `wfctl status` show the round count beside the review state? Nothing
  in this issue needs it, and it can follow.

## Software design decisions

No level-3 record. The only structural alternative, storing the count in a
file, is ruled out by `session-state-is-re-derived.md`. The level-2 records
are `docs/architecture/review-round-count.md` and
`docs/architecture/review-round-cap.md`.
