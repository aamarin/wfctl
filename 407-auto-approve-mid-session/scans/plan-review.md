# Plan review scan for #407

## Review 2026-11-20T00:15Z

- Verdict: satisfied
- Reviewed: plan.md 806e24d7f8e7bb09ec26a8a95d7ae2aa3a10d1b2, spec.md fa576d22cc066fb0cad6879a22566e6520e829f6, .specify/memory/constitution.md absent, AGENTS.md 9bfca6ea27edb32fa4595b6f1987644c26278702, design.md 92848832a4965464f3e98d67bbd7a823a9bc0275, docs/architecture/approval-mode-is-stored-intent.md ed2f7c38306805b0ac8f61b36353d2627eca466c, research.md 1bf36385b74c4b2989af542a8c5ec9cd9e835146, data-model.md 0abec0e290a1236d5bfaf88767ecc6cb9fafcc23, contracts/cli.md 7f40fa432caacc0de29b0b488e39a6a2eb8b9ba2, quickstart.md f8895b19af541174beff1f26993f16e66da89a90
- Review type: full (no plan copy from an earlier review)
- Open: BLOCKER 0 · MAJOR 3 · MINOR 5 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/407-auto-approve-mid-session/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Outstanding (PR-002, PR-003, PR-006) |
| Architecture and boundaries | Outstanding (PR-001) |
| Adversarial implementation and verification | Outstanding (PR-001, PR-005, PR-007) |
| Security and reliability | Outstanding (PR-002, PR-003, PR-004, PR-008) |

### Findings

- **PR-001, MAJOR, open.** research.md §1 says a session that ran `wfctl end` reads as `none` to the holder check, but `session_open_for` in `wfctl/evidence/_events.py` returns `other` for it. Stands because `auto-approve on` would then refuse that conversation with a false "another session holds this branch", and spec.md US1 scenario 4 covers only a different session.
- **PR-002, MAJOR, open.** The plan doesn't say whether `auto-approve on` while already on resets the review cap. Stands because `review_count` restarts at every `mode` event with `auto_approve` true and contracts/cli.md §on writes one on every `on`, which weakens the cap the record lists as a limit on self-granting; data-model.md calling an `off` event a grant leaves FR-014 ambiguous.
- **PR-003, MAJOR, open.** design.md says the agent runs `on` only when a person asked, and neither spec nor plan names where the agent is told so. Stands because FR-012 is met by a command-table row in `using-wfctl` alone, and that instruction is the only control on the record's accepted case 1.
- **PR-004, MINOR, open.** `grant_auto_approve` writes `mode.json` before appending the event, so a failed append leaves the mode on with no grant event. Stands because the spec's unwritable-state-dir edge case and the error's form are unaddressed.
- **PR-005, MINOR, open.** A hand-written `mode.json` on a branch with an earlier grant makes the bare command print that earlier grant instead of "no grant on record". Stands because data-model.md §Grant and contracts/cli.md §bare don't cover the record's Accepts item 3.
- **PR-006, MINOR, open.** The contract's revoked line doubles "wfctl" and differs from what `status` prints, which research.md §5 says it follows. Stands because `_revocation_line` in `wfctl/cli.py` renders differently.
- **PR-007, MINOR, open.** contracts/cli.md says the bare command never writes, but `_resolve_context` creates the state dir and removes old files; output on a branch with no issue is unstated. Stands because neither the plan nor the contract accounts for it.
- **PR-008, MINOR, open.** A `post_create` grant run from an agent pane inherits the parent conversation's identity, so the new worktree reads it as granted by another session. Stands because `presented_identity` in `wfctl/session/_session.py` takes the inherited `WFCTL_AGENT` session variable, and the spec's edge cases don't name it.

## Review 2026-11-20T01:04Z

- Verdict: satisfied
- Reviewed: plan.md a8ded9a59df0dcc36456e8f6f274fb581b4c47be, spec.md 9a49f194f21f477a11499a90f4daf7a20ca51336, .specify/memory/constitution.md absent, AGENTS.md 9bfca6ea27edb32fa4595b6f1987644c26278702, design.md 42f7cc7b18991dfbe7ee4255197c934411eaae66, docs/architecture/approval-mode-is-stored-intent.md ed2f7c38306805b0ac8f61b36353d2627eca466c, docs/architecture/auto-approve-grant-asks-first.md 506b749183a43635c2f0f738e375962630bd2c53, research.md b5a6ade0fc20c4dfc49816db0ee43a30ae5e4e4e, data-model.md f5c7467da6706485bfb7e866584eb3180fa3eb35, contracts/cli.md 6a1250828df2d500720860db43d7ec31d5726427, quickstart.md f8895b19af541174beff1f26993f16e66da89a90, plan-review.plan.md 806e24d7f8e7bb09ec26a8a95d7ae2aa3a10d1b2 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 9 · Fixed since the earlier review: 3
- Detail: /Users/andremarin/Development/wfctl-specs/407-auto-approve-mid-session/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-013) |
| Requirements and traceability | Outstanding (PR-005, PR-006, PR-011, PR-013; PR-003 fixed) |
| Architecture and boundaries | Resolved (PR-001 fixed) |
| Adversarial implementation and verification | Outstanding (PR-007, PR-009, PR-010; PR-001 fixed) |
| Security and reliability | Outstanding (PR-004, PR-008, PR-009, PR-012; PR-002 fixed) |

### Findings

- **PR-001, MAJOR, fixed.** Fixed by research.md §1 and the contract's refusal, which now reads "No session is open for this conversation on this branch", true both for another session and for this one after `wfctl end`; FR-004 and the edge cases state it.
- **PR-002, MAJOR, fixed.** Fixed by FR-001, research.md §3a, data-model.md's split of grant from mode change, and Review-plan fix 2: a repeated `on` writes nothing, so the review cap doesn't restart.
- **PR-003, MAJOR, fixed.** Fixed by Ownership item 5, which puts the "only when a person asked" rule in `using-wfctl` under `## Commands`, checked by `tests/test_skills_reference_auto_approve.py` and required by FR-012.
- **PR-009, MAJOR, open.** The new record's control depends on Claude Code acting on the two `ask` rules, and the plan verifies only that wfctl writes them. Stands because nothing checks that Claude Code prompts in auto mode or `bypassPermissions`, the modes unattended sessions use, or that the rule strings match what the agent types.
- **PR-004, MINOR, open.** `mode.json` is written before the event is appended, and neither the order on failure nor the error form is stated. Stands because only Walkthrough fix 1's later repair addresses it.
- **PR-005, MINOR, open.** After a hand-written mode file, the bare command prints the earlier mode change instead of "no grant on record". Stands because data-model.md and contracts/cli.md §bare don't cover it.
- **PR-006, MINOR, open.** The contract's revoked line, "turned off by wfctl: wfctl turned it off…", doesn't match `_revocation_line`. Stands because the contract wasn't changed.
- **PR-007, MINOR, open.** The contract says the bare command never writes, but `_resolve_context` creates the state dir, and output on a branch with no issue is unstated. Stands because the contract wasn't changed.
- **PR-008, MINOR, open.** The creation hook inherits `CLAUDE_CODE_SESSION_ID` from the launching pane, so the new worktree reads its grant as by another session. Stands because the plan adds nothing on it.
- **PR-010, MINOR, open.** The plan says install, uninstall and doctor treat an ask rule like the deny rule, but that path's messages are written for `cd`, and the install output would claim "It also now denies `Bash(cd:*)`" on every existing install at upgrade. Stands because the plan names no message changes.
- **PR-011, MINOR, open.** The plan lists no end-to-end tests for the ask rules, and doesn't name `tests/test_install_hook_merge.py`, where the install-refusal, doctor and uninstall tests live. Stands because the record promises a test for its form 3.
- **PR-012, MINOR, open.** The plan and record say the creation hook is one no agent runs, but agents here run `workmux add`, so `WFCTL_AUTO_APPROVE=1 workmux add` grants with no prompt. Stands because the record's Accepts list doesn't name it; the fix belongs in the record.
- **PR-013, MINOR, open.** data-model.md §mode event says a grant is only written when the mode was off, which contradicts Walkthrough fix 1, FR-001 and research.md §3a. Stands because data-model.md wasn't updated with the walkthrough fix.

## Review 2026-11-20T01:22Z

- Verdict: satisfied
- Reviewed: plan.md 3b40ef2fcc98f9e9bf7a226c61141af51b647963, spec.md 6a8d9e6d45789025365fa4df5d68fc954c73b692, .specify/memory/constitution.md absent, AGENTS.md 9bfca6ea27edb32fa4595b6f1987644c26278702, design.md 42f7cc7b18991dfbe7ee4255197c934411eaae66, docs/architecture/approval-mode-is-stored-intent.md ed2f7c38306805b0ac8f61b36353d2627eca466c, docs/architecture/auto-approve-grant-asks-first.md 46a42fe9863332db6274d8a89b388663ec67eb34, research.md c90081c79408c570ec0bb4eb2bf2b3fa7ee43027, data-model.md 4d19aede098fa663856e769b24c591f5801ec4b9, contracts/cli.md f923d6fce6a25b332ae4ab5860ca70f4a572eb1c, quickstart.md f8895b19af541174beff1f26993f16e66da89a90, plan-review.plan.md a8ded9a59df0dcc36456e8f6f274fb581b4c47be (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 2 · Fixed since the earlier review: 10
- Detail: /Users/andremarin/Development/wfctl-specs/407-auto-approve-mid-session/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Outstanding (PR-014, PR-015; PR-006, PR-011, PR-013 fixed) |
| Architecture and boundaries | Resolved (PR-001 fixed) |
| Adversarial implementation and verification | Resolved (PR-005, PR-007, PR-010 fixed) |
| Security and reliability | Resolved (PR-004, PR-008, PR-009, PR-012 fixed) |

### Findings

- **PR-014, MINOR, open.** contracts/cli.md shows the bare command's second line only when the last person's change matches `mode.json`. Stands because after the review cap revokes, that change is the grant while the mode reads off, so no line prints, and research.md §5 says the grant's line should print there.
- **PR-015, MINOR, open.** After a failed file write following `on`, contracts/cli.md prints `turned off outside wfctl`. Stands because spec.md §Edge Cases and data-model.md §mode event say the bare command prints `no grant on record` in that state.
- **PR-009, MAJOR, fixed.** Fixed by the manual prompt check in plan.md §Technical Context and §Constitution Check, and by the record's statement of which permission modes prompt and which deny.
- **PR-004, MINOR, fixed.** Fixed by research.md §3a's write order, event first, and the error line the contract and spec now state.
- **PR-005, MINOR, fixed.** Fixed by `newest_is_grant`, shared by the skip and the bare command, and the contract's `no grant on record` case.
- **PR-006, MINOR, fixed.** Fixed by the contract and research.md §5 using `_revocation_line`'s form.
- **PR-007, MINOR, fixed.** Fixed by the contract's `create=False` lookup and its no-issue case for the bare command and `off`.
- **PR-008, MINOR, fixed.** Fixed by spec.md §Edge Cases, which names the session a creation-hook grant carries, and the record's Accepts item 6.
- **PR-010, MINOR, fixed.** Fixed by each managed rule carrying its own explanation line, and the announcement naming only added rules.
- **PR-011, MINOR, fixed.** Fixed by `tests/test_install_hook_merge.py` in Project Structure.
- **PR-012, MINOR, fixed.** Fixed by the record's Accepts item 6 and the plan sentence that follows it.
- **PR-013, MINOR, fixed.** Fixed by data-model.md §mode event item 1.
