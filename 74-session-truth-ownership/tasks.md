# Tasks: session truth ownership

**Input**: Design documents from the branch's spec dir (`wfctl feature-paths`)
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: `pytest` is the verification path for every task here. Console
assertions pin `NO_COLOR`, per `conftest.py`. Two tasks are verified by hand
because they change shipped skills, which the suite checks for shape and
cross-references but not for reading correctly.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: different file, no dependency on an incomplete task
- Paths are repository-relative from the worktree root

---

## Phase 1: Setup

**Purpose**: one fixture the rest of the plan leans on.

- [X] T001 Add a `spec_tree` fixture to `tests/conftest.py` that builds a spec
      root with named artifacts and returns the feature dir, so a test can say
      which of `design.md` / `spec.md` / `plan.md` / `tasks.md` exist without
      hand-writing files; verify with T005, the first test that consumes it
- [X] T002 Validate Phase 1 with `uv run --frozen pytest -q` — merge gate

---

## Phase 2: Foundational

**Purpose**: blocking prerequisites. US1 and US2 both need a report that carries
the next command and whether a session exists, and FR-005a is a statement about
state *names* — it cannot be written while the state is a glyph.

- [X] T003 Replace `symbol` with `state` on `_PipelineStep` in
      `wfctl/_pipeline.py`, carrying `done` / `in_progress` / `pending` /
      `skipped` through all ten assignment branches; verify with T005
- [X] T004 Return `state` rather than `symbol` from `steps_display` in
      `wfctl/_pipeline.py`, keeping `name`, `is_current` and `annotation`
      unchanged; verify with T005
- [X] T005 Add `tests/test_pipeline_state_names.py` asserting each of the four
      state names is produced by the artifact combination that earns it, with no
      glyph present in any value returned by `steps_display`
- [X] T006 Add the name-to-glyph map to `wfctl/cli.py` as the only place a symbol
      exists, and render `status` from it; verify with T007
- [X] T007 Extend `tests/test_pipeline_commands.py` with a rendered-output
      assertion per state, `NO_COLOR` pinned, proving the console output is
      byte-identical to today's for every state that is not changing
- [X] T008 Add a `session_started` read in `wfctl/_session.py` that answers from
      a `start` event in `events.jsonl` rather than from a file's existence;
      verify with T009
- [X] T009 Add `tests/test_session_existence.py` covering: no state dir, a state
      dir with events but no `start`, and a state dir with a `start` event
- [X] T009a Build `PipelineReport` in `wfctl/_pipeline.py` carrying `steps`,
      `current`, `next_command` and `session_started` — one structure, computed
      once per read, so a caller needing two of those facts makes one call;
      verify with T009b
- [X] T009b Add to `tests/test_pipeline_state_names.py` the invariant from
      `data-model.md`: `current` is None exactly when `next_command` is None, and
      a report with a current step and no command cannot be constructed
- [X] T010 Validate Phase 2 with `uv run --frozen pytest -q` and
      `uv run --extra dev mypy wfctl/` — merge gate

---

## Phase 3: User Story 1 — a session that starts cold is told the truth (P1)

**Goal**: every value describing where a feature stands is computed when read.

**Independent Test**: advance a branch's artifacts with no session command in
between, then ask where it is; the answer reflects the artifacts.

**Verification**: `uv run --frozen pytest -q tests/test_agent_session.py
tests/test_pipeline_commands.py`, plus the manual skill check in T019.

- [X] T011 [US1] Delete `_render_current_md` and the `current.md` write from
      `wfctl/_session.py`, and the corruption/idempotency reads of
      `current.json` from `start_cmd` in `wfctl/cli.py`; verify with T014
- [X] T012 [US1] Replace the `current.json` existence gates in `resume_cmd` and
      `end_cmd` (`wfctl/cli.py`) with the `session_started` read from T008,
      printing `✗ No session found for this branch. Run \`wfctl start\` first.`;
      verify with T014
- [X] T013 [US1] Remove the `status` field from session state in
      `wfctl/_session.py`, including its render and both writes; verify with T014
- [X] T014 [US1] Rewrite `tests/test_agent_session.py` for the new shape: no
      `current.md` or `current.json` is written, the position is re-derived on
      every read, and a branch switch is reflected without any command being run
      in between
- [X] T015 [P] [US1] Print the next command as a trailing `next:` line in
      `status_cmd` (`wfctl/cli.py`), read from the `PipelineReport` of T009a
      rather than by calling `next_step_content` at the call site, with the
      story-complete sentence when no step is current; verify with T017
- [X] T016 [P] [US1] Separate not-started from skipped in `_infer_steps`
      (`wfctl/_pipeline.py`): a step is `skipped` only when its own artifact is
      absent and a later step's artifact exists, so an empty feature dir and a
      missing one both read `pending`; verify with T017
- [X] T016a [US1] Add a `--json` flag to `status_cmd` (`wfctl/cli.py`)
      serialising the `PipelineReport` of T009a with `json.dumps`, plus `issue`
      and `branch`. The console branch renders from the same object, so neither
      format can carry a fact the other lacks — a second inference is what
      `pipeline-state-is-one-payload` rejects, not a second format; verify with
      T016b
- [X] T016b [US1] Add to `tests/test_pipeline_commands.py` a test that parses
      `status --json` and asserts every step name, state, annotation and
      `is_current` matches the console rendering of the same fixture, with no
      glyph anywhere in the parsed output. Asserting the two agree is the point:
      a fact added to one branch and not the other is the drift the flag exists
      to prevent
- [X] T017 [US1] Extend `tests/test_pipeline_commands.py` with the six states
      from `design.md`: no spec dir, empty spec dir, marked spec, skipped
      clarify, implementing-unverified, and every step done — asserting the
      literal rendered line in each, `NO_COLOR` pinned
- [X] T017a [US1] Add to `tests/test_agent_session.py` a field-coverage test
      naming each field the removed session file carried — issue, branch, repo,
      step, next command, updated — and asserting each is still answered, from
      where `research.md` says it now comes. A field that disappears without
      changing a rendered line is invisible to T017 and is what FR-011 forbids
- [X] T018 [US1] Unlink `current.md` and `current.json` on sight in any command
      that resolves a state dir (`wfctl/cli.py`), silently; verify with
      `tests/test_session_migration.py` added in the same task
- [X] T019 [US1] Update `wfctl/agents/skills/start-session/SKILL.md` step 4 to
      read `wfctl status --json` instead of `current.md`; verify by running
      `uv run --frozen wfctl install-skills --yes` then `/start-session` in a
      scratch worktree and confirming it reports position without that file
- [X] T020 [US1] Validate Phase 3 with `uv run --frozen pytest -q`,
      `uv run --frozen ruff check wfctl/ tests/`, `uv run --extra dev mypy
      wfctl/` — merge gate

---

## Phase 4: User Story 2 — ending a session leaves an honest handoff (P2)

**Goal**: `end` reports what it observed and claims no completion.

**Independent Test**: end a session mid-implementation with uncommitted work;
nothing written or printed asserts completion.

**Verification**: `uv run --frozen pytest -q
tests/test_end_reports_observations.py`, plus the manual skill check in T024.

- [X] T021 [US2] Rewrite `_render_session_summary` in `wfctl/_session.py` to
      carry `**Step**`, `**Boundary**` and `**Tree**` and drop `**Status**:
      complete`; verify with T023
- [X] T022 [US2] Report the observed clauses from `end_cmd` (`wfctl/cli.py`) —
      pipeline position, boundary answered, tree dirty — reading the position
      from the `PipelineReport` of T009a and matching `contracts/cli-output.md`;
      verify with T023
- [X] T023 [US2] Add `tests/test_end_reports_observations.py` asserting the
      printed line and the summary file both name the position and the tree
      state, and that neither contains a completion claim in any pipeline state
- [X] T024 [US2] Update `wfctl/agents/skills/end-session/SKILL.md` so the
      handoff it asks the agent to fill in no longer has a status to assert;
      verify by running `uv run --frozen wfctl install-skills --yes` then
      `/end-session` in a scratch worktree
- [X] T025 [US2] Validate Phase 4 with `uv run --frozen pytest -q` and
      `uv run --frozen ruff check wfctl/ tests/` — merge gate

---

## Phase 5: User Story 3 — a step's state has a name (P3)

**Goal**: the encoding change from Phase 2 is guaranteed rather than incidental.

**Independent Test**: inspect inferred states for a feature whose clarify step
was skipped; it is named differently from the done steps, with no symbol
involved.

**Verification**: `uv run --frozen pytest -q tests/test_pipeline_state_names.py`.

- [X] T026 [US3] Add a test to `tests/test_pipeline_state_names.py` asserting
      that no *value* produced by inference is a glyph — every `state` on a step
      and every field of a `PipelineReport` is one of the four names — so a
      symbol reintroduced into inference fails the suite. Assert on returned
      values, never on source text: `● ▶ ○ –` legitimately appear in comments in
      `_pipeline.py` and in `_verify.py`'s own output, and a grep-based test
      would fail for reasons it does not mean
- [X] T027 [US3] Add a test asserting that changing the glyph map alters
      rendered output and leaves every inferred state unchanged, which is User
      Story 3's second acceptance scenario stated as code
- [X] T028 [US3] Validate Phase 5 with `uv run --frozen pytest -q` — merge gate

---

## Phase 6: Polish

- [X] T030 [P] Update `wfctl/agents/skills/using-wfctl/SKILL.md` where it lists
      `current.json` and `current.md` as session state; verify with
      `uv run --frozen pytest -q tests/test_skill_cross_references.py`
- [X] T031 Walk `quickstart.md`'s five checks by hand in a scratch worktree;
      verify by comparing each rendered line against `contracts/cli-output.md`
      and correcting whichever of the two is wrong
- [X] T032 Validate the whole feature with `uv run --frozen pytest -q`,
      `uv run --frozen ruff check wfctl/ tests/`, `uv run --extra dev mypy
      wfctl/`, and `wfctl doctor` — merge gate

---

## Dependencies

```
Setup (T001-T002)
  └─ Foundational (T003-T010)
       ├─ US1 (T011-T020)  ─┐
       ├─ US2 (T021-T025)  ─┤ US2 depends on T003-T004 only for the position
       └─ US3 (T026-T028)  ─┘ it reports; otherwise independent of US1
            └─ Polish (T029-T032)
```

**Why the encoding change is foundational rather than US3's**: FR-005a is a
statement about state *names* — "skipped only when passed by" cannot be written
while the state is a glyph. US3 keeps its verification, which is what makes the
change durable.

**Parallel opportunities**:
- T015 and T016 touch different files (`cli.py`, `_pipeline.py`) and land in
  either order.
- T029 and T030 are independent of each other and of everything before them.
- US2 can proceed alongside US1 once Foundational is merged; they overlap only
  in `_session.py`, in functions neither shares.

## Implementation strategy

**MVP**: Phase 1, Phase 2 and US1. That is #42 closed — the stale resume point
is gone and every value is re-derived.

**Increment 2**: US2, closing #70.

**Increment 3**: US3, which is verification of a change already made, and Polish.

Task count: 34. US1: 11 · US2: 5 · US3: 3 · Setup + Foundational: 12 · Polish: 3.

Changed by `/speckit.analyze` remediation: T009a and T009b added (FR-010 had no
task), T017a added (FR-011 was verified only through rendered lines), T026
restated to assert on values rather than source text, T029 removed because both
`spec.md` and `design.md` scope `load_agentconfig` out — it is worth its own
issue, not a silent extra in this one.
