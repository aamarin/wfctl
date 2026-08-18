# Tasks: Sweep the one-time migration checks

**Input**: Design documents from `specs/36-sweep-migration-checks/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Every story below declares a verification path. The two new notices
are user-visible output on a data-loss-adjacent path, so both get automated
coverage in their firing *and* silent states — a notice that never goes quiet is
as broken as one that never fires.

**Organization**: Grouped by user story. All three stories touch disjoint sites
and can be implemented, verified, and reviewed independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3 — maps to the user stories in spec.md
- Line numbers below are **pre-edit**, verified accurate against the working tree
  after the #43/#47 vendoring merge. Deletions shift everything beneath them, so
  after the first edit in a file, re-locate by symbol rather than by number:

  ```bash
  # definitions and call sites
  grep -n "_check_legacy_agent_dir\|_check_stale_archive_hook\|_check_spec_root_migration" wfctl/cli.py
  grep -n "pre_remove_uses_former_name" wfctl/_workmux.py
  # the two retained shims
  grep -n "ponytail: transition-only" wfctl/cli.py wfctl/_archive.py
  # the bundled template
  grep -n "archive-story" wfctl/agents/configs/workmux/.workmux.yaml
  ```

  Note for T013: `archive-story` also appears in `wfctl/_archive.py:41-42` and
  `wfctl/cli.py:339` as historical prose explaining the alias. Those are not
  shims and stay until the alias itself is removed in the follow-up.

## Path Conventions

Flat single-package layout: `wfctl/` and `tests/` at repository root. No `src/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish a known-green baseline so any later failure is attributable
to this feature rather than inherited.

- [ ] T001 Record the pre-change baseline by running `uv run pytest -q`, `uv run ruff check .`, and `uv run mypy` from the repository root; note the passing test count for comparison in T024

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: None required.

This feature is subtractive and introduces no shared module, schema, or
abstraction. Each story edits sites the others do not touch, so no story blocks
another. Recorded explicitly rather than filled with invented scaffolding.

---

## Phase 3: User Story 1 — Health output stops reporting finished transitions (P1)

**Goal**: `wfctl doctor` stops reporting two conditions nothing can create any
more, while both surviving drift reports keep working.

**Independent Test**: Run the health check in a fully-migrated repository and
confirm neither retired report appears; then construct each surviving report's
condition and confirm it still fires.

### Verification

- Automated: `uv run pytest -q tests/test_remaining_commands.py tests/test_workmux.py`
- Orphan check: `grep -rn "_check_legacy_agent_dir\|_check_stale_archive_hook\|pre_remove_uses_former_name" wfctl/ tests/` must return nothing. Ruff will not flag an unreferenced module-level function, so this grep is the gate.
- Manual: `uv run wfctl doctor` in this repository mentions neither `.agent/` nor `archive-story`.

### Tasks

- [ ] T002 [US1] Delete `_check_legacy_agent_dir` and its call site in `wfctl/cli.py` (definition at `:1673`, call at `:1887`); verify with the orphan grep above
- [ ] T003 [US1] Delete `_check_stale_archive_hook` and its call site in `wfctl/cli.py` (definition at `:1783`, call at `:1885`); verify with the orphan grep above
- [ ] T004 [US1] Delete `pre_remove_uses_former_name` from `wfctl/_workmux.py:159` and the sentence referencing it in the neighbouring docstring at `:152`; depends on T003 having removed its only caller; verify with the orphan grep above
- [ ] T005 [P] [US1] Remove the `pre_remove_uses_former_name` assertions from `tests/test_workmux.py:225-249`; verify with `uv run pytest -q tests/test_workmux.py`
- [ ] T006 [P] [US1] Remove the doctor cases covering the two deleted reports from `tests/test_remaining_commands.py`; verify with `uv run pytest -q tests/test_remaining_commands.py`
- [ ] T007 [US1] Rewrite the `_check_spec_root_migration` docstring in `wfctl/cli.py:1819` to state it reports recurring drift rather than a transition, citing that the setup prompt and `wfctl spec-root` can both create the condition today (FR-002, research.md R-002); verify by reading — no behavior change, so no test changes
- [ ] T008 [US1] Add a doctor test in `tests/test_remaining_commands.py` asserting that a repository containing a `.agent/` directory and a `.workmux.yaml` naming `archive-story` produces no mention of either; verify with `uv run pytest -q tests/test_remaining_commands.py`
- [ ] T009 [US1] Add or confirm doctor tests in `tests/test_remaining_commands.py` asserting the two surviving reports still fire — an unwired `pre_remove`, and a recorded spec root with stranded in-repo spec directories; verify with `uv run pytest -q tests/test_remaining_commands.py`
- [ ] T010 [US1] Validate Phase 3 with `uv run pytest -q && uv run ruff check . && uv run mypy` plus the orphan grep — merge gate

---

## Phase 4: User Story 2 — An unmigrated machine announces itself during teardown (P2)

**Goal**: The two retained compatibility paths each emit one line when they fire,
turning an unobservable comment into a condition decidable from ordinary use.

**Ordering note**: numbered before Phase 5, but the Implementation Strategy
recommends running Phase 5 first. Landing the template fix ahead of these notices
means the rename notice begins its observation window against a codebase that is
no longer re-seeding the retired name, so a notice seen later is real signal
rather than a repository seeded minutes earlier.

**Independent Test**: Invoke the archive command under the retired name and
confirm the rename notice; tear down a worktree holding a superseded directory
and confirm the rescue notice names the correct count. Repeat both on clean
inputs and confirm silence.

### Verification

- Automated: `uv run pytest -q tests/test_archive_specs.py`
- Contract: both notices must satisfy `contracts/cli.md` — no exit-code change, no effect on whether archiving completes.
- Manual: `quickstart.md` "Verify the two new notices", including the live legacy worktree at `~/Development/pfms/wt/440-editable-table-row`.

### Tasks

- [ ] T011 [US2] Add `ctx: typer.Context` as the first parameter of `archive_specs_cmd` in `wfctl/cli.py:299` and emit the retired-name notice when `ctx.info_name` is `archive-story`, per `contracts/cli.md`; place the emission inside the existing `try` so an unexpected failure cannot strand a worktree; verify with T014
- [ ] T012 [US2] Emit the legacy rescue notice in `wfctl/cli.py` after `_archive.archive` returns, counting entries in `mapped` whose destination starts with `extra/legacy-agent`; keep the derivation at the call site so `wfctl/_archive.py` continues to return data and own no console, and keep the emission inside the existing `try` so a failure while counting cannot strand a worktree (FR-012, same constraint as T011); verify with T015
- [ ] T013 [P] [US2] Rewrite the `ponytail:` comments on both retained paths — `wfctl/cli.py:299` and `wfctl/_archive.py:188` — to state their removal condition in terms of the notices from T011 and T012 rather than an unobservable trigger (FR-014); verify by reading against `quickstart.md` "The follow-up trigger"
- [ ] T014 [P] [US2] Add tests in `tests/test_archive_specs.py` asserting the rename notice appears when invoked as `archive-story` and is absent when invoked as `archive-specs`; verify with `uv run pytest -q tests/test_archive_specs.py`
- [ ] T015 [P] [US2] Add tests in `tests/test_archive_specs.py` asserting the rescue notice reports a count matching the files rescued, and is absent when the superseded directory is missing or empty; verify with `uv run pytest -q tests/test_archive_specs.py`
- [ ] T016 [US2] Add a test in `tests/test_archive_specs.py` covering a worktree that both holds a superseded directory and is invoked under the retired name — both notices appear, neither suppresses the other, and the exit code is unchanged; verify with `uv run pytest -q tests/test_archive_specs.py`
- [ ] T016a [US2] Extend `test_durable_spec_root_is_not_copied` in `tests/test_archive_specs.py:413` to assert the rescue notice and the existing durable-spec-dir notice co-occur without suppressing each other — the spec edge case "a worktree whose spec directory lives outside it"; the scenario is already constructed there, so this adds assertions rather than a test; verify with `uv run pytest -q tests/test_archive_specs.py`
- [ ] T016b [US2] Confirm the four inherited legacy-rescue tests still pass unmodified — `test_a_design_doc_at_the_superseded_path_is_still_archived:73`, `..._without_a_spec_dir:95`, `test_the_whole_superseded_directory_is_archived_not_just_spec_md:112`, and `test_durable_spec_root_is_not_copied:413` in `tests/test_archive_specs.py`. These are FR-006's real coverage; a diff to any of them means the rescue path changed when it should not have. Verify with `uv run pytest -q tests/test_archive_specs.py` and `git diff tests/test_archive_specs.py` showing additions only in the ranges touched by T014–T016a
- [ ] T017 [US2] Validate Phase 4 with `uv run pytest -q && uv run ruff check . && uv run mypy` — merge gate

---

## Phase 5: User Story 3 — Newly seeded repositories get the current command name (P3)

**Goal**: The bundled template stops handing out the retired command name, so
Story 2's rename condition can eventually reach zero.

**Independent Test**: Seed configuration into an empty repository and confirm the
resulting hook names the current command, with zero occurrences of the retired
one.

### Verification

- Automated: `uv run pytest -q tests/test_install_config.py`
- Bundle: `.github/scripts/check_wheel_contents.py` and `.github/scripts/check_installed_tree.py` — these arrived with the vendoring merge and assert on bundle contents, so the template edit is not free until they pass.
- Manual: `quickstart.md` "Verify the template correction".

### Tasks

- [ ] T018 [US3] Retarget both occurrences in `wfctl/agents/configs/workmux/.workmux.yaml` — the executable hook line at `:65` and the explanatory comment at `:55` — from `wfctl archive-story` to `wfctl archive-specs`; verify with `grep -c "archive-story" wfctl/agents/configs/workmux/.workmux.yaml` returning 0
- [ ] T019 [US3] Add a test in `tests/test_install_config.py` asserting a freshly seeded `.workmux.yaml` contains zero occurrences of the retired command name; verify with `uv run pytest -q tests/test_install_config.py`
- [ ] T020 [US3] Run the bundle checks against a built wheel per `quickstart.md` to confirm the corrected template ships and installs; verify with `.github/scripts/check_wheel_contents.py` and `.github/scripts/check_installed_tree.py`
- [ ] T021 [US3] Validate Phase 5 with `uv run pytest -q && uv run ruff check . && uv run mypy` plus the two bundle scripts — merge gate

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T022 [P] Confirm `wfctl/_archive.py` rescue logic is unchanged apart from its comment — `git diff wfctl/_archive.py` should show comment lines only; verify by reading the diff
- [ ] T023 [P] Walk `quickstart.md` end to end against this repository and correct any step that does not match observed behavior. Use the live legacy worktree at `~/Development/pfms/wt/440-editable-table-row` if it still exists; the synthetic `/tmp` construction in `quickstart.md` is the portable fallback once it is gone. Close by restating the follow-up trigger from the emitted output alone, without opening `wfctl/cli.py` or `wfctl/_archive.py` — if that cannot be done, SC-005 is not met and the notices need rewording
- [ ] T024 Run the full gate — `uv run pytest -q && uv run ruff check . && uv run mypy` — and compare the passing test count against the T001 baseline, accounting for tests deliberately removed in T005 and T006
- [ ] T025 Post a comment on issue #36 once the PR is open, recording that three of the five listed checks proved load-bearing and why — `_check_workmux_hook` and `_check_spec_root_migration` report recurring drift (research.md R-002), and the two rescue paths destroy data if removed early (research.md R-003) — so the follow-up removal inherits the reasoning rather than re-deriving it; approved 2026-08-17, post after implementation, not before; verify by reading the posted comment against research.md

---

## Dependencies

```
T001 (baseline)
  │
  ├── Phase 3 (US1)  T002 → T003 → T004 → {T005 ∥ T006} → T007 → T008 → T009 → T010 ─┐
  ├── Phase 4 (US2)  {T011 → T014} ∥ {T012 → T015} ∥ T013 → T016 → T016a → T016b → T017 ─┤
  └── Phase 5 (US3)  T018 → T019 → T020 → T021 ───────────────────────────────────────┤
                                                                                      │
                     Phase 6  {T022 ∥ T023} → T024 → T025 ◄───────────────────────────┘
                              (joins all three story phases — T024 compares the
                               full suite against T001, so every phase must land)
```

**Story order**: US1, US2, US3 are independent and may land in any order or
together. The only cross-story relationship is semantic, not blocking: US2's
rename condition cannot reach zero until US3 ships, because the bundled template
would otherwise keep re-seeding the retired name. US2 is fully implementable and
testable without US3.

**Within US1**: T004 must follow T003 — deleting the helper before its caller
breaks the build.

## Parallel Execution Examples

**Phase 3**: T005 and T006 touch different test files and may run together once
T004 lands.

**Phase 4**: three independent tracks — the rename notice (T011, T014), the
rescue notice (T012, T015), and the comment rewrite (T013). T016 joins them;
T016a and T016b follow, both touching `tests/test_archive_specs.py`.

**Phase 6**: T022 and T023 are independent reads.

**Across stories**: with three agents, US1, US2, and US3 can proceed
simultaneously after T001. Only `wfctl/cli.py` is shared — US1 deletes functions
near the end of the file, US2 edits the command near the top — so conflicts are
unlikely but not impossible; sequence the two if working in one worktree.

## Implementation Strategy

**MVP**: Phase 3 alone. It delivers issue #36's stated payoff — a health check
that reports only live drift — and is independently shippable.

**Recommended order**: Phase 3 → Phase 5 → Phase 4. Landing the template fix
(US3) before the notices (US2) means the rename notice starts its observation
window against a codebase that is no longer re-seeding the retired name, so a
notice seen afterwards is real signal rather than a repo seeded minutes earlier.

**Out of scope**: removing the two retained compatibility paths. That is the
follow-up change, triggered when neither notice has appeared on any machine.
