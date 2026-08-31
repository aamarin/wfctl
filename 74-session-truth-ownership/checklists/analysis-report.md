# Specification Analysis Report: session truth ownership

**Date**: 2026-08-30 · **Artifacts**: spec.md, plan.md, tasks.md (+ research.md,
data-model.md, contracts/, quickstart.md) · **Constitution**: none in repo; gates
substituted in plan.md and logged in Complexity Tracking.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| C1 | Coverage gap | HIGH | spec.md FR-010; data-model.md `PipelineReport`; tasks.md T003-T008, T015 | `PipelineReport` is specified as the one structure carrying steps, current, next command and `session_started` — no task builds it. T004 returns step dicts, T008 adds a separate existence read, T015 sources the next command from `next_step_content` at the call site. The requirement's whole point (one structure, not two reads) is unverified. | Add a Foundational task constructing `PipelineReport`, and make T015 and T022 read from it rather than from separate calls |
| C2 | Inconsistency | HIGH | tasks.md T029; spec.md Assumptions; design.md Out of scope | T029 deletes `load_agentconfig`, which both the spec and the design explicitly place out of scope. One of the three is wrong. | Either drop T029 and file it separately, or amend the spec's Assumptions — do not leave a task contradicting its own spec |
| C3 | Underspecification | HIGH | tasks.md T026 | The test as written ("no module but `cli.py` contains `● ▶ ○ –`") fails today for reasons it does not intend: 31 glyph occurrences across `_pipeline.py`, `cli.py` and `_verify.py`, most of them in comments explaining semantics, plus `_verify.py`'s own unrelated output. | Restate T026 to assert on *values* — nothing returned by `steps_display` or stored on a step is a glyph — not on source text |
| C4 | Coverage gap | MEDIUM | spec.md FR-011; tasks.md T007, T017 | FR-011 says removing the session file must not reduce what any command reports. Tasks assert rendered lines per state, which is narrower: a field that vanished without a rendering to change is not caught. | Add an assertion enumerating the fields the removed file carried and where each is now answered |
| C5 | Coverage gap | MEDIUM | spec.md SC-002; tasks.md T014 | "Zero values originate from a file written by an earlier session" has no direct check; T014 covers re-derivation but not provenance. | Accept as covered-by-construction once C1 lands (one structure, computed per read), or add an explicit test |
| C6 | Inconsistency | MEDIUM | tasks.md Phase 4 Verification block vs T023 | The block names `tests/test_agent_session.py`; the story's tests land in `tests/test_end_reports_observations.py`. A reader running the named command verifies the wrong story. | Point the Verification block at the file T023 creates |
| C7 | Ambiguity | MEDIUM | spec.md FR-011 | "MUST NOT reduce what any command reports" has no measurable form. | Restate as the field-by-field claim in C4's recommendation |
| C8 | Terminology drift | LOW | spec.md vs data-model.md, contracts/, tasks.md | The spec says "resume-point file" and "session state file"; every downstream artifact says `current.md` and `current.json`. | Intentional — the spec avoids implementation names. Leave, or add the mapping once in data-model.md |
| C9 | Weak verification | LOW | tasks.md T001 | The fixture's verification runs a test file that does not yet use the fixture, so it proves nothing about T001. | Verify T001 by the first test that consumes it (T005) |

## Coverage Summary

| Requirement | Has task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 | yes | T011, T014, T016 | yes | |
| FR-002 | yes | T011-T014 | yes | |
| FR-003 | yes | T011, T012, T014, T018 | yes | |
| FR-004 | yes | T015, T017 | yes | |
| FR-005 | yes | T016, T017 | yes | |
| FR-005a | yes | T005, T016, T017 | yes | |
| FR-006 | yes | T021-T023 | yes | |
| FR-007 | yes | T013, T014 | yes | |
| FR-008 | yes | T021, T023, T024 | yes | |
| FR-009 | yes | T003-T006, T026 | partial | C3 — the guard test does not work as written |
| FR-010 | **no** | — | no | C1 |
| FR-011 | partial | T007, T017 | weak | C4, C7 |
| FR-012 | yes | T018 | yes | |
| SC-001 | yes | T014 | yes | |
| SC-002 | partial | T014 | weak | C5 |
| SC-003 | yes | T017 | yes | |
| SC-004 | yes | T023 | yes | |
| SC-005 | yes | T018 | yes | |

## Constitution alignment

No constitution file. plan.md substitutes gates from `AGENTS.md` and the two
accepted/proposed records, and records the substitution. All five substituted
gates map to tasks: validation (T002, T010, T020, T025, T028, T032), complexity
(no new dependency or surface in any task), ownership (records, not re-decided),
config untouched (no task edits `pyproject.toml`), skills exercised (T019, T024,
T030).

## Unmapped tasks

- T001, T002 — setup and gate, expected.
- T029 — maps to nothing in the spec, and contradicts it. See C2.
- T030, T031, T032 — polish and gates, expected.

## Verification gaps

- FR-010: no task, therefore no verification (C1).
- FR-009: task exists, guard test is unworkable as specified (C3).
- FR-011, SC-002: verification is narrower than the claim (C4, C5).

## Metrics

- Total requirements: 18 (13 FR, 5 SC)
- Total tasks: 32
- Coverage: 15/18 fully covered (83%), 3 partial, 1 with no task
- Ambiguity findings: 1
- Duplication findings: 0
- Critical issues: 0
- High issues: 3

## Remediation applied — 2026-08-30

The findings above are the state at analysis time; this section records what was
done about them. Nothing in the table was edited.

| ID | Action |
| --- | --- |
| C1 | T009a builds `PipelineReport`; T009b asserts its invariant; T015 and T022 now read the position and next command from it rather than calling separately |
| C2 | T029 removed. Both `spec.md` and `design.md` scope `load_agentconfig` out; deleting it belongs to its own issue |
| C3 | T026 restated to assert on values returned by inference. The glyphs in `_pipeline.py` comments and in `_verify.py` are legitimate, and a grep-based test would fail for reasons it does not mean |
| C4 | T017a added: a field-coverage test naming each field the removed files carried and where each is now answered |
| C5 | Covered by C1 and C4 — one structure computed per read, and a test that names each field's new source |
| C6 | Phase 4's Verification block now names `tests/test_end_reports_observations.py` |
| C7 | FR-011 restated in `spec.md` as the field-by-field claim, which is checkable |
| C8 | `data-model.md` gained a Naming section mapping the spec's terms to the two filenames |
| C9 | T001 is verified by T005, the first test that consumes the fixture |

Task count moved 32 → 34. Coverage after remediation: 18/18 requirements have at
least one task, and FR-009, FR-010 and FR-011 each have a verification that tests
the claim rather than a proxy for it.
