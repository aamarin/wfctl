# Phase 1 Data Model: doctor exit-code contract

This feature introduces no new persisted data and no new type. What follows
describes the states the existing data already carries, which the contract makes
explicit.

## Check outcome

The central state of this feature. Three outcomes, carried by a `bool` plus the
printed output — deliberately not an enum.

| Outcome | Return | Output | Exit contribution |
| --- | --- | --- | --- |
| Drift found | `True` | names the problem and the remedy | `1` |
| No drift | `False` | silent, or a `✓` line | `0` |
| Could not determine | `False` | states why it could not check | `0` |

**Why not an enum.** A three-valued type would need every call site to map it back
to two exit states, and the mapping is total: both `False` cases contribute `0`.
The distinction that matters to a reader lives in the output, which is where they
look. An enum would add a type, a translation, and a new way for a check to be
wrong, to express something `bool` plus a printed line already carries.

`ponytail:` if a caller ever needs to *act* differently on could-not-determine —
retry, or report skipped-check counts — that is the trigger to introduce the enum.
Nothing needs it today.

## Install record

Existing, unchanged. `.wf-skills-manifest.json` at the repository root.

```
{
  "<layer>": {
    "repo": str, "ref": str, "commit": str,
    "content_hash": str,          # whole-bundle digest
    "wfctl_version": str,
    "installed_at": str,
    "items": [ {"path": str, "backup": str | None} ]
  },
  "tracker": str,                 # bare scalar, not a layer
  "spec_root": str                # bare scalar, not a layer
}
```

**Entry granularity.** `items[].path` is repository-relative and names either a
file or a directory installed as one unit:

| Example path | Kind |
| --- | --- |
| `.agents/commands/speckit.plan.md` | file |
| `.agents/skills/brainstorming` | directory |
| `.specify/scripts/bash` | directory |

This is what FR-008a keys on. An abandoned directory is one finding because it is
one recorded entry, matching how `uninstall-skills` already removes it.

**Rewrite semantics.** Each layer's `items` is replaced wholesale on install. A
path dropped upstream leaves no trace, which is why an abandoned entry cannot be
found by consulting history — it is found by comparing disk against the current
record. This is also why `uninstall-skills` cannot reach it.

**Layer vs scalar.** `tracker` and `spec_root` are bare strings sitting alongside
layer objects. Anything iterating layers must skip them, or `.get("items", [])`
raises on a string.

## Derived: the scan set

Not persisted. Computed per run by the abandoned-entry check.

```
recorded      = { item.path for layer in layers for item in layer.items }
scan_dirs     = { parent(p) for p in recorded } ∩ trees under .agents/ and .specify/
abandoned     = { child for d in scan_dirs for child in listdir(d) } − recorded
```

**One level, not recursive.** Every recorded path sits directly inside its parent,
so a one-level listing sees exactly the units the record describes. Recursing would
descend into recorded directories and report their contents — files that are
installed and accounted for.

**Restricted to the tool's own trees.** `.claude/commands/`, `.bob/`, and
`.github/skills/` are the user's directories; wfctl copies into them but does not
own them. See research.md for why the case from #38 is still caught without them.

**Empty when nothing is installed.** With no layers recorded, `recorded` is empty,
so every file on disk would be abandoned. `doctor` returns early in that state and
the scan never runs.

## Step-to-command table

Existing, unchanged. `_STEP_COMMAND` in `_pipeline.py:14-23` — eight entries
mapping a pipeline step to the slash command that advances it.

```
"brainstorm" → "/speckit.brainstorm"   ...   "implement" → "/speckit.implement"
```

**The invariant Story 4 asserts**: for every value `v`, a file
`wfctl/agents/commands/<v without leading slash>.md` exists in the shipped bundle.

**Direction.** One-way. The bundle ships commands the table does not name —
`start-session`, `code-review`, and 13 others — and that is correct: not every
command advances a pipeline step. Only the table's values are constrained.
