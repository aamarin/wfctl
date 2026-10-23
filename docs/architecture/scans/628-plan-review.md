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
