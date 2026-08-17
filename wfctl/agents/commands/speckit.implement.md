---
disable-model-invocation: true
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
allowed-tools: Read Glob Bash(.specify/scripts/bash/check-prerequisites.sh*) Bash(git rev-parse*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-implement/SKILL.md` (or `../skills/speckit-implement/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete implementation workflow.
