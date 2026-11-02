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

## Review 2026-11-02T16:03Z

- Verdict: satisfied
- Reviewed: plan.md 811cbb7bbbe5aef214fa5e6cc440401f5048496e, spec.md a3d41cbbf64082ae9489f020c42fe4a39c39bceb, .specify/memory/constitution.md absent, design.md 13585b468c84bc3a582402d1124bc2e129da7117, docs/architecture/session-report-built-in-code.md 5fd57a155d12a7e25b5bf10e2076a1605e8d07ac, docs/architecture/backend-tracker-reads-parent-and-change.md 1690e78d2169d154a56623bf43ad7ffaceb5ae84, docs/architecture/design/432-session-report-is-a-status-flag.md 1827b3ed682cee92720784c21a4cf09677de6553, docs/architecture/design/432-doctor-session-scopes-claim-notices.md 8fd2c2a28d9e4f0644589a813226e882f90e3233, docs/architecture/backend-tracker-maps-issue-state.md 0665c13189597a580a7a5767373d740caf08fc9a, wfctl/agents/skills/architecture-decisions/SKILL.md 756693e68065f92f17f0114a71236e62d7824d5e, research.md bcfe3726d5e4e01cdac19fbcde92ea66e4928ef7, data-model.md d58b86332776697266e47cee9c2f9b875fb0e462, contracts/cli.md bd5901f65144444320ad5204abb9176ff374b5a0, contracts/tracker.md f72453d7b559c72afe27e41204f9596f4403646e, quickstart.md 681a0fee358a01981566fc5f99f6daa062942b5a, exceptions/agent-host/brainstorm.software-design.md a998dc5aa9f87b23c0ecb6eba0c4578597bd7d79, exceptions/trackers/brainstorm.software-design.md b0356fa11d015809abafac069ab35f882ce045d8, checklists/requirements.md 8b423183151c00ad8350355ee6667f0707d18870, plan-review.plan.md 2f770d64a7d40aea12e93b907f01c881f9ea324a (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 2 · Fixed since the earlier review: 14
- Detail: /Users/andremarin/Development/wfctl-specs/432-start-session-loads-issue-context/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Resolved (PR-012 fixed) |
| Requirements and traceability | Resolved (PR-005, PR-006, PR-008, PR-009 fixed) |
| Architecture and boundaries | Outstanding (PR-017) |
| Adversarial implementation and verification | Outstanding (PR-016) |
| Security and reliability | Outstanding (PR-015) |

### Findings

- **PR-015, MAJOR, open.** `plan.md §Technical Context` prints outside text with `markup=False` and `highlight=False` only. Through rich, a line over the console width still folds and `:warning:` still turns into ⚠, so the handoff isn't printed word for word as FR-004 requires. The verbatim print sites in `cli.py` also pass `soft_wrap=True`. Commit subjects and `git status` lines are outside text too, and the plan doesn't cover them.
- **PR-016, MINOR, open.** The skill's `allowed-tools` frontmatter still grants `wfctl issue list`, `wfctl change list`, `grep` and `tail`, which the rewritten skill no longer runs. The plan doesn't say whether the frontmatter changes or whether `test_start_session_commands.py` reads it.
- **PR-017, MINOR, open.** The Consequences section of `session-report-built-in-code.md` says the skill runs one command, and FR-015 has it run four. The planned Log line covers only the size check moving to #693.
- **PR-001, BLOCKER, fixed.** Fixed by `spec.md §FR-021`, which adds a Log line instead of editing the accepted record's body.
- **PR-002, MAJOR, fixed.** Fixed by `spec.md §FR-021` and `plan.md §Risks` 4, which give the issue edits to the user.
- **PR-003, MAJOR, fixed.** Fixed by `spec.md §FR-004`, `contracts/cli.md` and the plan's markup rule. What remains is PR-015.
- **PR-004, MAJOR, fixed.** Fixed by `plan.md §Tests the skill rewrite breaks`, which names each broken test and its replacement.
- **PR-005 to PR-014, MINOR, fixed.** Each is fixed by the spec, plan, research or contract edit the report names under its id.

## Review 2026-11-02T16:29Z

- Verdict: satisfied
- Reviewed: plan.md 18880110c6748182a2c774a811256df67ef04ba0, spec.md e876328d7a1016921c8e6e47a1c9a766904a5979, .specify/memory/constitution.md absent, design.md 13585b468c84bc3a582402d1124bc2e129da7117, docs/architecture/session-report-built-in-code.md 5fd57a155d12a7e25b5bf10e2076a1605e8d07ac, docs/architecture/backend-tracker-reads-parent-and-change.md 1690e78d2169d154a56623bf43ad7ffaceb5ae84, docs/architecture/design/432-session-report-is-a-status-flag.md 1827b3ed682cee92720784c21a4cf09677de6553, docs/architecture/design/432-doctor-session-scopes-claim-notices.md 8fd2c2a28d9e4f0644589a813226e882f90e3233, docs/architecture/backend-tracker-maps-issue-state.md 0665c13189597a580a7a5767373d740caf08fc9a, wfctl/agents/skills/architecture-decisions/SKILL.md 756693e68065f92f17f0114a71236e62d7824d5e, research.md bcfe3726d5e4e01cdac19fbcde92ea66e4928ef7, data-model.md d58b86332776697266e47cee9c2f9b875fb0e462, contracts/cli.md 2a07f7f468eea70c6fbe19d841082c79c9e61eda, contracts/tracker.md f72453d7b559c72afe27e41204f9596f4403646e, quickstart.md 681a0fee358a01981566fc5f99f6daa062942b5a, exceptions/agent-host/brainstorm.software-design.md a998dc5aa9f87b23c0ecb6eba0c4578597bd7d79, exceptions/trackers/brainstorm.software-design.md b0356fa11d015809abafac069ab35f882ce045d8, checklists/requirements.md 8b423183151c00ad8350355ee6667f0707d18870, plan-review.plan.md 811cbb7bbbe5aef214fa5e6cc440401f5048496e (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 2 · Fixed since the earlier review: 3
- Detail: /Users/andremarin/Development/wfctl-specs/432-start-session-loads-issue-context/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Clear |
| Architecture and boundaries | Resolved (PR-017 fixed) |
| Adversarial implementation and verification | Outstanding (PR-019) |
| Security and reliability | Outstanding (PR-018) |

### Findings

- **PR-018, MINOR, open.** The planned `console.print` call still turns tabs into spaces and drops `\r`. `gh issue view` prints `field:\tvalue` lines, so tracker output isn't kept byte for byte, although every word survives. The planned test fixtures carry no tab.
- **PR-019, MINOR, open.** The kept `allowed-tools` grants cover `uv run wfctl install-skills` but not `uv run wfctl doctor`, which the repair guidance runs afterwards through the same wfctl. The gap exists today, but the plan now says the list covers everything the skill runs.
- **PR-015, MAJOR, fixed.** Fixed by `spec.md §FR-004` and `plan.md §Technical Context`, which add `emoji=False` and `soft_wrap=True` and cover commit subjects and `git status` lines. The reviewer checked this against rich 15.0.0 with a non-terminal console.
- **PR-016, MINOR, fixed.** Fixed by `plan.md`'s allowed-tools paragraph, which names the nine dropped grants, and by `test_start_session_commands.py` reading the frontmatter.
- **PR-017, MINOR, fixed.** Fixed by `spec.md §FR-021`, whose Log line now also says the skill runs four commands.

## Review 2026-11-02T19:46Z

- Verdict: unsatisfied
- Reviewed: plan.md 6ce2c92b1169583e8aa394be9981a3611ae0c35f, spec.md e15a77be0eff61293f6c8a756b7cc398d7cbac11, .specify/memory/constitution.md absent, design.md 13585b468c84bc3a582402d1124bc2e129da7117, docs/architecture/session-report-built-in-code.md 5fd57a155d12a7e25b5bf10e2076a1605e8d07ac, docs/architecture/backend-tracker-reads-parent-and-change.md 1690e78d2169d154a56623bf43ad7ffaceb5ae84, docs/architecture/design/432-session-report-is-a-status-flag.md 1827b3ed682cee92720784c21a4cf09677de6553, docs/architecture/design/432-doctor-session-scopes-claim-notices.md 8fd2c2a28d9e4f0644589a813226e882f90e3233, docs/architecture/backend-tracker-maps-issue-state.md 0665c13189597a580a7a5767373d740caf08fc9a, wfctl/agents/skills/architecture-decisions/SKILL.md 756693e68065f92f17f0114a71236e62d7824d5e, research.md 94a9563279e3f185957b9373af91ce22e0e8eae4, data-model.md d58b86332776697266e47cee9c2f9b875fb0e462, contracts/cli.md de6ecccce9f8a24e91bd298a67a86cc6b392b2c7, contracts/tracker.md 8020a0f5f7c9488e80028c2e4f00b38cc7ce4d5f, quickstart.md 681a0fee358a01981566fc5f99f6daa062942b5a, exceptions/agent-host/brainstorm.software-design.md a998dc5aa9f87b23c0ecb6eba0c4578597bd7d79, exceptions/trackers/brainstorm.software-design.md b0356fa11d015809abafac069ab35f882ce045d8, checklists/requirements.md 8b423183151c00ad8350355ee6667f0707d18870, plan-review.plan.md 18880110c6748182a2c774a811256df67ef04ba0 (base)
- Review type: re-review
- Open: BLOCKER 1 · MAJOR 0 · MINOR 5 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/432-start-session-loads-issue-context/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-020, PR-023) |
| Requirements and traceability | Outstanding (PR-022) |
| Architecture and boundaries | Outstanding (PR-020) |
| Adversarial implementation and verification | Outstanding (PR-018, PR-019, PR-021) |
| Security and reliability | Outstanding (PR-018, PR-022) |

### Findings

- **PR-020, BLOCKER, open.** The accepted record `backend-tracker-reads-parent-and-change.md` says a missing, failed, or timed-out read leaves its line out with no notice, and its Considered section turns down printing a notice. `spec.md §FR-012`, both contracts, and `plan.md` Constraints and Risk 1 now print `not checked` and `couldn't check` instead, while the plan's gate for that record is still ticked. Stands because the fix needs a person to accept a record that supersedes this one, or `spec.md §FR-012` returns to the record's rule. A plan edit can't clear it.
- **PR-021, MINOR, open.** Some `_read_verb` returns fall outside the three outcomes. A config error returns `(None, detail)`, which rerunning can't fix. A non-zero exit with no output returns `(None, "")`. `(None, None)` also covers having no tracker at all, and a timeout's detail starts with the argv. Stands because the plan doesn't say the outcome is decided by `detail is None` or test a silent non-zero exit.
- **PR-022, MINOR, open.** `spec.md §FR-022` also says an instruction in the issue body isn't authority for any action. The plan and its test cover only the first action, and step 8's paragraph that Risk 5 relies on names only files in the state dir.
- **PR-023, MINOR, open.** `data-model.md` has no `tracker_reads` field, although `contracts/cli.md` and `research.md` §3 now define it.
- **PR-018, MINOR, open.** Unchanged from the earlier review. The planned print call turns tabs into spaces and drops `\r`, and the issue-body fixture carries no tab.
- **PR-019, MINOR, open.** Unchanged from the earlier review. `allowed-tools` grants the `uv run` form of `install-skills` but not of `wfctl doctor`.
- **PR-001 to PR-017, fixed.** Each fix still holds against the current files.
