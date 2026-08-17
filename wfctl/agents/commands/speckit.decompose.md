---
disable-model-invocation: true
description: Delivery decomposition for a speckit feature. Analyzes tasks.md to determine PR boundaries, group tasks into GitHub issues, and map parallelization waves. Writes delivery.md and creates GitHub issues using the grouping plan. Replaces /speckit.taskstoissues as the default terminus for features.
handoffs:
  - label: Begin Implementation
    agent: speckit.implement
    prompt: Implement the delivery plan
allowed-tools: Read Glob
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).
If the user provides a custom grouping instruction (e.g., "group into 2 issues"), honour it.

Read `.agents/skills/speckit-delivery-plan/SKILL.md` (or `../skills/speckit-delivery-plan/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete decompose workflow.
