# Plan review scan for #359

## Review 2026-10-14T19:28Z

- Verdict: satisfied
- Reviewed: plan.md 252d08ae4f6b5ddac0ef8ec96c56f51e489e59bc, spec.md 68507ea870e0226a517cc6af694c083dd4630d8e, .specify/memory/constitution.md absent, design.md c7a193b7d570f80c83226c773e520322697ea402, docs/architecture/design/store-specs-implement-pass.md 67ebbd9713bc4f7aaf8c69f62c7934979a6b6eee, docs/architecture/design/store-specs-at-removal.md e0c8ce6b15812f6151f465305652a60d27048129, docs/architecture/design/store-specs-merges-before-push.md d8dacdaa617398f9aae737ad02a355de3b8e1091, docs/architecture/spec-storage-read-from-git.md e95749c063e9aac84c9aa1f23b205c3e4c7e8638, research.md e174dcd191aafc8f632fb7499cdef942e0c77f0a, data-model.md 11c80443f7a309e86dc1e02f12a73d1e41ff8c99, contracts/cli.md 1c88e34232fff7e384257a6012c716a587003bba, quickstart.md d1ff4edccde503ea9a4f869aa532a18d76e431f5
- Review type: full (no earlier report)
- Open: BLOCKER 0 · MAJOR 2 · MINOR 10 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/359-push-specs-to-trunk/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-009) |
| Requirements and traceability | Outstanding (PR-006, PR-008) |
| Architecture and boundaries | Outstanding (PR-002, PR-012) |
| Adversarial implementation and verification | Outstanding (PR-005, PR-007, PR-010, PR-011) |
| Security and reliability | Outstanding (PR-001, PR-003, PR-004) |

### Findings

- **PR-001, MAJOR, open.** If any path is staged in the spec store, every store's merge fails, even when the remote never touched that path. The reviewer reproduced this with git 2.44.0, where `git merge --no-edit @{u}` exits 2 with another path staged. FR-001 leaves staged paths in place on purpose, but research R8 treats the refusal as a rare case. No planned test combines a staged path with a remote that has moved.
- **PR-002, MAJOR, open.** After the host refuses the push, `report-block store-specs` holds `implement`, and a blocked `implement` with no open tasks routes to `wfctl verify`. The hold lifts only when a `store-specs` action is recorded. The plan doesn't say whether a successful `wfctl store specs` records one, so a store run by hand can leave the hold in place.
- **PR-003, MINOR, open.** Research R7 relies on `GIT_TERMINAL_PROMPT=0`, which covers only git's HTTPS credential prompt. pfms's spec store pushes over SSH, and SSH prompts for a passphrase or a host key on its own. As a result, a store run from `pre_remove` there can still wait at a prompt until the 60-second timeout.
- **PR-004, MINOR, open.** No autouse fixture keeps a test away from the developer's real spec store. A later test that runs `store specs` without `WFCTL_SPEC_DIR` set would commit and push the real spec dir, from a suite that is meant to run offline.
- **PR-005, MINOR, open.** Research R13 expects the regenerated payload snapshot to gain `store-specs` entries. The snapshot records step rows only, without sub-steps, so the file shouldn't change and the planned check has nothing to compare.
- **PR-006, MINOR, open.** In a layout with nowhere to push, the pass reads `skipped` and puts its text in `display`. The default `wfctl status` hides a skipped pass that carries no warning, so the "not backed up" text shows only with `--json` or `--all`.
- **PR-007, MINOR, open.** The message "the next `wfctl store specs` from any branch pushes it" holds only for a store that has files of its own to commit. FR-009 says an already-stored spec dir pushes nothing, so a commit left unpushed at removal has no command that pushes it, and `check specs` keeps exiting 1.
- **PR-008, MINOR, open.** Quickstart §6 times only the two git commands from research R3. The reader also works out the layout first, which takes about six more git calls, and the spec's validation step times `wfctl status` with and without the pass.
- **PR-009, MINOR, open.** data-model.md and contracts/cli.md give different text for the "committed, not backed up" outcome. Also, the text for a store with no upstream says "committed" even though the pipeline never runs the store in that layout.
- **PR-010, MINOR, open.** The plan has no rule for which fetch and push failures read "unreachable", "push refused", or "git failed". For example, a credential failure with prompts turned off would read "unreachable".
- **PR-011, MINOR, open.** After a conflict, the unmerged commit stays, so every branch's next store meets the same conflict. A store killed partway through a merge leaves `MERGE_HEAD` behind, and the next commit fails. The plan names no recovery step for either case.
- **PR-012, MINOR, open.** `committable` will import `_spec_store`, and no test covers the import cost on that path. The guard runs before every Bash call, so a heavy module-level import in `_spec_store` would slow every call.

## Review 2026-10-14T19:50Z

- Verdict: satisfied
- Reviewed: plan.md b4713961ce2fa17f49651e18c0cbe16a57851833, spec.md 68507ea870e0226a517cc6af694c083dd4630d8e, .specify/memory/constitution.md absent, design.md c08921165ed069a8150511b76ededfe5f029282e, docs/architecture/design/store-specs-implement-pass.md 67ebbd9713bc4f7aaf8c69f62c7934979a6b6eee, docs/architecture/design/store-specs-at-removal.md 9a8ab88a08fa68b6f36465310ca2252e355b1718, docs/architecture/design/store-specs-merges-before-push.md d8dacdaa617398f9aae737ad02a355de3b8e1091, docs/architecture/spec-storage-read-from-git.md e95749c063e9aac84c9aa1f23b205c3e4c7e8638, research.md dec1c550ba9675426768361825a93c6425dafef2, data-model.md 0950c40bdb5b3fe6a927f3c27a237f531bd578a8, contracts/cli.md ccd97adcf06266e68b558fe83114076b9d09682c, quickstart.md d1ff4edccde503ea9a4f869aa532a18d76e431f5, plan-review.plan.md 252d08ae4f6b5ddac0ef8ec96c56f51e489e59bc (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 16 · Fixed since the earlier review: 2
- Detail: /Users/andremarin/Development/wfctl-specs/359-push-specs-to-trunk/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-009, PR-019) |
| Requirements and traceability | Outstanding (PR-006, PR-008) |
| Architecture and boundaries | Outstanding (PR-013, PR-012, PR-017; PR-002 fixed) |
| Adversarial implementation and verification | Outstanding (PR-005, PR-007, PR-010, PR-011, PR-014, PR-016, PR-018) |
| Security and reliability | Outstanding (PR-003, PR-004, PR-015; PR-001 fixed) |

### Findings

- **PR-013, MAJOR, open.** If #40 merges first, the plan skips its removal step and the archive tests with it, including "a failed push at removal warns and exits 0". #40's record says `wfctl hook worktree-remove` exits non-zero when `store specs` refuses, and research R6 has `store specs` exit 1 on a failed push or a lock timeout. Nothing says which command turns that failure into a warning, so FR-021 and SC-003 are at risk.
- **PR-001, MAJOR, fixed.** Fixed by research R8, which now says a file staged anywhere blocks the merge, by the new `merge_blocked_staged` outcome that names the folders and a remedy, and by two new tests.
- **PR-002, MAJOR, fixed.** Fixed by research R15. A store that pushes records the `store-specs` action, which lifts the host block, and a blocked `implement` with an outstanding pass routes to that pass with `auto` false.
- **PR-003, MINOR, open.** Research R7 and the Constraints line still say the store never prompts. `GIT_TERMINAL_PROMPT=0` doesn't stop SSH prompts, and pfms's spec store pushes over SSH.
- **PR-004, MINOR, open.** The test suite's autouse fixtures still don't keep a test away from the developer's real spec store.
- **PR-005, MINOR, open.** Implementation step 6 and research R13 still expect the payload snapshot to gain `store-specs` entries. The snapshot records step rows only, so it won't change.
- **PR-006, MINOR, open.** The text for a layout with nowhere to push is still hidden by the default `wfctl status`, and the plan doesn't say that this is a choice.
- **PR-007, MINOR, open.** The contract still says "the next store from any branch pushes it". A branch with nothing new to commit pushes nothing (FR-009).
- **PR-008, MINOR, open.** Quickstart §6 and the Performance Goals still count two git commands. The layout check adds more calls, and `wfctl status` is never timed without the pass.
- **PR-009, MINOR, open.** data-model.md and contracts/cli.md still give different text for `committed_not_backed_up`, and the pass's text still says "committed" when nothing was committed.
- **PR-010, MINOR, open.** There's still no rule for which credential, deleted-branch, or permission failures read `not_pushed`, `push_refused`, or `git_failed`.
- **PR-011, MINOR, open.** The conflict output still names no remedy, and a store killed partway through a merge leaves `MERGE_HEAD` behind, which blocks every branch.
- **PR-012, MINOR, open.** No test covers the import cost on the guard's `git commit` path after `owns_branch` moves into `_spec_store`.
- **PR-014, MINOR, open.** Research R8 doesn't say how a refused merge is told apart from a conflict. After a conflict, `git diff --cached` prints files too, so checking it first would skip `git merge --abort`. Whether `MERGE_HEAD` exists is the test that separates them.
- **PR-015, MINOR, open.** An untracked file that the upstream adds is a fourth kind of refusal, with nothing staged and a different message from git. It falls through to the "local edits" text, which is plausible here given the 58 untracked spec dirs.
- **PR-016, MINOR, open.** The new test expects the first branch's next store to merge and push. The owning branch's push already carried that commit, so the next store reads `already_stored`.
- **PR-017, MINOR, open.** Research R15 routes on any outstanding pass, not on the `store-specs` block. As a result, a `push` block on a finished `implement`, or a pass a repository declares under `implement`, also routes to the pass, which reverses the order the `next_step_content` docstring states. Only the `store-specs` case is tested.
- **PR-018, MINOR, open.** If the spec dir reaches the remote another way, a rerun reads `already_stored` and records nothing, so the hold stays and routing goes back to `wfctl verify`. Running `wfctl report-action store-specs` still recovers it.
- **PR-019, MINOR, open.** Technical Context, the `session-state-is-re-derived` gate, and data-model.md say git history is the only thing written. Research R15 also appends an action event to the session log.

## Review 2026-10-14T20:24Z

- Verdict: satisfied
- Reviewed: plan.md 7bbbaa0ea4dac2c02cec78bb679faeedfbda0181, spec.md 68507ea870e0226a517cc6af694c083dd4630d8e, .specify/memory/constitution.md absent, design.md c08921165ed069a8150511b76ededfe5f029282e, docs/architecture/design/store-specs-implement-pass.md 67ebbd9713bc4f7aaf8c69f62c7934979a6b6eee, docs/architecture/design/store-specs-at-removal.md 9a8ab88a08fa68b6f36465310ca2252e355b1718, docs/architecture/design/store-specs-merges-before-push.md d8dacdaa617398f9aae737ad02a355de3b8e1091, docs/architecture/spec-storage-read-from-git.md e95749c063e9aac84c9aa1f23b205c3e4c7e8638, research.md ea3a2f345c55b8ab0714feeb867982d91dda0a46, data-model.md 348496389782b6211a6e5e85af9f373ddbc3ae6d, contracts/cli.md ccd97adcf06266e68b558fe83114076b9d09682c, quickstart.md d1ff4edccde503ea9a4f869aa532a18d76e431f5, plan-review.plan.md b4713961ce2fa17f49651e18c0cbe16a57851833 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 18 · Fixed since the earlier review: 1
- Detail: /Users/andremarin/Development/wfctl-specs/359-push-specs-to-trunk/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-009, PR-019, PR-020, PR-021) |
| Requirements and traceability | Outstanding (PR-006, PR-008, PR-021) |
| Architecture and boundaries | Outstanding (PR-012, PR-017, PR-020; PR-002 and PR-013 fixed) |
| Adversarial implementation and verification | Outstanding (PR-005, PR-007, PR-010, PR-011, PR-014, PR-016, PR-018; PR-001 fixed) |
| Security and reliability | Outstanding (PR-003, PR-004, PR-015, PR-020; PR-001 and PR-013 fixed) |

### Findings

- **PR-013, MAJOR, fixed.** Fixed by research R6 and the data model's store result, which say removal reads `StoreResult.stops_removal` rather than the exit code. That property is false for every outcome this branch adds, so a failed push, a lock timeout, or a refused merge warns and lets removal go ahead. #40's record at `448301e` says the same, and implementation step 7 keeps the removal tests in either merge order.
- **PR-020, MINOR, open.** Research R6 and the data model define `stops_removal` in two different ways. R6 says it is true when the spec dir is inside the worktree and was not copied out, while the data model says it is false for every outcome, `not_applicable` included. On this branch the case never reaches removal. Once #40 merges, the hook runs `store specs` in every layout, and if `not_applicable` comes back before #40's copy-out runs, the data model's rule lets removal delete the only copy of the spec dir.
- **PR-021, MINOR, open.** The `archive-specs` contract says it exits 0 whenever the spec dir is outside the worktree. #40's record makes it exit non-zero when `archive unsaved` refuses, for example on uncommitted edits. As a result, the removal tests the plan moves onto the hook need a clean worktree, and the plan doesn't say so.
- **PR-003 to PR-012 and PR-014 to PR-019, MINOR, open.** The revision didn't touch any of them, so each stands on the evidence the 19:50Z section gives.

## Review 2026-10-14T22:11Z

- Verdict: satisfied
- Reviewed: plan.md 310c0e01bd67952d7bcf01677357495b4ee635a0, spec.md 68507ea870e0226a517cc6af694c083dd4630d8e, .specify/memory/constitution.md absent, design.md c08921165ed069a8150511b76ededfe5f029282e, docs/architecture/design/store-specs-implement-pass.md 67ebbd9713bc4f7aaf8c69f62c7934979a6b6eee, docs/architecture/design/store-specs-at-removal.md 9a8ab88a08fa68b6f36465310ca2252e355b1718, docs/architecture/design/store-specs-merges-before-push.md d8dacdaa617398f9aae737ad02a355de3b8e1091, docs/architecture/spec-storage-read-from-git.md e95749c063e9aac84c9aa1f23b205c3e4c7e8638, research.md c60cec9d68d7bfa7fcf95b4a91302bf8a80987e7, data-model.md 07cf9a543cba5cfc65fa9d50ad662eb75d165b65, contracts/cli.md 1f7430d6d0254e2187ac61f8d151e15748ea8054, quickstart.md d1ff4edccde503ea9a4f869aa532a18d76e431f5, plan-review.plan.md 7bbbaa0ea4dac2c02cec78bb679faeedfbda0181 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 17 · Fixed since the earlier review: 5
- Detail: /Users/andremarin/Development/wfctl-specs/359-push-specs-to-trunk/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-009, PR-019) |
| Requirements and traceability | Outstanding (PR-006, PR-008; PR-021 fixed) |
| Architecture and boundaries | Outstanding (PR-012, PR-023, PR-025; PR-002, PR-013, PR-017 and PR-020 fixed) |
| Adversarial implementation and verification | Outstanding (PR-005, PR-007, PR-010, PR-011, PR-018, PR-022; PR-001, PR-014 and PR-016 fixed) |
| Security and reliability | Outstanding (PR-003, PR-004, PR-015, PR-024; PR-001 fixed) |

### Findings

- **PR-014, MINOR, fixed.** Fixed by research R8 and the plan's store entry, which check for `MERGE_HEAD` before reading `git diff --cached`, so a conflict is never read as staged files. The conflict test now asserts that order.
- **PR-016, MINOR, fixed.** Fixed by the plan's test list. The owning branch's push now carries the first branch's kept commit, and the first branch's next store is expected to read `already_stored`.
- **PR-017, MINOR, fixed.** Fixed by research R15, the plan, and the status contract. Only a block filed for the outstanding pass's own action routes to that pass, and any other block routes as it does today. Tests cover both sides.
- **PR-020, MINOR, fixed.** Fixed by research R6 and the data model, which now define `stops_removal` the same way. It matches #40's record at `2e9f124`, which also stops removal on `not_applicable` for a spec dir inside the worktree.
- **PR-021, MINOR, fixed.** Fixed by the `archive-specs` contract, which limits its exit rule to the store's half, and by implementation step 7, which starts the moved removal tests from a clean worktree.
- **PR-022, MINOR, open.** Research R8 runs `git diff --name-only --diff-filter=U` to name the conflicted folders after `git merge --abort`. The reviewer reproduced this with git 2.44.0, and after the abort that command prints nothing, so the conflict output would name no folder.
- **PR-023, MINOR, open.** #40's record at `2e9f124` says `store specs` run by hand exits 1 for every outcome that stops removal, which now includes `not_applicable` inside the worktree. This plan exits 0 for that outcome in research R6 and R11, the data model, and the contract. The two records agree on `stops_removal` but not on the exit code.
- **PR-024, MINOR, open.** A spec store can be its own checkout sitting inside the code's worktree, and nothing in research R2 rules that out. There, the rule as written stops every removal, even after `stored`. Read as an outcome-only rule instead, a failed push would let removal delete the unpushed commit. The plan covers neither case.
- **PR-025, MINOR, open.** Two places call `next_step_content`: `build_report`, and the `cli.py` command that writes `next-step.md`. The plan passes `block_action` from the first only, and no test reads `next-step.md`, so the second would keep routing a `store-specs` block to `wfctl verify`.
- **PR-003 to PR-012, PR-015, PR-018 and PR-019, MINOR, open.** The revision didn't touch any of them, so each stands on the evidence the 19:50Z section gives.

## Review 2026-10-14T23:51Z

- Verdict: satisfied
- Reviewed: plan.md 51905313e32de76891bfd0e7addbd656ac0acedd, spec.md 68507ea870e0226a517cc6af694c083dd4630d8e, .specify/memory/constitution.md absent, design.md c08921165ed069a8150511b76ededfe5f029282e, docs/architecture/design/store-specs-implement-pass.md 67ebbd9713bc4f7aaf8c69f62c7934979a6b6eee, docs/architecture/design/store-specs-at-removal.md 9a8ab88a08fa68b6f36465310ca2252e355b1718, docs/architecture/design/store-specs-merges-before-push.md d8dacdaa617398f9aae737ad02a355de3b8e1091, docs/architecture/spec-storage-read-from-git.md e95749c063e9aac84c9aa1f23b205c3e4c7e8638, research.md 9d45be6f7405e38e83ae923af49d616c9b359ab5, data-model.md 6ea70cff0e8568cd36ef2e88a3664910f3b8ad0f, contracts/cli.md 1f7430d6d0254e2187ac61f8d151e15748ea8054, quickstart.md d1ff4edccde503ea9a4f869aa532a18d76e431f5, plan-review.plan.md 310c0e01bd67952d7bcf01677357495b4ee635a0 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 17 · Fixed since the earlier review: 3
- Detail: /Users/andremarin/Development/wfctl-specs/359-push-specs-to-trunk/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-009, PR-019, PR-028) |
| Requirements and traceability | Outstanding (PR-006, PR-008) |
| Architecture and boundaries | Outstanding (PR-012, PR-027; PR-023 and PR-025 fixed) |
| Adversarial implementation and verification | Outstanding (PR-005, PR-007, PR-010, PR-011, PR-018, PR-024, PR-026; PR-022 fixed) |
| Security and reliability | Outstanding (PR-003, PR-004, PR-015, PR-024) |

### Findings

- **PR-022, MINOR, fixed.** Fixed by research R8, which now reads the conflicted paths before `git merge --abort` and says why. After the abort, that command prints nothing.
- **PR-023, MINOR, fixed.** Fixed by research R6, the data model, and a new test, which keep `not_applicable` at exit 0 when `store specs` is run by hand. #40's record at `b3fc797` now says the same.
- **PR-025, MINOR, fixed.** Fixed by research R15 and the plan, which name both callers of `next_step_content`, `build_report` and `next_cmd`, and by a routing test that reads `next-step.md` as well as `status --json`.
- **PR-026, MINOR, open.** `wfctl resume` also writes `next-step.md`, and it goes through `build_report`. As a result, the new test can pass while `next_cmd` still drops `block_action`, unless the test says the file it reads is the one `wfctl next` writes.
- **PR-027, MINOR, open.** Research R6 says #40 exits 1 "only" for a copy-out refusal or a spec store failure, but #40's record never says "only". Its reason for exit 1, that a script can tell the spec files aren't backed up, describes `committed_not_backed_up` exactly, and this plan exits 0 there. So the two records still disagree for a spec store with no upstream branch.
- **PR-028, MINOR, open.** The sentences added to research R15 leave "Its docstring" pointing at `next_cmd`. The quoted text is in `next_step_content`'s docstring.
- **PR-003 to PR-012, PR-015, PR-018, PR-019 and PR-024, MINOR, open.** The revision didn't touch any of them, so each stands on the evidence its earlier section gives.
