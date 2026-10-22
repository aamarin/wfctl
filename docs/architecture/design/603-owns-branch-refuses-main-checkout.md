---
status: proposed
---

# The `owns_branch` function refuses the `main` checkout, so the guard and the store share one rule

## Context

The worktree guard and the `wfctl store specs` command both ask the `owns_branch` function whether a commit in a folder lands on a branch of its own. The function checks whether any other worktree has the folder's branch checked out. If none does, it says yes.

The `main` checkout passes that check from any feature worktree, since no other worktree has `main` checked out. The store's `layout` function blocks the `main` checkout before it calls `owns_branch`, and has done so since 9ddb8cd. The guard's `committable` function calls `owns_branch` with no such step, so it reports the `main` checkout as a folder where commits are allowed.

Currently, a commit straight into the `main` checkout is still refused, because the guard's `_shareable` function refuses the `main` checkout as a shared folder. A commit into a folder inside it is not. The guard asks `committable` about the spec root only, and with the spec root at the `main` checkout, `committable` vouches for every folder in it. The guard then keeps a vouched folder when it sits under any shared root `_shareable` accepted, and a state folder inside the `main` checkout is one. This means a folder vouched for through the spec root is exempted through the state root, and an agent in a feature worktree can commit to `main` through it.

`spec-storage-read-from-git` constrains this: whether a folder takes the store's commits is asked of git, never of the agent. The level-2 declaration for this branch records that the change draws no new boundary.

## Verified

Line numbers are as of `origin/main` at 31d9f39.

- `_spec_store.py:92` `owns_branch` returns `branch not in taken` at line 129, where `taken` holds the branches of every worktree except the root's own (line 128).
- `_spec_store.py:196` `layout` returns `in_repo` when the root's top is `top_level(repo)` or `_main_worktree(repo)`, before it calls `owns_branch` at line 201.
- `_hook.py:123` `committable` keeps every shared root that passes `owns_branch`, with no check for the `main` checkout, and the hook passes it the spec root alone.
- `_guard.py:389` `_shareable` returns None when the root is the first worktree git lists, which is the `main` checkout.
- `_guard.py:670` keeps a commit folder when it sits inside any shared root `_shareable` accepted, not only the root `committable` vouched for it under.
- `_spec_store.py:213` `_main_worktree` runs git with `_quiet_env`, and `test_every_git_call_runs_without_a_prompt` holds every git call in the module to that.
- A scratch repository with the `main` checkout and one feature worktree beside it: `owns_branch(<main>, <feature>)` returned True, and `committable` returned `<main>` and `<main>/specs`. With only a spec folder set, the hook refused all eight commits it was sent.
- The same layout with `WFCTL_SPEC_DIR=<main>` and `WFCTL_STATE_DIR=<main>/.state`: on `origin/main` the hook allowed `git -C <main>/.state commit -m x` from the feature worktree, and on this branch it refuses it. `git -C <main> commit -m x` is refused on both.
- `owns_branch` has two callers, `committable` and `layout`.
- When `git worktree list` fails after both `rev-parse` calls succeed, `taken` stays empty and `owns_branch` returned True, against its docstring's "False whenever git cannot answer".

## Assumed

- No spec store is ever the `main` checkout of the code repository. A project that keeps its specs as the `main` checkout of a repository of its own is unaffected, because `owns_branch` returns True for a different repository before it reaches this check. A layout where the code's `main` checkout is meant to take the store's commits would falsify this.
- The `main` checkout is the first worktree git lists. In a bare repository that entry is the bare directory, and the worktree holding the code's default branch is an ordinary linked worktree, so this check does not cover it, and neither does `_shareable`. That gap predates this change. A project that uses a bare layout and sets its spec root to that worktree would still let an agent commit to its default branch.

## Direct baseline

This is the smallest fix with no new abstraction, not the code before the fix. The guard's `committable` function drops a root whose top is `_spec_store._main_worktree(here)` before it calls `owns_branch`, the same step `layout` takes. `owns_branch` stays as it is, and each caller blocks the `main` checkout for itself.

## Decision

`owns_branch` returns False when the root is the `main` checkout of `here`'s project, using `_main_worktree`, and also when `_main_worktree` cannot answer. The check sits after the different-repository test, so a spec repository of its own still passes. `committable` needs no change, and `layout` keeps its own check, since it has to return `in_repo` for the `main` checkout before it tests for a detached HEAD.

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
- A new shared helper, such as `is_code_checkout(top, repo)`, called by both `layout` and `committable`. This is sound, and it would also cover the caller's own checkout. We didn't choose it because it still needs every caller to call it, and the guard has no use for the own-checkout case, since a commit in the agent's own worktree never needs `committable`'s answer.

## Consequences

The guard's commit check now agrees with the store about the `main` checkout. The guard refuses one commit it used to allow, into a folder inside the `main` checkout that another shared root covers, and every other verdict is unchanged.

`owns_branch` reads `git worktree list` twice, once through `_main_worktree` and once for `taken`. Reading it once would save a subprocess, and we didn't do it because it would put a second parser of the listing's first entry beside `_main_worktree`.

`owns_branch` makes one more git call when the root and `here` share a repository. The guard pays it only for a command that runs git and was already headed for a refusal, and the store pays it once per `layout`.

`layout` checks the `main` checkout twice, once itself and once through `owns_branch`. Its own check stays because the `detached` test runs between the two.

## Verification

- `owns_branch(<main>, <feature>)` returns False, and `owns_branch` returns False when the worktree listing fails, in tests that fail before the change.
- `committable` no longer returns the `main` checkout or a folder in it.
- The hook refuses `git -C <main>/.state commit` from a feature worktree with the spec root at the `main` checkout and the state folder inside it, and still allows a commit in the feature worktree, in a test that fails before the change.
- The existing tests for a store beside the checkout, a spec repository nested in the `main` checkout, and a store reached from a feature folder still pass.
- Run by hand in this repository, the hook refuses a real `git commit` aimed at the `main` checkout and allows one inside this worktree.

## Log

- 2026-10-22  proposed  — written for #603, where the guard's commit check disagreed with the store about the `main` checkout.
- 2026-10-22  proposed  — revised before review: the first draft said no commit got through, and a commit into a state folder inside the `main` checkout did.
