---
status: proposed
---

# Promised evidence blocks on silence; ambient evidence proceeds

## Context

Three places in this repo read evidence and decide whether a step may proceed,
and each answers "what if the evidence is unavailable?" for itself.

`verification_block` blocks: a verify record marked `inconclusive` downgrades
`implement` and names the reason. `_arch.parse_record` blocks by another route —
a record it cannot read comes back with an empty status, and an empty status is
excluded from the projection, so an unreadable record is not in force.
`design_gate` proceeds, and argues for it: "a gate with no evidence against the
work does not refuse it", because guessing wrong there "blocks a pipeline with no
way to unblock it".

All three are locally correct. `design_gate`'s docstring reaches its answer by
explicitly declining `_arch`'s, with no visibility into the third. That is not a
disagreement anyone can settle by reading the code, because each argument is
sound about its own evidence and silent about the others.

#100 states the rule as two rows — repo-declared blocks, ambient proceeds — with
a separate reason for each. Two reasons do not extend. The epic's own goal names
four evidence sources, and the two it did not rule on are the accepted records
already implemented above and human approval, which nothing reads yet.

## Direct baseline

Leave the policy inside each gate and make them agree by hand: pick one
behaviour and apply it to both. Concretely, change `design_gate` to refuse when
`touched_on_this_branch` returns `None`, so both gates block on silence and the
divergence #100 documents is gone.

It is a small, real change and it fixes the reported symptom. What it does not
produce is a reason. `_arch` would still hold a third answer arrived at
independently; human approval would still have none; and the next gate is
written by someone reading two gates that agree and no statement of why. It also
loses the case `design_gate` was written for — a repository whose trunk cannot be
resolved would block at the design step with no action available to the user that
produces the missing evidence.

## Decision

A gate reads evidence and returns one of `satisfied`, `unsatisfied`,
`inconclusive`. It does not resolve `inconclusive`.

Resolution is a property of the evidence, keyed on whether anyone undertook to
produce it. Evidence that was promised — repo-declared commands, accepted
records, human approval — blocks when it is unavailable. Ambient evidence — git,
the filesystem — proceeds.

## Owns truth

The evidence source owns "what does it mean that this evidence is unavailable?".

A gate cannot own it. A gate sees one transition and one source, so its answer is
correct locally and unreachable from anywhere else — which is how three gates
came to hold two policies without any of them being wrong. The question is not
about the transition being gated at all: it asks whether anything undertook to
produce the evidence, which is a fact about the evidence's origin and is the same
answer at every gate that reads that source. Asked at the gate, it is re-derived
per gate and drifts; asked at the source, it is answered once.

## Considered

- Make the gates agree by hand, per **Direct baseline** — fixes the two gates
  that exist and leaves the rule unwritten, so the third policy already in the
  tree stays unexplained and the fourth source has no answer to consult.
- Block on silence everywhere, as the conservative default — sound, and already
  what two of the three do. It loses on the case `design_gate` exists for: a git
  fact that cannot be computed is not a missing answer the user can supply, so
  refusing leaves a pipeline stopped with no action that unblocks it.
- A per-step flag saying whether that step blocks on inconclusive evidence —
  #100 rejects a second Boolean on `_STEPS` and this is that Boolean. It also
  attaches the answer to the step, which permits two steps reading one source to
  resolve its silence differently; the source has not changed between them.
- Let the executor grade inconclusive evidence and proceed when it judges the
  risk low — refused by `escalate-never-waive`, which #280 owns: an executor may
  route a decision up, never down.

## Consequences

The verdict is three-valued, so a gate returning `bool` cannot express it. The
design gate's signature is the one that has to change, because `bool` has already
collapsed "no evidence against the work" into "evidence says proceed" at the
point the rule would be applied.

The evidence source has to be nameable at the point it is read. That is the whole
structure this record forces, and it is the smallest thing that can carry the
rule: something at each read site saying which class the source belongs to.

**Two gates call the rule, not one.** A rule wired into a single gate is applied
in exactly the place where applying it changes nothing, and the record would be
claiming a generality the code does not have. `design_block` and
`verification_block` both hand their verdict to `blocks`, which is what makes a
change to the rule a change to both.

`_arch.parse_record` is the exception, and stays one. It does not judge a
transition — it reads a set of records and reports which are in force, and a
caller asking "is this decision binding?" gets the same answer under any policy
this rule could state. Its conservative default is consistent with the rule
rather than an application of it, and routing it through `blocks` would make a
gate out of a parser.

## Log

- 2026-09-07  proposed    — #100's level-2 pass. Three policies over four
  evidence sources, and the epic's own table ruled on two of them.
