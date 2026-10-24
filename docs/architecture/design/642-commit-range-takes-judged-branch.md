---
status: proposed
---

# The `commit_range` function takes the branch under review, and refuses a trunk with the same name

## Context

The `commit_range` function lists the commits a review group hasn't reviewed. It leaves out every commit the trunk already holds, so the trunk has to be a different branch from the one under review. When the trunk is the branch itself, every commit reads as already on the trunk, and the range comes back empty. This happens when `wfctl.json` names the branch as the trunk, or when `origin/HEAD` points at it.

Currently, only the worktree guard checks for this. Its `_judge` function compares the trunk with the branch the PR command acts on and refuses a match. The `wfctl review start` and `wfctl review sign-off` commands call `commit_range` with no such check, so `review start` reports the group up to date with nothing reviewed. The CI check #627 is building will call `commit_range` too.

The check can't compare the trunk with the checked-out branch, because the guard judges a merge from the `main` checkout, where the checked-out branch is always the trunk. 5218818 tried that and was reverted. As a result, only the caller knows which branch is under review, and it has to pass it in.

`review-covers-unreviewed-commits` constrains the range: the first review on a branch starts where the branch left `main`. This record keeps that rule and does not change who decides the trunk, since `_paths.trunk_branch` still does.

## Verified

- `_review_gate.py:749` reads the trunk with `_paths.trunk_branch`, and line 756 returns a refusal when `branch == trunk`, before it calls `_review.unreviewed` at line 780.
- `_review.py:406` `start` calls `commit_range(repo_root, head, last_reviewed(...), timeout)`, with no branch.
- `cli.py:6213` `review sign-off` calls `_review.unreviewed(repo_root, agent_dir, groups, head)`, with no branch.
- `_review_gate.py` reports any `ReviewError` as "the review check failed", which `AGENTS.md` tells an agent to stop on and take to a person. The trunk check at line 756 is an ordinary refusal instead.
- `tests/test_review_gate.py:1072` pins the gate's own refusal text for a trunk that is the judged branch.

## Assumed

- #627's CI check knows the branch under review, from the pull request it runs on. A caller that cannot name the branch would get no check from this, and would need the single-branch refusal in `trunk_refs` alone.

## Direct baseline

Each caller checks for itself, the way the guard already does. `review start` and `review sign-off` each read `_paths.trunk_branch`, strip `origin/`, compare the result with `resolve_branch`, and print their own error. `commit_range` stays as it is.

## Decision

`commit_range`, `unreviewed`, and `start` take a keyword argument, `branch`, that defaults to None. When a caller passes it, `commit_range` raises a `ReviewError` if the trunk's branch name matches it. Every caller in wfctl passes it. A caller that leaves it out gets the behavior it had before, which keeps #627's calls working unchanged.

The guard keeps its own check, because it refuses a misdeclared trunk as an ordinary refusal and not as a failed check. It also passes `branch` to `unreviewed`, so a later change that reorders `_judge` still can't skip the check.

## Diagram

No boundary in force runs between these components, so neither graph has a divider.

```
baseline

  guard        ──calls──► trunk_branch
  guard        ──calls──► commit_range   (through unreviewed)
  review start ──calls──► trunk_branch
  review start ──calls──► commit_range
  sign-off     ──calls──► trunk_branch
  sign-off     ──calls──► commit_range   (through unreviewed)
  commit_range ──calls──► trunk_branch

decision

  guard        ──calls──► trunk_branch
  guard        ──calls──► commit_range   (through unreviewed, passes branch)
  review start ──calls──► commit_range   (passes branch)
  sign-off     ──calls──► commit_range   (through unreviewed, passes branch)
  commit_range ──calls──► trunk_branch
```

The baseline has seven arrows and the decision has five. In the baseline, each caller reads the trunk itself so it can make the comparison. In the decision, only the guard does, and only for its own refusal. The change this absorbs is a new caller such as #627's CI check, which adds two arrows in the baseline and one in the decision, and in the decision the one arrow carries the check with it.

## Considered

- The baseline: each caller checks for itself. We didn't choose this because it leaves the check to every caller, and `review start` is the caller that already missed it.
- A required `branch` argument. This is sound, since no caller could then skip the check. We didn't choose it because #627 is written against the current signature, and a required argument would break its calls before it can pass one.
- Removing the guard's own check, so `commit_range` is the one place it lives. We didn't choose it because the guard would then report a misdeclared trunk as a failed check, which tells the agent to stop and fetch a person over a `wfctl.json` edit it can fix itself.

## Consequences

`review start` and `review sign-off` now refuse a trunk that is the branch under review, instead of reporting nothing to review.

`review start` run from the `main` checkout now raises, since the branch under review is the trunk. It used to report the group up to date, which was true but hid that nothing on `main` can be reviewed this way.

The guard compares the names twice, once itself and once through `commit_range`. The second comparison never fires while the first comes before it.

A caller that leaves `branch` out is unprotected and gets no warning. That's the price of the default, and the check only covers wfctl's own callers.

## Verification

- A test sets `origin/HEAD` to the branch under review and shows that `commit_range` raises when given that branch.
- A test shows `review start` refuses the same state.
- `tests/test_review_gate.py:1072` still passes with its own refusal text.

## Log

- 2026-10-24  proposed  — written for #642, where `review start` reported a group up to date while the trunk was the branch under review
