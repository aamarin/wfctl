# Specification Analysis Report — 109-record-leads-with-drawing

**Date**: 2026-09-16 | **Artifacts**: `spec.md`, `plan.md`, `tasks.md` — all three present and read
**State**: post-remediation. Four findings were applied to the artifacts and one
was filed; the tables below describe the artifacts as they now stand, and the
Findings section says what changed.

## Findings

| ID | Category | Severity | Location(s) | Summary | Resolution |
| --- | --- | --- | --- | --- | --- |
| F1 | Inconsistency | HIGH | `spec.md` FR-008 vs `plan.md` / `research.md` R-004 | FR-008 required reporting "a drawing label that appears in no other section". Measured, that rule reports every label in the corpus — 43 findings over 4 records. `plan.md` and `research.md` carry a narrowed mechanism; `spec.md` did not. | Applied — FR-008 now states the content-word unit and cites R-004 |
| F2 | Inconsistency | MEDIUM | `spec.md` SC-004 vs `research.md` R-006 | SC-004 measured the check over "the 22 records that already carry drawings". Only 4 records carry a `## Boundary`; the 22 draw under `## Context` and `## Decision`, which the Drawing entity excludes. | Applied — SC-004's denominator corrected, with the split cited |
| F3 | Inconsistency | LOW | `spec.md` Assumptions, "three kinds are enough" | The stated validation — classify the 22 existing drawings — cannot run, for F2's reason. | Applied — the assumption now says why it stays open |
| F4 | Inconsistency | LOW | `spec.md` Assumptions and Edge Cases, "eleven" | The corpus grew; 24 proposed records now carry no drawing. | Applied — both sites now carry the current count and why it moved |
| E1 | Coverage gap | MEDIUM | FR-013; `tasks.md` | FR-013 — the rule binds every repository with no per-repository opt-in — had no task. A negative requirement with no test naming it breaks invisibly the first time somebody adds an opt-in. | Applied — T039 added |
| G1 | Design-record contradiction | HIGH | `docs/architecture/design/109-traceability-is-label-agreement.md` (`proposed`) vs `tasks.md` T029 | The record's `## Decision` binds label agreement against `## Owns truth` and `## Decision`, whole-label. T029 implements it against the whole record, content-word. Both narrowings; the record's own Verification is what falsified its rule. | Filed as #401 — only a human moves a `proposed` record, so neither artifact was rewritten to conform |

**No findings** under Duplication or Ambiguity. FR-004/FR-005 and FR-001/FR-009
are distinct requirements rather than near-duplicates, and no placeholder or
unmeasured adjective survives — every vague term in the spec (`noisy`, `wrong`)
is bound to SC-004's counted threshold.

## Coverage Summary

| Requirement | Has task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 declared kind readable | yes | T004, T005, T007 | `tests/test_arch_diagram.py` | |
| FR-002 absent is not a default | yes | T005, T007 | `tests/test_arch_diagram.py` | |
| FR-003 bad kind is reported | yes | T019, T021 | `tests/test_arch_diagram.py` | |
| FR-004 refuse a record with no drawing | yes | T010, T012, T013, T015, T016 | `tests/test_arch_accept_drawing.py` | covered by task text, not by ID citation |
| FR-005 refuse a drawing with no kind | yes | T011, T013, T016 | `tests/test_arch_accept_drawing.py` | |
| FR-006 accepted records untouched | yes | T010, T035 | test + `git ls-files -s` diff | |
| FR-007 listing excludes the refusable | yes | T010, T014 | `tests/test_arch_accept_drawing.py` | |
| FR-008 label report, no refusal | yes | T026, T028, T029 | `tests/test_arch_labels.py` | mechanism narrowed — F1, G1 |
| FR-009 template carries the drawing | yes | T022 | T020 drift test | |
| FR-010 kinds held against the template | yes | T020 | `tests/test_arch_sections.py` | |
| FR-011 projection unchanged | yes | T001, T034 | `arch context` diff against the baseline | |
| FR-012 guidance names which kind | yes | T023 | T024 end-to-end pass | |
| FR-013 no per-repository opt-in | yes | T039 | `tests/test_arch_diagram.py` | added by E1 |
| SC-001 zero exceptions after ship | yes | T010, T016 | the gate's own refusal tests | an outcome of FR-004; no corpus to count yet |
| SC-002 five accepted records identical | yes | T002, T035 | `git ls-files -s` diff | |
| SC-003 kind readable without prose | yes | T005, T011 | `tests/test_arch_diagram.py` | an outcome of FR-001 plus the kind blocker |
| SC-004 no more than two wrong findings | yes | T030, T031 | corpus test + human judgment | |
| SC-005 the refusal reads cold | yes | T017 | manual, judgment recorded in the PR | |
| SC-006 nothing else moves | yes | T001, T034, T040 | `arch context` diff + the full suite | |

**Coverage**: 19 of 19 requirements have at least one task — **100%**, after E1.

## Constitution Alignment

No `.specify/memory/constitution.md` exists. `plan.md`'s Constitution Check
substitutes gates from `AGENTS.md`'s definition of done and the accepted records
`wfctl arch context` projects, and records the substitution in Complexity
Tracking — which is what the plan template requires of a repository with no
constitution. No finding.

The six accepted records the plan names as directly binding were each checked
against the tasks: `a-rule-is-expressed-as-a-check`,
`required-sections-are-wfctls`, `knowledge-placement`, `layer-model`,
`vendor-upstream-skills`, `pipeline-state-is-one-payload`. No task reverses one.

## Unmapped Tasks

None. Every task maps to a requirement, to a success criterion, or to the
project's own definition of done (T003, T009, T018, T025, T032, T040 are merge
gates; T038 is the review panel `opening-a-change` requires).

## Verification Gaps

None standing. Seven tasks carry no `verify with` clause — T008, T011, T019,
T020, T026, T027, T030 — and all seven are test-authoring tasks: the file each
one writes *is* the verification path, and the merge gate closing its phase runs
it. Every implementation task names a test file, a command, or an explicit manual
check.

All three user stories carry an `Independent Test` and a `Verification` block
with automated, manual and evidence lines.

## Metrics

- Total requirements (FR + SC): 19
- Total tasks: 40
- Coverage: 100%
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0
- Findings: 6 · Acted on: 5 · Accepted: 1 (filed as #401)

## Next Actions

No CRITICAL finding stands. One HIGH stands: **G1**, filed as
[#401](https://github.com/aamarin/wfctl/issues/401), open rather than fixed
because only a human moves a `proposed` record past `proposed`. It does not block
`/speckit.decompose` — T033 in `tasks.md` is where the record is amended, and it
is held behind #401 rather than ahead of it.

- Read #401 and decide whether the narrowing stands, before T029 is implemented.
- Then `/speckit.decompose`.
