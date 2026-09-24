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

Read `.agents/skills/speckit-specify/SKILL.md` (or `../skills/speckit-specify/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete specify workflow, and come back here: the two sections below
are wfctl's over it, and the second is the step's only exit.

## When no description was typed

The skill takes the text typed after the command as the feature description,
and its step 5.1 stops on an empty one. Entered from `EXECUTE_COMMAND` there is
no such text — `speckit-orchestrate` emits the bare command — so an unattended
run would stop at the first line it reads, with brainstorm's work sitting
unused (#473). When nothing was typed, `design.md` is the description: the
skill already treats it as "the canonical handoff contract", and brainstorm is
the step that wrote it. Where there is no `design.md` either, the step has
nothing to specify from and stops, as the skill says.

## When the spec is written

**Pipeline**: invoke `speckit-orchestrate`.

The skill has no exit of its own. It is derived from spec-kit, whose `handoffs:`
above are buttons offered to a person who typed this command, and an agent that
entered the step from `EXECUTE_COMMAND` sees no button. Without this line an
unattended run writes `spec.md` and stops there, one step past brainstorm, with
nothing saying the step is over (#473). Here rather than in
`speckit-specify/SKILL.md`, because an edit there is reverted by the next
upstream pull with no conflict to notice.
