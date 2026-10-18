# Data model: saving unsaved work when a worktree is removed

wfctl writes two things to disk for this feature: spec files copied into the
main checkout's spec dir, and the `unsaved/` folder in the branch's state dir.
Every value below is computed from git and the filesystem when the command
runs, and nothing about a run is recorded (`session-state-is-re-derived`).

## Store result

What one run of the store ended with. `wfctl store specs` prints it and exits
with its `exit_code`. The removal hook prints it and reads `stops_removal`
(research R7).

These are the outcomes this branch adds. #359 adds its own for a spec store
outside the worktree, and they all have `stops_removal` false.

| Outcome | When | Stops removal | Exit by hand | First line printed |
| --- | --- | --- | --- | --- |
| `copied` | The copy-out wrote one or more files | no | 0 | `✓ copied N spec files → <dest>` |
| `already_copied` | Every file in the worktree's spec dir is identical in the destination | no | 0 | `✓ spec files already in <dest>, nothing copied` |
| `differs` | The destination holds a file that differs, and `--overwrite` was not given | yes | 1 | `✗ <dest> holds different spec files for <branch>` |
| `copy_failed` | A copy raised partway | yes | 1 | `✗ couldn't copy spec files to <dest> (<cause>)` |
| `to_unsaved` | The spec dir is inside the worktree and there is no main checkout | no | 0 | `ℹ no main checkout — spec files are saved with the unsaved work` |
| `not_applicable` | The command runs in the main checkout, or the spec dir is outside the worktree | no | 0 | `ℹ spec dir <path> is not inside a worktree being removed — nothing to copy` |
| `no_spec_dir` | No spec dir resolves for the branch | no | 0 | `ℹ no spec dir for <branch>` |

`stops_removal` is true when `inside` is true and the outcome is not `copied`,
`already_copied`, or `to_unsaved` (FR-029). `not_applicable` with `inside` true
therefore stops a removal. On this branch that can't happen, since the copy-out
runs whenever the spec dir is inside a worktree with a main checkout, but it is
the guard #359's research R6 asks for if a merged `store()` ever gets the order
wrong.

`copied` prints a second line, `    nothing backs this copy up`, and never the
word "durable" (FR-031).

`differs` prints, under its first line, each differing file's path relative to
the spec dir, and then each file's unified diff, indented four spaces.

## Copy-out

Computed by `_copy_out.plan(source, dest)`, and carried out by
`_copy_out.apply(plan, overwrite)`.

| Field | Meaning |
| --- | --- |
| `source` | The spec dir inside the worktree |
| `dest` | `spec_root(main checkout) / source.name` |
| `missing` | Relative paths in `source` with no file at `dest` |
| `same` | Relative paths whose bytes are identical |
| `different` | Relative paths whose bytes differ, each with its diff text |

`missing` and `different` are what a copy writes. `different` is only written
when `overwrite` is true. A path that exists only under `dest` is in none of the
three lists, so nothing ever touches it (FR-025).

"Main checkout" is `_paths.main_checkout(worktree)`. When that is None, the
store tells two cases apart with `git rev-parse --git-common-dir`: if the
common dir is the worktree's own `.git`, the command is running in the main
checkout and the outcome is `not_applicable`; otherwise the layout is bare and
the outcome is `to_unsaved`.

## Unsaved check

What `archive unsaved` finds before it copies anything. Computed by
`_archive.check(worktree, spec_dir)`.

| Field | Meaning |
| --- | --- |
| `edits` | Paths with uncommitted edits, staged or not (research R4) |
| `unmerged` | `<short sha> <subject>` for each commit on no remote that a merge into trunk would bring in (research R3) |
| `trunk` | The trunk the merge check used, for the output |
| `warnings` | One line per check git couldn't answer, and per `save_on_remove` problem |
| `untracked` | Relative paths from `git ls-files --others`, minus the spec dir (research R5) |
| `folders` | `save_on_remove` folders that exist in the worktree |
| `worktree` | The worktree the check ran in, so `save` knows where to copy from |
| `listing_error` | Why `git ls-files --others` failed, or None (#600 item 5) |

The check refuses when `edits` or `unmerged` is non-empty, or when
`listing_error` is set. `warnings` never refuse. The listing is the one check
that stops a removal when git can't answer, because going ahead would delete
every untracked file.

## The `unsaved/` folder

One per branch, at `<state dir>/unsaved/`. It holds every path in `untracked`
and every folder in `folders`, at its original path relative to the worktree
root. In the bare layout it also holds the spec dir, at its relative path.

| Path | What it is |
| --- | --- |
| `unsaved/` | The latest save |
| `unsaved.staging/` | A save in progress. Removed on failure, and cleared at the start of the next run |
| `unsaved-<YYYYMMDDTHHMMSSffffffZ>/` | An earlier save, moved aside |

No index file is written. The folder is a copy of the worktree's layout, and
restoring a file is a plain copy back (SC-002).

## Saved result

What the copy into `unsaved/` returns, for the output.

| Field | Meaning |
| --- | --- |
| `dest` | The `unsaved/` folder |
| `files` | Every file and symlink in it, relative and sorted |

`len(files)` is the count. The first 20 are printed, then `and N more` when
there are more (FR-023). When there is nothing to save, no folder is created
and the result is None (FR-022).

## `save_on_remove`

A key in `wfctl.json`, written by the repository.

```json
{ "save_on_remove": ["notes/", "research/"] }
```

| Entry | At removal | In `check config` |
| --- | --- | --- |
| A relative path to a folder that exists | copied | fine |
| A relative path to a folder that doesn't exist | skipped, silently | fine |
| An absolute path, or one resolving outside the repository | skipped, with a warning | finding |
| Not a string, or empty | skipped, with a warning | finding |
| The key present but not a list | every entry skipped, with a warning | finding |
