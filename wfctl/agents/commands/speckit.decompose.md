---
description: Delivery decomposition for a speckit feature. Analyzes tasks.md to determine PR boundaries, group tasks into tracker issues, and map parallelization waves. Writes delivery.md, and creates the issues the plan promises. Replaces /speckit.taskstoissues as the default terminus for features.
handoffs:
  - label: Begin Implementation
    agent: speckit.implement
    prompt: Implement the delivery plan
allowed-tools: Read Glob Write Bash(wfctl status*) Bash(wfctl issue create*) Bash(wfctl report-block*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).
If the user provides a custom grouping instruction (e.g., "group into 2 issues"), honour it.

Read `.agents/skills/speckit-delivery-plan/SKILL.md` (or `../skills/speckit-delivery-plan/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete decompose workflow.

## When `delivery.md` is written

**Pipeline**: invoke `speckit-orchestrate`.

`speckit-delivery-plan` ends at its references and has no exit of its own, and
the `handoffs:` above are a button offered to a person who typed this command.
An agent that entered the step from `EXECUTE_COMMAND` sees no button, so without
this line an unattended run writes `delivery.md` and stops one step short of
`implement` (#473). Here rather than in the skill because the skill is also read
on its own, to write a `delivery.md` outside the pipeline, and there it has no
step to hand off from.
