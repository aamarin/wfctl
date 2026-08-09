# Specification Analysis Report: Agent Artifact Layout

**Branch**: `11-agent-artifact-layout` | **Date**: 2026-08-05
**Artifacts**: spec.md, plan.md, tasks.md (+ research.md, data-model.md, contracts/cli.md, quickstart.md)

## Findings

| ID  | Category           | Severity | Location(s)                                      | Summary                                                                                                                                                              | Recommendation                                                                                              |
| --- | ------------------ | -------- | ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| E1  | Coverage Gap       | HIGH     | tasks.md T014–T026; `.agents/commands/brainstorm.md:3,7` | Two of `brainstorm.md`'s five `.agent/` references are repointed by no task — the frontmatter `description` (:3) and the handoff `prompt` (:7). T018 adds `mkdir`, T020 covers :11, T024 covers :13 and :15 | Widen T024 to the whole file, or add a task covering :3 and :7                                                |
| F1  | Inconsistency      | HIGH     | tasks.md T019                                    | T019's merge gate asserts `git grep -nE '\.agent/'` returns nothing across wf-skills. Given E1, the gate cannot pass — it is correct, the task set is incomplete       | Fix E1. The gate needs no change                                                                              |
| C1  | Underspecification | MEDIUM   | tasks.md T028                                    | Premise is false. This repository's `.gitignore` has no `.agent/` line, and wfctl never seeds one — `_ensure_gitignored` (`cli.py:633`) is called for the manifest, backup dir, install targets and `wt/` only. The real entry is hand-written in consumer repos, e.g. `wfctl/.gitignore:19` | Retarget at `wfctl/.gitignore:19` and move into the tooling boundary, or drop it and note consumers clean up at their own pace |
| F2  | Inconsistency      | MEDIUM   | tasks.md, Logical PR Boundaries 2/3/4            | `brainstorm.md` is edited from three different PR boundaries — T024 (boundary 2), T018 (boundary 3), T020 (boundary 4). Three PRs touching one file guarantees rebase conflicts | Group the `brainstorm.md` edits into one boundary, or note the shared file explicitly                        |
| E2  | Coverage Gap       | MEDIUM   | spec.md FR-006                                   | FR-006 ("writing the override file MUST preserve existing content") has zero tasks, because nothing in this feature writes `AGENTS.md` — the installer never seeds it and the managed region belongs to #16 | Mark FR-006 as a forward constraint inherited by #16, or remove it from this feature's scope                  |
| C2  | Underspecification | MEDIUM   | tasks.md T029                                    | Conditional task with an unverified premise. `using-wfctl/SKILL.md` contains no `.agent/` reference, so the task is a no-op as written                                 | Drop it, or replace the condition with the measured fact                                                      |
| D1  | Constitution       | MEDIUM   | `.specify/memory/constitution.md`                | File absent, so constitution alignment cannot be validated. plan.md derives gates from recorded decisions and logs the substitution in Complexity Tracking            | Not blocking. Tracked as the missing-constitution row on wf-skills#10                                         |
| E3  | Coverage Gap       | LOW      | spec.md SC-004                                   | "Overrides survive a fresh clone" is verified by a `git check-ignore` proxy (T021) rather than by an actual clone                                                      | Acceptable proxy; optionally add a clone step to T030's smoke                                                 |

## Coverage Summary

| Requirement | Has Task? | Task IDs                          | Verification? | Notes                                        |
| ----------- | --------- | --------------------------------- | ------------- | -------------------------------------------- |
| FR-001      | Yes       | T004–T011, T014–T018, T020, T023–T026 | Yes       | **Incomplete** — see E1                       |
| FR-002      | Yes       | T014, T016, T017, T018            | Yes           |                                              |
| FR-003      | Yes       | T014                              | Yes           |                                              |
| FR-004      | Yes       | T020, T021                        | Yes           |                                              |
| FR-005      | Yes       | T020, T022                        | Yes           |                                              |
| FR-006      | **No**    | —                                 | —             | **E2** — no writer exists in this feature     |
| FR-007      | Yes       | T004, T005, T010                  | Yes           |                                              |
| FR-008      | Yes       | T006                              | Yes           |                                              |
| FR-009      | Yes       | T023, T024, T027                  | Yes           |                                              |
| FR-010      | Yes       | T024, T025, T026                  | Yes           |                                              |
| FR-011      | Yes       | T025                              | Yes           |                                              |
| FR-012      | Yes       | T018                              | Yes           |                                              |
| FR-013      | Yes       | T005, T006, T011, T013            | Yes           |                                              |
| FR-014      | Yes       | T012                              | Yes           |                                              |
| SC-001      | Yes       | T013, T019, T031                  | Yes           | Blocked by E1 until brainstorm.md is complete |
| SC-002      | Yes       | T030                              | Yes           |                                              |
| SC-003      | Yes       | T010, T030                        | Yes           |                                              |
| SC-004      | Yes       | T021, T022                        | Partial       | **E3** — proxy verification                   |
| SC-005      | Yes       | T030                              | Yes           |                                              |
| SC-006      | Yes       | T027                              | Yes           |                                              |
| SC-007      | Yes       | T012                              | Yes           |                                              |

## Constitution Alignment Issues

Cannot be validated — `.specify/memory/constitution.md` does not exist and the
installer does not provision it. plan.md substitutes gates derived from this
repository's recorded decisions and logs the substitution. No MUST principle is
available to violate, so this is reported as MEDIUM rather than CRITICAL.

## Unmapped Tasks

| Task | Note |
| ---- | ---- |
| T001, T002, T003 | Setup — baseline capture and green-suite confirmation. Expected to be unmapped |
| T028 | Premise false; see C1 |
| T029 | No-op as written; see C2 |

## Verification Gaps

None structural. All 31 tasks carry a verification path (`verify with …`, a
validation command, or an explicit merge gate); all three user stories have both
an `Independent Test` and a `Verification` block.

The one substantive gap is E1, where a merge gate is correct but the task set
feeding it is incomplete.

## Metrics

| | |
| --- | --- |
| Total requirements | 21 (14 FR + 7 SC) |
| Total tasks | 31 |
| Coverage | 20/21 = **95%** (FR-006 uncovered) |
| Ambiguity count | 0 |
| Duplication count | 0 |
| Critical issues | **0** |
| High issues | 2 (E1, F1 — same root cause) |

## Next Actions

No CRITICAL issues. One root cause blocks a merge gate and should be fixed
before `/speckit.decompose`:

1. **Fix E1/F1** — widen T024 to cover all of `brainstorm.md`, or add a task for
   `:3` and `:7`. Without this, T019 cannot pass.
2. **Resolve C1** — retarget or drop T028.
3. **Resolve F2** — group the `brainstorm.md` edits so one PR owns the file.
4. **Decide E2** — keep FR-006 as an inherited constraint on #16, or drop it.
5. C2 and E3 are optional cleanups.

Items 1–3 are edits to `tasks.md` only. No change to spec.md or plan.md is
implied by any finding.

---

## Remediation Applied — 2026-08-05

Approved by the user after the report above. Findings are left as originally
written; this section records what changed.

| ID | Outcome | Change |
| --- | --- | --- |
| E1 | **Fixed** | T018 rewritten to repoint `brainstorm.md:3` and `:7`; the `mkdir` step it previously held moved to new task **T018a**. All 21 `.agent/` references now map to a task |
| F1 | **Fixed** | Resolved by E1. T019's merge gate is unchanged and can now pass |
| C1 | **Fixed** | T028 retargeted from this repository's `.gitignore` (which has no such line) to `wfctl/.gitignore:19`, with the evidence that the installer never seeds it |
| F2 | **Fixed** | PR boundaries restructured from 5 to 6. New boundary 2 groups every `brainstorm.md` edit — T018, T018a, T020, T024 — into one PR, with a note explaining why a boundary deliberately spans three user stories |
| C2 | **Fixed** | T029 removed. `using-wfctl/SKILL.md` has no `.agent/` reference, so the task was a no-op. The ID is left vacant rather than renumbering, so task references in this report remain valid |
| E2 | **Decided — no task added** | FR-006 annotated in spec.md as a constraint inherited by later work rather than a gap here. Nothing in this feature writes `AGENTS.md`, so a task would have no subject. Recorded in tasks.md Notes |
| E3 | **Accepted as-is** | SC-004's `git check-ignore` proxy is retained. A clone step would test git, not this feature |
| D1 | **No action** | Constitution absence is tracked on wf-skills#10; plan.md logs the substitution |

**Post-remediation counts**: 31 tasks (T029 vacant, T018a added — net unchanged),
all carrying a verification path. Requirement coverage 20/21; FR-006 is
deliberately uncovered and annotated as such, so the gap is now a recorded
decision rather than an omission.

**Verified after applying**:

- `grep -E '^- \[ \] T[0-9]{3}a?' tasks.md` → 31 tasks, none missing `verify` or a merge gate
- Every one of the 21 measured `.agent/` references maps to exactly one task
