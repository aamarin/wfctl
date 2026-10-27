# CLI contract: `wfctl review start` with a round cap

These are the lines `review start` prints after this change. Every line here is
asserted in `tests/test_review_cli.py`. The cap is 3 in each example unless the
example says otherwise.

## Warnings

Warnings come first, before any outcome line, and each starts with `⚠`. The
command prints a warning whichever outcome follows.

The branch names a different trunk than the default branch does. The review
goes on against the default branch's trunk, and the cap is read from there:

```
⚠ this branch sets trunk to loose, but wfctl reads main from origin/main until the change merges
```

The default branch's `trunk` value isn't a branch name:

```
⚠ trunk on origin/main isn't a branch name; wfctl reviews against main
```

The default branch's `wfctl.json` can't be read as a JSON object, when it's
read for the trunk:

```
⚠ can't read wfctl.json on origin/main (<reason>); wfctl reviews against main
```

When the trunk is the default branch, the cap read below reads the same file
and prints its own line too, since each line says what wfctl fell back to.

The branch sets a different valid value than the trunk:

```
⚠ this branch sets review.rounds to 5, but wfctl reads 3 from origin/main until the change merges
```

The trunk's value is invalid, or the trunk's `review` value isn't an object:

```
⚠ review.rounds on origin/main isn't a whole number of 0 or more; wfctl uses the default of 3
```

The trunk's `wfctl.json` can't be read as a JSON object:

```
⚠ can't read wfctl.json on origin/main (<reason>); wfctl uses the default of 3
```

## Outcome 1: nothing to review

This is unchanged. Exit 0.

```
security is up to date at 9f8e7d6
```

## Outcome 2: a run starts

Exit 0. Only the header changes. The `reports:` line and the roster lines stay
as they are today.

```
security run 002 · round 2 of 3 · 3 commits since a1b2c3d · head 9f8e7d6
reports: <state>/reviews/security/runs/002/
s1 claude
s2 claude
s3 claude
```

## Outcome 3: at or past the cap, and the sign-off covers every commit left

Exit 0, and nothing is written. The sign-off covers every commit in the group's
range, which is the check the guard makes. The line names the signed-off
commit, not the head, since a clean merge of the trunk after the sign-off makes
a head the sign-off doesn't cover. The first clause follows the count and the
cap the same way outcome 4 does.

At the cap:

```
security has run 3 of 3 rounds; the sign-off at 9f8e7d6 covers every commit left to review
```

Past the cap, after the trunk lowered it:

```
security has run 4 rounds, more than the 3 review.rounds allows; the sign-off at 9f8e7d6 covers every commit left to review
```

A cap of 0:

```
review.rounds is 0, so security doesn't run; the sign-off at 9f8e7d6 covers every commit left to review
```

## Outcome 4: at or past the cap, and the sign-off doesn't cover every commit left

Exit 1, and nothing is written. The first line depends on the count and the cap.

At the cap:

```
✗ security has run 3 of 3 rounds on this branch, the most review.rounds allows
  Ask the user to run `wfctl review sign-off` in their own terminal.
```

Past the cap, after the trunk lowered it:

```
✗ security has run 4 rounds on this branch, more than the 3 review.rounds allows
  Ask the user to run `wfctl review sign-off` in their own terminal.
```

A cap of 0:

```
✗ review.rounds is 0, so security doesn't run on this branch
  Ask the user to run `wfctl review sign-off` in their own terminal.
```

## No trunk, or the trunk is the branch under review

Exit 1, and nothing is written. These are today's two refusals. When the trunk
came from the default branch, each names that file, since the working tree's
`wfctl.json` isn't read on that path:

```
✗ can't find the trunk branch develop; check trunk in wfctl.json on origin/main, or run git fetch
✗ the trunk branch is 637-x, the branch under review; check trunk in wfctl.json on origin/main
```

On the fallback path, with no `origin/HEAD`, and when the branch's own `trunk`
names a branch the clone doesn't have, both keep today's wording.

## `origin/HEAD` names a ref the clone doesn't have

Exit 1, and nothing is written. This comes before any outcome, since the trunk
can't be found. `review sign-off` and the PR check refuse with the same line,
since they read the trunk the same way.

```
✗ origin/HEAD names origin/main, which this clone doesn't have; run git remote set-head origin --auto
```

## Invalid `review.rounds` in the working tree

This uses the same path as every other invalid `review` setting. Exit 1.

```
✗ wfctl.json:
  - review.rounds must be a whole number of 0 or more
```

`wfctl check config` reports the same problem string.
