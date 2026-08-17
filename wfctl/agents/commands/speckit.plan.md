---
disable-model-invocation: true
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
handoffs:
  - label: Create Tasks
    agent: speckit.tasks
    prompt: Break the plan into tasks
    send: true
  - label: Create Checklist
    agent: speckit.checklist
    prompt: Create a checklist for the following domain...
allowed-tools: Read Glob
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-plan/SKILL.md` (or `../skills/speckit-plan/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete planning workflow.
