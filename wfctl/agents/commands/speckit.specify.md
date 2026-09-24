---
description: Create or update the feature specification from a natural language feature description.
handoffs:
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
  - label: Clarify Spec Requirements
    agent: speckit.clarify
    prompt: Clarify specification requirements
    send: true
allowed-tools: Read Glob Write Edit Bash(wfctl status*) Bash(wfctl issue view*) Bash(git branch --show-current*) Bash(mkdir*)
---

Read `.agents/skills/speckit-specify/SKILL.md` (or `../skills/speckit-specify/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete specify workflow.

## When the spec is written

**Pipeline**: invoke `speckit-orchestrate`.

The skill has no exit of its own. It is derived from spec-kit, whose `handoffs:`
above are buttons offered to a person who typed this command, and an agent that
entered the step from `EXECUTE_COMMAND` sees no button. Without this line an
unattended run writes `spec.md` and stops there, one step past brainstorm, with
nothing saying the step is over (#473). Here rather than in
`speckit-specify/SKILL.md`, because an edit there is reverted by the next
upstream pull with no conflict to notice.
