# Specification Analysis Report: one predicate signature

**Date**: 2026-09-09
**Artifacts**: spec.md, plan.md, tasks.md, research.md, data-model.md, contracts/status-render.md
**Constitution**: none shipped — gates substituted from `AGENTS.md` and the accepted records, substitution recorded in plan.md Complexity Tracking

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| E1 | Coverage gap | MEDIUM | spec.md FR-007; tasks.md | No task names the continuation flags. `test_pipeline_commands.py:112` pins `next_step_content` for all eight steps and would catch a moved flag, but incidentally — the plan never says so, so a future edit to that test removes the only coverage without anyone noticing | Add a task asserting the eight `(command, auto)` pairs are unchanged, or state in T020 that `test_pipeline_commands.py:112` is FR-007's coverage |
| E2 | Coverage gap | MEDIUM | spec.md FR-008, SC-006; tasks.md | Nothing verifies that searching for a step's name still finds its predicate. The design record's Verification section names the `grep`; tasks.md dropped it | Add the `grep -rn '_decompose' wfctl/` check to T020 — it is the check that a registry of strings was not rebuilt by accident |
| E3 | Coverage gap | MEDIUM | spec.md SC-004; tasks.md T021, T024 | SC-004 says eight of eight steps resolve inconclusive evidence through `blocks`. T021 routes `decompose`; T024 checks the signature shape. Neither counts the callers | Extend T024 to assert every predicate that can reach an inconclusive verdict calls `blocks`, or accept SC-004 as verified by T022's diff plus code review and say so |
| F1 | Inconsistency | MEDIUM | spec.md FR-001/FR-003/SC-002 vs plan.md, data-model.md, tasks.md | Terminology drift: spec.md says "decision procedure" and "decision", every downstream artifact says "predicate". The spec avoided the term to stay stakeholder-readable, which is defensible, but the mapping is nowhere stated | Add one line to spec.md's Key Entities naming "predicate" as the codebase's term for a step's decision procedure |
| C1 | Constitution alignment | MEDIUM | plan.md; tasks.md T015 | T015 keeps `verification_block` importable from `_pipeline` after moving it to `_predicates`, which means a re-export shim. `the-underscore-is-the-module-contract` (proposed, not in force) holds that a module import is not a crossing — so `cli.py` may import `_predicates` directly and the shim is avoidable | Change `cli.py:3789` to import from `wfctl._predicates` rather than adding a re-export. A shim added for one call site is the kind that outlives its reason |
| U1 | Unmapped task | LOW | tasks.md T002, T030, T031 | T002/T030 guard the `mypy --strict` finding count and T031 is a conditional no-op. None maps to an FR or SC | Keep them. They are regression guards the repo's conventions call for; note in tasks.md that they map to `AGENTS.md` rather than to a requirement |
| U2 | Coverage gap | LOW | spec.md SC-002; tasks.md Phase 3 | SC-002 ("changing one step touches one decision procedure") is verified only by US1's story-level Independent Test — a scratch commit that is then discarded — with no numbered task | Acceptable. The measurement is inherently a one-off; recording its result in the PR body is enough |

No CRITICAL or HIGH findings. Every implementation task carries a verification
path, every user story has an `Independent Test` and a `Verification` block, and
each phase ends with a merge-gate task.

## Coverage Summary

| Requirement | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 one signature | yes | T007, T011-T018 | mypy + suite | |
| FR-002 state and reason | yes | T007, T015 | mypy + suite | |
| FR-003 declaration carries predicate | yes | T017, T027 | mypy, exercised | T027 makes it fail on purpose |
| FR-004 state is a closed set | yes | T007, T026, T027 | mypy, exercised | |
| FR-005 all resolve through `blocks` | yes | T021 | suite | see E3 |
| FR-006 verdict unchanged | yes | T001, T022, T023 | render diff | the strongest check here |
| FR-007 no continuation flag moves | **no** | — | incidental | **E1** |
| FR-008 grep still finds it | **no** | — | none | **E2** |
| FR-009 no new read | partial | T009 | render diff | order preserved by instruction, not by check |
| FR-010 predicates separable | yes | T004-T006, T029 | ruff + suite | |
| SC-001 byte-identical render | yes | T001, T022 | render diff | |
| SC-002 one-function diff | story-level | — | Independent Test | **U2**, accepted |
| SC-003 rejected before commit | yes | T027 | exercised | |
| SC-004 eight of eight | partial | T021 | none direct | **E3** |
| SC-005 no branch on step name | yes | T020 | `grep -c` | |
| SC-006 one hop each direction | **no** | — | none | **E2** |

## Unmapped Tasks

T002, T030, T031 — see U1. All three trace to `AGENTS.md` conventions rather
than to a requirement, which is legitimate but undeclared.

## Verification Gaps

None blocking. Every task in tasks.md carries `verify with`, a validation
command, or an explicit manual check. The three MEDIUM coverage gaps (E1, E2,
E3) are requirements without a *named* check, not tasks without one.

## Metrics

- Total requirements: 16 (10 FR, 6 SC)
- Total tasks: 33 across 6 phases
- Coverage: 12 of 16 requirements have ≥1 directly mapped task (75%); 2 partial, 3 unmapped
- Ambiguity count: 0 — no vague adjectives, no placeholders, no `[NEEDS CLARIFICATION]`
- Duplication count: 0
- Critical issues: 0

## Next Actions

No CRITICAL issues, so the pipeline may proceed. Three MEDIUM findings are worth
closing first because each is a one-line edit and each closes a requirement that
would otherwise be verified by accident:

1. **E2** — add the `grep` to T020. Closes FR-008 and SC-006 together.
2. **E1** — name `test_pipeline_commands.py:112` as FR-007's coverage in T020.
3. **C1** — change T015 to update `cli.py`'s import rather than add a re-export.

**F1** (terminology) and **E3** are worth doing and do not block: F1 is a line in
spec.md's Key Entities, E3 is a sentence in T024.

Suggested command: manually edit `tasks.md` for E1/E2/C1 and `spec.md` for F1,
then `/speckit.decompose`.

## Remediation applied — 2026-09-09

All six findings closed in the artifacts rather than carried into
implementation. The report above is kept as written so the findings and their
disposition can both be read; the rows are not edited to look clean.

| ID | Disposition | Where |
| --- | --- | --- |
| E1 | Fixed — T020 now names `test_pipeline_commands.py:112` as FR-007's coverage | tasks.md T020 |
| E2 | Fixed — T020 now greps for the predicate in both the table and the module | tasks.md T020 |
| E3 | Fixed — T024 now asserts eight of eight reach `blocks` | tasks.md T024 |
| F1 | Fixed — `Predicate` added to Key Entities, mapping the three terms | spec.md Key Entities |
| C1 | Fixed — T015 changes `cli.py`'s import instead of adding a re-export shim | tasks.md T015 |
| U1 | Accepted — T002 now states it maps to `AGENTS.md`, not to a requirement | tasks.md T002 |
| U2 | Accepted as-is — SC-002 is a one-off measurement; its result goes in the PR body | no change |

Coverage after remediation: 15 of 16 requirements have a named check. SC-002
remains story-level by design.
