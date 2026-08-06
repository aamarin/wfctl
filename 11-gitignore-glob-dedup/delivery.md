# Delivery Plan: gitignore glob dedup (11)

**Feature**: `11-gitignore-glob-dedup` | **Date**: 2026-08-04
**Source**: `specs/11-gitignore-glob-dedup/tasks.md` (29 tasks)
**Parent issue**: #11

---

## File-Touch Matrix

| Task(s) | File | Operation |
|---------|------|-----------|
| T005, T006, T018, T021, T022 | `wfctl/cli.py` | MODIFY |
| T003, T004, T008–T013, T016, T017 | `tests/test_install_skills.py` | MODIFY |
| T028 | `.gitignore` | MODIFY (one entry: `.wf-skills-backup/`) |
| T014, T019 | `tests/test_install_config.py` | READ ONLY — asserted unchanged |
| T001, T002, T007, T015, T020, T023–T027, T029 | — | READ ONLY / validation |

**Substantive files modified: 2.** `.gitignore` is a single generated entry, not
authored change.

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| TBD | T001–T029 | `wfctl/cli.py` (modified), `tests/test_install_skills.py` (modified), `.gitignore` (modified) | **XS** | `uv run pytest -q && uv run ruff check . && uv run mypy` all green (T029) |

**Rationale**: **Single PR.** All four boundary signals point the same way:

1. **File conflict risk — bundle.** All three user stories append to
   `tests/test_install_skills.py`, and US1 and US3 both modify the same region of
   `wfctl/cli.py`. Splitting would force concurrent edits to both shared files;
   sequencing them inside one PR avoids that entirely.
2. **Reviewability — bundle.** A reviewer cannot assess the guard without its
   tests, and the skip report is unintelligible without the guard's boolean
   return. The three details of T005 (`--no-index`, `capture_output`,
   non-zero-means-append) are each defended by a specific test; separating test
   from implementation would hide that pairing across two reviews.
3. **Mergeable increment — bundle.** US1 alone is genuinely mergeable (it is the
   MVP). US2 alone is not — it tests behavior that would not exist. US3 alone is
   not, for the same reason. Only one of three slices stands alone, so the split
   buys nothing.
4. **Story independence — no.** US2 and US3 both depend on US1's guard existing.
   They share acceptance criteria (the resulting `.gitignore` contents) and the
   same runtime path.

XS sizing (2 substantive files) puts this squarely in the single-PR row of the
sizing table with no judgment call required.

**PR closes**: `Closes #11`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #11 | T001–T029 | `install-skills appends .gitignore lines already covered by an existing glob` | ~1 h (6 lines of source, 10 tests) | PR (single) |

**Grouping pattern**: **Single issue** — and no issue is created by this step.

**Rationale**: Issue #11 already exists and the branch is named for it
(`11-gitignore-glob-dedup`). The whole feature is one XS PR closing that one
issue, which satisfies "one PR closes exactly one issue" exactly. Creating a new
issue here would produce two issues for one PR — the failure mode the rule
exists to prevent.

**Nothing to create.** The verification checklist item "GitHub issues created and
numbered" is satisfied by the pre-existing #11; there is no second deliverable to
track.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 | Baseline capture, no edits. T002 reverts its own `.gitignore` damage. |
| 1 | Sequential | T003 → T004 | US1 tests. **T003 must fail** before Wave 2 — it is the regression test for #11. |
| 2 | Sequential | T005 → T006 → **T007** | The guard. Do not split T005. Gate: `uv run pytest tests/test_install_skills.py`. |
| 3 | Coordinate | T008 ‖ T009 ‖ T010 ‖ T011 ‖ T012 ‖ T013, then T014 → **T015** | Six US2 tests. Logically parallel but **all append to one file** — one agent, or serialize the writes. T014 is read-only [P]. |
| 4 | Coordinate | T016 ‖ T017 → T018 → T019 → **T020** | US3 tests must fail before T018 implements. T019 asserts `cli.py:1134` untouched. |
| 5 | Parallel | T021 → T022, ‖ T023 ‖ T024 ‖ T026 | T021/T022 both edit `cli.py` — sequence those two. Lint, types, and the timing record are independent. |
| 6 | Sequential | T025 → T027 → T028 → **T029** | Full suite, manual quickstart, commit the one legitimate entry, final gate. |

**Every task assigned to exactly one wave.** Count: 2 + 2 + 3 + 8 + 5 + 5 + 4 = 29. ✅

### Why Wave 3 is "Coordinate" and not "Parallel"

T008–T013 touch no shared state and would be textbook `[P]` — except all six
append to `tests/test_install_skills.py`. Fanning six agents at one file produces
merge conflicts, not speed. The `[P]` markers in `tasks.md` record *logical*
independence, which is what matters if the file is ever split; they are not a
fanning instruction here.

**Single-agent order** (recommended for XS):

```
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 →
T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022 →
T023 → T024 → T025 → T026 → T027 → T028 → T029
```

---

## Agent Fanning Instructions

**Single agent recommended.** This is an XS feature: two substantive files, six
lines of source change, and every wave with more than one task is blocked by a
shared file. Fanning would add coordination cost with no wall-clock gain.

The wave table above is provided for reference and template reuse.

---

## Red Flag Check

| Red flag | Status |
|----------|--------|
| File-touch matrix shows 8+ files | ✅ 2 substantive files |
| All tasks in one wave (no parallelism) | ✅ 7 waves |
| Issue count > PR count | ✅ 1 = 1 |
| PR count > issue count | ✅ 1 = 1 |
| `analyze` has CRITICAL issues open | ✅ 0 CRITICAL, 0 HIGH (E1 resolved) |
| `delivery.md` already existed unreviewed | ✅ first write |

---

## Verification Checklist

- [x] `delivery.md` written to `specs/11-gitignore-glob-dedup/delivery.md`
- [x] PR count justified with rationale (single — all four signals agree)
- [x] Issue count equals PR count — 1 issue (#11), 1 PR
- [x] Every task assigned to exactly one wave (29/29, counted)
- [x] GitHub issue exists and is numbered — **#11, pre-existing; none created**
- [x] `Closes #11` references exactly one PR
- [ ] Sub-feature issues linked to parent epic — N/A, no split

---

## Notes for implementation

- **Artifacts are gitignored.** `specs/` and `.agent/` do not survive worktree
  removal except through `wfctl archive-story` (wired into `pre_remove`). Commit
  them deliberately if this branch is going to be reviewed by anyone else.
- **T012 is load-bearing.** It is the only test that fails if `--no-index` is
  removed from the guard. Flagged in `.agent/brief.md` as do-not-delete.
- **T014 is a tripwire, not a task.** If either pre-existing config test needs an
  edit to pass, stop — the change altered behavior it should not have.
