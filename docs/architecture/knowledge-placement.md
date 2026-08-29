---
status: accepted
---

# Where a piece of knowledge belongs

## Context

The same fact was reaching an agent from several files at once — the guidance
file, a skill, and a spec — with no rule saying which was its home. Duplicated
knowledge has to be kept in sync by hand, and the copies that fall behind do not
announce themselves; they simply contradict the ones that did not.

Without a stated rule, placement is decided per fact, differently each time, and
the guidance file accumulates whatever had nowhere else to go.

## Decision

Placement is decided by scope first, then by what is constrained:

```
a fact about one file            → that file
a constraint on the system       → docs/architecture/
guidance for the worker          → AGENTS.md
```

The exception is ownership. A fact about one file belongs to that file **when
the project controls that file's contents**. When it does not — a vendored file,
generated output, a file owned by another tool — the fact belongs to the record
governing that file's class instead. `vendor-upstream-skills` names which skills
are vendored for exactly this reason.

## Owns truth

Each destination owns its own content and nothing is copied between them, so
there is no syncing to get wrong. A fact with two homes has no owner, which is
the condition this rule exists to remove.

## Considered

- The guidance file holds everything — it grows past what fits in context, and
  hard constraints sitting among conventions get read as suggestions.
- One document per topic with no stated rule — placement stays a judgment call
  per fact, which is the state being corrected.
- Copy each fact everywhere it is relevant — the copies drift, which is the
  original failure.

## Consequences

`AGENTS.md` and `docs/architecture/` do not overlap and do not need syncing. A
fact that seems to belong in both is usually phrased as guidance while
functioning as a constraint, and belongs in a record.

Only accepted records reach the agent, through `wfctl arch context`. Knowledge
moved into a record that is never accepted has been deleted, not relocated.

## Log

- 2026-08-28  accepted    — states FR-012's rule rather than only applying it
