---
status: proposed
---

# The plan-review skill says how to review a plan, and its command holds everything tied to wfctl

**What does this record decide?**
Plan review lives in two files. The skill says how to review a plan and knows nothing about wfctl. The `/plan-review` command holds everything wfctl-specific, including the run that fixes the plan when a review finds blockers.

## Context

The README decides where Spec Kit ends and wfctl begins. Spec Kit keeps its
steps, and wfctl's own checks sit around them. Brainstorm, the four design
levels, and domain modeling run before Spec Kit. Decompose runs before
implement, and a refactor pass runs inside it. Plan review is one more of
wfctl's checks, and it runs between `plan` and `tasks`.

The plan-review skill arrived as a candidate written for Spec Kit. Most of it is
a review method that works anywhere. It covers the lenses the reviewer reads
through, how a finding is graded, what counts as evidence, and what the report
looks like. A handful of lines are tied to Spec Kit instead. They name the
`[NEEDS CLARIFICATION` notes to surface, the commands the review sits between,
the folder it writes into, and the command name it proposes. This means those
lines change whenever the pipeline does, and the method doesn't.

The name is a separate question. Eleven skills wfctl ships start with
`speckit-`, and three of them are wfctl's own checks rather than Spec Kit's
steps. This means the prefix blurs the line the README draws.

Two other records cover the rest, and this one doesn't restate them. The
`vendor-upstream-skills` record covers skills derived from Spec Kit, and it
allows the `speckit-` prefix on a skill wfctl wrote. The
`the-scan-is-attested-where-the-reviewer-reads` record decides where the review
and its scan file go.

## Verified

- `README.md` on `main`, under "Why wfctl", says "Brainstorm, the four design
  levels and domain modeling run before Spec Kit", and draws decompose and the
  refactor pass as wfctl's own.
- `docs/architecture/vendor-upstream-skills.md:113` says "The prefix is a
  naming convention, not a provenance claim".
- `wfctl/agents/skills/` holds eleven `speckit-` folders. Three of them,
  `speckit-brainstorm`, `speckit-delivery-plan`, and `speckit-orchestrate`, are
  written by wfctl.
- `wfctl/agents/skills/speckit-clarify/SKILL.md` ends with "Derived from
  github/spec-kit (MIT, © GitHub, Inc.)". Its command,
  `wfctl/agents/commands/speckit.clarify.md`, carries no such line. The command
  holds the Spec Kit-specific rules, which are the rule for
  `[NEEDS CLARIFICATION` notes and the `## Write the scan file` section.
- The candidate skill names Spec Kit in its body at `SKILL.md:3`, `:26`, `:89`,
  `:177`, and `:208` (`/speckit.plan`, `/speckit.tasks`, `/speckit.analyze`,
  and `[NEEDS CLARIFICATION]`), and proposes `/speckit.review-plan` at
  `references/wfctl-integration.md:33`.

## Assumed

- The wfctl-specific part stays small. It is the `[NEEDS CLARIFICATION` notes,
  the step names, and the scan-file instruction. This is wrong if the method
  turns out to need pipeline state to run, because then half the method ends up
  in the command. The run that fixes the plan does read pipeline state, but it
  isn't part of the method, so it sits in the command without testing this
  assumption.
- A command without the `/speckit.` prefix doesn't cost users more than an
  honest name is worth. Every other pipeline command a user types starts with
  `/speckit.`, including `/speckit.brainstorm` and `/speckit.decompose`, which
  are wfctl's. This is wrong if users look for `/speckit.plan-review` and miss
  `/plan-review`. Then the prefix is the right name, and the rename is a new
  record that supersedes this one.

## Direct baseline

Ship the candidate as one skill named `speckit-plan-review`, with its Spec Kit
references left in, and a thin command that only points at it. That is the
candidate as written, renamed to match the skills beside it. The skill carries
all of the behaviour, and the command carries none.

## Decision

The skill holds the review method, and the `/plan-review` command holds
everything tied to wfctl.

The skill names no pipeline, no command, and no Spec Kit syntax. This means it
reads correctly under any pipeline that points at it.

The command connects the skill to wfctl's pipeline. It names the
`[NEEDS CLARIFICATION` notes to surface, wfctl's step names (`plan`, `tasks`,
and `analyze`), where the report goes, and the instruction to follow
`writing-a-scan-file`. It has the same shape as `/speckit.clarify`, which is
where a skill already meets the pipeline today.

The command also holds the run that fixes the plan. When the last review of the
current plan left BLOCKERs open, the agent running `/plan-review` edits
`plan.md` to fix them instead of reviewing again. First, the command checks
whether anything else the review read has changed since, such as `spec.md`, a
design record, or a planning document. If something has, the agent reviews
instead. This means a plan owner who fixed a BLOCKER in `spec.md` gets that fix
reviewed, and does not get an agent edit to `plan.md`. The check leaves out two
files. `plan.md` is one, and the saved copy of the plan the review read is the
other, since every review overwrites that copy afterwards. The report never
lists itself, since a file can't record its own fingerprint.

A run that fixes the plan never loads the skill. This means the skill's three
promises stay true. The skill never edits what it reviews, never loops until the
findings clear, and never hands control on. The editing happens in the command's
fixing run, and after a review the command, not the skill, hands back to the
orchestrator.

In the code, the skill is `wfctl/agents/skills/plan-review/` and the command is
`wfctl/agents/commands/plan-review.md`.

## Diagram

```
               baseline                            decision

stable                                        ┌──────────────────────┐
                                              │ plan-review skill    │
                                              │ lenses, priorities,  │
                                              │ evidence, report     │
                                              └──────────────────────┘
                                                         ▲
                                                         │ reads
═══ skill / command, as speckit.clarify ═════════════════╪══════════════
                                                         │
changes   ┌───────────────────────┐           ┌──────────┴───────────┐
often     │ speckit-plan-review   │           │ /plan-review command │
          │ method, clarify notes,│           │ clarify notes, steps,│
          │ /speckit.* names      │           │ report + copy paths, │
          └───────────────────────┘           │ scan file instruction│
                     ▲                        └──────────────────────┘
                     │ reads
          ┌──────────┴────────────┐
          │ command, a pointer    │
          └───────────────────────┘
```

The two pictures differ in where the method sits. In the baseline, the method
shares a file with Spec Kit's vocabulary. This means it sits below the line and
changes whenever the pipeline does. In the decision, the method sits above the
line, and a new pipeline or a renamed step only touches the command.

## Considered

- **`speckit-plan-review`, with the split.** It is allowed, and it matches how
  `/speckit.brainstorm` and `/speckit.decompose` are typed. It loses because the
  prefix reads as "this came from Spec Kit", whatever a record says it means,
  and the README puts wfctl's checks outside Spec Kit. The bet under *Assumed*
  is what makes this choice cheap to reverse.
- **`sdd-plan-review`.** It swaps Spec Kit's vocabulary for spec-driven
  development's, which moves the naming problem without solving it. The skill
  is named after wfctl's own step instead.
- **The baseline, with Spec Kit's text kept in the skill.** It is one file, and
  that text is short. It loses because the skill then only reads correctly
  under Spec Kit, and a method that works anywhere is the part of the candidate
  worth keeping.

## Consequences

The skill works on its own. A pipeline other than Spec Kit can use it by
writing its own command, and a renamed step doesn't touch the skill.

`/plan-review` is the one pipeline command without the `/speckit.` prefix. This
means `wfctl status` prints `next: /plan-review` between two `/speckit.`
commands.

Two files carry the behaviour, so a reader opens both to see the whole check.
`/speckit.clarify` already asks the same of its reader.

The way this goes wrong is drift back into the skill. A later edit adds a
`/speckit.tasks` line to the method because it was the nearest file. Nothing
flags that edit at review time. Only a test in wfctl's suite catches it.

## Verification

Two tests in wfctl's suite hold the split:

1. One reads `plan-review/SKILL.md` and its references, and fails on
   `/speckit.`, `[NEEDS CLARIFICATION`, or `checklists/`.
2. The other checks that the command names the skill by path, the way
   `speckit.clarify.md` does.

## Log

- 2026-09-26  proposed  — #501 level 3. The candidate's method names no runner,
  and its name was the one open question #395 bears on.
- 2026-09-26  revised   — #395 closed, answered by the README's line between
  Spec Kit's steps and wfctl's passes. The name now rests on that line rather
  than on waiting for #395, and the reversal bet is the cost of a command
  outside the `/speckit.` namespace. Still proposed, so revised rather than
  superseded.
- 2026-09-27  revised   — the plan review of #501 found the plan had extended
  this record with a revise mode without amending it, and that the wrapper
  loaded the skill before editing the plan the skill forbids it to edit. The
  Decision now names the revise mode, and a revise run does not load the skill.
- 2026-09-27  revised   — the re-review found that a person who fixed a BLOCKER
  in `spec.md` and ran `/plan-review` got a revision of `plan.md` rather than a
  review of the fix. The revise mode now checks the report's other input
  identities first and reviews when one has changed. The third review found
  that the check included the plan copy, whose row never matches after a
  re-review, and that this record named fewer inputs than the check reads. The
  check now skips the copy, and the Decision names every recorded input.
- 2026-09-27  renamed   — from `501-plan-review-wrapper-split`, which named the
  refactor rather than the subject. The new slug pairs with
  `plan-review-severity`.
- 2026-09-27  renamed   — from `501-plan-review-boundaries`. Record names carry no
  issue-number prefix.
- 2026-09-28  rewritten   — plain language first, and an opening question
