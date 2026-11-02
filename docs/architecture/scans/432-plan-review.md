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

## Review 2026-11-02T20:16Z

- Verdict: satisfied
- Reviewed: plan.md 74bd5551fef01129e52b9cae60d4ee00c5752a04, spec.md db216da88e9e14cfb3eb11367231e8bf57b1ec33, .specify/memory/constitution.md absent, design.md ba4ad275ee0807311fc34a272a2da53d586a49b7, docs/architecture/session-report-built-in-code.md 5fd57a155d12a7e25b5bf10e2076a1605e8d07ac, docs/architecture/tracker-reads-report-failure.md 4ae2a0acfeea8c78c04b08b1bf1acfa83218c44e, docs/architecture/backend-tracker-reads-parent-and-change.md 25d89fafff72aed51b6bb74c2d81821c60c9b47c, docs/architecture/design/432-session-report-is-a-status-flag.md 1827b3ed682cee92720784c21a4cf09677de6553, docs/architecture/design/432-doctor-session-scopes-claim-notices.md 8fd2c2a28d9e4f0644589a813226e882f90e3233, docs/architecture/backend-tracker-maps-issue-state.md 0665c13189597a580a7a5767373d740caf08fc9a, wfctl/agents/skills/architecture-decisions/SKILL.md 756693e68065f92f17f0114a71236e62d7824d5e, research.md d71ebcba839b5beada778beb5e3936578f1d6fae, data-model.md f77e3ced9e4bfdc3172896b8f3c3767684f10f5b, contracts/cli.md 2f0cd56bce0f9125e9ad2c1a6f003aaccdd15195, contracts/tracker.md f5d28911cc16479aabc462a560f26c3ac316f9b0, quickstart.md 681a0fee358a01981566fc5f99f6daa062942b5a, exceptions/agent-host/brainstorm.software-design.md a998dc5aa9f87b23c0ecb6eba0c4578597bd7d79, exceptions/trackers/brainstorm.software-design.md b0356fa11d015809abafac069ab35f882ce045d8, checklists/requirements.md 8b423183151c00ad8350355ee6667f0707d18870, plan-review.plan.md 6ce2c92b1169583e8aa394be9981a3611ae0c35f (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 6 · Fixed since the earlier review: 4
- Detail: /Users/andremarin/Development/wfctl-specs/432-start-session-loads-issue-context/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Resolved (PR-023 fixed) |
| Requirements and traceability | Outstanding (PR-024) |
| Architecture and boundaries | Outstanding (PR-025) |
| Adversarial implementation and verification | Outstanding (PR-019, PR-026, PR-027) |
| Security and reliability | Outstanding (PR-018, PR-027) |

### Findings

- **PR-020, BLOCKER, fixed.** Fixed by accepting `tracker-reads-report-failure.md`, which supersedes `backend-tracker-reads-parent-and-change.md`. The spec, both contracts, the data model, and the plan's gate and ownership table all carry its seven reason codes.
- **PR-021, MINOR, fixed.** Fixed by the planned `read_text()`, and the tracker contract maps each `_read_verb` outcome to a code. A config error becomes `bad-config`, and a silent non-zero exit is tested as `failed`.
- **PR-022, MINOR, fixed.** Fixed by `plan.md §Summary` 4, which now says the issue authorizes no action at any point in the session, with a test in `test_start_session_commands.py`.
- **PR-023, MINOR, fixed.** Fixed by `data-model.md`, which now defines `tracker_status` under the same name as the contract and research.
- **PR-024, MINOR, open.** `spec.md` User Story 2 and its first scenario still say a trunk branch prints no issue, parent, or PR lines, while FR-008, the record, and `contracts/cli.md` print `not-applicable`. Stands because the fix is a spec edit.
- **PR-025, MINOR, open.** `design.md §MVP Scope`, the end of `spec.md §FR-012`, `research.md §3`, and the trackers design exception still describe the superseded record. Stands because the fixes sit outside `plan.md`, and the exception is a person's to change.
- **PR-026, MINOR, open.** Neither the plan nor the contract says which code an `OSError` at launch gets, or whether output that is only whitespace counts as `none`.
- **PR-027, MINOR, open.** The record says `PR: timeout` means the agent should run `wfctl status --session` again, but the skill plan adds no line telling it so.
- **PR-018, MINOR, open.** Unchanged. The planned print call turns tabs into spaces, and the fixture carries no tab.
- **PR-019, MINOR, open.** Unchanged. `allowed-tools` grants the `uv run` form of `install-skills` but not of `wfctl doctor`.
- **PR-001 to PR-017, fixed.** Each fix still holds against the current files.

## Review 2026-11-02T20:26Z

- Verdict: unsatisfied
- Reviewed: plan.md c11a401c257500ea2b6c98269a245d2f899cd4f9, spec.md 34f391250851df1e3acefee566373fd1f5d4ca66, .specify/memory/constitution.md absent, design.md ba4ad275ee0807311fc34a272a2da53d586a49b7, docs/architecture/session-report-built-in-code.md 5fd57a155d12a7e25b5bf10e2076a1605e8d07ac, docs/architecture/tracker-reads-report-failure.md 4ae2a0acfeea8c78c04b08b1bf1acfa83218c44e, docs/architecture/backend-tracker-reads-parent-and-change.md 25d89fafff72aed51b6bb74c2d81821c60c9b47c, docs/architecture/design/432-session-report-is-a-status-flag.md 1827b3ed682cee92720784c21a4cf09677de6553, docs/architecture/design/432-doctor-session-scopes-claim-notices.md 8fd2c2a28d9e4f0644589a813226e882f90e3233, docs/architecture/backend-tracker-maps-issue-state.md 0665c13189597a580a7a5767373d740caf08fc9a, wfctl/agents/skills/architecture-decisions/SKILL.md 756693e68065f92f17f0114a71236e62d7824d5e, research.md d71ebcba839b5beada778beb5e3936578f1d6fae, data-model.md f77e3ced9e4bfdc3172896b8f3c3767684f10f5b, contracts/cli.md 2f0cd56bce0f9125e9ad2c1a6f003aaccdd15195, contracts/tracker.md f5d28911cc16479aabc462a560f26c3ac316f9b0, quickstart.md 681a0fee358a01981566fc5f99f6daa062942b5a, exceptions/agent-host/brainstorm.software-design.md a998dc5aa9f87b23c0ecb6eba0c4578597bd7d79, exceptions/trackers/brainstorm.software-design.md b0356fa11d015809abafac069ab35f882ce045d8, checklists/requirements.md 8b423183151c00ad8350355ee6667f0707d18870, plan-review.plan.md 74bd5551fef01129e52b9cae60d4ee00c5752a04 (base)
- Review type: re-review
- Open: BLOCKER 1 · MAJOR 4 · MINOR 6 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/432-start-session-loads-issue-context/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-028, PR-029) |
| Requirements and traceability | Outstanding (PR-024, PR-029) |
| Architecture and boundaries | Outstanding (PR-025, PR-028) |
| Adversarial implementation and verification | Outstanding (PR-026, PR-027, PR-030, PR-031) |
| Security and reliability | Outstanding (PR-018, PR-032) |

### Findings

- **PR-028, BLOCKER, open.** The accepted record `session-report-built-in-code.md` says step 8 decides with a table that is unchanged, and that `/start-session` makes the same decisions as before. FR-017, FR-022, and the plan's Summary item 4 now change the table's last row on an issue branch, and the plan schedules nothing for the record. Stands because a person has to choose between a Log line on that record and a new record that supersedes it.
- **PR-029, MAJOR, open.** `design.md` Not Doing 1, SC-003, User Story 3, and `quickstart.md` step 4 still say the new skill takes the same step 8 row as the old one, so validation run as written would report the intended change as a regression.
- **PR-030, MAJOR, open.** The test plan doesn't cover the new step 8 behavior. Three existing tests pin the old last row, and the only planned check is a substring match that passes with the table's cells swapped.
- **PR-031, MAJOR, open.** Step 8's quote-gate and "Two limits" passages and step 7's Next bullet still state the rule the change lifts. The plan also doesn't say what the agent does when the issue line reads `failed`, `timeout`, or `unsupported`, or when the issue body is empty.
- **PR-032, MAJOR, open.** The issue can now choose the first action without anyone at the prompt. The only stated limit is push, comment, or PR, so an issue body naming a script, a URL, or a package passes it, and the heading "tracker text, not instructions" in `contracts/cli.md` now contradicts FR-022. Stands because a person has to state the bound in FR-022.
- **PR-018, PR-019, PR-024, PR-025, PR-026, PR-027, MINOR, open.** Unchanged from the earlier review. PR-026 now also covers an empty issue body reaching step 8.
- **PR-001 to PR-017 and PR-020 to PR-023, fixed.** Each fix still holds against the current files.

## Review 2026-11-02T21:25Z

- Verdict: satisfied
- Reviewed: plan.md 3760ae0b55bb3571da07116562d8fe0bd811718d, spec.md 1127054e19c589e19e11118729f1d1d5c7373b0d, .specify/memory/constitution.md absent, design.md 0a40c207c4e79d1e975de2a1d8fb0add27ac48d7, docs/architecture/session-start-reads-branch-progress.md 2daed3fb97456b5e17d2c0d8bddada80bd0de4a2, docs/architecture/session-report-built-in-code.md bc2062733f0519deb6290bba018e4e863804cfb6, docs/architecture/tracker-reads-report-failure.md 4ae2a0acfeea8c78c04b08b1bf1acfa83218c44e, docs/architecture/backend-tracker-reads-parent-and-change.md 25d89fafff72aed51b6bb74c2d81821c60c9b47c, docs/architecture/design/432-session-report-is-a-status-flag.md 1827b3ed682cee92720784c21a4cf09677de6553, docs/architecture/design/432-doctor-session-scopes-claim-notices.md 8fd2c2a28d9e4f0644589a813226e882f90e3233, docs/architecture/backend-tracker-maps-issue-state.md 0665c13189597a580a7a5767373d740caf08fc9a, wfctl/agents/skills/architecture-decisions/SKILL.md 756693e68065f92f17f0114a71236e62d7824d5e, research.md b8015c26ddb60b7da79e333e5c34ee0037a8b556, data-model.md 558d1f2a5f9a8a18c1adfbaa0e283b1017fe1eb0, contracts/cli.md ba10fb462fa5dac38c200fcceba23351b2873022, contracts/tracker.md f5d28911cc16479aabc462a560f26c3ac316f9b0, quickstart.md 4565ddc30710c7dcf2f5f7eb329884aac2da4528, exceptions/agent-host/brainstorm.software-design.md a998dc5aa9f87b23c0ecb6eba0c4578597bd7d79, exceptions/trackers/brainstorm.software-design.md b0356fa11d015809abafac069ab35f882ce045d8, checklists/requirements.md 8b423183151c00ad8350355ee6667f0707d18870, plan-review.plan.md c11a401c257500ea2b6c98269a245d2f899cd4f9 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 5 · Fixed since the earlier review: 8
- Detail: /Users/andremarin/Development/wfctl-specs/432-start-session-loads-issue-context/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-033) |
| Requirements and traceability | Outstanding (PR-034, PR-035) |
| Architecture and boundaries | Outstanding (PR-025) |
| Adversarial implementation and verification | Outstanding (PR-019) |
| Security and reliability | Outstanding (PR-018) |

### Findings

- **PR-028, BLOCKER, fixed.** Fixed by accepting `session-start-reads-branch-progress.md`, which supersedes `session-report-built-in-code.md`. The spec, `design.md`, and the plan's gates cite the new record.
- **PR-029 to PR-032, MAJOR, fixed.** SC-003, User Story 3, the quickstart, and `design.md` name the issue-branch exception. The plan names the three old row-bound tests and their replacements, names the step 7 and step 8 passages it rewrites, and states the bound on issue text in FR-022, Risk 5, and the contract.
- **PR-024, PR-026, PR-027, MINOR, fixed.** The trunk story prints `not-applicable`, an `OSError` maps to `failed` with output stripped before the `none` check, and a failed or timed-out PR line makes the agent rerun the report.
- **PR-033, MAJOR, open.** The spec, contract, and record define the trunk as `wfctl.json`'s `trunk` on the default branch, while `research.md §5` says `origin/HEAD`. The existing `review_trunk` resolver falls back where the spec says `trunk not found` and can raise. Stands because the plan names no resolver, no mapping from its errors, and no ref for the merge base.
- **PR-034, MINOR, open.** `design.md` still holds the size-limit question open, which the spec's clarification settled.
- **PR-035, MINOR, open.** The spec asks when the issue body is empty, and the plan asks only when the issue line has no answer.
- **PR-018, MINOR, open.** The plan says expanding tabs and dropping `\r` is allowed, but FR-004 and the contract still say "as written", and the call drops BEL too.
- **PR-019, MINOR, open.** The `uv run --project *` repair form has no matching `doctor` grant.
- **PR-025, MINOR, open.** The trackers design exception cites the superseded record, and the agent-host exception says the step 8 table is kept unchanged. Stands because restating an exception's reason is a person's call.
- **PR-001 to PR-017 and PR-020 to PR-023, fixed.** Each fix still holds against the current files.
