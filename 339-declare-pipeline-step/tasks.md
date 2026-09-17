# Tasks: Declare pipeline step

**Input**: Design documents from `/Users/andremarin/Development/wfctl-specs/339-declare-pipeline-step/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Every phase declares its verification. The suite is the gate for logic;
four cases in `quickstart.md` are exercised by hand because the suite can pass
while the behaviour is wrong — the spec's Validation Strategy names them and says
why for each.

**Organization**: by user story, in the spec's priority order. Phase 2 is the
mechanism, and no story can start before it lands. PR boundaries are
`/speckit.decompose`'s call, not this file's.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: different file, no dependency on an unfinished task
- Paths are repo-relative to the wfctl checkout
- The project's declared verification, run at every checkpoint:
  `uv run --frozen --extra dev pytest -q`,
  `ruff check wfctl/ tests/`, `mypy wfctl/`

---

## Phase 1: Setup

**Purpose**: the one thing every story's tests need and none of them owns.

- [ ] T001 Add a `declaring_repo` fixture to tests/conftest.py that writes a `wfctl.json` carrying a `steps` block into a tmp repo and returns its root; verify with `uv run --frozen --extra dev pytest -q tests/conftest.py --collect-only`
- [ ] T002 [P] Extend that fixture to seed `.agents/commands/<name>.md` so a declared command can be made installed or missing per test; verify with a throwaway assertion in tests/test_declared.py that both states are reachable

**Checkpoint**: a test can describe a repository that declares passes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: the pass as a shape, the reader that fills it, and the payload that
carries it. Nothing user-visible ships here.

**⚠️ CRITICAL**: no user story work can begin until this phase is complete.

- [ ] T003 Add the `SubStep` NamedTuple to wfctl/_pipeline.py beside `Step` — `name`, `command: str | None`, `on_finish`, `reads` — with a docstring saying why `reads` is a callable rather than a registry key; verify with tests/test_pipeline_state_names.py
- [ ] T004 Add `sub_steps: tuple[SubStep, ...] = ()` to `Step` in wfctl/_pipeline.py, defaulted so every existing row keeps parsing; verify with `uv run --frozen --extra dev pytest -q tests/test_pipeline_commands.py`
- [ ] T005 [P] Create wfctl/_declared.py with `load(repo_root) -> tuple[dict[str, list[SubStep]], list[str]]`, parsing `wfctl.json`'s `steps` key and returning problems rather than raising — the shape `_verify.load_config` already uses; verify with tests/test_declared.py
- [ ] T006 [P] Add the file-exists reader builder for `evidence` to wfctl/_predicates.py, resolving a relative path against `FEATURE_DIR` and an absolute path as given (research.md R3); verify with tests/test_predicates.py
- [ ] T007 Implement every validation rule from data-model.md § Validation rules in wfctl/_declared.py, one finding string per rule, with `<step>.<name>` as the form a finding names a pass by; verify with tests/test_declared.py
- [ ] T008 Apply the `on_finish` default as the list is read in wfctl/_declared.py — `review_required` for a declared pass — so nothing on a pass records its origin (FR-011, FR-021a); verify with tests/test_declared.py
- [ ] T009 Add `sub_steps: list[_PipelineStep]` to `_PipelineStep` in wfctl/_pipeline.py and walk each step's passes in `_infer_steps`, tool passes before declared, with the order overrides applied; verify with tests/test_pipeline_state_names.py
- [ ] T010 Implement the parent roll-up in `_infer_steps` — a `done` step with an outstanding pass reports `in_progress`; a `pending` or `skipped` step does not evaluate its passes (research.md R7, FR-006); verify with tests/test_pipeline_state_names.py
- [ ] T011 Emit `sub_steps` in `build_report`'s step dicts in wfctl/_pipeline.py with the keys contracts/status-payload.md names, always complete and never filtered (FR-020); verify with tests/test_pipeline_payload_snapshot.py
- [ ] T012 Teach `next_step_content` in wfctl/_pipeline.py to find the row carrying `on_finish` among a step's passes as well as in `_STEPS`, and to return a qualified pass name with `auto=False` for a manual pass; verify with tests/test_pipeline_commands.py
- [ ] T012a Apply the autonomy grant to a pass's `on_finish` in wfctl/_pipeline.py — a run with `auto_approve` set yields `auto: true` for a `review_required` pass, exactly as it does past the design gates, so autonomy stays one switch rather than one per kind of gate (FR-021b); verify with tests/test_pipeline_commands.py
- [ ] T013 Validate Phase 2 with `uv run --frozen --extra dev pytest -q && uv run --frozen --extra dev ruff check wfctl/ tests/ && uv run --frozen --extra dev mypy wfctl/` — merge gate

**Checkpoint**: the payload carries passes. No view renders them yet.

---

## Phase 3: User Story 1 — A repository's own stage becomes a row (Priority: P1) 🎯 MVP

**Goal**: a declared pass is a row on screen, the step is unfinished until it is,
and the tool names the command that runs it.

**Independent Test**: declare one pass in a scratch repository's configuration,
run the status view, confirm the pass appears indented under its step, that the
step reports unfinished while the pass is outstanding, and that the tool hands
out the declared command as what to run next.

**Verification**:

- Automated: tests/test_declared.py, tests/test_cli_status.py, tests/test_pipeline_payload_snapshot.py
- Manual: quickstart.md § *Declare a pass and walk a branch through it*, all six steps
- Evidence: `wfctl status` showing an indented row that no wfctl source change put there

### Tests for User Story 1 ⚠️

- [ ] T014 [P] [US1] Write tests/test_cli_status.py asserting a repository that declares nothing renders byte-identically to today — the regression every repository would see first (US1 acceptance 4)
- [ ] T015 [P] [US1] Write tests in tests/test_declared.py for each finding class in contracts/cli.md, one test per row of that table, each named for the failure it catches
- [ ] T016 [P] [US1] Write a test in tests/test_declared.py that a name reused under a *different* step is accepted and is not a finding (FR-002a)
- [ ] T017 [P] [US1] Write a test in tests/test_predicates.py that `evidence` resolves against the feature directory, not the repo root — the failure that leaves a pass reading `done` on every later branch (research.md R3)
- [ ] T017a [P] [US1] Write a test in tests/test_predicates.py that a built-in pass's `reads` can take a heading inside another step's artifact rather than a file of its own — the capability FR-008 exists for, which neither built-in pass exercises and which a regression to a path-only pass would remove without failing anything (spec edge case 5)
- [ ] T018 [P] [US1] Write a test in tests/test_pipeline_state_names.py that a declared pass runs after wfctl's own and that `before` moves it ahead of one (FR-003)
- [ ] T019 [P] [US1] Write a test in tests/test_declared.py that a cycle in `before`/`after` is a finding rather than an order (FR-003a)
- [ ] T020 [P] [US1] Write a test in tests/test_declared.py that a pass declaring passes of its own is a finding and that the outer pass is not loaded (FR-004) — the case Question 5 settled
- [ ] T021 [P] [US1] Write a test in tests/test_pipeline_commands.py that a manual pass yields the pass name and never a command, with `auto` false (FR-007, FR-022a)
- [ ] T022 [P] [US1] Write a test in tests/test_pipeline_state_names.py that a declared pass defaults to `review_required` and an overridden one is indistinguishable in the payload from a tool pass (FR-021, FR-021a, FR-011)

- [ ] T022a [P] [US1] Write a test in tests/test_pipeline_commands.py that a run granted `auto_approve` does not stop at a `review_required` pass — the gate that would otherwise halt every unattended run at the first declared pass (FR-021b)

### Implementation for User Story 1

- [ ] T023 [US1] Render passes indented under their step in `status_cmd` in wfctl/cli.py, in run order, using the existing `_STATE_GLYPH` map; verify with tests/test_cli_status.py
- [ ] T024 [US1] Render a pass's command beside an outstanding row, and the by-hand sentence for a manual pass, per contracts/cli.md § `wfctl status`; verify with tests/test_cli_status.py
- [ ] T025 [US1] Add the `check` Typer sub-app and `wfctl check config` to wfctl/cli.py, rendering `_declared`'s problems and exiting 1 on any (FR-022, research.md R4); verify with tests/test_declared.py and the exit codes in contracts/cli.md
- [ ] T026 [US1] Resolve a declared command against the installed command directories `_AGENT_TARGETS` names in wfctl/cli.py, so a command that ships from the consuming repository can be found; verify with the fixture from T002 in tests/test_declared.py
- [ ] T027 [US1] Update tests/pipeline_payload_snapshot.json wholesale for the new rows, and say in the commit message that the verdict change is deliberate — its own docstring names this as how that is declared; verify with tests/test_pipeline_payload_snapshot.py
- [ ] T028 [US1] Walk quickstart.md § *Declare a pass and walk a branch through it* end to end against a scratch repository and record what each of the six steps printed; verify by comparing each against contracts/cli.md
- [ ] T029 [US1] Validate Phase 3 with `uv run --frozen --extra dev pytest -q && ruff check wfctl/ tests/ && mypy wfctl/` — merge gate

**Checkpoint**: a repository can add a stage of its own and have it routed to,
with no change to wfctl's source (SC-001).

---

## Phase 4: User Story 2 — wfctl's own passes report separately (Priority: P2)

**Goal**: brainstorm stops collapsing into one state with a sentence hung off it.

**Independent Test**: on a branch part-way through brainstorming, read the
position and confirm each pass reports its own state, and that the outstanding
one names the command that produces it.

**Verification**:

- Automated: tests/test_predicates.py, tests/test_pipeline_state_names.py, tests/test_status_facts.py
- Manual: quickstart.md § *Read wfctl's own passes*
- Evidence: two rows under `brainstorm`, neither marked as wfctl's

### Tests for User Story 2 ⚠️

- [ ] T030 [P] [US2] Write a test in tests/test_predicates.py that the architecture pass reads the record and the design-doc pass reads `design.md`, each independently of the other (US2 acceptance 1)
- [ ] T031 [P] [US2] Write a test in tests/test_pipeline_state_names.py that a `brainstorm` with its record written and no `design.md` reports `in_progress` with exactly one outstanding pass (FR-006)
- [ ] T032 [P] [US2] Write a test in tests/test_pipeline_payload_snapshot.py that nothing in either built-in pass's payload entry distinguishes it from a declared one (FR-011, US2 acceptance 3)

### Implementation for User Story 2

- [ ] T033 [US2] Split `brainstorm` in wfctl/_predicates.py into the two pass readers data-model.md names, leaving the step's own reader owning only its `pending` and `skipped` branches; verify with tests/test_predicates.py
- [ ] T034 [US2] Order the two passes architecture-then-design-doc in `_STEPS["brainstorm"]` in wfctl/_pipeline.py, which fixes the read order `design.md` flagged — the reader checks `design.md` before the record, the reverse of the order both skills write them in; verify with tests/test_predicates.py
- [ ] T035 [US2] Confirm the one assertion in the suite that pins `current == "brainstorm"` still holds, and update it with a docstring saying what changed if it does not; verify with `uv run --frozen --extra dev pytest -q -k brainstorm`
- [ ] T036 [US2] Walk quickstart.md § *Read wfctl's own passes* on a branch part-way through brainstorming; verify the four expectations it lists
- [ ] T037 [US2] Validate Phase 4 with `uv run --frozen --extra dev pytest -q && ruff check wfctl/ tests/ && mypy wfctl/` — merge gate

**Checkpoint**: the mechanism has two consumers, one of them wfctl's own (SC-002).

---

## Phase 5: User Story 3 — A pass that does not apply is declared away (Priority: P3)

**Goal**: the gate gets an exit, and the exit reaches a reviewer.

**Independent Test**: declare a pass inapplicable with a reason, confirm the
claim is part of the change under review, confirm the pipeline advances, and
confirm the row is hidden by default and shown with the flag.

**Verification**:

- Automated: tests/test_step_none.py, tests/test_arch_records.py, tests/test_paths.py
- Manual: quickstart.md § *Claim a pass away, twice* and § *The one where a wrong answer looks like success*
- Evidence: two claim files on one branch, and a boundary gate that still holds

### Tests for User Story 3 ⚠️

- [ ] T038 [P] [US3] Write tests/test_step_none.py covering every row of contracts/cli.md § `wfctl step none`, including that nothing is written on a refusal (FR-013)
- [ ] T038a [P] [US3] Write a test in tests/test_step_none.py that a bare name carried by a pass under the current step is still refused when a second pass elsewhere carries it — a bare name never resolves against the step that happens to be current, which moves as unrelated work lands (FR-002c)
- [ ] T039 [P] [US3] Write a test in tests/test_step_none.py that two claims on one branch both survive, and that a second claim on one pass replaces it (FR-015, SC-005)
- [ ] T040 [P] [US3] Write a test in tests/test_arch_records.py that a claim does not satisfy the boundary check — the one where a wrong answer looks like success (FR-016, SC-006)
- [ ] T041 [P] [US3] Write a test in tests/test_paths.py that `non_record_subtrees` names `step-claims/`, so a reader added later inherits the exclusion (AGENTS.md, #370)
- [ ] T042 [P] [US3] Write a test in tests/test_cli_status.py that the default view hides a claimed pass, `--all` shows it with its reason, and a claimed pass that is holding the pipeline is shown either way (FR-018, FR-019)
- [ ] T043 [P] [US3] Write a test in tests/test_pipeline_payload_snapshot.py that `--json` carries a row the console hid (FR-020, SC-004)

- [ ] T043a [P] [US3] Write a test in tests/test_pipeline_state_names.py that a claimed pass whose artifact appears afterwards still reports `skipped` — whether a pass applies is a person's judgment and no artifact overturns it (spec edge case 7)

### Implementation for User Story 3

- [ ] T044 [US3] Add `step-claims` to `_paths.non_record_subtrees` with a constant beside `SCANS_DIR` and `IMPLEMENTATION_DIR`; verify with tests/test_paths.py
- [ ] T045 [US3] Add `wfctl step none <step>.<name> --reason` to wfctl/cli.py, reusing `arch none`'s empty and `<placeholder>` guards and its `touched_on_this_branch` check; verify with tests/test_step_none.py
- [ ] T046 [US3] Implement pass-name resolution for that command — qualified always, bare only where globally unambiguous, never against the current step (FR-002b, FR-002c); verify with tests/test_step_none.py
- [ ] T047 [US3] Read claims in `_infer_steps` in wfctl/_pipeline.py so a claimed pass reports `skipped` and carries its reason as `claimed` in the payload — the claim is read before the pass's own `reads`, so an artifact that appears after the claim does not overturn it (FR-017, spec edge case 7); verify with tests/test_pipeline_state_names.py
- [ ] T048 [US3] Add `--all` to `status_cmd` in wfctl/cli.py, filtering at the moment of printing and never in the payload; verify with tests/test_cli_status.py
- [ ] T049 [US3] Walk quickstart.md § *Claim a pass away, twice* and § *The one where a wrong answer looks like success*; verify each of the seven expectations they list
- [ ] T050 [US3] Validate Phase 5 with `uv run --frozen --extra dev pytest -q && ruff check wfctl/ tests/ && mypy wfctl/` — merge gate

**Checkpoint**: all three stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T051 [P] Document the `steps` key in AGENTS.md beside `change_check`, with the same argument about `.agents/` being gitignored; verify by reading it against contracts/wfctl-json.md
- [ ] T052 [P] Name `wfctl check config` in AGENTS.md's verification section, and say it is not `doctor`'s work; verify with `uv run wfctl check config --help`
- [ ] T053 Update any skill under wfctl/agents/ whose prose enumerates the eight rows as the whole of the position view; verify with `uv run --frozen --extra dev pytest -q tests/test_skill_cross_references.py`
- [ ] T054 Run `uv run wfctl install-skills --prune --yes --agent claude` then `uv run wfctl doctor`, and exercise anything changed under wfctl/agents/ — the suite checks that skills ship and cross-reference, not that they read well
- [ ] T055 Run the full quickstart.md validation end to end; verify every section's expectations
- [ ] T056 Validate the whole feature with `uv run --frozen --extra dev pytest -q && ruff check wfctl/ tests/ && mypy wfctl/` then `uv run wfctl doctor` — merge gate

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (1)**: none
- **Foundational (2)**: needs Setup. Blocks every story
- **US1 (3)**: needs Foundational. The MVP
- **US2 (4)**: needs Foundational. Independent of US1's CLI work, but shares `_infer_steps` with T009/T010
- **US3 (5)**: needs Foundational, and needs US1's rendering for its `--all` half
- **Polish (6)**: needs the stories that shipped

### Story dependencies

US1 and US2 are independent once Phase 2 lands — one adds a reader and a view,
the other adds two rows to a table. US3 depends on US1 only for where `--all`
hangs; its claim-writing half is independent of both.

### Within a phase

Tests marked [P] are different files and can be written together. Implementation
tasks in a phase are sequential where they share a file — T023, T024, T025 and
T048 all edit `wfctl/cli.py`, and T009, T010, T011 and T012 all edit
`wfctl/_pipeline.py`.

### Parallel opportunities

- T005 and T006 — different modules, no shared state
- T014 through T022a — eleven test files or eleven independent tests
- T030 through T032, and T038 through T043a — same, per story
- T051 and T052 — both AGENTS.md, so sequential in practice despite the [P]

## Implementation Strategy

**MVP is Phase 1 + 2 + 3.** That is SC-001 on its own: a repository adds a stage
and the pipeline routes to it. It ships a gate with no exit, which is why US3
exists and why shipping the MVP alone is a decision someone makes deliberately
rather than a stopping point this file recommends.

**Phase 4 is the evidence, not an extra.** A mechanism that cannot express
wfctl's own passes was built for one consumer and never tested against a second —
the spec says so in US2's own *Why this priority*.

**Phase 5 closes the gate.** Without it the first two stories install a pass that
does not apply and cannot be got past.
