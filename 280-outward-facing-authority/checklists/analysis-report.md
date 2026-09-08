# Specification Analysis Report: notify authority (#280)

**Date**: 2026-09-08
**Artifacts**: spec.md, plan.md, tasks.md, research.md, data-model.md, contracts/, quickstart.md, design.md
**Constitution**: none — `.specify/memory/constitution.md` does not exist. Gates were substituted from repo conventions and the substitution recorded in plan.md's Complexity Tracking, which is what the template requires. No constitution findings are possible; this is noted rather than scored.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|---|---|---|---|---|---|
| C1 | Coverage Gap | **CRITICAL** | spec.md FR-008; tasks.md (absent) | **FR-008 has zero tasks.** "Granted authority MUST NOT apply on `main`" is a security-shaped boundary carried from #131 principle 3 and the accepted decision record, and nothing implements or tests it. Grep for `main` across all 30 tasks returns nothing | Add a task in Phase 2 asserting a grant read on `main` returns refused regardless of any stored value, and a test that fails if it does not. This is the requirement most likely to be true by accident today and broken silently later |
| F1 | Inconsistency | HIGH | quickstart.md:18,35 vs contracts/notify-grant.md | **Rendered console output drifted.** quickstart shows `notify — granted by label …` and `notify — refused; no grant on this branch`; the contract pins `may notify people — you allowed it on issue #280` and `will not notify anyone — nobody has allowed it for this work`. Two artifacts now show different output for the same state | Update quickstart to the pinned wording. The contract is the owner |
| C2 | Coverage Gap | HIGH | spec.md FR-009; tasks.md T023–T026 | FR-009 has two halves — the agent MAY narrow, and MUST NOT widen. Phase 5 covers narrowing (T023) and the irreversible ceiling (T024/T026). Nothing tests that an agent cannot widen | Accept with a stated reason, or add a task. Note the honest position: `clarify` put the local command in every repo, so widening is prevented by rule and not mechanically — a test can only assert the rule is documented, which is weak evidence |
| C3 | Coverage Gap | MEDIUM | spec.md SC-001…SC-005; all artifacts | **No Success Criterion is referenced by any task, plan section, or research note.** SC-001 and SC-002 map cleanly to the manual exercises T014/T022 but are not cited, so the link exists only in my head | Cite SC-001 in T014 and SC-002 in T022. SC-005 (#240 lands unchanged) is not buildable here and should be marked as a post-merge check rather than left looking uncovered |
| C4 | Coverage Gap | MEDIUM | spec.md FR-001, FR-002, FR-007, FR-015; tasks.md | Four requirements are implemented by Phase 2 tasks but cited by none of them. T003/T004 build the storage FR-001 and FR-007 describe; T006 tests the shapes FR-002 and FR-015 name | Add the IDs to the task text. Uncited coverage is indistinguishable from absent coverage to the next reader, which is what this pass exists to catch |
| U1 | Underspecification | MEDIUM | contracts/notify-grant.md; tasks.md T015 | The plain-language rewrite dropped `notify` as a visible token, so no console line names the flag. A reader seeing `will not notify anyone — nobody has allowed it for this work` cannot guess `--allow-notify` | Name the flag in `--help` and say so in T015's task text. Flagged in conversation but never written into the task |
| U2 | Underspecification | MEDIUM | contracts/notify-grant.md; data-model.md | The `unreadable` line reads `couldn't reach GitHub to check`, but the contract's `detail` field is specified only as "why". Whether the line carries `gh` stderr, an exit code, or a fixed string is undecided, and the pinned wording implies a fixed one | Decide in T010. A fixed string is honest and useless; stderr is useful and unbounded in length |
| A1 | Ambiguity | LOW | tasks.md T011 | "the skill that performs it under `wfctl/agents/skills/`" — no skill is named. `decompose` and `end-session` are both candidates and the spec's stories imply both | Name the file(s). An unnamed path in a task is the thing tasks.md exists to prevent |
| I1 | Inconsistency | LOW | design.md:1,3 | Title and a path reference still say *outward-facing*. Both are correct — the filename and branch keep the old term deliberately — but a reader landing on design.md sees the old vocabulary first | Add a one-line note under the title, or accept. Cosmetic |

**Overflow**: none. 9 findings total, under the 50 cap.

## Coverage Summary

| Requirement | Has Task? | Task IDs | Verification? | Notes |
|---|---|---|---|---|
| FR-001 record per branch | yes (uncited) | T003, T004 | T006, T007 | C4 |
| FR-002 absent/unreadable → refused | yes (uncited) | T003 | T006 | C4 |
| FR-003 refused prints a line | yes | T010 | T013 | |
| FR-004 key present-and-false | yes | T009 | T012 | |
| FR-005 grant carries source | yes | T017 | T021 | |
| FR-006 write does not clobber | yes | T004 | T007 | The round-trip that argues for the second file |
| FR-007 event distinct from value | yes (uncited) | T004 | T007 | C4 |
| FR-008 branch-bounded, never main | **NO** | — | — | **C1 — critical** |
| FR-009 narrow yes, widen no | partial | T023, T024 | T025, T026 | C2 — widening untested |
| FR-010 report actions unprompted | yes | T018 | T022 | |
| FR-011 declined ≠ refused | yes | T023 | T025 | |
| FR-012 works with no tracker | yes | T016 | T020 | |
| FR-013 irreversible unreachable | yes | T024 | T026 | T026 must assert from a granted fixture |
| FR-014 read once per run | yes | T016 | T020 | |
| FR-015 failed read distinguishable | yes (uncited) | T010 | T006, T013 | C4 |
| SC-001…SC-005 | uncited | — | T014, T022 | C3 |

## Constitution Alignment Issues

None assessable — no constitution exists. The substituted gates in plan.md all pass, and the substitution is recorded as the template requires.

## Unmapped Tasks

None. All 30 tasks map to a requirement, a story, or a stated polish concern. T001/T002 map to the `clarify` naming decision rather than an FR, which is correct — the rename came out of clarification, not from a requirement.

## Verification Gaps

- **T026 is the one to watch.** It asserts no grant makes an irreversible action reachable. Written against the default fixture it passes vacuously — which is precisely how #240's guard gap survived 863 tests, per `0d2f516`'s own commit message. tasks.md already says "assert against a *granted* fixture, not the default"; keep that wording through implementation.
- Every user story has an `Independent Test` and a `Verification` block. Every implementation task names a verification path or is adjacent to one.
- T014 and T022 are manual and neither is optional. `.agents/` is gitignored, so a green suite is evidence about this repo and not about what `install-skills` produces elsewhere.

## Metrics

- Total requirements: 15 FR + 5 SC = 20
- Total tasks: 30
- FR coverage: 14/15 with ≥1 task = **93%** (FR-008 uncovered)
- FR coverage cited by ID: 10/15 = 67%
- SC coverage cited by ID: 0/5
- Ambiguity count: 1
- Duplication count: 0
- Inconsistency count: 2
- **Critical issues: 1**

## Remediation applied 2026-09-08

The user approved applying every finding that was an edit rather than a decision.

| ID | Status | What changed |
|---|---|---|
| C1 | **fixed** | T008a enforces FR-008; T008b tests it *from the granted side*, since an ungranted fixture passes vacuously. Task count 30 → 32 |
| F1 | **fixed** | quickstart.md re-rendered to the pinned wording; the contract owns it |
| C3 | **fixed** | SC-001 cited in T014, SC-002/SC-004 in T022. SC-005 marked a post-merge check — it cannot be verified until #240 rebases onto this |
| C4 | **fixed** | FR-001, FR-002, FR-006, FR-007, FR-015 now named in T003, T004, T006 |
| U1 | **fixed** | T015 now requires `--help` to carry the flag name, since no console line contains it any more |
| A1 | **fixed** | T011 names both skills — `speckit-delivery-plan` (creates issues) and `end-session` (commits, tracker writes, the omitted push) |
| I1 | accepted | design.md's title keeps the old term; the filename and branch do too, deliberately |
| C2 | **closed — accepted untested** | FR-009's *cannot widen* half has no mechanical enforcement, so a test could only assert the rule is written down. A green `test_agent_cannot_widen_authority` would read as protection that does not exist. Recorded in spec.md FR-009 and in Phase 5 so the absence reads as a decision |
| U2 | **fixed** | Console carries the fixed string; the tracker's stderr goes to a new `notify-unread` event. Two readers, two moments: `status` is glanced at, the log is opened by someone already debugging |

Metrics after remediation: 32 tasks, FR coverage 15/15 (**100%**), FR cited by ID 15/15, SC cited 3/5 with SC-003 and SC-005 stated as non-buildable, critical issues **0**, open findings **0**.

U2's fix surfaced one thing the report had not: the event log gains a *third* kind, `notify-unread`, and nothing was writing it. T005 was extended to add its writer. A decision about console wording turned out to be a decision about the data model.

## Next actions

C1 blocks. FR-008 is the requirement whose absence is least likely to be noticed at implementation time, because a state dir is per-branch and the behaviour is probably correct today by construction — which is exactly the condition under which nothing gets written to keep it correct.

F1, C3, C4 and U1 are edits to the artifacts, not decisions, and can be applied in one pass.

C2 and U2 need a call: whether to test the un-widenable half at all given it is rule-enforced rather than mechanical, and what the unreadable line carries.
