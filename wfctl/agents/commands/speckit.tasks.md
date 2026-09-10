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

Follow `.agents/skills/reading-design-records/SKILL.md` (or
`../skills/reading-design-records/SKILL.md` relative to this file, if
`.agents/skills` isn't present). It owns how the list is resolved, the four
states, and how they are reported. What it does not own is when this step reads
them, which is below.

**Before generating tasks**, not after. A task that reverses a recorded decision
is a defect `/speckit.analyze` reports as pass G; writing it and catching it one
step later is worse than not writing it.

