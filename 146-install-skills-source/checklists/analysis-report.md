# Specification Analysis Report: install-skills source

**Feature**: #146 | **Branch**: `146-install-skills-source` | **Date**: 2026-09-05
**Artifacts**: spec.md, plan.md, tasks.md (+ research.md, data-model.md, contracts/cli.md, quickstart.md)
**Mode**: read-only. No files were modified by this analysis.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| C1 | Coverage gap | HIGH | spec.md FR-004; tasks.md T006 | FR-004 requires the recorded source to resolve identically regardless of the directory a later command runs from. T006 asserts the stored value is absolute, which is the *mechanism*, but nothing exercises the *behavior* — no task runs the freshness check from a different working directory. | Add a test to Phase 3 that installs with a relative source and then invokes `doctor` from a subdirectory, asserting it still resolves. |
| I1 | Inconsistency | MEDIUM | spec.md US2/US3 "Independent Test"; tasks.md "Dependencies" | The spec gives US2 and US3 an `Independent Test` each, implying they stand alone. tasks.md states the opposite outright: both are freshness-check behaviors reading a record only US1 writes, and the dependency graph is a chain. Both cannot be true. | tasks.md is correct. Reword the two `Independent Test` entries to say "given a completed US1 install, …" so the spec stops claiming an independence the design does not have. |
| C2 | Coverage gap | MEDIUM | spec.md FR-012; research.md "Verified, needing no work" | FR-012 was verified to hold with no code, because `--prune` already diffs against what was just installed. Correct today, and nothing pins it — a future change to the prune diff would break the requirement silently. | Add one regression test asserting `--prune` with a named source removes a path that source stopped shipping. Cheap, and it converts a verified observation into a guarded one. |
| C3 | Coverage gap | MEDIUM | spec.md SC-005; quickstart.md | SC-005 is the consumer-repo outcome — a project with no wfctl source tree of its own. Every task and every quickstart step runs inside this repo, where `uv run wfctl` exists. The success criterion the feature is partly justified by is never exercised. | Add a quickstart step run from a repo that is not wfctl (pfms), naming an absolute path to a wfctl checkout. Or accept it as manual acceptance and say so explicitly in tasks.md. |
| C4 | Coverage gap | LOW | spec.md FR-005 | FR-005 (the record must not become committed project content) has no task. It is satisfied by construction — the manifest is already gitignored and R1 chose it for exactly this reason — so this is a traceability gap, not a risk. | No task needed. Note the by-construction satisfaction in tasks.md so the gap is deliberate rather than apparent. |
| I2 | Inconsistency | LOW | spec.md L161-175 | FR-013 appears after FR-014 and FR-015. The clarification pass inserted the two new requirements after FR-012, ahead of an existing FR-013. Numbering no longer matches reading order. | Renumber, or leave and accept it. No downstream artifact depends on the order. |
| I3 | Inconsistency | LOW | spec.md L205 | `SC-006a` is a non-standard identifier introduced to avoid renumbering during clarification. Every other criterion is `SC-###`. | Renumber to SC-007 if the spec is edited for I1 anyway; not worth an edit on its own. |
| A1 | Ambiguity | LOW | spec.md FR-009; contracts/cli.md; quickstart.md | The unreachable-source condition is called "cannot be read" (spec), "source is gone" (contract output), and "unreachable" (quickstart heading). Same state, three names. | Pick one for prose. The rendered string is the contract and should not change; the surrounding descriptions should agree with it. |

No CRITICAL findings. No duplication findings. No unresolved placeholders (`TODO`, `TKTK`, `???`) in any artifact.

## Coverage Summary

| Requirement | Has task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 accept a named source | yes | T005, T010 | yes | |
| FR-002 default unchanged | yes | T006 | partial | Relies on the existing suite as regression; no dedicated assertion |
| FR-003 record the source | yes | T006, T012 | yes | |
| FR-004 resolves from any cwd | yes | T006 | **no** | C1 — mechanism asserted, behavior not |
| FR-005 not committed content | no | — | n/a | C4 — satisfied by construction |
| FR-006 compare against recorded | yes | T014, T018 | yes | |
| FR-007 report the source | yes | T007, T016, T021 | yes | |
| FR-008 remedy carries the source | yes | T017, T018 | yes | Also quickstart step 4 |
| FR-009 unreachable is not a failure | yes | T021, T022 | yes | |
| FR-010 reject an invalid source | yes | T002, T003, T008 | yes | |
| FR-011 accept a checkout root | yes | T002, T003 | yes | |
| FR-012 prune follows the source | no | — | **no** | C2 — verified, unguarded |
| FR-013 session-start defers to the printed command | yes | T019 | yes | Manual read after install, per AGENTS.md |
| FR-014 one-shot semantics | yes | T006, T009 | yes | |
| FR-015 replacement notice | yes | T009, T013 | yes | Survives `--yes` |
| SC-001 one command, no hand edits | yes | T005, T010 | yes | |
| SC-002 no drift after a named install | yes | T007 | yes | |
| SC-003 remedy never discards the source | yes | T017, T025 | yes | |
| SC-004 source change is reported | yes | T016 | yes | |
| SC-005 consumer repo can install | no | — | **no** | C3 |
| SC-006a no silent source change | yes | T009 | yes | |
| SC-006 hand discipline unnecessary | n/a | — | n/a | Post-launch outcome; excluded per analysis rules |

## Constitution Alignment

This repo has **no** `.specify/memory/constitution.md`. plan.md substitutes gates
from `AGENTS.md` and the accepted records under `docs/architecture/`, and records
the substitution in Complexity Tracking — which is what the plan template
requires rather than a workaround.

No constitution conflicts, because there is no constitution to conflict with.
Two related observations, neither a violation:

- The ownership gate cites `drift-is-measured-against-the-recorded-source`, which
  is `proposed`. `wfctl arch context` lists only accepted records, so the gate is
  currently satisfied by a document that is not in force. Declared in Complexity
  Tracking; acceptance is a reviewer decision.
- All seven in-force records were checked against the plan. None is contradicted.
  `layer-model`, `session-state-is-re-derived` and `install-modes` are the three
  this feature touches, and plan.md addresses each.

## Unmapped Tasks

None. All 27 tasks map to at least one requirement, success criterion, or
declared process obligation (T001 baseline, T026 record hygiene, T027 gate).

## Verification Gaps

- **FR-004** — asserted at the storage layer, never at the behavior layer (C1).
- **FR-012** — verified once by reading the code, guarded by nothing (C2).
- **SC-005** — no exercise outside this repository (C3).
- **FR-002** — no dedicated assertion that default-install output is byte-identical
  to today's; depends on existing tests failing if it regresses. Acceptable, but
  worth knowing.

Every user story has both an `Independent Test` and a `Verification` block. Every
one of the 27 tasks carries a verification path in its own text.

## Metrics

| | |
| --- | --- |
| Total functional requirements | 15 |
| Total success criteria | 7 (6 buildable, 1 post-launch outcome) |
| Total tasks | 27 |
| Requirements with ≥1 task | 13 / 15 (87%) |
| Buildable success criteria with ≥1 task | 5 / 6 (83%) |
| Tasks with a declared verification path | 27 / 27 (100%) |
| Ambiguity findings | 1 (LOW) |
| Duplication findings | 0 |
| Critical issues | 0 |

## Next Actions

No CRITICAL issues — `/speckit.decompose` is not blocked.

One HIGH finding (C1) is worth closing first, because it is a one-line test for a
requirement that will otherwise be believed rather than known. C2 is the same
shape and nearly as cheap.

Suggested, in order:

1. Add the cwd-independence test to Phase 3 of tasks.md (closes C1).
2. Add the prune-with-named-source regression to Phase 3 or 6 (closes C2).
3. Decide C3: either add a consumer-repo quickstart step, or state in tasks.md
   that SC-005 is accepted manually and by whom.
4. Optionally fold I1's rewording into spec.md; I2, I3 and A1 are cosmetic and can
   ride along or be left.

---

## Remediation applied — 2026-09-05

All seven findings were addressed. The findings table above is preserved as
written; task IDs in it refer to tasks.md **revision 1**, which was renumbered
when two tasks were inserted. The mapping is in the table below.

| ID | Severity | Resolution |
| --- | --- | --- |
| C1 | HIGH | tasks.md T010 added — installs with a relative source, then runs `doctor` from a subdirectory. Tests FR-004's behavior rather than its mechanism. |
| I1 | MEDIUM | spec.md US2 and US3 `Independent Test` entries now state they are not independent of US1 and name the reason. tasks.md's Dependencies section already said this; the two artifacts now agree. |
| C2 | MEDIUM | tasks.md T011 added — `--prune` with a named source removes a path that source stopped shipping. FR-012 is now guarded rather than merely observed. |
| C3 | MEDIUM | quickstart.md step 8 added — a throwaway `git init` repo installing from an absolute path using the released wfctl on PATH. A repo with no wfctl source tree *is* the consumer condition, so this exercises SC-005 without depending on a specific external project. tasks.md T027 names it. |
| C4 | LOW | tasks.md gained a preamble stating that FR-005 carries no task by construction, and why. The traceability gap is now deliberate and visible rather than apparent. |
| I2 | LOW | spec.md FR-013 moved back into reading order, ahead of FR-014 and FR-015. No identifier changed, so nothing downstream needed updating. |
| I3 | LOW | spec.md SC-006a renumbered to SC-007 and placed after SC-006. |
| A1 | LOW | "unreachable" is now the single term in prose across spec.md FR-009, contracts/cli.md, and quickstart.md. The rendered string `source is gone, can't check` is unchanged — it is the contract, and contracts/cli.md now says so explicitly. |

### Task renumbering (revision 1 → revision 2)

| Revision 1 | Revision 2 |
| --- | --- |
| T001–T009 | unchanged |
| — | **T010 new** (C1), **T011 new** (C2) |
| T010–T014 | T012–T016 |
| T015 | T017 |
| T016–T020 | T018–T022 |
| T021–T023 | T023–T025 |
| T024–T027 | T026–T029 |

### Coverage after remediation

| | Before | After |
| --- | --- | --- |
| Requirements with ≥1 task | 13 / 15 (87%) | 14 / 15 (93%) |
| Buildable success criteria with ≥1 task | 5 / 6 (83%) | 6 / 6 (100%) |
| Tasks with a declared verification path | 27 / 27 | 29 / 29 |
| Total tasks | 27 | 29 |

FR-005 remains the one requirement without a task, now explicitly by
construction rather than by omission.
