---
disable-model-invocation: true
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
allowed-tools: Read Glob Write Edit Bash(.specify/scripts/bash/check-prerequisites.sh*) Bash(git rev-parse*) Bash(git diff*) Bash(git status*) Bash(wfctl feature-paths*) Bash(wfctl arch context*) Bash(wfctl arch-root*) Bash(wfctl verify*) Bash(wfctl report-block*)
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

## Refactor the finished diff, before it is verified

**Once every task is checked off, and before step 9b's sentinel**, run one
behaviour-preserving pass over the branch's diff. Read
`.agents/skills/clean-code/SKILL.md` (or `../skills/clean-code/SKILL.md`
relative to this file), then follow its routing row for a finished
implementation's diff. Before review, a structural move is part of the change.
After review, it is rework on a reviewed diff.

The front page first, not the reference alone. It carries what the pass works
under and the reference does not restate: accepted records outrank every
heuristic, the priority order that settles a conflict between two goals, and
writing in the target language's own idiom.

Before the sentinel rather than after it, because the sentinel is what `wfctl`
reads as "implement is finished". A run restarted between the two would find
the step done and never come back for the pass. Before 9c, so that
`wfctl verify` judges the tree the pass left rather than the one it started
from. Where the repository declares no narrower check, `wfctl verify` is the
baseline too: run it once before the first move.

This lives here rather than in `speckit-implement/SKILL.md` for the reason
the host-refusal section below gives (#364). It rides inside the step rather than being a
step of its own because nothing downstream can tell whether it ran — review
sees a diff either way — which makes it a method, and
`a-repo-concern-earns-a-step-hook-or-method` keeps methods out of the pipeline.
A pass that selects nothing is a finished pass. Its report still says what it
inspected.

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

