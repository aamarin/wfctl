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

A handoff's route line sends the change here, `/start-session` finds the spec
question unanswered, or you are about to start coding a change and no route was
stated. Step 1 is where the question gets its answer, so run at least step 1
whenever the branch has no spec folder and no recorded "no". If the change is
already going through the spec pipeline, run `.agents/skills/design-levels`
instead.

## The passes

### 1. Ask whether the change needs a spec

Before touching any code, answer yes or no by checking the change against the
three tests below. The change needs a spec when any one of them holds, and it
needs none only when you checked all three and none holds.

**Test 1: the change alters behavior.** A user sees something new or
different, or the change adds state that persists between runs. Examples are a
new command, flag, or option; output that reads differently; a new file wfctl
writes or reads; a new field in a file or payload; and a new key in
`wfctl.json`. This is level 1 in `.agents/skills/design-levels`, and a spec is
where level 1 gets written down and clarified before anyone builds against it.
Fixing behavior so it matches what is already documented doesn't count, since
the intended behavior is already written down.

**Test 2: the change makes an architecturally significant decision.** Michael
Nygard's test, quoted in Richards and Ford, *Fundamentals of Software
Architecture* (ch. 19, p. 284), names five categories a significant decision
affects:

1. Structure, such as adding, removing, merging, or splitting a component, or
   moving code across a module boundary.
2. Nonfunctional characteristics, such as what has to stay true about safety,
   durability, latency, or recovery under a stated condition.
3. Dependencies, such as adding a dependency, or reversing which side depends on
   which.
4. Interfaces, meaning a published contract and how it is versioned or
   deprecated. A contract is published when it is used by code you can't update
   in the same change (Martin Fowler, "Published Interface"). In wfctl that is
   `wfctl status --json`, a command's flags and output, a file format another
   tool reads, a hook, and anything a consumer repo or another agent parses. A
   private helper's signature is not one, since a rename updates every caller.
5. Construction techniques, such as how the system is built, tested,
   packaged, or released.

A category alone isn't enough. The decision also has to be expensive to
reverse, and each option has to give up something real. Klaus Iglberger (*C++
Software Design*, Guideline 1, quoting Ralph Johnson) defines architecture as
"the aspects of your software that are among the hardest things to change in
the future", and Ford, Parsons, Kua, and Sadalage (*Building Evolutionary
Architectures*, ch. 1) add that "each choice offers significant trade-offs". A
change that is in a category and cheap to undo, such as one more pytest marker
or a CI step you could revert in one commit, fails this test.

**Test 3: the change moves ownership.** Which side computes a value, holds a
piece of truth, or owns an abstraction changes. Iglberger (Guideline 9) calls
moving an abstraction to the other side "a reassignment of ownership", because
the side that owns an abstraction is the one every other part depends on. Having
the worktree guard read a file it didn't read before, or moving a decision from
the agent to wfctl, are both examples.

Size isn't a test. A two-line change can move ownership, and a thousand-line
change can stay inside one module. "It's small" or "it's a bug fix" is not a
reason.

A change that holds none of the three can still make a design choice, such as
how two functions depend on each other or whether to use a pattern like
Strategy. Iglberger places that choice at the design level rather than the
architecture level, so step 3 below records it, and it doesn't need a spec.

The reason names the tests. The sources draw the line differently: Iglberger by
size, Nygard by what a decision affects, and `design-levels` by how expensive it
is to reverse. So the answer says which test decided it, and a reviewer can
check that test against the diff:

- A yes names the test that holds and what in the change makes it hold: "Test
  1: adds a `review` step to `wfctl status`".
- A no says why each test fails: "Test 1: the output already documents this
  case and the code didn't match it. Test 2: one function, no category. Test 3:
  no value changes owner."

**When the answer is yes,** stop here and run `/speckit.brainstorm`. That
command doesn't send the change back to this skill, so a yes never loops. A yes
writes no file, since the spec steps the branch runs are the evidence for it.

**When the answer is no,** record it before any code, so `wfctl status` skips
the spec steps and points the branch at implement and review. The command writes
the reason to the branch's spec folder:

```bash
wfctl spec none --reason "Test 1: … Test 2: … Test 3: …"
```

Copy the same reason into the PR's "Needs a spec?" section at hand-off.

**When a later pass finds that a test holds,** the answer changes to yes. This
usually happens in step 2, when a boundary turns out to move, or while writing
the code. Delete the file `wfctl spec none` wrote, which `wfctl status` names,
and run `/speckit.brainstorm`. Richards and Ford (ch. 2) say architecture and
design have to stay in sync, so a finding at a lower level reopens the higher
one rather than being worked around in the code.

### 2. Level 2: records, domain model, and boundaries

Read the decisions in force with `wfctl arch context`, and the domain model under
`domain/` in the folder `wfctl arch-root` prints. A small fix is the change least
likely to check either one, and without this step it can redraw a boundary the
model already settled.

1. If the change alters what a modeled term means, run
   `.agents/skills/model-the-domain` first.
2. Check step 1's tests 2 and 3 against what you just read: whether the change
   redraws or edits a boundary, such as who owns a piece of truth, a published
   contract, a data boundary, or a deployment relationship.
   - If it does, the answer to step 1 is now yes. Follow step 1's "When a later
     pass finds that a test holds".
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

- [ ] The spec question was answered before any code was edited, and the reason
      names each of the three tests.
- [ ] A no was recorded with `wfctl spec none` before any code, and the PR's
      "Needs a spec?" section carries the same reason.
- [ ] A yes went to `/speckit.brainstorm` and ran none of the passes below.
- [ ] A test found to hold after the answer was no deleted the `wfctl spec none`
      file and went to `/speckit.brainstorm`.
- [ ] `wfctl arch context` and the domain model were read before step 2 decided
      anything.
- [ ] A change inside an existing boundary wrote no file under the arch root.
- [ ] The failing test was committed before the fix.
