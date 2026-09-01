# Experiment: does a whole-reply cap fire where the per-piece rules do not?

**Run**: 2026-08-31, during implementation of #102.
**Purpose**: settle whether rule 6 ships, and supply the before/after for the PR body.

## Why this run exists

The five rules implemented for #102 all govern **one piece** of a reply — is the
answer first, is it in plain words, is the subject established, is anything
volunteered, is the right form drawn. A reply can pass all five piece by piece
and still arrive as a wall, because nothing counts the pieces.

Observed live, zero turns after the rules were written. Three replies from three
different sessions, all reporting or proposing, all with the same trailing shape:

| Session | The counted lead-in |
| --- | --- |
| #102 implementation report | *"Three decisions I made under budget pressure"* · *"Two things the plan didn't anticipate"* |
| #85 merge install mode | *"Two questions left that are genuinely open, and both are small"* |
| #562 transaction balance | *"### Two things this improves here"* |

Each has a drawing. In each, the drawing did not replace the prose — the prose
repeats it and adds everything else. The register rule (rule 5) names *"two
things worth naming"* as its tell, and all three reproduce that tell verbatim in
a different wording.

## The candidate rule

```
## 6. The whole reply, not the pieces

Rules 1-5 each govern one piece. A reply can pass every one of them piece by
piece and still arrive as a wall, because nothing has counted the pieces.

**The answer, plus at most one supporting block. Then stop.**

One drawing, or one table, or one short list — not one of each, and not three of
one. Everything past that is a follow-up, and the reader will ask if they want
it.

The tell is a counted lead-in: "three decisions", "two things worth naming",
"two questions left", "two things this improves". The count is announcing a list
nobody asked for, and it is the most reliable signal that a reply stopped
answering and started reporting.
```

## Design

Two arms, three runs. Agents received the skill by path and were told not to
read the installed one, so rule text is the only variable — the same protocol as
the original #102 experiment.

| Arm | Skill | Task |
| --- | --- | --- |
| A | as implemented, 456 lines, rules 1-5 | report completed work |
| B | + rule 6, 473 lines | report completed work |
| B' | + rule 6 | propose an implementation for #88 |

**Why the report task.** All three observed failures are *reports*, not
proposals. The original experiment measured only #88, which is a proposal — so
the failure mode that prompted #102 was never the task being scored.

**Why B' exists.** A cap can fail by over-compressing. #88 is the one task with a
recorded baseline and a written rubric (`judgment-test.md`), so it is the check
that rule 6 does not cost an answer that genuinely needs its parts.

## Results

All three replies are preserved in `replies/`, along with the two skill files
and the task, so this is re-readable without the scratchpad.

| Arm | Prose words | Drawing | Counted lead-in | Answer on line 1 |
| --- | --- | --- | --- | --- |
| A — rules 1-5 | 209 | table, warranted | none | **no** — the question is the last line |
| B — rules 1-6, first wording | 151 | **lost** | none | yes |
| **B2 — rules 1-6, reworded** | **113** | **table, warranted** | none | yes |
| B' — rules 1-6, #88 | 217 | code only | none | yes |

### What rule 6 fixed

**A defers its answer.** The task states plainly that the user's next decision
is spawn-or-commit. A ends with *"Spawn the validation agent now, or commit what
exists first?"* — the answer is the closing line. B opens with *"Commit first,
then spawn"* and gives the reason in the same sentence.

That is the failure in the #85 screenshot and in the #102 implementation report:
everything true, ordered so the decision arrives last.

**A still bolds two counted sections** — *"One call you did not pre-approve"*,
*"Four validation tasks are still open"*. Not the worst form of the tell, but
the same reflex: material promoted to a section because it felt important, in a
reply the reader is reading to make one decision.

### What rule 6 broke

**Both B arms dropped a warranted drawing.**

B lost the three-file table that A produced correctly — three rows against two
columns, exactly the last row of the form-selection table.

B' never enumerated #88's four reachable states. That table is what
`judgment-test.md` J5 asks for, it is the shape the skill's own *Enumerate real
states* rule names, and the form-selection table says a property varying across
rows is a table. B' spent its one block on the code patch instead.

**Cause: "at most one supporting block" reads as one block total, and code
counts.** So rule 6 as written contradicts the Show section it sits above —
which was the exact mistake #102 was filed to fix, reproduced by the rule
meant to fix it.

### The fix, and its re-run

One clause. The cap counts **prose blocks**, not the drawing:

> A drawing the material calls for does not count against that — it is the
> answer's shape, and the selection table above decides whether it is warranted.
> The cap governs prose: one block, not one of each kind.

**B2 re-ran the same report task against the reworded rule and held both
properties.** Shortest of the four at 113 prose words, answer on line 1, table
restored.

It also picked a *better* table than A. A listed three files against their diff
stats; B2 drew a two-column **landed / open** partition — the first row of the
selection table, fired on the material's actual shape. That is #102's other
claim, and until this run it had only ever been observed in the arm that was
discarded for losing its drawing.

**One judgment left open.** B2 folds the unapproved ceiling change into a single
unbolded paragraph where A gave it a bolded section. Both disclose it; B2 is
easier to skim past. The material did not shrink, its prominence did. Whether
that is the cap working or the cap hiding something is not a call the rule's
author can make about their own rule — it belongs to the fresh-agent validation
pass (T030-T033).

### Incidental finding

B', grounding its proposal in the source rather than the issue text, found that
`_live_lines` (`wfctl/_workmux.py:133`) filters lines beginning with `#`. So
#88's own cheapest candidate — a marker comment — is invisible to the function
that would consume it. The issue does not record this. Worth a comment on #88
whatever happens to rule 6.

## Decision

**Shipped.** Rule 6 is in the skill, reworded to count prose blocks only
(T036); B2 confirms it (T037).

The evidence is thin and should be read as such: n=1 per arm, arms differing by
~17 lines of rule text, and one task. What it does show is that the cap changes
behaviour at all — A carries all five per-piece rules and still buries its
answer, so nothing in rules 1-5 was going to fix this.

Still unrun: the cap against a question that genuinely asks for depth. That is
SC-005's territory and T033 owns it. A rule that caps the whole reply is exactly
the kind of rule that could over-compress an answer the reader asked to be
long.
