---
description: Build and commit the repository's whole-system threat model, `THREAT_MODEL.md` at the repository root, by running upstream's `threat-model` skill and adding wfctl's opening line and rejected-fixes section.
---

Read `.agents/skills/threat-baseline/SKILL.md` (or `../skills/threat-baseline/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete workflow.

Don't run `wfctl step none brainstorm.threat-baseline`, even when `wfctl status` prints it as a remedy. Deciding the pass doesn't apply is the user's decision, not yours.
