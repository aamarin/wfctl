---
status: accepted
---

# A rule wfctl ships is expressed as a check, or it is a comment

## Context

wfctl ships rules three ways — a skill body, a hook that fires before the work,
a line in `AGENTS.md`. All three deliver prose to a reader, and the delivery is
the whole of it: nothing afterwards looks at what was written.

Four rules were filed as four separate bugs, by sessions that each believed they
had found something new:

```
   the rule                            stated in            observed by
   ─────────────────────────────────   ──────────────────   ───────────
   how a reply is shaped        #177   SKILL.md + a hook    nobody
     └─ refiled a month later   #212   the same file        the same nobody
   "not for trivial changes"    #161   four skill bodies    nobody
   this repo's own patterns     #165   AGENTS.md            nobody
   a leading underscore is
     private                   (#170)  a naming convention  nobody
```

`the-underscore-is-the-module-contract` already argues this decision for the last
row, and its rejection of the marker-alone option generalises without edit:
*"nothing new can check it, so the fifth crossing arrives the way the first four
did."* Two things keep that argument from reaching the sessions that needed it.
It is `status: proposed`, and `arch context` projects accepted records only. And
its subject is `cli`'s private imports, so a session scanning titles for
something that binds a PR body has no reason to open it.

The gap is not that the argument is wrong or missing. It is scoped to one
instance and printed to nobody, which at the moment a rule is being written is
indistinguishable from absent.

## Direct baseline

Leave it where it is. Close #177 and #212 as duplicates of each other, keep the
claim in epic #221 where the instances are already collected, and let
`arch context` go on printing eight decisions.

Not hypothetical — this is what happened four times. An epic is read by someone
who has already gone looking for it, and the fracture is earlier than that: at
the moment a rule is written, by someone who does not yet know the rule will need
observing. #177 and #212 are the same issue filed a month apart by sessions with
equal access to the same prose.

## Decision

A rule wfctl ships is expressed as a check, or it is a comment — and which of
the two it is turns on one question, asked of the rule rather than of the
tooling: is a violation of it visible in an artifact the work already produces?
Where the answer is yes, shipping the rule as prose alone is the gap this record
names; where it is no, the rule stays prose delivered at the moment it binds, and
that is not a defect.

```
   is a violation visible in an artifact
   the work already produces?
     │
     ├─ yes ──►  the rule is expressed as a check over that artifact.
     │           Stating it correctly and delivering it reliably, with
     │           nothing observing what was written, is not a partial
     │           implementation of the rule — it is the rule's absence,
     │           documented.
     │
     └─ no ───►  the rule stays prose, delivered at the moment it binds.
                 Not a defect, and not a candidate for a check that
                 guesses.
```

*Already produces* is the load-bearing half. It excludes a check that needs an
artifact invented so that it can be checked, and it includes the reply, the PR
body, the diff and the tree — which is where every violation above was observed.

Three things this does not decide: which mechanism carries a check, what a check
does when it fires, and whether a rule is worth having at all. #215 used a `Stop`
hook and a CLI command; #161 and #165 will need neither. A record that names a
mechanism is a record about that mechanism.

## Owns truth

A run owns *"is this rule holding?"*.

The rule's own text cannot answer it. Prose states what should be true and
renders the same words whether the rule is being followed or was broken four
times last month — a statement carries no state, so reading one teaches a session
nothing about compliance. Nor can the reader answer it, for a sharper reason than
inattention: the reader is the party the rule constrains, so an account of having
followed it is a self-report. That is the unfalsifiability
`wfctl-runs-the-verification` already refused to accept for *"did the check
pass?"*, arriving one level up — over the rules themselves rather than over one
run of a suite.

Which is why the answer is a run and not better prose. A run produces its verdict
as a side effect of running. A rule produces one only if the constrained party
volunteers it.

## Considered

- **Accept `the-underscore-is-the-module-contract` and rely on it generalising.**
  Sound — its sentence carries the whole argument with no edit. It loses on reach
  rather than on reasoning: `arch context` prints a title and a decision, and a
  session looking for what binds a PR body reads a title about `cli` and a
  leading underscore and moves on. Accepting it would also settle a question this
  record has no evidence about — whether `cli`'s four private crossings resolve
  the way that record says. That is its own decision and stays open.
- **Amend that record rather than write this one.** Rejected: a repo-wide claim
  filed under a title about one module's imports is unfindable in the place
  records are read from, and `architecture-decisions` gives a decision a file
  rather than a paragraph appended to a neighbour.
- **State the claim without the boundary — every rule becomes a check.** Stronger
  and shorter. Rejected on the only rule that has evidence: most of
  `conversation-response-shape`'s pre-send questions turn on what the reply was
  *for*, which is recorded in no artifact the work produces. An absolute claim is
  waived the first time it meets one of those, and a waived record binds less than
  a bounded one, because the next reader has watched it not bind.
- **Judge the unobservable rules with a model.** Reaches the rules the artifact
  test excludes, and it is the option to revisit if the prose side is ever
  observed failing in practice. Not chosen: a judge returns a second opinion where
  the driver ranked first here is an observation — a verdict the reader can
  re-derive from the artifact themselves — and a judge asked whether a rule was
  followed re-opens the self-report problem one participant over.
- **Keep the claim in epic #221.** Where it lives today, and the right place for
  collecting instances. Rejected as the durable form only: an epic is read by
  someone who has already gone looking for it, and `arch context` runs at the
  start of every session in this repo — which is where all four re-derivations
  happened. Records are not carried to another repo by `install-skills`, which
  copies skills and commands; a consuming repo gets the projection mechanism and
  writes its own records into it.

## Consequences

A rule is sorted onto one side of the test as it is written, not when someone
audits it later. That is the working change. #161's "not for trivial changes" and
#165's per-repo patterns are each a mixed set — some of what they state is
visible in a diff or a tree, some is a judgment about intent — and each issue
argues that boundary from scratch today. They cite this instead, and what is left
open in each narrows to the sort.

A rule on the prose side is not a defect and does not go on a backlog. Read as a
work item for every uncheckable rule, this record produces exactly the sweep that
gets it waived.

`the-underscore-is-the-module-contract` is the worked example — this argument
applied to one instance, with its alternatives ranked. It is cited for its
reasoning, not as authority: it is `status: proposed`, and what is unsettled in
it is whether `cli`'s four crossings resolve as it says, which is not a question
about this claim. It stays as it is.

No count of checkable against uncheckable rules is written here, for the reason
that record gives for the same omission: the set moves, and a stale number in a
record reads as a fact.

## Log

- 2026-09-06  accepted    — #222, under epic #221: the argument existed, scoped
  to module boundaries and projected to nobody, and four issues re-derived it
