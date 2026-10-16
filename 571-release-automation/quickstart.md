# Quickstart: release automation

## Writing a release note

Every branch commits one note for its issue before `wfctl verify` passes.

```bash
uv run towncrier create 571.change.md --content "What a user of wfctl will notice."
git add changes/571.change.md
uv run wfctl verify
```

Pick the category by what an existing user notices once the change ships:
`change` when something they rely on behaves differently, `addition` when
something new is there, `fix` when something broken now works, and `none` when
they notice nothing. A branch with no issue in its name uses
`changes/+<what-changed>.<category>.md`.

Without `--content`, towncrier writes "Add your info here", and the check fails
the note until it is replaced.

## Checking a branch by hand

```bash
uv run python .github/scripts/check_release_note.py
```

## Cutting a release

```bash
git switch main
git pull --ff-only
uv run python .github/scripts/release.py
```

The script proposes a version, lists merges that came with no note, and shows
the draft. Confirm or change the version, edit the draft in your editor, and
the script commits the release on `release/v<version>`, pushes it, and opens a
pull request. Merge that pull request once its checks pass. CI then tags the
merge and publishes the release commit's body.

## Protecting `main`, once this feature has merged

```bash
gh api -X POST repos/{owner}/{repo}/rulesets --input .github/rulesets/main.json
gh api -X PATCH repos/{owner}/{repo} -F allow_squash_merge=false -F allow_rebase_merge=false
gh api repos/{owner}/{repo}/rules/branches/main
gh api repos/{owner}/{repo}/rulesets --jq '.[] | select(.name == "main") | .id'
gh api repos/{owner}/{repo}/rulesets/<id> --jq '.bypass_actors'
gh api repos/{owner}/{repo} --jq '{merge: .allow_merge_commit, squash: .allow_squash_merge, rebase: .allow_rebase_merge}'
```

The last four read it back: the rules in force on `main` with their five
required checks, an empty bypass list, and merge commits as the only merge
method. From then on, a push straight to
`main` is refused, and a pull request merges only once test, wheel, lint, and
the release note check pass.

## Verifying this feature

1. `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/`.
2. `uv run wfctl check config`, after `wfctl.json` gains the check.
3. `uv run wfctl verify` on this branch with `changes/571.none.md` committed,
   and again with it removed, which fails.
4. On a scratch clone of `main` with a few notes copied in, run the release
   script and stop at the version prompt. `git status` and `git branch` show
   nothing changed.
5. After merge, protect `main` as above and read the ruleset back. The first
   release after that goes through its own pull request.
