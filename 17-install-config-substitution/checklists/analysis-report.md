# Specification Analysis Report

**Feature**: install-config substitution (#17)
**Date**: 2026-08-03
**Artifacts**: spec.md, plan.md, tasks.md, research.md, contracts/cli.md, quickstart.md
**Constitution**: none present (`.specify/memory/constitution.md` absent) — see C0

## Findings

| ID  | Category           | Severity | Location(s)                   | Summary                                                                 | Recommendation                                                        |
| --- | ------------------ | -------- | ----------------------------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------- |
| A1  | Ambiguity          | MEDIUM   | spec.md FR-015                | "cannot be modified **safely**" — the only vague adjective in the spec. Untestable as written. | Inline the precise condition from contracts/cli.md §3: the hook does not match `^pre_remove:\s*\[\]\s*$`. |
| C1  | Coverage Gap       | MEDIUM   | spec.md FR-009c → tasks T023  | "MUST NOT flag `<agent>`" is named in T023's prose but no test asserts it. A regression would ship silently. | Add an assertion to T024: a template retaining `<agent>` produces no warning. |
| C2  | Coverage Gap       | MEDIUM   | spec.md FR-012a → tasks T013/T015 | The archive-destination line in the prompt is required, but T015's cases don't assert it appears. | Extend T015 to assert the resolved destination path is present in the warning output. |
| C3  | Coverage Gap       | MEDIUM   | spec.md FR-013a → tasks T015  | The non-interactive reachability line ("run from a terminal") has no asserting test. | Extend T015's non-interactive case to assert the remediation line. |
| C4  | Coverage Gap       | MEDIUM   | spec.md FR-013b → tasks —     | "MUST NOT warn about an unsubstituted prefix" has no task at all. Negative requirement, zero coverage. | Add an assertion: a config with `<project>` intact and `pre_remove` wired produces no doctor output. |
| C5  | Coverage Gap       | MEDIUM   | spec.md FR-016 → tasks T013   | "MUST NOT change exit status" is in T013's prose; no case asserts the exit code. | Assert `result.exit_code == 0` in T015's warning cases. |
| C6  | Coverage Gap       | LOW      | spec.md FR-012b → tasks —     | "No non-interactive flag and no dedicated command" is verified only by not building them. | Acceptable. Optionally assert `--fix` is not an accepted option. |
| U1  | Underspecification | LOW      | tasks T027, T028              | Both trace to plan.md's constraints ("no new runtime dependency", "no subprocess"), not to any FR or SC. | Either add an FR for the dependency constraint or accept as plan-level gates. |
| I1  | Inconsistency      | LOW      | spec.md vs plan/tasks/contracts | Deliberate vocabulary split: spec says "terminal multiplexer", "worktree tool", "health check"; the rest say tmux, workmux, doctor. | Intentional per the stakeholder-facing spec guidance. No change; noted so it isn't mistaken for drift. |
| D1  | Duplication        | LOW      | spec.md FR-003, FR-009a, SC-008 | Three statements about the placeholder: the outcome, the detection, and the measure. | Overlapping but distinct roles. Keep. |
| I2  | Inconsistency      | LOW      | spec.md FR ID scheme          | Suffixed IDs (FR-009a/b/c, FR-012a/b, FR-013a/b) introduced by clarify, breaking the flat sequence. | Cosmetic; traceability is intact. Renumber only if a later pass rewrites the section. |
| C0  | Constitution       | INFO     | plan.md Constitution Check    | No `.specify/memory/constitution.md` exists. plan.md substitutes six repo-evidenced gates and says so explicitly. | No action. Recorded so the substitution is not mistaken for an omission. |

**No CRITICAL findings.** No constitution MUST exists to violate, no user story has zero coverage, and no story lacks an `Independent Test` or `Verification` block.

## Coverage Summary

| Requirement | Has Task? | Task IDs | Verification | Notes |
| ----------- | --------- | -------- | ------------ | ----- |
| FR-001 | yes | T006, T007 | manual | US1 — external (wf-skills#8) |
| FR-002 | yes | T008 | manual | teardown never blocked |
| FR-003 | yes | T020, T023 | automated | |
| FR-004 | yes | T020, T022, T024 | automated | |
| FR-005 | yes | T003, T004 | automated | Foundational phase, no story label by format rule |
| FR-006 | yes | T018, T019 | automated | |
| FR-007 | yes | T022, T024 | automated | |
| FR-008 | yes | T020, T021 | automated | apostrophe escaping |
| FR-009 | yes | T020, T021 | automated | |
| FR-009a | yes | T023 | automated | |
| FR-009b | yes | T023, T024 | automated | |
| FR-009c | yes | T023 | **prose only** | **C1** |
| FR-010 | yes | T013 | automated | |
| FR-011 | yes | T009, T010 | automated | |
| FR-012 | yes | T014 | automated | |
| FR-012a | yes | T013 | **prose only** | **C2** |
| FR-012b | no | — | by omission | C6 |
| FR-013 | yes | T015 | automated | |
| FR-013a | yes | T013 | **prose only** | **C3** |
| FR-013b | **no** | — | **none** | **C4** |
| FR-014 | yes | T012, T015, T016 | automated + manual | |
| FR-015 | yes | T011, T012, T015 | automated | wording issue A1 |
| FR-016 | yes | T013 | **prose only** | **C5** |
| FR-017 | yes | T015 | automated | |
| FR-018 | yes | T015 | automated | |
| SC-001 | yes | T007 | manual | US1 external |
| SC-002 | yes | T007 | manual | US1 external |
| SC-003 | yes | T008 | manual | US1 external |
| SC-004 | yes | T013, T015 | automated | |
| SC-005 | yes | T016 | manual | measured: 326→327 lines |
| SC-006 | yes | T018, T019 | automated | |
| SC-007 | yes | T004, T025 | automated + manual | |
| SC-008 | yes | T023, T024 | automated | |

## Constitution Alignment Issues

None. No constitution file exists. plan.md documents the substitution of six
repo-evidenced gates in its place and marks all six passing, with no Complexity
Tracking entries.

## Unmapped Tasks

T027, T028 (U1) — trace to plan.md constraints rather than to a spec requirement.
All other 27 tasks map to at least one FR or SC.

## Verification Gaps

Five requirements (FR-009c, FR-012a, FR-013a, FR-016, and FR-013b) are named in
task prose but have no asserting test. Four are **negative or output-content
requirements** — the class most likely to regress unnoticed, because nothing fails
when they break.

All five are addressed by extending two existing tasks (T015, T024) rather than
adding new ones. No structural change to the plan is required.

## Metrics

- Total Requirements: **33** (25 FR + 8 SC)
- Total Tasks: **29**
- Coverage: **32/33 = 97%** have ≥1 task (FR-012b is verified by omission)
- Strong verification: **28/33 = 85%**
- Ambiguity Count: **1** (A1)
- Duplication Count: **1** (D1, benign)
- Critical Issues: **0**

## Next Actions

No CRITICAL issues; `/speckit.decompose` is not blocked.

However, five MEDIUM verification gaps exist, and the skill's guidance is to
resolve missing verification paths **before** `/speckit.decompose`. All five are
cheap:

1. Extend **T015** to assert: the archive-destination line appears (C2), the
   non-interactive reachability line appears (C3), the exit code is unchanged (C5),
   and a wired-but-unsubstituted config produces no output (C4).
2. Extend **T024** to assert a retained `<agent>` produces no warning (C1).
3. Reword **FR-015** in spec.md to inline the precise refusal condition already
   stated in contracts/cli.md §3 (A1).

Items 1 and 2 are edits to `tasks.md`; item 3 is an edit to `spec.md`. None changes
the design or the phase structure.

---

## Remediation applied — 2026-08-03

All three were applied before `/speckit.decompose`.

| Finding | Resolution |
| ------- | ---------- |
| A1 | FR-015 reworded — "safely" replaced with the explicit condition (anything other than a bare disabled list on its own line), plus why guessing is refused |
| C1 | T024 extended — asserts a template retaining `<agent>` produces no warning |
| C2, C3, C4, C5 | **T015a added** — a dedicated task for output-content and negative assertions: destination line, reachability line, `exit_code == 0`, and doctor producing no output for an unsubstituted prefix |

C4 was the most consequential: FR-013b came out of `/speckit.clarify` and had **zero
tasks**, so the decision that doctor reports `pre_remove` only had no coverage at
all.

C6, U1, I1, D1, I2 and C0 were accepted as-is with rationale recorded above.

**Post-remediation**: 33 requirements, 30 tasks, coverage 32/33 (97%), strong
verification 33/33 (100%) excluding FR-012b which remains verified by omission.

