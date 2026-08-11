# Tasks: spec-root prompt and durable-spec skip

**Input**: Design documents from `~/Development/wfctl-specs/26-spec-root-prompt-and-durable-skip/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Required. This feature runs on the teardown path — a defect either
destroys design artifacts or makes worktrees unremovable. Every implementation
task below names a verification path.

**Organization**: By user story, with one deliberate departure recorded under
Phase 2.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable — different file, no dependency on incomplete work
- **[Story]**: US1 (P1 teardown), US2 (P2 install prompt), US3 (P3 naming)
- Source paths are repository-relative; spec artifacts live outside the repo

## Path Conventions

Single-package CLI. `wfctl/` and `tests/` at repository root; `.workmux.yaml` at
repository root.

---

## Phase 1: Setup

**Purpose**: Establish the baseline this change must not regress.

- [ ] T001 Record the current green baseline — run `uv run pytest -q`, `uv run ruff check .`, and `uv run mypy`, and note the passing test count; every later checkpoint compares against it
- [ ] T002 Confirm `wfctl feature-paths` resolves this branch's spec dir outside the repo, so no task writes to a literal `specs/<branch>`

**Checkpoint**: baseline captured, three commands green.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Land the rename and its alias **before** anything can refuse a
removal.

**⚠️ ORDERING DEPARTURE — read before reordering.** The rename belongs to User
Story 3 (P3) by priority, but it is foundational by risk and is sequenced here
deliberately. Phase 0 confirmed a non-zero `pre_remove` hook aborts the removal
(research.md R-001). A repo whose `.workmux.yaml` still names `archive-story`
would hit an unknown command, exit non-zero, and find its worktrees
**unremovable**. Shipping US1's blocking hook before the alias exists converts a
silent-loss bug into an outage. The alias must exist first; US3 keeps only the
parts that carry no such risk.

- [ ] T003 [P] Rename `tests/test_archive_story.py` to `tests/test_archive_specs.py` and change every `runner.invoke(app, ["archive-story", ...])` to `"archive-specs"`; expect failures now — the command does not exist yet
- [ ] T004 [P] Add a test in `tests/test_archive_specs.py` asserting `runner.invoke(app, ["archive-story"])` still dispatches identically to `archive-specs` (same exit code, same archive contents); expect it to fail
- [ ] T005 Add a test in `tests/test_archive_specs.py` asserting `archive-story` does **not** appear in `runner.invoke(app, ["--help"])` output while `archive-specs` does; expect it to fail
- [ ] T006 Rename the command to `archive-specs` in `wfctl/cli.py:276` and register `archive-story` as a hidden alias on the same function (no delegating second function, per research.md R-004); verify with `uv run pytest -q tests/test_archive_specs.py`
- [ ] T007 Validate Phase 2 with `uv run pytest -q && uv run ruff check . && uv run mypy` — merge gate

**Checkpoint**: both names work, only one is advertised, teardown behaviour is
unchanged. Safe to arm the hook in Phase 3.

---

## Phase 3: User Story 1 - Teardown stops destroying and stops duplicating (Priority: P1) 🎯 MVP

**Goal**: Preserve only what removal would destroy, and refuse the removal when
preserving fails.

**Independent Test**: Set a spec location outside the worktree, run a branch
through teardown, confirm the artifacts are untouched in place with no duplicate.
Separately, force preservation to fail on a default-layout repo and confirm the
worktree survives.

**Verification**:

- Automated: `tests/test_archive_specs.py` — one test per containment row, plus exit-status and message tests
- Manual: `quickstart.md` steps 2 through 5b — including the `--force` case (removal still refused) and the tool-absent case (removal proceeds)
- Evidence: no archive directory for a durable location; a surviving worktree after a forced failure; a completed removal when the tool is absent

### Tests for User Story 1 ⚠️

> Write these first and confirm they FAIL before implementing.

- [ ] T008 [P] [US1] Regression test in `tests/test_archive_specs.py`: a repo with no `spec_root` archives exactly the set it archives today — assert the full mapped list, not a count (FR-001, SC-002)
- [ ] T009 [P] [US1] Test in `tests/test_archive_specs.py`: `spec_root` outside the worktree archives the legacy `.agent/spec.md` and nothing from the spec dir (FR-002)
- [ ] T010 [P] [US1] Test in `tests/test_archive_specs.py`: `spec_root` resolving back **inside** the worktree still archives the spec dir — the case an on/off flag gets wrong (FR-003)
- [ ] T011 [P] [US1] Test in `tests/test_archive_specs.py`: durable location with no legacy file produces **no archive directory at all**, exit 0 (FR-004)
- [ ] T012 [P] [US1] Test in `tests/test_archive_specs.py`: the durable-skip message names the resolved spec-dir path, not just the fact of skipping (contracts/cli.md)
- [ ] T013 [P] [US1] Test in `tests/test_archive_specs.py`: at-risk artifacts present and a copy failure injected (unwritable state dir) exits non-zero (FR-006)
- [ ] T014 [P] [US1] Test in `tests/test_archive_specs.py`: exit 0 when nothing was at risk, including a missing worktree and a non-git directory (FR-007)
- [ ] T015 [P] [US1] Test in `tests/test_archive_specs.py`: the failure message contains the cause, the retry command, `git worktree remove`, `git branch -D`, the `--force` caveat, and the tmux-orphan note (FR-008, research.md R-006)
- [ ] T016 [P] [US1] Test in `tests/test_archive_specs.py`: given an existing complete archive, a run that fails partway leaves that archive **untouched at `archive/`** and leaves no partial directory behind (FR-023); assert the file count and content of `archive/` are unchanged from before the failed run
- [ ] T017 [P] [US1] Test in `tests/test_archive_specs.py`: a failed run followed by a successful retry produces exactly one `archive/` and one `archive-<stamp>/`, with no junk directory from the failed attempt — the residue this feature's own retry loop would otherwise manufacture (FR-023)

### Implementation for User Story 1

- [ ] T018 [US1] Add the containment predicate to `_plan` in `wfctl/_archive.py:98` — filter sources to those inside `worktree`; do not change the returned tuple shape (data-model.md); verify with T008–T012
- [ ] T019 [US1] Replace the blanket `except` contract in `wfctl/cli.py:300` with the narrow rule: non-zero only when at-risk artifacts existed and copying them failed; verify with T013, T014
- [ ] T020 [US1] Make `archive()` in `wfctl/_archive.py:158-176` promote-on-success: copy into a staging directory, write the index into it, discard it on any exception, and only then rename any existing `archive/` aside and rename staging into place (FR-023). Note `_archive.py:173` currently writes `README.md` into the live directory — it must move into staging too, or a failed run still leaves an index describing files it did not copy; verify with T016, T017
- [ ] T021 [US1] Implement the durable-skip and failure messages in `wfctl/cli.py`, including both escape-route caveats; verify with T012, T015
- [ ] T022 [US1] Rewrite the `pre_remove` hook in `.workmux.yaml:74-84` to the form in contracts/cli.md — remove `|| true` and the `command -v` short-circuit, keep the tool-absent branch; verify manually with quickstart.md step 5 (the hook is shell, not covered by pytest)
- [ ] T023 [US1] Verify the tool-absent branch of the hook: run teardown on a disposable repo with `wfctl` removed from `PATH`, and confirm it warns, exits 0, and lets the removal proceed (FR-009); verify with quickstart.md step 5b. This is the only path that permits a removal after artifacts went unarchived, so it must not be the only untested one
- [ ] T024 [P] [US1] Rewrite the module docstring in `wfctl/_archive.py:1-24`: state the rescue purpose and the containment predicate, replacing the superseded argument at lines 10-14 that archiving durable specs "is still worth running" (FR-021); verify by reading it against research.md R-003
- [ ] T025 [P] [US1] Rewrite the command docstring in `wfctl/cli.py:285-299`: replace "Never exits non-zero" with the two-layer rule, and reconcile the FR-013 one-artifact-location wording against the legacy `.agent/spec.md` read at `wfctl/_archive.py:114` (FR-005, FR-022); verify by reading it against data-model.md's exit-status table
- [ ] T026 [US1] Validate User Story 1 with `uv run pytest -q tests/test_archive_specs.py && uv run ruff check . && uv run mypy` — merge gate

**Checkpoint**: teardown preserves what it must, skips what it needn't, and
refuses rather than losing. Independently shippable.

---

## Phase 4: User Story 2 - A new project is asked where its specs should live (Priority: P2)

**Goal**: Make the durable location reachable by asking once, at first
interactive setup.

**Independent Test**: Run first-time setup interactively in a fresh repo, choose
each option in turn, confirm the recorded result. Re-run and confirm silence.

**Verification**:

- Automated: `tests/test_install_skills.py` — gating, recording, and cross-worktree suppression
- Manual: `quickstart.md` steps 7 and 8
- Evidence: a manifest with `spec_root_asked` and no `spec_root` resolving identically to one never asked

### Tests for User Story 2 ⚠️

- [ ] T027 [P] [US2] Test in `tests/test_install_skills.py`: a manifest containing `spec_root_asked: true` does not crash `_layer_keys`, `doctor`, or `install-skills` — the `AttributeError` guard (data-model.md invariant)
- [ ] T028 [P] [US2] Test in `tests/test_install_skills.py`: the prompt is asked on first interactive install, and silent under `--yes`, under a non-tty stdin, and when the marker already exists (FR-010, FR-011)
- [ ] T029 [P] [US2] Test in `tests/test_install_skills.py`: option 1 records `spec_root_asked` and **no** `spec_root`, and `spec_root` resolution is byte-identical to a repo never asked (FR-012, SC-006)
- [ ] T030 [P] [US2] Test in `tests/test_install_skills.py`: options 2 and 3 write the **main checkout's** manifest and report every file touched (FR-013)
- [ ] T031 [P] [US2] Test in `tests/test_install_skills.py`: a marker recorded in the main checkout suppresses the prompt when setup runs from a worktree whose own manifest is fresh (FR-016, research.md R-005)
- [ ] T032 [P] [US2] Test in `tests/test_install_skills.py`: a chosen location that does not exist is recorded without being created, cloned, or checked (FR-014)

### Implementation for User Story 2

- [ ] T033 [US2] Add `spec_root_asked` to `_NON_LAYER_KEYS` in `wfctl/cli.py:604` **in the same commit** as any code writing the key; verify with T027
- [ ] T034 [US2] Implement the three-option prompt in `wfctl/cli.py` beside the tracker question at `cli.py:803`, using the rendered form fixed in issue #26; verify with T028
- [ ] T035 [US2] Implement the marker read via the existing `spec_root_declaration` walk (`wfctl/_paths.py:222`) and the write to `main_checkout` as `wfctl spec-root` does (`wfctl/cli.py:424`); verify with T029, T030, T031
- [ ] T036 [US2] Implement option 2's follow-up output — printing the `git clone` and `mkdir` commands rather than running them — per contracts/cli.md; verify with T032
- [ ] T037 [US2] Validate User Story 2 with `uv run pytest -q tests/test_install_skills.py && uv run ruff check . && uv run mypy` — merge gate

**Checkpoint**: the durable option is reachable, asked once, and the default
answer is indistinguishable from never having been asked.

---

## Phase 5: User Story 3 - The command's name matches what it does (Priority: P3)

**Goal**: Give the compatibility alias an observable end condition.

The rename itself landed in Phase 2 for the risk reason recorded there. What
remains is the drift check that eventually makes the alias removable.

**Independent Test**: Point `doctor` at a repo whose `.workmux.yaml` still names
the old command and confirm it reports without failing.

**Verification**:

- Automated: `tests/test_remaining_commands.py` — report present, exit code unaffected
- Manual: `quickstart.md` step 6
- Evidence: a `⚠` line naming the stale hook, with `doctor` still exiting as before

### Tests for User Story 3 ⚠️

- [ ] T038 [P] [US3] Test in `tests/test_remaining_commands.py`: `doctor` reports a `.workmux.yaml` still calling `wfctl archive-story` (FR-020)
- [ ] T039 [P] [US3] Test in `tests/test_remaining_commands.py`: that report never changes `doctor`'s exit code, matching the superseded-path checks beside it
- [ ] T040 [P] [US3] Test in `tests/test_remaining_commands.py`: `doctor` stays silent for a `.workmux.yaml` already calling `archive-specs`, and for a repo with no `.workmux.yaml`

### Implementation for User Story 3

- [ ] T041 [US3] Implement the stale-hook check in `wfctl/cli.py` beside `_check_legacy_agent_dir` (`wfctl/cli.py:1338`), following its non-fatal drift pattern; verify with T038, T039, T040
- [ ] T042 [US3] Add a comment on the new check naming its removal condition and referencing issue #36, matching the `ponytail:` convention used at `wfctl/_archive.py:113`; verify by reading it against the #36 table
- [ ] T043 [US3] Validate User Story 3 with `uv run pytest -q && uv run ruff check . && uv run mypy` — merge gate

**Checkpoint**: all three stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T044 [P] Update `README.md` — the `spec-root` section (line ~347) gains the first-run question; the command list (line ~126) gains `archive-specs`; verify by grepping `README.md` for `archive-story` and finding only intentional historical mentions
- [ ] T045 [P] Write the pull request description covering the teardown behaviour change: under `|| true` no user has ever seen this hook block a removal, and afterwards a full disk stops teardown instead of silently destroying a spec — state what blocks, why, and the escape route; verify against contracts/cli.md's behaviour-change note
- [ ] T046 Run `quickstart.md` end to end against a disposable repo, including step 5's `--force` case and step 6's old-hook case; verify every expected output matches
- [ ] T047 Confirm `wfctl doctor` on this repo reports nothing unexpected after the change, since this repo has `spec_root` set and is therefore its own durable-location test case
- [ ] T048 Validate the whole feature with `uv run pytest -q && uv run ruff check . && uv run mypy`, and compare the test count against the T001 baseline — merge gate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup. **Blocks Phase 3 absolutely** — arming a blocking hook before the alias exists makes worktrees unremovable in every repo with an older configuration
- **US1 (Phase 3)**: depends on Phase 2
- **US2 (Phase 4)**: depends on Phase 1 only. Independent of US1 and Phase 2 — it touches `install-skills` and the manifest, no shared code with the archive path
- **US3 (Phase 5)**: depends on Phase 2 (the rename must exist before a check for its absence means anything)
- **Polish (Phase 6)**: depends on all stories

### Within User Story 1

Ordering inside the story is not stylistic — each step makes the next expressible:

1. T018 (predicate) before T019 (exit status) — "at-risk artifacts existed and failed" cannot be expressed until the plan distinguishes at-risk from not
2. T019 before T020 (atomicity) — the promote-on-success rewrite decides what a non-zero exit leaves on disk, so the exit rule must be settled first
3. T020 before T022 (hook) — the hook turns a status into a refused removal, which is what makes retries common enough for the residue to matter. Arming it before the atomicity fix means the first real failures manufacture exactly the junk directories T017 exists to prevent
4. T024, T025 (docstrings) last — they describe what shipped

### Parallel Opportunities

- T003, T004 in Phase 2
- T008–T017: all US1 tests, different test functions, no shared state
- T027–T032: all US2 tests
- T038–T040: all US3 tests
- T024, T025: different files
- **US2 (Phase 4) can run fully in parallel with Phases 2, 3, and 5** — it shares no code path with the archive work. This is the largest parallel opportunity in the feature

### Parallel Example: User Story 1 tests

```bash
# All seven US1 tests are independent — write them together, confirm all fail:
Task: "Regression test: default layout archives the same set (T008)"
Task: "Durable spec_root archives legacy file only (T009)"
Task: "spec_root resolving inside the worktree is still archived (T010)"
Task: "Durable location with no legacy file produces no archive dir (T011)"
Task: "Durable-skip message names the resolved path (T012)"
Task: "Copy failure with at-risk artifacts exits non-zero (T013)"
Task: "Nothing at risk exits zero (T014)"
Task: "Failed run leaves the existing archive untouched (T016)"
Task: "Failed run then retry leaves no junk directory (T017)"
```

---

## Logical PR Boundaries

Advisory only — `/speckit.decompose` decides. Signals observed here:

- **Phase 2 alone is a coherent PR**: a pure rename with a compatibility alias,
  no behaviour change, independently revertable. Landing it separately is also
  the safest sequencing, since it can reach users before anything blocks.
- **Phase 3 is one PR**: predicate, exit status, hook, and docstrings share a
  verification path and leave the feature broken if split — a predicate without
  the exit status silently skips durable specs with no refusal behind it.
- **Phase 4 is independently reviewable** and shares no files with Phase 3 beyond
  `cli.py`.
- Recommendation from plan.md stands: keep Phases 3 and 4 together in delivery.
  They are the setup and the consequence of one setting, and shipping the skip to
  a population with no way to opt in is the half-change worth avoiding.

---

## Implementation Strategy

### MVP (User Story 1)

1. Phase 1 → Phase 2 → Phase 3
2. **Stop and validate**: quickstart.md steps 2 through 5, `--force` included
3. At this point every repo has stopped losing specs silently, and durable repos have stopped accumulating duplicates

### Incremental Delivery

1. Phases 1–2 → rename shipped, nothing else changed, safe to release alone
2. Phase 3 → MVP; teardown is correct
3. Phase 4 → the durable option becomes reachable
4. Phase 5 → the alias gets its end condition
5. Phase 6 → docs and the behaviour-change announcement

### Notes

- Confirm each test fails before implementing it — several assert absence (no
  archive directory, no recorded key), which pass vacuously against the wrong
  setup
- T033 must not be split from whatever first writes `spec_root_asked`; the key
  without the `_NON_LAYER_KEYS` entry raises `AttributeError` immediately
- This repo has `spec_root` set, so it is its own test case for US1 — T047 is
  not ceremony
