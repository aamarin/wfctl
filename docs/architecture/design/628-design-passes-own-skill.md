---
status: proposed
---

# The four passes live in their own skill, which the route to implementation names

## Context

A change that skips Spec Kit goes straight to implementation, and no skill
covers that route. Three places currently tell a small change it can skip the
design passes:

1. The `design-levels` skill says it is not for "bug fixes, copy edits and other
   trivial changes that introduce no new state".
2. The `architecture-design` skill says those changes "go straight to
   implementation".
3. The `worktree-handoff` skill says a bug fix or a copy edit doesn't go through
   the pipeline, and the project instructions repeat it.

Andre asked for the four passes to run on these changes too, before any code is
written. The passes have to be reached when the agent picks the route, because a
skill that is only found by matching its description doesn't fire in an
unattended run. That is why the review panel became a numbered step in
`opening-a-change`.

`every-change-answers-spec-question` decides what the passes record and what
wfctl checks. This record decides where the instructions for all four live.

## Verified

- `.agents/skills/design-levels/SKILL.md:22` reads "Not for: bug fixes, copy
  edits and other trivial changes that introduce no new state".
- `.agents/skills/architecture-design/SKILL.md:46` reads "those go straight to
  implementation, and running this method over one costs more than the change".
- `.agents/skills/worktree-handoff/SKILL.md:66` makes every handoff state its
  route, "Straight to implementation, or through the spec pipeline", and line 70
  says "a bug fix or a copy edit does not".
- `AGENTS.md:391` reads "Not every change needs the spec pipeline", quoting the
  `design-levels` exclusion.
- `wfctl/agents/commands/speckit.implement.md:33` runs the refactor pass only
  inside `/speckit.implement`, after the last task.
- `docs/architecture/a-repo-concern-earns-a-step-hook-or-method.md` says a
  method "belongs inside the skill that performs the work".

## Assumed

- A handoff's route line is read before code is written. The `start-session`
  skill reads the handoff first, which supports this. A session started with no
  handoff would rely on the project instructions alone.
- #382's short track can name this skill as its design step's command. If #382
  needs the passes split into separate steps, the skill splits along the four
  numbered passes it already has.

## Direct baseline

Add no skill. Rewrite the three "not for" lines and the project instructions to
list the four passes, and point the level-2 and level-3 passes at the skills
that already run them. The test-first and refactor passes would be listed in
those lines too, since no existing skill covers them outside `/speckit.implement`.

## Decision

A new skill, `design-passes`, holds the four passes in order and says what each
one leaves behind. Every place that currently sends a small change straight to
implementation names this skill instead:

1. The route line in `worktree-handoff` names `design-passes` as the route for a
   change that skips Spec Kit.
2. The "not for" lines in `design-levels` and `architecture-design` say a small
   change skips Spec Kit, not the passes, and point at `design-passes`.
3. The project instructions say the same and point at the same skill.

The skill opens by asking whether the change needs a spec, and writes the answer
as a `Needs-spec:` trailer on the branch's first commit. A yes sends the change
to the Spec Kit pipeline. A no continues with the four passes.

The skill runs no design method of its own. Each pass calls the skill that
already does that work: `architecture-design` at level 2, `software-design-decisions`
at level 3, and `clean-code`, plus `python-pattern-selection` when a pattern name
comes up, for the refactor. At level 2, a change that works inside an existing
boundary writes nothing, and the skill says not to run `wfctl arch none` on this
route.

## Diagram

```
                baseline                               decision

stable    ┌───────────────┐ ┌──────────────┐ ┌──────────┐ ┌───────────────┐ ┌──────────────┐ ┌──────────┐
          │architecture-  │ │software-     │ │clean-code│ │architecture-  │ │software-     │ │clean-code│
          │design         │ │design-       │ │          │ │design         │ │design-       │ │          │
          │               │ │decisions     │ │          │ │               │ │decisions     │ │          │
          └───────▲───────┘ └──────▲───────┘ └────▲─────┘ └───────▲───────┘ └──────▲───────┘ └────▲─────┘
                  │ names          │ names        │ names         └──────calls─────┼──────────────┘
                  │                │              │                         ┌───────┴────────┐
                  │                │              │                         │ design-passes  │ (new)
                  │                │              │                         └───────▲────────┘
                  │                │              │                                 │ names
════ the route to implementation ═╪══════════════╪═════════════════════════════════╪══════════════════
          ┌───────┴────────────────┴──────────────┴──┐               ┌──────────────┴───────────────────┐
volatile  │ handoff route, design-levels, arch-design,│               │ handoff route, design-levels,    │
          │ AGENTS.md: each lists all four passes     │               │ arch-design, AGENTS.md           │
          └───────────────────────────────────────────┘               └──────────────────────────────────┘
```

The two graphs differ by one component and by the number of arrows that cross
the route line. In the baseline, four places each name three skills, which is 12
arrows. In the decision, four places each name one skill, which is 4 arrows, and
`design-passes` holds the three that remain. The change this is built to absorb
is a change to the passes, such as #479 moving the refactor to every task or a
fifth pass being added. In the baseline, that change edits all four places. In
the decision, it edits `design-passes` alone.

## Considered

- **The direct baseline above.** It adds no skill, and it reads well in any one
  of the four places. We didn't choose it because the four copies drift apart.
  The "not for trivial changes" line already exists in four skills that say it
  in four different ways.
- **A step in `opening-a-change`, before the review panel.** Andre decided
  against it. It runs after the code exists, and the passes are worth running
  only before code. It would also edit the file #622 is redesigning.
- **A section added to `design-levels`.** It already owns which level a question
  is answered at. We didn't choose it because its description matches designing
  "a feature, screen, or schema change", not a bug fix, so it wouldn't fire on
  the changes this is for. The test-first and refactor passes are also not its
  subject.

## Consequences

A change to the passes edits one skill. The cost is one more skill in the tree,
and four places that have to keep pointing at it. The suite's cross-reference
test catches a pointer to a skill that doesn't exist, but not a place that stops
pointing at it.

`design-passes` doesn't touch `opening-a-change`. It ends before the pull request
opens, so the review panel reviews the refactor along with the rest of the
change.

## Verification

- `uv run wfctl install-skills`, then a real run of `design-passes` on a
  throwaway branch for a one-line fix. The run should end with a `Needs-spec:`
  trailer on the first commit, a failing test committed before the fix, no
  `arch none` file, and either a refactor commit or no change.
- The skills that currently send a small change straight to implementation
  name `design-passes` instead, which a grep for "straight to implementation"
  confirms.

## Log

- 2026-10-22  proposed  — #628: the four passes need one home that a route
  without Spec Kit reaches before code is written
- 2026-10-22  proposed  — revised before review: the skill asks whether a spec
  is needed first, and writes no `arch none` for a change inside a boundary
