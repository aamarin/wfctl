# Review job contract

File: `.github/workflows/review.yml`. Job id and check name: `review`. The
ruleset and `wfctl store reviews`'s rerun both find it by that name, so
renaming it means editing `.github/rulesets/main.json`, applying it again, and
changing the rerun lookup.

## Trigger and trust

- `on: pull_request_target` with `types: [opened, synchronize, reopened,
  edited]`, so GitHub runs the base branch's copy of this file (research R4),
  and runs it again when the PR's base branch changes (research R14).
- `concurrency: { group: review-${{ github.event.pull_request.number }},
  cancel-in-progress: true }`, so a retarget cancels the run against the old
  base (research R14).
- `.github/rulesets/main.json` lists the check as `{ "context": "review",
  "integration_id": 15368 }`. 15368 is the GitHub Actions app, so a commit
  status someone posts by hand with the name `review` doesn't satisfy it.
  The id is checked in quickstart step 4: the read-back must show it on the
  `review` entry.
- `permissions: contents: read`, and nothing else. `ci.yml` gains the same
  top-level `permissions` key, since its PR jobs run the PR's code with the
  default token, which can push in this repository. The `tag` job keeps its
  own `contents: write`, which overrides the top-level key for that job.
- The job never executes a file from the PR's checkout. It runs no `uv sync`,
  `pip install`, script, or action from `pr/`.

## Steps

1. Check out the base branch into `trusted/` (the default ref for
   `pull_request_target`).
2. Check out `github.event.pull_request.head.sha` into `pr/` with
   `fetch-depth: 0`.
3. `git -C pr fetch origin +refs/notes/wfctl-review:refs/notes/wfctl-review`.
   When `origin` has no such ref, the step continues, and every commit then
   reads as unreviewed. `actions/checkout` already fetched every branch,
   including the base, so the check can read the base's `wfctl.json` from git
   without a second fetch (FR-015).
4. Set up uv, then run `uv run --project ../trusted wfctl check reviews --base
   "$BASE_REF"` with `pr/` as the working directory. The step sets `BASE_REF`
   from `github.event.pull_request.base.ref` in its `env:` block, never inline
   in `run:` (research R14).

The job's exit code is the command's.

## Not covered

- A PR from a fork. Its notes can't be pushed to `origin`, so its check fails
  until a person signs off. The repository has no fork PRs today.
- A configured `push` refspec for `refs/notes/*` on an agent's machine, which
  the guard can't see (`627-guard-blocks-note-writes.md`).
