# Phase 1 data model — #299

## `FactValue`

A closed set of three, in `wfctl/_predicates.py` beside `State` and `Verdict`.

```python
FactValue = Literal["met", "unmet", "n/a"]
```

Closed rather than `str` for the reason `State` is: mypy is not strict here, and
a derivation returning `"missing"` would type-check and render as an unknown
glyph. Distinct words from both neighbouring vocabularies on purpose — `State`'s
four are about a step, and `Verdict`'s three are about whether evidence could be
read. See `spec.md` § Clarifications for why `inconclusive` is not reused.

## `Fact`

```python
class Fact(NamedTuple):
    name: str
    value: FactValue
    detail: str
```

`detail` is never `None`. Every value has something to say — `met` names what was
read, `unmet` names what is missing, `n/a` names why the question does not arise
— and a nullable field would let a derivation answer without one.

A `NamedTuple` for `Reading`'s reason: it needs no import and no `__init__`, and
it serializes through `_asdict()` at the payload boundary the way `_PipelineStep`
is turned into a plain dict.

## The four, in fixed order

| # | `name` | Owner | `n/a` when |
| --- | --- | --- | --- |
| 1 | `artifacts written` | the spec dir | never — the question always arises |
| 2 | `definition of done` | `wfctl.json` + the verification record | the repository declares no definition of done |
| 3 | `architecture accepted` | the touched records' `status` field | the branch touched no record |
| 4 | `outward actions authorized` | the recorded human grant | this is the trunk |

Order is fixed and is the order above: it runs from what the branch produced to
who agreed it may land, which is the order the issue states them in. FR-007
requires it stable so a consumer may index rather than search.

## Derivation, one per fact

### 1 `artifacts written` — from `Evidence`

Reads `spec_text`, `plan_text`, `tasks_text` — the three the walk already gathers
unconditionally in `build_evidence`.

Takes `Evidence | None`. `_infer_steps` returns eight pending steps and never
builds an `Evidence` when no spec dir resolved, so the derivation has to answer
without one rather than being handed an empty one — an `Evidence` with three
empty strings would be indistinguishable from a feature directory holding three
empty files.

- `unmet` when no spec dir resolved (`ev is None`). Detail: `no spec dir for this
  branch`.
- `unmet` when any of the three is empty. Detail: `missing spec.md, tasks.md`.
- `met` otherwise. Detail: `spec.md, plan.md, tasks.md`.

Never reads a step's state. The three artifacts are the same evidence the step
predicates read, which is not the same thing as reading their conclusions —
FR-003 forbids the second, and the distinction is the whole feature.

Stops at `Evidence`'s three deliberately. Reaching further — `delivery.md`, the
checklists, `design.md` — means re-implementing predicates that already own those
reads, and `Evidence` is this repository's own definition of "the reads the walk
already performed".

### 2 `definition of done` — from `wfctl.json` and the verification record

- `n/a` when `_verify.load_config` returns no commands and no errors. Detail:
  `no definition of done declared`.
- `unmet` when `verification_block(repo_root)` returns a reason. Detail: that
  reason, unchanged — it is already written to be acted on.
- `met` otherwise. Detail: `passed at <sha7>`, from the record.

The record is read once more for the seven-character sha. That is a second file
read, not a second inference: `verification_block` has already decided, and this
only asks the record what tree it decided about.

### 3 `architecture accepted` — from the touched records' status

```
records_on_this_branch(repo_root, arch)      → slugs this branch added or modified
  ∩ {r.slug for r in load_records(arch)}     → drops design/, scans/, views/,
                                               declarations/ — load_records
                                               globs one level
```

- `n/a` when the intersection is empty. Detail: `no record on this branch`.
- `unmet` when any of them is `proposed` or carries no recognised status.
  Detail: `readiness-is-not-a-step-state (proposed)` — the status beside each
  slug, because `unmet` alone cannot say whether a record is waiting or unreadable.
- `met` otherwise. Detail: the slugs.

`proposed` and `""` are the two that mean "no human has ruled". `accepted`,
`superseded`, `rejected` and `retired` are all statuses a person moved a record
to, so a branch that supersedes a record is not held by this fact.

### 4 `outward actions authorized` — from the recorded grant

Reads the grant `build_report` already resolves, corrected for the trunk in the
payload rather than in the console.

- `n/a` when this is the trunk. Detail: `this is the trunk`.
- `unmet` when git cannot say whether this is the trunk. Detail: `cannot tell
  whether this is the trunk`. Reached through `blocks("inconclusive", "human")`,
  which is `True` because a human grant is promised evidence.
- `unmet` when nobody granted it. Detail: the existing refusal wording, keyed on
  `notify_source` so a person's decision is distinguishable from a failed read.
- `met` otherwise. Detail: names the source that granted it.

## What the payload carries

`PipelineReport` gains one field:

```python
facts: tuple[Fact, ...] = ()
```

A tuple, and defaulted, matching `notify` and `auto_approve`: a report built
without them is a report about a feature nobody granted anything to, and the same
reasoning applies to a report built before this field existed. Outside the
`current` / `next_command` / `auto` triple that `__post_init__` pairs, because
the facts are true of a finished story exactly as they are of a running one.

Serialized as a list of dicts at the `--json` boundary, the way `steps` already
is — a `NamedTuple` reaching `json.dumps` would need a second shape defined beside
it to say what a fact looks like on the wire.

## What is not added

- No fifth step state, and no change to any of the four (FR-008).
- No field on `_PipelineStep`. Three of the four facts are about the branch, and
  a per-step field would repeat one value across eight rows.
- No change to `blocks(verdict, source)` (FR-014).
- No new module. See `plan.md` § Structure Decision.
