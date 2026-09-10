---
disable-model-invocation: true
description: Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts.
handoffs:
  - label: Analyze For Consistency
    agent: speckit.analyze
    prompt: Run a project analysis for consistency
    send: true
  - label: Implement Project
    agent: speckit.implement
    prompt: Start the implementation in phases
    send: true
allowed-tools: Read Glob Bash(.specify/scripts/bash/check-prerequisites.sh*) Bash(wfctl feature-paths*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-tasks/SKILL.md` (or `../skills/speckit-tasks/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete task generation workflow.

## Read this feature's design records

**Before generating tasks**, not after. A task that reverses a recorded decision
is a defect `/speckit.analyze` will report as pass G; writing it and catching it
one step later is worse than not writing it.

```bash
wfctl feature-paths      # read FEATURE_DIR from the output
```

Read `<FEATURE_DIR>/design.md` and take the section headed
`## Software design decisions`. Every **list item** of the form
`- <path> — <text>` names a record; read each one.

**Prose in that section names no records.** The section carries prose by design —
`/speckit.brainstorm` requires a level answered with no record to say so in one
line rather than delete the heading — and that prose may name a *level-2* record.
A level-2 record read as level-3 binds nothing while looking like it does.

**Do not glob `<arch-root>/design/` by issue number instead.** That was the first
mechanism and it is silently wrong on any branch cut from an epic: the worktree
carries the epic's number, the record carries the child issue's, so the glob
loads another feature's record and misses this one. Neither failure raises
anything. `docs/architecture/design-md-indexes-the-records.md` carries the
argument.

**Report what was read, in the step's closing report, always** — including when
there was nothing:

```
Design records: 2 listed in design.md
  <path>
  <path>

Design records: none — design.md records no level-3 decision

Design records: unknown — no design.md at <FEATURE_DIR>
```

The last two are different facts and are never collapsed. One says a design pass
ran and recorded no structural decision; the other says no design pass ran. A
step that reports neither reproduces #307's defect one directory over.

A listed path that will not read — missing, or outside the working tree — gets
its own line, `<path> — listed, not found`, and does not stop the step.

Report paths, never a summary. A digest of a record is a second copy of it, and
the copy is what drifts.

**Here rather than in `speckit-tasks/SKILL.md`**: that skill is
`github/spec-kit`-derived (`vendor-upstream-skills`), so an in-place edit is
reverted by the next upstream pull with no conflict to notice, and the behaviour
then regresses at a moment whose diff mentions neither the skill nor this file.
Same layer, and the same reason, as the scan-file instruction in
`speckit.analyze.md`.
