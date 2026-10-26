---
status: proposed
---

# An absent artifact is claimed by a person, never inferred

## Context

A sub-step reports `done` when its artifact exists. When the artifact is
missing, wfctl can't infer why, because three different causes leave the same
empty folder:

1. The pass ran and had nothing to write.
2. The pass never ran.
3. The pass doesn't apply to this branch.

`python-pattern-selection`, one of wfctl's own skills, shows the first two. The
skill writes a file only when the implementation departs from one of its
constraints, for example when it builds a Strategy hierarchy anyway and has to
give a reason. If the implementation follows the skill's advice, there's
nothing to write. So a branch that ran the pass and followed it leaves the same
empty folder as a branch that never ran the pass. If wfctl reads the empty
folder as `done`, the row is worthless, because a branch that never ran the
pass also reads `done`. If wfctl reads it as `pending`, the branch is stuck,
because no file is ever coming.

The `ui-design` pass in pfms shows the third. A backend-only branch changes no
screens, so it has no wireframe and owes none. The pipeline still has to move
past the row.

The difference matters for the reason given in #307: a pass that found
something and a pass that never ran shouldn't look the same in a PR. The
missing file carries no evidence of which one happened, and nothing else wfctl
can read supplies it.

## Direct baseline

The simplest option is to reuse the `skipped` state the pipeline already
infers. Today `brainstorm` returns `skipped` when `spec.md` exists, which means
a later step ran without it (`_evidence.py`). Applying the same rule to a
sub-step costs nothing to write and needs no new command.

However, it marks the wrong branches. Every backend feature would read
`skipped`, and so would every UI feature whose author skipped the gate. Those
are the two cases this decision has to separate, and the rule gives both the
same state because it can't see the difference. A later step running tells
wfctl that the pipeline moved on, not why the artifact is missing.

## Decision

A sub-step whose artifact is missing stays `pending` until a person says
otherwise. The person says so with a command, which writes a sentence into the
branch's spec folder:

```
wfctl step none ui-design --reason "backend-only; no screens change"
```

The sub-step then reads `skipped`, with the sentence as its annotation. The
file goes in the branch's spec folder, one file per pass, and the PR body
carries the same sentence to the reviewer
(`design-exceptions-live-with-specs.md`). The command applies the same guards
as `arch none`: it refuses an empty reason and a `<why>` placeholder. Each pass
gets its own file because a branch can make as many claims as it has passes,
and with one shared file the second claim would overwrite the first.

"Ran and produced nothing" and "doesn't apply here" are one state, not two. In
both cases the pipeline moves on, and the reviewer reads a claim they can
disagree with. The two reasons are already easy to tell apart in English, such
as "followed callable-first; no departure" and "backend-only; no screens
change". A flag separating them would add a state that nothing acts on.

`wfctl arch none` keeps its own command, path, and text. The two commands are
siblings, not one general command. `arch none` overwrites a whole file holding
a single boundary claim, so a branch that claimed away several passes through
it would lose all but the last. Adding an optional pass argument to `arch none`
would also mix the boundary question's refusals and path with those of a pass.

## Owns truth

A person decides whether a pass ran and produced nothing or never ran at all,
and records that decision as a sentence in the branch's spec folder. The PR
body repeats the sentence for the reviewer.

wfctl can't compute it. Neither outcome leaves an artifact, so nothing on disk
differs. The difference is the person's intent, and intent isn't a file. The
branch's diff can't supply it either. A sub-step between `brainstorm` and
`specify` is reached before any code is written, so the diff that would carry
the evidence doesn't exist yet when the question comes up.

wfctl doesn't verify the claim, for the reason `arch_none_cmd` already records.
Whether a pass applies is a judgment with no objective test, unlike completion,
which either exits zero or doesn't. wfctl checks that the claim was made and
that it's readable, and `wfctl check-body` checks that the PR body carries it
to the reviewer.

## Considered

- The inferred `skipped` above. We didn't choose it because it marks backend
  branches and abandoned gates the same way, which is the problem this decision
  fixes.
- Path globs in `wfctl.json` that decide applicability from the changed files.
  We didn't choose it because the diff doesn't exist yet when the routing
  decision is made. #620 also shows a UI-driven decision landing in
  `packages/types`, where a `client/**` rule would have called it backend-only.
- A declaration written into `design.md`, which #339 proposed. We didn't choose
  it because `specs/` is gitignored and resolves outside the working tree, so
  the claim reached no reviewer. #635 later moved the claims into the spec
  folder too, with the PR body carrying each one to the reviewer, so that
  reason no longer holds on its own. A declaration in `design.md` would still
  tie a repository's own pass to the content of a built-in step's output, as
  #339 noted.
- A fourth state separating "ran, nothing to say" from "doesn't apply". We
  didn't choose it because nothing acts on the difference, and the reason
  sentence already carries it for the one reader who needs it.
- A per-sub-step `optional: true` in `wfctl.json`, so the repository declares
  once that a pass may be missing. We didn't choose it because it declares that
  for every branch at once, which is the inference problem again with more
  setup. The question is per branch, and so is the answer.

## Consequences

`wfctl step none <name>` is a second command for writing claims, beside
`wfctl arch none`, not a general version of it. Each claim is its own file in
the spec folder, so two claims on one branch never compete for one path, and
repeating a claim on the same pass replaces only that claim.

A sub-step can reach the same four states a step can:

1. `done` when its predicate is satisfied.
2. `in_progress` when the parent step is current and this sub-step is the
   outstanding one.
3. `pending` when the parent hasn't been reached, or an earlier sub-step under
   it is outstanding.
4. `skipped` when a claim exists for it on this branch, or the parent step is
   `skipped`.

So `skipped` has two sources, and the `claimed` field tells them apart. It's
set when a person declared the sub-step away, and null when the sub-step
inherited the state from a parent the pipeline walked past. A parent becomes
`skipped` only when the pipeline walks past it: `brainstorm` with a `spec.md`
and no `design.md`, `clarify` with a `plan.md` already written, `implement`
over a completion record with no open task, and `decompose` with no
`delivery.md`. So an inherited `skipped` means no claim was ever owed, and the
row needs none.

As a result, a sub-step skipped under a parent that ran always carries a
sentence. That's the property the earlier single-source wording was aiming for,
and it still holds now that the `claimed` field, rather than the state name,
carries the distinction.

`python-pattern-selection` under `implement` will read `skipped` on most wfctl
branches, because producing no artifact is its normal outcome. The row is still
worth keeping. The sentence tells it apart from a branch where nobody ran the
skill, and the default view hides the row once it's settled.

## Log

- 2026-09-16  proposed    — #339's level-2 pass; absence is the state a
  sub-step spends most of its time in, and the only one wfctl cannot read
- 2026-09-17  revised     — #408: the storage path, the verb's relationship to
  `arch none`, and the state count were all written before the spec settled
  them. `skipped` has two producers and `claimed` separates them; a fifth state
  was rejected on this record's own ground that nothing branches on it
- 2026-10-25  revised     — #635: claims move out of the architecture folder
  into the branch's spec folder, and the PR body carries them to the reviewer
  (`design-exceptions-live-with-specs.md`)
- 2026-10-26  revised     — #635: rewritten in plain language with every fact
  kept. The `design.md` alternative now says its original reason no longer
  holds once claims live in the spec folder
- 2026-10-26  revised     — #635: the Decision and Owns truth sections no
  longer say the claim is committed to the branch. The PR body carries it
  to the reviewer, and `check-body` checks that it does
