---
status: proposed
---

# The `owns_branch` function refuses the `main` checkout, so the guard and the store share one rule

## Context

The worktree guard and the `wfctl store specs` command both ask the `owns_branch` function whether a commit in a folder lands on a branch of its own. The function checks whether any other worktree has the folder's branch checked out. If none does, it says yes.

The `main` checkout passes that check from any feature worktree, since no other worktree has `main` checked out. The store's `layout` function blocks the `main` checkout before it calls `owns_branch`, and has done so since 9ddb8cd. The guard's `committable` function calls `owns_branch` with no such step, so it reports the `main` checkout as a folder where commits are allowed.

Currently, no commit gets through, because the guard's `_shareable` function refuses the `main` checkout as a shared folder and the guard drops every commit folder outside a shared one. This means the guard is correct only because two unrelated rules happen to line up. A third caller of `owns_branch`, or a change to `_shareable`, would let an agent commit to `main` from a worktree.

`spec-storage-read-from-git` constrains this: whether a folder takes the store's commits is asked of git, never of the agent. The level-2 declaration for this branch records that the change draws no new boundary.

## Verified

- `_spec_store.py:92` `owns_branch` returns `branch not in taken` at line 129, where `taken` holds the branches of every worktree except the root's own (line 128).
- `_spec_store.py:196` `layout` returns `in_repo` when the root's top is `top_level(repo)` or `_main_worktree(repo)`, before it calls `owns_branch` at line 201.
- `_hook.py:123` `committable` keeps every shared root that passes `owns_branch`, with no check for the `main` checkout.
- `_guard.py:389` `_shareable` returns None when the root is the first worktree git lists, which is the `main` checkout.
- `_guard.py:670` keeps a commit folder only when it sits inside a shared root `_shareable` accepted.
- `_spec_store.py:213` `_main_worktree` runs git with `_quiet_env`, and `test_every_git_call_runs_without_a_prompt` holds every git call in the module to that.
- A scratch repository with the `main` checkout and one feature worktree beside it: `owns_branch(<main>, <feature>)` returned True, and `committable` returned `<main>` and `<main>/specs`. The hook refused all eight commits it was sent, with the spec folder set to `.`, `specs`, and both full paths.
- `owns_branch` has two callers, `committable` and `layout`.

## Assumed

- No spec store is ever the `main` checkout of the code repository. A project that keeps its specs as the `main` checkout of a repository of its own is unaffected, because `owns_branch` returns True for a different repository before it reaches this check. A layout where the code's `main` checkout is meant to take the store's commits would falsify this.

## Direct baseline

The guard's `committable` function drops a root whose top is `_spec_store._main_worktree(here)` before it calls `owns_branch`, the same step `layout` takes. `owns_branch` stays as it is, and each caller blocks the `main` checkout for itself.

## Decision

`owns_branch` returns False when the root is the `main` checkout of `here`'s project, using `_main_worktree`. The check sits after the different-repository test, so a spec repository of its own still passes. `committable` needs no change, and `layout` keeps its own check, since it has to return `in_repo` for the `main` checkout before it tests for a detached HEAD.

## Diagram

No boundary in force runs between these components, so neither graph has a divider.

```
baseline

  committable ──calls──► owns_branch
  committable ──calls──► _main_worktree
  layout      ──calls──► owns_branch
  layout      ──calls──► _main_worktree

decision

  committable ──calls──► owns_branch
  layout      ──calls──► owns_branch
  layout      ──calls──► _main_worktree
  owns_branch ──calls──► _main_worktree   (new)
```

Both graphs have four arrows. In the baseline, each caller of `owns_branch` also calls `_main_worktree`, so a new caller has to remember the second call. In the decision, `owns_branch` calls `_main_worktree` itself, and a new caller gets the rule with the one call it already makes. The change this absorbs is a third caller of `owns_branch`, which adds two arrows in the baseline and one in the decision.

## Considered

- The baseline: `committable` blocks the `main` checkout itself. We didn't choose this because it leaves the rule in each caller, which is how the guard came to miss it in the first place.
- A new shared helper, such as `is_code_checkout(top, repo)`, called by both `layout` and `committable`. This is sound, and it would also cover the caller's own checkout. We didn't choose it because it still needs every caller to call it, and the guard has no use for the own-checkout case, since a commit in the agent's own worktree never reaches `committable`.

## Consequences

The guard's commit check now agrees with the store about the `main` checkout without relying on `_shareable`. The guard's verdict does not change for any command.

`owns_branch` makes one more git call when the root and `here` share a repository. The guard pays it only for a command that runs git and was already headed for a refusal, and the store pays it once per `layout`.

`layout` checks the `main` checkout twice, once itself and once through `owns_branch`. Its own check stays because the `detached` test runs between the two.

## Verification

- `owns_branch(<main>, <feature>)` returns False, in a test that fails before the change.
- `committable` no longer returns the `main` checkout or a folder in it.
- The existing tests for a store beside the checkout, a spec repository nested in the `main` checkout, and a store reached from a feature folder still pass.
- The hook, run against a real `git commit` aimed at the `main` checkout, refuses it, and a commit inside this worktree is still allowed.

## Log

- 2026-10-22  proposed  — written for #603, where the guard's commit check disagreed with the store about the `main` checkout.
