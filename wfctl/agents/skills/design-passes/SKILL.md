---
name: design-passes
description: 'Run the design passes on a change that bypasses Spec Kit, such as a bug fix or a copy edit, before any code is written. Asks whether the change needs a spec, reads the accepted records and the domain model, writes a failing test first, and ends with a refactor pass. Use when a handoff says the change does not go through the spec pipeline.'
---

# Design passes

## Overview

Every change runs the design passes. A change that goes through the spec
pipeline runs them in `.agents/skills/design-levels` and `/speckit.implement`.
A change that bypasses the pipeline, such as a bug fix or a copy edit, runs them
here, before any code is written.

This skill has no design method of its own. Each pass calls the skill that
already does that work, so changing a pass means editing one place.

It ends before the PR is opened. `.agents/skills/opening-a-change` takes it from
there, and its template's "Needs a spec?" section repeats the answer from step 1.

## When to use

A handoff's route line sends the change here, or you are about to start coding
a change and no route was stated. If the change is going through the spec
pipeline, run `.agents/skills/design-levels` instead.

## The passes

### 1. Ask whether the change needs a spec

Before touching any code, answer yes or no, and give the reason in one sentence.
Don't write the answer down yet. It goes in the PR's "Needs a spec?" section at
hand-off.

A yes is final. Stop here and run `/speckit.brainstorm`. That command doesn't
send the change back to this skill, so a yes never loops.

wfctl doesn't set where the line between yes and no falls. Each answer gives its
own reason, and the reviewer judges it. A reason like "it's small" says nothing a
reviewer can check, while "it fixes an off-by-one and moves no boundary" does.

### 2. Level 2: records, domain model, and boundaries

Read the decisions in force with `wfctl arch context`, and the domain model under
`domain/` in the folder `wfctl arch-root` prints. A small fix is the change least
likely to check either one, and without this step it can redraw a boundary the
model already settled.

1. If the change alters what a modeled term means, run
   `.agents/skills/model-the-domain` first.
2. Ask whether the change redraws or edits a boundary: who owns a piece of
   truth, a public contract, a data boundary, or a deployment relationship.
   - If it does, run `.agents/skills/architecture-design`, which hands a
     proposed boundary to `.agents/skills/architecture-decisions`.
   - If it stays inside an existing boundary, write nothing. Don't run
     `wfctl arch none` on this route, since the answer in step 1 already
     records that the change needed no spec.

### 3. Level 3: structural choices

If the change makes a structural choice with more than one credible option, such
as a new shape for a function's inputs or a pattern, write a record with
`.agents/skills/software-design-decisions`. A fix with one obvious shape writes
nothing.

### 4. Test first

Commit a failing test before the code that fixes it. For a bug, the test
reproduces the bug. For a copy edit or another change with nothing to run, say so
and move on.

### 5. Refactor

Once the change works, make one behavior-preserving pass over the diff with
`.agents/skills/clean-code`. Add `.agents/skills/python-pattern-selection` when a
pattern name comes to mind. Each refactor is its own commit, so a reviewer can
see that behavior didn't change. If there is nothing to refactor, say that.

### 6. Hand off

Open the change with `.agents/skills/opening-a-change`. The "Needs a spec?"
section repeats the answer from step 1, and `wfctl check-body` fails a body that
leaves it empty, writes N/A, or gives a yes or no with no reason.

## Verification

- [ ] The spec question was answered, with a reason, before any code was edited.
- [ ] A yes went to `/speckit.brainstorm` and ran none of the passes below.
- [ ] `wfctl arch context` and the domain model were read before step 2 decided
      anything.
- [ ] A change inside an existing boundary wrote no file under the arch root.
- [ ] The failing test was committed before the fix.
