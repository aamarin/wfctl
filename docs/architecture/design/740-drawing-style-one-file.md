---
status: accepted
governs: design-method
---

# The drawing style lives in one design-levels file

## Context

The drawing style is the set of rules an agent follows each time it draws an
SVG for a record. It covers boxes on a grid, a short label on every arrow, the
refused edge in red, a one-line caption, a background in the page's color, the
`failing-step` and `refused-edge` classes, and rendering the drawing to look at
it before committing.

Currently, four skills carry diagram guidance, and each one needs these rules:

1. `design-levels`, whose "Rendering the gate's answer" section picks which
   picture each level's answer gets.
2. `architecture-decisions`, in its SKILL.md and its `record-template.md`.
3. `software-design-decisions`, in the `## Diagram` section of its record
   template.
4. `model-the-domain`, in `references/visual-language.md`.

If each skill keeps a full copy, a fix to one rule takes four edits, and
the copies drift apart.

## Verified

- `wfctl/agents/skills/design-levels/SKILL.md` is 561 lines, and its "Rendering
  the gate's answer" section runs from line 330 to line 426. An agent reads the
  whole file whenever it runs a design session, whether or not it draws.
- `model-the-domain/references/visual-language.md:5` already defers to
  `design-levels` for the format rule, and `architecture-decisions/SKILL.md:93`
  points to the same section.
- `reviewing-security/SKILL.md:108` links to
  `../security-and-hardening/references/hardening-patterns.md`, so this
  repository already has a skill that links to a reference file in another
  skill's folder.
- `design-levels` has no `references/` folder yet.

## Assumed

- An agent drawing for a record follows a relative link to a reference file
  and reads it. An agent that follows the link and draws an SVG with no grid,
  no arrow labels, or no red refused edge would falsify this.

## Direct baseline

Add the full style to the "Rendering the gate's answer" section of
`design-levels/SKILL.md`, and have the other three skills point to that
section. This keeps one copy and adds no new file.

## Decision

The full style goes in one new file,
`wfctl/agents/skills/design-levels/references/drawing-style.md`.
`design-levels/SKILL.md` gets one sentence in "Rendering the gate's answer"
telling the agent to read that file when it draws. The other three skills keep
only what is specific to them, such as which kinds of diagram a record can
declare, and link to the same file.

The file lives in `design-levels` because that skill already decides which
picture each answer gets, and the other three draw the picture it picks.

## Diagram

```
        baseline                                decision

  ┌───────────────────┐                ┌───────────────────┐
  │ design-levels     │                │ design-levels     │
  │ SKILL.md          │                │ SKILL.md          │
  │ + full style      │                │ + one sentence    │
  │ (read every       │                └─────────┬─────────┘
  │  design session)  │                          │ links
  └───────────────────┘                          ▼
     ▲     ▲     ▲                     ┌───────────────────┐
     │     │     │ point to            │ drawing-style.md  │
     │     │     │                     │ (new, read only   │
  ┌──┴─┐┌──┴─┐┌──┴─┐                   │  when drawing)    │
  │ AD ││ SD ││ MD │                   └───────────────────┘
  └────┘└────┘└────┘                      ▲     ▲     ▲
                                          │     │     │ link
                                       ┌──┴─┐┌──┴─┐┌──┴─┐
                                       │ AD ││ SD ││ MD │
                                       └────┘└────┘└────┘

AD architecture-decisions   SD software-design-decisions   MD model-the-domain
```

Both sides have one copy of the style, so a fix is one edit in either. The
difference is which sessions load it. In the baseline, every design session loads
the style through `design-levels/SKILL.md`, including the ones that never
draw. In the decision, only an agent that draws opens `drawing-style.md`.

## Considered

- **The baseline, with the full style in the `design-levels` SKILL.md.** It
  adds no file. We didn't choose it because the main file is already 561 lines
  and is read in full on every design session, so every session would load
  rules that only a drawing needs.
- **A full copy in each of the four skills.** Each skill would be
  self-contained. We didn't choose it because a fix to one rule would need four
  edits, and a missed copy would teach a different style with no check to find
  it.
- **A fifth skill holding only the style.** It would load only when invoked. We
  didn't choose it because the drawing guidance is meant to stay in the four
  skills that already carry it, and a skill that triggers from its description
  can go unloaded when an agent draws without naming it.
- **Pointing the other three skills at `design-levels` instead of at the
  file.** The link would survive a rename of the file. We didn't choose it
  because the agent would load all of `design-levels` to find the drawing
  rules, which brings back the cost the decision removes.

## Consequences

The "Rendering the gate's answer" section in `design-levels/SKILL.md` grows by
one sentence, not by the style.

A change to the drawing style is one edit to `drawing-style.md`, and the four
skills pick it up through their links.

If `drawing-style.md` is renamed or moved, the four links break. The suite has
no general check for links between skills. It has only per-skill tests, such as
`test_the_skill_ships_every_reference_it_loads` in
`tests/test_plan_walkthrough_skill.py`. That's why this change adds a test that
each of the four links resolves.

## Verification

- `drawing-style.md` exists under `design-levels/references/`, and each of the
  four skills links to it by relative path.
- `grep -rn "refused-edge" wfctl/agents/skills` finds the class defined only in
  `drawing-style.md`. Any other hit is a link or a template example, not a
  second statement of the rule.
- A new test fails when one of the four links points to a missing file.
- After `uv run wfctl install-skills`, an agent drawing a record's SVG from the
  `architecture-decisions` skill produces a drawing that follows the style.

## Log

- 2026-11-13  proposed  — the second level-3 gate for #740
- 2026-11-15  accepted  — Andre, in the #740 implement session on 2026-11-15
