# Tasks: one predicate signature

**Input**: Design documents from this branch's spec directory (`wfctl feature-paths`)
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/status-render.md, quickstart.md

**Tests**: The suite cannot see this change's real risk — it asserts on step
states and console substrings, so a restructure that broke the shape while
preserving every assertion would pass it. The render diff in
`contracts/status-render.md` is the verification path that fails if the logic
broke, and it is a captured artifact rather than a recollection.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- Paths are repo-relative from `/Users/andremarin/Development/wfctl/wt/314-one-predicate-signature`

---

## Phase 1: Setup

- [x] T001 Capture the pre-change baseline: walk every row of the state matrix in `contracts/status-render.md` through `_infer_steps`, dump `(name, state, annotation, reason, remedy)` per step, and save to `specs/.../contracts/baseline-before.json`; verify with a re-run producing a byte-identical file
- [x] T002 [P] Record the current `uv run mypy --strict wfctl/_pipeline.py` finding count (maps to `AGENTS.md`'s Code style section, not to an FR) in the scratchpad, so the split does not silently add `type-arg` or `no-any-return` findings; verify by re-running the same command
- [x] T003 Validate Phase 1 by confirming `baseline-before.json` covers all 17 matrix rows and all 8 steps per row — merge gate

---

## Phase 2: Foundational (blocking — no user story can start without this)

- [x] T004 Create `wfctl/_predicates.py` with the module docstring stating what it owns and why it is separate from the walk; verify with `uv run ruff check wfctl/`
- [x] T005 Move `Verdict`, `Source`, `_PROMISED` and `blocks` from `wfctl/_pipeline.py` to `wfctl/_predicates.py` unchanged, re-exporting from `_pipeline` only if a caller needs it; verify with `uv run pytest -q tests/test_pipeline_state_names.py`
- [x] T006 Move `_file_exists`, `_has_open_checkboxes`, `_tasks_open`, `_ISSUE_MAP_SECTION`, `_TABLE_SEPARATOR` and `_unkeyed_issues` to `wfctl/_predicates.py` unchanged; verify with `uv run pytest -q`
- [x] T007 Add `State = Literal["done", "in_progress", "pending", "skipped"]` and `Predicate = Callable[[Evidence], tuple[State, str | None]]` to `wfctl/_predicates.py`; verify with `uv run mypy wfctl/`
- [x] T008 Add the frozen `Evidence` dataclass to `wfctl/_predicates.py` with the six fields in `data-model.md`; verify with `uv run mypy wfctl/`
- [x] T009 Extract the `Evidence` construction from `_infer_steps` lines 441-461 into a builder, leaving the reads and their order untouched; verify with `uv run pytest -q` and by confirming `baseline-before.json` still reproduces
- [x] T010 Validate Phase 2 with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` — merge gate

---

## Phase 3: User Story 1 — change one step's evidence without touching the others (P1)

**Goal**: The eight predicates share one signature and hang off `_STEPS`, so a
change to what one step proves is a diff to one function.

**Independent Test**: Change what one step proves on a scratch commit and read
the diff. It passes if the changed hunk is confined to one function and names
one step.

- [x] T011 [P] [US1] Extract the `brainstorm` arm into `_predicates.brainstorm`, moving `design_block` and `arch_root`/`DESIGN_BLOCK_REASON` usage with it; verify with `uv run pytest -q tests/test_pipeline_state_names.py`
- [x] T012 [P] [US1] Extract the `specify` arm into `_predicates.specify`; verify with `uv run pytest -q tests/test_pipeline_state_names.py`
- [x] T013 [P] [US1] Extract the `clarify` arm into `_predicates.clarify`, keeping the `## Clarifications` regex and its comment; verify with `uv run pytest -q tests/test_pipeline_state_names.py`
- [x] T014 [P] [US1] Extract the `plan`, `tasks` and `analyze` arms into `_predicates.plan`, `.tasks`, `.analyze`; verify with `uv run pytest -q tests/test_pipeline_state_names.py`
- [x] T015 [P] [US1] Extract the `implement` arm into `_predicates.implement`, moving `_implement_verdict` and `verification_block` with it, and change `cli.py:3789` to import `verification_block` from `wfctl._predicates` — a re-export shim for one call site is the kind that outlives its reason; verify with `uv run pytest -q && uv run python -c "from wfctl._predicates import verification_block"`
- [x] T016 [US1] Extract the `decompose` arm into `_predicates.decompose` with its verdict logic byte-for-byte as today — routing through `blocks` is T021, not this task; verify with `uv run pytest -q`
- [x] T017 [US1] Add `Step(NamedTuple)` with `command`, `continuation`, `predicate` to `wfctl/_pipeline.py` and re-type `_STEPS` to `dict[str, Step]`, filling every row; verify with `uv run mypy wfctl/`
- [x] T018 [US1] Replace the eleven `if name ==` arms in `_infer_steps` with `state, reason = _STEPS[name].predicate(ev)`, keeping `cascade`, the annotation composition and `_design_remedy` in the loop; verify with `uv run pytest -q`
- [x] T019 [US1] Update the `_STEPS` unpack in `tests/test_pipeline_commands.py:72` to read `step.command`; verify with `uv run pytest -q tests/test_pipeline_commands.py`
- [x] T020 [US1] Validate US1 with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/`; confirm `_infer_steps` contains no branch on a step name (SC-005) with `grep -c 'name ==' wfctl/_pipeline.py` returning 0; confirm `grep -rn '_decompose\|decompose' wfctl/_pipeline.py wfctl/_predicates.py` finds both the table row and the predicate (FR-008, SC-006); and confirm `tests/test_pipeline_commands.py:112` still pins the eight `(command, auto)` pairs, which is FR-007's coverage — merge gate

### Verification

`uv run pytest -q` (the suite), `uv run mypy wfctl/` (the signature actually
being shared — eight `Predicate` values in one `dict[str, Step]` is what makes
it checkable), and the `grep` in T020 for SC-005. The story's own independent
test is the scratch-diff described above; run it once and discard the commit.

---

## Phase 4: User Story 2 — tell a restructure from a behaviour change (P2)

**Goal**: A reviewer can confirm, without running it, that no step reaches a
different verdict. `decompose` joins the seven that resolve inconclusive
evidence through `blocks`.

**Independent Test**: Diff the captured baseline against the same capture taken
after. It passes on byte-identical output.

- [x] T021 [US2] Route `_predicates.decompose` through `blocks(verdict, "ambient")` per the mapping in `research.md` Q2, keeping the `tasks_open` test outside `blocks`; verify with `uv run pytest -q tests/test_pipeline_state_names.py tests/test_pipeline_commands.py`
- [x] T022 [US2] Capture the post-change baseline into `contracts/baseline-after.json` by the same procedure as T001, and diff against `baseline-before.json`; verify by the diff being empty
- [x] T023 [US2] If T022's diff is non-empty on any of the four `decompose` rows, stop and report it as a finding — do not adjust the verdict to make the diff pass; verify by recording the diff verbatim in the PR body
- [x] T024 [P] [US2] Add `tests/test_predicates.py` asserting that every value in `_STEPS` is callable with an `Evidence` and returns a member of `State`, so a future predicate cannot silently take a different shape; and assert every predicate that can reach an inconclusive verdict reaches it through `blocks` — eight of eight, which is SC-004; verify with `uv run pytest -q tests/test_predicates.py`
- [x] T025 [US2] Validate US2 with `uv run pytest -q` and an empty T022 diff — merge gate

### Verification

The render diff is the whole story: `baseline-before.json` against
`baseline-after.json`, empty. `tests/test_predicates.py` (T024) is what stops
the property regressing after this branch merges. The four `decompose` rows in
the state matrix are the ones at risk and are checked by name.

---

## Phase 5: User Story 3 — a step cannot be half-declared (P3)

**Goal**: An incomplete step declaration and an out-of-set state name are both
rejected by the type check the project already runs.

**Independent Test**: Add a `_STEPS` row missing its predicate, run the type
check, confirm it fails and names the row, then remove the row.

- [x] T026 [US3] Change `_PipelineStep.state` from `str` to `State` in `wfctl/_pipeline.py` and fix whatever `uv run mypy wfctl/` then reports; verify with `uv run mypy wfctl/`
- [x] T027 [US3] Confirm the invariants bite: temporarily add a `_STEPS` row with two elements and a predicate returning `"finished"`, run `uv run mypy wfctl/`, record both error messages in the PR body, then revert; verify by `git diff --quiet wfctl/` after the revert
- [x] T028 [US3] Validate US3 with `uv run mypy wfctl/` clean and T027's two messages recorded — merge gate

### Verification

`uv run mypy wfctl/` is the verification, and T027 is what proves it is a real
gate rather than a claim — an invariant nobody has watched fail is an assumption.

---

## Phase 6: Polish & Cross-Cutting

- [x] T029 [P] Update `wfctl/_pipeline.py`'s module docstring: it claims three jobs and now has two, and the reason display stays with inference is `pipeline-state-is-one-payload`; verify by reading it against `plan.md`'s Structure Decision
- [x] T030 [P] Check `uv run mypy --strict wfctl/` against T002's recorded count and fix any finding this change added; verify by the counts matching
- [x] T031 Re-run `uv run wfctl install-skills --prune --yes --agent "$WFCTL_AGENT"` only if anything under `wfctl/agents/` changed — it should not have; verify with `uv run wfctl doctor`
- [x] T032 Run the review panel (`fanning-out-code-review`) over the full diff and reconcile its findings; verify by the disposition table existing for the PR body
- [x] T033 Validate the whole change with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/ && uv run wfctl doctor` — merge gate

---

## Dependencies

```
Phase 1 (T001-T003)  baseline captured
        │
        ▼
Phase 2 (T004-T010)  Evidence, State, Predicate, _predicates.py
        │            blocking — nothing below starts without it
        ▼
Phase 3 (T011-T020)  US1 — the eight predicates and the table
        │
        ├──────────────► Phase 4 (T021-T025)  US2 — decompose routed, diff clean
        │
        └──────────────► Phase 5 (T026-T028)  US3 — the invariants
                                  │
                                  ▼
                         Phase 6 (T029-T033)  polish, panel, definition of done
```

US2 and US3 are independent of each other and both depend on US1. They are
listed as separate stories because they are verified separately, not because
either ships alone — the spec says so in each story's *Why this priority*.

## Parallel execution

Within Phase 3, T011-T015 touch different arms and can run together. T016 is
sequential against them only because it is the arm whose routing changes in
Phase 4, and keeping it byte-identical here is what makes T022's diff
attributable.

Within Phase 6, T029 and T030 are independent.

## Implementation strategy

Phases 1 and 2 then US1 is the MVP: at T020 the eight predicates share a
signature and the loop no longer branches on the step name, which is the whole
of scope item 1 and most of item 3. US2 and US3 are each one sitting.

T023 is the stop condition the handoff names. If routing `decompose` cannot
preserve the verdict, that is a finding for #240 and this branch reports it
rather than absorbing it.

## What the run actually did, where it differs from the list above

All 33 ticked, and three were satisfied by something other than what they say:

- **T001** planned a hand-run before/after capture. It became a committed golden
  file (`tests/pipeline_payload_snapshot.json`) so the check outlives this branch
  — #309, #240 and #299 each have to regenerate it and say which verdict moved.
- **T023** was the stop condition: report a finding if `decompose`'s verdict
  moved. It never fired — the diff was empty — so it is satisfied vacuously
  rather than by an action.
- **T031** was conditional on `wfctl/agents/` changing. Nothing under it changed,
  so it was correctly a no-op.

Not in the list and done anyway: merging `origin/main` after #308 landed as #315,
porting its `tasks` rewrite into `_predicates.py`, and adding four snapshot rows
because the snapshot could not otherwise see the verdict #308 moved.
