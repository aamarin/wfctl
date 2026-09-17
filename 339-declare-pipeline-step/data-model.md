# Data model: declare pipeline step

Three shapes: the pass as inference holds it, the pass as a repository writes it,
and the claim a person makes about one. Plus what each adds to the payload
`build_report` returns.

Field names below are the ones the code will carry. Where a field already exists
on `Step` or `_PipelineStep`, it is named as such rather than restated.

## SubStep — a pass, as inference holds it

The in-memory shape. A `NamedTuple` beside `Step` in `_pipeline`, for the reason
`Step` is one: the fields have names, and `reads` is a callable rather than a
key into a registry, so grep finds an evidence reader's definition and its row
together.

| Field | Type | Notes |
| --- | --- | --- |
| `name` | `str` | Unique among one step's passes (FR-002a). Bare in the position view, `<step>.<name>` everywhere typed or written to a path (FR-002b) |
| `command` | `str \| None` | The slash command that advances it. `None` means a person performs it (FR-022a) |
| `on_finish` | `Continuation` | `"automatic"` or `"review_required"`, the same two names `Step` carries |
| `reads` | `EvidenceReader` | `(Evidence) -> Assessment`, the same callable type `Step.reads` is (FR-008) |

Nothing on it records whether it came from the bundle or from configuration
(FR-011). The two lists are distinguishable only while they are being read,
which is where the `on_finish` default is applied (FR-021a).

**Where the built-in ones live.** `_STEPS["brainstorm"]` gains two, in the order
the design levels produce them:

| Name | Command | What it reads |
| --- | --- | --- |
| `architecture` | `/speckit.brainstorm` | a record under the arch root for this change — today's `design_block` |
| `design-doc` | `/speckit.brainstorm` | `design.md` in the feature directory |

Both name the step's own command, because both are produced by one run of it.
Ordering them this way fixes the read `design.md` flagged: `brainstorm` checks
`design.md` first and the record second, which is the reverse of the order
`design-levels` and the brainstorm skill write them in.

`architecture-design` earns no row — it hands its result to
`architecture-decisions` and writes nothing itself.

## DeclaredPass — a pass, as a repository writes it

The `wfctl.json` shape. Parsed by `_declared`, which returns `SubStep` values and
a list of problems; never read anywhere else.

| Key | Required | Type | Rule |
| --- | --- | --- | --- |
| `name` | yes | `str` | Non-empty, unique under its step (FR-002a) |
| `command` | one of | `str` | The slash command. Must be installed (FR-022) |
| `manual` | one of | `true` | The pass is performed by a person (FR-022a, R10) |
| `evidence` | yes | `str` | Path, resolved against `FEATURE_DIR` unless absolute (R3) |
| `on_finish` | no | `"automatic" \| "review_required"` | Defaults to `review_required` for a declared pass (FR-021) |
| `before` / `after` | no | `str` | Names a sibling under the same step (FR-003, R9) |

`evidence` is sugar and says so: it builds the file-exists reader on the
repository's behalf (FR-009), which is strictly less than a built-in reader
can express. A pass whose output is not a file at a fixed path is out of reach of
`wfctl.json` by construction — the record states this as a limit rather than an
oversight, and the answer is to change what that pass writes.

### Validation rules, and which requirement each serves

Every one of these is a `check config` finding and a non-zero exit (FR-022).
None of them is a silent drop.

| Rule | Requirement |
| --- | --- |
| The key under `steps` is one of the eight built-in step names | edge case 1 |
| A pass carries a non-empty `name` | FR-002a |
| No two passes under one step share a `name` | FR-002a |
| A pass carries exactly one of `command` and `manual` | FR-022a, R10 |
| A declared `command` is installed in this repository | FR-022 |
| A `before` / `after` names a sibling that exists | FR-003a |
| The stated order is satisfiable | FR-003a |
| A pass declares no passes of its own | FR-004 |
| `on_finish`, where present, is one of the two names | FR-021a |

The same name under two different steps is accepted and is not a finding
(FR-002a) — a repository adding a pass is never refused on account of a pass
under a step it did not name.

## ClaimedAbsence — one person's statement that one pass does not apply

Written by `wfctl step none`, read by nothing. The claim's only check is a
reviewer disagreeing with it, which is why it lives in the change under review
and not in the state dir.

| Part | Value |
| --- | --- |
| Path | `<arch-root>/step-claims/<branch>/<step>.<name>.md` |
| Body | `# <step>.<name> does not apply — <branch>` then the reason |
| Frontmatter | none — git answers branch and date, the same line `arch none` draws |

One file per pass, so a second claim on one branch cannot destroy the first, and
a second claim on the same pass replaces it (FR-015, SC-005).

`step-claims/` joins `_paths.non_record_subtrees`, so no reader of the arch root
counts a claim as a record. That is FR-016 and SC-006: a change that claims a
pass away and never puts the boundary question is still held by the check that
asks it.

**Refused, with nothing written** (FR-013): an empty reason, and a `<placeholder>`
in angle brackets — both already refused by `arch none`, whose guards this
generalises. **Refused, and the pipeline does not advance** (FR-014): a claim
whose file is outside the working tree or ignored by git, which `arch none`
already detects with `touched_on_this_branch`.

## What the payload carries

`PipelineReport.steps` is a list of dicts today. Each gains one key:

```
{ "name", "state", "annotation", "reason", "remedy", "is_current",
  "sub_steps": [ { "name", "state", "annotation", "command", "manual",
                   "claimed", "reason", "is_current" }, … ] }
```

`sub_steps` is always present and always complete — every pass including the
settled-away ones (FR-020). What the console hides, it hides at the moment of
printing (FR-018, FR-019); nothing is filtered out of the payload, because a view
computing a fact of its own is what `pipeline-state-is-one-payload` forbids.

`claimed` carries the reason a person wrote, or `null`. It is the field the
`--all` view renders (FR-019) and the only place the claim's text appears in the
payload.

### States, and how a pass reaches each

The same four names a step uses (FR-005), read from the payload rather than from
a glyph.

| State | Reached when |
| --- | --- |
| `done` | the pass's `reads` returns `done` |
| `in_progress` | the parent step is current and this pass is the outstanding one |
| `pending` | the parent has not been reached, or an earlier pass under it is outstanding |
| `skipped` | a claim exists for this pass on this branch, or the parent is `skipped` |

"The pass ran and produced nothing" and "the pass does not apply" are one state
with no third outcome between them (FR-017) — `skipped` is what both reach, which
is what `an-absent-artifact-is-claimed-not-inferred` decided.

A pass reaches `skipped` two ways, and `claimed` is what separates them. A
non-null `claimed` is a person's sentence, written by `wfctl step none` into the
change under review. A null `claimed` on a `skipped` pass means the state was
inherited: the parent step was walked past, so the pass was never reached and no
claim was owed. No consumer needs a second state name for this — the field
already answers it, and `--all` renders the sentence where there is one.

### Where the parent's state comes from

Its own `reads` first, then its passes (R7):

```
step `reads` returns `done`
  └─► any pass in_progress or pending?  ──► step is in_progress   (FR-006)
      otherwise                          ──► step is done

step `reads` returns `pending` or `skipped`
  └─► passes are not evaluated; they take the parent's own state
```

### What `next_command` may now name

A pass's command, where an outstanding pass is what holds the pipeline (FR-007).
Where that pass is `manual`, the payload names the pass and says a person
performs it rather than naming a command.

`speckit-orchestrate` needs no contract change for this — it treats
`next_command` as opaque, strips the leading `/` and emits it, and never
enumerates `steps[]`. What changes underneath is where `next_step_content` finds
the row carrying `on_finish`: today `_STEPS` alone, and `auto` is computed
from that lookup.
