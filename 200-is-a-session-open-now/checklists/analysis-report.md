# Specification Analysis Report — #200, is a session open now?

**Date**: 2026-09-13
**Artifacts**: `spec.md`, `plan.md`, `tasks.md` — all three present and read.
**Also read**: `contracts/cli.md`, `data-model.md`, `design.md`,
`checklists/requirements.md`.
**Constitution**: `.specify/memory/constitution.md` does not exist in this
repository. `plan.md` substitutes the repository's accepted architecture records
and records the substitution in Complexity Tracking, which is what the plan
template instructs. Pass D was run against that substituted set.

Counts below are **post-remediation** — the four in-scope fixes had been applied
to `tasks.md` and `plan.md` before this report was written.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| F1 | Inconsistency | HIGH | `tasks.md` T030 | T030 instructed the implementing run to move `200-session-id-rides-on-the-start-event.md` from `proposed` to `accepted` on the strength of phases 3–5 going green. `wfctl arch accept` requires `--agreed` — *where the human agreed* — and its own help names implementation as the one evidence it will not promote on. | **Fixed.** T030 now asks the reader for the citation and runs `wfctl arch accept … --agreed "<where>"`. |
| E1 | Coverage gap | MEDIUM | `spec.md` SC-004; `tasks.md` Phase 4 | SC-004 ("no sequence of interrupted sessions leaves a branch needing manual cleanup") mapped to no task by reference or keyword. T018 and T022 make it true in effect; nothing asserted it. | **Fixed.** T023a added to Phase 4. |
| E2 | Coverage gap | MEDIUM | `spec.md` FR-010, FR-011; `tasks.md` Phases 2–3 | Both are MUST NOTs. FR-010 (no separate state-dir file) and FR-011 (skills never read the event record for this answer) were each realised by a positive task — T018, T015 — with nothing asserting the negative. A later `session.json`, or a skill grepping `events.jsonl`, would pass every test the plan named. | **Fixed.** T009a and T017a added. |
| F2 | Inconsistency | MEDIUM | `plan.md` § Project Structure; `tasks.md` throughout | The plan's `tests/` block listed three files. `tasks.md` names nine. A reviewer reading the plan for the test surface saw a third of it. | **Fixed.** The plan's block now lists all nine. |
| C1 | Underspecification | MEDIUM | `spec.md` FR-014, SC-007; `contracts/cli.md` § `wfctl status --json` | FR-014 requires a takeover be "reported by status, so that neither the displaced conversation **nor a later reader** has to read that record directly". The contract gives status `session_holder`, a *current-state* field: after a takeover a third conversation reads `"other"`, which is what it would read had no takeover ever happened. The displaced-conversation half is served; the later-reader half is not. | **Accepted.** Deciding what status prints for a takeover is a surface decision the plan and contract left open. |
| G1 | Design-record contradiction (pass input) | MEDIUM | `design.md` | `design.md` carries no `## Software design decisions` section, so `reading-design-records` resolves the list as `unknown` and pass G had nothing to compare tasks against. The record exists and is named in prose under `## Level 3 — design`, which that skill explicitly does not read. Four steps — plan, tasks, implement, analyze — all resolve `unknown` for this feature. | **Accepted.** The fix is in `design.md`, outside the three artifacts this step may edit. |

No CRITICAL finding was raised. No duplication (pass A) and no ambiguity
(pass B) finding met the bar: there are zero unresolved placeholders, and every
vague adjective in `spec.md` carries a measurable criterion in Success Criteria.

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 | yes | T006, T018 | yes | |
| FR-002 | yes | T017 | yes | |
| FR-003 | yes | T007, T009, T024 | yes | |
| FR-004 | yes | T018 | yes | |
| FR-005 | yes | T019 | yes | |
| FR-006 | yes | T020, T024, T026 | yes | |
| FR-007 | yes | T010, T011 | yes | |
| FR-008 | yes | T013 | yes | |
| FR-009 | yes | T012 | yes | |
| FR-010 | yes | T018, **T009a** | yes | negative assertion added by E2 |
| FR-011 | yes | T015, **T017a** | yes | negative assertion added by E2 |
| FR-012 | yes | T022 | yes | |
| FR-013 | yes | T016 | yes | |
| FR-014 | yes | T018, T021, T014 | partial | status half is C1 |
| SC-001 | yes | T012, T013, T015 + quickstart | yes | manual exercise |
| SC-002 | yes | T025, T026, T028 | yes | |
| SC-003 | yes | T018, T021 + quickstart | yes | manual exercise |
| SC-004 | yes | **T023a** | yes | added by E1 |
| SC-005 | yes | T011, T014 | yes | |
| SC-006 | yes | T027 | yes | |
| SC-007 | yes | T014, T021 | yes | |

**Constitution Alignment Issues**: none. No constitution file exists; the six
accepted records `plan.md` substitutes were each checked against the task list
and none is reversed by a task.

**Unmapped Tasks**: T001, T002 (baseline capture), T029 (README), T030–T033
(record work, doctor, review panel). All are housekeeping the plan calls for
rather than requirements the spec states. No action.

**Verification Gaps**: none standing. FR-014's status half is a specification
question (C1), not a missing test.

## Metrics

- Total requirements (FR + SC): **21**
- Total tasks: **37** (33 before remediation, 4 added)
- Requirement-to-task coverage: **100%** (was 95% — SC-004 was the gap)
- Ambiguity count: 0
- Duplication count: 0
- Critical issues count: 0

## Next Actions

No CRITICAL stands, and none was found. Two MEDIUM findings stand, both
accepted rather than fixed:

- **C1** — what `wfctl status` prints so a later reader learns the branch changed
  hands. It is a contract question, and answering it is `/speckit.plan`'s to do
  or the reader's to rule out of scope. It does not block `/speckit.implement`:
  the displaced conversation, which is the case FR-014 was written for, is
  already served by `session_holder == "other"` and the second refusal string.
- **G1** — `design.md` needs a `## Software design decisions` section listing
  `docs/architecture/design/200-session-id-rides-on-the-start-event.md`. Until
  it has one, every downstream step reports the feature as having no design
  records. Cheap to fix and outside this step's edit scope.

`/speckit.decompose` is the next pipeline step. Every user story now carries an
`Independent Test` and every implementation task names a verification path, so
nothing in this report blocks it.
