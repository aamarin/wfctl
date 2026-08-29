---
status: accepted
---

# Upstream skills are vendored and layered, never forked

## Context

Some skills wfctl ships come from outside the project. Editing one in place is
invisible in a way a normal edit is not: the file reads as the project's own,
the suite passes, and the next upstream pull reverts the change without a
conflict, because the edit was never expressed as a difference from anything.

The behaviour then regresses at an unrelated moment, and nothing in the diff
that caused it mentions the skill.

## Decision

Vendored skills are taken unmodified. To change how one behaves, add a skill
that layers over it rather than editing it — `conversation-response-shape` is
the worked example, layering ordering rules on top of `i-have-adhd`'s brevity
rules without touching the vendored file.

Vendored today:

| Skill | Identified by |
| --- | --- |
| `i-have-adhd` | `license:` in its frontmatter — the only skill carrying one |

That list lives in this record rather than in each vendored skill's own
frontmatter, which is where a fact about one file would normally go. A vendored
file's contents are not the project's to add to, and an upstream pull would drop
the annotation. See `knowledge-placement` for the rule this is the exception to.

## Owns truth

Upstream owns the vendored file's contents. The project owns the layer above it.

The project cannot own the file itself: it does not control the next version,
and a local edit to a file that gets replaced is a change with no durable home.

## Considered

- Fork and edit — the pull overwrites it, and the loss is silent because the
  fork was never recorded as one.
- Keep a patch and apply it on install — a patch either applies to a moved line
  silently wrong or fails loudly, and installation gains a merge step.
- Reimplement rather than vendor — loses upstream fixes, and the reimplementation
  drifts from the thing it was copied from.

## Consequences

Changing a vendored skill's behaviour costs a whole new skill file. That
friction is intended: it makes the change visible in the tree, and it survives
the next pull.

## Log

- 2026-08-28  accepted    — relocated from `AGENTS.md`
