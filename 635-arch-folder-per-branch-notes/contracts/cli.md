# CLI contract: Design exceptions move to the spec folder

Every string below is what the user sees, with `NO_COLOR` set.

## `wfctl arch none --reason "<reason>"`

Success, whether or not the spec folder existed:

```
✓ Recorded: no boundary changed — "Copy fix in one help string; nothing moves"
  Put the reason in the PR body.
```

Exit 0. Writes `<spec folder>/exceptions/boundary.md`. Writes nothing under the
arch root.

Refusals, unchanged and exit 1, with nothing written:

```
✗ --reason cannot be empty: say why no boundary changed.
✗ "<why>" is a placeholder, not a reason — say what changed, or why nothing did.
```

Removed: the `⚠ Wrote …, but it is not part of the change under review …`
warning and its exit 1.

## `wfctl step none <step>.<pass> --reason "<reason>"`

Success:

```
✓ Recorded: brainstorm.ui-design does not apply — "No screen changes"
  Put the reason in the PR body.
```

Exit 0. Writes `<spec folder>/exceptions/brainstorm.ui-design.md`.

Refusals, unchanged and exit 1, with nothing written: the empty reason, the
placeholder, an undeclared pass, an unknown bare name, and a bare name declared
under two steps.

Removed: the `⚠ Did not record …` refusal for an exception outside the diff.

## `wfctl status` and `wfctl status --json`

No change to the payload's shape. What changes is which files produce it:

| Branch state | `brainstorm.architecture` |
| --- | --- |
| `design.md`, no record, no exception | `in_progress`, "no architecture record for this change" |
| `design.md` and `exceptions/boundary.md` | `done` |
| `design.md` and only `declarations/<branch>.md` | `in_progress` |
| `spec.md` exists | `done`, whatever the exceptions say |

A pass with `exceptions/<step>.<pass>.md` reads `skipped` with its reason as
`claimed`, as it did when the file was under `step-claims/`.

## `wfctl end`

The summary's Boundary line:

| Branch state | Line |
| --- | --- |
| a record touched on the branch | `**Boundary**: answered` |
| `exceptions/boundary.md` and no record | `**Boundary**: answered` |
| neither | `**Boundary**: unanswered` |
| git can't tell, and no `exceptions/boundary.md` | `**Boundary**: unknown` |

## `wfctl check-body` in this repo

`wfctl.json`:

```json
"change_sections": ["Needs a spec?", "Moves a boundary?"]
```

A body with no `## Moves a boundary?` heading gets the finding `check-body`
already prints for a missing listed section. A body answering
"No. Copy fix in one help string; nothing moves." gets none.

## `wfctl check-body` in any repo

One finding per exception whose reason the body doesn't contain:

```
✗ the boundary exception's reason isn't in the body: "Copy fix in one help string; nothing moves"
✗ brainstorm.ui-design's exception reason isn't in the body: "No screen changes"
```

Exit 1, like every other `check-body` finding.

## Worktree guard: `gh pr create` and `gh pr merge`

Both refusals exit 2, like the review check's, and run only after the review
check finds nothing pending.

A record that contradicts the branch's own boundary exception:

```
✗ 635-arch-folder-per-branch-notes touches docs/architecture/review-store-owns-runs.md, but its spec folder says no boundary moved.
  The record answers the boundary question, so delete the exception:
  rm '/Users/andremarin/Development/wfctl-specs/635-arch-folder-per-branch-notes/exceptions/boundary.md'
```

A record nobody has accepted:

```
✗ 635-arch-folder-per-branch-notes touches records nobody has accepted:
  design-exceptions-live-with-specs (proposed)
  an-absent-artifact-is-claimed-not-inferred (proposed)
  Ask a person to accept or reject each one before the PR opens.
```

When git can't list the records or show one, the guard refuses with the same
error form the review check uses.

## PR template section

Added to `.github/pull_request_template.md` right after "Needs a spec?":

```markdown
## Moves a boundary?
<!--
Does this change draw or move an architecture boundary? Answer yes or no, then
give the reason in one sentence. For a yes, name the record under
docs/architecture/. For a no, copy the reason you gave `wfctl arch none`. Then
list each pass you ran `wfctl step none` on, with its reason. The spec folder
holds both, and a reviewer can't see it.
-->
```
