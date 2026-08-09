---
description: 'Task list for spec-root-manifest-key (#18)'
---

# Tasks: spec-root-manifest-key

**Input**: Design documents from `specs/18-spec-root-manifest-key/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md

**Tests**: Required. Every phase below is verified by `pytest` against real git
repositories and real linked worktrees (`tests/conftest.py` and
`tests/test_paths.py` already build both), plus one manual walkthrough of
`quickstart.md`. The core regression — `feature-paths` on a branch with **no**
spec directory — is the case `WFCTL_SPEC_DIR` silently fails today, so it is
written first and must fail before implementation.

**Organization**: Grouped by user story. US1 is the defect and ships alone; US2
removes per-worktree setup; US3 makes the setting usable without hand-editing
JSON.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files or independent test functions)
- **[Story]**: US1 / US2 / US3, mapping to spec.md's prioritized stories
- Paths are repository-relative; this is a single Python package (`wfctl/`, `tests/`)

---

## Phase 1: Setup

**Purpose**: Establish the green baseline that SC-004 ("byte-identical paths for
a repo that records nothing") is measured against.

- [X] T001 Capture the pre-change baseline: run `pytest`, `ruff check wfctl tests`, and `mypy`, and record the passing counts in the PR description — this is the evidence SC-004 is compared to.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Register `spec_root` as a non-layer manifest key. Every story writes
or reads a manifest carrying that key, and without this the next
`install-skills` raises `AttributeError: 'str' object has no attribute 'get'` at
`wfctl/cli.py:728`.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Write failing test in `tests/test_install_skills.py`: `install-skills` over a manifest already carrying `spec_root` completes and leaves the key intact (per research.md D4).
- [X] T003 [P] Write failing test in `tests/test_install_skills.py`: `wfctl doctor` enumerates layers without error when the manifest carries `spec_root`.
- [X] T004 [P] Write failing test in `tests/test_install_skills.py`: `wfctl uninstall <agent>` leaves `spec_root` intact — FR-011 and SC-005 both name uninstall, and research.md D4 currently rests on a code read of `wfctl/cli.py:1023` with no test behind it.
- [X] T005 Add `"spec_root"` to `_NON_LAYER_KEYS` in `wfctl/cli.py:527`, extending the existing comment to explain that it is a bare string like `tracker`, not a layer; verify with T002, T003, and T004.
- [X] T006 Validate Phase 2 with `pytest tests/test_install_skills.py` — merge gate.

**Checkpoint**: The manifest can carry `spec_root` without breaking install, upgrade, uninstall, or doctor.

---

## Phase 3: User Story 1 - New specs land in the configured location (Priority: P1) 🎯 MVP

**Goal**: One resolver decides the spec root, and both the read path
(`resolve_spec_dir`) and the create path (`feature_paths_cmd`) consume it, so a
repo that records `spec_root` gets new spec directories under it.

**Independent Test**: Record `spec_root` in a repo's manifest, run
`wfctl feature-paths` on a branch with no spec directory, and confirm
`FEATURE_DIR` is under the recorded root. Shipped alone, a maintainer can already
relocate specs by recording the key in each working copy.

**Verification**:

- Automated: `pytest tests/test_paths.py`
- Manual: `WFCTL_SPEC_DIR=/tmp/x wfctl feature-paths | grep FEATURE_DIR` still wins over a recorded root
- Evidence: `FEATURE_DIR` under the recorded root for a branch whose spec directory does not exist — the exact command pair in issue #18's "Measured" section now differing

### Tests for User Story 1 ⚠️

> Write these first; each must FAIL before T011.

- [X] T007 [P] [US1] Write failing test in `tests/test_paths.py`: `spec_root()` precedence — `WFCTL_SPEC_DIR` beats a recorded `spec_root`, which beats `repo_root / "specs"` (FR-002, research.md D3).
- [X] T008 [P] [US1] Write failing test in `tests/test_paths.py`: `wfctl feature-paths` reports the recorded root for a branch with **no** existing spec directory — the core regression (FR-001, SC-003).
- [X] T009 [P] [US1] Write failing test in `tests/test_paths.py`: path forms — absolute used as-is, `~` expanded at read time, relative anchored to the declaring manifest's directory and not to cwd (FR-005).
- [X] T010 [P] [US1] Write failing test in `tests/test_paths.py`: a recorded root does not fall back to `<repo>/specs` even when a matching directory exists there (FR-013), and an unparseable manifest raises rather than defaulting (FR-015, current repo).

### Implementation for User Story 1

- [X] T011 [US1] Implement `spec_root(repo_root: Path) -> Path` in `wfctl/_paths.py`: `WFCTL_SPEC_DIR` → `spec_root` in this repo's manifest → `repo_root / "specs"`, reading the manifest through a lazy in-function import of `_load_manifest` (the `wfctl/_tracker.py:129` pattern — `cli.py:13` imports `_paths` at module level, so the reverse import must not be module-scoped); verify with T007, T009, T010.
- [X] T012 [US1] Point `resolve_spec_dir` at `spec_root()` in `wfctl/_paths.py:166-167`, leaving the match order (exact branch → issue-key glob → ancestor branches) untouched (FR-007); verify with T010 plus the existing `test_resolve_spec_dir_*` tests.
- [X] T013 [US1] Replace the hardcoded fallback at `wfctl/cli.py:352` with `spec_root(repo_root) / branch`, keeping stdout `eval`-safe — no added lines (contracts/cli.md); verify with T008.
- [X] T014 [US1] Add a `ponytail:` comment at the no-existence-check decision in `wfctl/_paths.py` naming why validating the root would rebuild this bug (research.md D7); verify by reading — no behavior change.
- [X] T015 [US1] Confirm SC-004: a repo recording nothing resolves byte-identical paths, with `pytest tests/test_paths.py` fully green against the T001 baseline.
- [X] T016 [US1] Validate Phase 3 with `pytest tests/test_paths.py tests/test_install_skills.py` — merge gate.

**Checkpoint**: The defect in issue #18 is fixed. Specs can live outside the repo, one working copy at a time.

---

## Phase 4: User Story 2 - Worktrees inherit the setting (Priority: P2)

**Goal**: A fresh worktree resolves the project's recorded root without any
per-worktree configuration, because the manifest lookup falls back to the main
checkout.

**Independent Test**: Record `spec_root` in a project's main checkout only, then
run `wfctl feature-paths` from a linked worktree that records nothing, and
confirm the main checkout's root is used.

**Verification**:

- Automated: `pytest tests/test_paths.py -k worktree`
- Manual: create a worktree with `git worktree add`, run `wfctl install-skills` in it (regenerating a manifest with no `spec_root`), and confirm `feature-paths` still reports the configured root
- Evidence: `FEATURE_DIR` outside the worktree, and still present after `git worktree remove`

### Tests for User Story 2 ⚠️

> Build real linked worktrees, following `test_project_name_from_a_worktree` and `test_resolve_agent_dir_keys_on_main_checkout_not_worktree` in `tests/test_paths.py`. No mocking of git.

- [X] T017 [P] [US2] Write failing test in `tests/test_paths.py`: a worktree whose own manifest lacks `spec_root` resolves the main checkout's value (FR-003, US2 AS1).
- [X] T018 [P] [US2] Write failing test in `tests/test_paths.py`: a worktree that records its own `spec_root` uses it and does not consult the main checkout (US2 AS2).
- [X] T019 [P] [US2] Write failing test in `tests/test_paths.py`: when the git common dir is not named exactly `.git` (bare / separate-gitdir layout), no manifest outside the repository is read (FR-004, US2 AS3, research.md D2).
- [X] T020 [P] [US2] Write failing test in `tests/test_paths.py`: an unparseable **main checkout** manifest raises when the worktree's own manifest declares nothing — FR-015 covers both locations, and T010 can only reach the current repo because the fallback does not exist until T021.

### Implementation for User Story 2

- [X] T021 [US2] Extend `spec_root()` in `wfctl/_paths.py` to consult the main checkout's manifest when the current repo's declares nothing, resolving it via `git rev-parse --git-common-dir` and proceeding only when that dir is named exactly `.git`; verify with T017, T018, T019, T020.
- [X] T022 [US2] Add a `ponytail:` comment at the `.git`-name guard naming the ceiling (bare and separate-gitdir layouts get no fallback) and the upgrade path (`git rev-parse --is-bare-repository` if those layouts ever need support); verify by reading — no behavior change.
- [X] T023 [US2] Confirm a relative `spec_root` declared in the main checkout resolves to one shared location from every worktree (FR-005), with `pytest tests/test_paths.py -k "relative or worktree"`.
- [X] T024 [US2] Validate Phase 4 with `pytest tests/test_paths.py` — merge gate.

**Checkpoint**: pfms can drop its per-worktree symlink step. US1 and US2 both work independently.

---

## Phase 5: User Story 3 - Recording the setting (Priority: P3)

**Goal**: `wfctl spec-root` records, shows, and removes the setting — writing the
main checkout so the value cannot evaporate with a worktree — and `doctor`
reports a recorded root co-existing with in-repo spec directories.

**Independent Test**: Run `wfctl spec-root <path>` in a fresh clone, then
`wfctl spec-root` with no argument, and confirm the effective root and its source
are reported and that `feature-paths` agrees.

**Verification**:

- Automated: `pytest tests/test_spec_root.py`
- Manual: run `wfctl spec-root ~/tmp/specs` from a worktree and confirm the printed path is the main checkout's manifest, not the worktree's
- Evidence: `doctor` printing the co-existence warning on a repo that has both, and its exit code unchanged

### Tests for User Story 3 ⚠️

- [X] T025 [P] [US3] Write failing tests in a new `tests/test_spec_root.py`: `wfctl spec-root <path>` writes the main checkout's manifest and prints that path; `wfctl spec-root` with no argument reports root plus source for each of the four sources; `--unset` removes the key; `<path>` together with `--unset` exits 2 (contracts/cli.md).
- [X] T026 [P] [US3] Write failing test in `tests/test_spec_root.py`: the recorded path is stored verbatim — `~` not expanded on write, no directory created, no existence check (FR-006, data-model.md).
- [X] T027 [P] [US3] Write failing test in `tests/test_install_skills.py`: `doctor` reports the co-existence of a recorded `spec_root` and non-empty `<repo>/specs/`, leaves its exit code unchanged, and still reports it in a repo with **no** installed layers — the check must run before the `if not layers:` early return at `wfctl/cli.py:1362` (FR-014, research.md D5).

### Implementation for User Story 3

- [X] T028 [US3] Implement the `spec-root` command in `wfctl/cli.py` (`[PATH]` argument, `--unset` flag, `_load_manifest`/`_save_manifest`, main-checkout write target reusing the same `.git`-name guard as the read path); verify with T025 and T026.
- [X] T029 [US3] Implement `_check_spec_root_migration(repo_root)` in `wfctl/cli.py`, modeled on `_check_workmux_hook` (`cli.py:1270`) — reports only, never moves or deletes, never changes the exit code — and call it beside `_check_workmux_hook` at `cli.py:1358`, before the layers gate; verify with T027.
- [X] T030 [US3] Validate Phase 5 with `pytest tests/test_spec_root.py tests/test_install_skills.py` — merge gate.

**Checkpoint**: All three stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T031 [P] Document the `spec_root` key, the `spec-root` command, the four-source precedence chain, and that recording a root does not migrate existing specs, in `README.md`; verify by following `specs/18-spec-root-manifest-key/quickstart.md` against the README text.
- [X] T032 [P] Run `ruff check wfctl tests` and `mypy` — both clean, with every added function annotated (`disallow_untyped_defs` is on for `wfctl/`).
- [X] T033 Walk `specs/18-spec-root-manifest-key/quickstart.md` end to end in a real worktree of this repository: record a root, create a worktree, run `wfctl feature-paths`, confirm the reported directory is outside the worktree, write a file into it, then `git worktree remove` the worktree and confirm that file still exists — SC-002's survival clause, which no automated test covers. Finish by `--unset` and confirming the default returns.
- [X] T034 Run the full `pytest` suite and compare against the T001 baseline — no pre-existing test changed its outcome (SC-004) — final gate.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Phase 1. **Blocks all user stories** — every story exercises a manifest carrying `spec_root`.
- **US1 (Phase 3)**: depends on Phase 2 only.
- **US2 (Phase 4)**: depends on Phase 3 — it extends the `spec_root()` function US1 creates. This is the one genuine cross-story dependency; it is a sequential extension of one function, not a coupling of separate features.
- **US3 (Phase 5)**: depends on Phase 2 for the manifest key. Its command can be written against US1's resolver; the main-checkout **write** target shares the guard introduced in US2, so implement after Phase 4 to avoid writing that guard twice.
- **Polish (Phase 6)**: depends on all shipped stories.

### Within Each User Story

- Tests first; confirm they FAIL before implementation.
- Resolver before its call sites (T011 → T012, T013).
- Read path before write path (US2's guard before US3's reuse of it).

### Parallel Opportunities

- T002, T003, T004 (Phase 2 tests) — independent test functions in one file.
- T007, T008, T009, T010 (US1 tests) — all in `tests/test_paths.py`, independent functions, no shared fixture state.
- T017, T018, T019, T020 (US2 tests) — same, each building its own worktree in `tmp_path`.
- T025, T026, T027 (US3 tests) — two files, independent.
- T031 and T032 (README and lint) — different surfaces.

Implementation tasks within a phase are **not** parallel: T011–T013 touch two
files in sequence, and T021 edits the function T011 creates.

## Logical PR Boundaries

Recommended: **one PR**. The whole change is ~60 lines across two modules, and
US1 alone leaves a feature that requires per-worktree configuration — a state
worth shipping only if the work has to be split.

If it must be split, the seam is Phase 2 + Phase 3 (the defect fix, complete and
independently valuable) followed by Phase 4 + Phase 5 (worktree inheritance and
the command). Do not split US2 from US1: US2 modifies the function US1
introduces, and merging US2's tests without US1 leaves the suite red.

`/speckit.decompose` owns this decision; the above is input to it, not a ruling.

---

## Parallel Example: User Story 1

```bash
# Write all four failing tests together (independent functions, one file):
Task: "spec_root() precedence test in tests/test_paths.py"             # T007
Task: "feature-paths with no spec dir test in tests/test_paths.py"     # T008
Task: "path form test (absolute, ~, relative) in tests/test_paths.py"  # T009
Task: "no-fallback + unparseable-manifest test in tests/test_paths.py" # T010

# Confirm they fail, then implement in sequence:
pytest tests/test_paths.py -k "spec_root"   # expect failures
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1: baseline.
2. Phase 2: the manifest key — blocks everything.
3. Phase 3: the resolver and both call sites.
4. **STOP and VALIDATE**: `wfctl feature-paths` in a repo with a recorded root and no spec directory reports that root. Issue #18's "Measured" reproduction now differs.

### Incremental Delivery

1. Phase 2 + 3 → the defect is fixed; specs can live outside the repo with per-working-copy setup.
2. Phase 4 → worktrees inherit; pfms drops its symlink step.
3. Phase 5 → the setting is configurable by anyone, and half-finished migrations are visible.
4. Phase 6 → documented and verified end to end.

### Parallel Team Strategy

Not applicable at this size. The three stories share one function in one file;
splitting them across people would cost more in coordination than the work
contains.

---

## Notes

- `[P]` = different files or independent test functions.
- This repository's validation commands are `pytest`, `ruff check wfctl tests`, and `mypy` — the installed template's `pnpm type-check` belongs to a different project.
- Verify each test fails before implementing it; the US1 regression test (T008) passing before T013 would mean it is not testing the fallback.
- Commit after each task or logical group.
- Never add a line to `feature-paths` stdout — it is `eval`'d by `.specify/scripts/bash/common.sh:45`.
- `.agent/` and `specs/` are gitignored here, so these artifacts are preserved by `wfctl archive-story` at worktree teardown, not by a commit.
- T004, T020, and T033's survival check were added after `/speckit.analyze` flagged E1, E2, and E3; task IDs were renumbered to stay sequential, so IDs cited in earlier conversation may have shifted by 1–2.
