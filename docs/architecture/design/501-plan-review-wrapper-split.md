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
`speckit-` prefix, and #395 is deciding which parts of the pipeline wfctl owns
and which remain spec-kit's. A new skill named `speckit-plan-review` adds a
twelfth name to the shelf that decision has to sort.

`vendor-upstream-skills` governs derived skills and permits the prefix on a
wfctl-authored one. It is cited, not restated. The placement of the report and
its scan file is `the-scan-is-attested-where-the-reviewer-reads`, and is not
this record's.

## Verified

- `docs/architecture/vendor-upstream-skills.md:114` says "The prefix is a
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
- That #395 moves wfctl's own passes away from spec-kit's names. Falsified if
  it decides wfctl keeps spec-kit's vocabulary for every step, and then
  `speckit-plan-review` is the correct name and this record was premature
  rather than wrong. A rename at that point is a new record superseding this
  one.

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
change of runner, or #395 renaming a step, touches the wrapper alone.

## Considered

- **`speckit-plan-review`, with the split.** It is permitted, and it is equally
  good today. It loses on timing: it adds a wfctl-owned skill to the shelf #395
  is sorting, and leaves that decision one more name to move. The reversal
  condition under *Assumed* is what makes choosing against it cheap.
- **`sdd-plan-review`.** It trades spec-kit's vocabulary for spec-driven
  development's, which moves the naming problem one step without solving it.
  The skill is named after wfctl's own step instead.
- **The baseline, runner text kept in the skill.** It is one file, and the
  runner text is short. It loses because the skill then reads correctly only
  under spec-kit, and a method that names no runner is the part of the
  candidate worth keeping.

## Consequences

The method reads on its own, and a runner other than spec-kit wraps it by
writing a wrapper. #395 can rename steps without editing the skill.

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
