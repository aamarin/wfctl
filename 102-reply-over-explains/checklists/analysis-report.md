# Specification Analysis Report: reply over-explains

**Generated**: 2026-08-29 · **Remediated**: 2026-08-31 · **Artifacts**: spec.md, plan.md, tasks.md (+ research.md, data-model.md, contracts/, quickstart.md, judgment-test.md)
**Constitution**: none — `.specify/memory/constitution.md` does not exist. Gates are substituted in `plan.md` from `CLAUDE.md` and `docs/architecture/`, which the plan template permits provided the substitution is recorded. It is. No constitution-alignment pass was possible; no finding below is a constitution violation.

## Status: all 11 findings remediated

Every finding below has been applied. The table is kept as the record of what was
found and what was decided — two findings were resolved by *changing the
criterion* rather than adding work, and that is the part worth being able to
re-read later.

| Finding | Resolution |
| --- | --- |
| C1 | **Criterion changed.** SC-009 no longer claims a rise. The 3-of-5 baseline counted whether a table *appeared*; the new measure records whether the form *matched*. Not comparable, so no delta is asserted. Whether form selection beats the table habit stays an open question in `design.md`. |
| C2 | New task **T033** — one depth-asking prompt against the edited skill. Guards T005's deletion of the ceiling sentence. |
| C3 | New criterion **J8** in `judgment-test.md`, exercised by new task **T032** on a state question. |
| C4 | Folded into **T028** — read the *Show* section once end to end. |
| C5 | **T034** extended to assert absence for FR-008 and FR-012a. |
| D1 | `**Verification**` block added to each of Phases 3-7. Five present, five Independent Tests. |
| D2 | **T003** rewritten as a real gate rather than a re-run of T002. Task IDs deliberately not renumbered — a LOW finding does not justify invalidating 33 references. |
| F1 | Both pointers corrected T017 → **T024**. |
| I1 | `plan.md` now reads "Two files change, one is added." |
| I2 | FR and SC identifiers reordered. |
| U1 | **T030** now names `checklists/judgment-88.md`. |

**Post-remediation counts**: 35 tasks (was 33), FR coverage 17/17, SC coverage 13/13.

**Not fixed, because it is not a defect**: T009 and T013 still verify against a
check that lands in Phase 6. That is a consequence of US3 running last so C-6 can
assert against every example the feature adds, and `tasks.md` states the reason in
its Dependencies section.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| C1 | Coverage Gap | HIGH | spec.md:360 (SC-009); tasks.md Phase 8 | SC-009 asserts the share of correctly-formed drawings **rises against the recorded baseline**. No task measures a rise. T031 reads four issues unscored, deliberately. The two-arm check research.md originally planned was removed when the judgment rubric replaced it. | Either restate SC-009 as an unscored observation matching T031, or add a task that runs #88 with and without the selection table. Do not leave a criterion asserting a delta nothing computes. |
| F1 | Inconsistency | HIGH | tasks.md:84 (T009), tasks.md:99 (T013) | Both say "verify with the C-6 check in **T017**". T017 is the caption replacement in Phase 5. The C-6 check is **T024**. An implementer following the pointer lands on the wrong task. | Change both to T024. |
| D1 | Underspecification | HIGH | tasks.md, all five story phases | `speckit-tasks` requires every user story phase to contain both an `Independent Test` **and** a `Verification` block. Five `Independent Test` blocks are present; **zero** `Verification` blocks. The per-phase merge-gate tasks and the closing Verification summary table cover the intent, but the mandated section is absent. | Add a `**Verification**` block to each of Phases 3-7, naming the automated check and the manual check for that story. The content already exists in the summary table; it needs to sit in the phase. |
| C2 | Coverage Gap | HIGH | spec.md:350 (SC-005) | SC-005 — a question that explicitly asks for reasoning still receives full reasoning — has no task. It is the sole guard on the one assumption the experiment never tested: that deleting *"Terseness is the default, not a ceiling"* (T005) does not over-compress. The feature deletes the sentence and never checks the thing the deletion risks. | Add a task to Phase 8: run one depth-asking prompt against the edited skill and confirm the reasoning survives. This is the highest-value missing check in the set. |
| C3 | Coverage Gap | MEDIUM | spec.md:363 (SC-010) | SC-010 — a reply answering a question about current state contains no manufactured "what changed" — has no task. `judgment-test.md` scores #88, which is a *propose an implementation* task, not a state question. The genre split introduced by FR-004 is therefore untested on the genre it was added for. | Add one state-question read to T031's unscored set, or extend the rubric with a J8 covering genre. |
| C4 | Coverage Gap | MEDIUM | spec.md:353 (SC-006) | SC-006 — a reader can state what a reply is composed of after one read — has no task. It is a comprehension check on the skill text, not on a reply, and nothing in Phase 8 reads the skill that way. | Fold into T028's "exercise the changed skill", or accept as a review-time judgment and say so. |
| C5 | Coverage Gap | MEDIUM | spec.md:256 (FR-008), spec.md:275 (FR-012a) | Two prohibitions with no verification. T032 checks the changed file paths, which catches neither "a per-form trigger was added" nor "general skill-hygiene checks were added". | Extend T032 to assert absence: no new trigger prose in the *Show* section, and no frontmatter or anatomy assertions in the new test file. |
| I1 | Inconsistency | MEDIUM | plan.md:89 vs tasks.md:T032 | plan.md says "**Three files change, one is added**" — four paths. T032 expects `git diff --name-only` to list "exactly **three** paths". The real count is two modified (`SKILL.md`, `pull_request_template.md`) plus one added (the test file) = three. plan.md's sentence is wrong. | Fix plan.md to "Two files change, one is added." |
| A1 | Ambiguity | MEDIUM | spec.md:90, spec.md:97 | Terminology drift on the central noun. spec.md uses *drawing* 17×, *diagram* 5×, *visual* 2×, *figure* 1×. The two surviving *visual* instances are inside US2's acceptance scenarios — the exact place an implementer reads for pass/fail. | Normalize to *drawing* in spec.md and the skill. Reserve *figure* for #556's pointer wording, which is a different surface. |
| I2 | Inconsistency | LOW | spec.md:266-289, spec.md:368-370 | Requirement IDs are out of numeric order: FR-012/FR-012a precede FR-011/011a/011b; SC-013 precedes SC-012. An artefact of insertion order, not a content error. | Reorder on the next edit. No functional impact. |
| D2 | Duplication | LOW | tasks.md:T002, T003 | T003 ("Validate Phase 1 with the three commands in T002") re-runs exactly what T002 ran, with no state change between them. | Merge into one task, or make T003 the baseline-recording gate rather than a re-run. |
| U1 | Underspecification | LOW | tasks.md:T030 | "record the scored result to the feature dir" names no filename. | Name the path, e.g. `checklists/judgment-88.md`. |

## Coverage Summary

### Functional Requirements — 15 of 17 covered

| Requirement | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 register rule | yes | T012 | yes | J3 on #88 |
| FR-002 precedence vs rule 1 | yes | T012 | yes | phase gate T015 |
| FR-003 four passages | yes | T005, T016, T017, T026 | yes | grep per conflict |
| FR-004 composition, two genres | yes | T019 | yes | T021 |
| FR-004a N drawings | yes | T019 | yes | T021 |
| FR-005 draw test | yes | T016 | yes | grep |
| FR-005a form selection | yes | T018 | yes | T020 C-5, T021 |
| FR-006 no wfctl in examples | yes | T022, T023, T024 | yes | C-6, red→green |
| FR-007 template points | yes | T026, T027 | yes | grep |
| **FR-008** no per-form trigger | **no** | — | **no** | prohibition — see C5 |
| FR-009 no new skill/key/CLI | partial | T032 | partial | checks paths, not frontmatter |
| FR-010 cross-ref tests pass | yes | T007, T033 | yes | suite |
| FR-011 subject rule | yes | T008 | yes | J1-J4 |
| FR-011a precedence placement | yes | T004, T008 | yes | C-3 |
| FR-011b observable check | yes | T008 | yes | T011 |
| FR-012 automated checks | yes | T006, T020, T024 | yes | the test file |
| **FR-012a** not general hygiene | **no** | — | **no** | prohibition — see C5 |

### Success Criteria — 8 of 13 covered, 3 partial, 4 uncovered

| Criterion | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| SC-001 #88 passes the rubric | yes | T030 | yes | judgment-test.md |
| SC-002 zero volunteered sections | yes | T030 | yes | J3 |
| SC-003 exactly one surface | yes | T020, T027 | yes | C-5 |
| SC-004 zero wfctl examples | yes | T024, T025 | yes | C-6 |
| **SC-005** depth still gets reasoning | **no** | — | **no** | **C2 — guards T005's deletion** |
| **SC-006** composition legible in one read | **no** | — | **no** | C4 |
| SC-007 no drawing when no structure | partial | T031 | partial | J6, unscored |
| SC-008 fan-out drawn unasked | partial | T031 | partial | J5, unscored |
| **SC-009** share rises vs baseline | **no** | — | **no** | **C1 — no task computes a delta** |
| **SC-010** no manufactured "what changed" | **no** | — | **no** | C3 |
| SC-011 zero subject follow-ups | yes | T030 | yes | J1/J4, instrument changed — declared |
| SC-012 word count never alone | yes | T030 | yes | rubric |
| SC-013 every invariant has a check | yes | T006, T020, T024 | yes | C-3, C-5, C-6, C-7 |

## Constitution Alignment Issues

None assessable — no constitution exists. The substitution is recorded in `plan.md` Complexity Tracking as the template requires, and the three substituted gates each pass.

## Unmapped Tasks

None. All 33 tasks map to at least one FR, SC, or contract invariant.

## Verification Gaps

1. **Zero `Verification` blocks** across five story phases (D1) — the one structural non-compliance with `speckit-tasks`.
2. **Four success criteria with no task** (C1, C2, C3, C4). SC-005 is the one that matters: the feature deletes the anti-over-compression sentence and never tests for over-compression.
3. **Two prohibitions unverified** (C5). Absence is checkable and currently unchecked.
4. **T009 and T013 cannot be verified in their own phase.** Both defer to the C-6 check, which lands in Phase 6. `speckit-tasks` wants an adjacent verification in the same phase. This is a real ordering consequence of putting US3 last, not only the F1 typo.

## Metrics

| | |
| --- | --- |
| Total functional requirements | 17 |
| Total success criteria | 13 |
| Total tasks | 33 |
| FR coverage (≥1 task) | 15/17 — 88% |
| SC coverage (≥1 task) | 9/13 — 69% (3 of those partial) |
| Ambiguity findings | 1 |
| Duplication findings | 1 |
| Critical issues | 0 |
| High issues | 4 |
| Medium issues | 4 |
| Low issues | 3 |
