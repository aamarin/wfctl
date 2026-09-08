---
disable-model-invocation: true
description: Start a brainstorming session. Wraps the design-levels + brainstorming + idea-refine skills, whose output lands in specs/<branch>/design.md for speckit pickup.
handoffs:
  - label: Start Specify
    agent: speckit.specify
    prompt: The design document is ready in specs/<branch>/design.md. Run specify.
    send: true
allowed-tools: Read Glob Write Bash(wfctl feature-paths*) Bash(wfctl status*) Bash(wfctl arch-root*) Bash(wfctl arch check*) Bash(mkdir*) Bash(git log*) Bash(git add*) Bash(git commit*)
---

Read `AGENTS.md` at the repository root for project overrides. It is optional —
if the file is absent, proceed silently. Then invoke the `design-levels` skill —
it governs which level each question gets answered at, and its gates run
throughout — and follow the `brainstorming` skill exactly.

Read which mode this feature is in before the first gate:

```bash
wfctl status --json      # read `auto_approve`
```

`false` is the default and today's behaviour: every pause below happens as
written. Treat any other answer — the key absent, the command failing, an older
wfctl — as `false`; the mode is the thing that removes a human, so an
inconclusive read has to leave one in.

`true` moves where the approval happens, and this command is where that override
is stated. `brainstorming` and `idea-refine` are upstream-derived and stay
unedited (`vendor-upstream-skills`, accepted: *"Prefer layering to editing"*), so
they still read as unconditional and this file is the layer above them. Four
pauses, all of them theirs, none of them wrong to have been written that way:

| Where it pauses | Under `auto_approve: true` |
|---|---|
| `brainstorming`'s HARD-GATE — no implementation "until the user has approved it" | The design is still presented, at every level, and still not skipped. What changes is who approves: each gate's answer goes into its record and the reviewer approves at the PR. Descending is not "taking implementation action" — the HARD-GATE's subject is code, and it still binds. |
| Step 3, one clarifying question at a time | Answer them yourself from the codebase and the tracker, and write each answer *and its basis* into the design. A question decided silently is the failure this step exists to prevent, and nobody being there to ask does not make it acceptable. |
| Step 5, approval after each level, and the two human diamonds in the `dot` flow | State the gate's answer in the form `design-levels` gives it, into the record, and descend. The flow's diamonds resolve to "yes" — they are not skipped. |
| Step 7 and the User Review Gate; `idea-refine`'s "Only save if they confirm" | Do not wait. Say which mode you are in, in one line, and write `design.md`. This is the pause that would otherwise strand the whole mode: an auto-approving run that stops here has done all the work and produced none of the artifact the reviewer was going to read. |

**None of this waives a record.** An auto-approving pass documents more than an
attended one, not less — every gate is still answered out loud, in its rendered
form, because those answers are what generate the level-3 requirements. A record
whose `Considered` is empty has skipped its gate more quietly, not passed it.
`wfctl`'s design gate holds a design step that produced no record — in both
modes, and it is unchanged by this file. It reports through the pipeline rather
than refusing the command: the step reads `in_progress` with the reason on it,
and `status`, `next` and `resume` all say so. Under `auto_approve` that is the
same stop it always was, arriving as state rather than as an exit code.

**Records land `proposed`.** An agent never writes `approved` — that transition
is a human's, and it is what makes "come back and change this later" real rather
than a re-litigation. Do not paraphrase the mode as approval you were given.

Create the destination directory:

```bash
wfctl feature-paths      # prints FEATURE_DIR='…/specs/<current-branch>'
```

Read `FEATURE_DIR` from that output and `mkdir -p` it. Substitute the real path —
`<branch>` in this file is a placeholder, never a directory name. The design
document is `design.md` inside that directory.

Level-3 records are written before `idea-refine` runs, not after. Invoke
`software-design-decisions` for each structural choice that weighed a credible
alternative, once level 2's records are written and while the reasoning is still
in front of you. The order is what makes the next paragraph possible: `design.md`
lists the records by path, so they have to exist before the file that points at
them.

The records land where that skill sends them and are committed there, which is
outside `FEATURE_DIR` on purpose — `specs/` is gitignored, so a record kept
beside `design.md` reaches no reviewer. That skill owns the check that it
actually landed.

Committing them here puts a record on the branch before step 7's review gate has
approved the direction. That is the intended order and not an oversight: records
land `proposed`, which is the status for a decision nobody has ratified, and a
direction the reader rejects leaves behind the argument for why it was
considered. A record is superseded by a later one rather than deleted.

After the brainstorming session concludes, invoke the `idea-refine` skill to
sharpen the chosen direction into an actionable one-pager. Its one-pager gains a
section `idea-refine` does not itself carry:

```markdown
## Software design decisions

- <arch-root>/design/<issue>-<decision>.md — <the decision in one line>
```

`wfctl arch-root` prints that root. Writing the default in is the assumption this
feature exists to remove: a repo can declare `arch_root` elsewhere, and a
one-pager naming a path no record was written to points at nothing.

Paths, never blocks. A digest of a record is a second copy of it, and the copy is
what drifts. Where a level was answered with no record, the section says so in
one line rather than being deleted — a missing section reads as a level nobody
ran.

Stated here rather than in `idea-refine` because that skill is upstream-derived
and fires outside this pipeline as often as inside it (`vendor-upstream-skills`),
and a one-pager written for someone with no `arch-root` has nothing to list.

**Output:** `specs/<branch>/design.md`, written by `idea-refine` — once, at final
fidelity. `brainstorming` carries its approved design here in context rather than
saving it first; a second write to that path destroys the approved design.
`/speckit.specify` reads the file from there.
