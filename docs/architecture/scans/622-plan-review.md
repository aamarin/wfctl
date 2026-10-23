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

- **PR-001, BLOCKER, open.** The plan keeps the vendored `/security-review` file byte-identical to upstream, and `vendor-upstream-skills.md` requires an attribution line inside every derived file. The test in `tests/test_skill_attribution.py` only reads `*/SKILL.md` and the specify scripts, so it can't see a file at `reviewing-security/references/security-review.md`. The finding stands because the plan has no place for the attribution line. Part of the cause is in `spec.md`, where FR-024 asks for the line and FR-025 says the file stays unedited.
- **PR-002, MAJOR, open.** Once a command matches, the review check only says how it fails for an unreadable record and a failed `gh` lookup. Every other error is unassigned. The `gh pr view` call has no timeout, so the host can kill the guard on its own hook timeout without an exit 2, and the merge goes ahead.
- **PR-003, MAJOR, open.** The sign-off refusal is the pattern `\breview\s+sign-off\b`. An agent gets past it with `wfctl review 'sign-off'`, `wfctl review sign\-off`, a shell variable, or by writing `sign-off.json` directly, and FR-013 requires a refusal every time.
- **PR-004, MAJOR, open.** Other `gh` commands open or merge a PR without matching, so SC-001's "zero exceptions" can't hold. Examples are `gh pr -R o/r merge`, `gh api` calls on the pulls endpoints, the GraphQL mutations, and `gh pr merge` while checks are pending, which turns on auto-merge and merges a later head. Part of the cause is in `spec.md`, since FR-012 lists only three commands.
- **PR-005, MAJOR, open.** R4 doesn't say how the check reads the PR argument or `--head` out of a command it only matches as text. When the extraction misses the argument, the check falls back to the current branch and judges the wrong one. The plan judges `--head` locally instead of looking it up on GitHub as FR-012a says, and it doesn't handle `-R`.
- **PR-006, MAJOR, open.** A run with zero expected reviewers completes with no review at all. This happens when a group's `reviewers` list is empty or missing, which `wfctl check config` doesn't catch, or when every listed model is unavailable. That can skip the security group, which FR-001 forbids.
- **PR-007, MINOR, open.** The `shutil.which` lookup runs on the agent's `PATH`, so the plan's claim that the agent can't mark a reviewer unavailable doesn't hold. In the other direction, a model that is on `PATH` but fails, such as Codex without a login, blocks every PR. The plan doesn't say it reads FR-023 this narrowly.
- **PR-008, MINOR, open.** The plan marks the `a-rule-is-expressed-as-a-check.md` gate as passed, while its own text says the three-round cap is checkable and ships as prose until #626. That belongs in Complexity Tracking as a deviation.
- **PR-009, MINOR, open.** The Safety section of `AGENTS.md` still says wfctl doesn't gate outward actions, and the plan lists no edit to it.
- **PR-010, MINOR, open.** The trunk refs are underspecified. The `trunk_branch` function usually returns `origin/main`, so the plan's "`origin/` counterpart" has nothing to add. The plan doesn't say what happens when `trunk_branch` returns None, and it uses discovery where FR-006 sets the default to `main`.
- **PR-011, MINOR, open.** The config contract puts no limit on a group's name. A name such as `../x` writes outside `reviews/`, case isn't normalised (`Security` and `security`), and a name can start with a character that isn't a letter.
- **PR-012, MINOR, open.** The spec's Validation Strategy and the design record both name a `wfctl store specs` test for SC-004, and the plan's test list leaves it out. The plan also doesn't say what happens to an old `$FEATURE_DIR/reviews/` folder.
- **PR-013, MINOR, open.** FR-003, the security group committing its fixes before the code group reviews, and FR-004, one findings table in chat, have no place in the plan. The plan names the skills it rewrites but not what they say.
- **PR-014, MINOR, open.** The upstream `security-and-hardening` skill points at `../../references/security-checklist.md`, a path outside its own folder, and R10 doesn't vendor that file.
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
- **PR-004, MAJOR, fixed.** Fixed by R6, FR-012, and SC-001. The patterns cover `-R` before the verb, both merge endpoints, a `gh api` create, and the GraphQL mutations, `--auto` refuses, and the spec's Edge Cases record the spellings that stay open.
- **PR-005, MAJOR, fixed.** Fixed by R4. It states the argument rule, looks `--head` up with `git ls-remote`, refuses when `-R` names another repository, and never falls back to the current branch.
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
- **PR-016, MAJOR, open.** The new table in `vendor-upstream-skills.md` changes an accepted record, and the plan doesn't say whether that is an amendment or a new record. The record currently calls the templates the one case where the notice stands in for the line. The existing test also reads every non-template row as a file that must carry the line, so the new row fails it until the test can tell the tables apart.
- **PR-017, MAJOR, open.** The check judges a matched command before any of the text runs. In `git commit -am x && git push && gh pr create`, or `git switch other && gh pr create`, the pull request opens on a commit or branch the check never judged. The spec's known limits don't name this case.
- **PR-018, MAJOR, open.** A relayed report travels in the command text, through a heredoc or `echo`, so the guard's text match reads it. A report quoting `gh pr create`, or mentioning "review" before "sign-off", is refused.
- **PR-019, MAJOR, open.** `gh pr new`, the built-in alias of `gh pr create`, matches no pattern, and neither does the GraphQL `enqueuePullRequest` mutation for the merge queue.
- **PR-020, MINOR, open.** R4's flag lists miss `-s`, `-m`, and `-r` for `merge`, don't say how `--flag=value` is read, and compare `-R HOST/OWNER/REPO` against `nameWithOwner`. Each fails safe as a wrong refusal.
- **PR-021, MINOR, open.** `gh api repos/other/repo/pulls/N/merge` and `GH_REPO=other/repo gh pr merge N` look up pull request N in this repository, which is the wrong-repository case the `-R` rule stops.
- **PR-022, MINOR, open.** Read literally, the rule that a non-zero exit refuses misfires on `git merge-base --is-ancestor` and `git show-ref --verify`, which answer "no" with exit 1. The `_paths` helpers R3 and R5 name run `git` with no timeout, and `resolve_agent_dir` creates the directory it is asked about by default.
- **PR-023, MINOR, open.** FR-021 asks for a finding on any group with no reviewers, and the config contract applies it only to custom groups, so a built-in group with an empty list has no defined meaning.
- **PR-024, MINOR, open.** The guard record still lists four commands, the groups record still lists three `check config` problems and says the review continues on a bad config, and `design.md` still gives #626 the question of how the sign-off is recorded, which R9 now decides.
- **PR-025, MINOR, open.** A pseudo-terminal from `script` or `pty.spawn` satisfies `isatty`, so FR-013's claim that a missed spelling still can't sign off overstates the check. It should read as a second obstacle, recorded beside the direct-write limit.

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

- **PR-016, MAJOR, fixed.** Fixed by R10 items 3 to 6 and the plan's Constitution Check. The vendor record is amended in place, its "one case" sentence names both cases, and the test tells the new row apart by its path. The plan counts nine earlier amendments where the record's Log shows eight.
- **PR-017, MAJOR, fixed.** Fixed by FR-012b, R4, and the guard record. A pull request command that follows another command in the same text refuses, and every match is judged.
- **PR-018, MAJOR, fixed.** Fixed by FR-017, R8, and the relay contract. `wfctl relay` reads the report only from the file `--from` names.
- **PR-019, MAJOR, fixed.** Fixed by R6 patterns 1 and 4, FR-012, and the spec's Edge Cases, which add `gh pr new`, `enqueuePullRequest`, and the `gh alias` limit.
- **PR-020, MINOR, fixed.** Fixed by R4, which adds the short merge flags, `--flag=value`, attached short values, `--help`, and a host prefix on `-R`.
- **PR-021, MINOR, fixed.** Fixed by R4 and FR-012a, which refuse another repository named by `GH_REPO=` or a `repos/<owner>/<repo>/` path.
- **PR-022, MINOR, open.** Narrowed. Answer exit codes and `create=False` are fixed, but `resolve_agent_dir` reaches `project_name`'s `git` call through `project_state_dir`, which takes no timeout, and the plan doesn't say how the check reads the current branch, where `resolve_branch` has no timeout either.
- **PR-023, MINOR, fixed.** Fixed by FR-019, FR-021, the data model, and the config contract. An empty `reviewers` list is a finding on any group, and only a missing key gives a built-in group its default.
- **PR-024, MINOR, fixed.** Fixed by the guard, relay, and groups records and by `design.md`'s Open Questions.
- **PR-025, MINOR, fixed.** Fixed by FR-013, R9, and the spec's Edge Cases, which call the terminal check a second obstacle and record the pseudo-terminal limit.
- **PR-026, MAJOR, open.** The vendored `/security-review` file ends "Your final reply must contain the markdown report and nothing else", so a reviewer following it writes no `Reviewed:` line and no verdict, and wfctl won't count the report. Its false-positive section also says not to write files. The `reviewing-security` note overrides only the git section, the checklist path, and the commit range.
- **PR-027, MINOR, open.** `_listed_templates()` also filters on `_TEMPLATE_ROW`, so turning it into a tuple puts the new row in the template set, where the Spec Kit notice test fails on it. The new `NOTICES.md` reader is also missing from `_declaration_sources`.
- **PR-028, MINOR, open.** A command substitution inside an argument, such as `gh pr create --title "$(git push)"`, and GNU `env -C dir gh pr create` change the branch or head with no separator before the match. Neither is a recorded limit.
- **PR-029, MINOR, open.** R4 strips an `owner:` prefix from `--head`, so a fork's head is judged against `origin`'s branch of the same name, which fails open. Grouped short flags such as `-sd` have no defined reading, which fails safe.
- **PR-030, MINOR, open.** The `opening-a-change` skill's existing step 5 block runs `gh pr create` after two other commands, which FR-012b refuses, and the plan doesn't name that block for change.

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

- **PR-022, MINOR, open.** Narrowed again. `resolve_branch` and `resolve_agent_dir` now take the timeout. The plan counts five helpers, but `trunk_branch` passes the timeout to `_resolve_declared` and `_bare_head` too, and `_bare_head` calls `is_bare_layout`, which runs `git config --bool core.bare` with no timeout and which no artifact names. The call is reached only when `origin/HEAD` isn't set and no trunk is declared.
- **PR-026, MAJOR, fixed.** Fixed by FR-025, R10 item 7, the plan's `reviewing-security` item 3, and `design.md`'s Key Assumptions. The note now tells the reviewer to write one report with a `Reviewed:` line and a verdict to the path wfctl printed, and says this outranks the vendored file's last line, its "don't write files" line, and its sub-task steps.
- **PR-027, MINOR, fixed.** Fixed by R10 item 6. `_TEMPLATE_ROW` stays a string, a new `_NOTICED_ROWS` tuple is what `_listed()` drops, and the new notice reader joins `_declaration_sources`.
- **PR-028, MINOR, fixed.** Fixed by FR-012b, R4, the guard record, and the guard contract. A command or process substitution in the matched command refuses. A substitution between `gh` and the verb, and `env -C`, are recorded limits.
- **PR-029, MINOR, fixed.** Fixed by FR-012a, R4, and the guard contract. A `--head` owner other than this checkout's refuses, and grouped short flags are read letter by letter.
- **PR-030, MINOR, fixed.** Fixed by the plan's `opening-a-change` item 1.5, which rewrites Step 5 so `wfctl check-body` and `gh pr create` run as separate commands with the body path written out.
- **PR-031, MINOR, open.** New. A `GIT_DIR=` or `GIT_WORK_TREE=` prefix sends `gh pr create` or a bare `gh pr merge` to another checkout's branch, with no separator or substitution for the check to see. It has the same shape as the recorded `env -C` limit, and it is neither refused nor recorded, so SC-001's count doesn't exclude it.

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
- **PR-032, MAJOR, open.** No artifact says whether the review check reads the branch from the payload's `cwd` or from its own process directory, and `_hook.py` reads the payload's on purpose because the two can differ. If the check reads its own, a session in the `main` checkout can `cd` into another worktree by a relative path and run `gh pr create --fill` unjudged. Quickstart sets `cwd` to `$PWD`, so no planned test would catch it.
- **PR-033, MAJOR, open.** The FR-012b rule on `gh` command words has no R6 pattern that triggers it, so the contract's own examples, such as `gh "$X" merge 630`, match nothing and pass. Running the rule on every `gh` in the text instead would refuse ordinary commands like `rg 'gh (pr|api)'`, which FR-016 argues against.
- **PR-034, MINOR, open.** R4 puts the `-R` value under the letters, digits, and hyphens rule, but every `-R` value holds a `/`, and repository names can hold `.` and `_`. Under the likely intended reading, the verb after `-R` is never checked, so `gh pr -R <this repo> 'merge' 630` merges unjudged.
- **PR-035, MINOR, open.** A GraphQL mutation read through a substitution, such as `gh api graphql -f query="$(cat m.graphql)"`, matches no pattern. Pattern 7 covers only `query=@file` and `--input`, and this case is neither refused nor recorded as a limit.
- **PR-036, MINOR, open.** The new rules refuse legitimate `gh api` calls. A `-f merge_method=merge` written before the path reads as an environment prefix, `gh`'s `:owner/:repo` placeholder compares as another repository, and pattern 6 refuses every variable-path write, including review-comment replies.
- **PR-037, MINOR, open.** Wrappers such as `uv run --directory ../630-x gh pr create --fill` and `direnv exec ../630-x gh …` change the directory `gh` runs in without a separator, prefix, or `env`. This is the same shape the walkthrough turned from a limit into a refusal.
- **PR-038, MINOR, open.** The trunk-checkout rule rests on the branch name, and a worktree can switch to the trunk branch, so Ownership item 6 reads as enforced when it is a convention. Separately, R4 doesn't repeat R3's `origin/` strip, so a plain comparison against `trunk_branch` never matches.
- **PR-039, MINOR, open.** The artifacts don't say which refusals carry FR-015's "person's own terminal" sentence. Contract row 150's timeout message lacks it while the error-refusal block's timeout example has it, and `opening-a-change` item 1.6 tells an error refusal apart by this text.
- **PR-040, MINOR, open.** Two spec passages describe the earlier behavior. User Story 3 says the agent can't loop forever on fixes, which nothing enforces until #626, and a Validation Strategy line judges another branch's PR from anywhere, while FR-012a allows it only from the trunk checkout.

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
- **PR-041, MAJOR, open.** New. `gh -R <repo> pr merge 630` and `gh pr -R<repo> merge 630` merge a pull request with no pattern matching, since pattern 1 needs `gh\s+pr` and a space or `=` after `-R`. `gh -R cli/cli pr merge --help` prints the `gh pr merge` help, which confirms `gh` parses `-R` before `pr`.
- **PR-035, MINOR, open.** A GraphQL mutation read through a substitution, such as `gh api graphql -f query="$(cat m.graphql)"`, still matches no pattern.
- **PR-036, MINOR, open.** Three legitimate calls still refuse: a `-f merge_method=merge` before the path, the `:owner/:repo` placeholder, and pattern 6 over unrelated writes such as review-comment replies.
- **PR-037, MINOR, open.** `uv run --directory ../630-x gh pr create` and `direnv exec ../630-x gh …` are neither refused nor recorded. The `cwd` rule doesn't reach them, since the session's directory hasn't moved.
- **PR-038, MINOR, open.** The trunk-checkout rule keys on a branch name, so Ownership item 6 reads as enforced when it is a convention. R4 still doesn't say it compares against `main` rather than `origin/main`.
- **PR-039, MINOR, open.** A timed-out lookup still has two different messages in the contract, and the unreadable-record and no-trunk rows don't point at the error refusal block.
- **PR-040, MINOR, open.** User Story 3 still says the agent can't loop forever on fixes, and the Validation Strategy line on another branch's PR doesn't name the trunk checkout.
- **PR-042, MINOR, open.** New. A quoted or variable `gh`, such as `"gh" pr merge 630` or `$GH pr merge 630`, matches no pattern, since patterns 1 and 8 both start at `\bgh\s+`.
- **PR-043, MINOR, open.** New. Pattern 8 refuses more ordinary commands than R6 says, such as `grep "gh pr create\|gh pr merge"`, `rg 'gh pr.*merge'`, and a commit message that quotes `gh "$X" merge 630`. R6 names only the glob cost and no workaround.
- **PR-044, MINOR, open.** New. A `gh` call made inside a script, such as `.github/scripts/release.py`'s `gh pr create`, is neither refused nor recorded in the spec's Edge Cases, and the artifacts don't say whether the release PR skips the review groups.
- **PR-045, MINOR, open.** New. R4 keeps `resolve_branch` honoring `WFCTL_BRANCH`, which names the branch without reading `cwd`, while FR-012c says the branch comes from `cwd`.
