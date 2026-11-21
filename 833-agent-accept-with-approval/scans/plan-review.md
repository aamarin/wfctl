# Plan review scan for #833

## Review 2026-11-20T20:50Z

- Verdict: unsatisfied
- Reviewed: plan.md a6252c8eacbd486ea8023e1ebe0e14e853e403d4, spec.md 5e5fae30f33b570680fc5130e5326e1019b72fec, .specify/memory/constitution.md absent, design.md c4cd4077024eb83527a869bbe1bce498027d10d7, docs/architecture/design/prompted-spellings-one-table.md 8f127d20432c2cc000ecadb01af5ee245edc5da2, docs/architecture/prompt-approves-person-commands.md 123694382ea580f76b47491c2d96a6ebc3e41577, docs/architecture/accept-check-threat-model.md f2e35654505027d1dda08b36026c994d0ceaeccb, docs/architecture/guard-catches-literal-accept.md 01a32d319ab38e1432fc9514316c21b05e8dd7dc, research.md 98063ba2910224db53987a36adcda3ee2474215d, data-model.md 0e9d9960532f4cf61776fd53a854dcd4f4d7967a, contracts/cli.md b86cc4507d509455abcd90d633da4f367ddb77ad, quickstart.md de422aafc7fc9404b069dc986f34e6a7494b8988
- Review type: full (no plan copy from an earlier review)
- Open: BLOCKER 2 · MAJOR 5 · MINOR 6 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/833-agent-accept-with-approval/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-001, PR-002) |
| Requirements and traceability | Outstanding (PR-002, PR-005) |
| Architecture and boundaries | Outstanding (PR-001, PR-009, PR-012) |
| Adversarial implementation and verification | Outstanding (PR-003, PR-006, PR-007, PR-008, PR-010, PR-011, PR-013) |
| Security and reliability | Outstanding (PR-001, PR-004) |

### Findings

- **PR-001, BLOCKER, open.** `plan.md §The guard` compares words after `shlex` splits them, which strips quotes and backslashes, so `wfctl "arch" accept s` matches a table entry and passes. Stands because the accepted record keeps that form refused (Must keep catching item 11).
- **PR-002, BLOCKER, open.** `plan.md §The guard` keeps `_SIGN_OFF` as the refusal's trigger, so `grep -rn "wfctl review sign-off" wfctl/` stays refused. Stands because that command is Must let through item 8.
- **PR-003, MAJOR, open.** The walk runs the installed wfctl's guard hook, not the branch's, so SC-001 can't be observed without installing the branch first.
- **PR-004, MAJOR, open.** `CLAUDECODE` is inherited by nested agents, such as `codex exec` started from Claude Code, which pass the terminal check with no prompt. The plan neither handles nor accepts it.
- **PR-005, MAJOR, open.** Moving the list test drops tests for the superseded record's items 3 - 20, which the new record keeps refused, and items 16 and 19 conflict with FR-005.
- **PR-006, MAJOR, open.** `tests/conftest.py` doesn't strip `CLAUDECODE`, so terminal-refusal tests change behavior when the suite runs inside Claude Code.
- **PR-007, MAJOR, open.** R-003 accepts a prompt on every dry run without weighing unattended runs, where the dry run is the pipeline's own fix line.
- **PR-008, MINOR, open.** How `read()` gets the payload, and what a malformed settings file or a missing agent dir does, is unstated.
- **PR-009, MINOR, open.** `cli.py` calls a private `_prompted_host()`, which the import check refuses, and the export names disagree.
- **PR-010, MINOR, open.** Refusal wording differs between the plan and the contract, and the precedence of reasons is unstated.
- **PR-011, MINOR, open.** No behavior for a blank `--agreed ""` or a redraw without a terminal.
- **PR-012, MINOR, open.** The successor word in the `superseded` Log line is undefined, and the departure from the record's `supersedes` line has no reviewer-visible home.
- **PR-013, MINOR, open.** No test that `WFCTL_AGENT` alone doesn't loosen the check, and the walk covers neither auto mode nor a declined sign-off.

## Review 2026-11-20T21:01Z

- Verdict: unsatisfied
- Reviewed: plan.md 816fcaf422aaef20c51a08629c55960935a22979, spec.md 5e5fae30f33b570680fc5130e5326e1019b72fec, .specify/memory/constitution.md absent, design.md c4cd4077024eb83527a869bbe1bce498027d10d7, docs/architecture/design/prompted-spellings-one-table.md 8f127d20432c2cc000ecadb01af5ee245edc5da2, docs/architecture/prompt-approves-person-commands.md 123694382ea580f76b47491c2d96a6ebc3e41577, docs/architecture/accept-check-threat-model.md f2e35654505027d1dda08b36026c994d0ceaeccb, docs/architecture/guard-catches-literal-accept.md 01a32d319ab38e1432fc9514316c21b05e8dd7dc, research.md 98063ba2910224db53987a36adcda3ee2474215d, data-model.md 0e9d9960532f4cf61776fd53a854dcd4f4d7967a, contracts/cli.md ba18df52afc42efe7869d5a01a972efec787c668, quickstart.md 41c2e6a42514cb13266e7a82fa92d5007b9b78fe, plan-review.plan.md a6252c8eacbd486ea8023e1ebe0e14e853e403d4 (base)
- Review type: re-review
- Open: BLOCKER 1 · MAJOR 1 · MINOR 8 · Fixed since the earlier review: 10
- Detail: /Users/andremarin/Development/wfctl-specs/833-agent-accept-with-approval/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-014, PR-016) |
| Requirements and traceability | Outstanding (PR-018, PR-019) |
| Architecture and boundaries | Outstanding (PR-009, PR-014) |
| Adversarial implementation and verification | Outstanding (PR-008, PR-013, PR-015, PR-017, PR-020) |
| Security and reliability | Outstanding (PR-014, PR-015, PR-019) |

### Findings

- **PR-014, BLOCKER, open.** `prompted-spellings-one-table.md §Decision` item 2 still matches words split the way the shell splits them, the mechanism PR-001 showed lets a quoted form through. Stands because the plan compares raw text and the proposed record wasn't amended.
- **PR-015, MAJOR, open.** `quickstart.md` step 6 signs off on the feature branch, which would cover the implementation commits with no review panel. Stands because the walk names no throwaway branch.
- **PR-008, MINOR, open.** `read()`'s new signature is unnamed, and Technical Context still says one file read.
- **PR-009, MINOR, open.** The export list omits `prompted_host`, and whether `CLAUDECODE` counts by presence or by `1` is unsettled.
- **PR-013, MINOR, open.** No walk step under Claude Code's auto mode.
- **PR-016, MINOR, open.** `data-model.md` and `research.md` describe the replaced design, and three files naming the dry run are missing from the change list.
- **PR-017, MINOR, open.** The refusal headline says "not an agent" while the reason line asks the agent to rerun, and the reword line needs the citation located.
- **PR-018, MINOR, open.** Refusing the hash character blocks citations that name an issue number.
- **PR-019, MINOR, open.** The reading of old items 16 and 19 is the user's to decide, so it belongs in the PR body.
- **PR-020, MINOR, open.** Only the accept is tested against the old items 3 - 20, and the generalized reader hard-codes the accept's words in several places.
- **PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-010, PR-011, PR-012, fixed.** Fixed by `plan.md §The guard`, `§The commands`, `§Records`, `§Tests`, `§Validation`, and the revised `quickstart.md` and `contracts/cli.md`.

## Review 2026-11-20T21:08Z

- Verdict: satisfied
- Reviewed: plan.md 62de2301c794d75619d74d24d1918fde5fbff75c, spec.md 5e5fae30f33b570680fc5130e5326e1019b72fec, .specify/memory/constitution.md absent, design.md c4cd4077024eb83527a869bbe1bce498027d10d7, docs/architecture/design/prompted-spellings-one-table.md fe7e80871ca3745c1109e62a0b919acf89424264, docs/architecture/prompt-approves-person-commands.md 123694382ea580f76b47491c2d96a6ebc3e41577, docs/architecture/accept-check-threat-model.md f2e35654505027d1dda08b36026c994d0ceaeccb, docs/architecture/guard-catches-literal-accept.md 01a32d319ab38e1432fc9514316c21b05e8dd7dc, research.md a545d35cda60953761971321c8a9116a6a4efbed, data-model.md 838940e2f4920504bb9f9723c44342c98e272062, contracts/cli.md f9373865f7f3c04acc7a6f7fd6f26a9507813441, quickstart.md d0a34220c750e9c3e2679ae8a91ee5c414b3cc73, plan-review.plan.md 816fcaf422aaef20c51a08629c55960935a22979 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 4 · Fixed since the earlier review: 7
- Detail: /Users/andremarin/Development/wfctl-specs/833-agent-accept-with-approval/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-016, PR-017) |
| Requirements and traceability | Resolved (PR-002, PR-005, PR-009, PR-019 fixed) |
| Architecture and boundaries | Resolved (PR-012, PR-014 fixed) |
| Adversarial implementation and verification | Outstanding (PR-008, PR-021) |
| Security and reliability | Outstanding (PR-021) |

### Findings

- **PR-008, MINOR, open.** The agent-dir lookup calls git without the gate's 5 s timeout, and the cost line doesn't count it. Stands because a host timeout lets the command run.
- **PR-016, MINOR, open.** `data-model.md §Accept Log line` has no row for a blank citation or a redraw.
- **PR-017, MINOR, open.** The contract's reason line gives a fixed list of characters that omits the newline and an unquoted comment.
- **PR-021, MINOR, open.** The pass check strips leading whitespace, and nothing shows Claude Code's rule does too. Stands because a leading-space form could pass the guard and match no rule.
- **PR-009, PR-013, PR-014, PR-015, PR-018, PR-019, PR-020, fixed.** Fixed by the amended `prompted-spellings-one-table.md §Decision`, `plan.md §The guard`, `§The commands`, `§Tests`, and `quickstart.md` steps 6, 7, and 7a.

## Review 2026-11-21T07:57Z

- Verdict: unsatisfied
- Reviewed: plan.md 59f75d5ed10a296faa1a22e1ff0e3ed13215e8ad, spec.md 101e6f815869db2178c511fe2f0879f8029eaf70, .specify/memory/constitution.md absent, design.md c4cd4077024eb83527a869bbe1bce498027d10d7, docs/architecture/design/prompted-spellings-one-table.md fe7e80871ca3745c1109e62a0b919acf89424264, docs/architecture/prompt-approves-person-commands.md a9de0f51e2e91f1ac6f5f404171b21dfc3340765, docs/architecture/accept-check-threat-model.md f2e35654505027d1dda08b36026c994d0ceaeccb, docs/architecture/guard-catches-literal-accept.md 01a32d319ab38e1432fc9514316c21b05e8dd7dc, research.md a545d35cda60953761971321c8a9116a6a4efbed, data-model.md 75a508b9d0d5562d0c699da0e064fc66c567d4ec, contracts/cli.md 1886a4314a9a638092d4aa98effc7363d1ec82ae, quickstart.md 27f626f680460b51fb2a0ac4e88ab2b4edcb562e, plan-review.plan.md 62de2301c794d75619d74d24d1918fde5fbff75c (base)
- Review type: re-review
- Open: BLOCKER 1 · MAJOR 1 · MINOR 5 · Fixed since the earlier review: 1
- Detail: /Users/andremarin/Development/wfctl-specs/833-agent-accept-with-approval/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-017, PR-024; PR-016 fixed) |
| Requirements and traceability | Outstanding (PR-022, PR-023, PR-025) |
| Architecture and boundaries | Resolved (PR-012, PR-014 fixed) |
| Adversarial implementation and verification | Outstanding (PR-008, PR-021) |
| Security and reliability | Outstanding (PR-021) |

### Findings

- **PR-022, BLOCKER, open.** `spec.md` FR-004, SC-003, and User Story 5 require `doctor` to exit 1 on a missing rule, while `contracts/cli.md §wfctl doctor` and quickstart step 9 say it prints a `⚠` line and leaves the exit code alone. Stands because the plan reuses #407's path, which never reaches the exit code. The fix belongs in `spec.md`.
- **PR-023, MAJOR, open.** `spec.md` FR-017 (re-accepting an amended record, #838) has a data-model row but no approach, test, or contract output in `plan.md`.
- **PR-024, MINOR, open.** `plan.md §The commands` item 1 and the contract name the redraw Log line `drawing signed off — …`, while `data-model.md` and the code write `redrawn — …`.
- **PR-025, MINOR, open.** `research.md` R-004, `design.md` MVP item 3, and the level-3 record's Consequences still describe the removed auto-approve check.
- **PR-008, MINOR, open, narrowed.** The repository lookup in pass check item 5 has no `TIMEOUT`, and `§Technical Context` still says two file reads where `§The guard` says one.
- **PR-017, MINOR, open.** The contract's reason line gives a fixed list of characters that leaves out the newline and an unquoted `#`.
- **PR-021, MINOR, open.** The pass check strips leading whitespace, and nothing shows Claude Code's rule does too.
- **PR-016, MINOR, fixed.** Fixed by `data-model.md §Accept Log line`, which now has the blank-citation and redraw rows.

## Review 2026-11-21T08:03Z

- Verdict: satisfied
- Reviewed: plan.md 9961891f8d7e35c6eed1f72c732c78d3ef4a28ee, spec.md 6bbaff42a2ec1529a4ea7dde5ee47d51b09c5318, .specify/memory/constitution.md absent, design.md c4cd4077024eb83527a869bbe1bce498027d10d7, docs/architecture/design/prompted-spellings-one-table.md fe7e80871ca3745c1109e62a0b919acf89424264, docs/architecture/prompt-approves-person-commands.md a9de0f51e2e91f1ac6f5f404171b21dfc3340765, docs/architecture/accept-check-threat-model.md f2e35654505027d1dda08b36026c994d0ceaeccb, docs/architecture/guard-catches-literal-accept.md 01a32d319ab38e1432fc9514316c21b05e8dd7dc, research.md a545d35cda60953761971321c8a9116a6a4efbed, data-model.md 75a508b9d0d5562d0c699da0e064fc66c567d4ec, contracts/cli.md 43f18b513386228ce99cd7bd01bbfbc0be2c6e05, quickstart.md 27f626f680460b51fb2a0ac4e88ab2b4edcb562e, plan-review.plan.md 59f75d5ed10a296faa1a22e1ff0e3ed13215e8ad (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 5 · Fixed since the earlier review: 3
- Detail: /Users/andremarin/Development/wfctl-specs/833-agent-accept-with-approval/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-017, PR-026; PR-024 fixed) |
| Requirements and traceability | Outstanding (PR-025; PR-022, PR-023 fixed) |
| Architecture and boundaries | Resolved (PR-012, PR-014 fixed) |
| Adversarial implementation and verification | Outstanding (PR-008, PR-021) |
| Security and reliability | Outstanding (PR-021) |

### Findings

- **PR-008, MINOR, open, narrowed.** Neither cost line counts the git call that finds the repository, and the plan doesn't say it runs under `_review_gate.TIMEOUT`.
- **PR-017, MINOR, open.** Contract reason 4 gives a fixed example list of characters with no newline and no unquoted `#`.
- **PR-021, MINOR, open.** The pass check strips leading whitespace, and nothing shows Claude Code's `ask` rule matches the stripped form.
- **PR-025, MINOR, open.** `research.md §R-004`, `design.md §MVP Scope` item 3, and the level-3 record's Consequences still describe the auto-approve check.
- **PR-026, MINOR, open.** `contracts/cli.md` has no output lines for the FR-017 re-accept or its dry run, and `plan.md §Project Structure` leaves out `tests/test_arch_accept.py`.
- **PR-022, BLOCKER, fixed.** Fixed by `spec.md` FR-004, SC-003, and User Story 5 scenario 1, which now match the contract's `⚠` line.
- **PR-023, MAJOR, fixed.** Fixed by `plan.md §The commands` item 1, which now covers FR-017.
- **PR-024, MINOR, fixed.** Fixed by `plan.md §The commands` item 1 and `contracts/cli.md`, which now name the `redrawn` Log line.

## Sign-off 2026-11-21T18:03Z

- Signed off: plan.md 0e5c55ba5353e4a771f9c97adbf6d38a03a8655c
- Reason: The plan now lists three prompted spellings instead of five, since the accept and the sign-off no longer have a uv run form. The user accepted the same change in the amended prompt-approves-person-commands record.
- Reviewed copy: compared
