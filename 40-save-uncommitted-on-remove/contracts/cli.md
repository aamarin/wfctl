# CLI contract: saving unsaved work when a worktree is removed

These are the commands this feature exposes. Output examples are exact apart
from paths, counts, commit ids, and dates. Tests assert on them with `NO_COLOR`
set.

## `wfctl hook worktree-remove [WORKTREE] [HANDLE]`

What workmux's `pre_remove` calls. `WORKTREE` defaults to `$WM_WORKTREE_PATH`,
then the current repository. `HANDLE` defaults to `$WM_HANDLE`, then the branch.
It runs every check, then the store, then the copy into `unsaved/` (research
R2).

A clean removal in the default layout, with untracked files:

```
$ wfctl hook worktree-remove wt/40-save-uncommitted-on-remove 40-save-uncommitted-on-remove
✓ copied 3 spec files → /Users/andremarin/Development/wfctl/specs/40-save-uncommitted-on-remove
    nothing backs this copy up
✓ saved 2 files → ~/.local/state/wfctl/wfctl/40-save-uncommitted-on-remove/unsaved
    notes.md
    src/new_module.py
```

More than 20 files:

```
✓ saved 54 files → ~/.local/state/wfctl/wfctl/40-save-uncommitted-on-remove/unsaved
    notes.md
    ref-clone/.git/HEAD
    …18 more lines…
    and 34 more
```

Nothing to save:

```
✓ spec files already in /Users/andremarin/Development/wfctl/specs/40-save-uncommitted-on-remove, nothing copied
ℹ no unsaved files to keep
```

Stopped. Every finding is listed, then the routes:

```
✗ removal stopped — this worktree holds work saved nowhere else
  uncommitted edits:
    wfctl/cli.py
    wfctl/_archive.py
  commits on no remote that aren't merged into origin/main:
    1ff95fd docs(scans): clarify scan for #40
  /Users/andremarin/Development/wfctl/specs/40-save-uncommitted-on-remove holds different spec files:
    spec.md
      --- main checkout/spec.md
      +++ worktree/spec.md
      @@ -301,2 +301,4 @@
      …

  Keep the worktree's spec files: cd '/…/wt/40-save-uncommitted-on-remove' && wfctl store specs --overwrite
  Remove anyway:                  git worktree remove --force '/…/wt/40-save-uncommitted-on-remove' && git branch -D 40-save-uncommitted-on-remove
                                  (leaves the tmux window workmux would have closed)
```

Exit 1. The `Keep the worktree's spec files` line is printed only when the
spec files differ.

A check git couldn't answer:

```
⚠ couldn't check for unmerged commits (no trunk branch found) — removal goes ahead
```

Exit 0, unless another check refused.

A copy into `unsaved/` that failed:

```
✗ couldn't save unsaved files (No space left on device) — removal stopped, nothing lost
  Remove anyway: git worktree remove --force '/…' && git branch -D 40-save-uncommitted-on-remove
```

Exit 1.

A `save_on_remove` entry that can't be used:

```
⚠ wfctl.json: 'save_on_remove' entry '../elsewhere' resolves outside the repository — skipped
```

The same wording, ending in `— skipped`, is used for an absolute path, a non-string
or empty entry, a key that isn't a list, an entry naming the repository itself, and
an entry that holds the spec dir.

Any other error:

```
⚠ worktree-remove failed (<error>) — continuing so the removal is not blocked
```

Exit 0.

### Hidden aliases

`wfctl archive-specs` runs the same function with the same output, and prints
no notice. Neither name appears in `wfctl --help`.

`wfctl archive-story` runs the same function and prints this first:

```
⚠ invoked as `archive-story`; the removal hook is now `wfctl hook worktree-remove`.
  Edit pre_remove in .workmux.yaml to call it.
  The alias is retired once this line stops appearing.
```

## `wfctl archive unsaved [WORKTREE]`

Runs the two checks and the copy into `unsaved/`, without the store. For running
by hand. `WORKTREE` defaults the same way. The output is the `saved`, `no
unsaved files`, warning, and stopped lines above, without the spec file
sections, and the exit codes are the same.

## `wfctl store specs [--overwrite]`

#359 defines this command for spec stores. This feature adds the default
layout's copy-out, run in a worktree whose spec dir is inside it.

```
$ wfctl store specs
✓ copied 3 spec files → /Users/andremarin/Development/wfctl/specs/40-save-uncommitted-on-remove
    nothing backs this copy up
```

```
$ wfctl store specs
✗ /Users/andremarin/Development/wfctl/specs/40-save-uncommitted-on-remove holds different spec files
    spec.md
      --- main checkout/spec.md
      +++ worktree/spec.md
      …
  run `wfctl store specs --overwrite` to replace them with the worktree's copies
```

Exit 1.

```
$ wfctl store specs --overwrite
✓ copied 1 spec file → /Users/andremarin/Development/wfctl/specs/40-save-uncommitted-on-remove
    nothing backs this copy up
```

```
$ wfctl store specs            # run in the main checkout
ℹ spec dir /Users/andremarin/Development/wfctl/specs/40-save-uncommitted-on-remove is not inside a worktree being removed — nothing to copy
```

Exit 0.

## `wfctl check config`

Adds `save_on_remove` findings to the existing list:

```
$ wfctl check config
✗ wfctl.json:
  - 'save_on_remove' entry '/abs/notes' is an absolute path; use a path relative to the repository
  - 'save_on_remove' entry '../elsewhere' resolves outside the repository
```

A listed folder that doesn't exist is not a finding.

## Help text

- `wfctl --help` lists `archive` and `store`, and not `archive-specs` or
  `archive-story`.
- `wfctl hook --help` describes the group as hooks that agent settings and
  workmux call, and lists `worktree-remove`.
- `wfctl archive --help` lists `unsaved`.
