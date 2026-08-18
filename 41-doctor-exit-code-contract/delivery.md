# Delivery Plan: doctor exit-code contract (41)

**Feature**: `41-doctor-exit-code-contract` | **Date**: 2026-08-17
**Source**: `41-doctor-exit-code-contract/tasks.md` (32 tasks)
**Parent issue**: #41

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| PR A | T001–T031 | `wfctl/cli.py` (modified), `wfctl/agents/configs/workmux/.workmux.yaml` (modified), `tests/test_install_skills.py` (modified), `tests/test_remaining_commands.py` (modified), `tests/test_workmux.py` (modified), `tests/test_bundle.py` (modified), `tests/test_pipeline_commands.py` (created) | M (7 files) | `uv run --frozen --extra dev pytest -q`, `ruff check .`, and `mypy` all green; `wfctl doctor` exits 0 in this repository |

**Rationale**: Single PR. All four boundary signals agree:

1. **File conflict risk** — eight tasks edit `wfctl/cli.py`. They are sequenceable
   within one branch; splitting means two branches editing the same function.
2. **Reviewability** — the deletion, the three `-> bool` conversions, and the two
   new checks are one decision wearing four issue numbers. A reviewer assessing
   whether the contract is right needs to see every adopter of it.
3. **Mergeable increment** — no subset merges cleanly. Converting two of three
   checks leaves the contract half-applied, which is the ambiguity the feature
   exists to remove.
4. **Story independence** — US1, US2, and US3 share `cli.py` and the exit-code
   path. Only US4 is genuinely independent, and it is one new test file; splitting
   it out would trade a 40-line PR for a second review cycle.

**PR closes**: `Closes #41`

#41's title — "one exit-code contract, and the checks that belong in it" — is PR A
exactly. The PR B work it also mentions (#21 + #35 B1, the version-check rewrite)
is explicitly held out by #41 itself and carries its own issues, so nothing goes
untracked when #41 closes here.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #41 | T001–T031 | `[41] doctor: one exit-code contract, and the checks that belong in it` | ~4h | PR A |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the whole feature, so one issue closes with it — the
default for M-size work, and the only pattern that keeps "one PR closes exactly one
issue" true.

### Child issue reconciliation

#41 is a parent. Three children are touched to different degrees, and the PR closes
none of them — closing multiple issues from one PR is what this rule exists to
prevent. Reconcile by hand at merge:

| Issue | State after PR A | Action at merge |
|-------|------------------|-----------------|
| #31 | **Fully delivered.** T024–T027 satisfy every acceptance criterion, via the test route rather than the doctor-check route the issue proposed — the vendoring made that possible. | Close, with a comment noting the route changed and why. |
| #36 | **Partially delivered.** One deletion (`_check_stale_archive_hook`) landed. Its items 1–2, annotating each remaining check with a removal condition, are deferred. | Comment naming what landed; leave open. |
| #38 | **Partially delivered.** The reporting surface landed. The install-time diff of `prior_items` against paths just written — the half that prevents orphans rather than reporting them — is out of scope here. | Comment naming what landed; leave open. |

Left unreconciled, #31 is exactly the "likely done" drift `/start-session` flags:
an open issue whose work the commits already complete.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | Baseline: 395 passing, ruff and mypy clean. **Done.** |
| 1 | Sequential | T002 → T003 → T004 → T005 → T006 | US2. Template fix before its test, test before the revert-and-confirm. **Done.** |
| 2 | Sequential | T007 → T008 → T009 | Deletion and its test removals. Gated on T002: while the shipped template names the old command, the check has a live consumer. |
| 3 | Coordinate | T010, T011, T012 | Three `-> bool` conversions. Not parallel — all edit `wfctl/cli.py`, and T013 consumes all three. Draft together, type-check together. |
| 4 | Sequential | T013 | OR into `exit_code`; records the contract. The fan-in point for Wave 3. |
| 5 | Parallel | T014 ‖ (T015 → T016 → T016a) | T014 edits `test_remaining_commands.py`; the rest edit `test_install_skills.py`. Different files, no shared state. |
| 6 | Sequential | T017 → T018 | FR-013 boundary grep, then the Phase 4 merge gate. |
| 7 | Sequential | T019 → T020 | US3 implementation. Needs the contract from T013. |
| 8 | Sequential | T021 → T022 → T023 | US3 tests, repository check, merge gate. |
| A | Parallel with 2–8 | T024 → T025 → T026 → T027 | **US4. Depends on nothing.** New test file, no production code, cannot conflict. Runnable at any point including first. |
| 9 | Parallel | T028 ‖ T029 | Docstring and the offline-I/O audit. Different files. |
| 10 | Sequential | T030 → T031 | Full gate set, then `wfctl doctor` in this repository. |

**Single-agent order** (recommended — see fanning note below):
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 →
T012 → T013 → T014 → T015 → T016 → T016a → T017 → T018 → T019 → T020 → T021 →
T022 → T023 → T024 → T025 → T026 → T027 → T028 → T029 → T030 → T031

---

## Agent Fanning Instructions

**Single agent recommended**, despite this being M-size. The wave table is real,
but the available parallelism is not worth a second agent:

- Waves 2, 3, 4, 7 all serialize on `wfctl/cli.py`. That is 8 of the 24 remaining
  tasks, and they are the substance of the feature.
- The genuinely independent work — Wave A (US4, 4 tasks) and Wave 9 (2 tasks) —
  totals ~50 lines across three files. Coordination overhead exceeds the saving.

**If fanning anyway**, Wave A is the only clean split:

**Agent A prompt:**
```
In the wfctl repository, implement tasks T024–T027 from
41-doctor-exit-code-contract/tasks.md (in the recorded spec root — find it
with `wfctl feature-paths`).

Create tests/test_pipeline_commands.py asserting every _STEP_COMMAND value in
wfctl/_pipeline.py has a matching wfctl/agents/commands/<name>.md in the shipped
bundle. On mismatch, the failure must name the entry and the nearest shipped name
via difflib.get_close_matches.

The assertion is one-way: the bundle ships commands the table does not name
(start-session, code-review, and 13 others) and that is correct. Assert only over
the table's values.

Confirm it catches real drift by temporarily renaming one _STEP_COMMAND entry and
re-running, then restore.

Touch no other file. Verify with:
  uv run --frozen --extra dev pytest tests/test_pipeline_commands.py -q
```

**Fan-in gate after Wave A:** `uv run --frozen --extra dev pytest -q`

---

## Scope Boundary

`_check_wfctl_version` (`wfctl/cli.py`) is not modified by this PR. It is the one
function the separate #21 + #35 B1 work rewrites end to end, and converting its
signature here would edit the exact lines that rewrite replaces. T017 verifies the
boundary held with a grep over the diff.

This is the only coupling between PR A and PR B, and scoping is what keeps them
mergeable in either order.
