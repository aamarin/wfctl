---
disable-model-invocation: true
description: End a development session — summarize the work, close wfctl state, and surface anything uncommitted.
allowed-tools: Read Write Bash(date*) Bash(git status*) Bash(git log*) Bash(git diff*) Bash(git symbolic-ref*) Bash(git rev-parse*) Bash(wfctl end*) Bash(wfctl status*) Bash(wfctl state-dir*) Bash(wfctl issue view*) Bash(wfctl issue close*) Bash(wfctl issue comment*) Bash(wfctl report-action*) Bash(wfctl report-block*) Bash(wfctl feature-paths*)
---

## User Input

```text
$ARGUMENTS
```

The exact input `restart` selects the skill's automatic-restart close; any other
input is a normal end-session.

Read `.agents/skills/end-session/SKILL.md` (or `../skills/end-session/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete session end workflow.
