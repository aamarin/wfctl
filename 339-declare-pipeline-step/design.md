# A repository declares a pipeline sub-step

**Issue:** #339 · **Branch:** `339-declare-pipeline-step`

## The problem

wfctl walks a feature through eight steps and tells the agent which one is next.
That list is fixed, so a repository whose process has a stage of its own can only
write that stage down in prose and hope somebody reads it.

pfms has exactly this. `pfms-ui-design-workflow` is a committed skill whose
SKILL.md says to run it between brainstorming and `speckit.specify`. Nothing
reads that sentence — `wfctl status` shows the same eight rows it shows every
repository, and a feature that walked past the UI design looks identical to one
that ran it.

The same gap exists inside wfctl, which is what makes this worth fixing properly
rather than accommodating. `brainstorm` is not one pass: it runs the four design
levels, escalates ownership questions to `architecture-decisions`, and ends with
`idea-refine` writing this document. Two of those leave artifacts the brainstorm
predicate already reads, and it collapses both into one state with a sentence
hung off it. A reader is told the step is unfinished and which single thing is
outstanding; nothing tells them how many passes the step has or which command
produces the missing one.

So the pipeline's structure is one level shallower than the work it tracks.

## What changes for the user

A step's passes become rows of their own, indented under it.

```
$ wfctl status
brainstorm          ▶
  architecture      ●   620-money-polarity-owned-by-types.md
  design            ●   620-money-polarity-owned-by-types.md
  ui-design         ○  ← current
                        run /pfms-ui-design-workflow, or
                        wfctl step none ui-design --reason "<why>"
specify             ○
```

A pass that does not apply to this branch is declared away, and the row then
carries the sentence somebody wrote:

```
$ wfctl step none ui-design --reason "backend-only; no screens change"
✓ Recorded: ui-design does not apply — "backend-only; no screens change"
```

Settled-away rows are hidden by default, so the ordinary view stays short, and
`--all` brings them back:

```
$ wfctl status                     # ui-design is declared away, so it is gone
brainstorm          ▶
  architecture      ●   620-money-polarity-owned-by-types.md
  design            ●   620-money-polarity-owned-by-types.md
specify             ○

$ wfctl status --all
brainstorm          ▶
  architecture      ●   620-money-polarity-owned-by-types.md
  design            ●   620-money-polarity-owned-by-types.md
  ui-design         –   backend-only; no screens change
specify             ○
```

Only `skipped` collapses. A pass still to run, running, or finished stays on
screen, and a pass that is holding the pipeline shows whatever flags were passed
— otherwise the step would report itself unfinished with no visible reason and
`next:` would name a command whose row you could not see.

`--json` is unaffected and always carries the full tree.

## How a repository declares one

In `wfctl.json`, keyed by the built-in step the pass belongs inside:

```json
{
  "steps": {
    "brainstorm": [
      { "command": "/pfms-ui-design-workflow", "evidence": "design/ui-contract.md" }
    ]
  }
}
```

The key is the anchor, so nothing declares a position and nothing breaks if the
step table is reordered. The value is an array, so more than one pass is free and
their order is the order written.

wfctl's own passes are sub-steps of the same shape, hardcoded rather than
configured. Nothing in a sub-step marks it as belonging to a repository, so
moving a built-in pass into configuration later changes where the list comes from
rather than what a sub-step is.

A pass earns a row only if it leaves an artifact somebody can point at.
`architecture-design` leaves none — it hands its result to
`architecture-decisions` and writes nothing itself — so it stays what it is: how
you do a sub-step, not a sub-step.

## Where a claimed absence is written

One file per claim, not one file holding several:

```
<arch-root>/declarations/<branch>.md          the boundary claim — wfctl arch none
<arch-root>/step-claims/<branch>/<sub-step>.md        wfctl step none <sub-step>
```

Nothing parses a declaration, so the format was never the constraint. The
constraint is the write mode. `arch none` overwrites its file whole, and says
why: one change makes one claim, and a branch that declares twice has changed
its mind. A branch can declare several *sub-steps* inapplicable without having
changed its mind about any of them — those are different claims, not a revised
one — so a single file that gets overwritten loses every claim but the last.
One file per claim keeps the overwrite rule intact and reads it per sub-step,
where it is still true, and it means `step none` never reads back its own
output.

A separate subtree, and not a child of `declarations/`, because the design gate
counts what it finds. That gate asks one question — did this branch touch
anything under the arch root, excluding `scans/`, `implementation/` and
`design/` — and never opens the file. So a sub-step claim written under
`declarations/` would answer the boundary question the branch never put, and
the sub-steps furthest from that question are the ones most able to answer it:
`python-pattern-selection` sits under `implement`, four levels below where a
boundary is drawn, and a branch declaring it inapplicable would clear the
level-2 gate. That is the failure `non_record_subtrees` exists to stop, met from
a new direction, so the repair is the one already in place:
`step-claims/` joins that list, and the gate goes on counting only the
corners of the arch root where something was decided.

## Architecture decisions

Both were written during this pass and are committed on the branch as `proposed`.

- `docs/architecture/a-step-carries-sub-steps-one-level-deep.md` — a step's
  payload carries an ordered list of sub-steps, each holding a predicate as
  `Step` already does, nested exactly one level deep
- `docs/architecture/an-absent-artifact-is-claimed-not-inferred.md` — when a
  sub-step's artifact is missing, a person says whether the pass ran and produced
  nothing or never ran, and that claim is committed to the change under review

## Software design decisions

No level-3 record was written. Every structural choice that weighed a credible
alternative here was a choice about who owns a piece of truth or about the
contract between a repository and wfctl, so each one landed in a level-2 record
instead — the two named in the section above, which are level-2 and bind as
level-2. The closest thing to a level-3 choice was whether a sub-step holds an
evidence path or a predicate, and that is recorded as a considered alternative
inside the first of those records rather than as a decision of its own, because
the path form cannot express wfctl's existing passes and so was never a credible
structure.

## Checked, and still assumed

Verified against the code during this pass:

- `specs/` is gitignored, so `design.md` reaches no reviewer — which is why the
  declared-inapplicable claim could not live here, as #339 first proposed
- `brainstorm` reads `design.md` before it reads the architecture record, which
  is the reverse of the order both `design-levels` and the brainstorm skill
  produce them in; ordering the rows correctly means fixing that read
- `wfctl arch none` already writes a committed declaration and refuses an empty
  reason, refuses a `<why>` placeholder, and warns when the file landed somewhere
  no reviewer will see it
- every consumer of the pipeline payload lives in `cli.py`, so the views this
  change touches are contained
- `clarify` has no artifact of its own; its evidence is a heading inside
  `spec.md`, which is why a sub-step holds a predicate rather than a path

Corrected during the pass, having first been asserted:

- `doctor` does **not** already hold the command inventory it would need to
  report a declared command that is not installed. That inventory is read by the
  test suite, and a test in wfctl's own suite cannot reach a command that ships
  from the consuming repository. `doctor` does walk the installed command
  directories, so the check is buildable — as new logic, not as wiring

Settled against the code after the pass, having been listed here as assumed:

- `speckit-orchestrate` needs no change to its own contract. It reads
  `next_command`, `auto`, `stall`, `reason` and `remedy` off the payload and
  never enumerates `steps[]`, and it treats `next_command` as opaque — it strips
  the leading `/` and emits it. A sub-step is another value that field can take.
  What does change is where `next_step_content` finds the row carrying
  `continuation`: today it is `_STEPS` alone, and `auto` is computed from that
  lookup.
- the tests can be updated. Exactly one assertion in the suite pins
  `current == "brainstorm"`; the rest read a named step's state out of a mapping,
  which adding rows does not disturb. `pipeline_payload_snapshot.json` is the one
  file a new row rewrites wholesale, and its own docstring already names updating
  it as how a deliberate change in verdict is declared.

## Scope

A repository declares sub-steps under a built-in step; wfctl's own brainstorm
passes become sub-steps of the same kind; `wfctl step none` generalises
`wfctl arch none`; `status` gains `--all`. A repo-declared sub-step is
`review_required` unless the repository opts into `automatic`, because wfctl does
not ship the command.

Out of scope: replacing or overriding a built-in step, a general hook mechanism
for review or PR stages, nesting beyond one level, and whether the eight step
names are the ones we want — that last is #395.

## Open questions for planning

- What `doctor` reports for a declared sub-step whose command is not installed,
  and whether that is a finding or a warning
- Whether `python-pattern-selection` should always write its departure to a file
  when a repository tracks it as a sub-step, which is a change to that skill
  rather than to this design
