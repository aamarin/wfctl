# Plan review scan for #724

## Review 2026-11-06T20:57Z

- Verdict: satisfied
- Reviewed: plan.md 2164759ac53cc4dbbafa48e304ff3a7c48b8435b, spec.md 040a074d1b14e88c1e88b6c0d2685a24aa3c5d3f, .specify/memory/constitution.md absent, design.md f2a7241ab5d56659020b8ae2623f9c92e7e515f6, docs/architecture/design/724-cross-layer-checks-in-rubric.md 350e1f0c82b5097ad95e53a8305d40c159815fe9, docs/architecture/vendor-upstream-skills.md 994c2021e811b43cdbc944453484e6873a2cdad6, research.md 92725d018019c3d32f57eb315b65d2ac745c03fe, data-model.md 92c3ef5f5b6598d8725615fb72c317bdbd503f1d, quickstart.md b0f5d9459c7bbb801d4bd2c65d8067acef65907b, contracts/review-report.md d22de129f40f57dec05ae53258a7805190b2b6ae, exceptions/design-method/boundary.md 0f8d7a56e6c37a17b9644832be7e215f419bb2ae, checklists/requirements.md f494fe4b228253869de069aa0319bfa6c135fc4a
- Review type: full (no earlier report)
- Open: BLOCKER 0 · MAJOR 1 · MINOR 7 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/724-cross-layer-review/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Outstanding (PR-001, PR-002) |
| Architecture and boundaries | Outstanding (PR-004) |
| Adversarial implementation and verification | Outstanding (PR-001, PR-003, PR-005, PR-006, PR-007, PR-008) |
| Security and reliability | Deferred (no trust boundary is touched; the change is prose in review skills and one count in one test) |

### Findings

- **PR-001, MAJOR, open.** `spec.md §FR-007` says the sibling pass reports code that brings back a pattern an earlier commit on the branch fixed. In panel rounds two and three, the reviewer gets only the commits since the last completed run, and `plan.md §Technical Context` rules out widening that list. The finding stands because the plan doesn't say where pass 8 finds fixes from earlier rounds, or whether FR-007 is limited to the commits the run covers.
- **PR-002, MINOR, open.** `contracts/review-report.md` has a trail row that names wfctl's own `wfctl.json` and a `--rounds` flag that doesn't exist. The finding stands because the row isn't one of the two neutral examples in `research.md §R5`, and copying it into the rubric would break `spec.md §FR-013`.
- **PR-003, MINOR, open.** The stale-count search in `quickstart.md` step 3 misses the red-flag line "other five passes" and the lens-name lists in both descriptions. The finding stands because the search would report clean on the drift FR-012 is meant to remove.
- **PR-004, MINOR, open.** `research.md §R3` leaves it to tasks whether `requesting-code-review` is upstream-derived. The `vendor-upstream-skills` record already lists that skill as derived, so the plan's Constitution Check is ticked on a question the record answers.
- **PR-005, MINOR, open.** `quickstart.md` doesn't name the SC-002 baseline, which is the trace reviewer's earlier report. Step 5 names no docs-only commit and no brief for SC-003. The finding stands because two people running these steps could compare against different things.
- **PR-006, MINOR, open.** `spec.md §SC-004` and `§FR-014` have no verification step. The finding stands because nothing checks that the review groups, reviewer counts, and round cap stay unchanged.
- **PR-007, MINOR, open.** `spec.md §FR-004` reports only contradictions between adjacent layers, but a layer can read `unknown`. The finding stands because the spec doesn't say whether a reviewer compares across an unknown layer.
- **PR-008, MINOR, open.** The design record treats one missed bug in the SC-001 run as proof the design fails, and `quickstart.md` step 4 runs that check once. The finding stands because the plan doesn't say what follows a miss.

## Review 2026-11-06T21:40Z

- Verdict: satisfied
- Reviewed: plan.md 571c94a9ed021ed8c77aee30e9f8d5b5338e4827, spec.md 040a074d1b14e88c1e88b6c0d2685a24aa3c5d3f, .specify/memory/constitution.md absent, design.md f2a7241ab5d56659020b8ae2623f9c92e7e515f6, docs/architecture/design/724-cross-layer-checks-in-rubric.md 350e1f0c82b5097ad95e53a8305d40c159815fe9, docs/architecture/vendor-upstream-skills.md 994c2021e811b43cdbc944453484e6873a2cdad6, research.md 92725d018019c3d32f57eb315b65d2ac745c03fe, data-model.md 92c3ef5f5b6598d8725615fb72c317bdbd503f1d, quickstart.md b0f5d9459c7bbb801d4bd2c65d8067acef65907b, contracts/review-report.md d22de129f40f57dec05ae53258a7805190b2b6ae, exceptions/design-method/boundary.md 0f8d7a56e6c37a17b9644832be7e215f419bb2ae, checklists/requirements.md f494fe4b228253869de069aa0319bfa6c135fc4a, plan-review.plan.md 2164759ac53cc4dbbafa48e304ff3a7c48b8435b (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 6 · Fixed since the earlier review: 1
- Detail: /Users/andremarin/Development/wfctl-specs/724-cross-layer-review/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Outstanding (PR-001, PR-002) |
| Architecture and boundaries | Resolved (PR-004 fixed) |
| Adversarial implementation and verification | Outstanding (PR-001, PR-003, PR-005, PR-006, PR-007, PR-008) |
| Security and reliability | Deferred (no trust boundary is touched; the change is prose in review skills and one count in one test) |

### Findings

- **PR-004, MINOR, fixed.** Fixed by `plan.md §Constitution Check`, which now says `requesting-code-review` is derived from obra/superpowers, and `plan.md §Source Code`, which drops the count from "the six-pass rubric". `research.md §R3` still says tasks checks the attribution line, but its own alternative allows what the plan chose.
- **PR-001, MAJOR, open.** Unchanged since the earlier review. The plan doesn't say where pass 8 finds fixes from earlier panel rounds, since reviewers in later rounds see only the commits since the last run. The gap is tracked in #729.
- **PR-002, PR-003, PR-005, PR-006, PR-007, PR-008, MINOR, open.** Unchanged since the earlier review, because none of their evidence in `plan.md`, `quickstart.md`, `research.md` or `contracts/review-report.md` changed.
