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
