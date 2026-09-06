---
status: proposed
---

# A branch is claimed by an artifact, never inherited from its ancestry

## Context

`resolve_spec_dir` answers "which feature does this branch belong to?" and had
three sources for the answer: the branch's own name or issue key, an epic's
`delivery.md` grouping map naming that key, and — when both fail — the spec dir
of the nearest git ancestor branch.

The third source exists for one convention: a child issue's worktree cut from
its parent epic's planning branch, where the epic carries `specs/<epic>/` and
the child carries nothing. #120 found the same leg handing a *foreign* feature's
finished pipeline to a branch with no work on it, and narrowed it — an ancestor
carrying a grouping map that does not name this key is skipped. An ancestor with
no map at all was still inherited, and #120's docstring left that shape open
rather than guessed at.

#263 is that shape reaching a user. A worktree cut with the wrong `--base`
reported three of another feature's steps as done, handed the agent
`/speckit.analyze` on a pipeline it had not entered, and — through
`wfctl feature-paths`, which shares this resolution — pointed a review panel at
another session's reports to write over.

The two cases are the same tree. The convention's own test and the bug's
reproduction differ in nothing an implementation can read:

```
  epic-planning convention              #263's reproduction
  330-epic-not-yet-decomposed  specs/   100-parent  specs/
    └─ 464-period-nav-pill     nothing    └─ 200-child  nothing
```

## Direct baseline

Keep the leg and narrow it further: require the ancestor's own issue key to
relate to this branch's, or walk only one level up, or match on more patterns.
Every such rule is computed from the same two facts — ancestry, and the
ancestor's directory name — and neither differs between the two trees above. A
narrowing that cannot separate them is a rule that keeps the bug and costs a
condition.

## Decision

Git ancestry is not an authority for feature membership. `resolve_spec_dir`
returns the feature that claims this branch — by its own name, its issue key, or
a `delivery.md` row — and unresolved otherwise. The ancestor leg and
`_ancestor_branches` are removed, and the epic-planning-branch convention is
retired with them: a child issue that belongs to an epic is claimed by the
epic's grouping map, which is what `speckit.decompose` writes.

## Owns truth

An artifact under the spec root owns "which feature claims this branch?" — the
directory named for its branch or key, or a `delivery.md` grouping map naming
its key.

Git cannot compute it. A branch's base records where a worktree was cut from,
which is provenance, not membership: `workmux add --base <epic>` and the
one-flag mistake `workmux add --base <whatever-was-checked-out>` write the same
ancestry, and no later read can tell which one happened. Membership is a
question somebody answers by writing it down; ancestry is a side effect of how
the worktree was created.

## Considered

- **Verify the ancestor's key against this branch's** (#263's third option) —
  computed from the ancestor's directory name, which is identical in both trees.
  It says two branches carry different keys, which was never in doubt, and
  nothing about whether they share a feature.
- **Record the spec dir at worktree creation** (#263's second option) —
  `pre_create` knows both the issue key and the base, so it could write the
  membership down at the one moment it is known. Sound, and it is what the
  epic-planning convention would need to survive. It loses on cost and on
  `session-state-is-re-derived`: it introduces durable state that must survive a
  branch rename, for a convention with no live user in this repo.
- **Keep the leg, document the hazard** — the failure is silent and says "you
  are further along than you are". A hazard nobody reads is not a mitigation,
  and `a-rule-is-expressed-as-a-check` says a rule visible in an artifact is
  expressed as a check rather than as prose.

## Consequences

A child worktree cut from an un-decomposed epic's planning branch now resolves
to unresolved rather than to the epic. That is the convention being retired, not
a regression left unnoticed: the epic claims its children by decomposing, and
until it has, no artifact says the child is one of them.

Unresolved is not a dead end. `feature-paths` turns it into
`<spec root>/<branch>`, so the child starts a spec dir of its own and the next
speckit step writes there — where before it wrote into the epic's. The epic
reclaims it whenever it decomposes, since the grouping map resolves ahead of
either.

Measured before deciding: no branch in this repo resolves through the ancestor
leg — 0 of 18 local branches — and 18 of 23 features on `specs-trunk` carry a
`delivery.md`, which is the claim that replaces it.

## Log

- 2026-09-06  proposed    — #263; the leg's convention and its bug are the same tree
