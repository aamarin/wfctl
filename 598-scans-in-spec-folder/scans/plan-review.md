# Plan review scan for #598

## Review 2026-11-11T15:17Z

- Verdict: satisfied
- Reviewed: plan.md 8f51297eaf30e2557b7b126cfec4519dfa4dffe0, spec.md e515a14624a99b368827f27aa98c7774e99da67d, .specify/memory/constitution.md absent, design.md 28221e092b75d0727651bb86cce96969ba697cea, docs/architecture/scans-live-in-spec-folder.md 11d494f95f2dd1a73fe70ac6f6c73dd990a817b3
- Review type: full (no earlier report, no plan copy)
- Open: BLOCKER 0 · MAJOR 4 · MINOR 6 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/598-scans-in-spec-folder/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-001) |
| Requirements and traceability | Outstanding (PR-005, PR-008, PR-010) |
| Architecture and boundaries | Clear |
| Adversarial implementation and verification | Outstanding (PR-002, PR-003, PR-006, PR-007, PR-009) |
| Security and reliability | Outstanding (PR-004) |

### Findings

- **PR-001, MAJOR, open.** The spec, the record, and the plan name the sign-off by the review-group command; the one that takes `plan.plan-review` is `wfctl step sign-off` (`cli.py:2461`). It stands because every artifact uses the wrong verb.
- **PR-002, MAJOR, open.** The plan holds clarify and analyze with a `reason`, which marks the current step blocked and never automatic (`_pipeline.py:1183`), while plan review holds with `display` only. It stands because the same condition routes two ways, and the design says an unattended run is sent back.
- **PR-003, MAJOR, open.** The `/plan-review` wrapper's mode table has no row for the three scan readings, so filling a missing scan reruns a full review and spends the cap. It stands because the plan's wrapper edits don't reach the mode table.
- **PR-004, MAJOR, open.** Without the branch check, an agent's plan sign-off, which can clear open BLOCKERs, leaves no trace a person reads. It stands because the plan names no replacement, and the PR-body check for exceptions is the precedent.
- **PR-005, MINOR, open.** Wrapper and skill prose still assumes the PR reviewer reads the scan (analyze lines 232, 287, 333, 338 - 341; clarify line 123; the skill's `#unknown` and out-of-tree refusals). It stands because the plan's edits don't reach it.
- **PR-006, MINOR, open.** The plan doesn't cover the conftest helpers that stage clarify, plan review, and analyze as done. It stands because 18 test files rely on them.
- **PR-007, MINOR, open.** The reader matches `^- Verdict:`, and `writing-a-scan-file` never requires that line form. It stands because only the wrapper templates show it.
- **PR-008, MINOR, open.** design.md, the spec, and the plan render the held and warning text differently, and two warnings have no fix line. It stands because the strings aren't fixed in one place.
- **PR-009, MINOR, open.** The plan doesn't say whether the sign-off still refuses a branch with no issue key. It stands because a test pins the refusal.
- **PR-010, MINOR, open.** The fallback for older features is permanent, so SC-002 holds only for runs in pipeline order. It stands because SC-002 says 100% without that condition.

## Review 2026-11-11T15:23Z

- Verdict: satisfied
- Reviewed: plan.md ebc35e9a4783c990cd4d19efa49fe1a4221660fc, spec.md 3bcdde088920b7a5100f920662ff222bbb94561d, .specify/memory/constitution.md absent, design.md 4d8ca46eb24d58ca390eb8c9771522c11e831d93, docs/architecture/scans-live-in-spec-folder.md c73458e7dbf74fe11d226504b17c28b2db267e4a, docs/architecture/the-scan-is-attested-where-the-reviewer-reads.md f2cce1a1ee8a79e728bb639d4234b395129362fe, plan-review.plan.md 8f51297eaf30e2557b7b126cfec4519dfa4dffe0 (base)
- Review type: re-review, with spec.md, design.md, and the design record re-read in full because they changed since the earlier review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 3 · Fixed since the earlier review: 10
- Detail: /Users/andremarin/Development/wfctl-specs/598-scans-in-spec-folder/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Resolved (PR-001, PR-005, PR-008, PR-010 fixed) |
| Architecture and boundaries | Clear |
| Adversarial implementation and verification | Outstanding (PR-011, PR-012) |
| Security and reliability | Outstanding (PR-013) |

### Findings

- **PR-001 to PR-010, fixed.** Fixed by the revised spec, design.md, record, and `plan.md §Source Code`: the sign-off is `step sign-off`, a held step displays without blocking, the wrapper has a scan-only mode, `check-body` carries the sign-off reason, the prose and fixtures are named, the skill states the verdict line, the texts agree, the no-issue refusal is dropped, and SC-002 is scoped to pipeline order.
- **PR-011, MINOR, open.** The fixture change covers the helpers but not 61 direct `CLEAN_SPEC` writes in 13 test files or the 9 files naming `analysis-report.md`. It stands because the plan doesn't list them; tasks will.
- **PR-012, MINOR, open.** The scan-only mode row names no state, so a `done` pass carrying the scan warning reruns a full review. It stands because the row covers only the held readings; tasks will add the warning case.
- **PR-013, MINOR, open.** A missing scan reruns the step automatically, and the stall check fires only while the three artifacts are unchanged, so a clarify run that edits `spec.md` each time can loop. It stands because clarify's existing automatic rerun carries the same risk, and the stall count (#332) bounds the common case.
