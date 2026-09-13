---
disable-model-invocation: true
description: Start a brainstorming session. Points at the speckit-brainstorm skill, which wraps design-levels + brainstorming + idea-refine and lands its output in specs/<branch>/design.md for speckit pickup.
handoffs:
  - label: Start Specify
    agent: speckit.specify
    prompt: The design document is ready in specs/<branch>/design.md. Run specify.
    send: true
allowed-tools: Read Glob Write Bash(wfctl feature-paths*) Bash(wfctl status*) Bash(wfctl arch-root*) Bash(wfctl arch check*) Bash(wfctl arch none*) Bash(mkdir*) Bash(git log*) Bash(git add*) Bash(git commit*)
---

Read `.agents/skills/speckit-brainstorm/SKILL.md` (or `../skills/speckit-brainstorm/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete brainstorming workflow. That skill is the layer over `brainstorming` and `idea-refine`; this file states no rule of its own.
