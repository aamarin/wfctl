---
disable-model-invocation: true
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
allowed-tools: Read Glob Bash(.specify/scripts/bash/check-prerequisites.sh*) Bash(git rev-parse*) Bash(wfctl feature-paths*) Bash(wfctl arch context*) Bash(wfctl arch-root*) Bash(wfctl report-block*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-implement/SKILL.md` (or `../skills/speckit-implement/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete implementation workflow.

## Read this feature's design records

Follow `.agents/skills/reading-design-records/SKILL.md` (or
`../skills/reading-design-records/SKILL.md` relative to this file, if
`.agents/skills` isn't present). It owns how the list is resolved, the four
states, and how they are reported. What it does not own is when this step reads
them, which is below.

**Before executing the first task**, not while reviewing the last. The records
hold the structural decisions the code is supposed to be written against; a
record read after the code exists describes whatever got built.

**A record is not a task list.** Implementing what a record decided is the tasks'
job; reading it is what keeps a task's implementation faithful to the shape that
was chosen. Do not add work because a record mentions it and `tasks.md` does not
— that is a finding for `/speckit.analyze`, not a licence to widen the change.

## Report a host refusal, whichever task hits it

Here rather than in `speckit-implement/SKILL.md` (#364): that file is
spec-kit-derived, and an in-place edit is reverted by the next upstream pull
with no conflict to notice — the same reason `reading-design-records` above
lives in this wrapper rather than there.

A task that closes an issue, comments, pushes, or opens a PR can be refused by
your own host — Claude Code's auto-mode classifier and its equivalents on
other hosts — before wfctl's own process ever starts. wfctl records nothing in
that case, because there is nothing for it to see: no exit code, no stderr, no
invocation. Report it yourself:

```bash
wfctl report-block <action> --reason "<what your host said>"
```

`<action>` is a short name for what was refused — `issue-<verb>` for a tracker
write (`issue-close`, `issue-comment`), which is the name `wfctl issue` records
when that write succeeds, or `push`. It holds the step this task belonged to, so
`implement` reports unfinished rather than done with a write nobody made. A
later successful `wfctl issue` write lifts the hold by itself; a person who takes
the action outside wfctl lifts it with `wfctl report-action <action>`.

Do not route around the refusal — `gh` directly, or any other client. The host
is the only gate on these actions, and wfctl keeps none of its own.

