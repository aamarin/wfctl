# Plan review scan for #622

## Review 2026-10-23T10:19Z

- Verdict: unsatisfied
- Reviewed: plan.md 96270dd4a271be76eb72d06b2d298484768a6a58, spec.md 1c0295476e1be3e76a9c2aa58e098602d6c41fbd, .specify/memory/constitution.md absent, design.md d40e0b4516c828c4cbe8fd0640829c5222ddebc3, docs/architecture/design/622-review-records-in-state-dir.md 4027336f312d54eaf9b30470a60a701fe87f5e8c, docs/architecture/design/622-review-groups-list.md 0b649f0a435241ffd1007d8b4b7a845cebde164b, docs/architecture/design/622-blocked-reviewer-relays-report.md 29357caf33b2837de6f39a779afa8ec1ff034455, docs/architecture/design/622-review-check-in-worktree-guard.md 34648561c62fc6280d75df7b436cd41d2f296f3a, research.md cb3f2229f4e15641e3c14458cfca915a45c949df, data-model.md c13adbc782701c1527f845dfef6de4c98633970b, contracts/cli.md e32da44ed0a574afb86b4c7c4ecca6d83e775d46, contracts/config.md e36510dafc37222df3080d496bbc0da794cff51e, quickstart.md feb1ec0adbe61a05f4f034dbdd290eccd5a8ba38, docs/architecture/review-covers-unreviewed-commits.md 69bf5f4cdcae15c3495bf402deb23c104fa3bd3c, docs/architecture/vendor-upstream-skills.md 299f4f8cb5e2b2e0d84661741696f97ca6c0b3f0, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/wfctl-records-outward-actions-and-never-gates-them.md 8ff8575e2c4b1e5c7ff342092144866d12c98380, AGENTS.md 4dfb90941c8fb593b64d5bdc5d2ff631a4bcc70a, wfctl/_hook.py 77060f8723515559fe708b0e9f10bff2ee9ae99c, wfctl/_entry.py a26598d8eeb62a3847fff5fb70235410ae4ccde9, wfctl/_io.py 50990ecb0d1bfb76788e4592465c21bffb3306ed, wfctl/_paths.py 73d865219982aa4da4aade36fe472032fe550da7, tests/test_guard_entry.py 04b8a817989f7d5af46815ae6cf36a29b916c5d1, tests/test_skill_attribution.py 6665bbf9db2490b969e0d389d0e45561accadb6a, wfctl/agents/skills/fanning-out-code-review/SKILL.md dcf63a66bd69730ab52866916c0bd83299a395c2, wfctl/agents/skills/code-review/SKILL.md f1b669063ac31d22c94cfaebb32c1131f147e304, wfctl/agents/skills/idea-refine/SKILL.md ca60506bac2baa0dd8bca0e3ef9b42de20a524d4
- Review type: full (no plan copy from the earlier review)
- Open: BLOCKER 1 · MAJOR 5 · MINOR 9 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/622-security-review-panel/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-012) |
| Requirements and traceability | Outstanding (PR-010, PR-013) |
| Architecture and boundaries | Outstanding (PR-001, PR-008, PR-009, PR-011, PR-014) |
| Adversarial implementation and verification | Outstanding (PR-005, PR-007, PR-015) |
| Security and reliability | Outstanding (PR-002, PR-003, PR-004, PR-006) |

### Findings

- **PR-001, BLOCKER, open.** The plan keeps the vendored `/security-review` file byte-identical to upstream, but `vendor-upstream-skills.md` requires an attribution line inside every derived file. The test in `tests/test_skill_attribution.py` reads only `*/SKILL.md` and the specify scripts, so it doesn't check a file at `reviewing-security/references/security-review.md`. The finding stands because the plan has no place for the attribution line. Part of the cause is in `spec.md`, where FR-024 requires the line and FR-025 says the file stays unedited.
- **PR-002, MAJOR, open.** Once a command matches, the review check defines how it fails only for an unreadable record and a failed `gh` lookup, and leaves every other error undefined. The `gh pr view` call has no timeout, so the host can kill the guard on its own hook timeout before the guard exits 2, and the merge goes ahead.
- **PR-003, MAJOR, open.** The sign-off refusal uses the pattern `\breview\s+sign-off\b`. An agent can bypass it with `wfctl review 'sign-off'`, `wfctl review sign\-off`, a shell variable, or by writing `sign-off.json` directly, but FR-013 requires a refusal every time.
- **PR-004, MAJOR, open.** Other `gh` commands open or merge a PR without matching any pattern, so SC-001's "zero exceptions" can't hold. Examples include `gh pr -R o/r merge`, `gh api` calls on the pulls endpoints, the GraphQL mutations, and `gh pr merge` while checks are pending, which turns on auto-merge and merges a later head. Part of the cause is in `spec.md`, since FR-012 lists only three commands.
- **PR-005, MAJOR, open.** R4 doesn't say how the check extracts the PR argument or `--head` from a command it matches only as text. When the extraction misses the argument, the check falls back to the current branch and judges the wrong one. The plan also judges `--head` locally instead of looking it up on GitHub as FR-012a says, and it doesn't handle `-R`.
- **PR-006, MAJOR, open.** A run with zero expected reviewers completes with no review. This happens when a group's `reviewers` list is empty or missing, which `wfctl check config` doesn't catch, or when every listed model is unavailable. That can skip the security group, which FR-001 forbids.
- **PR-007, MINOR, open.** The `shutil.which` lookup runs on the agent's `PATH`, so the plan's claim that the agent can't mark a reviewer unavailable doesn't hold. Conversely, a model that is on `PATH` but fails, such as Codex without a login, blocks every PR. The plan doesn't say it reads FR-023 this narrowly.
- **PR-008, MINOR, open.** The plan marks the `a-rule-is-expressed-as-a-check.md` gate as passed, but its own text says the three-round cap is checkable and ships as prose until #626. That belongs in Complexity Tracking as a deviation.
- **PR-009, MINOR, open.** The Safety section of `AGENTS.md` still says wfctl doesn't gate outward actions, and the plan lists no edit to it.
- **PR-010, MINOR, open.** The trunk refs are underspecified. The `trunk_branch` function usually returns `origin/main`, so the plan's "`origin/` counterpart" adds nothing. The plan also doesn't say what happens when `trunk_branch` returns None, and it discovers the trunk where FR-006 sets the default to `main`.
- **PR-011, MINOR, open.** The config contract doesn't restrict group names. A name such as `../x` writes outside `reviews/`, case isn't normalised (`Security` and `security`), and a name can start with a non-letter.
- **PR-012, MINOR, open.** The spec's Validation Strategy and the design record both name a `wfctl store specs` test for SC-004, but the plan's test list leaves it out. The plan also doesn't say what happens to an old `$FEATURE_DIR/reviews/` folder.
- **PR-013, MINOR, open.** The plan doesn't cover FR-003, where the security group commits its fixes before the code group reviews, or FR-004, which asks for one findings table in chat. It names the skills it rewrites but not what they'll say.
- **PR-014, MINOR, open.** The upstream `security-and-hardening` skill points to `../../references/security-checklist.md`, a path outside its own folder, and R10 doesn't vendor that file.
- **PR-015, MINOR, open.** When reviewed commits aren't pushed yet, the pushed head is behind the last reviewed commit, and R3's ancestor rule then lists every commit on the branch as unreviewed. The check still refuses, which is safe, but the list it prints is wrong.

## Review 2026-10-23T15:26Z

- Verdict: satisfied
- Reviewed: plan.md 6eca84d0a6c550d50d9e9eee89f42dbd0c614f0e, spec.md 131acea9c1e2c1cd8a68809f1f0a52e654e73eca, .specify/memory/constitution.md absent, design.md d4cae71c606e64ecb6216d18d5afdfc85b4641a4, docs/architecture/design/622-review-records-in-state-dir.md 4027336f312d54eaf9b30470a60a701fe87f5e8c, docs/architecture/design/622-review-groups-list.md 0b649f0a435241ffd1007d8b4b7a845cebde164b, docs/architecture/design/622-blocked-reviewer-relays-report.md 29357caf33b2837de6f39a779afa8ec1ff034455, docs/architecture/design/622-review-check-in-worktree-guard.md b927b04c49a1880495b4a1ec8143e403e9811e58, research.md 9bc39239550e7b749950154cd566eeeeea1a07f4, data-model.md d43b098e8ac6ac90a4c2ac7b8368c0be9043627d, contracts/cli.md b83e2952b47a566bf542a8376e108dbaf08cf5ed, contracts/config.md 03415ccdbd139a10d138f1534a024e91030aa80b, quickstart.md 1fd59c8ec9724088dc9b3735bb70d255428f9a4b, docs/architecture/review-covers-unreviewed-commits.md 69bf5f4cdcae15c3495bf402deb23c104fa3bd3c, docs/architecture/vendor-upstream-skills.md 299f4f8cb5e2b2e0d84661741696f97ca6c0b3f0, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/wfctl-records-outward-actions-and-never-gates-them.md 8ff8575e2c4b1e5c7ff342092144866d12c98380, AGENTS.md 4dfb90941c8fb593b64d5bdc5d2ff631a4bcc70a, wfctl/_hook.py 77060f8723515559fe708b0e9f10bff2ee9ae99c, wfctl/_entry.py a26598d8eeb62a3847fff5fb70235410ae4ccde9, wfctl/_io.py 50990ecb0d1bfb76788e4592465c21bffb3306ed, wfctl/_paths.py 73d865219982aa4da4aade36fe472032fe550da7, wfctl/_restart.py 97eface9df371260af973dca55a215a2251304de, tests/test_guard_entry.py 04b8a817989f7d5af46815ae6cf36a29b916c5d1, tests/test_skill_attribution.py 6665bbf9db2490b969e0d389d0e45561accadb6a, wfctl/agents/skills/NOTICES.md 4aeb6145750062f3fbc661974f460a2f885f8ab2, wfctl/agents/skills/fanning-out-code-review/SKILL.md dcf63a66bd69730ab52866916c0bd83299a395c2, wfctl/agents/skills/code-review/SKILL.md f1b669063ac31d22c94cfaebb32c1131f147e304, wfctl/agents/skills/idea-refine/SKILL.md ca60506bac2baa0dd8bca0e3ef9b42de20a524d4, wfctl/agents/skills/opening-a-change/SKILL.md ec2437e0ab6ff1d188cadd9b677db0c715144ee5, wfctl/agents/skills/architecture-decisions/SKILL.md bdcc407f2bbe287b6d31099ab2bcf483129e405f, plan-review.plan.md 96270dd4a271be76eb72d06b2d298484768a6a58 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 4 · MINOR 6 · Fixed since the earlier review: 15
- Detail: /Users/andremarin/Development/wfctl-specs/622-security-review-panel/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Resolved (PR-012 fixed) |
| Requirements and traceability | Outstanding (PR-023; PR-010 and PR-013 fixed) |
| Architecture and boundaries | Outstanding (PR-016, PR-024; PR-001, PR-008, PR-009, PR-011 and PR-014 fixed) |
| Adversarial implementation and verification | Outstanding (PR-018, PR-020, PR-022; PR-005, PR-007 and PR-015 fixed) |
| Security and reliability | Outstanding (PR-017, PR-019, PR-021, PR-025; PR-002, PR-003, PR-004 and PR-006 fixed) |

### Findings

- **PR-001, BLOCKER, fixed.** Fixed by `plan.md`'s Technical Context and Constitution Check, `research.md` R10, and FR-024. The `security-and-hardening` skill ends with the attribution line, and the `/security-review` copy is credited by a new table in the vendor record, a `NOTICES.md` entry, and an extended attribution test.
- **PR-002, MAJOR, fixed.** Fixed by R4 and FR-015. Any error, timeout, or non-zero exit after a match refuses, and every `gh` and `git` call has a 5-second timeout.
- **PR-003, MAJOR, fixed.** Fixed by R6 and R9. The sign-off pattern matches the two words anywhere in the text, the command needs a terminal and a typed sha, and the spec records a direct write of `sign-off.json` as a limit.
- **PR-004, MAJOR, fixed.** Fixed by R6, FR-012, and SC-001. The patterns cover `-R` before the verb, both merge endpoints, a `gh api` create, and the GraphQL mutations. `--auto` refuses, and the spec's Edge Cases record the invocations that remain open.
- **PR-005, MAJOR, fixed.** Fixed by R4. It states the argument rule, looks up `--head` with `git ls-remote`, refuses when `-R` names another repository, and never falls back to the current branch.
- **PR-006, MAJOR, fixed.** Fixed by FR-023, R7, and the data model. A run with no available reviewer stays incomplete, and a custom group with no reviewers is a `check config` finding.
- **PR-007, MINOR, fixed.** Fixed by the plan's ownership point 2 and the spec's Assumptions, which say the `PATH` lookup is visible rather than enforced.
- **PR-008, MINOR, fixed.** Fixed by Complexity Tracking, which records the round cap as a deviation pending #626.
- **PR-009, MINOR, fixed.** Fixed by the plan's Constitution Check and Project Structure, which list the edit to the `AGENTS.md` Safety section.
- **PR-010, MINOR, fixed.** Fixed by R3, which names the trunk refs and the case where no trunk is found, and by FR-006.
- **PR-011, MINOR, fixed.** Fixed by FR-020, the data model, and the config contract, which restrict group names to `^[a-z][a-z0-9-]*$`.
- **PR-012, MINOR, fixed.** Fixed by `test_review_store.py` in the plan's test list and by the data model's note on old `reviews/` folders.
- **PR-013, MINOR, fixed.** Fixed by the plan's new section on what the skill rewrites say.
- **PR-014, MINOR, fixed.** Fixed by R10, which vendors the upstream checklist into the skill's `references/` folder.
- **PR-015, MINOR, fixed.** Fixed by R3 item 3, which treats a head that is the last reviewed commit or one of its ancestors as reviewed.
- **PR-016, MAJOR, open.** The new table in `vendor-upstream-skills.md` changes an accepted record, and the plan doesn't say whether that is an amendment or a new record. The record currently says the templates are the one case where the notice replaces the line. The existing test also treats every non-template row as a file that must carry the line, so the new row fails the test until the test can tell the tables apart.
- **PR-017, MAJOR, open.** The check judges a matched command before any of the text runs. In `git commit -am x && git push && gh pr create`, or `git switch other && gh pr create`, the PR opens on a commit or branch the check never judged. The spec's known limits don't name this case.
- **PR-018, MAJOR, open.** A relayed report travels in the command text, through a heredoc or `echo`, so the guard's text match reads it. The guard refuses a report that quotes `gh pr create` or mentions "review" before "sign-off".
- **PR-019, MAJOR, open.** `gh pr new`, the built-in alias of `gh pr create`, matches no pattern, and neither does the GraphQL `enqueuePullRequest` mutation for the merge queue.
- **PR-020, MINOR, open.** R4's flag lists omit `-s`, `-m`, and `-r` for `merge`, don't say how `--flag=value` is read, and compare `-R HOST/OWNER/REPO` against `nameWithOwner`. Each fails safe as a wrong refusal.
- **PR-021, MINOR, open.** `gh api repos/other/repo/pulls/N/merge` and `GH_REPO=other/repo gh pr merge N` make the check look up PR N in this repository, which is the wrong-repository case the `-R` rule blocks.
- **PR-022, MINOR, open.** Read literally, the rule that a non-zero exit refuses misfires on `git merge-base --is-ancestor` and `git show-ref --verify`, which return exit 1 to mean "no". The `_paths` helpers that R3 and R5 name run `git` with no timeout, and by default `resolve_agent_dir` creates the directory it's asked about.
- **PR-023, MINOR, open.** FR-021 asks for a finding on any group with no reviewers, but the config contract applies it only to custom groups, so a built-in group with an empty list has no defined behavior.
- **PR-024, MINOR, open.** The guard record still lists four commands, the groups record still lists three `check config` problems and says the review continues on a bad config, and `design.md` still gives #626 the question of how the sign-off is recorded, which R9 now decides.
- **PR-025, MINOR, open.** A pseudo-terminal from `script` or `pty.spawn` satisfies `isatty`, so FR-013's claim that a missed invocation still can't sign off overstates the check. The terminal check should read as a second obstacle, recorded beside the direct-write limit.

## Review 2026-10-23T16:18Z

- Verdict: satisfied
- Reviewed: plan.md 3b3fd81b384d660ee538ccece2011bef3e487b29, spec.md c7399ddc8a2ad2c3f8ca21d0fbed3f991a9d336f, .specify/memory/constitution.md absent, design.md 1f0871e7048770d0955d5df9fc3a4880f5db19f8, docs/architecture/design/622-review-records-in-state-dir.md 4027336f312d54eaf9b30470a60a701fe87f5e8c, docs/architecture/design/622-review-groups-list.md 44048f18080066767fa5f064e3b7e75c9738fa91, docs/architecture/design/622-blocked-reviewer-relays-report.md 737f15b5d4a3019e229cdc9bb30a6eb544450116, docs/architecture/design/622-review-check-in-worktree-guard.md a488745e9aa28d9a2da49b44e3983bab45bd82c2, research.md 356cdeadb72df75c24d39faee337531c329516b4, data-model.md 4a2b1597bd61bf6d47295f00336d5a0fb2716f26, contracts/cli.md bf7d7fa91bcab78a40f4d67d04cf2b81487a4650, contracts/config.md a6cb93ef21e11f2778edb6e78b51027b2dbd0576, quickstart.md ff7e876c9ed0bd86381649db4d6a0ffec639348c, docs/architecture/review-covers-unreviewed-commits.md 69bf5f4cdcae15c3495bf402deb23c104fa3bd3c, docs/architecture/vendor-upstream-skills.md 299f4f8cb5e2b2e0d84661741696f97ca6c0b3f0, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/wfctl-records-outward-actions-and-never-gates-them.md 8ff8575e2c4b1e5c7ff342092144866d12c98380, AGENTS.md 4dfb90941c8fb593b64d5bdc5d2ff631a4bcc70a, wfctl/_hook.py 77060f8723515559fe708b0e9f10bff2ee9ae99c, wfctl/_entry.py a26598d8eeb62a3847fff5fb70235410ae4ccde9, wfctl/_io.py 50990ecb0d1bfb76788e4592465c21bffb3306ed, wfctl/_paths.py 73d865219982aa4da4aade36fe472032fe550da7, wfctl/_restart.py 97eface9df371260af973dca55a215a2251304de, tests/test_guard_entry.py 04b8a817989f7d5af46815ae6cf36a29b916c5d1, tests/test_skill_attribution.py 6665bbf9db2490b969e0d389d0e45561accadb6a, wfctl/agents/skills/NOTICES.md 4aeb6145750062f3fbc661974f460a2f885f8ab2, wfctl/agents/skills/fanning-out-code-review/SKILL.md dcf63a66bd69730ab52866916c0bd83299a395c2, wfctl/agents/skills/code-review/SKILL.md f1b669063ac31d22c94cfaebb32c1131f147e304, wfctl/agents/skills/idea-refine/SKILL.md ca60506bac2baa0dd8bca0e3ef9b42de20a524d4, wfctl/agents/skills/opening-a-change/SKILL.md ec2437e0ab6ff1d188cadd9b677db0c715144ee5, wfctl/agents/skills/architecture-decisions/SKILL.md bdcc407f2bbe287b6d31099ab2bcf483129e405f, plan-review.plan.md 6eca84d0a6c550d50d9e9eee89f42dbd0c614f0e (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 5 · Fixed since the earlier review: 9
- Detail: /Users/andremarin/Development/wfctl-specs/622-security-review-panel/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Resolved (PR-016 fixed) |
| Requirements and traceability | Outstanding (PR-030; PR-023 fixed) |
| Architecture and boundaries | Resolved (PR-024 fixed) |
| Adversarial implementation and verification | Outstanding (PR-022, PR-026, PR-027; PR-018 and PR-020 fixed) |
| Security and reliability | Outstanding (PR-028, PR-029; PR-017, PR-019, PR-021 and PR-025 fixed) |

### Findings

- **PR-016, MAJOR, fixed.** Fixed by R10 items 3 to 6 and the plan's Constitution Check. The vendor record is amended in place, its "one case" sentence now names both cases, and the test identifies the new row by its path. The plan counts nine earlier amendments, but the record's Log shows eight.
- **PR-017, MAJOR, fixed.** Fixed by FR-012b, R4, and the guard record. A PR command that follows another command in the same text refuses, and the check judges every match.
- **PR-018, MAJOR, fixed.** Fixed by FR-017, R8, and the relay contract. `wfctl relay` reads the report only from the file `--from` names.
- **PR-019, MAJOR, fixed.** Fixed by R6 patterns 1 and 4, FR-012, and the spec's Edge Cases, which add `gh pr new`, `enqueuePullRequest`, and the `gh alias` limit.
- **PR-020, MINOR, fixed.** Fixed by R4, which adds the short merge flags, `--flag=value`, attached short values, `--help`, and a host prefix on `-R`.
- **PR-021, MINOR, fixed.** Fixed by R4 and FR-012a, which refuse another repository named by `GH_REPO=` or a `repos/<owner>/<repo>/` path.
- **PR-022, MINOR, open.** Narrowed. The "no" exit codes and `create=False` are fixed. But `resolve_agent_dir` reaches `project_name`'s `git` call through `project_state_dir`, which takes no timeout. The plan also doesn't say how the check reads the current branch, and `resolve_branch` has no timeout either.
- **PR-023, MINOR, fixed.** Fixed by FR-019, FR-021, the data model, and the config contract. An empty `reviewers` list is a finding on any group, and only a missing key gives a built-in group its default.
- **PR-024, MINOR, fixed.** Fixed by the guard, relay, and groups records and by `design.md`'s Open Questions.
- **PR-025, MINOR, fixed.** Fixed by FR-013, R9, and the spec's Edge Cases, which call the terminal check a second obstacle and record the pseudo-terminal limit.
- **PR-026, MAJOR, open.** The vendored `/security-review` file ends with "Your final reply must contain the markdown report and nothing else", so a reviewer following it writes no `Reviewed:` line and no verdict, and wfctl won't count the report. Its false-positive section also says not to write files. The `reviewing-security` note overrides only the git section, the checklist path, and the commit range.
- **PR-027, MINOR, open.** `_listed_templates()` also filters on `_TEMPLATE_ROW`, so turning it into a tuple adds the new row to the template set, where the Spec Kit notice test fails on it. The new `NOTICES.md` reader is also missing from `_declaration_sources`.
- **PR-028, MINOR, open.** A command substitution inside an argument, such as `gh pr create --title "$(git push)"`, and GNU `env -C dir gh pr create` change the branch or head with no separator before the match. Neither is a recorded limit.
- **PR-029, MINOR, open.** R4 strips an `owner:` prefix from `--head`, so the check judges a fork's head against `origin`'s branch of the same name, which fails open. Grouped short flags such as `-sd` have no defined reading, which fails safe.
- **PR-030, MINOR, open.** The `opening-a-change` skill's existing step 5 block runs `gh pr create` after two other commands, which FR-012b refuses, and the plan doesn't list that block as one to change.

## Review 2026-10-23T18:33Z

- Verdict: satisfied
- Reviewed: plan.md ca6d84060873482a49de5254152d548c0cc1fb7b, spec.md f5315879639f558a409f67856d2cf95d54f2a935, .specify/memory/constitution.md absent, design.md e82e45ce32266ada7c33003be09900fdbd625387, docs/architecture/design/622-review-records-in-state-dir.md 4027336f312d54eaf9b30470a60a701fe87f5e8c, docs/architecture/design/622-review-groups-list.md 44048f18080066767fa5f064e3b7e75c9738fa91, docs/architecture/design/622-blocked-reviewer-relays-report.md 737f15b5d4a3019e229cdc9bb30a6eb544450116, docs/architecture/design/622-review-check-in-worktree-guard.md 01b7e7cfed9b1b0c28d0a853435b0f4bfefec308, research.md fe60e1b99475be30815fdb1911b2a11aa554ac92, data-model.md 4a2b1597bd61bf6d47295f00336d5a0fb2716f26, contracts/cli.md d28aefd9fd8d8180ad1829e84e64c795083d395d, contracts/config.md a6cb93ef21e11f2778edb6e78b51027b2dbd0576, quickstart.md ff7e876c9ed0bd86381649db4d6a0ffec639348c, docs/architecture/review-covers-unreviewed-commits.md 69bf5f4cdcae15c3495bf402deb23c104fa3bd3c, docs/architecture/vendor-upstream-skills.md 299f4f8cb5e2b2e0d84661741696f97ca6c0b3f0, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/wfctl-records-outward-actions-and-never-gates-them.md 8ff8575e2c4b1e5c7ff342092144866d12c98380, AGENTS.md 4dfb90941c8fb593b64d5bdc5d2ff631a4bcc70a, wfctl/_hook.py 77060f8723515559fe708b0e9f10bff2ee9ae99c, wfctl/_entry.py a26598d8eeb62a3847fff5fb70235410ae4ccde9, wfctl/_io.py 50990ecb0d1bfb76788e4592465c21bffb3306ed, wfctl/_paths.py 73d865219982aa4da4aade36fe472032fe550da7, wfctl/_restart.py 97eface9df371260af973dca55a215a2251304de, tests/test_guard_entry.py 04b8a817989f7d5af46815ae6cf36a29b916c5d1, tests/test_skill_attribution.py 6665bbf9db2490b969e0d389d0e45561accadb6a, wfctl/agents/skills/NOTICES.md 4aeb6145750062f3fbc661974f460a2f885f8ab2, wfctl/agents/skills/fanning-out-code-review/SKILL.md dcf63a66bd69730ab52866916c0bd83299a395c2, wfctl/agents/skills/code-review/SKILL.md f1b669063ac31d22c94cfaebb32c1131f147e304, wfctl/agents/skills/idea-refine/SKILL.md ca60506bac2baa0dd8bca0e3ef9b42de20a524d4, wfctl/agents/skills/opening-a-change/SKILL.md ec2437e0ab6ff1d188cadd9b677db0c715144ee5, wfctl/agents/skills/architecture-decisions/SKILL.md bdcc407f2bbe287b6d31099ab2bcf483129e405f, plan-review.plan.md 3b3fd81b384d660ee538ccece2011bef3e487b29 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 2 · Fixed since the earlier review: 5
- Detail: /Users/andremarin/Development/wfctl-specs/622-security-review-panel/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Resolved (PR-026 and PR-030 fixed) |
| Architecture and boundaries | Clear |
| Adversarial implementation and verification | Outstanding (PR-022; PR-026 and PR-027 fixed) |
| Security and reliability | Outstanding (PR-031; PR-028 and PR-029 fixed) |

### Findings

- **PR-022, MINOR, open.** Narrowed again. `resolve_branch` and `resolve_agent_dir` now take the timeout. The plan counts five helpers, but `trunk_branch` also passes the timeout to `_resolve_declared` and `_bare_head`. `_bare_head` calls `is_bare_layout`, which runs `git config --bool core.bare` with no timeout, and no artifact names it. The check reaches that call only when `origin/HEAD` isn't set and no trunk is declared.
- **PR-026, MAJOR, fixed.** Fixed by FR-025, R10 item 7, the plan's `reviewing-security` item 3, and `design.md`'s Key Assumptions. The note now tells the reviewer to write one report with a `Reviewed:` line and a verdict to the path wfctl printed, and says this overrides the vendored file's last line, its "don't write files" line, and its sub-task steps.
- **PR-027, MINOR, fixed.** Fixed by R10 item 6. `_TEMPLATE_ROW` stays a string, `_listed()` drops the rows in a new `_NOTICED_ROWS` tuple, and the new notice reader joins `_declaration_sources`.
- **PR-028, MINOR, fixed.** Fixed by FR-012b, R4, the guard record, and the guard contract. A command or process substitution in the matched command refuses. A substitution between `gh` and the verb, and `env -C`, are recorded limits.
- **PR-029, MINOR, fixed.** Fixed by FR-012a, R4, and the guard contract. The check refuses a `--head` owner other than this checkout's, and reads grouped short flags letter by letter.
- **PR-030, MINOR, fixed.** Fixed by the plan's `opening-a-change` item 1.5, which rewrites Step 5 so `wfctl check-body` and `gh pr create` run as separate commands with the body path written out.
- **PR-031, MINOR, open.** New. A `GIT_DIR=` or `GIT_WORK_TREE=` prefix sends `gh pr create` or a bare `gh pr merge` to another checkout's branch, with no separator or substitution for the check to see. It has the same shape as the recorded `env -C` limit, but it is neither refused nor recorded, so SC-001's count doesn't exclude it.

## Review 2026-10-23T20:54Z

- Verdict: satisfied
- Reviewed: plan.md 0a23bdd355a41a8056ec6be0233202a4ca6842fd, spec.md 43f16ed10283b97444b8ef0b6d3ecc73403a3bdf, .specify/memory/constitution.md absent, design.md e82e45ce32266ada7c33003be09900fdbd625387, docs/architecture/design/622-review-records-in-state-dir.md 4027336f312d54eaf9b30470a60a701fe87f5e8c, docs/architecture/design/622-review-groups-list.md 44048f18080066767fa5f064e3b7e75c9738fa91, docs/architecture/design/622-blocked-reviewer-relays-report.md 737f15b5d4a3019e229cdc9bb30a6eb544450116, docs/architecture/design/622-review-check-in-worktree-guard.md 6548fd74c0c016edbe86b140349a170627777424, research.md 9fc3d1ec5e0c86a4ef978de51c71382975114974, data-model.md 4a2b1597bd61bf6d47295f00336d5a0fb2716f26, contracts/cli.md 790544cf51f7df64af04ab00790e4d1f9f96d86d, contracts/config.md a6cb93ef21e11f2778edb6e78b51027b2dbd0576, quickstart.md ff7e876c9ed0bd86381649db4d6a0ffec639348c, docs/architecture/review-covers-unreviewed-commits.md 69bf5f4cdcae15c3495bf402deb23c104fa3bd3c, docs/architecture/vendor-upstream-skills.md 299f4f8cb5e2b2e0d84661741696f97ca6c0b3f0, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/wfctl-records-outward-actions-and-never-gates-them.md 8ff8575e2c4b1e5c7ff342092144866d12c98380, AGENTS.md 4dfb90941c8fb593b64d5bdc5d2ff631a4bcc70a, wfctl/_hook.py 77060f8723515559fe708b0e9f10bff2ee9ae99c, wfctl/_entry.py a26598d8eeb62a3847fff5fb70235410ae4ccde9, wfctl/_io.py 50990ecb0d1bfb76788e4592465c21bffb3306ed, wfctl/_paths.py 73d865219982aa4da4aade36fe472032fe550da7, wfctl/_restart.py 97eface9df371260af973dca55a215a2251304de, wfctl/_guard.py 2b6f0d39f1c0af749d32b0fbd409448fdf5e06f3, tests/test_guard_entry.py 04b8a817989f7d5af46815ae6cf36a29b916c5d1, tests/test_skill_attribution.py 6665bbf9db2490b969e0d389d0e45561accadb6a, wfctl/agents/skills/NOTICES.md 4aeb6145750062f3fbc661974f460a2f885f8ab2, wfctl/agents/skills/fanning-out-code-review/SKILL.md dcf63a66bd69730ab52866916c0bd83299a395c2, wfctl/agents/skills/code-review/SKILL.md f1b669063ac31d22c94cfaebb32c1131f147e304, wfctl/agents/skills/idea-refine/SKILL.md ca60506bac2baa0dd8bca0e3ef9b42de20a524d4, wfctl/agents/skills/opening-a-change/SKILL.md ec2437e0ab6ff1d188cadd9b677db0c715144ee5, wfctl/agents/skills/receiving-code-review/SKILL.md d9dc70c6c98e60b96b9fb591e2079920bd2eec99, wfctl/agents/skills/architecture-decisions/SKILL.md bdcc407f2bbe287b6d31099ab2bcf483129e405f, plan-review.plan.md ca6d84060873482a49de5254152d548c0cc1fb7b (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 2 · MINOR 7 · Fixed since the earlier review: 2
- Detail: /Users/andremarin/Development/wfctl-specs/622-security-review-panel/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-034, PR-039, PR-040) |
| Requirements and traceability | Outstanding (PR-033, PR-040) |
| Architecture and boundaries | Outstanding (PR-032, PR-038) |
| Adversarial implementation and verification | Outstanding (PR-032, PR-033, PR-036; PR-022 fixed) |
| Security and reliability | Outstanding (PR-034, PR-035, PR-037, PR-038; PR-031 fixed) |

### Findings

- **PR-022, MINOR, fixed.** Fixed by R4 item 1, Scale/Scope, and Project Structure. The plan now names all eight `_paths` helpers that take the timeout, `is_bare_layout` included.
- **PR-031, MINOR, fixed.** Fixed by FR-012b, R4, the guard contract, and guard record item 6. Any `NAME=value` word or `env` before a matched command now refuses, whatever the variable.
- **PR-032, MAJOR, open.** No artifact says whether the review check reads the branch from the payload's `cwd` or from its own process directory. `_hook.py` deliberately reads the payload's `cwd` because the two can differ. If the check reads its own directory, a session in the `main` checkout can `cd` into another worktree by a relative path and run `gh pr create --fill` unjudged. Quickstart sets `cwd` to `$PWD`, so no planned test would catch this.
- **PR-033, MAJOR, open.** No R6 pattern triggers FR-012b's rule on `gh` command words, so the contract's own examples, such as `gh "$X" merge 630`, match nothing and pass. Running the rule on every `gh` in the text would instead refuse ordinary commands like `rg 'gh (pr|api)'`, which FR-016 argues against.
- **PR-034, MINOR, open.** R4 applies the letters, digits, and hyphens rule to the `-R` value, but every `-R` value contains a `/`, and repository names can contain `.` and `_`. Under the likely intended reading, the verb after `-R` is never checked, so `gh pr -R <this repo> 'merge' 630` merges unjudged.
- **PR-035, MINOR, open.** A GraphQL mutation read through a substitution, such as `gh api graphql -f query="$(cat m.graphql)"`, matches no pattern. Pattern 7 covers only `query=@file` and `--input`, and this case is neither refused nor recorded as a limit.
- **PR-036, MINOR, open.** The new rules refuse legitimate `gh api` calls. A `-f merge_method=merge` before the path is read as an environment prefix, `gh`'s `:owner/:repo` placeholder is treated as another repository, and pattern 6 refuses every variable-path write, including review-comment replies.
- **PR-037, MINOR, open.** Wrappers such as `uv run --directory ../630-x gh pr create --fill` and `direnv exec ../630-x gh …` change the directory `gh` runs in without a separator, prefix, or `env`. This is the same shape the walkthrough changed from a limit into a refusal.
- **PR-038, MINOR, open.** The trunk-checkout rule depends on the branch name, and a worktree can switch to the trunk branch, so Ownership item 6 reads as enforced when it's a convention. Separately, R4 doesn't strip `origin/` as R3 does, so a plain comparison against `trunk_branch` never matches.
- **PR-039, MINOR, open.** The artifacts don't say which refusals carry FR-015's "person's own terminal" sentence. Contract row 150's timeout message lacks it while the error-refusal block's timeout example includes it, and `opening-a-change` item 1.6 uses this text to identify an error refusal.
- **PR-040, MINOR, open.** Two spec passages still describe the earlier behavior. User Story 3 says the agent can't loop forever on fixes, but nothing enforces that until #626. A Validation Strategy line judges another branch's PR from anywhere, but FR-012a allows that only from the trunk checkout.

## Review 2026-10-23T22:17Z

- Verdict: satisfied
- Reviewed: plan.md 6e775fb68e10014feeff35942930d4040217aadc, spec.md 3cfff7e768c02fe1b9d36b1f6e34feec9566b2f2, .specify/memory/constitution.md absent, design.md e82e45ce32266ada7c33003be09900fdbd625387, docs/architecture/design/622-review-records-in-state-dir.md 4027336f312d54eaf9b30470a60a701fe87f5e8c, docs/architecture/design/622-review-groups-list.md 44048f18080066767fa5f064e3b7e75c9738fa91, docs/architecture/design/622-blocked-reviewer-relays-report.md 737f15b5d4a3019e229cdc9bb30a6eb544450116, docs/architecture/design/622-review-check-in-worktree-guard.md f6d03db7433c10ee6d1f9674f1d3dee9efbff3d3, research.md 45ded1ddc1a4a06b653ca8df10f269e250af8809, data-model.md 4a2b1597bd61bf6d47295f00336d5a0fb2716f26, contracts/cli.md 4228c65782d6ebe69d7d383ee8c5ea6568e90321, contracts/config.md a6cb93ef21e11f2778edb6e78b51027b2dbd0576, quickstart.md ff7e876c9ed0bd86381649db4d6a0ffec639348c, docs/architecture/review-covers-unreviewed-commits.md 69bf5f4cdcae15c3495bf402deb23c104fa3bd3c, docs/architecture/vendor-upstream-skills.md 299f4f8cb5e2b2e0d84661741696f97ca6c0b3f0, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/wfctl-records-outward-actions-and-never-gates-them.md 8ff8575e2c4b1e5c7ff342092144866d12c98380, AGENTS.md 4dfb90941c8fb593b64d5bdc5d2ff631a4bcc70a, wfctl/_hook.py 77060f8723515559fe708b0e9f10bff2ee9ae99c, wfctl/_entry.py a26598d8eeb62a3847fff5fb70235410ae4ccde9, wfctl/_io.py 50990ecb0d1bfb76788e4592465c21bffb3306ed, wfctl/_paths.py 73d865219982aa4da4aade36fe472032fe550da7, wfctl/_restart.py 97eface9df371260af973dca55a215a2251304de, wfctl/_guard.py 2b6f0d39f1c0af749d32b0fbd409448fdf5e06f3, tests/test_guard_entry.py 04b8a817989f7d5af46815ae6cf36a29b916c5d1, tests/test_skill_attribution.py 6665bbf9db2490b969e0d389d0e45561accadb6a, wfctl/agents/skills/NOTICES.md 4aeb6145750062f3fbc661974f460a2f885f8ab2, wfctl/agents/skills/fanning-out-code-review/SKILL.md dcf63a66bd69730ab52866916c0bd83299a395c2, wfctl/agents/skills/code-review/SKILL.md f1b669063ac31d22c94cfaebb32c1131f147e304, wfctl/agents/skills/idea-refine/SKILL.md ca60506bac2baa0dd8bca0e3ef9b42de20a524d4, wfctl/agents/skills/opening-a-change/SKILL.md ec2437e0ab6ff1d188cadd9b677db0c715144ee5, wfctl/agents/skills/receiving-code-review/SKILL.md d9dc70c6c98e60b96b9fb591e2079920bd2eec99, wfctl/agents/skills/architecture-decisions/SKILL.md bdcc407f2bbe287b6d31099ab2bcf483129e405f, .github/scripts/release.py 5573934e6746db3dd261a7c143d91730b22decf1, plan-review.plan.md 0a23bdd355a41a8056ec6be0233202a4ca6842fd (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 10 · Fixed since the earlier review: 3
- Detail: /Users/andremarin/Development/wfctl-specs/622-security-review-panel/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-039, PR-040, PR-045; PR-034 fixed) |
| Requirements and traceability | Outstanding (PR-040, PR-044; PR-033 fixed) |
| Architecture and boundaries | Outstanding (PR-038, PR-045; PR-032 fixed) |
| Adversarial implementation and verification | Outstanding (PR-036, PR-041, PR-043; PR-032 and PR-033 fixed) |
| Security and reliability | Outstanding (PR-035, PR-037, PR-038, PR-041, PR-042, PR-044; PR-034 fixed) |

### Findings

- **PR-032, MAJOR, fixed.** Fixed by `research.md` R4 (Where the check reads from), FR-012c, plan Ownership item 8, two contract rows, and the guard record. The check reads the payload's `cwd`, finds the root with `git -C <cwd> rev-parse --show-toplevel`, and refuses a matched command when `cwd` is missing or outside a repository.
- **PR-033, MAJOR, fixed.** Fixed by R6 pattern 8, FR-012b, and FR-016. The command-word rule now has its own trigger and refuses every time, and every refused and passing example in the contract behaves as its row says.
- **PR-034, MINOR, fixed.** Fixed by R4, which says the `-R` value isn't a command word. Pattern 8 now checks the verb after it, so `gh pr -R <repo> 'merge' 630` refuses.
- **PR-041, MAJOR, open.** New. `gh -R <repo> pr merge 630` and `gh pr -R<repo> merge 630` merge a PR without matching any pattern, since pattern 1 requires `gh\s+pr` and a space or `=` after `-R`. `gh -R cli/cli pr merge --help` prints the `gh pr merge` help, which confirms `gh` parses `-R` before `pr`.
- **PR-035, MINOR, open.** A GraphQL mutation read through a substitution, such as `gh api graphql -f query="$(cat m.graphql)"`, still matches no pattern.
- **PR-036, MINOR, open.** Three legitimate calls still refuse: a `-f merge_method=merge` before the path, the `:owner/:repo` placeholder, and pattern 6 over unrelated writes such as review-comment replies.
- **PR-037, MINOR, open.** `uv run --directory ../630-x gh pr create` and `direnv exec ../630-x gh …` are neither refused nor recorded. The `cwd` rule doesn't catch them, since the session's directory doesn't change.
- **PR-038, MINOR, open.** The trunk-checkout rule depends on a branch name, so Ownership item 6 reads as enforced when it's a convention. R4 still doesn't say it compares against `main` rather than `origin/main`.
- **PR-039, MINOR, open.** A timed-out lookup still has two different messages in the contract, and the unreadable-record and no-trunk rows don't point to the error refusal block.
- **PR-040, MINOR, open.** User Story 3 still says the agent can't loop forever on fixes, and the Validation Strategy line on another branch's PR doesn't name the trunk checkout.
- **PR-042, MINOR, open.** New. A quoted or variable `gh`, such as `"gh" pr merge 630` or `$GH pr merge 630`, matches no pattern, since patterns 1 and 8 both start at `\bgh\s+`.
- **PR-043, MINOR, open.** New. Pattern 8 refuses more ordinary commands than R6 says, such as `grep "gh pr create\|gh pr merge"`, `rg 'gh pr.*merge'`, and a commit message that quotes `gh "$X" merge 630`. R6 names only the glob cost and no workaround.
- **PR-044, MINOR, open.** New. A `gh` call made inside a script, such as `.github/scripts/release.py`'s `gh pr create`, is neither refused nor recorded in the spec's Edge Cases, and the artifacts don't say whether the release PR skips the review groups.
- **PR-045, MINOR, open.** New. R4 keeps `resolve_branch` honoring `WFCTL_BRANCH`, which sets the branch without reading `cwd`, but FR-012c says the branch comes from `cwd`.

## Review 2026-10-23T22:59Z

- Verdict: satisfied
- Reviewed: plan.md f7ee6cd95c7e21eeeb8c8d33d730fa3e768a0224, spec.md 260a5e975e8faffd5af78ac22294da7186a0f925, .specify/memory/constitution.md absent, design.md e82e45ce32266ada7c33003be09900fdbd625387, docs/architecture/design/622-review-records-in-state-dir.md 4027336f312d54eaf9b30470a60a701fe87f5e8c, docs/architecture/design/622-review-groups-list.md 44048f18080066767fa5f064e3b7e75c9738fa91, docs/architecture/design/622-blocked-reviewer-relays-report.md 737f15b5d4a3019e229cdc9bb30a6eb544450116, docs/architecture/design/622-review-check-in-worktree-guard.md f6d03db7433c10ee6d1f9674f1d3dee9efbff3d3, research.md d976bfdaeb49bcdd5ca3c2fba1e51e0f1e119c72, data-model.md 4a2b1597bd61bf6d47295f00336d5a0fb2716f26, contracts/cli.md b84161d3a8350869809fb79b6ca5e92967d8ff09, contracts/config.md a6cb93ef21e11f2778edb6e78b51027b2dbd0576, quickstart.md ff7e876c9ed0bd86381649db4d6a0ffec639348c, docs/architecture/review-covers-unreviewed-commits.md 69bf5f4cdcae15c3495bf402deb23c104fa3bd3c, docs/architecture/vendor-upstream-skills.md 299f4f8cb5e2b2e0d84661741696f97ca6c0b3f0, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/wfctl-records-outward-actions-and-never-gates-them.md 8ff8575e2c4b1e5c7ff342092144866d12c98380, AGENTS.md 4dfb90941c8fb593b64d5bdc5d2ff631a4bcc70a, wfctl/_hook.py 77060f8723515559fe708b0e9f10bff2ee9ae99c, wfctl/_entry.py a26598d8eeb62a3847fff5fb70235410ae4ccde9, wfctl/_io.py 50990ecb0d1bfb76788e4592465c21bffb3306ed, wfctl/_paths.py 73d865219982aa4da4aade36fe472032fe550da7, wfctl/_restart.py 97eface9df371260af973dca55a215a2251304de, wfctl/_guard.py 2b6f0d39f1c0af749d32b0fbd409448fdf5e06f3, tests/test_guard_entry.py 04b8a817989f7d5af46815ae6cf36a29b916c5d1, tests/test_skill_attribution.py 6665bbf9db2490b969e0d389d0e45561accadb6a, wfctl/agents/skills/NOTICES.md 4aeb6145750062f3fbc661974f460a2f885f8ab2, wfctl/agents/skills/fanning-out-code-review/SKILL.md dcf63a66bd69730ab52866916c0bd83299a395c2, wfctl/agents/skills/code-review/SKILL.md f1b669063ac31d22c94cfaebb32c1131f147e304, wfctl/agents/skills/idea-refine/SKILL.md ca60506bac2baa0dd8bca0e3ef9b42de20a524d4, wfctl/agents/skills/opening-a-change/SKILL.md ec2437e0ab6ff1d188cadd9b677db0c715144ee5, wfctl/agents/skills/receiving-code-review/SKILL.md d9dc70c6c98e60b96b9fb591e2079920bd2eec99, wfctl/agents/skills/architecture-decisions/SKILL.md bdcc407f2bbe287b6d31099ab2bcf483129e405f, .github/scripts/release.py 5573934e6746db3dd261a7c143d91730b22decf1, plan-review.plan.md 6e775fb68e10014feeff35942930d4040217aadc (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 12 · Fixed since the earlier review: 1
- Detail: /Users/andremarin/Development/wfctl-specs/622-security-review-panel/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-039, PR-040, PR-045; PR-041 fixed) |
| Requirements and traceability | Outstanding (PR-040, PR-044) |
| Architecture and boundaries | Outstanding (PR-038, PR-045) |
| Adversarial implementation and verification | Outstanding (PR-036, PR-043, PR-046, PR-048; PR-041 fixed) |
| Security and reliability | Outstanding (PR-035, PR-037, PR-038, PR-042, PR-044, PR-046, PR-047; PR-041 fixed) |

### Findings

- **PR-041, MAJOR, fixed.** Fixed by R6 pattern 1's `REPO` group before `pr` and before the verb, R4 reading `-R` wherever it sits and refusing two, pattern 8 skipping `-R`, FR-012, three contract rows, and the planned tests. All three commands the finding named now match.
- **PR-046, MAJOR, open.** New. Pattern 1 allows only one `-R` before `pr` and one before the verb, but `gh` accepts more there. `gh pr --squash=true merge 630` and `gh -R <this repo> -R owner/other pr merge 630` reach no check. `gh pr --squash=true merge --help` prints the merge help, which confirms that `gh` parses a verb's flag placed before the verb.
- **PR-047, MINOR, open.** New. In `gh -R $(git push -q; echo a/b) pr merge 630`, pattern 1 fails at `push`, and pattern 8 reads `push` as the command word and passes it.
- **PR-048, MINOR, open.** New. R4's argument reader starts at the matched verb. No artifact says where the comparison gets an `-R` value placed before `pr` or before the verb, how the two-`-R` count spans both positions, or that `-R=value` drops the `=`.
- **PR-035, MINOR, open.** A GraphQL mutation built in a variable or a substitution still matches no pattern.
- **PR-036, MINOR, open.** Three legitimate `gh api` calls still refuse: `-f merge_method=merge` before the path, the `:owner/:repo` placeholders, and pattern 6 over every variable-path write.
- **PR-037, MINOR, open.** `uv run --directory` and `direnv exec` still change the directory `gh` runs in with no separator, prefix, or `env`.
- **PR-038, MINOR, open.** Ownership item 6 still reads as enforced, and R4 still doesn't say to compare the branch with `origin/` stripped.
- **PR-039, MINOR, open.** A timed-out lookup still has two different messages, and the error rows don't say which carry the line about a person's own terminal.
- **PR-040, MINOR, open.** Widened to three stale spec passages. The Validation Strategy line now also says only "`-R` before the verb", while FR-012 names every placement.
- **PR-042, MINOR, open.** A quoted or variable `gh` word still matches no pattern.
- **PR-043, MINOR, open.** Pattern 8 still refuses greps with `\|`, regexes with `.*`, and commit messages that quote a refused form.
- **PR-044, MINOR, open.** A `gh` call inside a script, such as `release.py`, is still neither refused nor recorded.
- **PR-045, MINOR, open.** The `WFCTL_BRANCH` override still names the branch without reading `cwd`, against FR-012c.

## Review 2026-10-23T23:14Z

- Verdict: satisfied
- Reviewed: plan.md b90696cd3c1290bfdf731946fc1fd5c8f06fbd7b, spec.md 55fff2c781ba78aa9f112eed7fe5f4bd8d604dbe, .specify/memory/constitution.md absent, design.md e82e45ce32266ada7c33003be09900fdbd625387, docs/architecture/design/622-review-records-in-state-dir.md 4027336f312d54eaf9b30470a60a701fe87f5e8c, docs/architecture/design/622-review-groups-list.md 44048f18080066767fa5f064e3b7e75c9738fa91, docs/architecture/design/622-blocked-reviewer-relays-report.md 737f15b5d4a3019e229cdc9bb30a6eb544450116, docs/architecture/design/622-review-check-in-worktree-guard.md 5f12268036002c751f8a007740e18c0a767c67a4, research.md d1c7429bc972c48b62731ab50f526aa3aa0d4fcc, data-model.md 4a2b1597bd61bf6d47295f00336d5a0fb2716f26, contracts/cli.md 5d451fe4fb033e184a46103c2a32732f3f4582ca, contracts/config.md a6cb93ef21e11f2778edb6e78b51027b2dbd0576, quickstart.md ff7e876c9ed0bd86381649db4d6a0ffec639348c, docs/architecture/review-covers-unreviewed-commits.md 69bf5f4cdcae15c3495bf402deb23c104fa3bd3c, docs/architecture/vendor-upstream-skills.md 299f4f8cb5e2b2e0d84661741696f97ca6c0b3f0, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/wfctl-records-outward-actions-and-never-gates-them.md 8ff8575e2c4b1e5c7ff342092144866d12c98380, AGENTS.md 4dfb90941c8fb593b64d5bdc5d2ff631a4bcc70a, wfctl/_hook.py 77060f8723515559fe708b0e9f10bff2ee9ae99c, wfctl/_entry.py a26598d8eeb62a3847fff5fb70235410ae4ccde9, wfctl/_io.py 50990ecb0d1bfb76788e4592465c21bffb3306ed, wfctl/_paths.py 73d865219982aa4da4aade36fe472032fe550da7, wfctl/_restart.py 97eface9df371260af973dca55a215a2251304de, wfctl/_guard.py 2b6f0d39f1c0af749d32b0fbd409448fdf5e06f3, tests/test_guard_entry.py 04b8a817989f7d5af46815ae6cf36a29b916c5d1, tests/test_skill_attribution.py 6665bbf9db2490b969e0d389d0e45561accadb6a, wfctl/agents/skills/NOTICES.md 4aeb6145750062f3fbc661974f460a2f885f8ab2, wfctl/agents/skills/fanning-out-code-review/SKILL.md dcf63a66bd69730ab52866916c0bd83299a395c2, wfctl/agents/skills/code-review/SKILL.md f1b669063ac31d22c94cfaebb32c1131f147e304, wfctl/agents/skills/idea-refine/SKILL.md ca60506bac2baa0dd8bca0e3ef9b42de20a524d4, wfctl/agents/skills/opening-a-change/SKILL.md ec2437e0ab6ff1d188cadd9b677db0c715144ee5, wfctl/agents/skills/receiving-code-review/SKILL.md d9dc70c6c98e60b96b9fb591e2079920bd2eec99, wfctl/agents/skills/architecture-decisions/SKILL.md bdcc407f2bbe287b6d31099ab2bcf483129e405f, .github/scripts/release.py 5573934e6746db3dd261a7c143d91730b22decf1, plan-review.plan.md f7ee6cd95c7e21eeeb8c8d33d730fa3e768a0224 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 11 · Fixed since the earlier review: 3
- Detail: /Users/andremarin/Development/wfctl-specs/622-security-review-panel/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-039, PR-040, PR-045) |
| Requirements and traceability | Outstanding (PR-040, PR-044) |
| Architecture and boundaries | Outstanding (PR-038, PR-045) |
| Adversarial implementation and verification | Outstanding (PR-036, PR-043, PR-049, PR-050; PR-046 and PR-048 fixed) |
| Security and reliability | Outstanding (PR-035, PR-037, PR-038, PR-042, PR-044, PR-049, PR-050; PR-046 and PR-047 fixed) |

### Findings

- **PR-046, MAJOR, fixed.** Fixed by R4 (What sits before a command word) and R6 pattern 8, which allow one plain `-R` before `pr` and before the verb and refuse every other word starting with `-` there, plus FR-012b, the new contract row, and the planned tests. `gh pr --squash=true merge 630` and two `-R` before `pr` now refuse.
- **PR-047, MINOR, fixed.** Fixed by R4 item 2. A plain `-R` value can't contain a quote, `$(`, or a backtick, so `gh -R $(git push -q; echo a/b) pr merge 630` refuses at the value.
- **PR-048, MINOR, fixed.** Fixed by R4 (Another repository) item 1, which says where each `-R` value is read from, drops the `=` in `-R=value`, and counts `-R` across all three places. Its one remaining question, which value goes to `gh pr view`, moves to PR-050.
- **PR-049, MAJOR, open.** New. Every pattern and the substring test require a lowercase `gh`, but macOS runs `gh` with any capitalization: `GH --version` prints `gh version 2.91.0`, and `GH pr merge --help` prints the merge help. `GH pr create --fill` misses the substring test, and `GH pr merge 630` matches no pattern, so both open or merge an unreviewed PR.
- **PR-050, MINOR, open.** New. R4 compares a `HOST/OWNER/REPO` value after dropping the host, so the check treats `gh pr -R ghe.example.com/andremarin/wfctl merge 630` as this repository while `gh` merges on the other host. No artifact says which value goes to `gh pr view`. The spec's Edge Case and the guard record name only `OWNER/REPO`.
- **PR-035, MINOR, open.** A GraphQL mutation built in a variable or a substitution still matches no pattern.
- **PR-036, MINOR, open.** Three legitimate `gh api` calls still refuse: `-f merge_method=merge` before the path, the `:owner/:repo` placeholders, and pattern 6 over every variable-path write.
- **PR-037, MINOR, open.** `uv run --directory` and `direnv exec` still change the directory `gh` runs in with no separator, prefix, or `env`.
- **PR-038, MINOR, open.** Ownership item 6 still reads as enforced, and R4 still doesn't say to compare the branch with `origin/` stripped.
- **PR-039, MINOR, open.** A timed-out lookup still has two different messages, and the error rows don't say which carry the line about a person's own terminal.
- **PR-040, MINOR, open.** Narrowed to two stale spec passages: the round cap in US3 and the other-branch test in the Validation Strategy. The new Validation Strategy line now names `-R` before `pr`.
- **PR-042, MINOR, open.** A quoted or variable `gh` word still matches no pattern.
- **PR-043, MINOR, open.** Widened. Pattern 8 now also refuses any text that quotes a flag after `gh`, which item 3 names. Greps with `\|`, regexes with `.*`, and commit messages quoting an unplain command word are still refused and unnamed.
- **PR-044, MINOR, open.** A `gh` call inside a script, such as `release.py`, is still neither refused nor recorded.
- **PR-045, MINOR, open.** The `WFCTL_BRANCH` override still names the branch without reading `cwd`, against FR-012c.

## Review 2026-10-24T04:46Z

- Verdict: satisfied
- Reviewed: plan.md f89881396f793a8a0306340916ef3ddb051c27a6, spec.md 6173e59cded4478f74c5c5fc9bc53e05bf9f12a1, .specify/memory/constitution.md absent, design.md e82e45ce32266ada7c33003be09900fdbd625387, docs/architecture/design/622-review-records-in-state-dir.md 4027336f312d54eaf9b30470a60a701fe87f5e8c, docs/architecture/design/622-review-groups-list.md 44048f18080066767fa5f064e3b7e75c9738fa91, docs/architecture/design/622-blocked-reviewer-relays-report.md 737f15b5d4a3019e229cdc9bb30a6eb544450116, docs/architecture/design/622-review-check-in-worktree-guard.md 9ca19addd8c991d2baa103aafc4a3730d088683a, research.md 8fd2f0e0ff3892f4d990d2652cb7902943533c06, data-model.md 4a2b1597bd61bf6d47295f00336d5a0fb2716f26, contracts/cli.md 7d6f3ccdd5fa102650a27f17e3018be2fe852c1e, contracts/config.md a6cb93ef21e11f2778edb6e78b51027b2dbd0576, quickstart.md ff7e876c9ed0bd86381649db4d6a0ffec639348c, docs/architecture/review-covers-unreviewed-commits.md 69bf5f4cdcae15c3495bf402deb23c104fa3bd3c, docs/architecture/vendor-upstream-skills.md 299f4f8cb5e2b2e0d84661741696f97ca6c0b3f0, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/wfctl-records-outward-actions-and-never-gates-them.md 8ff8575e2c4b1e5c7ff342092144866d12c98380, AGENTS.md 4dfb90941c8fb593b64d5bdc5d2ff631a4bcc70a, wfctl/_hook.py 77060f8723515559fe708b0e9f10bff2ee9ae99c, wfctl/_entry.py a26598d8eeb62a3847fff5fb70235410ae4ccde9, wfctl/_io.py 50990ecb0d1bfb76788e4592465c21bffb3306ed, wfctl/_paths.py 73d865219982aa4da4aade36fe472032fe550da7, wfctl/_restart.py 97eface9df371260af973dca55a215a2251304de, wfctl/_guard.py 2b6f0d39f1c0af749d32b0fbd409448fdf5e06f3, tests/test_guard_entry.py 04b8a817989f7d5af46815ae6cf36a29b916c5d1, tests/test_skill_attribution.py 6665bbf9db2490b969e0d389d0e45561accadb6a, wfctl/agents/skills/NOTICES.md 4aeb6145750062f3fbc661974f460a2f885f8ab2, wfctl/agents/skills/fanning-out-code-review/SKILL.md dcf63a66bd69730ab52866916c0bd83299a395c2, wfctl/agents/skills/code-review/SKILL.md f1b669063ac31d22c94cfaebb32c1131f147e304, wfctl/agents/skills/idea-refine/SKILL.md ca60506bac2baa0dd8bca0e3ef9b42de20a524d4, wfctl/agents/skills/opening-a-change/SKILL.md ec2437e0ab6ff1d188cadd9b677db0c715144ee5, wfctl/agents/skills/receiving-code-review/SKILL.md d9dc70c6c98e60b96b9fb591e2079920bd2eec99, wfctl/agents/skills/architecture-decisions/SKILL.md bdcc407f2bbe287b6d31099ab2bcf483129e405f, .github/scripts/release.py 5573934e6746db3dd261a7c143d91730b22decf1, plan-review.plan.md b90696cd3c1290bfdf731946fc1fd5c8f06fbd7b (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 2 · MINOR 11 · Fixed since the earlier review: 2
- Detail: /Users/andremarin/Development/wfctl-specs/622-security-review-panel/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-039, PR-040, PR-045) |
| Requirements and traceability | Outstanding (PR-040, PR-044, PR-052) |
| Architecture and boundaries | Outstanding (PR-038, PR-045, PR-053) |
| Adversarial implementation and verification | Outstanding (PR-036, PR-037, PR-043, PR-051, PR-053; PR-049 and PR-050 fixed) |
| Security and reliability | Outstanding (PR-035, PR-037, PR-038, PR-042, PR-044, PR-051, PR-052; PR-049 and PR-050 fixed) |

### Findings

- **PR-049, MAJOR, fixed.** Fixed by R6, which now matches the program word `gh` case-insensitively in the substring test and in every pattern that names it, and keeps the rest of each pattern case-sensitive. FR-012b, a new Edge Case, a contract row, the plan's test list, and the guard record's Decision item 7 say the same. `GH pr merge 630`, `GH pr create --fill`, and `/opt/homebrew/bin/Gh pr create --fill` now match. `gh PR merge --help` exits 1, and GitHub returns 404 for a `PULLS` path, so keeping the rest case-sensitive lets nothing through.
- **PR-050, MINOR, fixed.** Fixed by R4 (Another repository) item 1, which refuses an `-R` host other than `github.com` and passes the value to `gh pr view` as written, plus FR-012b, the Edge Case, Decision item 7, a contract row, and a planned test.
- **PR-051, MAJOR, open.** New. Pattern 3 lists its body flags as words and its path as "ending in `/pulls`", and doesn't say whether it reads an attached field or a query string after the path. `gh api` reads `-fper_page=1` as a field, so under the whole-word reading, `gh api repos/{owner}/{repo}/pulls -fhead=630-x -fbase=main -ftitle=t` opens a PR without matching. A `pulls?x=1` path also gets past a strict reading, assuming GitHub ignores the query string on a POST as it does on a GET.
- **PR-052, MAJOR, open.** New. `gh extension list` shows `gh stack` from `github/gh-stack` on this machine. `gh stack submit` creates PRs, and `gh stack merge` merges them without prompting in a non-interactive terminal. Neither matches any pattern, and the spec records only `gh alias set` shortcuts as a limit.
- **PR-053, MINOR, open.** New. R4's host rule names `github.com` rather than this checkout's host, so in a checkout on a GitHub Enterprise host, the check treats `-R github.com/<owner>/<repo>` as this repository. `gh` also accepts a URL as an `-R` value, and R4 doesn't say how the check reads one after the verb.
- **PR-035, MINOR, open.** A GraphQL mutation built in a variable or a substitution still matches no pattern.
- **PR-036, MINOR, open.** Three legitimate `gh api` calls still refuse: `-f merge_method=merge` before the path, the `:owner/:repo` placeholders, and pattern 6 over every variable-path write.
- **PR-037, MINOR, open.** Widened. `uv run --directory` and `direnv exec` still change the directory `gh` runs in. `<<<630 xargs gh pr merge` also adds an argument the check never reads, so the check judges the current branch's PR while `gh` merges PR 630.
- **PR-038, MINOR, open.** Ownership item 6 still reads as enforced, and R4 still doesn't say to compare the branch with `origin/` stripped.
- **PR-039, MINOR, open.** A timed-out lookup still has two different messages, and the error rows don't say which carry the line about a person's own terminal.
- **PR-040, MINOR, open.** Two spec passages are still stale: the round cap in US3 and the other-branch test in the Validation Strategy.
- **PR-042, MINOR, open.** A quoted or variable `gh` word still matches no pattern.
- **PR-043, MINOR, open.** Widened slightly: pattern 8 now also refuses `GH` followed by a flag in quoted text. Greps with `\|`, regexes with `.*`, and commit messages quoting an unplain command word are still refused and unnamed.
- **PR-044, MINOR, open.** A `gh` call inside a script, such as `release.py`, is still neither refused nor recorded.
- **PR-045, MINOR, open.** The `WFCTL_BRANCH` override still names the branch without reading `cwd`, against FR-012c.

## Review 2026-10-24T05:48Z

- Verdict: satisfied
- Reviewed: plan.md 7d3e9135f3df5ae3bf18244aa18b0de06240ed58, spec.md 9f0fd27407bc80a542c4dbb5047b617ff61fef3f, .specify/memory/constitution.md absent, design.md e82e45ce32266ada7c33003be09900fdbd625387, docs/architecture/design/622-review-records-in-state-dir.md 4027336f312d54eaf9b30470a60a701fe87f5e8c, docs/architecture/design/622-review-groups-list.md 44048f18080066767fa5f064e3b7e75c9738fa91, docs/architecture/design/622-blocked-reviewer-relays-report.md 737f15b5d4a3019e229cdc9bb30a6eb544450116, docs/architecture/design/622-review-check-in-worktree-guard.md 58c5bdc5f834cb064b642c8f89cb7c679ac2e866, research.md 156a96a1e2c40cb3f93c3a05d37b7596950093bf, data-model.md 4a2b1597bd61bf6d47295f00336d5a0fb2716f26, contracts/cli.md 8238fee7c35630897babd7cbd93e1d809c13202b, contracts/config.md a6cb93ef21e11f2778edb6e78b51027b2dbd0576, quickstart.md ff7e876c9ed0bd86381649db4d6a0ffec639348c, docs/architecture/review-covers-unreviewed-commits.md 69bf5f4cdcae15c3495bf402deb23c104fa3bd3c, docs/architecture/vendor-upstream-skills.md 299f4f8cb5e2b2e0d84661741696f97ca6c0b3f0, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/wfctl-records-outward-actions-and-never-gates-them.md 8ff8575e2c4b1e5c7ff342092144866d12c98380, AGENTS.md 4dfb90941c8fb593b64d5bdc5d2ff631a4bcc70a, wfctl/_hook.py 77060f8723515559fe708b0e9f10bff2ee9ae99c, wfctl/_entry.py a26598d8eeb62a3847fff5fb70235410ae4ccde9, wfctl/_io.py 50990ecb0d1bfb76788e4592465c21bffb3306ed, wfctl/_paths.py 73d865219982aa4da4aade36fe472032fe550da7, wfctl/_restart.py 97eface9df371260af973dca55a215a2251304de, wfctl/_guard.py 2b6f0d39f1c0af749d32b0fbd409448fdf5e06f3, tests/test_guard_entry.py 04b8a817989f7d5af46815ae6cf36a29b916c5d1, tests/test_skill_attribution.py 6665bbf9db2490b969e0d389d0e45561accadb6a, wfctl/agents/skills/NOTICES.md 4aeb6145750062f3fbc661974f460a2f885f8ab2, wfctl/agents/skills/fanning-out-code-review/SKILL.md dcf63a66bd69730ab52866916c0bd83299a395c2, wfctl/agents/skills/code-review/SKILL.md f1b669063ac31d22c94cfaebb32c1131f147e304, wfctl/agents/skills/idea-refine/SKILL.md ca60506bac2baa0dd8bca0e3ef9b42de20a524d4, wfctl/agents/skills/opening-a-change/SKILL.md ec2437e0ab6ff1d188cadd9b677db0c715144ee5, wfctl/agents/skills/receiving-code-review/SKILL.md d9dc70c6c98e60b96b9fb591e2079920bd2eec99, wfctl/agents/skills/architecture-decisions/SKILL.md bdcc407f2bbe287b6d31099ab2bcf483129e405f, .github/scripts/release.py 5573934e6746db3dd261a7c143d91730b22decf1, plan-review.plan.md f89881396f793a8a0306340916ef3ddb051c27a6 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 4 · MINOR 13 · Fixed since the earlier review: 2
- Detail: /Users/andremarin/Development/wfctl-specs/622-security-review-panel/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-039, PR-040, PR-045) |
| Requirements and traceability | Outstanding (PR-040, PR-044, PR-055, PR-056; PR-052 fixed) |
| Architecture and boundaries | Outstanding (PR-038, PR-045, PR-053, PR-059) |
| Adversarial implementation and verification | Outstanding (PR-036, PR-037, PR-043, PR-053, PR-054, PR-056, PR-057, PR-058, PR-059; PR-051 fixed) |
| Security and reliability | Outstanding (PR-035, PR-037, PR-038, PR-042, PR-044, PR-054, PR-055, PR-056, PR-057, PR-058; PR-051 and PR-052 fixed) |

### Findings

- **PR-051, MAJOR, fixed.** Fixed by R6 pattern 3, which now reads a path ending in `/pulls`, `/pulls/`, or `/pulls?<query>`; a body flag as its own word, attached, or after `=`; and `-X` or `--method` with `POST` in every spacing and any case. FR-012b, the Validation Strategy, a contract row, and the plan's test list say the same. Both commands the earlier finding named now match.
- **PR-052, MAJOR, fixed.** Fixed by R4 and R6 pattern 8, which require the word after `gh` to be on a fixed list of `gh`'s own commands, taken from `gh help` in `gh` 2.91, excluding `copilot` and `agent-task`. `gh stack submit` and `gh stack merge` now refuse every time. FR-012b, the Edge Case, a contract row, the plan's test list, and the guard record agree.
- **PR-054, MAJOR, open.** New. Pattern 8 drops a trailing backtick from the command word and allows a backtick at the end of the verb, so `` gh pr` git push -q` merge 630 `` reads as `pr` followed by the plain verb `git`. Pattern 1 requires whitespace after `pr`, so nothing matches. The shell runs the push, joins the substitution's empty output to `pr`, and runs `gh pr merge 630` unjudged. In zsh, `` gh pr` true` view 633 --json number `` prints PR 633.
- **PR-055, MAJOR, open.** New. `extension` is on the list, and `gh extension exec stack merge` runs `gh stack merge`, which `gh extension exec stack merge --help` confirms. Pattern 8 stops at `extension`, and no other pattern matches, so the extension PR-052 refuses is one word away.
- **PR-056, MAJOR, open.** New. `gh` allows a two-word alias under one of its own commands, as its help shows with `gh issue mine`. `gh alias set 'pr ship' 'pr merge'` passes the check, and `gh pr ship 630` then merges without matching. With a scratch `GH_CONFIG_DIR` holding `pr ship: pr merge`, `gh pr ship --help` prints the merge help. The spec now says shortcuts refuse, and the alias limit was removed from the Edge Cases.
- **PR-057, MAJOR, open.** New. Pattern 3 still lists the specific forms it reads. `gh api 'repos/{owner}/{repo}/pulls#x' -f head=630-x -f base=main -f title=t` ends in `pulls#x`, and `gh` drops the fragment before sending. `gh api repos/{owner}/{repo}/pulls -ifhead=630-x -ifbase=main -iftitle=t` starts each flag with `-i`, and `gh` reads `-if` as `-i -f`. Both create a PR without matching.
- **PR-058, MINOR, open.** New. In `printf '%s\n' pr merge 630 | xargs gh`, nothing follows `gh`, so patterns 1 and 8, which both require `gh\s+`, never read a word. `xargs` runs `gh pr merge 630`. PR-037's suggested response doesn't close this gap.
- **PR-059, MINOR, open.** New. `gh api -X PUT repositories/<other id>/pulls/630/merge` matches pattern 2, but R4 compares only a `repos/<owner>/<repo>/` path, so the check judges this repository's PR 630 while `gh` merges another repository's. GitHub does route `repositories/1300044503/pulls/633`.
- **PR-043, MINOR, open.** Widened. Pattern 8 now refuses `gh` followed by any word off the list, so it also refuses `which gh && gh pr view`, `command -v gh || echo missing`, and prose with `GH` in capitals. Greps with `\|`, regexes with `.*`, and commit messages quoting an unplain command word are still refused and unnamed.
- **PR-053, MINOR, open.** Widened slightly. `gh api --hostname ghe.example.com` with `{owner}/{repo}` placeholders is judged as this repository while `gh` acts on the other host, beside the earlier `-R github.com/…` and URL cases.
- **PR-035, MINOR, open.** A GraphQL mutation built in a variable or a substitution still matches no pattern.
- **PR-036, MINOR, open.** Three legitimate `gh api` calls still refuse: `-f merge_method=merge` before the path, the `:owner/:repo` placeholders, and pattern 6 over every variable-path write.
- **PR-037, MINOR, open.** `uv run --directory`, `direnv exec`, and `<<<630 xargs gh pr merge` still change where `gh` runs or what it receives without a separator, prefix, or substitution.
- **PR-038, MINOR, open.** Ownership item 6 still reads as enforced, and R4 still doesn't say to compare the branch with `origin/` stripped.
- **PR-039, MINOR, open.** A timed-out lookup still has two different messages, and the error rows don't say which carry the line about a person's own terminal.
- **PR-040, MINOR, open.** Two spec passages are still stale: the round cap in US3 and the other-branch test in the Validation Strategy.
- **PR-042, MINOR, open.** A quoted or variable `gh` word still matches no pattern.
- **PR-044, MINOR, open.** A `gh` call inside a script, such as `release.py`, is still neither refused nor recorded.
- **PR-045, MINOR, open.** The `WFCTL_BRANCH` override still names the branch without reading `cwd`, against FR-012c.

## Review 2026-10-24T12:41Z

- Verdict: satisfied
- Reviewed: plan.md 41b127397541b1228cc131fe0fc86f80bfc795bf, spec.md 292a98a74e2a9c0a33629e4513ae50a8e85cbc9a, .specify/memory/constitution.md absent, design.md e82e45ce32266ada7c33003be09900fdbd625387, docs/architecture/design/622-review-records-in-state-dir.md 4027336f312d54eaf9b30470a60a701fe87f5e8c, docs/architecture/design/622-review-groups-list.md 44048f18080066767fa5f064e3b7e75c9738fa91, docs/architecture/design/622-blocked-reviewer-relays-report.md 737f15b5d4a3019e229cdc9bb30a6eb544450116, docs/architecture/design/622-review-check-in-worktree-guard.md 0a9221a25e13dbaa3bd7a05cba7edb8c8b13724a, research.md 17f7b1f36eb7ccd74ae5e28ceb529ed3c83b4962, data-model.md 4a2b1597bd61bf6d47295f00336d5a0fb2716f26, contracts/cli.md 9c633dacc9f4c7b8e578315d36323d05f1701b77, contracts/config.md a6cb93ef21e11f2778edb6e78b51027b2dbd0576, quickstart.md ff7e876c9ed0bd86381649db4d6a0ffec639348c, docs/architecture/review-covers-unreviewed-commits.md 69bf5f4cdcae15c3495bf402deb23c104fa3bd3c, docs/architecture/vendor-upstream-skills.md 299f4f8cb5e2b2e0d84661741696f97ca6c0b3f0, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/wfctl-records-outward-actions-and-never-gates-them.md 8ff8575e2c4b1e5c7ff342092144866d12c98380, AGENTS.md 4dfb90941c8fb593b64d5bdc5d2ff631a4bcc70a, wfctl/_hook.py 77060f8723515559fe708b0e9f10bff2ee9ae99c, wfctl/_entry.py a26598d8eeb62a3847fff5fb70235410ae4ccde9, wfctl/_io.py 50990ecb0d1bfb76788e4592465c21bffb3306ed, wfctl/_paths.py 73d865219982aa4da4aade36fe472032fe550da7, wfctl/_restart.py 97eface9df371260af973dca55a215a2251304de, wfctl/_guard.py 2b6f0d39f1c0af749d32b0fbd409448fdf5e06f3, tests/test_guard_entry.py 04b8a817989f7d5af46815ae6cf36a29b916c5d1, tests/test_skill_attribution.py 6665bbf9db2490b969e0d389d0e45561accadb6a, wfctl/agents/skills/NOTICES.md 4aeb6145750062f3fbc661974f460a2f885f8ab2, wfctl/agents/skills/fanning-out-code-review/SKILL.md dcf63a66bd69730ab52866916c0bd83299a395c2, wfctl/agents/skills/code-review/SKILL.md f1b669063ac31d22c94cfaebb32c1131f147e304, wfctl/agents/skills/idea-refine/SKILL.md ca60506bac2baa0dd8bca0e3ef9b42de20a524d4, wfctl/agents/skills/opening-a-change/SKILL.md ec2437e0ab6ff1d188cadd9b677db0c715144ee5, wfctl/agents/skills/receiving-code-review/SKILL.md d9dc70c6c98e60b96b9fb591e2079920bd2eec99, wfctl/agents/skills/architecture-decisions/SKILL.md bdcc407f2bbe287b6d31099ab2bcf483129e405f, .github/scripts/release.py 5573934e6746db3dd261a7c143d91730b22decf1, plan-review.plan.md 7d3e9135f3df5ae3bf18244aa18b0de06240ed58 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 5 · Fixed since the earlier review: 16
- Detail: /Users/andremarin/Development/wfctl-specs/622-security-review-panel/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-060, PR-061; PR-039, PR-040, PR-045 fixed) |
| Requirements and traceability | Outstanding (PR-060; PR-040, PR-044, PR-055, PR-056 fixed) |
| Architecture and boundaries | Resolved (PR-038, PR-045, PR-053, PR-059 fixed) |
| Adversarial implementation and verification | Outstanding (PR-043, PR-062; PR-036, PR-037, PR-053, PR-054, PR-056, PR-057, PR-058, PR-059 fixed) |
| Security and reliability | Outstanding (PR-063; PR-035, PR-037, PR-038, PR-042, PR-044, PR-054, PR-055, PR-056, PR-057, PR-058 fixed) |

### Findings

Scored under Andre's decision of 2026-10-24: the review check stops adding rules, a disguised command already listed as a known limit isn't a finding, and a new one is at most MINOR.

- **PR-060, MINOR, open.** New. The plan's Summary still says the check refuses any command whose text it can't read with certainty, and R6 and the guard record place the cutoff at the fifth plan review. But the limit list includes PR-035 and PR-037, first reported in the 2026-10-23T20:54Z review, and PR-042 and PR-044, first reported at 22:17Z. PR-035 and PR-042 also involve a substitution or a variable, which R6's sorting test says should refuse. Stands because the sentences around the list contradict it. Dating the cutoff at 2026-10-24 and naming the limits in the Summary would fix it.
- **PR-061, MINOR, open.** New. R4 (Another branch) numbers its items 1, 2, 3, 4, and 3. The refusal text became a second item 3 when the PR-038 fix added items 3 and 4.
- **PR-062, MINOR, open.** New. The contract refuses `WFCTL_STATE_DIR` set for another branch and `WFCTL_BRANCH` naming a different branch from `cwd`, but the plan's `test_review_gate.py` list names neither. Many test fixtures, including those in `tests/conftest.py`, set `WFCTL_BRANCH`.
- **PR-063, MINOR, open.** New. A git alias written into `.git/config` with a file tool, such as `pm = !gh pr merge`, and a shell function from the person's profile both run `gh pr merge` with no `gh`, `merge`, or `sign` in the command text. No known limit names either. The response is to record them by widening limit 2.10 to cover scripts, git aliases, and shell aliases or functions.
- **PR-043, MINOR, open.** Narrowed. The spec now names the wrong refusals, but its one rewording, searching without the `gh ` prefix, fits only the two searches. `which gh && gh pr view` needs a separate command, and a commit message that quotes a refused form needs `git commit -F <file>`. R6 says the spec gives a rewording for each.
- **PR-054, PR-055, PR-056, PR-057, MAJOR, fixed.** Recorded as known limits in `spec.md §Edge Cases` (2.1 to 2.4) and R6. R4 item 1 now says `gh extension exec` passes, R4 item 3 says a two-word alias is accepted, R6 pattern 8 says the glued backtick reads as `pr`, and R6 pattern 3 and FR-012b name the invocations they read rather than every invocation.
- **PR-035, PR-037, PR-042, PR-044, PR-053, PR-058, PR-059, MINOR, fixed.** Recorded as known limits in `spec.md §Edge Cases` and R6 (Known limits). Naming `release.py` there answers PR-044's question about the release PR.
- **PR-036, MINOR, fixed.** The three wrong `gh api` refusals are recorded in `spec.md §Edge Cases`, each with a rewording that avoids the refusal as R4 describes it.
- **PR-038, MINOR, fixed.** R4 strips `origin/` from the trunk ref before comparing, which is correct for both forms `_paths.trunk_branch` returns. Ownership 6, R4 item 4, the guard record's Consequences, and a contract row call the rule a convention.
- **PR-039, MINOR, fixed.** `contracts/cli.md` names every refusal that uses the error refusal block, and the timed-out lookup has one message.
- **PR-040, MINOR, fixed.** US3 says nothing enforces the round cap until #626, and the Validation Strategy runs the other-branch merge from the trunk checkout and refuses it from a feature worktree.
- **PR-045, MINOR, fixed.** R4 (Timeouts and errors) item 2 and a contract row refuse a `WFCTL_BRANCH` that names a different branch from `cwd`, which agrees with FR-012c.

## Review 2026-10-24T12:47Z

- Verdict: satisfied
- Reviewed: plan.md 6a0e2d4abba00699396f571a735b7bd758b30f28, spec.md 839880bd6f5205a0073a1158793a7df7dc09c8e7, .specify/memory/constitution.md absent, design.md e82e45ce32266ada7c33003be09900fdbd625387, docs/architecture/design/622-review-records-in-state-dir.md 4027336f312d54eaf9b30470a60a701fe87f5e8c, docs/architecture/design/622-review-groups-list.md 44048f18080066767fa5f064e3b7e75c9738fa91, docs/architecture/design/622-blocked-reviewer-relays-report.md 737f15b5d4a3019e229cdc9bb30a6eb544450116, docs/architecture/design/622-review-check-in-worktree-guard.md c08a744939fabe46c8971bf8727e65c9306d61ad, research.md ba551572fd9977ddf274c92bc5ea034c8db29357, data-model.md 4a2b1597bd61bf6d47295f00336d5a0fb2716f26, contracts/cli.md 9c633dacc9f4c7b8e578315d36323d05f1701b77, contracts/config.md a6cb93ef21e11f2778edb6e78b51027b2dbd0576, quickstart.md ff7e876c9ed0bd86381649db4d6a0ffec639348c, docs/architecture/review-covers-unreviewed-commits.md 69bf5f4cdcae15c3495bf402deb23c104fa3bd3c, docs/architecture/vendor-upstream-skills.md 299f4f8cb5e2b2e0d84661741696f97ca6c0b3f0, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/wfctl-records-outward-actions-and-never-gates-them.md 8ff8575e2c4b1e5c7ff342092144866d12c98380, AGENTS.md 4dfb90941c8fb593b64d5bdc5d2ff631a4bcc70a, wfctl/_hook.py 77060f8723515559fe708b0e9f10bff2ee9ae99c, wfctl/_entry.py a26598d8eeb62a3847fff5fb70235410ae4ccde9, wfctl/_io.py 50990ecb0d1bfb76788e4592465c21bffb3306ed, wfctl/_paths.py 73d865219982aa4da4aade36fe472032fe550da7, wfctl/_restart.py 97eface9df371260af973dca55a215a2251304de, wfctl/_guard.py 2b6f0d39f1c0af749d32b0fbd409448fdf5e06f3, tests/test_guard_entry.py 04b8a817989f7d5af46815ae6cf36a29b916c5d1, tests/test_skill_attribution.py 6665bbf9db2490b969e0d389d0e45561accadb6a, wfctl/agents/skills/NOTICES.md 4aeb6145750062f3fbc661974f460a2f885f8ab2, wfctl/agents/skills/fanning-out-code-review/SKILL.md dcf63a66bd69730ab52866916c0bd83299a395c2, wfctl/agents/skills/code-review/SKILL.md f1b669063ac31d22c94cfaebb32c1131f147e304, wfctl/agents/skills/idea-refine/SKILL.md ca60506bac2baa0dd8bca0e3ef9b42de20a524d4, wfctl/agents/skills/opening-a-change/SKILL.md ec2437e0ab6ff1d188cadd9b677db0c715144ee5, wfctl/agents/skills/receiving-code-review/SKILL.md d9dc70c6c98e60b96b9fb591e2079920bd2eec99, wfctl/agents/skills/architecture-decisions/SKILL.md bdcc407f2bbe287b6d31099ab2bcf483129e405f, .github/scripts/release.py 5573934e6746db3dd261a7c143d91730b22decf1, plan-review.plan.md 41b127397541b1228cc131fe0fc86f80bfc795bf (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 1 · Fixed since the earlier review: 5
- Detail: /Users/andremarin/Development/wfctl-specs/622-security-review-panel/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-064; PR-060 and PR-061 fixed) |
| Requirements and traceability | Outstanding (PR-064; PR-060 fixed) |
| Architecture and boundaries | Clear |
| Adversarial implementation and verification | Resolved (PR-043 and PR-062 fixed) |
| Security and reliability | Resolved (PR-063 fixed) |

### Findings

Scored under Andre's decision of 2026-10-24: the review check stops adding rules, a disguised command already listed as a known limit isn't a finding, and a new one is at most MINOR. This review found no new disguised command.

- **PR-064, MINOR, open.** New. `research.md §R6` item 1 says the rules cover "the holes fixed before 2026-10-24" and that every hole still open on that date is a known limit. `plan.md §Summary` and the guard record say the same. But the guard record's own Log adds two rules on 2026-10-24, and the reviews at 2026-10-24T04:46Z and 05:48Z mark PR-049 to PR-052 as fixed by them. PR-051 and PR-052 were open when the day began. Stands because the date alone doesn't mark the cutoff. Naming the decision instead, as the spec's Clarification already does with "from now on", would fix it.
- **PR-060, MINOR, fixed.** Fixed by `plan.md §Summary`, which now names the known limits in the spec's Edge Cases and #627, and by R6 item 1 and the guard record, which date the cutoff instead of counting reviews.
- **PR-061, MINOR, fixed.** Fixed by `research.md §R4` (Another branch), which now numbers its items 1 to 5.
- **PR-062, MINOR, fixed.** Fixed by the `test_review_gate.py` list in `plan.md §Project Structure`, which adds both override refusals and says every other gate test clears `WFCTL_BRANCH` or sets it to the `cwd`'s branch, since `tests/conftest.py` sets it in two fixtures.
- **PR-063, MINOR, fixed.** Fixed by `spec.md §Edge Cases` known limit 2.10 and R6 limit 11, which now name a git alias in `.git/config` and a shell function or alias from the person's profile.
- **PR-043, MINOR, fixed.** Fixed by `spec.md §Edge Cases` wrong refusals 4 to 6, which give a search without the `gh ` prefix, `which gh` on its own, and `git commit -F <file>`. Each one avoids the refusal as R6 describes the patterns.
