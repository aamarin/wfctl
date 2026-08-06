# Specification Analysis Report: spec-root-manifest-key

**Feature**: `18-spec-root-manifest-key` (#18)
**Date**: 2026-08-05 (findings) · remediation applied same day
**Artifacts**: spec.md, plan.md, tasks.md, research.md, data-model.md, contracts/cli.md, quickstart.md
**Mode**: the analysis pass was read-only; the three MEDIUM findings were then remediated in `tasks.md` at the user's request. Task IDs below are post-remediation.

## Findings

| ID | Category | Severity | Location(s) | Summary | Status |
| --- | --- | --- | --- | --- | --- |
| E1 | Coverage Gap | MEDIUM | spec.md FR-011, SC-005 | FR-011 and SC-005 both name **uninstall**, but no task exercised `wfctl uninstall` against a manifest carrying `spec_root`. research.md D4 asserted the key survives on a code read of `cli.py:1023`, unpinned by any test. | **Resolved** — T004 added to Phase 2: `wfctl uninstall <agent>` leaves `spec_root` intact. |
| E2 | Coverage Gap | MEDIUM | spec.md FR-015 | FR-015 requires a loud failure for an unparseable manifest "in the current repository **and in the primary working copy** alike". The original test covered only the current repo, and sat in US1 — before the main-checkout fallback exists — so the second half was untestable there. | **Resolved** — T020 added to Phase 4: unparseable main-checkout manifest raises when the worktree declares nothing. |
| E3 | Coverage Gap | MEDIUM | spec.md SC-002 | SC-002 requires artifacts to be "still present after the worktree is deleted". The manual walkthrough never deleted the worktree, leaving the criterion's second clause unverified. | **Resolved** — T033 extended: write a file under the root, `git worktree remove`, confirm it survives. |
| E4 | Coverage Gap | LOW | spec.md FR-006; tasks.md T014, T026 | FR-006 forbids creating or existence-checking the root. T026 pins this for the **command**; for the **resolver** it is only implied by T008 (a branch with no spec directory resolving). No task asserts `spec_root()` itself creates nothing. | Open — fold an assertion into T008 if desired. |
| E5 | Coverage Gap | LOW | spec.md Edge Cases ("Setting present but empty"); data-model.md | The empty-string-means-unset rule is stated in two artifacts and tested by none. | Open — add the case to T007's precedence test. |
| E6 | Coverage Gap | LOW | spec.md US1 AS2; tasks.md T010, T012 | US1 AS2 (an existing spec directory **under the configured root** is found by the unchanged match order) has no dedicated task; it is implied by T010's no-fallback test and T012's reuse of existing `test_resolve_spec_dir_*` cases, which run against the default root. | Open — add the issue-key-glob match under a configured root to T010. |
| F1 | Inconsistency | LOW | spec.md throughout vs plan.md / research.md / tasks.md / contracts | Terminology drift: spec.md says "primary working copy", "per-invocation environment override", "diagnostic command"; every downstream artifact says "main checkout", `WFCTL_SPEC_DIR`, `doctor`. | No change — deliberate register difference; spec.md avoids implementation names by design. Recorded so a reader does not mistake them for different concepts. |
| F2 | Inconsistency | LOW | spec.md US2 framing vs tasks.md Dependencies | The spec presents stories as independently implementable; US2 in fact extends the very function US1 introduces, and US2's tests merged without US1 leave the suite red. | No change — already disclosed in tasks.md ("the one genuine cross-story dependency"). `/speckit.decompose` needs it visible, which it is. |

No CRITICAL or HIGH findings. No duplication, no ambiguity, no unresolved placeholders.

## Coverage Summary

| Requirement | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 one root, both call sites | Yes | T008, T011–T013 | Automated | The defect itself |
| FR-002 precedence chain | Yes | T007, T011 | Automated | |
| FR-003 current repo → main checkout | Yes | T017, T018, T021 | Automated | |
| FR-004 no outside read without a main checkout | Yes | T019, T021, T022 | Automated | |
| FR-005 absolute / `~` / relative | Yes | T009, T011, T023 | Automated | |
| FR-006 never create or validate | Partial | T014, T026 | Automated (command only) | E4 |
| FR-007 match order unchanged | Yes | T012 | Automated (existing suite) | |
| FR-008 unchanged without the setting | Yes | T001, T015, T034 | Automated + baseline | |
| FR-009 command records/reads/removes | Yes | T025, T028 | Automated | |
| FR-010 writes where it persists, reports it | Yes | T025, T028 | Automated + manual | |
| FR-011 survives upgrade/install/uninstall | Yes | T002, T004, T005 | Automated | E1 resolved by T004 |
| FR-012 not treated as a layer | Yes | T002, T003, T005 | Automated | Blocks all stories |
| FR-013 recorded root is the only root | Yes | T010, T012 | Automated | |
| FR-014 diagnostic reports co-existence | Yes | T027, T029 | Automated | Placement before the layers gate pinned in T027 |
| FR-015 unparseable manifest fails loudly | Yes | T010, T020 | Automated | E2 resolved by T020 — both locations now covered |
| SC-001 zero per-worktree steps | Yes | T017–T024, T033 | Automated + manual | |
| SC-002 artifacts survive worktree deletion | Yes | T033 | Manual | E3 resolved — deletion step added |
| SC-003 configured root for a branch with no spec dir | Yes | T008 | Automated | Core regression |
| SC-004 byte-identical paths without the setting | Yes | T001, T015, T034 | Automated + baseline | |
| SC-005 install/upgrade/uninstall/doctor clean | Yes | T002–T006 | Automated | E1 resolved by T004 |
| SC-006 told about a half-finished migration | Yes | T027, T029 | Automated | |

## Constitution Alignment

No `.specify/memory/constitution.md` exists in this repository. plan.md records
this explicitly and substitutes gates derived from the repo's own conventions
(`pyproject.toml` lint pinning and `disallow_untyped_defs`, the `ponytail:`
comment convention). All substituted gates pass. No violations to report; the
absence is a fact about the repo, not a finding against this feature.

## Unmapped Tasks

None problematic. T001 (baseline), T032 (lint), T034 (final gate) map to SC-004
and repo convention rather than to a single requirement; T014 and T022
(`ponytail:` comments) document FR-006 and FR-004 rather than implementing them;
T031 (README) serves FR-009's discoverability intent without a requirement of its
own. All are legitimate.

## Verification Gaps

Every user story phase carries an `Independent Test` and a `Verification` block,
and every implementation task names a verification path — checked task by task.
After remediation, one numbered requirement remains partially verified: FR-006
(E4), where the no-creation guarantee is pinned for the command but only implied
for the resolver. Two acceptance-level gaps remain (E5, E6), both LOW.

## Metrics

- Total requirements: **21** (15 FR + 6 SC)
- Total tasks: **34** (T001–T034, sequential, no gaps — was 32 before remediation)
- Coverage (requirements with ≥1 task): **21/21 = 100%**
- Requirements fully verified: **20/21 = 95%** (was 16/21 = 76%; E1–E3 resolved, E4 open)
- Ambiguity count: **0**
- Duplication count: **0**
- Critical issues: **0**
- High issues: **0**

## Next Actions

No CRITICAL or HIGH findings, and all three MEDIUM findings are remediated in
`tasks.md`. `/speckit.decompose` is not blocked.

The three remaining LOW items (E4, E5, E6) are single assertions folded into
tests that already exist in the plan; they can be picked up during
implementation without a further planning pass, or left as-is.

Suggested next command: `/speckit.decompose`.
