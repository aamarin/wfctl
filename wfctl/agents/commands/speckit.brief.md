---
disable-model-invocation: true
description: Generate a per-task agent brief (specs/<branch>/brief.md) from the active GitHub Issue or JIRA ticket. Scopes this agent to the task with hard stops and escalation criteria.
handoffs:
  - label: Start Working
    agent: init
    prompt: Load context and begin work within brief scope
allowed-tools: Read Glob Write Bash(wfctl issue view*) Bash(wfctl feature-paths*) Bash(mkdir*)
---

Read `.agents/skills/agent-brief/SKILL.md` (or `../skills/agent-brief/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete brief generation workflow.
