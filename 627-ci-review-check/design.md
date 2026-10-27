# A required CI check that fails a PR while a review group has unreviewed commits

## Problem Statement

How might we block a PR from merging while a review group hasn't reviewed every
commit on it, however the merge command was typed, and whichever agent ran it?

Currently, only the worktree guard enforces this. The guard blocks `gh pr
create` and `gh pr merge` only when the command exactly matches its rules, and
#622 records 14 ways around it. An agent without hook support skips the check
entirely. A required CI check blocks the merge on GitHub in every one of those
cases.

## Who this is for

Andre, who merges PRs that agents open. Success is that a PR whose commits
weren't all reviewed shows a red "review" check and can't merge, and a PR whose
commits were all reviewed, or signed off by a person, shows green with no extra
step.

## Recommended Direction

When a review run completes, wfctl adds a git note to the run's head commit
saying which group reviewed it, and sends the notes ref to GitHub. A person's
sign-off adds a note the same way. A new `review` job in CI fetches those notes,
works out which commits on the PR no review covers, and fails while any group
has one. The `main` ruleset makes it a required check.

CI works out the result itself instead of trusting a pass the local machine
posted, because GitHub's "Update branch" button changes the PR's head without
the local machine. The range rules drop a clean merge like that, so CI passes
it, where a locally posted pass would block until someone reran the review.

The local check keeps reading the state directory, and both sides count with
the same function. The guard also blocks an agent from writing a note or pushing
a notes ref by hand, so only wfctl writes them.

## What the user sees (level 1)

The CI `review` job prints one of these, by state. Andre approved this wording.

```
every commit is covered by a note for each group, or by a sign-off
  ✓ Every commit on this PR has been reviewed.

a group has a commit no note covers
  ✗ 1 commit hasn't been reviewed:
      9f8e7d6 test: cover an empty note   (security, code)
    Run the review panel. If you already did, run `wfctl store reviews`.

the branch reached GitHub before its review notes did
  the same failure as above. The second sentence covers it.

the head is a clean "Update branch" merge of main after a review
  ✓ Every commit on this PR has been reviewed.

the branch was rebased after its review
  ✗ the failure above, listing every rebased commit

a shallow clone, no trunk ref, or a note CI can't read
  ✗ a line naming the cause. CI fails rather than guessing.

a push to main, not a PR
  the job doesn't run, like release-note
```

Each state's level-3 consequence:

1. The failure lists commit subjects, so CI needs the full history, not a shallow
   checkout.
2. "If you already did" means wfctl sends notes on its own, and `wfctl store
   reviews` exists only to resend.
3. The "Update branch" pass means CI computes the range itself with the same
   rules as the local check.
4. Listing groups per commit means CI reads the group list from the PR's own
   `wfctl.json`.

## Structure (level 3)

1. A note holds one plain line per event: `reviewed by security`, `reviewed by
   code`, `signed off by a person`. It carries no run number or time, so two
   machines that record the same event write the same line.
2. `unreviewed` takes each group's last reviewed commit and the signed-off
   commits as arguments. A state directory reader builds them for the guard and
   `review sign-off`, and a notes reader builds them for CI. From the notes, a
   group's last reviewed commit is the nearest ancestor of the head that carries
   its line.
3. `wfctl review check` adds the note when it completes a run, and `wfctl review
   sign-off` adds one when a person signs off. Each then sends the notes ref. A
   failed send prints a warning and leaves the note for `wfctl store reviews`.
4. `wfctl store reviews` sends the notes ref. When `origin` rejects the push, it
   fetches the remote ref, merges it with `git notes merge -s cat_sort_uniq`, and
   pushes again.
5. A CI-facing `wfctl review` subcommand reads the notes, prints the level-1
   messages, and exits 1 on any unreviewed commit. Its name isn't settled.
6. A new PR-only `review` job in `.github/workflows/ci.yml` checks out the full
   history, fetches `refs/notes/wfctl-review`, and runs that subcommand.
   `.github/rulesets/main.json` adds `review` to its required checks, and Andre
   applies the ruleset by hand.
7. The guard refuses any `git notes` write and any `git push` that names
   `refs/notes/` or carries `--mirror`, from the command's text alone.

### Checked and assumed

| Checked | Assumed |
|---|---|
| `unreviewed` reads the sign-off and each group's last reviewed commit from the state directory itself (`_review.py:609`, lines 624 and 639). | GitHub accepts a push of `refs/notes/wfctl-review`, and a `pull_request` job can fetch it with the default token. |
| `commit_range` takes the last reviewed commit as an argument and reads nothing from disk (`_review.py:178`). | On a `pull_request` run, `actions/checkout` checks out a merge of the PR into its base, not the PR's head, so the job has to check out the head commit itself. |
| `commit_range` refuses a shallow clone (`_review.py:208`), and the existing `release-note` job already checks out with `fetch-depth: 0`. | `actions/checkout` leaves no `origin/HEAD` and no local `main`, so `_paths.trunk_branch` returns None in CI unless `wfctl.json` declares `trunk` or the job sets `origin/HEAD`. |
| `_paths.trunk_branch` tries the `trunk` declared in `wfctl.json`, then `origin/HEAD`, then a bare repository's HEAD, then a local `main`, `master`, or `dev`. This repo declares no `trunk`. | A run always starts where the last complete run ended, so a note on commit C covers every commit from where the branch left `main` up to C. |
| A notes ref written in one worktree shows in the others with no fetch. | |
| After a rejected notes push, `git notes merge -s cat_sort_uniq` joins both clones' lines and the next push succeeds (git 2.44.0, scratch repository). | |
| `_hook.py:176` loads the review check only for a command holding `gh`, `merge`, or `sign`, so `notes` and `--mirror` have to join that test. | |
| #642 adds a `branch` keyword to `commit_range`, `unreviewed`, and `start`, defaulting to None. | |

## Key Assumptions to Validate

- [ ] GitHub accepts the notes push and a PR job fetches it. Push a throwaway
      notes ref from this branch and fetch it in a CI run, before plan.
- [ ] The CI checkout lands on a merge commit and has no `origin/HEAD`. Print
      `git rev-parse HEAD`, the PR head SHA, and `git symbolic-ref
      refs/remotes/origin/HEAD` in a throwaway CI run.
- [ ] A run always starts where the last complete run ended. Read `start` in
      `_review.py` after #642 merges, since #642 changes it.

## MVP Scope

In:

1. Notes written on run completion and on sign-off, and sent to GitHub.
2. `wfctl store reviews` to resend.
3. The shared counting function with two readers.
4. The CI subcommand, the `review` job, and the ruleset entry.
5. The guard rule against hand-written notes.
6. A scratch repository test that runs both readers over one history and checks
   they agree.

## Not Doing (and Why)

- Signing notes. The agent runs with the person's own keys, so it could sign a
  forged note too (`review-record-in-git-notes.md`).
- Running the reviewers in CI. It's the only full fix for a forged note, and
  it's a much larger change than this one.
- Having the local guard read the notes. The accepted record keeps the guard on
  the state directory, and #642 is changing that code now.
- Re-running the check when notes arrive. Pushing the notes ref doesn't start a
  PR run, so a branch pushed before its notes fails once and needs a rerun. The
  failure message says so.
- Applying the ruleset. That's Andre's step, done by hand per `AGENTS.md`.

## Open Questions

- The CI subcommand's name. `wfctl review ci` is the working name.
- How the job gets the trunk: a `trunk` key in this repo's `wfctl.json`, or a
  step that sets `origin/HEAD` from the repository's default branch. The second
  works for every repo that copies the job.

## Software design decisions

- docs/architecture/design/627-unreviewed-takes-coverage.md — the local check and CI count unreviewed commits with one function, each passing in its own record of what was reviewed
- docs/architecture/design/627-review-note-line-per-event.md — a review note holds one plain line per event, such as "reviewed by security"
- docs/architecture/design/627-guard-blocks-note-writes.md — the worktree guard blocks an agent from writing any git note or pushing any notes ref

The level-2 decision is `docs/architecture/review-record-in-git-notes.md`,
accepted.
