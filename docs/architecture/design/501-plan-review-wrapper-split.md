---
status: proposed
---

# The plan-review method is a skill named for wfctl's step, and everything that names a runner lives in its command wrapper

## Context

The candidate skill reviews `spec.md` and `plan.md` before `tasks` expands them
into work. Its method (the lenses, the priority tests, the evidence rules and
the report shape) names no runner. A handful of lines do: the marker it
surfaces, the commands it places itself between, the directory it writes into,
and the wrapper name it proposes. Those lines change whenever the runner does,
and the method does not.

The name is open for a separate reason. Eleven shipped skills carry the
`speckit-` prefix, and three of them are wfctl's own passes. The README draws
the line those names blur: Spec Kit keeps its steps, and wfctl's design method
sits around them, with brainstorm, the four design levels, and domain modeling
before Spec Kit, decompose before implement, and a refactor pass inside
implement. plan-review is one more pass of that kind, between `plan` and
`tasks`.

`vendor-upstream-skills` governs derived skills and permits the prefix on a
wfctl-authored one. It is cited, not restated. The placement of the report and
its scan file is `the-scan-is-attested-where-the-reviewer-reads`, and is not
this record's.

## Verified

- `README.md` on `main`, under "Why wfctl", says "Brainstorm, the four design
  levels and domain modeling run before Spec Kit" and draws decompose and the
  refactor pass as wfctl's own.
- `docs/architecture/vendor-upstream-skills.md:113` says "The prefix is a
  naming convention, not a provenance claim".
- `wfctl/agents/skills/` holds eleven `speckit-` directories. Three of them,
  `speckit-brainstorm`, `speckit-delivery-plan`, and `speckit-orchestrate`, are
  wfctl-authored.
- `wfctl/agents/skills/speckit-clarify/SKILL.md` ends with "Derived from
  github/spec-kit (MIT, © GitHub, Inc.)". Its wrapper,
  `wfctl/agents/commands/speckit.clarify.md`, carries no such line and holds
  the runner-bound rules: the `[NEEDS CLARIFICATION` marker rule and the
  `## Write the scan file` section.
- The candidate names spec-kit in its body at `SKILL.md:3`, `:26`, `:89`,
  `:177`, and `:208` (`/speckit.plan`, `/speckit.tasks`, `/speckit.analyze`,
  and `[NEEDS CLARIFICATION]`), and proposes `/speckit.review-plan` at
  `references/wfctl-integration.md:33`.

## Assumed

- That the runner-bound part stays small: the marker, the step names, and the
  scan-file instruction. Falsified if the method turns out to need pipeline
  state to run, in which case the split puts half the method in the wrapper.
  The revise mode reads pipeline state and is not the method, which is why it
  sits in the wrapper without testing this assumption.
- That a command outside the `/speckit.` namespace does not cost users more
  than the honesty of the name is worth. Every other pipeline command a user
  types starts with `/speckit.`, including `/speckit.brainstorm` and
  `/speckit.decompose`, which are wfctl's. Falsified if users look for
  `/speckit.plan-review` and miss `/plan-review`, and then the prefix is the
  right name and a rename is a new record superseding this one.

## Direct baseline

Ship the candidate as one skill named `speckit-plan-review`, with its spec-kit
references left in the body, and a thin wrapper that only points at it. This is
the candidate as written, renamed to match the shelf it sits on, and it needs
no second file to carry behaviour.

## Decision

The skill is `wfctl/agents/skills/plan-review/` and holds the method. Its body
names no runner, no command, and no marker syntax.

A new wrapper, `wfctl/agents/commands/plan-review.md`, binds the skill to the
pipeline. It holds the marker to surface, wfctl's step names (`plan`, `tasks`,
and `analyze`), the report path, and the instruction to follow
`writing-a-scan-file`. It follows `speckit.clarify.md`'s shape, which is the
existing layer where a skill meets the pipeline.

The wrapper also holds the revise mode. It reads the pass from `wfctl status`,
and when a review of the current plan has BLOCKERs open it edits `plan.md`
against them instead of reviewing. A revise run does not read the skill. The
method never edits what it reviews, never iterates until findings clear, and
never hands control on, and none of the three happens inside it. The revise run
does not load the method, and a review run hands back to the orchestrator from
the wrapper, after the method has written its report and stopped.

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
═══ skill / command wrapper, as speckit.clarify ═════════╪══════════════
                                                         │
volatile  ┌───────────────────────┐           ┌──────────┴───────────┐
          │ speckit-plan-review   │           │ /plan-review wrapper │
          │ method + marker +     │           │ marker, step names,  │
          │ /speckit.* names      │           │ report path, scan    │
          └───────────────────────┘           │ file instruction     │
                     ▲                        └──────────────────────┘
                     │ reads
          ┌──────────┴────────────┐
          │ wrapper, a pointer    │
          └───────────────────────┘
```

The graphs differ by where the method sits. In the baseline the method shares
a file with the runner's vocabulary, so it sits below the divider and changes
whenever the runner does. In the decision the method sits above it, and a
change of runner, or a renamed step, touches the wrapper alone.

## Considered

- **`speckit-plan-review`, with the split.** It is permitted, and it matches
  how `/speckit.brainstorm` and `/speckit.decompose` are invoked. It loses
  because the prefix reads as provenance whatever the record says it means,
  and the README places wfctl's passes outside the Spec Kit box. The bet under
  *Assumed* is what makes choosing against it cheap to reverse.
- **`sdd-plan-review`.** It trades spec-kit's vocabulary for spec-driven
  development's, which moves the naming problem one step without solving it.
  The skill is named after wfctl's own step instead.
- **The baseline, runner text kept in the skill.** It is one file, and the
  runner text is short. It loses because the skill then reads correctly only
  under spec-kit, and a method that names no runner is the part of the
  candidate worth keeping.

## Consequences

The method reads on its own, and a runner other than spec-kit wraps it by
writing a wrapper. A renamed step does not touch the skill.

It is the one pipeline command outside the `/speckit.` namespace, so
`wfctl status` prints `next: /plan-review` between two `/speckit.` commands.

Two files carry the behaviour, so a reader has to open both to see the whole
pass. `speckit.clarify.md` already asks the same of its reader.

The failure mode is drift back into the skill: a later edit adds a
`/speckit.tasks` line to the method because it was the nearest file. Nothing
catches that unless a test does.

## Verification

A test in wfctl's suite reads `plan-review/SKILL.md` and its references and
fails on `/speckit.`, `[NEEDS CLARIFICATION`, or `checklists/`. A second test
checks that the wrapper names the skill by path, the way
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
