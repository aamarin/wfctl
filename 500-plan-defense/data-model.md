# Data model: plan-walkthrough

## Declared pass (`wfctl.json` `steps`)

One entry in a step's list. Only `needs_person` is new.

| Field | Type | Required | Rule |
|---|---|---|---|
| `name` | string | yes | unchanged |
| `command` | string | one of `command` or `manual` | unchanged; `/plan-walkthrough` for this feature |
| `manual` | boolean | one of `command` or `manual` | unchanged |
| `evidence` | string | yes | `plan-walkthrough.md` or `change-walkthrough.md` for this feature |
| `before`, `after` | string | no | unchanged |
| `needs_person` | boolean | no, default `false` | a finding when it is not a boolean, and a finding when it is `true` on a `manual` pass |

In code, `SubStep` gains `needs_person: bool = False`, and only
`_declared._load_step` sets it.

## Pass reading

A pass holds one of the four existing states. The checks apply in this order,
and the first that applies decides:

| Order | Condition | State | `annotation` | `claimed` | Sets cascade |
|---|---|---|---|---|---|
| 1 | a claim exists for `<step>.<name>` | `skipped` | none | the claim's reason | no |
| 2 | the parent step is `skipped` | `skipped` | none | none | no |
| 3 | the parent step is not `done`, or an earlier pass cascaded | `pending` | none | none | no |
| 4 | the reader returns `done` (evidence exists) | `done` | the reader's | none | no |
| 5 | `needs_person` and `auto_approve` on | `skipped` | "needs a person; auto-approve is on" | none | no |
| 6 | otherwise | the reader's state | the reader's | none | yes, unless `done` |

Rows 1, 2, 3, 4, and 6 are today's behavior. Row 5 is new.

### Transitions for a pass declared with `needs_person`

| From | Event | To |
|---|---|---|
| `skipped` (row 5) | `wfctl start --no-auto-approve` | `in_progress` (outstanding) |
| `in_progress` | an attended run writes the marker | `done` |
| `done` | `wfctl start --auto-approve` | `done` (row 4 precedes row 5) |
| any | `wfctl step none` writes a claim | `skipped` (row 1) |

No transition writes or deletes a file on wfctl's side.

Row 5's skip does not hold the parent step `done`; row 6 cascades it back to
`in_progress`. So `_current_step_name` returns `plan` again the moment
`--no-auto-approve` clears the skip, even after `tasks`, `analyze`,
`decompose`, or `implement` already read `done` from their own evidence —
those steps' evidence is untouched, but `plan` blocks ahead of all of them
until the marker is written. A person returning after an autonomous run
passed the skip sees `wfctl status` point back at `plan`, not at wherever the
run actually got to.

## Sub-step payload (`wfctl status --json`)

`steps[].sub_steps[]` gains one key:

| Key | Type | Value |
|---|---|---|
| `needs_person` | boolean | the declaration's flag; `false` for every built-in pass |

A consumer tells the three producers of `skipped` apart without reading the
annotation:

| `claimed` | `needs_person` | Producer |
|---|---|---|
| a string | any | a person's claim |
| `null` | `true`, with `auto_approve` `true` | this feature's skip |
| `null` | `false` | inherited from a skipped parent |

## Answers file

Written by the skill, never read by wfctl.

- **Path**: `$(wfctl state-dir)/walkthrough/<mode>-<YYYY-MM-DDTHH-MM-SS>.md`, where
  `<mode>` is `plan` or `change`. A new file on every run.
- **Contents**: the sources read, then one block per challenge (claim,
  challenge, basis, answer, evidence, disposition, consequence), then the open
  challenges and the outcome. Dispositions are `SETTLED`,
  `REVISION_REQUIRED`, `DEFERRED`, or `UNRESOLVED`.
- **Incomplete run**: the file keeps what was answered and carries
  `Status: incomplete` at the top.

## Marker

Written by the skill only when an attended interview reaches its outcome.

- **Path**: `<FEATURE_DIR>/plan-walkthrough.md` or
  `<FEATURE_DIR>/change-walkthrough.md`.
- **Contents**: exactly three fields and nothing else.

| Field | Plan mode | Change mode |
|---|---|---|
| `Mode` | `plan` | `change` |
| `Walked through` | `sha256:<hex>` of `plan.md` | the commit id of `HEAD` |
| `Date` | ISO 8601 date | ISO 8601 date |
