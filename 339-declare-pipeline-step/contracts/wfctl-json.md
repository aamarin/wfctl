# Contract: `wfctl.json`, the `steps` key

One new top-level key, beside `verify` and `change_check`. Absent means a
repository declares no passes, which is the state every repository is in today.

```json
{
  "verify": [["uv", "run", "pytest", "-q"]],
  "change_check": ["assignees"],
  "steps": {
    "brainstorm": [
      {
        "name": "ui-design",
        "command": "/pfms-ui-design-workflow",
        "evidence": "ui-contract.md"
      },
      {
        "name": "design-review",
        "manual": true,
        "evidence": "ui-review.md",
        "after": "ui-design"
      }
    ]
  }
}
```

## Rules

| Rule | Detail |
| --- | --- |
| Key | One of the eight built-in step names. Nothing else is accepted |
| Value | A list of pass objects, in the order they run |
| `name` | Required, non-empty, unique under this step. The same name under another step is fine |
| `command` xor `manual` | Exactly one. `manual` is `true`; there is no `false` reading |
| `evidence` | Required. Relative resolves against the feature directory, absolute is used as given |
| `on_finish` | Optional. `"automatic"` or `"review_required"`. Defaults to `review_required` |
| `before` / `after` | Optional. Names a sibling under the same step, bare |
| Anything else | A pass declaring passes of its own is refused, not dropped |

Order is written order, the tool's own passes first. `before` / `after` moves one
pass relative to a sibling, including relative to one of wfctl's own.

`on_finish` defaults differ by where the list was read from, not by anything
on the pass: a pass read from configuration defaults to `review_required`,
because wfctl cannot vouch for a command it does not ship; a pass carried with
the tool defaults to `automatic`. A repository that sets `"on_finish":
"automatic"` produces a pass indistinguishable from a tool-shipped one (FR-011,
FR-021a).

`evidence` builds the file-exists reader on the repository's behalf, and that
is the whole of what configuration can express. A pass whose evidence is a
heading inside another file, or a line in a commit message, is out of reach of
this file by construction; the answer is to change what that pass writes.

## Every rule above is checked

`wfctl check config` reports each violation by name and exits non-zero. Nothing
here is dropped silently — a declaration wfctl discards without saying so is
indistinguishable to its author from one it never read.
