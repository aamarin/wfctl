# Specification Analysis Report: 005-update-install-skills-default

**Generated**: 2026-07-30
**Remediated**: 2026-07-30 — all 10 findings applied; see Resolution column
**Artifacts**: spec.md, plan.md, tasks.md, research.md, data-model.md, contracts/cli.md, quickstart.md
**Constitution**: absent — see D1

## Findings

All findings below have been applied. The original analysis is preserved so the
reasoning survives; the Resolution column records what changed.

| ID | Category | Severity | Location(s) | Summary | Resolution |
|---|---|---|---|---|---|
| E1 | Coverage | MEDIUM | spec.md FR-012–FR-015; tasks.md T030–T032 | The four tracker requirements have no task citing them. Phase 6 covers the area but names no FR, because the behavior already shipped in `b636356`. | **Applied.** Phase 6 split from 3 tasks to 6 (T030–T035), one per requirement, each naming the existing test that proves it. |
| E2 | Coverage | MEDIUM | spec.md FR-014; tasks.md Phase 6 | FR-014 (declining prints both routes back) is verified by an existing assertion but named by no task at all — the weakest link in the already-implemented set. | **Applied.** New T032 cites FR-014 and names the `("n\n", False)` case of `test_install_skills_prompts_for_tracker` as its evidence. |
| C1 | Underspecification | MEDIUM | spec.md FR-011; tasks.md T013; contracts/cli.md | The summary classifies items "by source directory", but the tracker config is appended outside the `targets` loop and has no source directory. Nothing specifies how it becomes the `1 tracker` figure. | **Applied.** contracts/cli.md gains a counting-rules table stating the tracker config is counted separately for exactly that reason; T013 references it. |
| C2 | Underspecification | MEDIUM | contracts/cli.md; tasks.md T013 | The summary's shape is undefined when a layer contributes zero items. `--agent none` and `--agent codex` both add no layer — is a zero line printed, or omitted? | **Applied.** contracts/cli.md: zero-item layers and zero-count kinds are omitted, never printed as `0`. T011 asserts it. |
| F1 | Inconsistency | MEDIUM | spec.md vs plan.md / contracts/cli.md | Terminology drift: spec.md says "assistant" 55× and "agent" 25×; plan.md and contracts/cli.md say "agent" exclusively; tasks.md is mixed (7 vs 39). A reader mapping FR-003's "assistant layers" to `_AGENT_TARGETS` must translate. | **Applied.** spec.md Assumptions now states the two terms are interchangeable and the drift is deliberate — the spec names the concept, everything downstream names the flag. |
| C3 | Underspecification | MEDIUM | tasks.md T002 | T002 says to capture the reference layout "with the *current* release", but `wfctl` on PATH is now installed from this worktree, so the release is no longer available without reinstalling from git. | **Applied.** T002 now specifies `uvx --from git+https://github.com/aamarin/wfctl.git@master`, which needs no reinstall. |
| E3 | Coverage | LOW | spec.md FR-004, SC-006; tasks.md T003 | FR-004 and SC-006 are implemented by T003 but cited by neither ID. | **Applied.** T003 cites both. |
| E4 | Coverage | LOW | spec.md SC-003, SC-005 | Neither criterion is cited by a task. Both are behaviorally covered (SC-003 by T022/T025, SC-005 by T032 via quickstart §6). | **Applied.** SC-003 cited in T022 (with "in one command, on a repo with no prior install"); SC-005 in T035. |
| A1 | Duplication | LOW | spec.md FR-004 vs SC-006 | Both state that destination uniqueness is enforced automatically. | **Applied.** Kept both, cross-referenced: FR-004 now ends "(Measured by SC-006.)" |
| F2 | Inconsistency | LOW | tasks.md T020 | T020 (uninstall removes only the agent's files, FR-007) sits in the US2 upgrade phase, but FR-007 belongs to US3's agent-layer story. | **Applied.** Kept in US2, with the reason stated in the task: it is the same ownership change as T019 — both prove base-layer paths stopped belonging to the `claude` entry. |

## Coverage Summary

| Requirement | Has Task? | Task IDs | Verification? | Notes |
|---|---|---|---|---|
| FR-001 | Yes | T010, T012 | Automated | |
| FR-002 | Yes | T010, T012 | Automated | |
| FR-003 | Yes | T022, T025 | Automated | |
| FR-004 | Yes | T003 | Automated | |
| FR-005 | Yes | T017, T019 | Automated | |
| FR-006 | Yes | T018 | Automated | |
| FR-007 | Yes | T020 | Automated | |
| FR-008 | Yes | T023, T026 | Automated | |
| FR-009 | Yes | T024, T027 | Automated | |
| FR-010 | Yes | T014 | Automated | |
| FR-011 | Yes | T011, T013 | Automated | |
| FR-012 | Yes | T030 | `test_install_skills_prompts_for_tracker` | |
| FR-013 | Yes | T031 | `test_install_skills_no_tracker_without_a_human` | |
| FR-014 | Yes | T032 | `test_install_skills_prompts_for_tracker` decline case | |
| FR-015 | Yes | T033 | `test_install_skills_keeps_existing_tracker_config` | |
| FR-016 | Yes | T036, T037 | Manual review | |
| SC-001 | Yes | T010 | Automated | |
| SC-002 | Yes | T017 | Automated | |
| SC-003 | Yes | T022, T025 | Automated | |
| SC-004 | Yes | T011 | Automated | |
| SC-005 | Yes | T035 | Manual (quickstart §6) | |
| SC-006 | Yes | T003 | Automated | |
| SC-007 | Yes | T002, T029 | Manual diff | Reference now captured via `uvx --from git+…@master` |

## Constitution Alignment Issues

**D1 (informational, not a violation)**: `.specify/memory/constitution.md` does not
exist in this repository, so the authority this analysis is meant to check
against is absent. `install-skills` provisions `.specify/scripts` and
`.specify/templates` but no constitution. plan.md's Constitution Check therefore
uses six gates authored from this repo's own conventions, and records that
substitution in Complexity Tracking. No principle is violated because none is
defined. Tracked upstream as aamarin/wf-skills#3.

## Unmapped Tasks

None. All 39 tasks map to a requirement, a success criterion, or an explicit
phase gate (T009, T016, T021, T029, T035, T039).

## Verification Gaps

None blocking. All four user stories carry an `Independent Test` and a
`Verification` block. Every implementation task names a verification path; the
only tasks without one are test-authoring tasks (T010, T011, T017, T018, T022,
T023, T024), whose deliverable *is* the verification.

## Metrics

| Metric | Value |
|---|---|
| Total requirements (16 FR + 7 SC) | 23 |
| Total tasks | 39 |
| Coverage — behavioral (≥1 task) | 23/23 (100%) |
| Coverage — explicit ID citation | 23/23 (100%) |
| Ambiguity count | 0 |
| Placeholder count | 0 |
| Duplication count | 1 (LOW) |
| Critical issues | 0 |
| High issues | 0 |

## Next Actions

All 10 findings applied. Re-verified after remediation:

- 39 tasks, IDs contiguous `T001`–`T039`, no duplicates
- All 16 FR and all 7 SC cited by at least one task
- 0 CRITICAL, 0 HIGH, 0 open findings

`/speckit.decompose` may proceed.

The one item that remains genuinely open is not a finding but a validation:
**T028**, the live Copilot discovery check. It is the only task that can
invalidate the design, and it carries a defined fallback (the `.agent.md`
transform from issue #5) that changes only the `copilot` entry in
`_AGENT_TARGETS` plus an extras hook.

**D1 stands**: there is still no constitution file. The gates in plan.md are
locally authored and recorded as such in its Complexity Tracking.
