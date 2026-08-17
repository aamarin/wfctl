---
disable-model-invocation: true
description: Generate a custom checklist for the current feature based on user requirements.
allowed-tools: Read Glob Bash(.specify/scripts/bash/check-prerequisites.sh*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-checklist/SKILL.md` (or `../skills/speckit-checklist/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete checklist workflow.
