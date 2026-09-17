# Specification Analysis Report — #339 declare pipeline step

**Date**: 2026-09-17
**Artifacts**: `spec.md`, `plan.md`, `tasks.md` — all three present and read.
**Constitution**: `.specify/memory/constitution.md` does not exist in this repo.
`plan.md` § Constitution Check substitutes `AGENTS.md` and the records
`wfctl arch context` prints, and records the substitution under Complexity
Tracking. Pass D was run against that substituted set.
**Design records** (level-3, from `design.md` § Software design decisions):
`none` — the section is present and carries prose only. Its prose names two
*level-2* records, which bind as level-2 and are read under pass D, not pass G.

This report is written after remediation. Four findings were applied to
`tasks.md`; five stand and are filed.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| D1 | Constitution alignment (record) | HIGH | `docs/architecture/an-absent-artifact-is-claimed-not-inferred.md`; `plan.md` § Complexity Tracking; `data-model.md` § ClaimedAbsence; `contracts/cli.md` § Unchanged | The record's Decision and Consequences are reversed in three places: the claim goes to "the declarations directory" vs `step-claims/<branch>/<step>.<name>.md`; `step none` "generalises `wfctl arch none` rather than sitting beside it" vs a second verb that leaves `arch none` untouched; "a sub-step has three reachable states" vs the four FR-005 requires | Revise the record, or revise the plan. A human's call — the record is `proposed` |
| D2 | Constitution alignment (record) | HIGH | `docs/architecture/a-step-carries-sub-steps-one-level-deep.md` § Consequences; `spec.md` § Clarifications Q2; `contracts/cli.md` § Unchanged | The record says `doctor` gains the finding for a declared pass whose command is not installed. Q2 put it in `wfctl check config` and said explicitly "not in the drift report"; `plan.md` says "`doctor` is not touched" | Same as D1 |
| D3 | Constitution alignment (record) | HIGH | `docs/architecture/brainstorm-is-one-step-with-addressable-levels.md` § Decision; `tasks.md` T004, T034 | The record says `_STEPS` "gains no second axis" and that `design-levels`, not the step table, owns which gates run inside `brainstorm`. T004 adds `sub_steps` to `Step`; T034 puts `architecture` — level 2 — into `_STEPS["brainstorm"]` with an `on_finish` of its own. `plan.md`'s Constitution Check does not mention this record at all | Same as D1, plus: add the record to `plan.md`'s gate list whichever way it is settled |
| F1 | Inconsistency | HIGH | `data-model.md` § ClaimedAbsence; `contracts/cli.md` § `wfctl step none`; `tasks.md` T045, T047; `spec.md` FR-014, US3 acceptance 5 | A claim that cannot reach a reviewer has two opposite specifications. `data-model.md`: "**Refused, and the pipeline does not advance**". `contracts/cli.md`: `⚠ Wrote <path>, but it is not part of the change under review …`, exit 1 — the file *is* written. Because T047 reads claims off disk, a written claim makes the pass `skipped` and the pipeline advances, reversing FR-014. `arch none` does not have this problem: its gate reads git, so an unreachable claim genuinely fails to satisfy it | Decide which reading wins — refuse and write nothing, or honour a claim only where `touched_on_this_branch` is true — then make `data-model.md`, `contracts/cli.md` and T045/T047 agree |
| F2 | Inconsistency | MEDIUM | `spec.md` throughout; both `docs/architecture/*339*` record titles; `data-model.md` § SubStep; `contracts/status-payload.md` | Two vocabularies for one thing. The records and the code say *sub-step* (`SubStep`, `sub_steps`); the spec, plan, tasks and every user-facing string say *pass*. `a-step-carries-sub-steps-one-level-deep` keeps them as distinct terms — "how you do a sub-step, not a sub-step" — and `spec.md` collapses that to "how you do a pass, not a pass". A reader of `--json` sees `sub_steps` while `check config` reports "passes" | Pick one word for the user-facing surface and say in the record why the identifier differs, if it does |
| E1 | Coverage gap | HIGH | `spec.md` FR-021b; `tasks.md` (no task) | FR-021b — a feature granted autonomy runs past a `review_required` pass without stopping — had zero tasks. `auto_approve` is a notice today (`cli.py:570`, `cli.py:807`) and never reaches `next_step_content`, whose comment states the two are deliberately separate axes. As planned, `--auto-approve` would halt at every declared pass, since FR-021 makes `review_required` the default | **Applied**: T012a (implementation) and T022a (test) |
| C1 | Underspecification | MEDIUM | `data-model.md` § States; `spec.md` edge case 7; `tasks.md` T047 | The state table gives `done` when the pass's `reads` returns it and `skipped` when a claim exists, and states no precedence — read top-down it gives `done`, which is the opposite of the spec's edge case: "a pass is declared away, and a later commit produces its artifact anyway: the claim stands". No test covered it | **Applied**: T047 amended to read the claim ahead of the pass's `reads`; T043a added |
| E2 | Coverage gap | MEDIUM | `quickstart.md` § Tests to add; `spec.md` FR-002c; `tasks.md` T038 | `quickstart.md` names "a bare name is not resolved against the current step — FR-002c, the failure the references note argues is silent" as a test to add. T038 covers only the rows of `contracts/cli.md` § `wfctl step none`, and that case is not one of them | **Applied**: T038a |
| E3 | Coverage gap | MEDIUM | `spec.md` FR-008 and edge case 5; `data-model.md` § Where the built-in ones live | FR-008 exists so a pass whose evidence is a heading inside another step's artifact can report correctly, and edge case 5 requires it. Both built-in passes read whole files (`architecture` a record, `design-doc` `design.md`), and `evidence` builds a file-exists reader, so nothing in the delivered set exercises the capability. A regression to a path-only pass would fail no test | **Applied**: T017a |

## Coverage Summary

| Requirement key | Has task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 | yes | T005, T007, T023, T028 | yes | |
| FR-002 | yes | T005, T007 | yes | unknown-step-key rule |
| FR-002a | yes | T007, T015, T016 | yes | |
| FR-002b | yes | T007, T023, T046 | yes | |
| FR-002c | yes | T046, T038, T038a | yes | T038a added by this run |
| FR-003 | yes | T009, T018 | yes | |
| FR-003a | yes | T007, T015, T019 | yes | |
| FR-004 | yes | T007, T020 | yes | |
| FR-005 | yes | T003, T009, T011 | yes | |
| FR-006 | yes | T010, T031 | yes | |
| FR-007 | yes | T012, T021, T024 | yes | |
| FR-008 | yes | T003, T006, T017a | yes | T017a added by this run |
| FR-009 | yes | T006, T017 | yes | |
| FR-010 | yes | T033, T034 | yes | |
| FR-011 | yes | T008, T022, T032 | yes | |
| FR-012 | yes | T045 | yes | |
| FR-013 | yes | T045, T038 | yes | |
| FR-014 | yes | T045 | partial | F1 — the "decline to advance" half is unimplemented and contradicted |
| FR-015 | yes | T045, T039 | yes | |
| FR-016 | yes | T044, T040 | yes | |
| FR-017 | yes | T047, T043a | yes | T043a added by this run |
| FR-018 | yes | T048, T042 | yes | |
| FR-019 | yes | T048, T042 | yes | |
| FR-020 | yes | T011, T043 | yes | |
| FR-021 | yes | T008, T022 | yes | |
| FR-021a | yes | T008, T022, T032 | yes | |
| FR-021b | yes | T012a, T022a | yes | E1 — both added by this run |
| FR-022 | yes | T007, T015, T025 | yes | |
| FR-022a | yes | T007, T021, T025 | yes | |
| SC-001 | yes | T028 | yes | |
| SC-002 | yes | T024, T036 | yes | |
| SC-003 | yes | T045, T049 | yes | |
| SC-004 | yes | T042, T048 | yes | |
| SC-005 | yes | T039 | yes | |
| SC-006 | yes | T040, T044 | yes | |

## Constitution Alignment Issues

No `.specify/memory/constitution.md` exists. Against the substituted set:
D1, D2, D3 above. None is against an **accepted** record — all three are
`proposed`, which is why they are HIGH rather than CRITICAL. The twelve accepted
records `wfctl arch context` prints are honoured: `plan.md` addresses
`pipeline-state-is-one-payload`, `a-rule-is-expressed-as-a-check`,
`knowledge-placement`, `vendor-upstream-skills`, `session-state-is-re-derived`
and `wfctl-runs-the-verification` explicitly, and nothing in `tasks.md`
contradicts any of them.

One citation error, not counted as a finding: `plan.md`'s Constitution Check
lists `the-underscore-is-the-module-contract` without the "(proposed)" marker it
gives the two #339 records. That record is `proposed`.

## Unmapped Tasks

None. T001–T002 are fixtures, T035 and T051–T056 are maintenance and polish, and
every other task carries a requirement or a story.

## Verification Gaps

After remediation, none outstanding. Three user stories each carry an
`Independent Test` and a `Verification` block naming automated tests, a manual
quickstart section, and the evidence to look at. F1 leaves FR-014 partially
implemented rather than unverified.

## Metrics

- Total requirements (FR + SC): 35
- Total tasks: 61 (56 before remediation)
- Requirement-to-task coverage: 100% (97% before remediation)
- Ambiguity count: 0
- Duplication count: 0
- Critical issues count: 0
- Findings: 9 · Acted on: 4 · Accepted: 5

## Next Actions

No CRITICAL finding was raised, so nothing here blocks `/speckit.implement` on
the skill's own rule. What stands is three HIGH and one MEDIUM, all filed rather
than fixed:

- **D1, D2, D3, F2** — the three #339-adjacent architecture records disagree with
  the spec and plan they produced. Filed as one issue. Settling it is a human's
  call: all three records are `proposed`, and only a person moves a record.
  Worth settling **before `/speckit.decompose`**, because D3 in particular
  changes whether `_STEPS` gains `sub_steps` at all.
- **F1** — the claim that cannot reach a reviewer. Filed. Worth settling before
  `/speckit.implement`: T045 and T047 as written produce a claim that warns and
  advances anyway, which is FR-014 inverted, and it is the failure class the spec
  itself calls "the one where a wrong answer looks like success".

Suggested commands: `wfctl arch show <slug>` to read each record, then either
revise the records or open `plan.md` § Complexity Tracking and record why the
plan departs from them.
