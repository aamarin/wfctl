---
status: proposed
---

# The four passes live in their own skill, and the route to implementation points to it

## Context

A change that bypasses Spec Kit goes straight to implementation, and no skill
covers that route. Right now, three places tell a small change it can skip the
design passes:

1. The `design-levels` skill says it is not for "bug fixes, copy edits and other
   trivial changes that introduce no new state".
2. The `architecture-design` skill says those changes "go straight to
   implementation".
3. The `worktree-handoff` skill says a bug fix or a copy edit doesn't run through
   the pipeline, and the project instructions repeat it.

Andre asked for the four passes to run on these changes too, before any code is
written. The agent has to hit the passes when it picks the route, because a
description-triggered skill doesn't fire in an unattended run. That's why the
review panel became a numbered step in `opening-a-change`.

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
- `docs/architecture/domain/wfctl.md` holds this repo's domain model, and
  `.agents/skills/model-the-domain/SKILL.md:104` says later questions start from
  it rather than asking again. `.agents/skills/design-levels/SKILL.md:174` lets
  level 2 skip its method when a record or spec settles the boundary, and says
  nothing about reading the domain model first.

## Assumed

- The agent reads a handoff's route line before writing code. The
  `start-session` skill reads the handoff first, which backs this up. A session
  that starts without a handoff relies on the project instructions alone.
- #382's short track can use this skill as the command for its design step. If
  #382 needs the passes as separate steps, the skill splits along the four
  numbered passes it already has.

## Direct baseline

Don't add a skill. Rewrite the three "not for" lines and the project
instructions to list the four passes, and point levels 2 and 3 at the skills
that already run them. Those lines would also list the test-first and refactor
passes, since no existing skill covers them outside `/speckit.implement`.

## Decision

A new skill, `design-passes`, holds the four passes in order and says what each
one produces. Every place that currently sends a small change straight to
implementation points to this skill instead:

1. The route line in `worktree-handoff` names `design-passes` as the route for a
   change that bypasses Spec Kit.
2. The "not for" lines in `design-levels` and `architecture-design` say a small
   change skips Spec Kit, not the passes, and point to `design-passes`.
3. The project instructions say the same and point to the same skill.

The skill starts by asking whether the change needs a spec, before any code is
written. The answer goes in the PR's "Needs a spec?" section. If it does, the
change goes through the Spec Kit pipeline. If not, it continues with the four
passes.

The skill has no design method of its own. Each pass calls the skill that
already does that work: `architecture-design` at level 2,
`software-design-decisions` at level 3, and `clean-code` for the refactor, plus
`python-pattern-selection` when a pattern name comes up. At level 2, a change
inside an existing boundary writes nothing, and the skill says not to run
`wfctl arch none` on this route.

Level 2 starts by reading the accepted records and the domain model in the
`domain/` folder under the arch root. A small fix is the change least likely to
check either one. Without this step, it can redraw a boundary the model already
settled, and nobody notices. If a change shifts what a modeled term means, it
goes to `model-the-domain` before `architecture-design`, the same order
`design-levels` already uses. `design-levels` currently skips this step too, so
it gets the same first step at level 2. That way a change reads the domain
model on either route.

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

The two graphs differ by one component and by how many arrows cross the route
line. In the baseline, four places each name three skills, for 12 arrows. In
the decision, four places each name one skill, for 4 arrows, and
`design-passes` holds the remaining three. This design is meant to handle a
change to the passes, such as #479 moving the refactor to every task, or adding
a fifth pass. In the baseline, that change touches all four places. In the
decision, it touches only `design-passes`.

## Considered

- **The direct baseline above.** It doesn't add a skill, and it reads fine in
  any one of the four places. We didn't choose it because the four copies drift apart.
  Four skills already carry the "not for trivial changes" line, each worded
  differently.
- **A step in `opening-a-change`, before the review panel.** Andre decided
  against it. It runs after the code is written, and the passes only pay off
  before that. It would also touch the file #622 is redesigning.
- **A section added to `design-levels`.** It already decides which level
  answers each question. We didn't choose it because its description matches
  designing "a feature, screen, or schema change", not a bug fix, so it
  wouldn't fire on the changes this is meant for. It also doesn't cover the
  test-first and refactor passes.

## Consequences

Changing the passes means editing one skill. The cost is one more skill in the
tree, and four places that have to keep pointing to it. The suite's
cross-reference tests catch both a pointer to a missing skill and a place that
stops pointing to `design-passes`.

`design-passes` doesn't touch `opening-a-change`. It ends before opening a PR,
so the review panel covers the refactor with the rest of the change.

## Verification

- Run `uv run wfctl install-skills`, then run `design-passes` for real on a
  throwaway branch with a one-line fix. The run should ask the spec question
  before any code, and end with a failing test committed before the fix, no
  `arch none` file, and either a refactor commit or nothing to refactor.
- The skills that currently send a small change straight to implementation
  point to `design-passes` instead. `tests/test_skill_cross_references.py`
  fails if any of them stops naming it, or if a shipped file still sends a
  change "straight to implementation".

## Log

- 2026-10-22  proposed  — #628: the four passes need one home that a route
  without Spec Kit reaches before code is written
- 2026-10-22  proposed  — revised before review: the skill asks whether a spec
  is needed first, and writes no `arch none` for a change inside a boundary
- 2026-10-22  proposed  — revised before review: level 2 reads the accepted
  records and the domain model before answering the boundary question
- 2026-10-23  proposed  — revised after plan review: the skill asks the spec
  question first and writes no trailer, so the PR section is the only record
