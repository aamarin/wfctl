# Tasks: step-command drift check

**Input**: Design documents from `specs/31-step-command-drift-check/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: The feature *is* a test, plus a behaviour-preserving refactor beneath
it. Both halves carry automated verification; no manual-only steps.

**Organization**: Grouped by user story. Phase order departs from story numbering
— US3 (the merged table) comes first because US1's check reads the table it
produces, and writing US1 against the structure being deleted would mean writing
it twice.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3 per spec.md
- Paths are repository-root relative

## Path Conventions

Single package: `wfctl/`, `tests/` at repository root.

---

## Phase 1: Setup & Baseline

**Purpose**: Capture the behaviour the refactor must preserve, before touching it.

- [X] T001 Record the current step table values — run `uv run python -c "from wfctl._pipeline import _STEP_NAMES, _STEP_COMMAND, _STEP_AUTO; print([(n, _STEP_COMMAND[n], _STEP_AUTO[n]) for n in _STEP_NAMES])"` and confirm all eight rows match the table in `data-model.md`; verify by diffing the two lists by eye before any edit
- [X] T002 [P] Record baseline pipeline output — run `wfctl status` on this branch and keep the output; it is the comparison target for T012

**Checkpoint**: The pre-change behaviour is written down, so "unchanged" is checkable rather than asserted.

---

## Phase 2: Foundational (Blocking Prerequisites)

**None.** No shared infrastructure, schema, dependency or scaffolding is required
— the feature touches two files in an existing package with an existing test
suite. Recorded explicitly rather than padded with invented tasks.

---

## Phase 3: User Story 3 - A step cannot exist without its command (Priority: P1)

**Goal**: Merge `_STEP_NAMES`, `_STEP_COMMAND` and `_STEP_AUTO` into one table, so
a step missing its command or its automation flag stops being representable.

**Independent Test**: Every existing step resolves to today's exact command and
flag; the derived step order matches the previous hand-maintained list; an
undefined step still yields `("", False)`.

**Verification**: `uv run pytest -q`, `uv run mypy`, `uv run ruff check .`, and
`wfctl status` compared against the T002 baseline.

- [X] T003 [US3] Write the behaviour-preservation test first in `tests/test_pipeline_commands.py` — assert the **ordered** list `[(n, *next_step_content(n)) for n in _STEP_NAMES]` equals the eight rows of `data-model.md` in order, not step-by-step: `_STEP_NAMES` derives from the merged literal and *is* the pipeline sequence, so a per-step assertion would pass through a silent reorder (analysis C1); verify it passes against the *current* three-table code before any refactor, so it is proven to test behaviour rather than the new structure
- [X] T004 [US3] Add a test in `tests/test_pipeline_commands.py` asserting `next_step_content("complete")` and an arbitrary unknown step both return `("", False)` — pins the path `cli.py:170` depends on to print "story complete"; verify with `uv run pytest tests/test_pipeline_commands.py -q`
- [X] T005 [US3] Replace `_STEP_NAMES`, `_STEP_COMMAND` and `_STEP_AUTO` (lines 9-35 of `wfctl/_pipeline.py`) with the single `_STEPS: dict[str, tuple[str, bool]]` from `quickstart.md`, deriving `_STEP_NAMES = list(_STEPS)`; verify with `uv run pytest tests/test_pipeline_commands.py -q` — T003 and T004 must still pass unchanged
- [X] T006 [US3] Rewrite `next_step_content` (`wfctl/_pipeline.py:203`) as a single `_STEPS.get(step, ("", False))`, keeping a docstring line stating why an unknown step must not raise; verify with `uv run pytest -q`
- [X] T007 [US3] Validate Phase 3 with `uv run pytest -q && uv run mypy && uv run ruff check .` — merge gate

**Checkpoint**: Two of the three drift shapes are now unrepresentable, and the full suite still passes.

---

## Phase 4: User Story 1 - Drift fails the build (Priority: P1) 🎯 MVP

**Goal**: Fail the suite when a step names a command that does not ship.

**Independent Test**: Against the real shipped tree the check passes; with a
shipped command renamed it fails and names the unresolved entry.

**Verification**: `uv run pytest tests/test_pipeline_commands.py -q`. Both
negative cases — a renamed command and an empty command set — run as tests
through the `_unresolved` helper, so nothing is verified by inspection and
nothing mutates tracked files.

- [X] T008 [US1] Add the module-level constant `_COMMANDS = Path(wfctl.__file__).parent / "agents" / "commands"` to `tests/test_pipeline_commands.py`, with a comment stating why it does not read `_bundle.BUNDLE_ROOT` — `conftest.py`'s autouse `bundle` fixture repoints that constant at a fake tree, so a check using it reports every command missing (`research.md` R2); verify with `uv run pytest tests/test_pipeline_commands.py -q`
- [X] T009 [US1] Add the pure helper `_unresolved(shipped: set[str]) -> dict[str, str]` to `tests/test_pipeline_commands.py`, returning the step→command entries absent from `shipped`. Taking the set as an argument rather than globbing internally is what lets the negative cases run without touching the filesystem (analysis E1, E2); verify with `uv run pytest tests/test_pipeline_commands.py -q`
- [X] T010 [US1] Add `test_every_step_command_ships_in_the_bundle` to `tests/test_pipeline_commands.py`, calling `_unresolved` with the `*.md` stems under `_COMMANDS`; assert the result is empty and that the assertion message names the unresolved step and command when it is not (FR-003); verify it passes on the unmodified tree — 23 commands present, 0 of 8 unresolved
- [X] T011 [US1] Prove the check catches a real rename without mutating the repository — call `_unresolved` with the real stems minus `speckit.plan` plus `plan`, assert `speckit.plan` comes back unresolved; verify with `uv run pytest tests/test_pipeline_commands.py -q`. Renaming tracked files and restoring them by hand was rejected: an interrupted run leaves the repo broken and the bundle content hash wrong (analysis E2)
- [X] T012 [US1] Prove the check fails rather than passing vacuously on an empty command set — call `_unresolved(set())` and assert all eight entries come back unresolved; verify with `uv run pytest tests/test_pipeline_commands.py -q`. This replaces a by-inspection check that would have left the edge case unguarded on every later commit (analysis E1)
- [X] T013 [US1] Confirm the pipeline's own output is unchanged — run `wfctl status` and diff against the T002 baseline; verify they match exactly
- [X] T014 [US1] Validate Phase 4 with `uv run pytest -q && uv run mypy && uv run ruff check .` — merge gate

**Checkpoint**: MVP complete. #31's acceptance criteria 1 and 3 are met; the feature is shippable here.

---

## Phase 5: User Story 2 - The failure names which side moved (Priority: P2)

**Goal**: Make the failure message carry both sides, so a rename and a wrong
table entry are distinguishable without opening either file.

**Independent Test**: A failure message contains every unresolved entry *and* the
sorted list of shipped command names.

**Verification**: `uv run pytest tests/test_pipeline_commands.py -q` with an
assertion on the message content.

- [X] T015 [US2] Build the failure message in `tests/test_pipeline_commands.py` from the unresolved entries plus the sorted shipped stems; nominate no candidate — similarity scoring names an innocent file on 3 of 5 measured drift cases (`research.md` R1); verify with `uv run pytest tests/test_pipeline_commands.py -q`
- [X] T016 [US2] Assert the message content rather than trusting it — feed `_unresolved` the renamed-command set from T011 and check the rendered message contains both the missing entry and at least one shipped name; verify with `uv run pytest tests/test_pipeline_commands.py -q`
- [X] T017 [US2] Validate Phase 5 with `uv run pytest -q && uv run mypy && uv run ruff check .` — merge gate

**Checkpoint**: #31 acceptance criterion 2 met.

---

## Phase 6: Polish & Cross-Cutting

- [X] T018 [P] Confirm the check holds for an installed wheel, not just a checkout — the CI job at `.github/workflows/ci.yml` already builds a wheel and asserts the bundled trees ship; verify no new step is needed by re-reading that job rather than assuming
- [X] T019 Validate the whole feature with `uv run pytest -q && uv run mypy && uv run ruff check .` on both CI interpreters if available locally — merge gate

---

## Dependencies

```text
Phase 1 (baseline)
   └─> Phase 3 / US3 (merged table)         ← must precede US1: the check reads _STEPS
          └─> Phase 4 / US1 (the check)     ← MVP boundary
                 └─> Phase 5 / US2 (message)
                        └─> Phase 6 (polish)
```

- **US3 → US1** is a real dependency, not a preference: writing the check against
  the three tables would mean rewriting it after the merge.
- **US1 → US2** is soft. US2 only changes the failure message, so US1 is
  shippable without it — that is the MVP boundary.
- T002 (baseline) is consumed by T013. Capture it before editing anything.
- T009 (the `_unresolved` helper) blocks T010, T011, T012 and T016. All four call
  it; none touches the filesystem.

## Parallel Opportunities

Few, and that is expected — two files, one of them touched by a single story.

- T001 and T002 are independent (`[P]`).
- T018 reads CI config and touches nothing (`[P]`).
- T010, T011 and T012 are independent of one another once T009 exists — same
  file, so not marked `[P]`, but they can be written in any order.
- Within Phase 3 tasks are sequential: T003 must be proven against the old code
  before T005 replaces it.

## Implementation Strategy

**MVP = Phases 1, 3 and 4.** That delivers the merged table and the check, which
is #31's acceptance criteria 1 and 3 and the whole reason the issue exists. Stop
there and the feature is complete and useful.

**Phase 5** adds criterion 2 — attribution. Worth having, not worth blocking on:
a bare unresolved list still catches the drift, it just costs the reader a minute.

**Order matters once**: T003 before T005. A behaviour-preservation test written
after the refactor tests the new structure, not the old behaviour, and would pass
even if the merge changed a flag.
