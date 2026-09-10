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
allowed-tools: Read Glob Bash(wfctl feature-paths*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-plan/SKILL.md` (or `../skills/speckit-plan/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete planning workflow.

## Read this feature's design records

Follow `.agents/skills/reading-design-records/SKILL.md` (or
`../skills/reading-design-records/SKILL.md` relative to this file, if
`.agents/skills` isn't present). It owns how the list is resolved, the four
states, and how they are reported. What it does not own is when this step reads
them, which is below.

**Before the workflow's Outline step 3**, and not after. A plan generated first
and checked against the records afterwards is a plan written blind; the records
hold the structural decisions this feature's design pass argued out, and they are
what Phase 1's `data-model.md` and `contracts/` are supposed to be written
against. The skill's Outline step 2 loads `FEATURE_SPEC` and the constitution;
this is a third input.

