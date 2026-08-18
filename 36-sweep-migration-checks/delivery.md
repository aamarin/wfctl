# Delivery Plan: Sweep the one-time migration checks (36)

**Feature**: `36-sweep-migration-checks` | **Date**: 2026-08-17
**Source**: `specs/36-sweep-migration-checks/tasks.md` (27 tasks)
**Parent issue**: #36

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| PR-1 | T001–T025 (all) | `wfctl/cli.py` (modified), `wfctl/_workmux.py` (modified), `wfctl/_archive.py` (modified, comment only), `wfctl/agents/configs/workmux/.workmux.yaml` (modified), `tests/test_workmux.py` (modified), `tests/test_remaining_commands.py` (modified), `tests/test_archive_specs.py` (modified), `tests/test_install_config.py` (modified) | M (8 files; 4 source, 4 test) | `uv run pytest -q && uv run ruff check . && uv run --extra dev mypy` green, orphan grep returns nothing, both bundle scripts pass |

**Rationale**: Single PR. Signal 2 (reviewability) is decisive and points the
opposite way from a split: the entire argument of this change is that reviewing
the five checks *together* is what makes it obvious which are load-bearing and
which are not. A reviewer seeing only the deletions cannot judge whether the
retained paths were correctly retained, and a reviewer seeing only the
announcements cannot judge whether they cover what the deletions removed. Splitting
would reintroduce exactly the one-at-a-time review issue #36 was filed to prevent.

Signal 1 (file conflict) also favours bundling — US1 and US2 both edit
`wfctl/cli.py`, at opposite ends of the file, and are trivially sequenced within
one PR but would conflict across two. Signals 3 and 4 weakly favour a split
(Phase 3 is independently mergeable, and the stories have separate acceptance
criteria), but the default is to bundle and neither signal is strong enough to
override signal 2.

**Scope flag**: 8 files touched sits exactly on the M/L boundary, which the
skill's red-flag list says to surface rather than decide silently. Surfacing it:
the diff is roughly 130 lines net negative, half the files are test files, and
`wfctl/_archive.py` changes by one comment. The reviewability burden is 4 source
files. Recommendation is a single PR; if you would rather split, the natural cut
is US3 (template + its test, 2 files, fully independent) as its own PR under its
own issue — but that needs a second issue opened first, since one PR closes
exactly one issue.

**PR closes**: `Closes #36`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #36 | T001–T025 | `[36] Sweep the one-time migration checks` | ~2.5 h | PR-1 |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the full feature, and issue #36 already exists and
describes exactly this scope. Opening sub-issues for a 130-line subtractive change
would be the issue noise the grouping rules warn against.

**Note on scope drift from the issue text**: #36 as written asks for five checks
to be deleted in one pass. This plan deletes two, retains three, and adds an
observable end condition to the two rescue paths. T025 records that reasoning on
the issue after the PR opens, so the issue and the delivered work agree before
anyone reads #36 as still-pending work.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | Baseline must be green before any edit; T024 compares against it |
| 1 | Parallel | (T002 → T003 → T004) ‖ T018 | Track A walks `cli.py` top-down then `_workmux.py`; Track B is the template. No shared file |
| 2 | Parallel | T005 ‖ T006 ‖ T019 ‖ T007 | Four different files. T007 needs `cli.py` free, so it follows Track A |
| 3 | Parallel | (T008 → T009) ‖ T020 | T008/T009 share `test_remaining_commands.py` — sequential with each other |
| 4 | Parallel | T010 ‖ T021 | US1 and US3 merge gates; both read-only |
| 5 | Sequential | T011 → T012 → T013 | All in `wfctl/cli.py` (T013 also touches `_archive.py`). Same file, must sequence |
| 6 | Sequential | T014 → T015 → T016 → T016a → T016b | All in `tests/test_archive_specs.py`. Same file, must sequence |
| 7 | Sequential | T017 | US2 merge gate |
| 8 | Parallel | T022 ‖ T023 | Independent read-only checks |
| 9 | Sequential | T024 → T025 | Full gate, then the tracker comment once the PR is open |

**Single-agent order** (recommended — see fanning note below):
T001 → T018 → T019 → T020 → T021 → T002 → T003 → T004 → T005 → T006 → T007 →
T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T016a → T016b →
T017 → T022 → T023 → T024 → T025

This order follows the Implementation Strategy's recommendation of US3 → US1 →
US2 rather than phase numbering, so the rename notice begins its observation
window against a codebase that is no longer re-seeding the retired name.

---

## Agent Fanning Instructions

**Single agent recommended**, despite the M sizing. Three of the four source
files funnel through `wfctl/cli.py`, so the wave table's parallelism is mostly
between implementation and its own tests rather than between independent tracks.
Coordination overhead would exceed the ~2.5 h of work.

One genuine two-agent split exists if you want it — US3 is fully independent of
the other two stories, sharing no file:

**Agent B prompt (US3, runs start to finish alongside Agent A):**
```
In the wfctl repo, implement User Story 3 of specs/36-sweep-migration-checks/tasks.md:
tasks T018, T019, T020, T021.

Scope: wfctl/agents/configs/workmux/.workmux.yaml and tests/test_install_config.py
ONLY. Do not touch wfctl/cli.py, wfctl/_workmux.py, wfctl/_archive.py, or any
other test file — another agent owns those.

Retarget both occurrences of `wfctl archive-story` in the bundled template (the
hook line and its explanatory comment) to `wfctl archive-specs`, add a test that a
freshly seeded .workmux.yaml contains zero occurrences of the retired name, then
run the two bundle scripts in .github/scripts/ and the full gate.

Read contracts/cli.md for the install-config guarantees before editing.
```

**Agent A** takes the rest in single-agent order, skipping T018–T021.

**Fan-in gate**: `uv run pytest -q && uv run ruff check . && uv run --extra dev mypy`, plus
the orphan grep from the Phase 3 verification block. Run after both agents report
done, before T022.
