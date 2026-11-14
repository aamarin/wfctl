# Plan review scan for #739

## Review 2026-11-09T21:15Z

- Verdict: satisfied
- Reviewed: plan.md 1c39726a6cd924177125cbf3ab5d6f7b2ad3c04f, spec.md b5490d0b17bcbcab95b862271bdffdb5050100f9, .specify/memory/constitution.md absent, design.md 35eeec90e35269d36caf2dd5f9a824996bc08dbb, research.md 99fcc34c20e1cb30a9e3e8371f8da8b8231e9ce1, data-model.md e0e64fe48619f7d2bebc22f5ca5558ac736d4341, contracts/cli.md d0d9ccc7663a8f918ed6d1ab6f0d8a488f2ad192, quickstart.md 9a47e853f4af6f2d157e8189479ff1276c28d39d, checklists/requirements.md d5925f3b1a84965cb1d73f8b712f6b1b75092da0, docs/architecture/required-views-are-wfctls.md dd3a1e869a9c5da1f2bf133d23dfeaa55c1d6bb0, docs/architecture/the-author-declares-the-diagram-kind.md 4da32858fd4cd85b6b3d8af161334bc035c01800, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/branch-contexts-select-records.md 06dd5c4d9c75c78add625ea1a7ec738b5b37c17c, docs/architecture/domain/wfctl.md 406e93843e422bdd70292396c90c315de0e09ed9
- Review type: full (no earlier review)
- Open: BLOCKER 0 · MAJOR 2 · MINOR 9 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/739-architecture-views/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-001, PR-007, PR-010) |
| Requirements and traceability | Outstanding (PR-001, PR-006, PR-010) |
| Architecture and boundaries | Outstanding (PR-002, PR-011) |
| Adversarial implementation and verification | Outstanding (PR-003, PR-004, PR-005, PR-008, PR-009) |
| Security and reliability | Deferred (the feature reads local markdown and adds acceptance refusals, and crosses no trust boundary) |

### Findings

- **PR-001, MAJOR, open.** `spec.md §FR-013` asks for the refusal agreed in `design.md`, a `✗ <slug> declares … but doesn't draw one.` line with a separate `Fix:` line. `contracts/cli.md §wfctl arch accept` keeps the existing `cannot be accepted yet` header with indented `problem: fix` lines. Stands because the plan gives no reason for the difference, and its tests pin the contract exactly.
- **PR-003, MAJOR, open.** `research.md §R-005` and `data-model.md §Drawing per kind` take the first fenced block under a `### <kind>` heading, but don't say where that subsection ends. If it runs to the next `##`, a `### data-flow` heading with no fence picks up the fence under `### sequence`. Stands because the plan also leaves open a fence directly under `## Boundary`, heading case, and whether the existing `no drawing` blocker still prints.
- **PR-002, MINOR, open.** `the-author-declares-the-diagram-kind.md §Consequences` says `Record.diagram` is a list, and `research.md §R-004` keeps it a string beside a new `Record.kinds`. `required-views-are-wfctls.md §Consequences` checks the view list against the domain page template, and `§FR-004` checks it against the view templates. Stands because neither record has been updated to match.
- **PR-004, MINOR, open.** `research.md §R-003` says the view filter matches the record filter, but the record filter also narrows on the `Outside parties` line. Stands because the plan also doesn't say that `contexts(arch)` keeps the `Contexts` line's order, which contract rule 1 needs.
- **PR-005, MINOR, open.** The plan's Validation Strategy saves every on-disk record's acceptance result in a test. Stands because a test reading the live records folder fails the first time a record is added or edited after merge, and the plan doesn't say whether it uses a fixture copy.
- **PR-006, MINOR, open.** `start-session/SKILL.md` step 2 says the last lines of `wfctl arch context` count the records left out, and the new Views block prints after them. Stands because the plan doesn't update the skill, and User Story 2 depends on the agent reading the views.
- **PR-007, MINOR, open.** `spec.md §FR-015` says `doctor` warns about every FR-012 problem on a proposed record, while `research.md §R-006` keeps an unknown kind an error on every status. Stands because the research explains the choice but the spec wasn't updated.
- **PR-008, MINOR, open.** `research.md §R-009` prints view paths relative to the repository root. Stands because `arch_root` can sit outside the working tree and the plan doesn't say what prints then.
- **PR-009, MINOR, open.** `quickstart.md §3` runs `wfctl arch accept <slug> --agreed "test" --dry-run`. Stands because the same line without the flag accepts the record for real, and wfctl's own form puts `--dry-run` before the slug.
- **PR-010, MINOR, open.** `spec.md §SC-005` says a filled domain page has one table, and `§FR-016` keeps three other tables in the template. Stands because the two requirements disagree.
- **PR-011, MINOR, open.** The plan's Constitution Check keeps the stability layout rule as prose because no check ships today. Stands because `a-rule-is-expressed-as-a-check` asks the question of the rule rather than the tooling; deferring the check to #743 is sound, but the stated reason isn't.

## Review 2026-11-10T05:38Z

- Verdict: satisfied
- Reviewed: plan.md 32de5374d2cdc6288e6c5462adfcf13fd9872d5d, spec.md b6fc6989255c515bdfeb0f77a4a98d2aefff5a6f, .specify/memory/constitution.md absent, design.md 9794ff4227fc3be5e233071d203061432d050a19, research.md f415d9d2343b6ec249f6c5e64d2000bbc933794f, data-model.md 010bfc8ab592796c7a4ae93d42e61435137cf2f4, contracts/cli.md e4155e9a01291f58e41fb8a25be9e6a8aae6ea60, quickstart.md 00360fe47d9576f2ef304b7d35408a903631d06f, checklists/requirements.md d5925f3b1a84965cb1d73f8b712f6b1b75092da0, docs/architecture/required-views-are-wfctls.md 4b39a7b1988bba304dc97b460a90a060cf093afb, docs/architecture/the-author-declares-the-diagram-kind.md 0c32077ce31aca87ee00f777f0bc85728e5f413d, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/branch-contexts-select-records.md 06dd5c4d9c75c78add625ea1a7ec738b5b37c17c, docs/architecture/domain/wfctl.md 406e93843e422bdd70292396c90c315de0e09ed9, plan-review.plan.md 1c39726a6cd924177125cbf3ab5d6f7b2ad3c04f (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 2 · Fixed since the earlier review: 11
- Detail: /Users/andremarin/Development/wfctl-specs/739-architecture-views/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-012, PR-014; PR-001, PR-007, PR-010 fixed) |
| Requirements and traceability | Outstanding (PR-013; PR-001, PR-006, PR-010 fixed) |
| Architecture and boundaries | Resolved (PR-002, PR-011 fixed) |
| Adversarial implementation and verification | Outstanding (PR-012; PR-003, PR-004, PR-005, PR-008, PR-009 fixed) |
| Security and reliability | Deferred (the feature reads local markdown and git history, and its new `git log` and `git rev-list` calls are read-only and cross no trust boundary) |

### Findings

- **PR-012, MAJOR, open.** `research.md §R-010` and contract rules 3, 5, and 6 don't say what prints when the stale check's `git` call fails, which happens when the architecture root is outside the working tree. Stands because an implementer could read the empty output as "no commit yet" and print the view as current forever, so the plan needs a third `unchecked` reason and a test for that case.
- **PR-013, MINOR, open.** `quickstart.md §2` expects plain paths, but any commit to `wfctl/` after the views are drawn makes the container view print as `stale:`. Stands because the quickstart also doesn't check the `covers` line or the arrow labels that FR-003b and FR-003c require.
- **PR-014, MINOR, open.** The `vendor-upstream-skills` gate and the Structure Decision still count three edited skills, and the plan now edits `start-session` as well. Stands because the count is wrong, though the gate's conclusion holds since `start-session` isn't a derived skill.
- **PR-001, MAJOR, fixed.** `spec.md §FR-013` now spells out the `✗ <slug> <problem>.` line with a `Fix:` line, the contract matches it, and `research.md §R-013` explains why the old blockers keep their block.
- **PR-003, MAJOR, fixed.** `research.md §R-005` and `data-model.md` now end a kind's drawing at the next `###` or `##` heading, and define heading case, a fence above the first heading, and a multi-kind record with no fence, each with a named test.
- **PR-002, MINOR, fixed.** Both records' Consequences sections now keep `Record.diagram` verbatim beside `Record.kinds`, and compare the view list against the view templates.
- **PR-004, MINOR, fixed.** `research.md §R-003` now says the views filter differs from the records filter on outside parties, and `§R-002` says `contexts(arch)` returns an ordered tuple with repeats dropped.
- **PR-005, MINOR, fixed.** The acceptance test now compares frozen copies under `tests/fixtures/one-kind-records/`, not the live records folder.
- **PR-006, MINOR, fixed.** The plan now updates `start-session/SKILL.md` step 2 and gives the sentence to add.
- **PR-007, MINOR, fixed.** `spec.md §FR-015` now keeps an unknown kind an error on every status.
- **PR-008, MINOR, fixed.** View paths print through `_paths.arch_location`, with a test for an architecture root outside the working tree.
- **PR-009, MINOR, fixed.** The quickstart now runs `wfctl arch accept --dry-run -- <slug>`.
- **PR-010, MINOR, fixed.** `spec.md §FR-016` now names all nine tables in the domain page template.
- **PR-011, MINOR, fixed.** The gate now says a broken layout rule or arrow label is visible in the view, so it's a gap that #743 closes.

## Review 2026-11-10T14:37Z

- Verdict: satisfied
- Reviewed: plan.md c35ab84d872a98701795267d0a00a1f91e5770a5, spec.md d01e78918246d887167bbd0a9b88586f100a6527, .specify/memory/constitution.md absent, design.md 9794ff4227fc3be5e233071d203061432d050a19, research.md 3227bc91fbd9b78d541598312ec7d3a23be26541, data-model.md 5a7f740a30d66172dd90aa5b0878c8107724c584, contracts/cli.md 6f8f915fe65be22ff509cf47bd65699e5e6fe59d, quickstart.md 0fa327cc5522471467e79e2a7bc9aaa73f600bb3, checklists/requirements.md d5925f3b1a84965cb1d73f8b712f6b1b75092da0, docs/architecture/required-views-are-wfctls.md 4b39a7b1988bba304dc97b460a90a060cf093afb, docs/architecture/the-author-declares-the-diagram-kind.md 0c32077ce31aca87ee00f777f0bc85728e5f413d, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/branch-contexts-select-records.md 06dd5c4d9c75c78add625ea1a7ec738b5b37c17c, docs/architecture/domain/wfctl.md 406e93843e422bdd70292396c90c315de0e09ed9, plan-review.plan.md 32de5374d2cdc6288e6c5462adfcf13fd9872d5d (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 1 · Fixed since the earlier review: 3
- Detail: /Users/andremarin/Development/wfctl-specs/739-architecture-views/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Resolved (PR-001, PR-007, PR-010, PR-012, PR-014 fixed) |
| Requirements and traceability | Resolved (PR-001, PR-006, PR-010, PR-013 fixed) |
| Architecture and boundaries | Resolved (PR-002, PR-011 fixed) |
| Adversarial implementation and verification | Outstanding (PR-015; PR-003, PR-004, PR-005, PR-008, PR-009, PR-012 fixed) |
| Security and reliability | Deferred (the feature reads local markdown and git history, and its `git` calls take paths after `--`, so no trust boundary is touched) |

### Findings

- **PR-015, MINOR, open.** `data-model.md §Required view` lists three `unchecked` reasons but doesn't say which one prints when two apply. `research.md §R-010` and the plan's out-of-tree test assume the history reason always wins, while a view with no `covers` line would likely print `(no covers line)`, since that check needs no `git` call. Stands because the order is unstated.
- **PR-012, MAJOR, fixed.** `spec.md §FR-006a` and its edge case, `research.md §R-010`, `data-model.md` freshness and rule 5, contract rules 6 and 7, and the plan's out-of-tree test now agree that a failed `git` call prints `unchecked: <path> (not in this repository's history)` and keeps exit 0. The reviewer checked that `git log` on an out-of-repo path exits 128, so rule 6's empty-output case isn't reached there.
- **PR-013, MINOR, fixed.** `quickstart.md §2` now explains the `stale:` mark and how to clear it, and `§1` checks the `covers` line and the arrow labels.
- **PR-014, MINOR, fixed.** The `vendor-upstream-skills` gate now lists four skills, including `start-session`, and the Structure Decision says four.
- **PR-001 to PR-011, fixed.** Each stays fixed, and this round's edits didn't change the text that fixed them.
