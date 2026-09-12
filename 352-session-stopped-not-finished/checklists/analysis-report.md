# Specification Analysis Report — #352 Session Stopped, Not Finished

**Date**: 2026-09-11
**Artifacts**: `spec.md`, `plan.md`, `tasks.md` — all three present and read.
**Supporting**: `research.md`, `data-model.md`, `contracts/wfctl-end.md`,
`contracts/start-session-step-9.md`, `quickstart.md`,
`docs/architecture/stop-kind-is-a-field-not-an-event.md`.

**Design records**: unknown — no `design.md` at
`/Users/andremarin/Development/wfctl-specs/352-session-stopped-not-finished`.
Pass G could not run; see its row below.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| F1 | Inconsistency | HIGH | `tasks.md` T004; `contracts/start-session-step-9.md` § Step 9 | T004 says to rewrite row one "leaving rows two and three as they stand". The contract's table rewrites row two as well — from "a summary, and an `end` event — a session has finished here before" to "a summary, and a stop that was wrapped up". Left as it stands, row two's condition is true of a *continued* stop too, so rows one and two both match the exact case the feature exists to fix. | Rewrite row two in the same task. Its condition must name the stop's kind, not the event's presence. |
| E1 | Coverage gap | HIGH | `tasks.md` T002, T007; `tests/test_start_session_asks_conditionally.py:63,76` | `_row()` selects a row by its condition-column **prefix** and calls `pytest.fail` when it finds none. T003/T004 change the prefixes of rows one and two, so `test_a_handoff_on_a_branch_nobody_has_worked_on_starts_without_a_reply` and `test_a_branch_that_has_ended_a_session_before_is_still_asked` both fail. No task owns updating them; T007's merge gate runs the module and goes red with no assignee. | Extend T002 to re-anchor the two existing assertions on the new conditions. |
| C1 | Underspecification | HIGH | `tasks.md` T003; `tests/test_start_session_asks_conditionally.py:33` | T003 rewrites **step 4** and says "verify with T002's assertions". `_step_nine()` returns `text[text.index(_STEP_NINE_HEADING):]`, so every helper in that module slices from step 9's heading downward. Step 4 sits above the slice and is unreachable — T003 ships with no verification at all. | Give T002 a step-4 slice and an assertion binding the stated `grep … | tail -1` command and its three-outcome table; point T003's verify at it. |
| E2 | Coverage gap | HIGH | `tasks.md` T020 | T020 asserts three existing readers reach today's verdict (SC-005) and verifies with `tests/test_session_existence.py tests/test_agent_session.py`. Neither module references `_stall._passes_this_sitting` or `_stall.opens_a_new_sitting`; the only module that exercises sitting behaviour is `tests/test_stall.py`. Two of the three readers named are unverified by the command given. | Add `tests/test_stall.py` to T020's verification command. |
| C2 | Underspecification | MEDIUM | `tasks.md` T016; Phase 5 preamble | T016 asserts "the most-recent-wins rule (FR-007)" in `tests/test_session_stopped_not_finished.py`, a CLI-level module. FR-007 is implemented by `tail -1` inside `start-session/SKILL.md`, and Phase 5 states "No production change is expected in this phase" — so there is no function for the test to call. As written it can only assert the log's file order, which is FR-008's property, already T015's. | Restate T016 as what it can observe (mixed history survives in order with kinds intact) and move FR-007's routing pin to the step-4 table assertion from C1 plus `quickstart.md` half 2. |
| F2 | Inconsistency | MEDIUM | `tasks.md` T011; `wfctl/_session.py:458`; `wfctl/cli.py` | The `- [ ] (fill in)` placeholder is written by `_render_session_summary` in `_session.py`. T011 puts the detector that recognises it in `cli.py`. The literal then lives in two modules with nothing binding them, so a change to the template silently kills the FR-013 warning — the failure mode `a-rule-is-expressed-as-a-check` exists to prevent. | Have T011 read the placeholder from a shared constant beside the template in `_session.py`. |
| E3 | Coverage gap | MEDIUM | `tasks.md` T022; `spec.md` FR-006, SC-003 | "A continued stop never relaxes the quote gate" is the invariant `contracts/start-session-step-9.md` lists first, and its only verification is `quickstart.md` half 3 by hand (T022). The row-level check that pins every other cell can reach it, and does not. | Add a third assertion to T002: row three's condition still selects an ask, and row one's condition requires a named first action rather than a stop kind alone. |
| B1 | Ambiguity | LOW | `spec.md` FR-014; `contracts/wfctl-end.md` § Console output | FR-014 says "*continued* is the canonical term … No other word names the same thing", with no carve-out. The one user-facing line the feature adds reads `✓ Session stopped, not finished`. The contract justifies the wording (it is the issue's own title, and it states what was recorded rather than a verdict on the work), but the requirement as phrased forbids it. | Leave the console line. Note the exception on the pull request rather than editing `spec.md`; `/speckit.analyze` is read-only on it. |
| E4 | Coverage gap | LOW | `spec.md` FR-003, FR-010, FR-014 | Three requirements carry no task. FR-003 (survives a context reset) falls out of storing the mark in `events.jsonl` and is asserted by nothing directly; FR-010 (names no agent) and FR-014 (canonical term) are review properties the plan's Constitution Check covers. | Accept. A grep for `recycle`/`unfinished`/`interrupted` would cover FR-010 and FR-014 cheaply if a reviewer wants one. |
| F3 | Inconsistency | LOW | `tasks.md` § Format, T017, T019, T020 | The Format section requires "Exact file paths in every description"; three tasks name none. | Fixed — all three now name `tests/test_session_stopped_not_finished.py`. |
| C3 | Underspecification | LOW | `tasks.md` T017, T019 | `pytest -k log` collects 32 tests across `test_tracker.py` and `test_worktree_guard.py`; `-k status` collects 57. Both select the intended tests and a good deal else. | Accept, or name the module once it exists. |

## Coverage Summary

| Requirement | Has task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 distinguishable record | yes | T008, T009 | yes | `tests/test_session_stopped_not_finished.py` |
| FR-002 handoff under same rules | yes | T008 | yes | write-once + kept-file report |
| FR-003 survives a context reset | no | — | indirect | E4 |
| FR-004 continued + quotable → carry on | yes | T002, T004 | yes | row assertion |
| FR-005 finished → ask | yes | T002, T004, T022 | yes | both halves |
| FR-006 no quote → ask | yes | T022 | manual only | E3 |
| FR-007 most recent wins | yes | T003, T016 | weak | C1, C2 |
| FR-008 every stop retained | yes | T015 | yes | |
| FR-009 a person can mark it | yes | T010 | yes | |
| FR-010 names no agent | no | — | review | E4 |
| FR-011 omitting → finished | yes | T008 | yes | |
| FR-012 reaches every repo | yes | T003, T004, T021 | yes | edit lands in `wfctl/agents/` |
| FR-013 warns on an unfilled handoff | yes | T011 | yes | F2 on where the literal lives |
| FR-014 canonical term | no | — | review | B1, E4 |
| FR-015 status unchanged | yes | T019 | yes | |
| SC-001 zero human inputs | yes | T022 | manual | half 1 |
| SC-002 finished always asks | yes | T002, T022 | yes | half 2 |
| SC-003 never an inferred action | yes | T022 | manual only | E3 |
| SC-004 N interruptions report N | yes | T015 | yes | |
| SC-005 existing readers unchanged | yes | T013, T020 | partial | E2 |

## Constitution Alignment

No `.specify/memory/constitution.md` in this repository. `plan.md` substitutes
the gates from `AGENTS.md` and the accepted records under `docs/architecture/`,
and records the substitution in Complexity Tracking as the template requires.
Checked against the ten accepted records `wfctl arch context` projects: no
requirement, plan element or task conflicts with one. `layer-model`,
`no-hardcoded-agent` and `session-state-is-re-derived` are each named by a task
that lands where the record requires.

## Unmapped Tasks

None that are orphans. T001 (baseline), T021 (install from the working tree) and
T023 (definition of done) map to no single requirement by construction — they
are the repo's gates, and `quickstart.md` carries them.

## Verification Gaps

- FR-006 / SC-003 — manual only (E3).
- FR-007 — the routing half is verified by nothing automated (C1, C2).
- SC-005 — two of three readers unverified by T020's command (E2).
- Step 4's new table — unreachable by the module named to verify it (C1).

## Metrics

- Total requirements: 20 (15 FR, 5 SC)
- Total tasks: 23
- Requirement-to-task coverage: 85% (17 of 20 with ≥1 task)
- Ambiguity count: 1
- Duplication count: 0
- Critical issues: 0
- High: 4 · Medium: 3 · Low: 4

## Next Actions

No CRITICAL finding, so nothing blocks `/speckit.decompose`. Four HIGH findings
are all defects in `tasks.md` that would surface as a red merge gate with no
owner — F1, E1, C1 and E2 are mechanical and were applied. C2, F2, E3 and F3
were applied in the same pass. B1, E4 and C3 stand, with reasons recorded in the
scan file.
