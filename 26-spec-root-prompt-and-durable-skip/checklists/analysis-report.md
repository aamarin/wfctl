# Specification Analysis Report: spec-root prompt and durable-spec skip

**Date**: 2026-08-11
**Artifacts**: spec.md, plan.md, tasks.md (+ research.md, data-model.md, contracts/cli.md, quickstart.md)
**Status**: analysis complete, remediation applied and re-verified. Task IDs below reflect the post-remediation numbering.
**Constitution**: none present. Gates substituted from repo conventions and recorded in plan.md Complexity Tracking, as the plan template requires. The substitution is disclosed rather than silent.

## Findings

| ID | Category | Severity | Location(s) | Summary | Resolution |
| --- | --- | --- | --- | --- | --- |
| A1 | Coverage | HIGH → **resolved** | spec.md FR-009 | The tool-absent branch was implemented but never verified — the only path that lets a removal proceed after artifacts went unarchived. | Added T023 and quickstart step 5b. |
| A2 | Coverage / Inconsistency | HIGH → **resolved** | spec.md Edge Cases; `_archive.py:158-176` | Spec claimed a failed run "does not overwrite a good earlier one." The code displaced `archive/` **before** copying, so a mid-copy failure left an unindexed partial under the canonical name while the complete result sat under a timestamp reading as superseded. Reproduced against the real module. | Added FR-023, SC-008, T016, T017, T020; rewrote the edge case; documented the naming contract in data-model.md; added quickstart step 5a. |
| A3 | Inconsistency | MEDIUM → **resolved** | spec.md FR-008 | R-006's `--force` and tmux-orphan caveats reached contracts/cli.md and T015 but never FR-008, leaving the requirement the weakest statement of the contract. | FR-008 amended to require the manual route be stated completely. |
| A4 | Coverage | LOW | FR-015/017/018/019, SC-001/003/004/005/007 | Covered by tasks but not cited by ID. Traceability only. | Open — optional, no functional gap. |
| A5 | Inconsistency | LOW | spec.md vs plan.md/tasks.md | spec.md uses abstract terms while plan/tasks use `archive-specs` and `workmux`. Satisfies the template's technology-agnostic rule. | No action. Recorded so it is not "fixed" into drift. |
| A6 | Coverage | LOW | data-model.md | No task asserts `wfctl spec-root` leaves `spec_root_asked` untouched. | Open — a no-change property, low value. |

### Why A2 mattered more than its first framing suggested

The initial reading was "a misleading directory after a rare failure." Reproducing
it showed the feature manufactures the condition: refusing a removal invites a
retry, and the retry displaced the partial into the timestamped pool where nothing
distinguished it from real history. The safety mechanism was the source of the
ambiguity. That moved it from a wording fix to a behaviour fix.

A demonstration against the real module, three successful runs:

```
archive                          4 files   content=v3     ← current
archive-20260811T142417286317Z   4 files   content=v1
archive-20260811T142417301297Z   4 files   content=v2
```

Multiple stored results are normal — every teardown re-run, merge cleanup, and
manual invocation produces one, and nothing prunes them. So the timestamped pool
is real history, which is exactly why a failed attempt must not land in it.

## Coverage Summary

| Requirement | Task IDs | Verification |
| --- | --- | --- |
| FR-001 preserve only at-risk | T008, T018 | yes |
| FR-002 skip artifacts outside worktree | T009, T018 | yes |
| FR-003 containment, not "is it set" | T010, T018 | yes |
| FR-004 report when nothing at risk | T011, T012, T021 | yes |
| FR-005 preserve superseded-location doc | T009, T025 | yes |
| FR-006 refuse on failed preservation | T013, T019 | yes |
| FR-007 proceed when nothing at risk | T014, T019 | yes |
| FR-008 refusal names routes out, completely | T015, T021 | yes |
| FR-009 tool absent → warn, proceed | T022, **T023** | yes (was A1) |
| FR-010 ask at first interactive setup | T028, T034 | yes |
| FR-011 silent when non-interactive | T028, T034 | yes |
| FR-012 default records no location | T029, T035 | yes |
| FR-013 durable choice → primary checkout | T030, T035 | yes |
| FR-014 never create/clone/check | T032, T036 | yes |
| FR-015 record that it was asked | T029, T035 | yes |
| FR-016 record found from any worktree | T031, T035 | yes |
| FR-017 record never affects resolution | T029 | yes |
| FR-018 command named for its artifacts | T006 | yes |
| FR-019 former name keeps working | T004, T005, T006 | yes |
| FR-020 report stale configurations | T038–T041 | yes |
| FR-021 rationale states rescue purpose | T024 | manual, target named |
| FR-022 reconcile one-location wording | T025 | manual, target named |
| **FR-023 never displace a complete result** | **T016, T017, T020** | yes (was A2) |
| SC-001 zero duplicates, any teardown count | T009, T011 | yes |
| SC-002 default layout set unchanged | T008 | yes |
| SC-003 zero artifacts lost to failure | T013 | yes |
| SC-004 refusal always names a route | T015 | yes |
| SC-005 asked exactly once, any worktree | T028, T031 | yes |
| SC-006 default indistinguishable | T029 | yes |
| SC-007 old-name configs still complete | T004 | yes |
| **SC-008 no junk after failure and retry** | **T017** | yes (was A2) |

## Constitution Alignment Issues

None possible — no constitution file. Substitution disclosed in plan.md.

## Unmapped Tasks

T001, T002 (baseline), T046, T047, T048 (validation and manual runs). Validation
infrastructure, not requirement implementation. Expected.

## Verification Gaps

**None.** Every requirement has an automated test, a named validation command, or
an explicit manual check with a stated comparison target. Every user story phase
has an `Independent Test` and a `Verification` block. Every implementation task
names a verification path — checked mechanically across all 48 tasks, zero misses.

## Cross-Artifact Consistency Checks Passed

- Source line numbers cited in tasks.md verified against the working tree:
  `cli.py:276, 300, 424, 604, 803, 1338`; `_archive.py:98, 113, 114, 158-176, 173`;
  `_paths.py:222`; `.workmux.yaml:74-84`. All resolve to the intended constructs.
- All referenced files exist, including `tests/test_remaining_commands.py`.
- Task IDs T001–T048 sequential, no gaps, no duplicates, after two renumbering
  passes during remediation. Prose cross-references re-checked against the new
  numbering.
- Phase 2's ordering departure is consistent across plan.md, tasks.md, and
  research.md R-001.
- US1's internal ordering now has four causal steps, with T020 (atomicity) placed
  before T022 (hook) — arming the hook first would let the first real failures
  manufacture the residue T017 exists to prevent.
- No placeholders, TODOs, or unresolved `[NEEDS CLARIFICATION]` markers.
- No vague quantifiers in requirements or success criteria.

## Metrics

| | Before remediation | After |
| --- | --- | --- |
| Total requirements | 29 (22 FR + 7 SC) | **31** (23 FR + 8 SC) |
| Total tasks | 44 | **48** |
| Coverage (≥1 task) | 100% | **100%** |
| Verification coverage | 97% (FR-009 open) | **100%** |
| Critical | 0 | **0** |
| High | 2 | **0** |
| Medium | 1 | **0** |
| Low | 3 | 3 (A4, A5, A6 — all optional) |

## Next Actions

No blocking issues. `/speckit.decompose` is ready.

A4 and A6 are optional traceability improvements. A5 requires no action and is
recorded only so a future reader does not mistake the deliberate abstraction in
spec.md for drift.

One note carried forward for whoever implements T020: `_archive.py:173` writes
`README.md` into the live archive directory today. It must move into staging with
the copies, or a failed run still leaves an index describing files it never
copied.
