# Contract — resolving a feature's record list

The instruction all four wrappers carry, identically. It is written once here so
the four copies can be compared against one thing rather than against each other.

## The steps

```bash
wfctl feature-paths      # read FEATURE_DIR from the output
```

Read `<FEATURE_DIR>/design.md`. Take the section headed
`## Software design decisions`. From it, take every **list item** of the form
`- <path> — <text>`; the path is a record path. Prose in the section contributes
no paths.

Read each record at its path.

## What "resolve" returns

Exactly one of three outcomes, and the step reports which:

| Outcome | Condition |
| --- | --- |
| `listed` | `design.md` present, section present, one or more entries |
| `none` | `design.md` present, section absent or carrying no entries |
| `unknown` | no `design.md` at `FEATURE_DIR` |

## Refusals and near-misses

**Do not glob `<arch-root>/design/` by issue number.** It is the mechanism this
design started with and it was falsified on this branch: the worktree is named
for epic #121, the record for child #326, so `design/121-*.md` loads #122's
record and misses the one written here. The failure is silent in both directions.
`docs/architecture/design-md-indexes-the-records.md` carries the argument.

**Do not assume `specs/<branch>/`.** A repository can record a `spec_root`
outside the working tree, and this one does. `wfctl feature-paths` is the single
authority; the upstream `speckit-specify` skill's own step 3 assumes the literal
path and is wrong here.

**Do not take every path that appears in the section.** The section carries prose
by design — the `/speckit.brainstorm` wrapper requires a level answered with no
record to say so in one line rather than delete the section — and that prose may
name a **level-2** record. A level-2 record read as level-3 binds nothing while
looking like it does.

**Do not summarise a record into the step's own output.** Report paths. A digest
is a second copy and the copy is what drifts; the rule is `design.md` item 5's
and this is the same rule one step downstream.

**Do not read a record the list does not name.** Not every record under
`<arch-root>/design/` belongs to this feature, and the epic's wording is "only
the ones their tasks reference, never a catalog".

## A listed path that will not read

Report it as listed and unreadable, naming the path. Two shapes:

- the file does not exist — a record that moved is a broken reference, not an
  absence
- the path is outside the repository — `wfctl arch check` is what prevents this
  at write time, and a step reading the list does not re-litigate it, but it must
  not present the record as read

Neither is a reason to stop the step.
