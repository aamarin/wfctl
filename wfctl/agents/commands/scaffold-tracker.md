---
disable-model-invocation: true
description: Author an issue-tracker backend for `wfctl issue` / `wfctl change` — generate a `.agents/trackers/<name>.json` (verbs, changes, key_pattern, identity/{me}) for a tracker other than GitHub (Jira, Gerrit, Linear, a custom CLI), then validate it with `wfctl tracker-check`.
---

Read `.agents/skills/scaffold-tracker/SKILL.md` (or `../skills/scaffold-tracker/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete workflow.
