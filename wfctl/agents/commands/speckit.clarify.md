---
disable-model-invocation: true
description: Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec.
handoffs:
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
allowed-tools: Read Glob Bash(.specify/scripts/bash/check-prerequisites.sh*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-clarify/SKILL.md` (or `../skills/speckit-clarify/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete clarification workflow.
