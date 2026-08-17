---
disable-model-invocation: true
description: Create or update the project constitution from interactive or provided principle inputs, ensuring all dependent templates stay in sync.
handoffs:
  - label: Build Specification
    agent: speckit.specify
    prompt: Implement the feature specification based on the updated constitution. I want to build...
allowed-tools: Read Glob
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-constitution/SKILL.md` (or `../skills/speckit-constitution/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete constitution workflow.
