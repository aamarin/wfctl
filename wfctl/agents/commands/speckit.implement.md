---
disable-model-invocation: true
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
allowed-tools: Read Glob Bash(.specify/scripts/bash/check-prerequisites.sh*) Bash(git rev-parse*) Bash(wfctl feature-paths*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-implement/SKILL.md` (or `../skills/speckit-implement/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete implementation workflow.

## Read this feature's design records

Follow `.agents/skills/reading-design-records/SKILL.md` (or
`../skills/reading-design-records/SKILL.md` relative to this file, if
`.agents/skills` isn't present). It owns how the list is resolved, the four
states, and how they are reported. What it does not own is when this step reads
them, which is below.

**Before executing the first task**, not while reviewing the last. The records
hold the structural decisions the code is supposed to be written against; a
record read after the code exists describes whatever got built.

**A record is not a task list.** Implementing what a record decided is the tasks'
job; reading it is what keeps a task's implementation faithful to the shape that
was chosen. Do not add work because a record mentions it and `tasks.md` does not
— that is a finding for `/speckit.analyze`, not a licence to widen the change.

