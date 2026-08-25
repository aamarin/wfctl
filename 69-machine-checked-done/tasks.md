# Tasks: Machine-checked done

**Input**: Design documents from `specs/69-machine-checked-done/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required. This feature's whole value is that a verdict is
trustworthy, so every requirement asserting non-forgeability, staleness, or
degrade-on-absence carries an automated test. `AGENTS.md` names the project's
bar: `uv run --frozen --extra dev pytest -q`, `uv run ruff check wfctl/ tests/`,
`uv run mypy wfctl/`, then `wfctl doctor`.

**Organization**: Grouped by user story. US1 is the MVP and is independently
shippable; US2 and US3 each add a property US1 does not have.

**Terminology**: per spec.md — *definition of done* is the declared command
list, a *verification run* is one execution of it, the *verification record* is
what a completed run leaves on disk.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel — different files, no dependencies
- Paths are repository-relative, single-package layout per plan.md

**On `[P]` in Phases 2–4**: absent by design, not by oversight. Those phases
interleave two test files, and every task within one file conflicts with its
siblings. The parallelism is between the *lanes*, not between adjacent tasks —
see Parallel opportunities.

---

## Phase 1: Setup

**Purpose**: A place for the new tests to land. No dependencies to add and no
scaffolding — the package layout already exists.

- [ ] T001 Create `tests/test_verify.py` with a module docstring naming why it exists and the `NO_COLOR` pinning `tests/conftest.py` requires for output assertions; verify with `uv run --frozen --extra dev pytest tests/test_verify.py -q` collecting zero tests without error.
- [ ] T002 Validate setup with `uv run --frozen --extra dev pytest -q` — merge gate; the suite is still green at its pre-change count.

---

## Phase 2: Foundational

**Purpose**: The config reader, the record reader/writer, and code identity.
Every story below reads at least one, so nothing else can start.

**⚠️ BLOCKS all user stories.**

- [ ] T003 Create `wfctl/_verify.py` with a module docstring stating why it is separate from `_pipeline.py` — it spawns subprocesses and writes state, while `_pipeline` is pure inference — and `load_config(repo_root) -> tuple[list[list[str]], list[str]]` returning the definition of done and a list of problems; verify with T004.
- [ ] T004 Add config validation tests to `tests/test_verify.py` covering every row of `contracts/wfctl-json.md`'s accepted/rejected table — absent file, `{}`, empty list, one command, a bare string, a string element, an empty argv, a non-string token, unparseable JSON, unknown keys ignored; verify with `uv run --frozen --extra dev pytest tests/test_verify.py -q`.
- [ ] T005 Implement `record_path`, `load_record`, and `write_record` in `wfctl/_verify.py`, reusing `_io.write_json_atomic`; a record missing any field required by `contracts/verify-record.md` loads as `None`, never as a partial dict; verify with T006.
- [ ] T006 Add record round-trip and malformed-record tests to `tests/test_verify.py`, asserting a truncated, empty, or field-missing record loads as absent rather than raising; verify with `uv run --frozen --extra dev pytest tests/test_verify.py -q`.
- [ ] T007 Implement `code_identity(repo_root) -> tuple[str, bool]` in `wfctl/_verify.py` using `git rev-parse HEAD` and `git status --porcelain`, with untracked files counting as dirty per spec Assumptions; verify with T008.
- [ ] T008 Add identity tests to `tests/test_verify.py` in a temporary repository asserting a clean tree reads clean, a modified tracked file reads dirty, and an untracked file reads dirty; verify with `uv run --frozen --extra dev pytest tests/test_verify.py -q`.
- [ ] T009 Validate Phase 2 with `uv run --frozen --extra dev pytest -q && uv run mypy wfctl/` — merge gate.

---

## Phase 3: User Story 1 — Completion cannot be self-certified (P1) 🎯 MVP

**Goal**: A definition of done that has not passed keeps `implement` at `▶`, and
the reason is on screen.

**Independent Test**: Configure a failing command, tick every task, write the
sentinel, and confirm `wfctl status` reports `▶` and names the failing command.

**Verification**: `tests/test_verify.py` for the run and the record;
`tests/test_pipeline_commands.py` for the step arm; one manual walk of
`contracts/cli-verify.md`.

- [ ] T010 Implement `run_verification(repo_root, commands)` in `wfctl/_verify.py`: each command via `subprocess.run(argv, cwd=repo_root)` with output inherited, never `shell=True`, running every command even after one fails (FR-013); verify with T011.
- [ ] T011 Add execution tests to `tests/test_verify.py` asserting all commands run when the first fails, that failures are collected in order, and that a command containing `$(...)`, backticks, and `;` is passed through as literal argv (FR-010); verify with `uv run --frozen --extra dev pytest tests/test_verify.py -q`.
- [ ] T012 Catch `FileNotFoundError` in `run_verification` in `wfctl/_verify.py` and record the command as failed rather than letting it propagate (FR-023); verify with T013.
- [ ] T013 Add a missing-executable test to `tests/test_verify.py` asserting a command naming a nonexistent binary yields exit 1, appears in `failed`, and prints a message naming the command rather than a traceback; verify with `uv run --frozen --extra dev pytest tests/test_verify.py -q`.
- [ ] T014 Write the record only after every command finishes (FR-017), and never reuse a prior result to skip work (FR-018), in `wfctl/_verify.py`; verify with T015.
- [ ] T015 Add an interruption test to `tests/test_verify.py` raising `KeyboardInterrupt` from the second of three commands, asserting no record was written and any pre-existing record is byte-identical; verify with `uv run --frozen --extra dev pytest tests/test_verify.py -q`.
- [ ] T016 Append one `verify` event per completed run to `events.jsonl` via `_io.append_event`, carrying verdict, sha, and failing commands (FR-022); verify with T017.
- [ ] T017 Add an event-log test to `tests/test_verify.py` asserting a failing run followed by a passing run leaves two distinguishable entries (SC-008); verify with `uv run --frozen --extra dev pytest tests/test_verify.py -q`.
- [ ] T018 Add the `verify` command to `wfctl/cli.py` with the exit codes and output of `contracts/cli-verify.md`, importing `_verify` lazily inside the function per the existing command pattern; verify with T019.
- [ ] T019 Add CLI tests to `tests/test_verify.py` asserting exit 0 on all-pass, exit 1 on any failure, exit 1 on malformed config, and that every failing command is named in the output (FR-007, FR-012); verify with `uv run --frozen --extra dev pytest tests/test_verify.py -q`.
- [ ] T020 Extend the `implement` arm of `_infer_steps` in `wfctl/_pipeline.py` using the already-present `repo_root` parameter, adding the never-run and failed branches in the order given by `data-model.md`, and update the docstring that currently calls `repo_root` unused; verify with T021.
- [ ] T021 Add step-inference tests to `tests/test_pipeline_commands.py` for never-run and failed, asserting `▶` with the correct annotation, that a sentinel file alone does not produce `●` when a definition of done is configured (FR-005), and that a record present with no `tasks.md` still reports `○`; verify with `uv run --frozen --extra dev pytest tests/test_pipeline_commands.py -q`.
- [ ] T022 Render the failing commands in the failed annotation in `wfctl/_pipeline.py`, not only the exit code, and add a test to `tests/test_pipeline_commands.py` asserting `wfctl status` alone names them (SC-006); verify with `uv run --frozen --extra dev pytest tests/test_pipeline_commands.py -q`.
- [ ] T023 Add a test to `tests/test_pipeline_commands.py` asserting a passing record with open checkboxes still reports `▶` — verification is an additional condition, never a replacement for the existing ones; verify with `uv run --frozen --extra dev pytest tests/test_pipeline_commands.py -q`.
- [ ] T024 Route a verification-blocked `implement` to `wfctl verify` rather than `/speckit.implement` in `next_step_content` in `wfctl/_pipeline.py` (FR-008); verify with T025.
- [ ] T025 Add a routing test to `tests/test_pipeline_commands.py` asserting `wfctl next` writes `wfctl verify` when tasks are complete but verification has not passed; verify with `uv run --frozen --extra dev pytest tests/test_pipeline_commands.py -q`.
- [ ] T026 Add a cost test to `tests/test_pipeline_commands.py` asserting `wfctl status` executes zero commands from the definition of done (FR-009, SC-002), using a command that writes a sentinel file and asserting the file is absent after status; verify with `uv run --frozen --extra dev pytest tests/test_pipeline_commands.py -q`.
- [ ] T027 Walk every output case in `contracts/cli-verify.md` against a scratch repository by hand and correct any output that differs; verify by pasting each observed block beside the contract's.
- [ ] T028 Validate US1 with `uv run --frozen --extra dev pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` — merge gate.

---

## Phase 4: User Story 2 — A stale pass is not a pass (P2)

**Goal**: A verdict stops counting the moment the code, the tree, or the
definition of done moves.

**Independent Test**: Verify successfully, change one line without committing,
and confirm `wfctl status` no longer reports `●`.

**Verification**: `tests/test_pipeline_commands.py` for each staleness trigger;
`tests/test_verify.py` for the inconclusive path.

- [ ] T029 Add the staleness comparisons to the `implement` arm in `wfctl/_pipeline.py` — recorded sha versus `HEAD`, recorded dirty or currently dirty, recorded commands versus the definition of done by exact list equality — in the order given by `data-model.md`; verify with T030.
- [ ] T030 Add one test per staleness trigger to `tests/test_pipeline_commands.py` — commit moved, tree dirty, untracked file present, definition changed — each asserting `▶` with its own annotation; verify with `uv run --frozen --extra dev pytest tests/test_pipeline_commands.py -q`.
- [ ] T031 Add a precedence test to `tests/test_pipeline_commands.py` asserting a failed run on a moved commit reports failed, not stale, pinning the branch order rather than the current implementation; verify with `uv run --frozen --extra dev pytest tests/test_pipeline_commands.py -q`.
- [ ] T032 Capture code identity again after the run and set `inconclusive` when it differs from the capture before (FR-016) in `wfctl/_verify.py`; verify with T033.
- [ ] T033 Add an inconclusive test to `tests/test_verify.py` mutating the tree from inside a configured command, asserting the record is inconclusive and `wfctl verify` exits 1; verify with `uv run --frozen --extra dev pytest tests/test_verify.py -q`.
- [ ] T034 Add a fresh-checkout test to `tests/test_pipeline_commands.py` asserting a clone of a verified branch reports `▶ unverified` (SC-005); verify with `uv run --frozen --extra dev pytest tests/test_pipeline_commands.py -q`.
- [ ] T035 Validate US2 with `uv run --frozen --extra dev pytest -q && uv run mypy wfctl/` — merge gate.

---

## Phase 5: User Story 3 — Projects without a definition of done are untouched (P3)

**Goal**: Zero behavioral change for a project that never adopts the feature.

**Independent Test**: Run the pipeline on a project with no `wfctl.json` and
confirm every reported state matches the current release byte for byte.

**Verification**: regression assertions in `tests/test_pipeline_commands.py`,
`tests/test_verify.py`, and `tests/test_install_skills.py`.

- [ ] T036 [P] Add a regression test to `tests/test_pipeline_commands.py` asserting pipeline output for an unconfigured project is unchanged across every reachable `implement` state — no tasks, open boxes, sentinel present, all ticked (SC-001); verify with `uv run --frozen --extra dev pytest tests/test_pipeline_commands.py -q`.
- [ ] T037 [P] Make `wfctl verify` report the absence and exit 0 when no definition of done is configured (FR-019) in `wfctl/cli.py`; verify with T038.
- [ ] T038 [P] Add a test to `tests/test_verify.py` asserting exit 0 and the notice text when the config is absent, empty, or has no `verify` key, so an unconditional caller does not break; verify with `uv run --frozen --extra dev pytest tests/test_verify.py -q`.
- [ ] T039 [P] Add a regression test to `tests/test_install_skills.py` asserting `install-skills` leaves `wfctl.json` tracked and adds no ignore entry for it (FR-011), pinning the property rather than the current loop; verify with `uv run --frozen --extra dev pytest tests/test_install_skills.py -q`.
- [ ] T040 Validate US3 with `uv run --frozen --extra dev pytest -q` — merge gate.

---

## Phase 6: Workflow integration & polish

**Purpose**: Close the loop so the agent that wrote the code learns the build is
red, and correct the claim this issue was filed against.

- [ ] T041 Add step 9c to `wfctl/agents/skills/speckit-implement/SKILL.md` running `wfctl verify` as the final action and reporting the verdict, keeping step 9b's sentinel write intact (FR-020); verify by running `wfctl install-skills` and exercising the step, per `AGENTS.md` — the suite checks that skills ship, not that they read well.
- [ ] T042 State in `wfctl/agents/skills/speckit-implement/SKILL.md` that the step must not report the work complete when the verification it just ran did not pass (FR-021); verify with the manual exercise in T041.
- [ ] T043 [P] Correct `README.md:15` so the claim describes what is enforced rather than asserting phases cannot be faked (FR-014); verify by reading the line beside `design.md`'s tamper-evident-not-unforgeable statement.
- [ ] T044 [P] Report a malformed `wfctl.json` as a finding in `doctor_cmd` in `wfctl/cli.py`, returning drift so the existing exit-code contract carries it (FR-015); verify with a test in `tests/test_remaining_commands.py` asserting exit 1 and the finding text.
- [ ] T045 Create `wfctl.json` at the repository root declaring this project's own definition of done — pytest, ruff, mypy — per `AGENTS.md`; this is the only end-to-end exercise the feature gets, so it stands in for SC-001 through SC-008 in situ; verify with `wfctl verify` passing and `wfctl status` reporting `implement ●`.
- [ ] T046 Validate the whole feature with `uv run --frozen --extra dev pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/ && wfctl doctor` — merge gate.

---

## Dependencies

```
Phase 1 (setup)
   │
Phase 2 (foundational: config, record, identity)   ⚠ blocks everything
   │
   ├──► Phase 3  US1  P1   ◄── MVP, shippable alone
   │        │
   │        ├──► Phase 4  US2  P2   (extends the same _pipeline arm)
   │        │
   │        └──► Phase 5  US3  P3   (independent of US2)
   │
   └──► Phase 6  workflow integration & polish   (needs US1 only)
```

US2 depends on US1 because both edit the `implement` arm of `_infer_steps`;
landing them in either order works, concurrently does not.

US3 depends on US1 only for `wfctl verify` existing (T037). Its regression tests
T036 and T039 have no dependency at all and should be written first — they must
pass before any of this work and still pass after, which is the whole point of
the story.

## Parallel opportunities

**Two lanes, not many.** Phases 2 through 4 interleave `tests/test_verify.py` and
`tests/test_pipeline_commands.py`. Within a file, tasks are strictly sequential;
across the two files they are independent. Split the work by file, not by task:

```
lane A  tests/test_verify.py        T004 T006 T008 · T011 T013 T015 T017 T019 · T033 T038
lane B  tests/test_pipeline_...py   T021 T022 T023 T025 T026 · T030 T031 T034 T036
```

Each lane's implementation task must land before its test. Lanes A and B share
`wfctl/_verify.py` only at Phase 2, which is why Phase 2 gates both.

**Genuinely parallel tasks** are marked `[P]`: Phase 5's four tasks each touch a
different file, and Phase 6's T043 and T044 do not overlap.

## Implementation strategy

**MVP is Phase 1 + 2 + 3.** That delivers the issue's actual complaint: a
completion claim backed by something other than the claimant.

**Do not stop at the MVP.** US2 is what keeps US1 true after the first commit.
Treat Phases 3 and 4 as one shipment unless something forces them apart.

**Phase 6 is not optional polish.** T045 adopts the feature in this repository,
the only end-to-end exercise it gets — every other test runs in a temporary
repository. T043 corrects the README claim this issue quotes in its opening line.

**Delivery boundaries are not decided here.** `/speckit.decompose` decides PR
grouping and waves.
