# Design exceptions move to the spec folder

## Problem Statement

How might we keep a branch's "this design step doesn't apply" answers where the pipeline and the reviewer can read them, without adding a file to `docs/architecture/` for every branch that gives one?

A design exception is a branch's statement, with a reason, that a design step doesn't apply to it. Today two commands write them into the architecture folder:

1. `wfctl arch none --reason "…"` writes `declarations/<branch>.md`, saying the branch drew no new boundary.
2. `wfctl step none <step>.<pass> --reason "…"` writes `step-claims/<branch>/<step>.<pass>.md`, saying a pass the repo declared doesn't apply.

On 2026-10-25 the folder held 15 declarations and 5 step claims, all from branches that had already merged. Each one describes a single change, not the system, so a reader looking for the system's architecture has to skip past them.

## Recommended Direction

The spec folder holds each branch's design exceptions, and the PR body carries them to the reviewer. The pipeline reads them from the spec folder because the brainstorm gate runs before any PR exists. The reviewer reads them in the PR body because the spec folder is gitignored and, in this repo, outside the working tree. The architecture folder holds neither copy.

Both kinds of exception go in one `exceptions/` folder inside the spec folder, one file per exception. One small module, `wfctl/_design_exceptions.py`, owns that folder. The two commands that write exceptions and the two readers that check them all call it, so the path and the file format are defined once.

The PR body gets a "Moves a boundary?" section. Every PR answers it yes or no with a reason, the same way it answers "Needs a spec?", and lists any pass exceptions under it. This repo makes the section required by adding it to `change_sections` in `wfctl.json`, and wfctl doesn't name the heading itself.

## Behavior (level 1)

A branch `700-fix-help-typo` is a one-line fix with no new boundary, and the repo's `ui-design` pass doesn't apply to it. The agent runs:

```
wfctl arch none --reason "Copy fix in one help string; nothing moves"
wfctl step none brainstorm.ui-design --reason "No screen changes"
```

The two answers land here:

| | Today | After this change |
|---|---|---|
| "No new boundary" | `docs/architecture/declarations/700-fix-help-typo.md` | `<spec folder>/700-fix-help-typo/exceptions/boundary.md` |
| "ui-design doesn't apply" | `docs/architecture/step-claims/700-fix-help-typo/brainstorm.ui-design.md` | `<spec folder>/700-fix-help-typo/exceptions/brainstorm.ui-design.md` |
| Committed with the PR? | Yes, both files land in the diff | No, both are stored on `specs-trunk` with `design.md` |

The reviewer sees the answer in the PR body:

```markdown
## Moves a boundary?

No. Copy fix in one help string; nothing moves.

- brainstorm.ui-design doesn't apply: no screen changes.
```

Each reachable state, with the string it prints and whether that string is true in that state:

```
arch none, with a reason
  ✓ Recorded: no boundary changed — "Copy fix in one help string; nothing moves"
    Put the reason in the PR body.
  True. The exception is in the spec folder, and the reviewer's copy is still to be written.

step none, with a reason
  ✓ Recorded: brainstorm.ui-design does not apply — "No screen changes"
    Put the reason in the PR body.
  True, for the same reason.

arch none or step none, with an empty or <why> reason
  ✗ --reason cannot be empty: …   /   ✗ "<why>" is a placeholder, not a reason — …
  True and unchanged.

step none, on a pass the repo doesn't declare
  ✗ x.y is not a declared pass. Under x: …
  True and unchanged.

arch none or step none, where the file would not be in the PR diff
  (today) ⚠ Wrote …, but it is not part of the change under review …
  Removed. The file is never in the diff now, so the warning would fire on every run and say nothing.

brainstorm, with design.md and no answer to the boundary question
  ▶ no architecture record for this change
  True and unchanged. The boundary exception and a record both release it.

brainstorm, on a branch carrying a declaration written by an older wfctl
  ▶ no architecture record for this change
  True. `declarations/` joins the subtrees the gate ignores, so an old file
  doesn't satisfy it and the folder doesn't start filling up again.

check-body, on a PR with no "Moves a boundary?" section, in a repo that lists it
  reports the section missing
  True. In a repo that doesn't list it, nothing is reported, and the reviewer
  loses their copy. That's accepted while wfctl has one user.
```

Level-3 consequences of these decisions:

1. Removing the not-in-the-diff refusal means `arch none` and `step none` no longer call `touched_on_this_branch`, and `_refuse_unseen` loses its `step none` caller.
2. The commands create the spec folder when it's missing, since `resolve_spec_dir` returns nothing until the folder exists. This is the assumption below.
3. `_paths.non_record_subtrees` gains `declarations/` and drops `step-claims/`. The 5 existing step claims move into their spec folders.

## Architecture (level 2)

The level-2 record settles where design exceptions live and who reads each copy. The person or agent on the branch still decides whether a boundary moved or a pass applies, and writes the reason. This change moves only where the exception is kept.

## Software design decisions

- docs/architecture/design-exceptions-live-with-specs.md — the spec folder and the PR body hold design exceptions, and the architecture folder holds neither
- docs/architecture/design/design-exceptions-module.md — one `_design_exceptions` module of plain functions owns the exceptions folder, its path, and its file format

## Structure (level 3)

What I checked against the code, and what I'm still betting on:

| Checked | Assumed |
|---|---|
| `arch_none_cmd` writes `declarations/<branch>.md` and overwrites on a second run | A spec folder holding only `exceptions/` still reads brainstorm as the current step |
| `step_none_cmd` writes one file per pass, named `<step>.<pass>.md` | #648's "no design decision" exception fits the same one-reason format |
| `_step_claims` globs `*.md` and parses the header `step none` writes | |
| `_step_claims` is called before the no-spec-folder arm in `_pipeline.py` | |
| `_architecture_answered` already takes the spec folder | |
| `resolve_spec_dir` returns a folder only when it exists | |
| The spec store runs `git add -A -- <folder>`, which stages subfolders | |
| `wfctl.json` lists only "Needs a spec?" under `change_sections` | |

## Key Assumptions to Validate

- [ ] A spec folder created by `arch none` before `design.md` exists leaves brainstorm as the current step. Test: run `arch none` on a branch with no spec folder, then read `wfctl status --json`.
- [ ] The pipeline reports exactly the pass exceptions and never `boundary.md` as a pass. Test: `step none` on two passes plus `arch none` once, then check the pipeline's claimed passes.
- [ ] No caller still builds an exception path or parses an exception file outside `_design_exceptions`. Test: grep `cli.py`, `_pipeline.py`, and `_evidence.py`.

## MVP Scope

In:

1. `wfctl/_design_exceptions.py`, and `arch none`, `step none`, the brainstorm gate, and the pipeline's exception reader all calling it.
2. `declarations/` added to `non_record_subtrees`.
3. The not-in-the-diff refusal removed from both commands, and the "Put the reason in the PR body." line added.
4. "Moves a boundary?" added to `wfctl.json`'s `change_sections` and to `.github/pull_request_template.md`.
5. The 15 declarations deleted, and the 5 step claims moved to their spec folders.
6. `_contract.py`'s fixture writing its step claim into the spec folder.
7. Skill text that names the old paths updated: `design-levels` level 2, `architecture-design`, `speckit-brainstorm`, `model-the-domain`, `design-passes`, `commands/speckit.brainstorm.md`, and `opening-a-change` for the new section.
8. A release note, `changes/635.change.md`.

## Not Doing (and Why)

- A level-3 gate in the pipeline. That's #648, which waits on this branch so its "no design decision" exception lands in the same folder.
- #382's short track. It reads the same boundary exception, and that issue gets a comment saying so rather than a design here.
- wfctl naming "Moves a boundary?" itself. It would be the first heading wfctl names, and a repo whose template lacks it would fail every PR.
- Moving the old declarations into spec folders. Every one belongs to a branch already on `main`, and git history and the merged PRs keep their reasons.
- A commit trailer or a committed folder outside the arch root. The level-2 record covers why both lost.

## Open Questions

- None blocking. `check-body` is run by the `opening-a-change` skill but not by CI or the worktree guard, so the reviewer's copy depends on that skill running. The level-2 record accepts that while wfctl has one user.
