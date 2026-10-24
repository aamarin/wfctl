# Skill contract: `design-passes` and the four places that point to it

## `wfctl/agents/skills/design-passes/SKILL.md` (new)

Frontmatter `name: design-passes`, and a description that names a change
bypassing Spec Kit. The body carries, in order:

1. **The spec question.** Before any code, ask whether the change needs a full
   spec, and answer yes or no with a one-sentence reason. Don't write it
   down yet. It goes in the PR's "Needs a spec?" section at hand-off. If
   yes, stop and route to `/speckit.brainstorm`. That yes is final, and
   brainstorm doesn't send the change back here.
2. **Level 2.** Read `wfctl arch context` and the domain model under
   `<arch-root>/domain/`. A change to what a modeled term means goes to
   `.agents/skills/model-the-domain` first. Then ask whether the change redraws
   or edits a boundary. Inside an existing boundary, write nothing, and don't
   run `wfctl arch none`. Redrawing or editing one goes to
   `.agents/skills/architecture-design`.
3. **Level 3.** A structural choice with more than one credible option gets a
   record from `.agents/skills/software-design-decisions`.
4. **Test first.** Commit a failing test, then the code.
5. **Refactor.** A behavior-preserving pass with `.agents/skills/clean-code`,
   plus `.agents/skills/python-pattern-selection` when a pattern name comes up.
   Each refactor is its own commit, or there's nothing to refactor.
6. **Hand-off.** The skill ends before the PR. `opening-a-change` takes it from
   there, and its template's "Needs a spec?" section repeats the answer.

The skill names Andre's spec-line criterion as not settled yet: each answer
gives its own reason, and the reviewer judges it.

## The four places

Each place names the skill by its full path, `.agents/skills/design-passes`.
The path is what the cross-reference tests look for, and it also brings each
line under `test_every_referenced_skill_ships`.

| File | Today | After |
| --- | --- | --- |
| `wfctl/agents/skills/worktree-handoff/SKILL.md`, item 3, "Which route this work takes" | opens "Straight to implementation, or through the spec pipeline", and ends "a bug fix or a copy edit does not" go through the pipeline | opens "Through `.agents/skills/design-passes`, or through the spec pipeline", and ends "A bug fix or a copy edit runs `.agents/skills/design-passes` before any code is written. That skill decides whether the change needs a spec." |
| `wfctl/agents/skills/design-levels/SKILL.md:22-24` | "Not for: bug fixes, copy edits and other trivial changes …" | see the routing section below |
| `wfctl/agents/skills/architecture-design/SKILL.md:46-50` | "bug fixes, copy edits, dependency bumps, naming, refactors that move no boundary … go straight to implementation" | see the routing section below |
| `AGENTS.md:391` | "Not every change needs the spec pipeline …" | the same, plus "Every change runs the design passes, either through the pipeline or through `.agents/skills/design-passes`." |

## Routing between the skills

A bug fix can reach four skills from `design-passes`, and each one currently
opens its "Not for" line with a list of change kinds, such as "bug fixes, copy
edits":

1. `architecture-design`, for a fix that moves a boundary.
2. `model-the-domain`, for a fix that changes what a modeled term means.
3. `architecture-decisions`, where `architecture-design` hands every proposed
   boundary.
4. `design-levels`, which brainstorm runs for a fix `design-passes` answered
   "needs a spec" for.

So a bug fix is sent to a skill that says it isn't for bug fixes. Once that
line points at `design-passes`, the agent is sent back to where it started,
and it can bounce between the two.

No counter stops this loop, so the wording has to. wfctl's attempt cap counts
pipeline steps, one per `wfctl resume`. A bounce between two skills inside one
conversation never reaches it, and `design-passes` isn't a pipeline step.

The fix is to key all four "Not for" lines on whether a boundary moves or a
term changes meaning, not on the kind of change. The kinds stay in the line as
examples of what usually moves nothing. `design-levels` already uses this test
at level 2 ("whether a boundary moves, not how large the change is"). Its own
"Not for" line also says that a change `design-passes` sent to brainstorm stays
there, since the spec question was already answered yes.

Each method is called from two places: `design-levels` level 2 on the Spec Kit
route, and `design-passes` level 2 outside it. So a change the method skips
goes on to level 3 of whichever skill sent it, and the method doesn't name a
next step of its own. Only a change that arrived from neither, such as a fix an
agent is about to start coding, is sent to `design-passes`.

### `architecture-design/SKILL.md:46-50`

```markdown
**Not for**: a change that moves no boundary, whatever its kind or size. Most
bug fixes, copy edits, dependency bumps, renames, and refactors are like that.
Such a change skips this method and goes on to level 3 of the skill that sent
it here, either `design-levels` or `.agents/skills/design-passes`. A change
that came from neither starts at `.agents/skills/design-passes`. A bug fix that
does move a boundary belongs here. Nor for work whose boundaries are already
settled in an accepted record or an existing spec.
```

### `model-the-domain/SKILL.md:125-129`

```markdown
**Not for**: a change that leaves every modeled term meaning what it did and
moves no boundary, whatever its kind or size. Such a change skips this method
and goes on to level 3 of the skill that sent it here. A bug fix that changes
what a modeled term means belongs here, and `.agents/skills/design-passes`
sends one. Not for work whose language and boundaries an accepted record or
spec already settles. Not for a capability the table above leaves in the right
column. Not for quality drivers, which go to `architecture-design`. Not for how
code expresses a settled model, which is `.agents/skills/clean-code`.
```

### `architecture-decisions/SKILL.md:29-31`

```markdown
**Not for**: a change that moves no boundary, whatever its kind. Most bug
fixes, refactors, renames, style changes, and library version bumps are like
that, and so is anything a code comment already carries. A record per change
is a changelog, and nobody reads a changelog to find a constraint. A bug fix
that moves a boundary does get a record, and `.agents/skills/architecture-design`
sends it here.
```

Neither `model-the-domain` nor `architecture-decisions` is one of the four
places, since neither line ever sent a change to implementation. They change
only so the route from `design-passes` has no dead end.

### `design-levels/SKILL.md:22-24`

```markdown
Not for: a change that adds no new state or user-visible behavior and moves no
boundary, whatever its kind. Most bug fixes and copy edits are like that. They
skip the four levels here, not the design passes, and go to
`.agents/skills/design-passes`. Nor for work whose behavior and boundaries are
already settled in an existing spec. A change that `.agents/skills/design-passes`
sent here was already answered "needs a spec", so it runs the four levels here
even when it's a bug fix, and isn't sent back.
```

### `design-levels/SKILL.md:174-177`

Level 2's exit says "either method's own **Not for** list is the exit a
trivial change takes". After the edit, `architecture-design`'s line names
`design-passes`, and an agent on the Spec Kit route could read that as a
reason to leave brainstorm. The paragraph says where the exit leads:

```markdown
Skip the method when an accepted record or an existing spec already settles the
boundary, naming the one that does, or when the change moves no boundary at all.
The test is whether a boundary moves, not how large the change is. A skipped
method sends the change on to level 3 here, which is what its **Not for** line
says too.
```

## `fanning-out-code-review` Step 2

Nothing checks that `design-passes` asked the spec question before any code.
An agent that skipped it can still answer "No" when the PR opens, and
`check-body` passes it. The panel runs before the description is written, so a
reviewer can't compare the diff with the PR's answer. Instead, each reviewer
reports what the diff decides, and the author writes the answer after reading
those findings. The author still decides what to do with each one. In an
attended run, the person sees the findings in the panel's table before the PR
opens. In an unattended run nobody reads the table, so a finding the author
dismisses stays in the reviewer's report.

The list of bullets every dispatch carries gains a fifth, and "these four"
becomes "these five":

```markdown
- **Report any design decision the diff makes that nothing on the change
  covers:** new stored state, a new file or setting the code reads, a new
  command or flag, or a boundary drawn or moved. A record or spec the change
  names covers it; the change calling itself a bug fix doesn't. Nothing checks
  that the author asked whether the change needs a spec before writing code,
  and an agent that skipped the question can still answer "No" when the PR
  opens. A reviewer that reads only the diff is the first reader who didn't
  write it.
```

`fanning-out-code-review` is wfctl's own skill, not one derived from upstream,
so an in-place edit stays. `opening-a-change` isn't edited (FR-013).

## `design-levels` level 2

Its first step reads the accepted records and the domain model before choosing
a method, in the same wording `design-passes` uses, and sends a change to a
modeled term's meaning to `model-the-domain` first.
