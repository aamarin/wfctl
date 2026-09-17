# Contract: `wfctl status --json`

One key is added to each entry in `steps`. Every other key and its meaning is
unchanged, and no key is removed.

| Key | Before | After |
| --- | --- | --- |
| `steps[].sub_steps` | absent | always present, a list, empty where a step has no passes |
| `next_command` | a slash command, `wfctl verify`, or `null` | may also be a qualified pass name `<step>.<name>` |
| `current` | a step name, or `null` | unchanged — always the *step*, never a pass |

`current` deliberately stays the step. A consumer asking where the pipeline
stands gets the same eight-valued answer it gets today; which pass inside that
step is outstanding is read from `sub_steps`, where it has a state of its own.

## `sub_steps` entries

```json
{
  "name": "ui-design",
  "state": "in_progress",
  "annotation": null,
  "command": "/pfms-ui-design-workflow",
  "manual": false,
  "claimed": null,
  "is_current": true
}
```

| Key | Type | Meaning |
| --- | --- | --- |
| `name` | `str` | Bare. The qualified form is `<parent>.<name>` and is not stored twice |
| `state` | `"done" \| "in_progress" \| "pending" \| "skipped"` | The same four names a step carries (FR-005) |
| `annotation` | `str \| null` | What the console renders beside the row |
| `command` | `str \| null` | `null` exactly when `manual` is true |
| `manual` | `bool` | A person performs this pass (FR-022a) |
| `claimed` | `str \| null` | The reason a person wrote when declaring it inapplicable (FR-019) |
| `is_current` | `bool` | This pass is what holds the pipeline |

Always complete. A pass hidden by the console's default view is present here with
`state: "skipped"` and its `claimed` reason (FR-020) — `--all` changes the
console rendering and never this payload.

At most one entry across the whole payload carries `is_current: true`, and it is
under the step whose own `is_current` is true.

## What a consumer that ignores `sub_steps` sees

A repository that declares no passes emits `"sub_steps": []` on every step except
`brainstorm`, which carries wfctl's own two. `current`, `next_command` and `auto`
answer as they do today for every step but `brainstorm`, where `next_command` may
now name `/speckit.brainstorm` for a reason one level more specific than before.

`speckit-orchestrate` reads `next_command`, `auto`, `stall`, `reason` and
`remedy` and never enumerates `steps[]`, so it needs no change. A manual pass is
safe there for one reason and it is worth stating: a manual pass is never
`auto: true`, and `auto: false` is the branch that displays the command rather
than emitting it.
