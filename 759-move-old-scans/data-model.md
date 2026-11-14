# Data model: Move the old review scans into their spec folders

Nothing here is persisted. Each type lives for one run of `wfctl store scans`
and is rebuilt from the files on the next run, which is what lets a rerun pick
up where a failed run stopped.

## Review scan

A file under `<arch-root>/scans/` whose name matches
`^(<key_pattern>)-(clarify|plan-review|analyze)\.md$`.

| Field | Type | Source |
| --- | --- | --- |
| `path` | `Path` | the file in the code repository |
| `key` | `str` | the issue key from the file name, such as `656` |
| `step` | `"clarify" \| "plan-review" \| "analyze"` | the step from the file name |
| `text` | `str` | the working tree's content, not the index's |

Every other file under `<arch-root>/scans/`, such as `424-evaluation.md` or
`426-spike.md`, is never read.

## Placement

What the command decided for one scan before writing anything.

| Field | Type | Meaning |
| --- | --- | --- |
| `scan` | `Review scan` | |
| `folder` | `str \| None` | the spec folder's name, such as `649-design-checks-by-context` |
| `source` | `"detail" \| "issue"` | whether the name came from a `Detail` line or the issue number |
| `problem` | `str \| None` | why no folder was chosen: `no folder for #121`, `#40 matches 40-a, 40-b`, or `Detail names 40-a and 40-b` |

A placement has a folder or a problem, never both.

## Write

The result of writing one placed scan into `<folder>/scans/<step>.md`.

| State | When | What happens to the destination |
| --- | --- | --- |
| `written` | the destination didn't exist | created with the scan's text |
| `appended` | it existed and the scan was named with `--append` | the scan's block added at the end |
| `overwritten` | it existed and the scan was named with `--overwrite` | replaced with the scan's text |
| `already_there` | it already holds what this write would produce (research R5) | unchanged |
| `conflict` | it existed and the scan was named with neither flag | unchanged; the scan is kept |

`written`, `appended`, `overwritten`, and `already_there` all make the scan
ready to store. `conflict` keeps it, and the report prints the two commands.

An `--overwrite` whose destination an earlier scan wrote in the same run is a
`conflict`, not `overwritten`. Otherwise the earlier scan's text would be
replaced before it was ever stored, and that scan would still be deleted,
since its own write reads `written`. The report says to rerun with
`--overwrite` once this run has stored the earlier scan (research R5).

## Folder result

One row of the table: one spec folder and the scans the run tried to put
there.

| Field | Type | Meaning |
| --- | --- | --- |
| `folder` | `str` | the folder's name |
| `created` | `bool` | the folder didn't exist before this run |
| `writes` | `list[tuple[Review scan, Write state]]` | one entry per scan aimed at this folder, in the order they were written |
| `store` | `StoreResult \| None` | from `_spec_store.store`; `None` when no scan was ready to store, or when the command stopped storing before this folder (research R8) |

The list is keyed by scan, not by step, because two scans can share a step's
destination. Folder `649-design-checks-by-context` gets both
`649-plan-review.md` and `656-plan-review.md`, and each keeps its own state.

A scan is deleted from the code repository only when its own write is
`written`, `appended`, `overwritten`, or `already_there`, and `store.outcome`
is `stored`, `already_stored`, or `committed_not_backed_up` (research R6). A
`conflict` scan is never deleted, even when the rest of its folder is stored.

## Run result

| Field | Type | Meaning |
| --- | --- | --- |
| `folders` | `list[Folder result]` | in ascending issue order |
| `unplaced` | `list[Placement]` | scans with a `problem` |
| `unused_flags` | `list[str]` | `--append` or `--overwrite` names that matched no conflict |
| `refused` | `str \| None` | why nothing moved, when the spec root isn't a store with a branch |

`exit_code` is 0 when `refused` is `None`, `unplaced` is empty, no write is a
`conflict`, and every folder with a ready scan was stored. Otherwise it is 1
(FR-012). An unused flag doesn't change the exit code.
