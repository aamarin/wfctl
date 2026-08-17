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
allowed-tools: Read Glob Bash(.specify/scripts/bash/check-prerequisites.sh*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-tasks/SKILL.md` (or `../skills/speckit-tasks/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete task generation workflow.
