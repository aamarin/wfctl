# Contract: `.github/scripts/release.py`

## Invocation

```
uv run python .github/scripts/release.py
```

Run by Andre from the repository root of an up-to-date `main`. `uv run`
reaches the `dev` dependency group by default, which carries towncrier. The
`gh` CLI has to be signed in as Andre, since the script opens the pull request
with it.

## Preconditions

The script refuses, changes nothing, and exits 1 when any of these fails:

| Precondition | Refusal |
| --- | --- |
| the current branch is `main` | `✗ releases are cut from main, and this is <branch>` |
| the working tree is clean | `✗ the working tree has changes, commit or stash them first` |
| `main` matches `origin/main` after `git fetch origin main` | `✗ main isn't at origin/main, run git pull --ff-only` |
| a `v*` tag exists | `✗ no release tag found to compare against` |

Since the release commit is made on its own branch, `main` is never left ahead
of `origin/main` by the script, and a re-run after an unmerged release reaches
the branch check below rather than this table.

## Output, in order

```
Proposed version: 0.24.0 (minor: 2 behaviour changes, 1 addition)
Merged with no release note: #566, #570

## Behaviour changes

- ... (#542)

## Additions

- ... (#509)

## Fixes

- ... (#537)

Confirm the version [0.24.0]:
```

The "Merged with no release note" line is absent when every merge added a note.

## Prompts

1. `Confirm the version [<proposed>]:` takes Enter for the proposal or a typed
   `X.Y.Z` greater than the current version. Anything else asks again. End of
   input or Ctrl-C aborts.
2. Once the version is confirmed, the script refuses with `✗ release/v<version>
   already exists, close its pull request or delete the branch first` when that
   branch exists locally or on `origin`, and changes nothing.
3. The draft then opens in `git var GIT_EDITOR`. Saving an empty file aborts,
   so a draft that started empty has to be written before the commit is made.
   An editor that exits non-zero, such as vim's `:cq`, aborts too.

The spec's User Story 2 now names the same order, version first and draft
second. The draft is not the last gate: the pull request it becomes is read
again before Andre merges it.

## After both prompts

1. `git switch -c release/v<version>` from `main`.
2. `pyproject.toml`'s version line is set to the confirmed version.
3. `uv lock` runs.
4. Every file under `changes/` is removed with `git rm`. The step is skipped
   when `changes/` holds no file, which is the case after a release that
   deleted every note and no merge since.
5. `git add pyproject.toml uv.lock`, then `git commit --cleanup=verbatim -F
   <message>`. The script writes the message file itself: the subject
   `chore(release): cut <version>`, a blank line, and then the edited draft as
   the body. git takes the subject from the file's first line, so passing the
   draft alone would make its first heading the subject. The note deletions
   are already staged by step 4.
6. `git push -u origin release/v<version>`.
7. `gh pr create --base main --head release/v<version> --fill` opens the pull
   request. The branch holds one commit, so `--fill` takes the title from its
   subject and the description from its body, and the command needs no draft
   file that could be gone by the time it is retried.
8. `git switch main`.
9. The script prints the closing lines shown under "The release text lives in
   the commit".

It never pushes `main` and never merges. When a step from 1 to 5 fails, the
script restores exactly the paths it wrote, with `git restore --staged
--worktree --source=HEAD -- pyproject.toml uv.lock changes/`, then switches
back to `main`, deletes the release branch, and exits 1 naming the step. The
restore comes first because the version bump, the relock, and the staged note
deletions are uncommitted at that point, and a plain switch would carry them
onto `main`. It names its paths rather than running `git reset --hard`, because
the editor session sits between the clean-tree check and the commit, and a
tracked file Andre edited in another window then would be lost to a reset.

When step 6 or 7 fails, the commit already exists, so the script leaves the
branch in place, switches back to `main`, and exits 1 printing the command that
failed, for Andre to run again. Both commands are complete as printed: `git
push -u origin release/v<version>` and `gh pr create --base main --head
release/v<version> --fill`.

## The release text lives in the commit

The pull request's description is a copy of the release commit's body, made
once by `--fill`. The tag job publishes the commit's body, never the
description, so an edit made to the description on GitHub never reaches the
release. To change the release text after the pull request opens, amend the
commit on `release/v<version>` and force-push that branch. The script's
closing line says so:

```
Release pull request opened: <url>. Merge it once its checks pass.
To change the release notes, amend the commit on release/v0.24.0 and force-push it.
Editing the pull request's description doesn't change the release.
```

## Nothing to release

When `changes/` holds only `none` notes, or no notes, and every merge since the
last tag added a note:

```
Nothing to release: 3 changes merged since v0.23.0, all marked none.
```

The script exits 0 and changes nothing.

A merge with no note is never read as `none`. When any are listed, the script
carries on even with no other notes, proposes a patch from the notes it has, and
says the proposal leaves them out:

```
Proposed version: 0.23.1 (patch: no notes yet, and 9 merges with no release note to read first)
Merged with no release note: #570, #573, #577, #581, #589, #592, #596, ...
```

With no notes to build from, towncrier prints `No significant changes.`, and
the script drops that line, so the draft opens empty and Andre writes those
merges into it by hand. This is the first release after this feature ships,
since every merge since v0.23.0 predates the check.

## Abort

An abort prints `Stopped, nothing was changed.` and exits 1. Everything before
the branch is created reads; the draft is built in a temporary directory outside
the repository.
