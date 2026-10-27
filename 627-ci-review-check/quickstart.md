# Quickstart: checking the CI review check works

The test suite covers the notes, the readers, the guard, and the commands.
What it can't cover is GitHub: the job only runs from `main`, so the last
three steps happen after this feature merges, on a throwaway PR.

## 1. Locally, before the PR

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy
uv run wfctl verify
```

Then, on this branch, run both review groups. `git notes --ref=wfctl-review
show HEAD` prints `reviewed by security` and `reviewed by code`, and `uv run
wfctl check reviews` prints the pass line.

## 2. After merge: open a throwaway PR

The maintainer opens a draft PR from a branch with one unreviewed commit. The
`review` check appears on the PR and fails, listing the commit under both
groups.

This step checks research R4's assumption: a `pull_request_target` job reports
its check on the PR's head commit. If the check doesn't appear on the PR,
stop before applying the ruleset. R4's fallback runs the PR's own workflow
file, which FR-017a forbids, so the maintainer decides whether to amend
FR-017a first.

## 3. Review it and watch the rerun

Run both review groups on the throwaway branch. The second `review check`
sends the notes and prints `↻ reran the failed review check on PR #<n>`. The
rerun passes.

This step checks R8's assumption about the shape of the link `gh pr checks`
returns.

## 4. Apply the ruleset

Only after step 3 passes:

```bash
gh api -X PUT repos/{owner}/{repo}/rulesets/<id> --input .github/rulesets/main.json
gh api repos/{owner}/{repo}/rules/branches/main
```

The read-back lists six required checks, `review` among them, and the
`review` entry carries `"integration_id": 15368`, the GitHub Actions app.
Without the id, a commit status anyone posts by hand under the name `review`
would satisfy the requirement (`contracts/review-job.md`).

Before closing the throwaway PR, push one more commit to it that adds a job
named `review` to `ci.yml`, with a single step that runs `true`. The commit is
unreviewed, so the real `review` job fails. Check whether the PR's merge box
still lists the `review` requirement as failing. If GitHub reports it as
passing, the spoof works, and the limit in `review-record-in-git-notes.md`
holds as written. If GitHub reports it as failing, update that limit to say so.
Then close the throwaway PR and delete its branch.

## 5. A stacked PR is checked again when GitHub retargets it

Open a throwaway PR into `main`, and a second PR into the first one's branch.
Merge the first with its branch deletion turned on. GitHub retargets the
second to `main`, and a new `review` run starts against `main`.

This step checks research R14's assumption that GitHub sends `edited` for a
retarget it makes itself. If no run starts, the stacked PR keeps a result
measured against the deleted branch until its next push, and R14 needs
another trigger.
