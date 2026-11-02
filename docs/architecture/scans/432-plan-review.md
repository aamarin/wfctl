# Plan review scan for #432

## Review 2026-11-02T14:56Z

- Verdict: unsatisfied
- Reviewed: plan.md 2f770d64a7d40aea12e93b907f01c881f9ea324a, spec.md acb43a376c3b6a531078b27c27d38f420836b9ab, .specify/memory/constitution.md absent, design.md 13585b468c84bc3a582402d1124bc2e129da7117, docs/architecture/session-report-built-in-code.md 5fd57a155d12a7e25b5bf10e2076a1605e8d07ac, docs/architecture/backend-tracker-reads-parent-and-change.md 1690e78d2169d154a56623bf43ad7ffaceb5ae84, docs/architecture/design/432-session-report-is-a-status-flag.md 1827b3ed682cee92720784c21a4cf09677de6553, docs/architecture/design/432-doctor-session-scopes-claim-notices.md 8fd2c2a28d9e4f0644589a813226e882f90e3233, docs/architecture/backend-tracker-maps-issue-state.md 0665c13189597a580a7a5767373d740caf08fc9a, wfctl/agents/skills/architecture-decisions/SKILL.md 756693e68065f92f17f0114a71236e62d7824d5e, research.md 0cb40f194abe00df64089d26cae294fbaba3589c, data-model.md d58b86332776697266e47cee9c2f9b875fb0e462, contracts/cli.md b284fc6cbea5ac98a3f20ac0416bc21afc1799ce, contracts/tracker.md 00e392285e4fcf20865f7c58dad2808ab4f18cce, quickstart.md 681a0fee358a01981566fc5f99f6daa062942b5a, exceptions/agent-host/brainstorm.software-design.md a998dc5aa9f87b23c0ecb6eba0c4578597bd7d79, exceptions/trackers/brainstorm.software-design.md b0356fa11d015809abafac069ab35f882ce045d8, checklists/requirements.md 8b423183151c00ad8350355ee6667f0707d18870
- Review type: full (no earlier review)
- Open: BLOCKER 1 · MAJOR 3 · MINOR 10 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/432-start-session-loads-issue-context/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Outstanding (PR-005, PR-008, PR-009, PR-012) |
| Architecture and boundaries | Outstanding (PR-001, PR-006, PR-007, PR-014) |
| Adversarial implementation and verification | Outstanding (PR-002, PR-004, PR-011, PR-013) |
| Security and reliability | Outstanding (PR-003, PR-010) |

### Findings

- **PR-001, BLOCKER, open.** `spec.md §FR-021` and `plan.md §Project Structure` both edit the Consequences section of `session-report-built-in-code.md`, which is accepted. `architecture-decisions/SKILL.md §An accepted record is immutable` says the body of an accepted record is never edited. The fix belongs in `spec.md`, as an appended Log line or a record that supersedes this one.
- **PR-002, MAJOR, open.** FR-021 also edits the #432 issue body. No `wfctl issue` verb edits an issue body, and the plan names no owner or route for that edit.
- **PR-003, MAJOR, open.** FR-004 promises the handoff word for word, but the plan says nothing about rich markup. `console.print` drops `[x]` and raises `MarkupError` on `[/x]`, and handoffs and issue bodies are text from outside wfctl.
- **PR-004, MAJOR, open.** Three tests in `test_start_session_asks_conditionally.py` pin the skill's `events.jsonl` read, which moves into code. The plan plans no code-level test to replace them, and it doesn't list `test_handoff_records_work_in_flight.py` as affected.
- **PR-005, MINOR, open.** The plan omits `scaffold-tracker/SKILL.md`, which documents the tracker verbs. Its test fails for `parent`, and `branch` would go undocumented.
- **PR-006, MINOR, open.** `research.md §4` adds the `#` prefix for digit-only keys inside wfctl, while FR-019 says the form comes from `key_pattern`.
- **PR-007, MINOR, open.** The Constitution Check treats `backend-tracker-maps-issue-state` as an accepted gate, but it's still proposed.
- **PR-008, MINOR, open.** The skill's "likely done" alignment check is dropped, and neither the spec nor the plan says so.
- **PR-009, MINOR, open.** With no `origin/HEAD`, `research.md §5` marks no commit, which is an exception FR-019 doesn't carry.
- **PR-010, MINOR, open.** Three tracker reads with a 15-second timeout each can hold session start for 45 seconds, and the plan doesn't say whether they run in sequence or together.
- **PR-011, MINOR, open.** The `branch` verb's answer is undefined when two open PRs from different forks share a head branch name.
- **PR-012, MINOR, open.** `design.md §Recommended Direction` still says the report gives the handoff's path, but the spec now prints the whole handoff.
- **PR-013, MINOR, open.** No test checks the skill's four-command list or the absence of `issue list` and `change list` (FR-015, FR-016).
- **PR-014, MINOR, open.** No contract covers the eight extra keys `status --session --json` adds to the payload.
