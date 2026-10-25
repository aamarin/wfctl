# Plan review scan for #627

## Review 2026-10-25T12:43Z

- Verdict: satisfied
- Reviewed: plan.md 438d83be1eda5138b13890f983182e25e865ad0f, spec.md 5cf0b978c72029ed709e5d7456ea11eb12574cf3, .specify/memory/constitution.md absent, design.md a300e080b4678211c03622c9cc526026ac136c85, docs/architecture/design/627-unreviewed-takes-coverage.md 6952a2a5ce10f93a970695db193bacb0a5ffa297, docs/architecture/design/627-review-note-line-per-event.md 9630d75158af14e37fe67d866147ee1054355e44, docs/architecture/design/627-guard-blocks-note-writes.md 666b18a2720685bbb6174ea35aa39ea7d69b17ac, docs/architecture/review-record-in-git-notes.md ac9c3ac3275ebbfec560deef9ccf5521e16bd910, docs/architecture/review-covers-unreviewed-commits.md 24c4b0e1c20ef1fa397c6e861eaf907785b28769, research.md 653ba3238031da25db2efee1625297ec1f370b62, data-model.md cbc8c4f4e8554154c6fef144575b02cd5bfc01ff, quickstart.md 14518a15544a63e52363f8f41beed03531ebb5b8, contracts/cli.md 35158d2d511f7d9fbb1281d3b5cc8275b59adaaa, contracts/review-job.md ea805382169da9eec02ae66c71d108371be8a9c6, contracts/review-note.md dfdbb4b3891a514c88396ff9d958191cc203a765, checklists/requirements.md f0f311123f87812b1660c822ee055effe594c3f7
- Review type: full (no earlier report and no plan copy)
- Open: BLOCKER 0 · MAJOR 3 · MINOR 8 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/627-ci-review-check/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Outstanding (PR-003, PR-007) |
| Architecture and boundaries | Outstanding (PR-001, PR-006) |
| Adversarial implementation and verification | Outstanding (PR-002, PR-005, PR-009, PR-011) |
| Security and reliability | Outstanding (PR-004, PR-008, PR-010) |

### Findings

- **PR-001, MAJOR, open.** `research.md` R4 moves the review job to `pull_request_target` and runs `main`'s wfctl. The accepted record `review-record-in-git-notes.md` says the CI job runs the PR's own wfctl, and the plan's Constitution Check says no gate changed. Stands because the accepted record still says the opposite of the plan.
- **PR-002, MAJOR, open.** R4's fallback keeps the `pull_request` trigger, so GitHub runs the PR's own workflow file, which FR-017a forbids. Stands because the plan doesn't say the fallback needs a spec change, and R8's rerun lookup depends on the same assumption, which can only be checked after merge.
- **PR-003, MAJOR, open.** `release.py` ends with `git switch main`, and the sign-off command takes no commit argument, so run from `main` it fails with "trunk is the branch under review". Stands because R12 gives no exact command for FR-024 to print, so the implementer has to choose between printing a branch switch and changing the sign-off CLI.
- **PR-004, MINOR, open.** The guard's push rule matches only command text holding `refs/notes/`. On git 2.44.0, `git push origin notes/wfctl-review` pushed the notes ref without that text, and a `'refs/*:refs/*'` refspec would too. Stands because the plan names no rule for those forms.
- **PR-005, MINOR, open.** R9 doesn't say `notes` must be git's subcommand. Under a loose reading, a commit message containing "git notes add" is refused. Stands because the plan also doesn't say how the guard detects an env-prefixed `GIT_NOTES_REF=x git notes add`.
- **PR-006, MINOR, open.** `627-review-note-line-per-event.md` says notes are added with `git notes append` and that recording doesn't read the note first. R6, the data model, and the note contract all read first. Stands because only `research.md` mentions the change, and the proposed record still needs a Consequences edit and a Log entry.
- **PR-007, MINOR, open.** The spec's Validation Strategy asks for a `review` job run on this feature's own PR. The 2026-10-25 clarification and R4 say that PR has no job, and the quickstart moves the check to a throwaway PR after merge. Stands because the spec still says the first.
- **PR-008, MINOR, open.** The spec's Assumptions leave it to the plan to decide where else `contents: read` applies. The plan answers only for `review.yml`. Stands because `ci.yml` has no top-level `permissions` key, so PR jobs run the PR's code with a token that can push.
- **PR-009, MINOR, open.** FR-004 covers only a failed push. Stands because nothing says what the review check or sign-off commands print or exit with when the local `record` fails, for example when two worktrees contend for the lock on the shared notes ref.
- **PR-010, MINOR, open.** The required checks in `main.json` list a `context` with no `integration_id`. Stands because a commit status that anyone with write access posts with `context=review` would satisfy the check.
- **PR-011, MINOR, open.** R3 says the notes walk matches what the state directory holds. After a reset that drops the state directory's last reviewed commit from the branch, the guard counts from the merge base and the notes reader counts from an older noted commit. Stands because both answers are safe but different, which strains SC-004.
