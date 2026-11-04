Implementation complete: 2026-11-03

## Tasks at completion

~~~~markdown
# Tasks: Session start loads the records for the branch's contexts

**Input**: Design documents from `/Users/andremarin/Development/wfctl-specs/700-session-start-relevant-records/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Every acceptance scenario gets a test. Write it first and run it red
before the code that makes it pass. Tests that check output pin `NO_COLOR`, as
`conftest.py` explains. Test names are sentences, and each docstring says which
failure the test catches.

**Design records**: `docs/architecture/design/700-one-function-selects-records.md`
(level 3) and `docs/architecture/branch-contexts-select-records.md` (level 2).
Both are proposed, and no task below reverses either one.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel, since it edits a different file and depends on no open task
- **[Story]**: the user story the task belongs to

---

## Phase 1: Setup

No setup. The change adds no dependency, package, or config, and `uv run`
resolves the environment from `uv.lock`.

---

## Phase 2: Foundational (the selection rule)

**Purpose**: Build the one function every reader calls. Stories 1 to 3 all
depend on it, so it lands first.

**Verification**:

- `uv run pytest -q tests/test_contexts.py tests/test_evidence.py`
- `uv run mypy`

- [X] T001 Write failing tests for `_contexts.select(names, listed, accepted)` in `tests/test_contexts.py`, one per row of `data-model.md §select`, in order. When `names` is `None`, it returns every record with nothing else set. When `listed` is `None` or `()`, it returns every record with `unlisted=True`. When a listed name isn't in `names`, it returns every record with `unknown` set to the first such name. Otherwise it keeps each record with no `governs` field or with a `governs` field sharing a name with `listed`, sets `contexts` to `listed`, and counts the rest in `left_out`. Add one test that checks `len(records) + left_out == len(accepted)` across every row, and one for an outside party such as `trackers`, which is kept only when the branch lists it. Verify they fail with `uv run pytest -q tests/test_contexts.py`.
- [X] T002 Add `Selection` and `select` to `wfctl/_contexts.py`. `Selection` is a `NamedTuple` with `records`, `left_out`, `contexts`, `unlisted`, and `unknown`, plus a `narrowed` property that is `left_out > 0`. `select` reads no files and keeps the records in the order it's given them. Verify with `uv run pytest -q tests/test_contexts.py`.
- [X] T003 Write failing tests for `_evidence.records_for_branch(repo_root, branch)` in `tests/test_evidence.py`, against a temporary arch root, domain page, and spec folder set through `WFCTL_SPEC_DIR`. A branch with no spec folder passes `listed=None`. A spec folder whose `design.md` names one context narrows the set. An unreadable `design.md` reads as having no `Contexts` line. Verify they fail with `uv run pytest -q tests/test_evidence.py`.
- [X] T004 Add `records_for_branch` to `wfctl/_evidence.py`, beside `context_gap`. It resolves `arch_root(repo_root)` and `_paths.resolve_spec_dir(branch, repo_root)`, reads `_contexts.names` and `_contexts.listed`, loads `_arch.in_force(_arch.load_records(arch))`, and returns `_contexts.select(...)`. Import `_contexts` inside the function, as the module's other `_contexts` callers do. Verify with `uv run pytest -q tests/test_evidence.py` and `uv run python .github/scripts/check_imports.py`.
- [X] T005 Validate Phase 2 with `uv run pytest -q tests/test_contexts.py tests/test_evidence.py`, `uv run mypy`, and `uv run python .github/scripts/check_imports.py` — merge gate

**Checkpoint**: One function decides which records apply, and nothing calls it yet.

---

## Phase 3: User Story 1 - A branch that lists its contexts sees only its records (Priority: P1) 🎯 MVP

**Goal**: `wfctl arch context` prints only the records for the branch's contexts, plus every record with no `governs` field, and says how many it left out.

**Independent Test**: Write a `design.md` whose `Contexts` line names one context, run `wfctl arch context`, and check the printed records and the footer line that names the count and `wfctl arch context --all`.

**Verification**:

- `uv run pytest -q tests/test_remaining_commands.py -k arch_context`
- By hand: `quickstart.md` step 1

### Tests for User Story 1

- [X] T006 [US1] Write failing tests in the `wfctl arch context` section of `tests/test_remaining_commands.py` for spec.md US1 scenarios 1 to 4:
  1. When the line names `install-and-drift`, a record governing only `session-continuity` isn't printed, and the footer reads ``1 accepted record governs only other contexts — `wfctl arch context --all` prints them``.
  2. A record with no `governs` field prints.
  3. A record governing `install-and-drift, workmux` prints.
  4. A branch whose contexts cover every governed record prints exactly today's output.
  5. When every accepted record carries a `governs` field and none of them names a listed context, the header reads `# Architectural contract — 0 of M accepted decisions apply to this branch`, not `no accepted decisions`, and the footer counts all M as left out (FR-002).

  Also check the narrowed header, `# Architectural contract — N of M accepted decisions apply to this branch`, with the `Contexts:` line under it, and the singular form `1 of M accepted decisions applies` from `contracts/cli.md`. Check that the existing `N records not shown (…)` line is unchanged and still last. Verify they fail with `uv run pytest -q tests/test_remaining_commands.py -k arch_context`.

### Implementation for User Story 1

- [X] T007 [US1] In `wfctl/cli.py`, inside `arch_context_cmd` only, replace the separate `_arch.in_force(_arch.load_records(root))` call with `_evidence.records_for_branch(repo_root, branch)`, taking `branch` from `_resolve_context()`. Keep `records = _arch.load_records(root)`, since the excluded-by-status and unreadable counts still need it. When `selection.narrowed`, print the narrowed header and the `Contexts:` line, and print the left-out line above the `records not shown` line. Branch on `selection.narrowed` before the existing `if accepted:` check, since a selection that leaves out every record has no records to print but still has a narrowed header to show. Leave `status` and `review start` alone, since #711 is changing them. Verify with `uv run pytest -q tests/test_remaining_commands.py -k arch_context`.
- [X] T008 [US1] Validate User Story 1 with `uv run pytest -q tests/test_remaining_commands.py` and `quickstart.md` step 1, which expects 24 of 28 records and 4 left out — merge gate

**Checkpoint**: A branch that lists its contexts gets the narrowed set.

---

## Phase 4: User Story 2 - A branch that hasn't listed its contexts sees every record (Priority: P1)

**Goal**: When wfctl can't tell which records apply, it prints every one and says why.

**Independent Test**: Run `wfctl arch context` with no spec folder, then with a `design.md` that has no `Contexts` line, and check that every accepted record prints with the reason line.

**Verification**:

- `uv run pytest -q tests/test_remaining_commands.py -k arch_context`
- By hand: `quickstart.md` step 2

### Tests for User Story 2

- [X] T009 [US2] Write failing tests in `tests/test_remaining_commands.py` for spec.md US2 scenarios 1 to 4:
  1. With no spec folder, every record prints, followed by `Every accepted record is printed, since design.md lists no contexts for this branch yet.`
  2. A `design.md` with no `Contexts` line, or an empty one, prints the same as scenario 1.
  3. A line naming `sesion-continuity` prints every record, followed by `⚠ Every accepted record is printed, since design.md lists sesion-continuity, which isn't on the domain page.`
  4. A repo whose domain page has no name list prints exactly today's output, with neither line.

  Verify they fail with `uv run pytest -q tests/test_remaining_commands.py -k arch_context`.

### Implementation for User Story 2

- [X] T010 [US2] In `arch_context_cmd` in `wfctl/cli.py`, print the `unlisted` and `unknown` reason lines from the `Selection`, above the `records not shown` line. Escape the unknown name before printing it, because it comes from `design.md` and rich would read a bracket in it as markup. Verify with `uv run pytest -q tests/test_remaining_commands.py -k arch_context`.
- [X] T011 [US2] Validate User Story 2 with `uv run pytest -q tests/test_remaining_commands.py` and `quickstart.md` step 2, which expects all 28 records and the "lists no contexts" line — merge gate

**Checkpoint**: A binding record is never left out when the branch's contexts are unknown.

---

## Phase 5: User Story 3 - The session report and `--all` agree with the narrowed set (Priority: P2)

**Goal**: `--all` prints every record, and the session report's `Records` line and JSON give the same counts as `arch context`, from the same function.

**Independent Test**: With a `Contexts` line that leaves records out, compare `wfctl status --session` with `wfctl arch context`, then check that `wfctl arch context --all` prints every record.

**Verification**:

- `uv run pytest -q tests/test_remaining_commands.py tests/test_session_report.py tests/test_cli_status.py`
- `uv run python .github/scripts/check_imports.py`
- By hand: `quickstart.md` steps 3 and 4

### Tests for User Story 3

- [X] T012 [P] [US3] Write a failing test in `tests/test_remaining_commands.py` for spec.md US3 scenario 3. On a branch that would narrow, `wfctl arch context --all` prints every accepted record with today's header, and with neither the `Contexts:` line nor any reason line. Verify it fails with `uv run pytest -q tests/test_remaining_commands.py -k arch_context`.
- [X] T013 [P] [US3] Update `tests/test_session_report.py` for US3 scenarios 1, 2, and 4. Change the `Readers` fixture at line 230 from `accepted_records=lambda: 27` to `records=lambda: (27, None)`, and keep the existing ``Records: 27 accepted · `wfctl arch context` prints them`` assertion. Add a test with `records=lambda: (28, 6)` that checks for ``Records: 6 of 28 accepted apply to this branch · `wfctl arch context` prints them, `--all` prints every one`` and `payload["applying_records"] == 6`, and check that the payload that isn't narrowed carries `applying_records` as `None`. Verify they fail with `uv run pytest -q tests/test_session_report.py`.
- [X] T014 [US3] Add `applying_records` to the expected session key set in `tests/test_cli_status.py` at line 364. Verify it fails with `uv run pytest -q tests/test_cli_status.py`.
- [X] T015 [US3] Write a failing test in `tests/test_cli_status.py` that checks FR-010 through the real readers, as plan review PR-004 asked. On one temporary spec folder whose `Contexts` line names one context, run `wfctl status --session --json` and `wfctl arch context` through the CLI runner. Check that `applying_records` equals the number of slugs `arch context` printed, and that `accepted_records` equals that number plus the left-out count. A fake reader can't catch `default_readers` passing the wrong branch, and this test can. Verify it fails with `uv run pytest -q tests/test_cli_status.py`.

### Implementation for User Story 3

- [X] T016 [US3] Add an `--all` option to `arch_context_cmd` in `wfctl/cli.py`. When it's set, skip `records_for_branch` and print `_arch.in_force(records)` with today's output, so printing every record never depends on the domain page (`design.md §Level-3 consequences`, item 3). Verify with T012.
- [X] T017 [US3] In `wfctl/_session_report.py`, replace `Readers.accepted_records` with `records: Callable[[], tuple[int, int | None]]`, which returns `(accepted, applying)`. `applying` is `len(selection.records)` when the set is narrowed and `None` otherwise, and `accepted` is `len(selection.records) + selection.left_out`. Build it in `default_readers` from `_evidence.records_for_branch(repo_root, branch)`, and drop the `_arch` import there. In `build_session_report`, set `accepted_records` and `applying_records` from it. In `render_session_report`, print the narrowed `Records` line when `applying_records` isn't `None`, and today's line otherwise. Verify with `uv run pytest -q tests/test_session_report.py tests/test_cli_status.py`.
- [X] T018 [US3] In `wfctl/_session_report.py`, change "ten session keys" in the `build_session_report` docstring and "lists ten" in the `render_session_report` docstring to eleven, to match `contracts/cli.md` (plan review PR-003). Verify with `grep -n "ten session\|lists ten" wfctl/_session_report.py` printing nothing.
- [X] T019 [US3] Delete the line `_session_report.py -> _arch.py` from `.github/scripts/check_imports.baseline`, since T017 removes the import it named (plan review PR-002). The check fails on a baseline line that matches no import, so verify with `uv run python .github/scripts/check_imports.py` passing with no new line.
- [X] T020 [US3] Validate User Story 3 with `uv run pytest -q tests/test_remaining_commands.py tests/test_session_report.py tests/test_cli_status.py`, `uv run python .github/scripts/check_imports.py`, and `quickstart.md` steps 3 and 4 — merge gate

**Checkpoint**: Both readers report the same selection, and `--all` prints every record.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Tell the agent about the narrowing in the two skills, and commit the release note.

**Verification**:

- `uv run pytest -q tests/test_skill_cross_references.py tests/test_start_session_commands.py`
- `uv run wfctl install-skills --yes --agent claude`, then `uv run wfctl doctor`
- By hand: the check in `spec.md §Validation Strategy`

- [X] T021 [P] In `wfctl/agents/skills/start-session/SKILL.md`, edit step 2 to say `wfctl arch context` may print only the records for the branch's contexts, and that `wfctl arch context --all` prints the rest. In step 7's In force bullet, say to report the narrowed count when the header gives one (FR-011). Load the `writing-style` skill first. Verify with `uv run pytest -q tests/test_skill_cross_references.py tests/test_start_session_commands.py`.
- [X] T022 [P] In `wfctl/agents/skills/architecture-decisions/SKILL.md`, near line 71 where the `governs` field is described, say that a record binding every change leaves the `governs` field out, and that `arch context` then prints it on every branch (FR-012). Load the `writing-style` skill first. Verify with `uv run pytest -q tests/test_skill_cross_references.py`.
- [X] T023 [P] Create the release note with `uv run towncrier create 700.change.md --content "…"`. It says what a user of wfctl will notice: `wfctl arch context` and the session report's `Records` line narrow to the branch's contexts, and `--all` prints every record. Load the `writing-style` skill first. Verify with the release-note check in `uv run wfctl verify`.
- [X] T024 Run `uv run wfctl install-skills --yes --agent claude`, then `uv run wfctl doctor`, and read the installed `start-session` step 2 to check that it reads well. Verify with `doctor` exiting 0.
- [X] T025 Run the by-hand check in `spec.md §Validation Strategy`. With `WFCTL_SPEC_DIR` pointed at a scratch spec folder whose `Contexts` line names one context, the output includes every record for that context and every record with no `governs` field. On a branch with no spec folder, it prints every record. Verify by comparing the printed slugs with the `governs` fields under `docs/architecture/`.
- [X] T026 Validate the feature with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and `uv run wfctl verify` — merge gate

---

## Dependencies & Execution Order

### Phase dependencies

1. Phase 2 blocks every story.
2. US1 (Phase 3) and US2 (Phase 4) both edit `arch_context_cmd`, so US1 goes first and US2 follows.
3. US3 (Phase 5) depends on Phase 2. Its session report half (T013, T014, T017, T018, T019) can start once Phase 2 lands. Its `--all` half (T012, T016) and the wiring test (T015) need US1's change to `arch_context_cmd`.
4. Phase 6 follows the stories. T021 to T023 edit prose, so they can start any time after Phase 2.

### Within each story

- Tests are written and run red before the implementation.
- The phase's validation task closes it.

### Parallel opportunities

- T001 and T003 are in different files, but T003's tests need the shape `select` returns, so T003 follows T002.
- In US3, T012 and T013 are in different files and can be written together. T014 and T015 share `tests/test_cli_status.py`, so they run one after the other.
- T021, T022, and T023 edit three different files and can run together.

## Parallel Example: User Story 3

```text
T012 tests/test_remaining_commands.py   --all output
T013 tests/test_session_report.py       Readers fixture and Records line
```

## Implementation Strategy

### MVP first

1. Phase 2, the selection rule.
2. Phase 3, US1, so `arch context` narrows.
3. Phase 4, US2, so the agent learns why nothing was left out. `select` already prints every record when the branch's contexts are missing or misspelled, but without US2's lines the agent can't tell that from a branch where every record applies, so US2 ships with it.
4. Stop and validate with `quickstart.md` steps 1 and 2.

### Incremental delivery

1. Phases 2 to 4 give the narrowed `arch context`.
2. Phase 5 makes the session report agree and adds `--all`.
3. Phase 6 tells the agent about it in the skills.

## Notes

- Keep `cli.py` edits inside `arch_context_cmd`, since #711 edits `review start` in the same file.
- No task adds a `governs` field to an accepted record.
- Commit after each phase's validation task.
~~~~
