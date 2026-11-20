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
