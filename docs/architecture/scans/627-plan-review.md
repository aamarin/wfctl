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

## Review 2026-10-25T15:40Z

- Verdict: satisfied
- Reviewed: plan.md 5c1cfa80e45835314be9571dab823427e4cc955f, spec.md e633fffe89c59ab1f8228a0e3df3623b95714321, .specify/memory/constitution.md absent, design.md a300e080b4678211c03622c9cc526026ac136c85, docs/architecture/design/627-unreviewed-takes-coverage.md 6952a2a5ce10f93a970695db193bacb0a5ffa297, docs/architecture/design/627-review-note-line-per-event.md 9630d75158af14e37fe67d866147ee1054355e44, docs/architecture/design/627-guard-blocks-note-writes.md 666b18a2720685bbb6174ea35aa39ea7d69b17ac, docs/architecture/review-record-in-git-notes.md 4e24a7da9f16a04447f2f681e9b307f6fac76d9a, docs/architecture/review-covers-unreviewed-commits.md 24c4b0e1c20ef1fa397c6e861eaf907785b28769, research.md 5d4d0e34a4816757e923c482e89a9647236b85cb, data-model.md 469957bb0c12a9250c332ad93f7d854cb9bca7e9, quickstart.md 7fe0a3660c89a83d3acb9562d54c181840bc9f69, contracts/cli.md 8ffe9828a2b86cc34aabaabd0ba1026cf2d9a1a5, contracts/review-job.md 8f0893a411883a061178a85d93032ae5e044e65b, contracts/review-note.md dfdbb4b3891a514c88396ff9d958191cc203a765, checklists/requirements.md f0f311123f87812b1660c822ee055effe594c3f7, plan-review.plan.md 438d83be1eda5138b13890f983182e25e865ad0f (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 2 · MINOR 9 · Fixed since the earlier review: 5
- Detail: /Users/andremarin/Development/wfctl-specs/627-ci-review-check/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-014; PR-007 fixed) |
| Requirements and traceability | Outstanding (PR-012; PR-003 fixed) |
| Architecture and boundaries | Outstanding (PR-006, PR-016; PR-001 fixed) |
| Adversarial implementation and verification | Outstanding (PR-005, PR-009, PR-011, PR-015; PR-002 fixed) |
| Security and reliability | Outstanding (PR-004, PR-010, PR-013; PR-008 fixed) |

### Findings

- **PR-012, MAJOR, open.** CI keeps requiring a group the PR removed (FR-015, R13), but `review start` loads groups from the working tree and refuses that group, and the guard doesn't count it. Stands because a PR that removes a group passes locally and fails in CI, and FR-010 forbids widening the local group list, so either the local side or FR-015 has to change in the spec.
- **PR-013, MAJOR, open.** R13 reads `main`'s `wfctl.json` at `trunk_refs`' first entry, and `_paths.trunk_branch` honours a `trunk` key in the PR's own `wfctl.json` before `origin/HEAD`. Stands because a PR that declares a branch already holding its head as `trunk` gets an empty range and passes with no review, and its groups are read from that branch's file.
- **PR-014, MINOR, open.** `_review_config.load` reads only from disk, and the plan's Project Structure doesn't list `_review_config.py`. Stands because the plan doesn't say whether the joined group list is validated as one declaration, where the first-letter rule could report a clash neither file has.
- **PR-015, MINOR, open.** If a merged change makes `main`'s wfctl refuse `main`'s own `review` key, every PR fails, the fixing PR included. Stands because the ruleset has no bypass and no recovery step is written down.
- **PR-016, MINOR, open.** R8 can't tell "no PR" from "`gh` is missing or `origin` isn't on GitHub". Stands because in such a repository every notes push prints the rerun warning.
- **PR-004, MINOR, open.** R9 rule 2 is unchanged. Stands because `git push origin notes/wfctl-review` and a `refs/*` glob push the notes ref without `refs/notes/` in the text.
- **PR-005, MINOR, open.** R9 rule 1 still doesn't require `notes` to be git's subcommand. Stands because a commit message containing "git notes add" may be refused, and no test catches a false refusal.
- **PR-006, MINOR, open.** `627-review-note-line-per-event.md` still says recording doesn't read the note first. Stands because R6 and the data model say it does, and the proposed record wasn't edited.
- **PR-009, MINOR, open.** `contracts/cli.md` defines no output or exit code for a failed local `record`. Stands because a ref lock held by another worktree has no stated behavior.
- **PR-010, MINOR, open.** The ruleset's `review` entry has no `integration_id`. Stands because any commit status named `review` satisfies it.
- **PR-011, MINOR, open.** R3's claim that the two readers agree is unchanged. Stands because they disagree once the state directory's last reviewed commit has left the branch, though both answers are safe.
- **PR-001, MAJOR, fixed.** Fixed by `review-record-in-git-notes.md` Consequences and its 2026-10-25 `revised` Log entry, and by the plan's Constitution Check, which now says the record was revised.
- **PR-002, MAJOR, fixed.** Fixed by R4 and the spec's Assumptions, which say the fallback needs FR-017a amended by the maintainer first and the ruleset waits until that is settled.
- **PR-003, MAJOR, fixed.** Fixed by FR-024 and R12, which give the printed output: `git switch release/v<version>`, then the person's own command.
- **PR-007, MINOR, fixed.** Fixed by the spec's Validation Strategy, which names a throwaway PR after merge.
- **PR-008, MINOR, fixed.** Fixed by `contracts/review-job.md` and the plan, which give `ci.yml` a top-level `permissions: contents: read`, with the `tag` job keeping `contents: write`.

## Review 2026-10-25T21:20Z

- Verdict: satisfied
- Reviewed: plan.md ac694568f3e22398d13e703fe85b79db0ce4e3cd, spec.md dc5887554dc92f2ef5b27058e7e6848678d947f2, .specify/memory/constitution.md absent, design.md a300e080b4678211c03622c9cc526026ac136c85, docs/architecture/design/627-unreviewed-takes-coverage.md 6952a2a5ce10f93a970695db193bacb0a5ffa297, docs/architecture/design/627-review-note-line-per-event.md 9630d75158af14e37fe67d866147ee1054355e44, docs/architecture/design/627-guard-blocks-note-writes.md 666b18a2720685bbb6174ea35aa39ea7d69b17ac, docs/architecture/review-record-in-git-notes.md 4e24a7da9f16a04447f2f681e9b307f6fac76d9a, docs/architecture/review-covers-unreviewed-commits.md 24c4b0e1c20ef1fa397c6e861eaf907785b28769, research.md c01fee80337a9a7786298e53b831b1ed225287b8, data-model.md 469957bb0c12a9250c332ad93f7d854cb9bca7e9, quickstart.md 7fe0a3660c89a83d3acb9562d54c181840bc9f69, contracts/cli.md c0508c86175149a21ae88c557d3f1fa9166d0d90, contracts/review-job.md f1e2e8a18e1c25528359e0722a62fb03801f204e, contracts/review-note.md dfdbb4b3891a514c88396ff9d958191cc203a765, checklists/requirements.md f0f311123f87812b1660c822ee055effe594c3f7, plan-review.plan.md 5c1cfa80e45835314be9571dab823427e4cc955f (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 16 · Fixed since the earlier review: 2
- Detail: /Users/andremarin/Development/wfctl-specs/627-ci-review-check/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-014, PR-019) |
| Requirements and traceability | Outstanding (PR-017, PR-018; PR-012 fixed) |
| Architecture and boundaries | Outstanding (PR-006, PR-016, PR-020) |
| Adversarial implementation and verification | Outstanding (PR-005, PR-009, PR-011, PR-015, PR-021, PR-022) |
| Security and reliability | Outstanding (PR-004, PR-010, PR-023; PR-013 fixed) |

### Findings

- **PR-017, MINOR, open.** `wfctl review groups` and `wfctl relay` still read only the working tree's `wfctl.json`. Stands because the review panel lists its groups with `review groups`, so it never starts a group the branch removed, and `relay` can't find that group's reviewers.
- **PR-018, MINOR, open.** FR-010 says the guard's results change only for a removed group. Stands because the edge cases also change an uncommitted group: today the guard requires it, and under the new list it doesn't.
- **PR-019, MINOR, open.** R10's `unreviewed` signature and the notes reader have no parameter that carries `--base` down to `trunk_refs`. Stands because neither R10 nor R14 says whether the single-branch refusal applies to a trunk named by `--base`.
- **PR-020, MINOR, open.** `review-record-in-git-notes.md` still says CI requires `main`'s groups, and R14 reads the base branch's. Stands because the record wasn't revised and the plan's Constitution Check doesn't mention R14.
- **PR-021, MINOR, open.** The plan's Summary says a PR that passes locally passes in CI. Stands because a stale local `origin/main` can give the local check a different group list.
- **PR-022, MINOR, open.** Neither the Validation Strategy nor the plan's test list covers FR-010 or FR-010a. Stands because the shared group list and `review start`'s wider list have no named test.
- **PR-023, MINOR, open.** Nothing checks that `edited` fires when GitHub retargets a stacked PR on its own, and the job has no `concurrency` group. Stands because a missed retarget leaves a stale result, and two overlapping runs on the same head are unordered.
- **PR-014, MINOR, open.** `_review_config.load` reads only from disk, and the plan's Project Structure doesn't list `_review_config.py`. Stands because the plan doesn't say whether the joined group list is validated as one declaration.
- **PR-015, MINOR, open.** A problem in the trunk's `review` key fails every PR, the fixing PR included. Stands because the guard and the sign-off now read the trunk's file too, so the guard also refuses `gh pr create` on every branch.
- **PR-016, MINOR, open.** R8 can't tell "no PR" from "`gh` is missing or `origin` isn't on GitHub". Stands because in such a repository every notes push prints the rerun warning.
- **PR-004, MINOR, open.** R9 rule 2 is unchanged. Stands because `git push origin notes/wfctl-review` and a `refs/*` glob push the notes ref without `refs/notes/` in the text.
- **PR-005, MINOR, open.** R9 rule 1 still doesn't require `notes` to be git's subcommand. Stands because a commit message containing "git notes add" may be refused, and no test catches a false refusal.
- **PR-006, MINOR, open.** `627-review-note-line-per-event.md` still says recording doesn't read the note first. Stands because R6 and the data model say it does.
- **PR-009, MINOR, open.** `contracts/cli.md` defines no output or exit code for a failed local `record`. Stands because a ref lock held by another worktree has no stated behavior.
- **PR-010, MINOR, open.** The ruleset's `review` entry has no `integration_id`. Stands because any commit status named `review` satisfies it.
- **PR-011, MINOR, open.** R3's claim that the two readers agree is unchanged. Stands because they disagree once the state directory's last reviewed commit has left the branch, though both answers are safe.
- **PR-012, MAJOR, fixed.** Fixed by FR-010, FR-010a, and R13, which give the guard, the sign-off, and `wfctl check reviews` one group list, and let `review start` run a removed group with the trunk's skill and reviewers.
- **PR-013, MAJOR, fixed.** Fixed by FR-015a, R14, and step 4 of `contracts/review-job.md`. CI passes `--base` from the event through `env:` and ignores the `trunk` key.

## Review 2026-10-25T22:41Z

- Verdict: satisfied
- Reviewed: plan.md 06cc9fce3aa12eca6167ac5b3f034b8157d64e89, spec.md 36130e83efd7cf26e04864e3fdf4ae84c899c41d, .specify/memory/constitution.md absent, design.md a300e080b4678211c03622c9cc526026ac136c85, docs/architecture/design/627-unreviewed-takes-coverage.md 6952a2a5ce10f93a970695db193bacb0a5ffa297, docs/architecture/design/627-review-note-line-per-event.md 2899b52b14cad409fc8524a1c28eb34f789988a0, docs/architecture/design/627-guard-blocks-note-writes.md 666b18a2720685bbb6174ea35aa39ea7d69b17ac, docs/architecture/review-record-in-git-notes.md 00389d02a47676c5a0efaa0f649ee16a4fd4ff05, docs/architecture/review-covers-unreviewed-commits.md 24c4b0e1c20ef1fa397c6e861eaf907785b28769, research.md 59cf1651e2f87ee14be4b63a276d06f15b2326f9, data-model.md 469957bb0c12a9250c332ad93f7d854cb9bca7e9, quickstart.md a563a80554c1892fdc4c411fb301657f43e31835, contracts/cli.md 03c3df17467cd06fed7c1c661930a09a0db79ff0, contracts/review-job.md c18409e6a0dda3726e7c4a86832605ad160d3369, contracts/review-note.md dfdbb4b3891a514c88396ff9d958191cc203a765, checklists/requirements.md f0f311123f87812b1660c822ee055effe594c3f7, plan-review.plan.md ac694568f3e22398d13e703fe85b79db0ce4e3cd (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 7 · Fixed since the earlier review: 12
- Detail: /Users/andremarin/Development/wfctl-specs/627-ci-review-check/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-026; PR-014, PR-019 fixed) |
| Requirements and traceability | Outstanding (PR-024; PR-017, PR-018 fixed) |
| Architecture and boundaries | Resolved (PR-006, PR-016, PR-020 fixed) |
| Adversarial implementation and verification | Outstanding (PR-005, PR-009, PR-011, PR-025; PR-015, PR-021, PR-022 fixed) |
| Security and reliability | Outstanding (PR-004; PR-010, PR-023 fixed) |

### Findings

- **PR-024, MINOR, open.** The CLI contract says `review check` still refuses a name outside the group list, but today `review_check_cmd` checks only the name's shape. Stands because the plan puts trunk lookups and their failures in front of the step that records the note, and nothing says so or tests it.
- **PR-025, MINOR, open.** The `relay` refusal's example, `security` and `style`, can't happen, since every file carries the built-in groups and rejects `style`. Stands because the only real clash is a group renamed on the branch, where the "rename one" remedy doesn't help.
- **PR-026, MINOR, open.** `contracts/review-job.md` says quickstart step 4 checks `integration_id` 15368, and step 4 doesn't mention it. Stands because FR-018 and the plan's ruleset and test lines don't name the id either, so it could be left out.
- **PR-009, MINOR, open.** The contract now covers a failed note write in `review check`, but not in the sign-off. Stands because running the sign-off again finds nothing unreviewed and records nothing, so CI stays red.
- **PR-004, MINOR, open.** R9 rule 2 is unchanged. Stands because `git push origin notes/wfctl-review` and a `refs/*` glob push the notes ref without `refs/notes/` in the text. Left open by the author as a known limit of the guard's text match.
- **PR-005, MINOR, open.** R9 rule 1 still doesn't require `notes` to be git's subcommand. Stands because a commit message mentioning "git notes add" may be refused. Left open by the author for the same reason.
- **PR-011, MINOR, open.** R3 still says the two readers agree. Stands because they differ once the state directory's last reviewed commit has left the branch, though both answers are safe. Left open by the author.
- **PR-006, MINOR, fixed.** Fixed by the design record's Consequences, which say recording reads the note only to skip a duplicate.
- **PR-010, MINOR, fixed.** Fixed by `contracts/review-job.md`, which gives the ruleset entry `integration_id` 15368.
- **PR-014, MINOR, fixed.** Fixed by the plan's Project Structure, which lists `_review_config.py`, and by R13, which validates each file alone and joins by name.
- **PR-015, MINOR, fixed.** Fixed by R13, which keeps a broken trunk `review` key a failure and names the `AGENTS.md` recovery.
- **PR-016, MINOR, fixed.** Fixed by R8, which reruns and prints nothing when `gh` is missing or `origin` isn't on GitHub.
- **PR-017, MINOR, fixed.** Fixed by FR-010a, which now covers `review groups` and `relay`.
- **PR-018, MINOR, fixed.** Fixed by FR-010, which lists all three cases where the guard's result changes.
- **PR-019, MINOR, fixed.** Fixed by R10's `trunk` keyword and R14's single-branch skip.
- **PR-020, MINOR, fixed.** Fixed by the record's Consequences and Log entry, and by the Constitution re-check line naming R14.
- **PR-021, MINOR, fixed.** Fixed by the narrowed Summary and R13's paragraph on a stale fetch.
- **PR-022, MINOR, fixed.** Fixed by the Validation Strategy and the new test lines in the plan.
- **PR-023, MINOR, fixed.** Fixed by quickstart step 5, R14's post-merge check, and the job's `concurrency` group.
