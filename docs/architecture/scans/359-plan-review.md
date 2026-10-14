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
