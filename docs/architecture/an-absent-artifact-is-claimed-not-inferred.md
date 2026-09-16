---
status: proposed
---

# An absent artifact is claimed by a person, never inferred

## Context

A sub-step reads one artifact and reports `done` when it exists. The hard case is
when it does not, because absence has three causes and the disk shows the same
thing for all of them.

`python-pattern-selection` is the sharpest instance, and it is wfctl's own. The
skill writes a file only when the implementation *departs* from one of its
constraints — built the Strategy hierarchy after all, and owes a reason. Follow
its advice and there is nothing to write down. So a branch that ran the pass and
followed it, and a branch that never ran the pass, leave an identical empty
directory. Reading that as `done` makes the row worthless, because never running
it also reads `done`. Reading it as `pending` strands the branch, because no file
is ever coming.

pfms's `ui-design` has the third cause. A backend-only branch changes no screens,
so there is no wireframe and none is owed — but the pipeline still has to advance
past the row.

The distinction matters for the reason #307 already named: a pass that found
something and a pass that never ran must not be the same pull request. Absence
carries no evidence of which it was, and nothing wfctl can read will supply it.

## Direct baseline

Reuse the `skipped` the pipeline already infers. `brainstorm` returns `skipped`
today when `spec.md` exists, meaning "a later step ran without this one"
(`_predicates.py`). Applied to a sub-step, the same rule costs nothing to write
and needs no new command.

It marks the wrong branches. Every backend feature would read `skipped`, and so
would every UI feature whose author walked past the gate — the two cases the
distinction exists to separate, given the same glyph by a rule that cannot see
the difference. Inference of this shape is not a weaker answer to the question;
it is an answer to a different question, being read as this one.

## Decision

A sub-step whose artifact is absent is `pending` until a person says otherwise.
That claim is a command, and it writes a committed sentence into the change under
review:

```
wfctl step none ui-design --reason "backend-only; no screens change"
```

The sub-step then reads `skipped`, carrying the sentence as its annotation. The
file goes where `wfctl arch none` already writes — the declarations directory
under the arch root — and carries the same guards: an empty reason is refused, a
`<why>` placeholder is refused, and a write that landed somewhere no reviewer
will see it warns and exits non-zero.

"Ran and produced nothing" and "does not apply here" are one state, not two.
Both mean the pipeline advances and a reviewer reads a claim they can disagree
with, and "followed callable-first; no departure" and "backend-only; no screens
change" are already distinguishable as English. A flag separating them would add
a state nothing branches on.

`wfctl arch none` becomes the level-2 instance of this verb rather than a
mechanism of its own.

## Owns truth

A person owns "did this pass run and produce nothing, or never run at all?", and
owns it as a sentence committed to the branch.

wfctl cannot compute it. Both outcomes leave no artifact, so there is nothing on
disk that differs — the difference is intent, and intent is not a file. Nor can
the answer be derived from the branch's diff: a sub-step sitting between
`brainstorm` and `specify` is routed to before any code is written, so the diff
that would carry the evidence does not exist at the moment the question is asked.

The claim is not verified, deliberately, for the reason `arch_none_cmd` already
records: whether a pass applies is a judgment with no objective test, unlike
completion, which either exits zero or does not. What wfctl owns is that the
claim was made, that it is legible, and that it reached the reviewer.

## Considered

- The inferred `skipped` above — marks backend branches and abandoned gates
  alike, which is the conflation the feature exists to end.
- Path globs in `wfctl.json` deciding applicability from the changed files — the
  diff does not exist when the routing decision is made, and #620 shows a
  UI-driven decision landing in `packages/types`, where a `client/**` rule would
  have called it backend-only.
- A declaration written into `design.md`, which #339 proposed as the candidate —
  `specs/` is gitignored and resolves outside the working tree, so the claim
  reaches no reviewer. A claim nobody can disagree with is the silent omission
  wearing a command.
- A fourth state separating "ran, nothing to say" from "does not apply" —
  nothing branches on the difference, and the reason sentence already carries it
  for the only reader who cares.
- A per-sub-step `optional: true` in `wfctl.json`, so the repository declares
  once that a pass may be absent — declares it for every branch at once, which is
  the inference problem with a longer setup. The question is per branch and so is
  the answer.

## Consequences

`wfctl step none <name>` is a new verb, and it generalises `wfctl arch none`
rather than sitting beside it. The declarations file gains a line per declared
sub-step instead of holding a single claim.

A sub-step has three reachable states and no ambiguity in any of them: `done`
when the artifact exists, `pending` when it does not, `skipped` when someone
declared it. Unlike the top-level pipeline, `skipped` on a sub-step has exactly
one producer, so the glyph means one thing.

`python-pattern-selection` under `implement` will read `skipped` on most wfctl
branches, because producing no artifact is its normal outcome. The row still
earns its place: the sentence is what distinguishes it from a branch where nobody
ran the skill, and the default view hides the row once it is settled.

## Log

- 2026-09-16  proposed    — #339's level-2 pass; absence is the state a
  sub-step spends most of its time in, and the only one wfctl cannot read
