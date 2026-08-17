---
disable-model-invocation: true
description: Create or update the feature specification from a natural language feature description.
handoffs:
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
  - label: Clarify Spec Requirements
    agent: speckit.clarify
    prompt: Clarify specification requirements
    send: true
allowed-tools: Read Glob Bash(wfctl status*) Bash(wfctl issue view*) Bash(git branch --show-current*)
---

Read `.agents/skills/speckit-specify/SKILL.md` (or `../skills/speckit-specify/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete specify workflow.
