# Delivery Plan: version check — default branch and fork (21)

**Feature**: `21-version-check-master-and-fork` | **Date**: 2026-08-17
**Source**: `specs/21-version-check-master-and-fork/tasks.md` (26 tasks)
**Parent issue**: #21

---

## File-Touch Matrix

Four distinct files. Grouped by file rather than by task, because the
concentration is the whole story here.

| File | Tasks | Kind |
| --- | --- | --- |
| `wfctl/cli.py` | T004, T006, T009, T010, T015, T016, T019, T024 | modified — **all eight inside `_check_wfctl_version` or its immediate helpers** |
| `tests/test_doctor_version.py` | T002, T003, T005, T008, T012, T013, T014, T018, T023 | created (T002), then appended |
| `tests/test_install_skills.py` | T006, T020, T023 | modified |
| `README.md` | T022 | modified |
| — | T001, T007, T011, T017, T021, T025, T026 | read-only: baseline capture, gates, manual verification |

**Size: S** (3–5 files) → single PR, single issue, per the sizing table.

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
| --- | --- | --- | --- | --- |
| 1 (unnumbered) | T001–T026 | `wfctl/cli.py` (modified), `tests/test_doctor_version.py` (created), `tests/test_install_skills.py` (modified), `README.md` (modified) | S | T026 green: `pytest && ruff check && mypy`, plus a live `wfctl doctor` showing the drift block |

**Rationale**: Single PR. All four boundary signals point the same way.

1. **File conflict risk — bundle.** Eight of the implementation tasks edit the *same function*. Sequenced in one branch this is trivial; split across concurrent PRs it is eight rebases of the same fifty lines.
2. **Reviewability — bundle.** `data-model.md` E3 is one decision table: release verdict, branch verdict, suppression, warning composition. A reviewer handed "the drift block" without "what suppresses it" or "what happens when a query fails" is reviewing a partial state machine and cannot judge correctness.
3. **Mergeable increment — split possible but not required.** US1 alone would genuinely work: the skip rules land in Phase 2 with `_installed_build()`, so a pinned or editable install is already handled before US1 renders anything. This is the one signal that permits a split, and it is what the MVP path in `tasks.md` describes.
4. **Story independence — bundle.** US1/US2/US3 have separate acceptance criteria but share one runtime path and one function. They are three aspects of one behavior, not three behaviors.

Three of four say bundle; the fourth permits but does not require a split. Default holds.

**PR closes**: `Closes #21`

### Exactly one close line — this matters here

This branch's work touches three issues. Only one may be closed by the PR.

| Issue | Relationship | PR should |
| --- | --- | --- |
| **#21** | The feature. Fully satisfied by this PR. | `Closes #21` |
| **#35** | B1 (fork targeting) is satisfied by FR-009 + FR-012. A1 remains open, and the A2/A3 obsolescence call is still yours. | Reference only — "addresses #35 B1". **Never** `Closes #35`. |
| **#41** | This is PR B of two. PR A (#36, #31, #38) has not landed. | Reference only — "PR B of #41". **Never** `Closes #41`. |

Closing #35 or #41 from this PR would silently discard tracked, unfinished work
in both.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
| --- | --- | --- | --- | --- |
| #21 | T001–T026 | `[21] doctor reports 'latest' against release tags only, hiding merged-but-unreleased work` | ~4h | PR 1 |

**Grouping pattern**: Single issue.
**Rationale**: One PR delivers the whole feature, and #21 already exists as the
branch's named issue — no issue is created here. Splitting into per-story issues
would produce three issues closed by one PR, which the one-PR-one-issue rule
forbids outright.

---

## Parallelization Waves

Waves follow the phase structure, because the phases *are* the dependency
graph: each ends in a gate that the next depends on.

| Wave | Mode | Tasks | Gate / Notes |
| --- | --- | --- | --- |
| 0 | Sequential | T001 | Baseline capture. Must precede any edit or the evidence is gone. |
| 1 | Mixed | T002 → (T003 ‖ T005) → T004 → T006 → **T007** | T002 creates the module the rest append to. T004 and T006 both edit `cli.py` — sequential. Gate: T007. |
| 2 | Sequential | T008 → T009 → T010 → **T011** | All of T009/T010 edit the same function. Gate: T011. |
| 3 | Mixed | (T012 ‖ T013 ‖ T014) → T015 → T016 → **T017** | Test authoring first, then two sequential `cli.py` edits. Gate: T017. |
| 4 | Sequential | T018 → T019 → T020 → **T021** | T020 must precede T021: T019 invalidates an assertion in `test_install_skills.py` and T021 runs the full suite. |
| 5 | Mixed | (T022 ‖ T023) → T024 → T025 → **T026** | T022/T023 are genuinely independent files. T024 rewrites returns the earlier waves added. T025 needs a real install. |

**Every task appears in exactly one wave.** 26 assigned, 26 accounted for.

### Honest note on the parallel markers

The `‖` pairs within waves 1, 3, and 5 are weaker than they look. Only
**T022 ‖ T023** is parallel by the strict rule (different files, no shared
state). The test-authoring groups — T003/T005, T012/T013/T014 — all append to
`tests/test_doctor_version.py`. Append-only edits to one file conflict rarely
but not never, and they share fixtures.

For a single implementer this is moot: the recommended path is straight through.
The wave table exists to record the dependency structure and the gates, not to
promise speedup that a one-function feature cannot deliver.

**Single-agent order** (recommended):
T001 → T002 → T003 → T005 → T004 → T006 → T007 → T008 → T009 → T010 → T011 →
T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022 →
T023 → T024 → T025 → T026

---

## Agent Fanning Instructions

Single agent recommended. This is an S-size feature whose implementation is
eight edits to one function; fanning agents across it would spend more time
resolving conflicts in `_check_wfctl_version` than the work itself takes.

The wave table above is provided for dependency reference and for the gates,
which are the parts worth honouring regardless of who implements.

---

## Notes for the implementer

- **Stop at the T011 gate and evaluate.** That is the MVP boundary: issue #21's acceptance criterion is met there. If the remaining stories need to become their own PR for any reason, T011 is the only clean cut point in this plan.
- **T025 cannot run before merge.** It verifies the printed reinstall command against the real HTTPS origin, which requires an installed build. It carries its own remediation branch if `--force` proves insufficient there.
- **The two silent-failure traps** are recorded in `tasks.md` Notes: a test missing `@pytest.mark.real_version_check` exercises conftest's stub and proves nothing, and a stale `_fake_ls_remote_tags` makes existing tests pass through the wrong code path. Both produce green suites.
