---
status: proposed
---

# wfctl pins the sections a spec and a plan must carry, and checks them against the template it ships

## Context

`specify` and `plan` are the two steps `speckit-orchestrate` may pass without
pausing while their predicates prove only that a file exists and holds more than
zero bytes. A `spec.md` whose entire content is the character `x` reads
`specify: done` (#309, found by the audit in #300).

The evidence that would raise them is the artifact's shape: whether it carries
the sections its template defines. That is the whole of what a machine can say
about a prose document, and it is enough to reject the constructed case.

Those section names come from `github/spec-kit`, which wfctl vendors under
`vendor-upstream-skills` rather than owns. Naming them in `_infer_steps` couples
inference to a document upstream can rename, and the coupling is why the check
was never added as a drive-by. What follows has to say what happens on the pull
that renames a heading.

There is a second reader of that question. Inference runs against a spec
directory and reads nothing else — not the repository's installed skills, not
`.specify/`. A predicate that consults the template at read time gives it a
second input, and that input is legitimately absent in a repo that has never run
`install-skills`, and legitimately stale in one where the installed tree and the
running wfctl come from different trees (#291).

## Direct baseline

Leave both predicates reading file size and close #309 as accepted behaviour:
the flag says the step may proceed unattended, the agent that wrote the file is
trusted, and a spec too thin to be a spec is a failure the human notices at
review.

Rejected because the flag's whole claim is that no human is in that loop. The
constructed case is not adversarial — it is what a truncated write, a failed
generation, or a `touch` produces, and today all three read `done` in green.

## Decision

The list of sections a `spec.md` and a `plan.md` must carry is wfctl's, written
as constants beside the predicates that read them. A test in wfctl's own suite
compares those constants against the templates the same wheel ships, and fails
when they diverge.

Inference reads the spec directory and nothing else. It never opens a template.

## Owns truth

wfctl owns "must a spec carry these sections for the step to pass?". The
question is about wfctl's own gate, not about the document's genre, and the
answer has to hold in a repository that has installed no templates at all.

Upstream cannot answer it: a template states what a document should contain, and
has no claim on what a *pipeline* treats as sufficient evidence. The two agree
today and are not the same question — upstream may add a section to guide an
author without intending to block a step, and wfctl may keep requiring one
upstream drops.

The installed `.specify/` tree cannot answer it either, for a plainer reason: it
need not exist. `wfctl status` works from a spec directory alone, so a predicate
depending on the tree has to decide what its absence means, and both answers are
wrong — passing restores the defect this record exists to close, and failing
blocks every step in a repository whose only fault is not having run
`install-skills`.

## Considered

- Read the required names from the shipped template at inference time — puts the
  names where they are authored, and follows a rename for free. Loses on the
  absent-and-stale input above: the failure it introduces is worse and quieter
  than the one it removes.
- Read them from the project's installed `.specify/templates/` — closer still to
  what the agent actually wrote from, and it inherits every fault of the option
  above plus staleness against the running wfctl.
- Require that the document carry *some* sections, without naming which — no
  coupling at all, and it rejects the constructed case. Sound, and it loses on
  evidence: 22 of the 25 specs on disk carry all four mandatory headings, and the
  three that do not are the oldest directories there, ported in from before this
  pipeline existed rather than evidence of ongoing drift.
- Extend `wfctl.json`'s `verify` to `specify` and `plan` — the one predicate in
  the pipeline not authored by its claimant is `implement`, which reads a
  verification record. "Is this spec adequate" has no executable answer, so the
  entry would be a command invented to have something to run, and it would
  render in `status` exactly as `implement`'s does: a strong badge over weak
  evidence.
- A per-step sentinel file, as `checklists/implement-complete.md` already
  establishes — the agent that wrote the thin `spec.md` writes the sentinel, so
  it proves what it is asked to prove and nothing else.
- Flip either step to `review_required` — out of scope in #309 and against the
  direction of #100: it trades an unchecked pass for a human pause on every run.

## Consequences

A required list may be stricter than the template; it may not contradict it.
`plan-template.md` carries `## Complexity Tracking` and tells the author to fill
it *only* where the Constitution Check found violations, so a plan with none is
instructed to delete it. 23 of the 24 plans on disk keep it — enough that
requiring it would have passed the corpus and still left an author who followed
their own template unable to clear the step. It is therefore not required, and
the four that are carry no such instruction. This is the rule the spec side never
had to state, because that template declares its mandatory sections outright.

A section rename upstream fails wfctl's build rather than changing a verdict in
the field. Someone reconciles the constants with the template in the same change
that pulls it, which is the maintenance obligation this record accepts by name.

Three spec directories written before the pipeline existed
(`24-read-artifacts-from-specs`, `configurable-issue-key`,
`install-config-workmux`) do not carry the required sections and would read
`in_progress` if inference ran against them. All three are closed work on closed
branches. They are left as they are; editing them would be rewriting finished
history to satisfy a checker.

`vendor-upstream-skills` is not superseded. Its subject is the *file* — who owns
a derived file's contents, and that no local edit is made to it. This record
touches no template. What it adds is that a fact *about* an upstream document
may be pinned in wfctl's code, provided a check holds the pin against the
document.

## Log

- 2026-09-09  proposed    — the level-2 gate for #309
