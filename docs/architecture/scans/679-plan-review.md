# Plan review scan for #679

## Review 2026-10-31T20:32Z

- Verdict: satisfied
- Reviewed: plan.md 1a8a92e8e6e5326803d8a7f19fa30a5244cfec19, spec.md 2c0e80a1bcce31128fe547d0a34de60ddb8eea2d, .specify/memory/constitution.md absent, design.md 44fd52bdb194cc3e87d4eae670590c1dad7a0637, docs/architecture/design/679-review-is-its-own-step.md 67753ae019ea66ade8dbedb4cc81217f72e9ba51, docs/architecture/design/679-no-spec-skips-spec-rows.md 162d78b6c1499a8a111d1aeea45b91823ebbde1c, docs/architecture/review-step-reads-guard-state.md 7193ced53f18edacdd6c6b8c72fa0896d1609dba, docs/architecture/every-change-answers-spec-question.md 044685f60fa49a70975ab2bd47f0926834bcff99, research.md 2353c706e64876f481554cfd3b39b6e4ea0b5e7b, data-model.md 46ac43aa193f7dd3977a11a9cc1fc2284cec4907, contracts/cli.md bd6f2a3d8bc8b9a39562cd1b1f36d978838f673c, quickstart.md 25d27488732d1d8cb8bcaf30986086ad3bb004a9, AGENTS.md 5090e1cb455f4d0293a1938504fae5d200f59ae7
- Review type: full (no earlier report and no plan copy)
- Open: BLOCKER 0 · MAJOR 4 · MINOR 11 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/679-review-step-after-implement/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-003, PR-015) |
| Requirements and traceability | Outstanding (PR-002, PR-008, PR-009, PR-010, PR-011) |
| Architecture and boundaries | Outstanding (PR-004, PR-006, PR-012, PR-014) |
| Adversarial implementation and verification | Outstanding (PR-001, PR-005, PR-007, PR-013) |
| Security and reliability | Clear |

### Findings

- **PR-001, MAJOR, open.** When `review.rounds` is 0 or the round cap is reached, the review row stays automatic and routes to `/fanning-out-code-review`, but `review start` refuses with `RoundCapReached`. Stands because only a person's sign-off clears that state, so an unattended run repeats until the stall bound stops it.
- **PR-002, MAJOR, open.** User Story 1 scenario 5 says review reads done exactly when the guard allows the PR. Stands because `_judge` also refuses for reasons outside review coverage, such as a level-2 record still `proposed`, so status can read complete while the guard refuses.
- **PR-003, MAJOR, open.** The plan says the contract regenerate command updates the payload contract to 1.4. Stands because the only story-complete fixture has no `origin`, so it now stops at review, `current`, `next_command`, and `auto` lose their null type, and the bump asks for 2.0. No fixture fills `no_spec`, and `payload_of` in `tests/conftest.py` needs the key.
- **PR-004, MAJOR, open.** The plan skips `_pass_states` on the seven spec rows. Stands because their `sub_steps` come back empty, which breaks the rule that every step lists all its passes. `_pass_states` already marks passes skipped when the step reads skipped.
- **PR-005, MINOR, open.** `head_commit()` runs outside `pending_at_head`, so a branch with no commits crashes status, and the tests that assert "Story complete" aren't listed for update.
- **PR-006, MINOR, open.** `check-body` requires the no-spec reason even when a spec artifact makes the pipeline ignore it, so two places decide whether a "no" is in effect.
- **PR-007, MINOR, open.** The stall digest reads only spec.md, plan.md, and tasks.md, so progress at the review step reads as no progress.
- **PR-008, MINOR, open.** On a no-spec branch, the "artifacts written" fact reads unmet for good, and the plan doesn't say whether that's intended.
- **PR-009, MINOR, open.** design.md's level-1 output has a `wfctl spec none` hint under `next` that neither the spec nor the plan produces, and the review annotation differs between design.md and contracts/cli.md.
- **PR-010, MINOR, open.** spec.md's first clarification still says the reason goes in the "Needs a spec?" section, while FR-017 and research R5 accept it anywhere in the body.
- **PR-011, MINOR, open.** SC-004 has no timing step in the plan or the quickstart.
- **PR-012, MINOR, open.** Research R9's import-cycle contingency can't happen, since `_review` already imports `_review_config` and `_paths`.
- **PR-013, MINOR, open.** An unreadable review config still routes to `/fanning-out-code-review` with no remedy, and that command fails on the same error.
- **PR-014, MINOR, open.** Adding `review` to `_STEPS` makes `steps.review` a valid declaration in `wfctl.json`, a new public option nobody decided on.
- **PR-015, MINOR, open.** `679-no-spec-skips-spec-rows.md` says in Consequences and Verification that each skipped row carries the reason, which contradicts its Decision and FR-010.

The security and reliability lens applied and found nothing. The guard still enforces the rule and doesn't change, and the review row only reads what the guard reads.

## Review 2026-10-31T22:30Z

- Verdict: satisfied
- Reviewed: plan.md 16f689075dacfb51f780e2a839cf116a6ccb5371, spec.md b03b68ac58e61b4bc492aba88b37c4676a058d41, .specify/memory/constitution.md absent, design.md c40e7d98e0d94c153127f24c436fc60a807ef76a, docs/architecture/design/679-review-is-its-own-step.md 67753ae019ea66ade8dbedb4cc81217f72e9ba51, docs/architecture/design/679-no-spec-skips-spec-rows.md b97f1ba3a4e2abe30373155a8674108d16916787, docs/architecture/review-step-reads-guard-state.md 695fa83fb1be99bf988089aff533a43459412005, docs/architecture/every-change-answers-spec-question.md 044685f60fa49a70975ab2bd47f0926834bcff99, docs/architecture/design/498-the-fix-line-travels-with-the-reason.md bda01a0bf2a62ded2aa18ba6f33e2c2b0f34320e, research.md a23d619e7104648a372b4362f21b03297ea82f2d, data-model.md 715a0681ae1167d377439d6cb76f38573d38c6bb, contracts/cli.md 3d7bc4daaa6841d0f557984d7286f3ea8a8ea775, quickstart.md 8c5d3c0645bce61c85a0eac9658210c796b2c95b, AGENTS.md 5090e1cb455f4d0293a1938504fae5d200f59ae7, plan-review.plan.md 1a8a92e8e6e5326803d8a7f19fa30a5244cfec19 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 6 · Fixed since the earlier review: 15
- Detail: /Users/andremarin/Development/wfctl-specs/679-review-step-after-implement/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Resolved (PR-003, PR-015 fixed) |
| Requirements and traceability | Outstanding (PR-019, PR-021) |
| Architecture and boundaries | Outstanding (PR-016, PR-017) |
| Adversarial implementation and verification | Outstanding (PR-016, PR-017, PR-018, PR-020) |
| Security and reliability | Clear |

### Findings

- **PR-001 to PR-015, fixed.** The plan now blocks the review row on a capped group, narrows scenario 5 to unreviewed commits, plans the `no_spec` fixture state and the `payload_of` key, keeps skipped rows' passes, reads HEAD inside `pending_at_head`, shares `spec_in_effect` with `check-body`, adds the review state to the stall digest, reads the artifacts fact `n/a` on a no-spec branch, matches design.md's annotation strings, notes R5 under the clarification, times SC-004, drops the cycle contingency, gives the error reading a remedy, refuses `steps.review`, and matches the no-spec record to its Decision.
- **PR-016, MINOR, open.** Computing `capped` in the shared function makes `resolve_round_dir` create its folder and adds a trunk read the guard throws away. Stands because the plan computes it on every call.
- **PR-017, MINOR, open.** `HeadCoverage.error` is a string, so the remedy has to be chosen by matching message text, and `git fetch origin` doesn't fix `NoTrunk`, whose message says to set `trunk` in `wfctl.json`.
- **PR-018, MINOR, open.** Fixtures with no `origin` fall back to the local `main` as trunk, so `review` reads done instead of erroring. Stands because the plan's test changes assume a no-trunk error, and scenarios 1, 4, and 5 need a feature branch with commits off the trunk.
- **PR-019, MINOR, open.** `not reviewed yet` gives no count, which FR-005 requires, and it misdescribes a branch with a person's approval but no completed run.
- **PR-020, MINOR, open.** `contracts/cli.md` shows the cap reason on the capped step's line, while the console prints `display` there.
- **PR-021, MINOR, open.** SC-004 names the longest open branch, and the plan measures this branch without recording the substitution.

## Review 2026-10-31T23:09Z

- Verdict: satisfied
- Reviewed: plan.md d4f3e65d06a1ef031b3974949b3496cfef082de1, spec.md f361e22239992c19c69256d8650b64f0d83eb0cb, .specify/memory/constitution.md absent, design.md baa914c455c5faea16f4e08d8a7efea379901b26, docs/architecture/design/679-review-is-its-own-step.md 67753ae019ea66ade8dbedb4cc81217f72e9ba51, docs/architecture/design/679-no-spec-skips-spec-rows.md b97f1ba3a4e2abe30373155a8674108d16916787, docs/architecture/review-step-reads-guard-state.md 94ab0f6dbcfea44ae996a29e81922802fa25efec, docs/architecture/every-change-answers-spec-question.md f5c2177ef30ae80b16043c1ecfc733f9102764f9, docs/architecture/design/498-the-fix-line-travels-with-the-reason.md bda01a0bf2a62ded2aa18ba6f33e2c2b0f34320e, research.md 9e80dc0b6b65015e50196c47d5330018ffa0ce91, data-model.md e3b5c3863dff3d4d6c83f0acdaf7747132dbb3cb, contracts/cli.md bd5c70b15f2cc30a7659597321e3327a245ccfb2, quickstart.md 32368240bb1e255abb05557bd2a4f4fea8271ac7, AGENTS.md 5090e1cb455f4d0293a1938504fae5d200f59ae7, plan-review.plan.md 16f689075dacfb51f780e2a839cf116a6ccb5371 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 4 · Fixed since the earlier review: 6
- Detail: /Users/andremarin/Development/wfctl-specs/679-review-step-after-implement/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-026) |
| Requirements and traceability | Resolved (PR-019, PR-021 fixed) |
| Architecture and boundaries | Outstanding (PR-024) |
| Adversarial implementation and verification | Outstanding (PR-022, PR-023, PR-025) |
| Security and reliability | Clear |

### Findings

- **PR-016 to PR-021, fixed.** `capped` is computed only when status asks for it, without creating the round-tally folder; the remedy is set where the error is caught; the test plan matches the trunk fallback for git-backed fixtures; the status line carries a count; the capped reading shows its reason; and SC-004 names this branch with its commit count.
- **PR-022, MAJOR, open.** Four tests assert story complete on a directory with no git repository, so the review row reads an error and they fail: `tests/test_pipeline_state_names.py`, `tests/test_decompose_issues.py`, `tests/test_tasks_hold_a_task.py`, and `tests/test_completion_record.py`. Stands because the plan says the first passes unedited, and its fallback, a sign-off at HEAD, needs a HEAD.
- **PR-023, MINOR, open.** `required_at` also reports problems in the branch's own `wfctl.json`, and the config remedy always points at the trunk's copy.
- **PR-024, MINOR, open.** The guard's record check needs `trunk_ref` after the moved calls, and `HeadCoverage` doesn't return it, so `_judge` would read the trunk a second time.
- **PR-025, MINOR, open.** `since` names the last reviewed commit even when a later sign-off moved where the count starts, and after a rebase it can name a commit the branch no longer has.
- **PR-026, MINOR, open.** `research.md §R1` still describes `HeadCoverage` with two fields, where the plan and data model give five.

## Review 2026-11-01T04:13Z

- Verdict: satisfied
- Reviewed: plan.md 24def0b7e215005de4c46763809a60f63b4280e1, spec.md f361e22239992c19c69256d8650b64f0d83eb0cb, .specify/memory/constitution.md absent, design.md baa914c455c5faea16f4e08d8a7efea379901b26, docs/architecture/design/679-review-is-its-own-step.md 67753ae019ea66ade8dbedb4cc81217f72e9ba51, docs/architecture/design/679-no-spec-skips-spec-rows.md b97f1ba3a4e2abe30373155a8674108d16916787, docs/architecture/review-step-reads-guard-state.md 94ab0f6dbcfea44ae996a29e81922802fa25efec, docs/architecture/every-change-answers-spec-question.md f5c2177ef30ae80b16043c1ecfc733f9102764f9, docs/architecture/design/498-the-fix-line-travels-with-the-reason.md bda01a0bf2a62ded2aa18ba6f33e2c2b0f34320e, research.md 9034e0e4be270dad95e9cede3accff6b10ba3b5b, data-model.md 8b86d9d6fc7dc62d143ea628cf6d7490e302adf9, contracts/cli.md ebc4a49b51a1f63c4e42cc6977bedee2384cad3f, quickstart.md 32368240bb1e255abb05557bd2a4f4fea8271ac7, AGENTS.md 5090e1cb455f4d0293a1938504fae5d200f59ae7, plan-review.plan.md d4f3e65d06a1ef031b3974949b3496cfef082de1 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 2 · Fixed since the earlier review: 5
- Detail: /Users/andremarin/Development/wfctl-specs/679-review-step-after-implement/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Resolved (PR-026 fixed) |
| Requirements and traceability | Outstanding (PR-028) |
| Architecture and boundaries | Resolved (PR-024 fixed) |
| Adversarial implementation and verification | Outstanding (PR-027) |
| Security and reliability | Clear |

### Findings

- **PR-022 to PR-026, fixed.** The four story-complete tests outside a git repository get `git_repo(tmp_path)` and a feature branch name, which the reviewer ran and confirmed reach story complete. The config remedy names whichever `wfctl.json` the error names. `HeadCoverage` carries `trunk_ref`, so the guard reads the trunk once. `since` is the first parent of the oldest unreviewed commit. Research R1 lists the six fields.
- **PR-027, MINOR, open.** Two git reads that `since` adds can fail: `is_under` on a last reviewed commit that `git gc` pruned after a rebase, and `<root>^` when a merge brings in an unrelated history. Stands because the plan turns either failure into an error for the whole reading, which blocks the review row and makes the guard refuse with a git error. The guard also computes `since` without showing it.
- **PR-028, MINOR, open.** The plan gives the rebase case two answers: case 3 says `since` is the merge base, and the `None` rule and its test say `None`. Stands because case 1 is also false after a clean merge of `main`, where `since` names the merge, and the oldest commit by date can sit on a merged feature branch.

## Review 2026-11-01T15:05Z

- Verdict: satisfied
- Reviewed: plan.md a843ecf24f1f90a3dc68e5facd2a7a76d24bd434, spec.md f361e22239992c19c69256d8650b64f0d83eb0cb, .specify/memory/constitution.md absent, design.md baa914c455c5faea16f4e08d8a7efea379901b26, docs/architecture/design/679-review-is-its-own-step.md 67753ae019ea66ade8dbedb4cc81217f72e9ba51, docs/architecture/design/679-no-spec-skips-spec-rows.md b97f1ba3a4e2abe30373155a8674108d16916787, docs/architecture/review-step-reads-guard-state.md 94ab0f6dbcfea44ae996a29e81922802fa25efec, docs/architecture/every-change-answers-spec-question.md f5c2177ef30ae80b16043c1ecfc733f9102764f9, docs/architecture/design/498-the-fix-line-travels-with-the-reason.md bda01a0bf2a62ded2aa18ba6f33e2c2b0f34320e, research.md e8b57079ccf7965671ed01c808a89e08746d28f9, data-model.md d6ccfe862d2e77d6c45920510f25470b4931cebe, contracts/cli.md ebc4a49b51a1f63c4e42cc6977bedee2384cad3f, quickstart.md 32368240bb1e255abb05557bd2a4f4fea8271ac7, AGENTS.md 5090e1cb455f4d0293a1938504fae5d200f59ae7, plan-review.plan.md 24def0b7e215005de4c46763809a60f63b4280e1 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 0 · Fixed since the earlier review: 2
- Detail: /Users/andremarin/Development/wfctl-specs/679-review-step-after-implement/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Resolved (PR-028 fixed) |
| Architecture and boundaries | Resolved (PR-027 fixed) |
| Adversarial implementation and verification | Resolved (PR-027, PR-028 fixed) |
| Security and reliability | Resolved (PR-027 fixed) |

### Findings

- **PR-027, fixed.** `since` and `capped` are computed only when status passes `for_status=True`, so the guard makes no new git reads and its refusals don't change. Every git read in the `since` calculation is best-effort, and a failure gives `None` instead of an error.
- **PR-028, fixed.** `since` is the newest of the last reviewed commit and the signed-off commit that's still on the branch. It reads the signed-off commit after a later sign-off, stays the last reviewed commit after a merge from the trunk, and is `None` after a rebase that dropped both, which reads `not reviewed yet`.
- No new finding. The reviewer noted that two reviewed commits on different lines of history read `not reviewed yet` with the right count, which the plan chose on purpose.
