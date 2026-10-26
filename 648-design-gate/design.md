# Brainstorm holds until the software design question is answered

## Problem Statement

How might we make every branch answer the level-3 question, whether the change
makes a structural choice worth recording, before it leaves brainstorm?

Today brainstorm holds a branch until the level-2 boundary question is answered,
with a record or `wfctl arch none`. Nothing holds it on level 3. An agent can
skip the software design pass entirely, or answer it with a file layout, and the
pipeline moves on either way. That's how the #635 agent answered level 3 with a
folder name rather than a structural choice.

## Recommended Direction

Brainstorm gains a third pass, `software-design`, between `architecture` and
`design-doc`. The pass reads `done` when the branch commits a record under
`docs/architecture/design/`. When the change makes no structural choice, the
user claims the pass with `wfctl step none brainstorm.software-design --reason
"<why>"`, which already works on any pass wfctl ships. A claimed pass is hidden
like any other claimed pass.

When the pass is held, `wfctl status` shows the row as `no software design
record for this change`, and prints both answers under `next:`:

```
  Either record the structural choice this change makes — one file under:
      docs/architecture/design/
  or state that it makes none:
      wfctl step none brainstorm.software-design --reason "<why>"
```

`wfctl status --all` shows a claimed pass as `claimed: <reason>`. A branch that
already has `spec.md` isn't held, which is the same escape the architecture
pass uses. The name column widens to fit the longest pass name, which also fixes
`plan-walkthrough` running into its glyph.

The skills change with it. `design-levels` rewords level 3's Form column to lead
with which module owns the logic and which pattern fits, and says a file layout
or schema alone doesn't answer it. Today the column leads with "Schemas,
contracts", which is plausibly why the #635 agent answered with a file layout.

## Level answers

1. Level 1 (behavior) was approved as the `wfctl status` output above.
2. Level 2 (architecture) draws no new boundary. The new check sits in Evidence
   and derivation and reads what the Design method produces, which is the same
   relationship the architecture check has (`docs/architecture/domain/wfctl.md`).
   `docs/architecture/declarations/648-design-gate.md` records this.
3. Level 3 (design) has one record, listed below.
4. Level 4 (implementation) follows the existing reader. `brainstorm_software_design`
   goes in `_evidence.py` beside `brainstorm_architecture`. It calls
   `touched_on_this_branch(repo_root, arch / DESIGN_DIR)` and
   `blocks(verdict, "ambient")`, and returns its own `remedy`, the way
   `_judge_drawings` does. `_pipeline._infer_steps` already prefers a pass's
   remedy, so `_design_remedy` stays unchanged.

## Software design decisions

- docs/architecture/design/software-design-none-is-a-claim.md — a branch with no structural choice answers with `wfctl step none`, not a new `wfctl design none` verb

## Key Assumptions to Validate

- [ ] #635 keeps `wfctl step none` as the command that writes claims. If #635
      merges first, its gate ignores `declarations/`, so after the rebase this
      branch runs `arch none` again at the new location.
- [ ] One answer per branch is enough. A branch with two structural choices
      writes two records, and a branch with none writes one claim.
- [ ] The Form column wording is what led the #635 agent to a file layout. The
      test is whether the next level-3 answer names a module and a pattern.

## MVP Scope

In:

1. The `software-design` pass, its reader, and its remedy.
2. The name column fix in `wfctl status`.
3. Skill text: `design-levels` level 3 (the Form column and the `step none`
   answer), `speckit-brainstorm` (the re-entry paragraph covers level 3, and the
   "no record" line names the claim), and `software-design-decisions` where it
   says a choice with no alternative earns no record.
4. Tests for each state: held, released by a record, released by a claim, and
   not held past `spec.md`.
5. A release note, `changes/648.change.md`.

## Not Doing (and Why)

- A new `wfctl design none` verb. It adds a command and a file kind to say what a
  claim already says, and #635 would have to learn about it.
- Tying the check to the domain contexts a change touches. Records don't say
  which context they cover, and branches don't say which contexts they touch.
  That's #649, which also moves the architecture check over.
- The domain model's stricter level-3 rule ("a second module has to honor it").
  It doesn't work in monolithic code, where there's no clear second module. It
  waits on #544, as the #649 comment says.
- Treating a missing record as "no". A branch that never asked and a branch that
  answered "no" would look the same
  (`an-absent-artifact-is-claimed-not-inferred.md`).

## Open Questions

- None blocking. The #635 rebase is the one ordering risk, and the assumption
  above covers it.
