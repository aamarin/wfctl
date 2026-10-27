# Specification Analysis Report: #649

Run: 2026-10-26, unattended `/speckit.analyze`, after remediation.

Inputs read: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `contracts/cli.md`, `quickstart.md`, `design.md`, and `plan-review.md` (PR-012 to PR-017). No `.specify/memory/constitution.md` exists, so the gates come from `AGENTS.md` and the accepted records, as the plan's Constitution Check says.

Design records: 1 listed in design.md
  docs/architecture/design/649-contexts-module.md (status: proposed)

`design.md` also names `docs/architecture/domain-page-names-contexts.md` in prose. That's a level-2 record, so pass G doesn't read it as binding. Pass D reads it as an accepted gate.

## Findings

| ID | Category | Severity | Location(s) | Summary | Outcome |
| --- | --- | --- | --- | --- | --- |
| C1 | Underspecification | MEDIUM | tasks.md T003 | T003's lead branch, names on the row and reasons in the JSON `annotation` and under `--all`, can't be built. The row and the JSON `annotation` are one field, `sub_steps` carry no `reason`, a reason on a done pass holds its step, and `--all` prints no extra line. Its own fallback, `soft_wrap=True`, is the branch the code leaves. | Fixed: T003 rewritten to the soft-wrap branch, with the three reasons. |
| F1 | Inconsistency | MEDIUM | tasks.md T003, T012, T048 | Three tasks edit `plan.md` during implementation. wfctl reads the plan review as stale after any edit and routes the pipeline back to `plan` (`plan-edit-requires-new-review`, implemented in `_evidence.plan_review`). T003's edit only records a display choice. | Fixed: T003 writes the choice to `contracts/cli.md` only. T012 and T048 say the edit makes the review stale and name the two ways forward. |
| F2 | Inconsistency | LOW | plan.md Phase A item 5, Constitution Check; tasks.md T035, T051 | The tasks differ from the plan in three places the "Review findings" section didn't name: the `--context` skill text moves from Phase A to Phases 5 and 9, the `allowed-tools` line and `design-passes` don't change, and the Constitution Check undercounts the additions beyond the level-3 record. | Fixed: a paragraph in tasks.md's "Review findings these tasks settle" says the task wins and lists the three. `plan.md` isn't edited, for the reason in F1. |
| E1 | Coverage gap | MEDIUM | tasks.md T025, T049; contracts/cli.md `step none` | `step none brainstorm.software-design` has no test for its `--context` success line, its two name refusals, or the bare-form refusal (FR-010, FR-011). T025 runs before #648 adds the pass. | Fixed: T049 adds those tests in `tests/test_step_none.py`, and Phase 9's Verification block names the file. |
| F3 | Inconsistency | MEDIUM | tasks.md T032, T033; spec.md FR-002, FR-021; plan.md Phase B item 7 | T032 and T033 read per-context files with no name-list condition. FR-021 and the plan put the guard check under "with a name list", and FR-002 rules out a new refusal or finding in a repo with no list. They disagree only when per-context files exist without a list. | Accepted: how the guard learns the list at the commit it acts on is a choice the artifacts never made. Filed as #653. |
| F4 | Inconsistency | LOW | tasks.md T033 | T033 extends #635 R12's skip to an inherited per-context "no" whenever the branch changes any level-2 record. A narrower rule matching research R8 is as plausible, and PR-015 asked the plan to choose. | Accepted: picks between approaches the plan left open. Filed as #653. |
| G1 | Design-record contradiction | HIGH | tasks.md T008, T009 | T008 adds `_arch.split_names`, which defines the comma format for all three lists. The record says `_arch.py` gets only the `governs` field and the `validate` finding. | Accepted: the record is `proposed`. Filed as #652. |
| G2 | Design-record contradiction | HIGH | tasks.md T017, T018, T050 | `_evidence.context_gap` gathers the records for both levels. The record says each check gathers its own records and calls `unanswered`. | Accepted: the record is `proposed`. Filed as #652. |

### Pass G detail

- **G · Design-record contradiction, HIGH**: T008 reverses a proposed decision.
  Record: `docs/architecture/design/649-contexts-module.md`
  Decision: "`_arch.py` gets only the `governs` field and the `validate` finding." Consequences: "One module defines the format of the name list and the `Contexts` line."
  Task: "Add `split_names(value) -> tuple[str, ...]` and `Record.governs: tuple[str, ...] = ()` to `wfctl/_arch.py`" (T008), and "The module imports `split_names` from `_arch`" (T009).
- **G · Design-record contradiction, HIGH**: T017 reverses a proposed decision.
  Record: `docs/architecture/design/649-contexts-module.md`
  Decision: "Each check gathers its own records and calls `unanswered`. The architecture pass gives it this branch's level-2 records, and #648's pass gives it this branch's level-3 records. That way, each pass decides which records count."
  Task: "It gathers level-2 records from `records_on_this_branch(...)`, and level-3 records from `records_on_this_branch(repo_root, arch / DESIGN_DIR)` ... A mapping in `_evidence`, keyed by `Level`, picks the folder for each level" (T017), and "call `context_gap(..., SOFTWARE_DESIGN)`" (T050).

Both are likely the design moving rather than a mistake: research R5 explains the split's location, and the user chose the shared function in the plan walkthrough (research R7). A person still has to amend the record or change the tasks.

The extra functions in `_contexts` (`malformed`, `pause`, `answers`, and the `Level` constants) aren't reported as reversals. They add to the one module the record creates, and the record's matching rule stays in it.

### The six plan-review mappings

Each mapping in tasks.md's "Review findings these tasks settle" was checked against the review's suggested response.

1. PR-012 holds. T017 takes git's silence from `trunk_branch` and the arch root's location, T016 and T018 apply it only to `unanswered`, T021 and T050 hand it to `blocks`, and T034 reads it without `blocks`. This follows #648's plan and `promised-evidence-blocks-on-silence.md`.
2. PR-013 holds after C1. Its names-only branch was unreachable, so T003 now resolves to the soft-wrap branch.
3. PR-014 holds. Every file the review listed is named by a task, and `design-passes` line 56 does tell the agent not to run `arch none`.
4. PR-015 holds, with two choices filed under F3 and F4.
5. PR-016 holds. The mapping in `_evidence` is one of the review's two suggestions, and T050 calls `context_gap`.
6. PR-017 holds. T001 and T002 add the `wfctl end` table, the guard refusal, and the two readers.

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 | Yes | T006, T009, T010 | Yes | |
| FR-002 | Yes | T040, T041, T044 | Yes | F3 edge case |
| FR-003 | Yes | T007, T009 | Yes | |
| FR-004 | Yes | T005, T008, T017 | Yes | |
| FR-005 | Yes | T015, T016, T020, T021 | Yes | |
| FR-005a | Yes | T021, T023 | Yes | |
| FR-006 | Yes | T049, T050 | Yes | |
| FR-007 | Yes | T015, T037 | Yes | |
| FR-008 | Yes | T015, T037 | Yes | |
| FR-009 | Yes | T015, T020 | Yes | |
| FR-010 | Yes | T024, T025, T029, T049 | Yes | level 3 added by E1 |
| FR-010a | Yes | T003, T023, T031, T049 | Yes | |
| FR-011 | Yes | T024, T025, T026, T030, T049 | Yes | level 3 added by E1 |
| FR-012 | Yes | T043 to T046 | Yes | |
| FR-013 | Yes | T040 | Yes | |
| FR-014 | Yes | T010 | Yes | |
| FR-015 | Yes | T054 | Manual | read the installed copy |
| FR-016 | Yes | T035, T051, T057 | Manual | grep in T059 |
| FR-017 | Yes | T055, T056 | Manual | |
| FR-018 | Yes | T058 | Manual and `check config` | |
| FR-019 | Yes | T004 | Yes | `wfctl verify` |
| FR-020 | Yes | T027, T034 | Yes | |
| FR-021 | Yes | T028, T032 | Yes | F3 edge case |
| SC-001 | Yes | T026, T030, T021 | Yes | |
| SC-002 | Yes | T023, T024 | Yes | |
| SC-003 | Yes | T040 | Yes | |
| SC-004 | Yes | T040 | Yes | |
| SC-005 | Yes | T018, T060 | Yes | the grep finds nothing today |

**Constitution alignment**: no conflict with an `AGENTS.md` gate or an accepted record. The release note (T004), the definition of done (T062), the install-and-exercise step for skill changes (T059), and `vendor-upstream-skills` all hold. None of the edited skills is spec-kit-derived.

**Unmapped tasks**: none. T012 and T048 rebase onto the dependencies, and T052 carries a Consequence of the level-3 record.

**Verification gaps**: E1, now closed.

## Metrics

- Total requirements: 28 (23 FRs and 5 SCs)
- Total tasks: 62
- Coverage: 100% of requirements have at least one task, after remediation
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0
- Findings: 8, of which 4 were fixed and 4 accepted and filed (#652, #653)

## Next Actions

No CRITICAL finding stands. Two HIGH findings stand (G1 and G2), filed as #652 rather than fixed, because the record they reverse is `proposed` and only a person moves it. A person should decide #652 before Phase 2 is implemented, since T008 is where the split lands. #653 holds two MEDIUM and LOW choices that need deciding before Phase 5. Neither blocks `/speckit.decompose`.
