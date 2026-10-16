# Contract: `.github/scripts/check_release_note.py`

## Invocation

```
uv run --frozen --extra dev python .github/scripts/check_release_note.py   # wfctl verify
python3 .github/scripts/check_release_note.py                              # CI, pull requests
```

It takes no arguments and runs from the repository root, which is where
`wfctl verify` runs its commands.

## Inputs

| Input | Used for |
| --- | --- |
| `GITHUB_HEAD_REF`, when not empty | the branch name in a pull request run |
| `git rev-parse --abbrev-ref HEAD` | the branch name anywhere else |
| `GITHUB_REF_NAME` | the branch name when HEAD is detached |
| `origin/main`, then `main` | the base to diff from |
| `[[tool.towncrier.type]]` in `pyproject.toml` | the category list |
| `[tool.towncrier].directory` | the notes folder, `changes` |
| `[project].version` in `pyproject.toml` at `HEAD` | whether a `release/v<X.Y.Z>` branch carries its own version |
| `[project].version` in `pyproject.toml` at the base | whether that version is higher than `main`'s |

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | the branch passes, it is `main`, or it is a release branch whose version matches its name and is higher than the base's |
| 1 | a finding, printed to stdout |

## Messages

Each finding prints its own block. A branch can produce several, and all of them
print before the script exits.

No note for the branch's issue:

```
✗ no release note for #571
  add changes/571.<category>.md, where the category is change, addition, fix, or none
  for example: uv run towncrier create 571.change.md --content "What a user of wfctl will notice."
```

A branch whose name starts with no issue, and adds no note:

```
✗ no release note on this branch
  add changes/+<what-changed>.<category>.md, where the category is change, addition, fix, or none
  for example: uv run towncrier create +<what-changed>.fix.md --content "What a user of wfctl will notice."
```

A note naming a category that doesn't exist:

```
✗ changes/571.feature.md names the category "feature", which doesn't exist
  use change, addition, fix, or none
```

A file under `changes/` with neither note form:

```
✗ changes/notes.md isn't a release note name
  name it <issue>.<category>.md, or +<name>.<category>.md for work with no issue
```

A note with nothing written in it:

```
✗ changes/571.change.md has no release note written in it
  replace "Add your info here" with what a user of wfctl will notice
```

The last line reads `the file is empty` when the note is empty or whitespace.

No base to compare against:

```
✗ can't find main to compare this branch against
  run git fetch origin main, then check again
```

On `main`:

```
✓ on main, nothing to check
```

On a release branch whose version matches its name and is higher than the
base's:

```
✓ release branch for 0.24.0, no note needed
```

On a release branch whose version doesn't match its name:

```
✗ release/v0.24.0 carries version 0.23.1 in pyproject.toml
  a release branch needs no note only when its version matches its name
```

On a release branch whose version matches its name but isn't higher than the
base's:

```
✗ release/v0.23.0 carries version 0.23.0, and main already carries 0.23.0
  a release branch needs no note only when it raises the version
```

A branch is a release branch when its whole name matches `release/v<X.Y.Z>`.
Any other branch, `release/` prefix or not, follows the rules above. The
versions are compared as three integers, so 0.10.0 is higher than 0.9.0.

A pass:

```
✓ release note for #571: changes/571.change.md
```

## Category list

The list is read from `pyproject.toml` on every run, and the messages print it
in the table's order, so a category added there reaches every message above
with no edit to the script.
