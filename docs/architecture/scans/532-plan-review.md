# Plan review scan for #532

## Review 2026-09-29T12:48Z

- Verdict: satisfied
- Reviewed: plan.md 1ea81b3e2b29413d588fdb4ef40a6d492949bea0, spec.md db761a3a67e99e808e94d086f5b53e8a6a41d8a6, .specify/memory/constitution.md absent, design.md 3f67ed463c463556220ef033868828531753e8c8, docs/architecture/design/532-payload-warnings-list.md 78c8d80a3e185ef6922695f76f785332e2517474, docs/architecture/check-rework-loop.md 4c28df71f6c77456920b4ee0f5e0e468402ef2fc, research.md f56a7555db71f79ddda894a20a9e8eac1620ce5b, data-model.md 198beda6aeb5e4c2df926ba9bef77a9972d9f08a, contracts/cli.md a79ffeb9e39ac25f3a084760ca65161be6f5e120, quickstart.md 77534b4d72dcc16a2fed3d0e57f03714f4196a3f
- Review type: full (no earlier report)
- Open: BLOCKER 0 · MAJOR 2 · MINOR 5 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/532-rework-loop/plan-review.md

The review ran in a fresh-context subagent, under auto-approve.

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Outstanding (PR-003, PR-005) |
| Architecture and boundaries | Outstanding (PR-004, PR-006) |
| Adversarial implementation and verification | Outstanding (PR-001, PR-002, PR-007) |
| Security and reliability | Deferred (no trust boundary is touched; console escaping is already tested) |

### Findings

- **PR-001, MAJOR, open.** The routing test compares every step's `reason` and
  `remedy` against the same feature without the warning, and for `decompose`
  the warned step's reason is the warning, so the test fails as written. Stands
  because the plan names the comparison and not the fix; `tasks.md` carries the
  corrected comparison.
- **PR-002, MAJOR, open.** No test reads `next-step.md` after `wfctl resume`,
  and `next_step_file`'s `warnings` keyword defaults to empty, so a call that
  omits it drops warnings silently. Stands for the same reason; `tasks.md` makes
  the keyword required and adds the resume test in both file forms.
- **PR-003, MINOR, open.** FR-004 says the contract records the new paths, and
  the plan records only `warnings: array`, with the deferral argued in research
  but not in the spec.
- **PR-004, MINOR, open.** The hand-copied `payload_of` in `tests/conftest.py`
  is not listed among the files to change.
- **PR-005, MINOR, open.** The two `arch` validation commands and FR-013 are not
  traced into the plan's implementation order.
- **PR-006, MINOR, open.** Nothing decides whether a pass warning under a held
  step is listed.
- **PR-007, MINOR, open.** There is no test for a remedy that spans several
  lines.
