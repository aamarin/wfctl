# Specification Analysis Report — #307

Artifacts loaded: `spec.md`, `plan.md`, `tasks.md`, plus the two records committed
on the branch and `design.md`.

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| C1 | Coverage gap | MEDIUM | tasks.md T007–T008 | Eight functional requirements (FR-003, FR-006, FR-009, FR-010, FR-011, FR-014, FR-015) are carried by two tasks that say only "add the instruction". An implementer following `tasks.md` alone can complete T007 and satisfy none of them. | Expand T007/T008 into the sections the instruction must carry, one per requirement, or accept the coarseness explicitly. |
| D1 | Duplication | MEDIUM | spec.md § Assumptions; design.md § Assumed; 307-the-coverage-map-is-the-evidence § Assumed | The same three assumptions — reviewer reads the diff, agent fills rather than fabricates the table, taxonomy is stable — are written out in three artifacts. Two of them are gitignored, so the drift will be invisible. | Keep the record's copy, which is the one a reviewer reads, and point at it from the other two. |
| B1 | Ambiguity | MEDIUM | spec.md FR-004 | "the status the scan assigned it" names no vocabulary. `speckit-clarify` uses Clear / Partial / Missing while scanning and Resolved / Deferred / Clear / Outstanding when reporting; the scan file already written uses the second set. Two implementers would pick differently. | Fix the reporting set in FR-004: Clear, Resolved, Deferred, Outstanding. |
| C2 | Coverage gap | LOW | tasks.md T009 | The AGENTS.md paragraph is a task with no requirement behind it. | Either add an FR for the guidance or note the task as documentation carried by convention. |
| U1 | Underspecification | LOW | spec.md FR-009, FR-010 | Two negative requirements — do not alter the predicates, do not add a gate — with no task and no assertion. The existing suite would fail on a predicate change, which is real coverage but incidental. | Accept; note in the PR body that these are held by the existing suite rather than by a new test. |
| F1 | Inconsistency | LOW | design.md § MVP Scope | Written before FR-013 existed, so its "In" list does not mention committing the scan file or running `arch check`. The clarify step's own answers postdate the design document. | Leave. `design.md` is the upstream artifact and the spec supersedes it; rewriting it would lose the level-1 work. |

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 write clarify scan file | yes | T007 | manual T015 | |
| FR-002 write analyze scan file | yes | T006, T008 | manual T015 | |
| FR-003 verdict vocabulary | no | — | none | C1 |
| FR-004 coverage table | yes | T004, T007, T008 | manual T015 | B1 on the status set |
| FR-005 empty run states it looked | yes | T007 | manual T015 | the case the issue was filed over |
| FR-006 pointer, not a copy | no | — | none | C1 |
| FR-007 arch root is asked | yes | T007 | none | |
| FR-008 wrapper, not SKILL.md | yes | T007, T008 | T010 | |
| FR-009 no predicate change | no | — | existing suite | U1 |
| FR-010 no gate added | no | — | existing suite | U1 |
| FR-011 replace whole, never append | no | — | none | C1 |
| FR-012 suite asserts the wrappers | yes | T010 | T010 | |
| FR-013 commit then arch check | yes | T005, T006 | T012 | |
| FR-014 named for the issue key | no | — | none | C1 |
| FR-015 called a scan file | no | — | none | C1 |
| SC-001 reviewer answers from the diff | yes | T004 | human | not machine-verifiable, acknowledged in spec |
| SC-002 empty run renders every row | yes | T004 | manual T015 | |
| SC-003 no-scan run has no table | — | — | human | the difference is the artifact, not a test |
| SC-004 arch check 0 / 1 | yes | T005, T012 | T012 | |
| SC-005 arch context unchanged | yes | T011 | T011 | |
| SC-006 pipeline unchanged | no | — | existing suite | |
| SC-007 arch check 0 at step end | yes | T005, T006 | T012 | |

## Constitution Alignment Issues

None. The repo ships no `.specify/memory/constitution.md`; `plan.md` substitutes
gates from the accepted records and `AGENTS.md`, and records the substitution in
Complexity Tracking as the template requires. All six gates are ticked with a
named source.

## Unmapped Tasks

- T009 (AGENTS.md paragraph) — see C2.
- T017, T018 (review panel, open the change) — process tasks from
  `opening-a-change`, deliberately outside the requirement set.

## Verification Gaps

- FR-011's replace-never-append rule has no check, which is the cost the level-2
  record's `Considered` accepted when it chose one file per step over one file per
  change: the rule is smaller, but it is still prose.
- SC-003 cannot be tested. A run that never scanned is an agent behaviour, not a
  code path, and the artifact difference is the whole mechanism.

## Metrics

- Total requirements: 22 (15 FR, 7 SC)
- Total tasks: 18
- Coverage: 14 of 22 requirements named by at least one task — 64%
- Ambiguity count: 1
- Duplication count: 1
- Critical issues count: 0

## Next Actions

No CRITICAL issue. Two MEDIUM findings are worth fixing before implementation
because both are cheap: B1 is one clause in FR-004, and C1 is expanding two tasks.
D1 is worth fixing during implementation rather than before it.

Proceed to `/speckit.decompose`, then `/speckit.implement`.
