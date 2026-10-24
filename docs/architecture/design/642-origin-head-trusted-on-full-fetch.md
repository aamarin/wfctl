---
status: proposed
---

# The review range trusts `origin/HEAD` as the trunk only when `origin` fetches every branch

## Context

The review range leaves out every commit the trunk already holds, so the range is only as correct as the trunk it finds. The `_paths.trunk_branch` function finds the trunk. It reads the branch `wfctl.json` declares, then `origin/HEAD`, then a bare repository's HEAD, and then the first of `main`, `master`, or `dev` that `git rev-parse --verify` resolves. The `trunk_refs` function in `_review.py` turns that name into the refs the range excludes.

Two clone states made `trunk_refs` exclude the branch under review:

1. A clone made with `git clone --single-branch --branch <feature>` fetches only the feature branch. If `origin/HEAD` names that branch, the trunk is the branch itself and the range comes back empty. Newer git sets `origin/HEAD` this way on its own, and `git remote set-head` does it on any version. A check that compares the trunk's name with the branch under review misses it after `git branch -m` renames the local branch, and on a detached HEAD, where there's no branch name to compare.
2. The same clone has no `main` branch at all, so `trunk_branch` falls through to the name guess, and `git rev-parse --verify main` resolves a tag named `main`. Previously, `trunk_refs` then returned the short name `main`, which git resolved to that tag, and every commit up to the tag read as already on the trunk.

`review-covers-unreviewed-commits` constrains this: the first review on a branch starts where the branch left `main`. This record keeps that rule and keeps `_paths.trunk_branch` as the one place the trunk is decided. It changes only which answers `trunk_refs` accepts.

## Verified

- On git 2.44, Apple and Homebrew alike, a single-branch clone of a feature branch gets no `origin/HEAD`, and `git remote set-head -a` fails. The tests set it with `git symbolic-ref`, the way `git remote set-head origin <branch>` would.
- A single-branch clone writes `remote.origin.fetch` as `+refs/heads/<feature>:refs/remotes/origin/<feature>`. A full clone writes `+refs/heads/*:refs/remotes/origin/*`. This repository's own refspec is the wildcard.
- `_paths.trunk_branch` returns the declared trunk before it looks at `origin/HEAD`, so a declared trunk never goes through this check.
- `_review_gate.py` turns every exception from `_judge` into "the review check failed".

## Assumed

- `origin/HEAD` in a clone that fetches every branch names the remote's default branch, unless someone set it by hand. A clone where someone ran `git remote set-head origin <feature>` and then renamed the branch passes this check (the security review reproduced it at 013b70d). That takes a deliberate command, and this record doesn't cover it.

## Direct baseline

Compare the trunk's branch name with the branch under review and refuse a match, which the `642-commit-range-takes-judged-branch.md` record already does. Keep falling back to the short name when neither `refs/remotes/origin/<trunk>` nor `refs/heads/<trunk>` exists.

## Decision

`trunk_refs` accepts a trunk only as a branch ref. When neither `refs/remotes/origin/<trunk>` nor `refs/heads/<trunk>` exists, it raises `NoTrunk` instead of returning the short name, so a tag can never stand in for the trunk.

When the trunk came from `origin/HEAD` and `wfctl.json` declares none, `trunk_refs` reads `remote.origin.fetch` and refuses unless one refspec's source is `refs/heads/*` or `refs/*`. The refusal says to fetch the trunk with `git remote set-branches --add origin <trunk>` and `git fetch`, and then declare it in `wfctl.json`.

A negative refspec beside the wildcard, such as `^refs/heads/main`, still passes. It stops `origin/main` from updating, which leaves the trunk stale and the range larger, never smaller. It can't point `origin/HEAD` at the branch under review.

## Diagram

No boundary in force runs between these components, so neither graph has a divider.

```
baseline

  trunk_refs ──calls──► trunk_branch
  trunk_refs ──reads──► branch refs, falling back to the short name

decision

  trunk_refs ──calls──► trunk_branch
  trunk_refs ──reads──► branch refs only
  trunk_refs ──reads──► remote.origin.fetch (new), when the trunk came from origin/HEAD
```

The decision adds one arrow, a read of the fetch refspec. The baseline answers whether the trunk has the same name as the branch under review. The decision answers whether `origin/HEAD` could name anything except the remote's default branch, which still holds after a rename or a checkout that leaves no name to compare. The change this absorbs is any new way to reach the same clone state, such as a checkout that hasn't been tried, since the refspec doesn't depend on the local branch.

## Considered

- The direct baseline. We didn't choose it because a rename or a detached HEAD gets past the name comparison in the clone state the issue describes.
- Compare `origin/HEAD` with the remote's real default, from `git ls-remote --symref origin HEAD`. This also catches `origin/HEAD` set by hand in a full clone. We didn't choose it because it adds a network call to every `wfctl review start` and every guard check, and fails offline.
- Refuse when the trunk is the upstream of the branch under review. We didn't choose it because `git checkout -b x origin/main` makes `origin/main` the upstream of an ordinary feature branch, so the refusal would fire on the most common way to start one.

## Consequences

A single-branch clone of a feature branch can no longer empty the review range, whatever its local branch is called.

A correct single-branch clone of `main` is refused too, until `wfctl.json` declares `trunk`. The refusal prints that remedy, and `test_range_reads_a_declared_trunk_in_a_single_branch_clone_of_it` checks that it works.

Every caller of `trunk_refs` now gets `NoTrunk` where it used to get a short name, including #627's CI check. A CI checkout that fetches only the PR's branch has to fetch the trunk or declare it.

At the worktree guard, both refusals surface as "the review check failed", which tells an agent to stop and ask a person, even though the agent could fix the state itself by declaring `trunk`. A shallow clone and a missing trunk already surface the same way, and reporting these as ordinary refusals is a change to the guard for every `ReviewError`, which this record leaves for a separate issue.

## Verification

- `test_range_refuses_a_single_branch_clone_whose_origin_head_names_the_branch` covers the clone as cloned, after a rename, and on a detached HEAD.
- `test_range_reads_a_declared_trunk_in_a_single_branch_clone_of_it` covers the remedy.
- `test_range_refuses_a_tag_named_after_a_trunk_branch_the_clone_lacks` covers the tag.

## Log

- 2026-10-24  proposed  — written for #642, after the security review found the fetch refspec rule and the tag refusal in the code with no record deciding them
