---
disable-model-invocation: true
description: Perform a non-destructive cross-artifact consistency and quality analysis across spec.md, plan.md, and tasks.md after task generation.
allowed-tools: Read Glob Bash(.specify/scripts/bash/check-prerequisites.sh*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-analyze/SKILL.md` (or `../skills/speckit-analyze/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete analysis workflow.
