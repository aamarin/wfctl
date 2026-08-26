# Specification Analysis Report: Architecture Knowledge Lifecycle

**Generated**: 2026-08-26
**Artifacts**: spec.md, plan.md, tasks.md, data-model.md, contracts/, research.md
**Mode**: read-only; no files were modified

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| G1 | Coverage Gap | HIGH | data-model.md VR-002/003/004; spec.md Edge Cases; tasks.md | Three of six validation rules have no implementing task. VR-003 (dangling `supersedes` is an error) and VR-004 (two records superseding the same target) are unimplemented, and VR-004 is also a declared spec edge case — so an edge case the spec names has zero coverage. Tasks reference only VR-006, and that as manual seed inspection. | Add tasks to Phase 2 implementing link validation in `wfctl/_arch.py`: dangling `supersedes` → error, superseded-with-no-successor → warning, split supersession → error. Pair with cases in `tests/test_arch_records.py`. |
| G2 | Coverage Gap | HIGH | spec.md FR-012; tasks.md T030–T035 | FR-012 requires placement to "follow a **stated** rule". Tasks apply the rule but no task writes it anywhere shipped. It currently exists only in `design.md` and `data-model.md` — spec artifacts in a separate repo, never installed into a consuming project. The feature about durable knowledge leaves its own placement rule undurable. | Add a task writing the placement rule as a record under `docs/architecture/`, e.g. `knowledge-placement.md`. It is a constraint on the system, so by its own rule that is where it belongs. |
| I1 | Inconsistency | MEDIUM | data-model.md state diagram; tasks.md | The transition graph asserts no transition returns to `proposed` and none leaves `rejected`, but nothing implements or tests that. Records are hand-edited markdown and wfctl only reads `status`, so the diagram describes intent the system does not enforce. | Either add an enforcement task, or state in `data-model.md` that transitions are conventions checked at review, not enforced by wfctl. The second is likely correct and cheaper. |
| G3 | Coverage Gap | MEDIUM | spec.md SC-005; tasks.md T011 | SC-005 ("reasoning recoverable by opening a single file, no version-control archaeology") has no verification task. T011 creates a template with the right sections, which makes the property likely but unverified. | Add a check to T040's quickstart run: open one seed record and confirm its rationale is complete without `git log`. |
| I2 | Inconsistency | LOW | contracts/cli-commands.md vs spec.md, data-model.md | Terminology drift in the user-visible string. Spec and data model say "in-force set" (11 and 3 uses); the rendered CLI output says "Architectural contract — N accepted decisions". Two names for one concept, and the drifting one is what users actually read. | Pick one. "In-force set" is the spec's term; "architectural contract" is the epic's. Normalize the rendered output to match whichever survives. |

No CRITICAL findings.

## Coverage Summary

| Requirement | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 resolution order | yes | T002, T003 | automated | Six legs covered including out-of-tree and non-existent |
| FR-002 query the root | yes | T006 | automated | |
| FR-002a out-of-tree warning | yes | T002, T006 | automated | |
| FR-003 record fields | yes | T011, T012, T015 | manual + skills test | Skill content not suite-verifiable by design |
| FR-004 five statuses | yes | T004, T005 | automated | |
| FR-004a `retired` needs no successor | partial | T004 | automated | Parsing covered; the "no successor required" rule falls under G1 |
| FR-005 accepted body immutable | yes | T009, T014 | automated | |
| FR-006 gate writes the record | yes | T013 | manual (T016) | |
| FR-007 present in-force set | yes | T018, T020, T021 | automated | |
| FR-008 non-accepted excluded | yes | T018, T020 | automated | |
| FR-009 reaches agent at session start | yes | T022, T023 | manual (T023) | Delivery via `start-session`, not a hook — see research.md §5 |
| FR-010 refuse advance | yes | T025, T026 | automated | |
| FR-010a declaration is reviewable | yes | T027, T028 | manual (T028) | |
| FR-011 remove `promote` | yes | T007 | automated + grep | |
| FR-012 placement rule stated | **partial** | T030–T035 | — | Applied but never stated in a shipped artifact — **G2** |
| FR-013 falsification test recorded | yes | T039 | manual | |
| SC-002 agent names in-force set | yes | T023 | manual | |
| SC-004 3/3 edit source tree | yes | T036 | manual | The trial that proves US4 was safe |
| SC-005 single-file reasoning | **no** | — | — | **G3** |

SC-001 and SC-003 are post-launch outcome metrics and are excluded from buildable
coverage, per the analysis guidance. SC-001 is nonetheless load-bearing: it is the
stop-and-measure gate after the MVP that decides whether US3 gets built.

## Constitution Alignment

No `.specify/memory/constitution.md` exists in this repository — verified absent,
and `.specify/` is gitignored, so running `/speckit.constitution` would not
produce one that reaches contributors. `plan.md` substitutes gates from
`AGENTS.md` and records the substitution in Complexity Tracking, which is exactly
what `plan-template.md` instructs for a repo with no constitution.

No conflicts. The substituted gates are all satisfied by the plan and tasks.

## Unmapped Tasks

None. T001 (baseline), T008/T017/T024/T029/T037/T041 (merge gates), T038 (docs)
and T040 (quickstart) are infrastructure and polish rather than requirement
implementations, which is expected.

## Verification Gaps

All four user stories carry an `Independent Test` and a `Verification` block.
All 41 tasks carry a verification path — automated test, validation command, or
named manual check. No implementation task leaves verification implied.

One structural note, not a defect: four verifications are manual (T016, T023,
T028, T036). This is correct rather than lazy — `AGENTS.md` states the suite
checks that skills ship and cross-reference, not that they work, so skill
behaviour cannot be asserted by pytest.

## Metrics

- Total requirements: 19 (16 FR + 3 buildable SC)
- Total tasks: 41
- Coverage: 19/19 have ≥1 task or are explicitly excluded; **2 partial** (FR-012, FR-004a), **1 uncovered** (SC-005)
- Ambiguity count: 0 — no placeholders, TODOs, or unquantified vague adjectives
- Duplication count: 0
- Critical issues: 0
- High issues: 2 (G1, G2)

## Next Actions

No CRITICAL issues; `/speckit.decompose` is not blocked. Two HIGH findings are
worth closing first, and both are small:

1. **G1** — add validation-rule tasks to Phase 2. Three rules, one module, one
   test file. Leaving them means the first split supersession is discovered by a
   human noticing, which is the failure mode this feature exists to remove.
2. **G2** — add one task writing the placement rule as a record. It is a
   one-file addition, and the rule is what makes US4 repeatable rather than a
   one-time cleanup.

`I1` is a two-line documentation fix. `G3` folds into T040. `I2` is a wording
choice.

Suggested: manually edit `tasks.md` to add coverage for G1 and G2, then proceed
to `/speckit.decompose`.
