# Plan review scan for #799

## Review 2026-11-18T20:10Z

- Verdict: satisfied
- Reviewed: plan.md 87869267c008b3e1aaa35a4824db3396be9f6a22, spec.md d9e68f4065d3ad43cb93ba1abf04237bb9cc6813, .specify/memory/constitution.md absent, design.md 9147b9f95680548479042075fa4a61dff18dd8da, docs/architecture/design/799-threat-model-in-the-record.md 6d9c979ad7fad08f9ef5a903e21e024837e3b93d, docs/architecture/security-change-needs-threat-model.md 7cbe2d2d9099bd2d12319f074b1dd2855cec0362, docs/architecture/accept-check-threat-model.md fccb089598778a7ed79a30f86b40ea1eb95afa76, research.md 16d6346e97222ced454407b0b4d339b65ed2d4c1, data-model.md 85ddb31f68d413828b56e3a0f83eacaa71623ebc, quickstart.md 190a709581198e245c009b93f8e75ed5cdff3fd6, contracts/threat-model-section.md 93be7d8cc51969c22f7aa5f77e86fe5844061542
- Review type: full (no plan copy from an earlier review)
- Open: BLOCKER 0 · MAJOR 2 · MINOR 5 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/799-security-control-threat-model/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-007) |
| Requirements and traceability | Outstanding (PR-003, PR-004, PR-005) |
| Architecture and boundaries | Outstanding (PR-006) |
| Adversarial implementation and verification | Outstanding (PR-002) |
| Security and reliability | Outstanding (PR-001) |

### Findings

- **PR-001, MAJOR, open.** R-002 has the reviewer read the threat model at the run's head, so a branch that edits an accepted record's lists moves the bar it's judged against. Stands because nothing tells the reviewer to compare with the trunk's version.
- **PR-002, MAJOR, open.** The accept-check test calls `_review_gate.read`, while FR-010 and the record say "through the guard". Stands because the hook's substring prefilter in `wfctl/guard/_hook.py` isn't exercised.
- **PR-003, MINOR, open.** Two of FR-006's four cases, a refused "Must let through" form and a form in no list, aren't traced in the plan.
- **PR-004, MINOR, open.** design.md's draft skill text still says "adds, removes, or narrows", and the plan doesn't say the clarified wording replaces it.
- **PR-005, MINOR, open.** The spec's `arch accept --dry-run` check and SC-003 aren't in the plan.
- **PR-006, MINOR, open.** The heading test's comparison isn't specified, and the plan says tests run in every repository's copy of the bundle, which they don't.
- **PR-007, MINOR, open.** data-model.md says each listed item carries exactly one backticked command, and five items carry more. R-003 miscounts the `--dry-run` items.

## Review 2026-11-18T20:15Z

- Verdict: satisfied
- Reviewed: plan.md 8025c87f2e938ce2c1e9621d78175cc6d4762e42, spec.md e74eeb74c39372770956a48f0480040ebca61f86, .specify/memory/constitution.md absent, design.md 9147b9f95680548479042075fa4a61dff18dd8da, docs/architecture/design/799-threat-model-in-the-record.md 6d9c979ad7fad08f9ef5a903e21e024837e3b93d, docs/architecture/security-change-needs-threat-model.md 7cbe2d2d9099bd2d12319f074b1dd2855cec0362, docs/architecture/accept-check-threat-model.md fccb089598778a7ed79a30f86b40ea1eb95afa76, research.md 16d6346e97222ced454407b0b4d339b65ed2d4c1, data-model.md 85ddb31f68d413828b56e3a0f83eacaa71623ebc, quickstart.md 190a709581198e245c009b93f8e75ed5cdff3fd6, contracts/threat-model-section.md 93be7d8cc51969c22f7aa5f77e86fe5844061542, tasks.md ddb6ab026dbb93b96fef51b79ca0eee9b7d7f80c, plan-review.plan.md 87869267c008b3e1aaa35a4824db3396be9f6a22 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 2 · MINOR 5 · Fixed since the earlier review: 1
- Detail: /Users/andremarin/Development/wfctl-specs/799-security-control-threat-model/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-007) |
| Requirements and traceability | Outstanding (PR-003, PR-004, PR-005, PR-008) |
| Architecture and boundaries | Outstanding (PR-006) |
| Adversarial implementation and verification | Outstanding (PR-002) |
| Security and reliability | Resolved (PR-001 fixed) |

### Findings

- **PR-001, MAJOR, fixed.** Fixed by spec.md FR-013, which requires judging against the trunk's lists when a branch edits an accepted threat model.
- **PR-008, MAJOR, open.** FR-013 has no technical approach in the plan, and research.md R-002 still reads records at the head only. Stands because the plan doesn't say which ref is the trunk, how the reviewer tells a record is accepted there, or what happens when the branch also edits the status.
- **PR-002, MAJOR, open.** The accept-check test runs forms through `_review_gate.read` only, not the full hook, and "Must let through" forms aren't run through the hook at all.
- **PR-003, MINOR, open.** Two of FR-006's four cases aren't traced into the plan or R-005.
- **PR-004, MINOR, open.** design.md's draft skill text still says "narrows".
- **PR-005, MINOR, open.** No plan step for the `arch accept --dry-run` check or SC-003.
- **PR-006, MINOR, open.** The heading test's comparison is still unspecified, though the bundle-reading part is now answered.
- **PR-007, MINOR, open.** data-model.md's one-backtick rule and R-003's wording slip and miscount.
