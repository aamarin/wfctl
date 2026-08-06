# Specification Analysis Report: gitignore glob dedup

**Feature**: `11-gitignore-glob-dedup` | **Date**: 2026-08-04
**Artifacts**: [spec.md](../spec.md), [plan.md](../plan.md), [tasks.md](../tasks.md), [research.md](../research.md), [quickstart.md](../quickstart.md)
**Mode**: read-only cross-artifact consistency analysis

## Findings

**Resolution pass applied 2026-08-04** — E1, E2, E3, and C4 were remediated with
the user's approval. Status column records the outcome; the original finding text
is preserved so the analysis stays auditable.

| ID | Category | Severity | Status | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| E1 | Coverage Gap | **HIGH** | ✅ **RESOLVED** | spec.md FR-006; tasks.md T005 | `--no-index` is a deliberate, load-bearing choice with **no test**. Removing it would make the guard append inert lines for tracked paths, and every existing test would still pass. | Added **T012** — tracks a file, seeds a matching pattern, asserts no entry appended. Named in `.agent/brief.md` as do-not-delete. |
| E2 | Coverage Gap | MEDIUM | ✅ **RESOLVED** | spec.md SC-006; tasks.md T024 | SC-006 sets a **1.5 s** budget, but no task measures install time. The only timing reference is a conditional aside in quickstart.md. | Added **T026** — records ms/call in the PR description. Deliberately *not* a CI assertion: at ~12 ms/call the budget is ~2× measured, close enough to flake, and a flaky test gets deleted. |
| E3 | Coverage Gap | MEDIUM | ✅ **RESOLVED** | spec.md Edge Cases (trailing newline); tasks.md | "Ignore file exists but has no trailing newline" has no test. The behavior is inherited from existing code, so a rewrite could silently drop it. | Added **T013**. |
| C4 | Inconsistency | MEDIUM | ✅ **RESOLVED** | spec.md FR-005 | The stated rationale — "entries are written for artifacts at the moment they are installed" — is inaccurate. `cli.py:881` copies every file before `cli.py:929-932` writes entries, so install paths **do** exist by then. | FR-005 reworded: the requirement holds for `.wf-skills-backup/` and `wt/`, which may not exist, not for the install paths. |
| E5 | Coverage Gap | MEDIUM | ⬜ **OPEN — accepted** | spec.md SC-002; tasks.md T027 | SC-002 claims a newly created worktree shows zero modified files, but no task creates a worktree. T027 only installs into the existing one. | Left open. SC-002 follows from SC-001 plus the `post_create` hook; a scratch-worktree task would cost a ~15 s clone to re-prove it. Revisit if worktree creation itself ever changes. |
| E6 | Coverage Gap | LOW | spec.md Edge Cases (second install adds a target); tasks.md T004 | T004 runs two **identical** installs. The edge case describes a second install that adds a *new* target, which is not exercised. | Extend T004 or add a case installing with `--agent claude` after a bare install. |
| E7 | Coverage Gap | LOW | spec.md SC-005 | No task verifies SC-005. It holds by construction — no wfctl diagnostic exists to contradict it — but nothing asserts it. | Acceptable as-is. Optionally fold a `git check-ignore -v` assertion into T024. |
| A8 | Duplication | LOW | spec.md FR-003, FR-004 | FR-004 (create the file when absent) is a special case of FR-003 (append when uncovered). | Keep both — the file-creation path is distinct enough to warrant its own test (T008). No action. |
| F9 | Inconsistency | LOW | spec.md vs plan.md/tasks.md | spec.md says "ignore file"/"ignore entry"; plan.md and tasks.md say `.gitignore`. | Deliberate altitude difference, not drift. No action. |
| D10 | Constitution | LOW | `.specify/memory/constitution.md` | File does not exist. The skill's "Constitution Authority" clause has nothing to enforce; plan.md substituted repo-appropriate gates and declared the substitution. | No action for this feature. Consider authoring one if the pipeline is used repeatedly here. |

## Coverage Summary

| Requirement | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 no entry for covered path | ✅ | T003, T005 | ✅ automated | Regression test for #11 |
| FR-002 consult VCS, not text | ✅ | T005 | ✅ automated | Implied by T003 passing |
| FR-003 append uncovered | ✅ | T005, T009 | ✅ automated | |
| FR-004 create file when absent | ✅ | T008 | ✅ automated | |
| FR-005 works for nonexistent paths | ✅ | T010 | ✅ automated | Rationale corrected (C4) |
| FR-006 tracked path = covered | ✅ | T012 | ✅ automated | **E1 resolved** — defends `--no-index` |
| FR-007 no stderr leak | ✅ | T011 | ✅ automated | |
| FR-008 fail closed | ✅ | T011 | ✅ automated | |
| FR-009 repeat run identical | ✅ | T004 | ✅ automated | |
| FR-010 applies to every caller | ✅ | T005, T012, T017 | ✅ automated | T012 is a tripwire |
| FR-011 report skipped count | ✅ | T014, T016 | ✅ automated | |
| FR-012 silent when zero | ✅ | T015, T016 | ✅ automated | |
| SC-001 zero changes when covered | ✅ | T003, T024 | ✅ automated + manual | |
| SC-002 worktree zero modified | ⚠️ | T027 | ⚠️ inferred | **E5 open, accepted** |
| SC-003 byte-identical repeats | ✅ | T004 | ✅ automated | |
| SC-004 zero regressions | ✅ | T008-T014 | ✅ automated | |
| SC-005 git tooling explains skips | ⚠️ | — | ⚠️ by construction | **E7 — low risk** |
| SC-006 ≤1.5 s budget | ✅ | T026 | ✅ recorded | **E2 resolved** — measured, not CI-asserted |
| SC-007 83 skipped / 1 written | ✅ | T027 | ✅ manual | Self-checking: counts must sum to 84 considered |

## Unmapped Tasks

None problematic. T001-T002 (baseline), T019-T020 (markers and comments),
T021-T022 (CI gates), T025 (commit hygiene) map to plan.md and quickstart.md
rather than to a numbered requirement, which is expected for setup and polish.

## Verification Gaps

All three gaps from the initial pass are closed:

1. ~~**FR-006** — no test~~ → **T012**. Every one of T005's three load-bearing
   details now has a test that fails without it: T012 for `--no-index`, T011 for
   `capture_output` and the non-zero fallback.
2. ~~**SC-006** — unmeasured~~ → **T026**, recorded rather than CI-asserted.
3. ~~**Trailing-newline edge case**~~ → **T013**.

Remaining: **SC-002** is inferred from SC-001 rather than directly verified
(E5, accepted). Every user story has an `Independent Test` and a `Verification`
block. Every implementation task (T005, T006, T018, T019) names a verification
path.

## Metrics

| Metric | Initial pass | After resolution |
| --- | --- | --- |
| Total Requirements | 19 (12 FR + 7 SC) | 19 |
| Total Tasks | 26 | **29** |
| New tests | 8 | **10** |
| Coverage (≥1 task) | 17/19 = 89% | **19/19 = 100%** |
| Fully verified | 15/19 = 79% | **18/19 = 95%** |
| Ambiguity Count | 0 | 0 |
| Duplication Count | 1 (LOW, no action) | 1 |
| **Critical Issues** | **0** | **0** |
| High Issues | 1 | **0** |
| Medium Issues | 4 | **1** (E5, accepted) |
| Low Issues | 4 | 4 (no action needed) |

## Next Actions

**Nothing blocks `/speckit.decompose`.** Zero CRITICAL, zero HIGH.

Resolved this pass: E1, E2, E3, C4. Files changed — `spec.md` (FR-005),
`tasks.md` (three inserts, renumber T012-T026 → T014-T029), `plan.md` (test
table 8 → 10), `.agent/brief.md` (T012 marked do-not-delete), this report.

Accepted without action: **E5** (SC-002 inferred, not directly verified — a
scratch-worktree task costs a ~15 s clone to re-prove what SC-001 already
shows), plus **E6, E7, A8, F9, D10** — all LOW.

E6, E7, A8, F9, D10 need no action.
