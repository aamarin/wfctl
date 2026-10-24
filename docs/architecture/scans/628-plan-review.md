# Plan review scan for #628

## Review 2026-10-23T10:24Z

- Verdict: satisfied
- Reviewed: plan.md 9120efc407a0bb72ed24472d1d883d461d080f9a, spec.md c4afed155933ade72e1dcb3992458d51da4cf243, .specify/memory/constitution.md absent, design.md 70580e199e408d7b34c677a9cdcedb444dcad972, docs/architecture/design/628-design-passes-own-skill.md 732b745500899f1cd5c26440589f31f33514e948, docs/architecture/design/628-early-answer-in-commit-trailer.md 9da0c49fbce7ca5ac254b60ecfda987181d3bfb8, docs/architecture/design/628-spec-answer-in-pr-body.md 5a06bf0e65368c1b69e511bba2dcd737440d507c, docs/architecture/every-change-answers-spec-question.md 16db0fbc8df3b8197ab3ccfef26548a3b555b9e9, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/required-sections-are-wfctls.md d9e545e997c1a990b66e1790e9698b8e4297ca48, docs/architecture/scans/628-clarify.md 15d82f295d378b3555e00371d1f9fd0639f28a8d, research.md 5271329ec38854c756ad6489d146d5f84512e498, data-model.md 9968a16a136006fa87c38fededc2c945f3871a33, quickstart.md 7519815aef0ff052be5f4b3ce038d64f8c5f5b5a, contracts/cli.md 4a33f364dd16e4ee5b72efcad4e9c4070bf86c53, contracts/skills.md e9e7f6ed2a1637eabd509de360d4fe64c2ec467b, checklists/requirements.md ecaadae4e34c4b62523600d25eca79e912b3bc96
- Review type: full (no earlier report and no plan copy)
- Open: BLOCKER 0 · MAJOR 5 · MINOR 7 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/628-design-passes-every-change/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-006) |
| Requirements and traceability | Outstanding (PR-002, PR-008, PR-009, PR-010) |
| Architecture and boundaries | Outstanding (PR-004, PR-005, PR-011, PR-012) |
| Adversarial implementation and verification | Outstanding (PR-001, PR-003, PR-007) |
| Security and reliability | Deferred (the feature reads local files and writes none, and adds no authorization, secret, destructive operation, concurrent state, or migration) |

### Findings

- **PR-001, MAJOR, open.** The repointed "Not for" lines create a routing loop. `design-passes` sends a fix that moves a boundary to `architecture-design`, and `architecture-design`'s new "Not for" line sends bug fixes back to `design-passes`. Stands because no line in the plan breaks the loop.
- **PR-002, MAJOR, open.** SC-005 has no verification route. Research R1 moves the instruction into the PR template's comment under the new heading, and no artifact gives that comment's text. Stands because R1 assumes every section has a comment, and this repo's template doesn't.
- **PR-003, MAJOR, open.** The planned cross-reference test only checks lines that say "straight to implementation", and the planned edits remove that phrase. Stands because the test passes even when no route line points to `design-passes`, which the spec requires it to catch.
- **PR-004, MAJOR, open.** Git drops the `Needs-spec:` trailer when it sits in its own paragraph before the Co-Authored-By block, or when its reason wraps onto an unindented second line. Both were tested in a scratch repo. Stands because nothing checks the trailer, so the loss goes unreported.
- **PR-005, MAJOR, open.** The Constitution Check says the trailer and test-first "leave nothing a check can trust", and both show in branch history. Stands because the plan doesn't weigh a report-only check against `a-rule-is-expressed-as-a-check`. It is MAJOR rather than BLOCKER because the core rule is already checked in the PR body.
- **PR-006, MINOR, open.** `design.md` still shows the old `✗` strings, a clean run printing nothing, and the key name as an open question. Stands because nobody has edited `design.md` since research R1 - R3 changed them.
- **PR-007, MINOR, open.** The plan doesn't say whether HTML comments are stripped before or after headings are found. Stands because a section commented out as a block reads as answered under one order and missing under the other.
- **PR-008, MINOR, open.** `opening-a-change` Step 4 allows "None" as well as "N/A", and research R5 catches only N/A. Stands because a bare "None" passes the check.
- **PR-009, MINOR, open.** On the yes path, the plan doesn't say who writes the trailer. Stands because `design-passes` stops before any commit, while Key Entities says the answer is written twice.
- **PR-010, MINOR, open.** The spec's US4 test names `docs/architecture/domain/`, the contract names `<arch-root>/domain/`, and neither covers a repo with no domain model. Stands because the two paths still disagree.
- **PR-011, MINOR, open.** The `check_body_cmd` docstring and `opening-a-change` Step 5 both say `check-body` checks one thing. Stands because the plan schedules neither edit.
- **PR-012, MINOR, open.** "Required sections" is wfctl-owned in `required-sections-are-wfctls` and repo-owned here. Stands because the plan doesn't cite that record or say why the owner differs.

## Review 2026-10-23T18:45Z

- Verdict: satisfied
- Reviewed: plan.md ca8c5cb89695e720737e3e2bef5df2f8507696b3, spec.md 22dcd56e2f46e2e70ccc1f6717ae05ee7cf0c620, .specify/memory/constitution.md absent, design.md d41fe5c87e60026e8f2db51caa0d1dcf3db43e18, docs/architecture/design/628-design-passes-own-skill.md fa8c79b243f230b7ab9bfc0f0bbd03804a6b71ce, docs/architecture/design/628-early-answer-in-commit-trailer.md 068548995e0554924008460ed2153ac702637f5f, docs/architecture/design/628-spec-answer-in-pr-body.md a1c9322052627ddbb05a9340946ef5531e94d7b0, docs/architecture/every-change-answers-spec-question.md f00e30683ff076ab93cf49425e23a9ef3c000dd4, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/required-sections-are-wfctls.md d9e545e997c1a990b66e1790e9698b8e4297ca48, docs/architecture/scans/628-clarify.md 15d82f295d378b3555e00371d1f9fd0639f28a8d, research.md f2f8c277931c2d2d041d83e345f734e49f71ebba, data-model.md 3793d677e770ef5aed343b1121544c305af3a6eb, quickstart.md 03b7e874d36f957bfc64b2651e5e592055e53bc8, contracts/cli.md f5c9a922db0f8007d0be3967edf88e6c9b7007dc, contracts/skills.md 0fd792d1050e5430f8563adc5953113485b7a91e, checklists/requirements.md ecaadae4e34c4b62523600d25eca79e912b3bc96, plan-review.plan.md 9120efc407a0bb72ed24472d1d883d461d080f9a (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 2 · MINOR 9 · Fixed since the earlier review: 7
- Detail: /Users/andremarin/Development/wfctl-specs/628-design-passes-every-change/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-007, PR-010, PR-015) |
| Requirements and traceability | Outstanding (PR-010, PR-015, PR-016) |
| Architecture and boundaries | Outstanding (PR-005, PR-011, PR-012, PR-014, PR-016, PR-018) |
| Adversarial implementation and verification | Outstanding (PR-007, PR-013, PR-014, PR-017) |
| Security and reliability | Deferred (the feature reads local files and writes none, and adds no authorization, secret, destructive operation, concurrent state, migration, or history operation) |

### Findings

- **PR-013, MAJOR, open.** The `design-levels` "Not for" line still excludes changes by kind, and the contract adds a pointer to `design-passes` to it. A bug fix that reaches brainstorm, whether a handoff routed it there or `design-passes` answered yes, is sent back to `design-passes`. Stands because the contract keys that line on kind, not on whether the change needs a spec.
- **PR-014, MAJOR, open.** `architecture-decisions` still says "Not for: bug fixes", and `architecture-design` hands every proposed boundary to it. Stands because the plan rekeys `model-the-domain` for this reason and misses the same dead end one hop further on.
- **PR-005, MINOR, open.** Downgraded from MAJOR, since the trailer half no longer applies. The Constitution Check still says test-first "leaves nothing a check can trust", and the commit order is visible in history. Stands because the gate line doesn't give the real reason, that a check would have to judge whether a test applies.
- **PR-007, MINOR, open.** The plan still doesn't say whether HTML comments are stripped before or after headings are found. Stands because no artifact changed it.
- **PR-010, MINOR, open.** The spec names `docs/architecture/domain/`, the contract names `<arch-root>/domain/`, and neither covers a repo with no domain model. Stands because no artifact changed it.
- **PR-011, MINOR, open.** The `check_body_cmd` docstring update isn't scheduled, and no follow-up for #622 names `opening-a-change` Step 5. Stands because no artifact changed it.
- **PR-012, MINOR, open.** "Required sections" has two owners, and the plan doesn't cite `required-sections-are-wfctls`. Stands because no artifact changed it.
- **PR-015, MINOR, open.** `628-design-passes-own-skill.md` still names the grep in its verification and says no test catches a place that stops pointing, while `design.md` names the section test. Stands because the record wasn't updated with `design.md`.
- **PR-016, MINOR, open.** The contract rewrites only the opening and end of `worktree-handoff` item 3, leaving "design-levels owns where the line falls" and "draws a boundary … goes through the pipeline", which contradict the new route. Stands because the middle of the item isn't in the contract.
- **PR-017, MINOR, open.** The new `architecture-design` paragraph names `design-passes` twice, so the quickstart step that deletes one mention leaves the section test passing. Stands because the mutation step doesn't say which mention, or to delete both.
- **PR-018, MINOR, open.** `architecture-design` is also reached from `model-the-domain`, which has no level 3, so the contract's "called from two places" is incomplete. Stands because the contract names only two callers.
- **PR-001, MAJOR, fixed.** Fixed by `contracts/skills.md §Routing between the skills`, which keys the `architecture-design` and `model-the-domain` "Not for" lines on whether a boundary moves, and sends a skipped change to level 3 of the caller.
- **PR-002, MAJOR, fixed.** Fixed by `contracts/cli.md §The template comment the messages point at`, which gives the comment's text, and `quickstart.md §4`, which observes SC-005 with an agent.
- **PR-003, MAJOR, fixed.** Fixed by `plan.md §The cross-reference tests`, which reads four sections between markers, fails on a missing marker, and bans the old phrase case- and wrap-insensitively.
- **PR-004, MAJOR, fixed.** Fixed by `spec.md §FR-005`, which drops the trailer and records the answer only in the PR section.
- **PR-006, MINOR, fixed.** Fixed by `design.md`, which now shows the current strings and key.
- **PR-008, MINOR, fixed.** Fixed by the template comment in `contracts/cli.md`, which says N/A and None aren't answers, and accepts that `check-body` reports only N/A.
- **PR-009, MINOR, fixed.** Fixed by the trailer's removal, so the yes path writes nothing early, and Key Entities matches.

## Review 2026-10-23T20:54Z

- Verdict: satisfied
- Reviewed: plan.md d0740bdb4f336f0e3b6a0903bf03da1e8cd3d333, spec.md 45857b5e8860f32b30c89f06ca35601ac9ca3bba, .specify/memory/constitution.md absent, design.md d41fe5c87e60026e8f2db51caa0d1dcf3db43e18, docs/architecture/design/628-design-passes-own-skill.md fa8c79b243f230b7ab9bfc0f0bbd03804a6b71ce, docs/architecture/design/628-early-answer-in-commit-trailer.md 068548995e0554924008460ed2153ac702637f5f, docs/architecture/design/628-spec-answer-in-pr-body.md 010bc12a6c3450f2c3df65ad6054e5ad55ce68ae, docs/architecture/every-change-answers-spec-question.md b6eaf518b57c98aa47b0a796786528937379d931, docs/architecture/a-rule-is-expressed-as-a-check.md 81e9a7d67301935f73a6e3b97c9b06284310879f, docs/architecture/required-sections-are-wfctls.md d9e545e997c1a990b66e1790e9698b8e4297ca48, docs/architecture/scans/628-clarify.md 15d82f295d378b3555e00371d1f9fd0639f28a8d, research.md 231a518874733dcd61700c672a68367b59df6374, data-model.md 601f44991139d0bb70b6f06e0b00aa0938a7f7b1, quickstart.md 48b694f6a7f77ae4b863073ee2ffe8cfb86ed241, contracts/cli.md 91236b8f9bab39707a4ac485469a05389c7c2ef6, contracts/skills.md 3d5fcb7369e5986761ed822d797127e352c09f2d, checklists/requirements.md ecaadae4e34c4b62523600d25eca79e912b3bc96, plan-review.plan.md ca8c5cb89695e720737e3e2bef5df2f8507696b3 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 17 · Fixed since the earlier review: 2
- Detail: /Users/andremarin/Development/wfctl-specs/628-design-passes-every-change/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-020, PR-021, PR-026) |
| Requirements and traceability | Outstanding (PR-010, PR-015, PR-016, PR-021, PR-023, PR-025, PR-026) |
| Architecture and boundaries | Outstanding (PR-005, PR-011, PR-012, PR-018, PR-022, PR-023, PR-026; PR-013 and PR-014 fixed) |
| Adversarial implementation and verification | Outstanding (PR-007, PR-017, PR-019, PR-020, PR-024, PR-025) |
| Security and reliability | Deferred (no trust boundary is touched: the feature reads local files and writes none, and the panel bullet is instruction text) |

### Findings

- **PR-013, MAJOR, fixed.** Fixed by the `design-levels/SKILL.md:22-24` row in `contracts/skills.md`, which keys the line on new state, behavior, or a moved boundary and keeps a change `design-passes` answered yes for (spec FR-004, User Story 1 scenario 7).
- **PR-014, MAJOR, fixed.** Fixed by the `architecture-decisions/SKILL.md:29-31` row in `contracts/skills.md`, which keys its "Not for" line on boundary movement.
- **PR-005, MINOR, open.** The test-first gate line gives a reason `a-rule-is-expressed-as-a-check` doesn't recognise. Stands because the plan text is unchanged.
- **PR-007, MINOR, open.** R4 and R5 don't fix whether sections are found before or after HTML comments are stripped. Stands because neither says.
- **PR-010, MINOR, open.** The spec and the contract name the domain model's folder differently, and neither says what level 2 does without one. Stands because both are unchanged.
- **PR-011, MINOR, open.** The `check_body_cmd` docstring and `opening-a-change` Step 5 still say `check-body` checks only drawings. Stands because the plan updates neither.
- **PR-012, MINOR, open.** "Required sections" now names two different lists, and the plan doesn't cite `required-sections-are-wfctls` to tell them apart. Stands because nothing was added.
- **PR-015, MINOR, open.** `628-design-passes-own-skill.md` still describes the old grep as the verification. Stands because the record wasn't edited.
- **PR-016, MINOR, open.** The `worktree-handoff` row leaves two sentences in the route item that contradict the new route. Stands because the row is unchanged.
- **PR-017, MINOR, open.** The quickstart's mutation deletes one of two occurrences of the path, so the section test can't fail. Stands because §3 is unchanged.
- **PR-018, MINOR, open.** The routing section's lists of callers are incomplete. Stands because it omits `architecture-design` to `model-the-domain` and `model-the-domain` to `architecture-decisions`.
- **PR-019, MINOR, open.** The `design-levels` sentence that keeps a "yes" change relies on the conversation remembering who sent it. Stands because nothing records it, so a restart costs one extra hop.
- **PR-020, MINOR, open.** The fifth dispatch bullet, used verbatim, fails `test_the_dispatch_list_requires_the_coverage_the_clean_row_reproduces`, and the Scale line still says four skills. Stands because the bold phrase wraps onto a second line, and the reviewer confirmed the count of 4 against "five" on a scratch copy.
- **PR-021, MINOR, open.** `design.md` and research R1's message list predate the no-reason message and the panel bullet. Stands because only the committed record was updated.
- **PR-022, MINOR, open.** The #622 constraint protects only `opening-a-change`, and the plan now edits `fanning-out-code-review`, which #622 is also redesigning. Stands because the plan doesn't address the overlap.
- **PR-023, MINOR, open.** The no-reason rule applies to every listed section, where a bare "No." can be a complete answer, such as "Breaking changes?". Stands because a repo can't opt a section out.
- **PR-024, MINOR, open.** Emphasis isn't stripped before matching, so "**No.**" and "**N/A**" pass. Stands because R5's patterns match the bare text only.
- **PR-025, MINOR, open.** The spec and the record say an agent other than the author judges a "No", but no reviewer sees the answer, the author disposes of the finding, and in an unattended run nobody reads the table. Stands because the wording overstates what the panel does.
- **PR-026, MINOR, open.** The contract keeps the `AGENTS.md:391` paragraph "the same", and that paragraph quotes the kind-keyed `design-levels` exclusion the plan rewrites. Stands because the row is unchanged.
