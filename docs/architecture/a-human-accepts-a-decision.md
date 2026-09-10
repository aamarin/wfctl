---
status: proposed
---

# A human accepts a decision, and wfctl records the citation

## Context

Twenty-four records sit under this repo's arch root and ten are `accepted`.
`wfctl arch context` projects those ten and prints `14 records not shown (14
proposed)`. Two of the fourteen describe rules the code already enforces —
`promised-evidence-blocks-on-silence` is what `_predicates.blocks` implements,
and `the-scan-is-attested-where-the-reviewer-reads` was written by #307 — so an
agent reading the projection to learn what binds this repo is shown neither.

Nothing moves a record from `proposed` to `accepted`. `_arch.supersede` is the
module's only status mutation and it reaches no command; `wfctl arch` exposes
`context`, `none` and `check`, and none of them writes a status. The fourteen are
not a backlog of forgotten steps. There was no step.

The ten that are accepted got there by hand, and their `Log` lines record two
different kinds of evidence for the same transition:

```
wfctl-runs-the-verification   accepted — #96 shipped it; the code enforced a
                                         rule the contract still called open
required-sections-are-wfctls  accepted — agreed by the maintainer on #318
```

Both are locally reasonable and they do not extend. The first promotes on the
implementation existing, the second on a person agreeing. Nothing says which is
the rule, so the next record is promoted by whichever argument its author reaches
for — which is how three gates in `_predicates` came to hold two policies without
any of them being wrong (`promised-evidence-blocks-on-silence`).

The transition also already has a consumer waiting. `_predicates.Source` names
four evidence classes and `accepted-record` is one of them, in `_PROMISED`, so a
gate reading it blocks when it is silent. Nothing produces it. #299 is the gate
that would, and it is marked blocked on precisely this.

## Direct baseline

Keep promoting by hand: open the record, change one frontmatter key, append a
`Log` line, commit. That is exactly what the two promotions above did, and both
of them wrote a citation into the `Log` without being asked to.

It draws no new structure and it is not obviously wrong. What it does not produce
is a *rule*. The two hand-promotions cite two different kinds of evidence, and a
third author reading them finds no answer to which one binds — so the divergence
propagates rather than being settled. It also leaves the citation optional: it is
prose in a file, and a promotion that omits it is indistinguishable from one that
had nothing to cite. `a-rule-is-expressed-as-a-check` is accepted and says a
shipped rule is expressed as a check rather than as prose someone has to
remember; this is that rule's own subject matter left on the prose side.

## Decision

Acceptance is a human's act. wfctl records it and never infers it.

`wfctl arch accept <slug> --agreed "<where the human agreed>"` changes `status`
to `accepted` and appends one dated `Log` line carrying the citation. The
citation is required, and a placeholder is refused the way `arch none --reason`
refuses one. Nothing else in the file is touched.

wfctl does not promote a record because its code shipped, because its branch
merged, or because a pipeline step that consumes it passed.

## Owns truth

A human owns *"is this decision binding?"*. wfctl owns *"where was that said, and
when?"*.

wfctl cannot compute the first. Every signal available to it is evidence that the
decision was **implemented**, not that it was **agreed** — a merged branch, a
green pipeline step, a shipped command. A record promoted on the strength of its
own implementation can never disagree with the implementation, and a record that
cannot disagree with the code is documentation of the code, which the code
already is. The one existing promotion of that kind says so in its own commit
message: *"It makes the contract match code that has been enforcing it since
24beb3e."* That is the correct description of what happened and the reason it is
not the rule.

The human cannot own the second half. A citation kept in a person's memory, in a
review thread, or in a commit message is not on the record a later reader opens,
and the transition it justifies is invisible from `arch context` — which is the
present state, and the reason `arch context` can say fourteen and not say why.

**This is tamper-evident, not unforgeable**, and the honest ceiling for a local
CLI — the same ceiling `wfctl-runs-the-verification` names for itself. Nothing
stops an agent from running `arch accept` with an invented citation. What the
required citation buys is that a promotion with nothing behind it has to *say
something false in the file a reviewer reads*, rather than being a one-character
diff nobody can distinguish from a correct one.

## Considered

- **Merge is the promotion** — a record that reached the trunk was reviewed by
  whoever approved the change. Cheapest, and it would make all fourteen accepted
  today. It is falsified by this repo's own history: `required-sections-are-wfctls`
  merged `proposed` and was accepted three commits later, after a human agreed on
  #318. Under this rule that separate agreement was ceremony, and the commit that
  recorded it would not exist. It also collides with where records are written —
  `/speckit.brainstorm` commits them during the design step, before the reviewer
  has read anything, so the merge that promotes the record is the same merge that
  first shows it to anyone.
- **A gate at a pipeline step** — promotion happens when a step that consumes the
  decision passes. The most #100-shaped answer, and it ties the transition to
  evidence rather than to memory. It loses on what the evidence proves: a step
  passing shows the decision was built, which is the substitution **Owns truth**
  rules out. It also scopes a per-record fact to a per-branch run — a record can
  be accepted a week after the branch that wrote it is gone
  (`wfctl-runs-the-verification` was, by its own commit message) — and it would
  couple `_arch` to `_pipeline`, which are independent today.
- **A repo-configurable policy**, so a project picks merge, command or gate —
  defensible, and it is the answer if two projects genuinely need different rules.
  No second project has asked, and a configurable authority question means the
  first reader of a strange repo cannot tell who accepted a record without
  reading its config. Reversible: a policy key can be added over this rule
  later, and cannot be removed from under one.
- **Promote on a maintainer's approving review of the change carrying the
  record** — a real human act, already recorded, and it needs no new command. It
  is rejected because the reviewer is approving a change, not ratifying a
  contract, and a review cannot say which of the several records in a diff it
  agreed with. It would also give exactly one shape of citation, and
  `wfctl-runs-the-verification` was accepted on a shipped release rather than on
  any review.
- **Let a run promote a record when it assesses the decision as low risk** —
  refused by `escalate-never-waive` (#100 scope item 6, #280): a risk level may
  select analysis depth and nothing else, and an executor may route a decision up,
  never down.

## Consequences

`accepted-record` becomes a producible evidence class. `_predicates.Source`
already names it and `_PROMISED` already blocks on its silence, so #299's
*architecture accepted* fact has a source once this ships. Nothing in this record
implements that gate.

The fourteen stranded records are not promoted by this record's existence. Each
now needs a human to agree to it and a citation for where — which is the work
this rule creates, and it is deliberately not done in the change that states the
rule: a diff that flips fourteen statuses buries the one decision a reviewer is
meant to argue with.

An agent working unattended cannot finish the transition. Under `auto_approve`
the design gates move to the PR, and `/speckit.brainstorm` already states that a
record lands `proposed` and that an agent never writes the accepted status. This
record is why: the mode moves *who approves*, and acceptance is the approval, so
moving it is the one thing the mode is not permitted to do.

## Log

- 2026-09-09  proposed    — #321's level-2 gate. Twenty-four records, ten
  accepted, no rule for the transition and two incompatible precedents for it.
