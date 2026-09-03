---
name: fanning-out-code-review
description: 'Review a change with a panel of independent reviewers instead of one: dispatch several fresh-context reviewers over the same diff, confirm every one of them actually reported, then reconcile and verify the findings yourself. Use when asked to review this, review the PR, review a diff, check something before merge, and after finishing an implementation. Layers over requesting-code-review (the trigger and the hand-off), code-review (the rubric) and receiving-code-review (verify before implementing); it owns none of those.'
# No `disable-model-invocation`, for #124's reason: the moment a panel is most
# worth running — a change about to be opened or merged — is a moment nobody
# types a command. `install-skills` names this skill among those it mirrors into
# `.claude/skills/`, so the model can reach it without one.
# `conversation-response-shape` is the precedent.
---

# Fanning out a code review

One reviewer gives you one reading of a diff, and no way to tell a real defect
from that reader's blind spot. A panel of reviewers that **cannot see each
other's findings** gives you a second signal for free: agreement between two of
them is evidence, and a finding only one of them raised is a hypothesis you now
have to test.

What the fan-out buys is *independent context*, not *coverage*. That distinction
decides the whole design — see "The axes are not the split" below.

**Announce at start:** "I'm using the fanning-out-code-review skill to run a
review panel over this change."

## What this skill does not own

| Skill | Owns |
| --- | --- |
| `.agents/skills/requesting-code-review/SKILL.md` | when to request a review, and the hand-off rules for dispatching one |
| `.agents/skills/code-review/SKILL.md` | the rubric: the passes, the severities, the report format |
| `.agents/skills/receiving-code-review/SKILL.md` | verifying feedback before implementing it |

Read them. Do not edit them, and do not restate them here. This skill adds the
three things none of them has: the fan-out, the check that every reviewer
actually reported, and the reconciliation.

### The axes are not the split

The obvious panel is one reviewer per axis — correctness, simplification,
over-engineering. Do not build that one. `code-review` already folds those into
a single pass on purpose ("*one* review instead of four overlapping ones") —
simplification and over-engineering are each one of its own passes. A panel by
axis contradicts a skill this project ships, and it gives each reviewer a
narrower brief than a single reviewer would have had.

**Every reviewer runs the whole `code-review` rubric.** Independence is the
variable. The rubric is not.

## Step 1 — Fix one target and one destination

Resolve the diff once, and give every reviewer the same one. A panel reviewing
slightly different targets produces disagreement that means nothing.

Reviews go in `$FEATURE_DIR/reviews/`, one file per reviewer — `r1.md`,
`r2.md`, `r3.md`. `wfctl feature-paths` prints that directory as a shell
assignment, so bind it rather than reading it off and retyping it:

```bash
eval "$(wfctl feature-paths)"    # binds FEATURE_DIR in *this* shell
```

Every later command that names `$FEATURE_DIR` re-binds it the same way. A shell
here does not outlive the command it ran, so a value bound in this step is gone
by the next one — which is why Step 3's check carries its own `eval` rather than
trusting this one. Outside a wfctl repo, replace that line with
`FEATURE_DIR=<some directory outside the worktree>`.

**One file per reviewer, never a shared one.** `code-review` Step 5 sends its
report to `REVIEW.md`; three reviewers following it unmodified write that same
path and the last one to finish is the only one you read. Overriding the
destination per reviewer is what makes the next step possible at all.

Three reviewers is the default. Two leaves a disagreement with no way to read
it; past three you are mostly buying the same reading again.

## Step 2 — Dispatch

Per `requesting-code-review`'s hand-off rules, each reviewer gets the diff, what
the change is supposed to do, and the project's rules — **never your session
history**, and never another reviewer's findings. A reviewer primed with the
first reviewer's report is not a second opinion.

Every dispatch instruction carries these three:

- **Follow the `code-review` skill.** Name the skill; do not paste a rubric.
- **Report only. Change nothing.** Reviewers here share a worktree with each
  other and with you. Three agents editing a tree a fourth is reading corrupts
  all four, and the corruption is not recoverable afterwards — you cannot tell
  whose half-applied edit produced the state you are looking at. Writing its own
  findings file is not an edit to the tree; touching anything under review is.
  The boundary is wider than the tree, though: anything the project reads back
  later as evidence is off limits too. Under wfctl that is `wfctl verify`, which
  writes one record per branch outside the worktree — a reviewer running it
  replaces the parent's proof of done with one taken mid-review.
- **Write findings to `$FEATURE_DIR/reviews/<id>.md`,** the id you assigned it.

Dispatch them in parallel — they are independent by construction.

A reviewer nobody dispatched still counts. Bot and human comments already on the
change are panel members you did not pay for; collect them in the same pass.

## Step 3 — Confirm every reviewer reported

**This is the step the skill exists for.** In a fan-out, a reviewer that returns
nothing is indistinguishable from a reviewer that found nothing, and an agent
will report the second. One real run produced the completion message *"this is
the completion notification for the review I already relayed above — same
finding, nothing new. No action needed"* for a review that had never arrived.
Asked again, that reviewer produced the only confirmed correctness defect in the
change.

So the roster is checked against the disk, not against what you remember
receiving:

```bash
eval "$(wfctl feature-paths)"
REVIEWS="$FEATURE_DIR/reviews"
for id in r1 r2 r3; do
  if [ -s "$REVIEWS/$id.md" ]; then echo "reported  $id"; else echo "MISSING   $id"; fi
done
```

The id list is **the roster you dispatched**, substituted like the path above —
not a glob over the directory. `for id in "$REVIEWS"/*.md` checks the reports
that exist, which is the one question this step is not asking: a reviewer that
never wrote a file leaves nothing for a glob to find, and the loop reports three
of three from a panel of four.

`MISSING` is a **failure, not a pass.** Ask that reviewer again for its findings
in the format `code-review` specifies. If a reviewer insists it already
reported, the report is the evidence and its recollection is not — ask again
anyway.

"No findings" is a valid result only when it says **which passes ran and what
was checked in each**. A bare "looks good" is a missing report wearing a verdict.

## Step 4 — Reconcile

Read all the reports together, then group:

- **Two or more reviewers, same defect** → evidence. Verify it anyway; verify it first.
- **One reviewer only** → a hypothesis, not noise. How often this happens is not
  worth predicting: one three-reviewer run produced three disjoint sets and zero
  overlap, with the most valuable finding coming from one reviewer alone; the
  next produced unanimous agreement on a single defect. Both are normal.
  A lone finding is verified, not discounted.
- **Reviewers contradicting each other** → they read the same code and disagree,
  which means the code supports two readings. That is a finding in itself.

## Step 5 — Verify each finding yourself

Not delegable, and not fanned out. Holding findings from several reviewers
against one codebase is exactly the synthesis a parent cannot hand off. Follow
`receiving-code-review`: check each finding against the code before acting on
it, and push back with a demonstration rather than an argument.

This step is not a formality. In the real run it changed the disposition of half
the findings — two of four would have been wrong to apply as written.

## Step 6 — Report a disposition table

Every finding from every reviewer appears, with what you did about it and why.
Silence on a finding is not an option: an unmentioned finding reads as one
nobody raised.

```
## Review panel: <target> — 3 reviewers, 4 findings

| # | Reviewer | Finding | Disposition |
|---|---|---|---|
| 1 | r2 | `find` matches directories, misses multi-template layouts | applied — reproduced it first |
| 2 | r1 | `wfctl change` named as a command that opens a change | applied — confirmed it exits 0 |
| 3 | r1 | mirror-membership test is near-tautological | accepted — for a sharper reason than the one given (see below) |
| 4 | r3 | the `_MIRRORED_SKILLS` comment rationale doesn't apply here | rejected — the rationale is about #124's failure mode, which this entry has |

roster: r1 ✓  r2 ✓  r3 ✓ (r3 re-asked once)
```

Three dispositions, each requiring a reason on the line: **applied**,
**accepted** (with the reason you accepted it for, when it differs from the one
given), **rejected** (with the reason). A run in which everything was applied
has not exercised the reconciliation — it has relayed three reports.

## Red flags

- Recording a pass as clean because a reviewer said it had nothing to add. That
  is the exact sentence this skill was written after.
- Giving each reviewer a different lens. That is a coverage split, and
  `code-review` already covers those axes in one pass.
- Letting a reviewer edit the tree, or fixing findings while reviewers are still
  running. Both corrupt the diff the others are reading.
- Handing reviewer 2 what reviewer 1 found, or handing any of them your session
  history. Both destroy the independence that is the only thing a panel buys.
- Applying findings straight from the reports. Half of them changed shape under
  verification.
- A disposition table shorter than the number of findings collected.
