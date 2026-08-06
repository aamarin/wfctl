---
description: 'Task list for 11-gitignore-glob-dedup'
---

# Tasks: gitignore glob dedup

**Input**: Design documents from `/specs/11-gitignore-glob-dedup/`
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [quickstart.md](./quickstart.md)

**Tests**: Required. The defect is a silent, recurring one that hid for months
because nothing asserted on it — a regression test that fails against today's
code is the first task of the MVP phase, not an afterthought.

**Organization**: Grouped by user story. US1 is a complete, shippable fix on its
own; US2 is its no-regression net; US3 adds the skip report.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files or independent test functions)
- **[Story]**: US1, US2, US3 — maps to the user stories in spec.md
- Every implementation task names its verification path

## Path Conventions

Single Python package at the repository root: `wfctl/`, `tests/`. All paths
below are repo-relative.

## Commands

| Purpose | Command |
| --- | --- |
| Targeted tests | `uv run pytest tests/test_install_skills.py tests/test_install_config.py` |
| Full suite | `uv run pytest -q` |
| Lint | `uv run ruff check .` |
| Types | `uv run mypy` |

---

## Phase 1: Setup

**Purpose**: Establish the baseline so "it passed before" is a fact, not a memory.

- [X] T001 Confirm a green baseline before any edit: run `uv run pytest -q` and record the pass count in the commit message or session notes
- [X] T002 Capture the defect as evidence: with a clean tree, run `wfctl install-skills --agent claude`, then `git diff --numstat -- .gitignore` (expect 83 added lines), then `git checkout -- .gitignore` to restore

**Checkpoint**: Baseline green, defect reproduced and reverted.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: None required.

This feature adds no shared infrastructure, no schema, no new module, and no
dependency. The single changed function is reached directly by User Story 1, so
inserting a foundational phase would only defer work that US1 already owns. This
phase is intentionally empty rather than padded.

**Checkpoint**: N/A — proceed directly to Phase 3.

---

## Phase 3: User Story 1 - A new worktree starts clean (Priority: P1) 🎯 MVP

**Goal**: An install stops appending ignore entries that an existing broader
pattern already covers, so a fresh worktree's `git status` is clean.

**Independent Test**: Seed a repo's `.gitignore` with a broad pattern, install,
and confirm the file is byte-identical afterward.

**Verification**:

- Automated: `tests/test_install_skills.py::test_install_skills_skips_glob_covered_paths`, `::test_install_skills_second_run_leaves_gitignore_identical`
- Manual: [quickstart.md](./quickstart.md) — install twice, expect one added line total
- Evidence: `git diff .gitignore` shows only `.wf-skills-backup/`; `git check-ignore -v --no-index .agents/skills/start-session` resolves to the `.agents/` pattern

### Tests for User Story 1 ⚠️ write first, must fail

- [X] T003 [US1] Add `test_install_skills_skips_glob_covered_paths` to `tests/test_install_skills.py`: seed `.gitignore` with `.agents/` and `.specify/`, install, assert no `.agents/skills/*` or `.specify/templates/*` line was appended; verify it FAILS against current code with `uv run pytest tests/test_install_skills.py -k skips_glob_covered`
- [X] T004 [P] [US1] Add `test_install_skills_second_run_leaves_gitignore_identical` to `tests/test_install_skills.py`: install twice, assert `.gitignore` bytes are equal after each; verify with `uv run pytest tests/test_install_skills.py -k second_run`

### Implementation for User Story 1

- [X] T005 [US1] Rewrite the guard in `_ensure_gitignored` at `wfctl/cli.py:633` to consult `git check-ignore -q --no-index <line>` with `cwd=repo_root` and `capture_output=True`, returning `False` when the exit code is 0 and `True` after writing; use a function-local `import subprocess as sp` per the convention at `cli.py:295` and `:695`; verify with `uv run pytest tests/test_install_skills.py -k "skips_glob_covered or second_run"`
- [X] T006 [US1] Update the `_ensure_gitignored` docstring to state the return contract and why the exact-match guard was insufficient, per plan.md § Design; verify by reading — no behavior change, so `uv run pytest -q` must still pass

- [X] T007 [US1] Validate User Story 1 with `uv run pytest tests/test_install_skills.py` — merge gate

**Checkpoint**: US1 green. This alone is a shippable fix for issue #11.

---

## Phase 4: User Story 2 - Repos without broad patterns keep working (Priority: P2)

**Goal**: Prove the guard narrowed *only* the redundant case. Everything ignored
today stays ignored.

**Independent Test**: Install into a repo with no `.gitignore` and confirm one is
created listing every install path.

**Verification**:

- Automated: the six tests below, plus the two pre-existing `test_install_config.py` cases passing unedited
- Manual: none required — fully covered by tests
- Evidence: `uv run pytest tests/test_install_skills.py tests/test_install_config.py` green with zero edits to the existing config tests

### Tests for User Story 2

- [X] T008 [P] [US2] Add `test_install_skills_creates_gitignore_when_absent` to `tests/test_install_skills.py`: delete any `.gitignore`, install, assert the file exists and lists every installed path; verify with `uv run pytest tests/test_install_skills.py -k creates_gitignore_when_absent`
- [X] T009 [P] [US2] Add `test_install_skills_appends_uncovered_paths` to `tests/test_install_skills.py`: seed `.gitignore` with an unrelated pattern (`*.log`), install, assert every install path was appended; verify with `uv run pytest tests/test_install_skills.py -k appends_uncovered`
- [X] T010 [P] [US2] Add `test_ensure_gitignored_handles_directory_form` to `tests/test_install_skills.py`: assert `wt/` and `.wf-skills-backup/` are recognised as covered when their pattern is present but the directory is absent from disk, and appended when it is not; verify with `uv run pytest tests/test_install_skills.py -k directory_form`
- [X] T011 [P] [US2] Add `test_ensure_gitignored_appends_when_not_a_repo` to `tests/test_install_skills.py`: point `WFCTL_REPO_ROOT` at a non-repo directory, assert the line is still written and nothing is printed to stderr (FR-007, FR-008); verify with `uv run pytest tests/test_install_skills.py -k not_a_repo`
- [X] T012 [P] [US2] Add `test_install_skills_skips_tracked_path_covered_by_pattern` to `tests/test_install_skills.py`: create `.agents/skills/test-skill/SKILL.md`, `git add -f` and commit it (a plain `add` refuses once `.agents/` is ignored), seed `.gitignore` with `.agents/`, install, assert the path was not appended (FR-006). This is the only test that defends `--no-index` — without the flag it fails, because a tracked path reports "not ignored" even when a pattern matches. Verify with `uv run pytest tests/test_install_skills.py -k tracked_path`
- [X] T013 [P] [US2] Add `test_install_skills_appends_after_missing_trailing_newline` to `tests/test_install_skills.py`: write `.gitignore` as `*.log` with no trailing newline, install, assert `*.log` survives intact as its own line and the first appended entry is on a separate line; verify with `uv run pytest tests/test_install_skills.py -k missing_trailing_newline`
- [X] T014 [US2] Run the two pre-existing config tests unedited — `test_seed_writes_workmux_and_gitignores_wt` and `test_gitignore_no_duplicate_when_present`; verify with `uv run pytest tests/test_install_config.py`. If either needs an edit to pass, stop: the change altered behavior it should not have.

- [X] T015 [US2] Validate User Story 2 with `uv run pytest tests/test_install_skills.py tests/test_install_config.py` — merge gate

**Checkpoint**: US2 green, existing config tests unedited.

---

## Phase 5: User Story 3 - A genuinely new artifact is surfaced for review (Priority: P3)

**Goal**: Report how many entries were skipped, so "nothing needed writing" is
distinguishable from "the step never ran".

**Independent Test**: Install where some entries are covered and confirm the
count appears; install where none are and confirm silence.

**Verification**:

- Automated: the two tests below
- Manual: [quickstart.md](./quickstart.md) — expect `83 ignore entries already covered`
- Evidence: skipped count plus lines in the diff account for every entry the install considered (SC-007)

### Tests for User Story 3

- [X] T016 [P] [US3] Add `test_install_skills_reports_skipped_count` to `tests/test_install_skills.py`: seed a covering pattern, install, assert the CLI output names the number skipped; verify with `uv run pytest tests/test_install_skills.py -k reports_skipped_count`
- [X] T017 [P] [US3] Add `test_install_skills_silent_when_nothing_skipped` to `tests/test_install_skills.py`: install into a repo with no covering patterns, assert no skip line appears in the output (FR-012); verify with `uv run pytest tests/test_install_skills.py -k silent_when_nothing_skipped`

### Implementation for User Story 3

- [X] T018 [US3] Replace the three separate calls at `wfctl/cli.py:929-932` with one loop over `(_MANIFEST_PATH, f"{_BACKUP_DIR}/", *gitignore_targets)` that counts falsy returns, then print the count with `console.print` only when non-zero, placed immediately before the existing backup notice at `:934`; verify with `uv run pytest tests/test_install_skills.py -k "reports_skipped_count or silent_when_nothing_skipped"`
- [X] T019 [US3] Confirm `wfctl/cli.py:1134` (`install-config`'s `wt/`) is left unedited — the bool return is ignorable; verify with `git diff wfctl/cli.py` showing no change at that line and `uv run pytest tests/test_install_config.py` green

- [X] T020 [US3] Validate User Story 3 with `uv run pytest tests/test_install_skills.py tests/test_install_config.py` — merge gate

**Checkpoint**: US3 green, skip report behaving in both directions.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T021 [P] Add the `ponytail:` marker inside `_ensure_gitignored` naming the per-path cost (~12 ms), the trigger (issue #1 removing the runtime clone), and the replacement (`git check-ignore --stdin` over the already-collected `gitignore_targets`); verify with `rg -n "ponytail:" wfctl/cli.py` returning two markers
- [X] T022 [P] Add the inline comments explaining why `--no-index` and `capture_output` are load-bearing, per research.md §D2 and §D3; verify by reading — a future reader must not be able to "simplify" either away, and T012 is the test that fails if they do
- [X] T023 [P] Run `uv run ruff check .` — zero findings
- [X] T024 [P] Run `uv run --extra dev mypy` — zero findings, including the new `bool` return annotation. (CI runs a bare `uv run mypy` at `.github/workflows/ci.yml:95`, but only after `uv sync --extra dev`; locally the extra must be named or mypy is not installed.)
- [X] T025 Run the full suite with `uv run pytest -q` and compare the pass count against the T001 baseline — expect baseline plus the ten new tests, zero failures
- [X] T026 Record the coverage-check cost for SC-006: in a scratch repo, time 50 `_ensure_gitignored` calls and note ms/call in the PR description. Do **not** assert a wall-clock budget in CI — at ~12 ms/call a 1.5 s budget is ~2× the measured cost, close enough that a shared runner flakes, and a flaky test gets deleted. SC-006 exists to catch an order-of-magnitude regression, not jitter. Flag for review if ms/call exceeds ~25 ms.
- [X] T027 Execute the manual path in [quickstart.md](./quickstart.md) end to end: clean tree → `wfctl install-skills --agent claude` → `git diff .gitignore` shows exactly one added line (`.wf-skills-backup/`) with an `83 skipped` notice → confirm 83 + 1 = the 84 entries considered → run again → still one line
- [X] T028 Commit `.wf-skills-backup/` to `.gitignore` as the one legitimate new entry, separate from the code commit so the fix and its first output are distinguishable in history

- [X] T029 Validate the whole feature with `uv run pytest -q && uv run ruff check . && uv run mypy` — merge gate

**Checkpoint**: feature complete, all three CI gates green.

---

## Dependencies

```text
Phase 1 (Setup)
    │
    ▼
Phase 3 (US1) ──── the guard. Everything else builds on it.
    │
    ├──▼ Phase 4 (US2)  no-regression tests — test-only, no source change
    │
    └──▼ Phase 5 (US3)  skip report — needs US1's bool return
             │
             ▼
        Phase 6 (Polish)
```

- **US1 blocks US2 and US3.** Both assert against guard behavior that does not
  exist until T005 lands.
- **US2 and US3 are independent of each other** and can proceed in parallel once
  US1 is green. US2 touches only test files; US3 is the only story that edits
  `cli.py` a second time.
- **Phase 2 is empty** and imposes no ordering.

## Parallel execution examples

**Within US1** — T003 and T004 are separate test functions in the same file;
write T003 first (it must fail), then T004 alongside it.

**Within US2** — T008 through T013 are six independent test functions:

```bash
# all six can be written concurrently, then:
uv run pytest tests/test_install_skills.py -k "creates_gitignore_when_absent or appends_uncovered or directory_form or not_a_repo or tracked_path or missing_trailing_newline"
```

**Within US3** — T016 and T017 in parallel, then T018 makes both pass.

**Within Phase 6** — T021, T022, T023, T024 are fully independent:

```bash
uv run ruff check . & uv run mypy & wait
```

**Across stories** — after T007 (US1 merge gate) is green, US2 and US3 can be
worked simultaneously by different agents; they share no file except
`tests/test_install_skills.py`, so coordinate on that one or sequence the test
additions.

## Implementation strategy

**MVP = Phase 1 + Phase 3 (US1).** Seven tasks, T001-T007. That is a complete,
correct, shippable fix for issue #11: the redundant lines stop being written and
a regression test proves it. Everything after is hardening and ergonomics.

**Increment 2 = Phase 4 (US2).** Test-only. Buys confidence that the narrowing
did not go too far. No source change, so it cannot break the MVP.

**Increment 3 = Phase 5 (US3).** The skip report. Genuinely optional — the fix
works without it — but it is what makes the change legible from the terminal
rather than only from `git diff`.

**Do not split T005.** It is six lines and the three details (`--no-index`,
`capture_output`, non-zero-means-append) are interdependent; landing any subset
produces a guard that is wrong in a specific, tested way. Each now has a test
that fails without it: T012 for `--no-index`, T011 for `capture_output` and the
non-zero fallback.

## Task summary

| Phase | Story | Tasks | Count |
| --- | --- | --- | --- |
| 1 Setup | — | T001-T002 | 2 |
| 2 Foundational | — | *(intentionally empty)* | 0 |
| 3 User Story 1 | US1 | T003-T007 | 5 |
| 4 User Story 2 | US2 | T008-T015 | 8 |
| 5 User Story 3 | US3 | T016-T020 | 5 |
| 6 Polish | — | T021-T029 | 9 |
| **Total** | | | **29** |

New tests added: **10** — 2 in US1 (T003, T004), 6 in US2 (T008-T013), 2 in US3
(T016, T017). T014 runs existing tests rather than adding one.

Source files edited: **1** (`wfctl/cli.py`). Test files edited: **1**
(`tests/test_install_skills.py`); `tests/test_install_config.py` is asserted
unchanged.

### Revision history

The plan's test table originally listed six cases and undercounted. Corrected to
eight after `/speckit.tasks`, then to ten after `/speckit.analyze`:

| Added | Task | Why it was missing |
| --- | --- | --- |
| at tasks | T010 directory-form | spec Assumptions bullet 3 requires it asserted, not assumed |
| at tasks | T011 not a git repo | FR-007/FR-008 had no coverage |
| at analyze | T012 tracked path | **FR-006 had no test at all** — `--no-index` was undefended (analysis E1, HIGH) |
| at analyze | T013 trailing newline | edge case listed in spec, no test (analysis E3) |

T026 (SC-006 cost measurement) was also added at analyze, addressing E2 — a
quantified budget with nothing measuring it.

This list stays authoritative for test names and task IDs; `plan.md`'s table is
a summary and may lag.

## Template deviations

`.specify/templates/tasks-template.md` carries two references to another
project's stack (`server/zmodel/*.zmodel`, `bootstrap.zmodel` at line 80;
`pnpm type-check` at line 305). Both were dropped rather than answered — wfctl
is a Python CLI with no schema layer. Tracked upstream as
`aamarin/wf-skills#10`, whose PR 6 covers this file. Third artifact in this
feature to need the same surgery.
