# Delivery Plan: install-skills source (146)

**Feature**: `146-install-skills-source` | **Date**: 2026-09-05
**Source**: `<spec_root>/146-install-skills-source/tasks.md` (29 tasks, revision 2)
**Parent issue**: #146

---

## File-touch matrix

| Task(s) | File | Action |
|---|---|---|
| T002 | `tests/test_bundle.py` | MODIFY |
| T003 | `wfctl/_bundle.py` | MODIFY — add `resolve_root` |
| T005–T011, T018, T019, T023 | `tests/test_install_skills.py` | MODIFY |
| T012–T016, T020, T024 | `wfctl/cli.py` | MODIFY — `install_skills_cmd`, `doctor_cmd` |
| T021 | `wfctl/agents/skills/start-session/SKILL.md` | MODIFY |
| T028 | `docs/architecture/drift-is-measured-against-the-recorded-source.md` | MODIFY (already written, untracked) |
| T001, T004, T017, T022, T025, T026, T027, T029 | — | READ ONLY (gates, manual checks) |

**Six files.** Size **M**.

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| one PR | T001–T029 | `wfctl/_bundle.py` (mod), `wfctl/cli.py` (mod), `wfctl/agents/skills/start-session/SKILL.md` (mod), `tests/test_bundle.py` (mod), `tests/test_install_skills.py` (mod), `docs/architecture/drift-is-measured-against-the-recorded-source.md` (mod) | M | T029 green — three `verify` commands plus `wfctl doctor` — and `quickstart.md` run through step 8 |

**Rationale**: Single PR. Three of the four boundary signals say bundle, and the
fourth is not strong enough to override them.

| Signal | Reading |
|---|---|
| File conflict risk | **Bundle.** Seven tasks across all three stories edit `wfctl/cli.py`, five of them in `install_skills_cmd` and `doctor_cmd` specifically. Splitting by story would put concurrent edits in the same two functions. |
| Reviewability | **Bundle.** `doctor` has four reachable states and a reviewer needs all of them to judge any one. US2's remedy line is meaningless without US1's record; US3's warning is a branch in the loop US1 builds. |
| Mergeable increment | **Split candidate.** US1 alone (T001–T017) is genuinely mergeable and testable — the MVP boundary tasks.md already names. US2 and US3 are not. |
| Story independence | **Bundle.** Established at analyze (finding I1) and now stated in spec.md: US2 and US3 read a record only US1 writes. They are not independent. |

The one split signal argues for `US1 | US2+US3`, which would be two PRs against
the same two functions, the second of which exists only to finish states the
first half-built. At M size that trades a reviewable whole for a merge conflict.

**PR closes**: `Closes #146`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #146 | T001–T029 | `install-skills has one hardcoded source, so a branch, a PR, and a hand-placed skill are all unreachable` | M | the single PR above |

**Grouping pattern**: Single issue.
**Rationale**: One PR delivers the whole feature, and #146 already exists as the
issue the branch is named for — no issue needs creating, and one PR closes
exactly one issue.

**Scope note.** #146's title names three unreachable things; this PR delivers two
of them. The hand-placed-skills half was split out during brainstorming
(decision 5) after the finding that two of its three bullets already hold — see
`design.md` *Not Doing*. **That split issue does not exist yet.** It should be
opened before this PR closes #146, so the surviving bullet — `doctor`'s abandoned
scan reporting an unrecorded, untracked skill directory — is not lost with the
issue that carried it.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | Baseline green. No edits. |
| 1 | Sequential | T002 | Foundational tests, written to fail. |
| 2 | Sequential | T003 → T004 | `resolve_root`, then the phase gate. Blocks everything below. |
| 3 | Parallel | T005 ‖ T006 ‖ T007 ‖ T008 ‖ T009 ‖ T010 ‖ T011 | Seven test functions. Parallel as authoring work only — all land in `tests/test_install_skills.py` and are committed together. Confirm each fails before Wave 4. |
| 4 | Sequential | T012 → T013 → T014 → T015 → T016 | Overlapping regions of `install_skills_cmd` and `doctor_cmd`. Not parallelizable despite being one phase. |
| 5 | Sequential | T017 | US1 merge gate. **MVP reached here.** |
| 6 | Parallel | T018 ‖ T019 ‖ T021 | T018/T019 are test functions; T021 is a different file entirely (`start-session/SKILL.md`) and needs no code from Wave 7. |
| 7 | Sequential | T020 → T022 | US2 implementation, then its gate. |
| 8 | Sequential | T023 → T024 → T025 | US3: test, implementation, gate. |
| 9 | Parallel | T026 ‖ T028 | Help-text check and the record's `Log` line. Independent of each other. |
| 10 | Sequential | T027 | `quickstart.md`, all eight steps. Manual, and needs everything above. |
| 11 | Sequential | T029 | Final gate: three `verify` commands plus `wfctl doctor`. |

All 29 tasks are assigned to exactly one wave.

**Single-agent order** (recommended for this feature):

T001 → T002 → T003 → T004 → T005–T011 → T012 → T013 → T014 → T015 → T016 →
T017 → T018 → T019 → T021 → T020 → T022 → T023 → T024 → T025 → T026 → T028 →
T027 → T029

---

## Agent Fanning Instructions

**Single agent recommended, despite the M size.** The wave table shows real
parallelism in only three places, and none of it is worth a second agent:

- **Wave 3** is seven test functions in one file. Two agents editing
  `tests/test_install_skills.py` concurrently would spend more on merge than the
  authoring saves.
- **Wave 6** has one genuinely independent task — T021, the skill prose, in its
  own file. One task is not a fan-out.
- **Wave 9** is two read-only checks that take under a minute together.

The feature's real shape is a chain: `resolve_root` blocks the record, the record
blocks every `doctor` state, and the states are three branches in one loop. That
is a sequential feature with a parallel-looking phase structure, and the honest
delivery plan says so rather than manufacturing agents for it.

**Fan-in gates**: `uv run --frozen --extra dev pytest -q tests/test_bundle.py`
(after Wave 2), then `... pytest -q tests/test_install_skills.py tests/test_bundle.py`
(after Waves 5, 7 and 8), then the full `verify` set plus `wfctl doctor` (Wave 11).
