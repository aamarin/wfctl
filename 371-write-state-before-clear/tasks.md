# Tasks: Session restart that writes its handoff first

**Input**: Design documents from `specs/371-write-state-before-clear/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/hook-session-restart.md, quickstart.md

**Tests**: Required. The decision is critical-path logic that types into a person's pane; every rule in `data-model.md` gets a test, and the installer change touches a consumer-owned file.

**Organization**: Grouped by user story. Phase 2 carries the installer identity and the parsing every story reads.

Design records that bind these tasks (from `design.md`):
`docs/architecture/wfctl-performs-the-session-restart.md`,
`docs/architecture/a-managed-hook-is-owned-by-its-subcommand.md`,
`docs/architecture/design/371-the-session-restart-sends-from-a-detached-worker.md`,
`docs/architecture/design/371-the-session-restart-instruction-lives-in-end-session.md`,
`docs/architecture/design/371-the-session-restart-threshold-is-an-environment-variable.md`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup

**Purpose**: Establish the baseline the change is measured against.

- [X] T001 Confirm the baseline before any change: run `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/` on the branch head; verify with all three exiting 0
- [X] T002 Validate Setup with `uv run pytest -q` — merge gate

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Let Stop carry two wfctl rows, and give the hook the pure readers every story depends on.

**⚠️ CRITICAL**: US1 cannot install until T003–T008 land.

### Installer identity (FR-019–FR-022; record `a-managed-hook-is-owned-by-its-subcommand`)

- [X] T003 [P] Write failing tests in `tests/test_settings_merge.py`: `merge_hook` with a subcommand replaces only the row with that subcommand and leaves a second wfctl row on the same event; two rows with the same subcommand collapse to one; `prune_unshipped` removes a wfctl row whose subcommand is not shipped and leaves consumer rows; `managed_command(settings, event, subcommand)` returns that subcommand's row only; `MANAGED_PREFIX` still does not claim `wfctl hookup`
- [X] T004 Implement `subcommand_of(command)`, subcommand-aware `merge_hook` and `managed_command`, and `prune_unshipped` in `wfctl/_settings.py`; verify with `uv run pytest tests/test_settings_merge.py -q`
- [X] T005 [P] Write failing tests in `tests/test_install_hook_merge.py`: a settings file carrying only `wfctl hook response-shape` on Stop gains a second Stop row on install and keeps the first; a second install changes nothing (file not rewritten); a wfctl row on Stop with an unshipped subcommand is pruned; doctor reports a missing `session-restart` row and a missing `response-shape` row as two separate findings with their own `_HOOK_GONE` text; uninstall removes both Stop rows
- [X] T006 Change `MANAGED_HOOKS` in `wfctl/cli.py` to `(event, command)` pairs, key `_HOOK_GONE` by `(event, subcommand)`, and update `_merge_hooks` (targets, `prior` keyed `(rel, event, subcommand)`, prune per event) and `_check_managed_hooks`/`_report_hook_drift` to iterate pairs; leave `_unmerge_hooks` calling `remove_hooks` per event; verify with `uv run pytest tests/test_install_hook_merge.py tests/test_install_skills.py -q`

### Readers the decision needs

- [X] T007 [P] Write failing tests in `tests/test_restart_occupancy.py`: last `message.usage` record wins, sum of `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`; missing file, no usage record, malformed lines only, and a non-dict `usage` each return `None`
- [X] T008 Create `wfctl/_restart.py` with `DEFAULT_THRESHOLD = 200000`, `threshold(environ)` per research R11, `occupancy(path)` per R1, and `read_events(state_dir)` returning parsed dicts in line order and skipping malformed lines; stdlib plus `wfctl._paths`/`wfctl._io` only; verify with `uv run pytest tests/test_restart_occupancy.py -q`
- [X] T009 Add `create: bool = True` to `resolve_agent_dir` in `wfctl/_paths.py` so the hook can compute the state dir without creating it (research R3); verify with a test in `tests/test_paths.py` that `create=False` on a fresh `XDG_STATE_HOME` returns the path and creates nothing
- [X] T010 Validate Foundational with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` — merge gate

**Checkpoint**: Stop can hold two wfctl rows; occupancy, threshold and events are readable.

---

## Phase 3: User Story 1 — A full session restarts itself and the next one picks up where it stopped (Priority: P1) 🎯 MVP

**Goal**: Over the threshold, send `/end-session restart`; once a stop lands after that send, send `/clear` and `/start-session`; the restart turn records a continued stop and asks nothing.

**Independent Test**: In a workmux Claude pane with a low threshold, the pane receives `/end-session restart`, then `/clear` and `/start-session`; the new session quotes the handoff just written; the event log carries a continued `end` between the two sends.

**Verification**:

- Automated: `tests/test_restart_decide.py` (US1 rules), `tests/test_restart_send.py`, `tests/test_restart_hook_cli.py`, `tests/test_restart_end_session.py`, `tests/test_install_hook_merge.py`
- Manual: `quickstart.md` § Live, steps 1–6; `/end-session restart` typed by hand in this worktree
- Evidence: continued `end` event after a `session-restart-send` for `/end-session restart`; transcript id changes after `/clear`; `.claude/settings.json` Stop carries both rows

### Tests for User Story 1 ⚠️

- [X] T011 [P] [US1] Write failing tests in `tests/test_restart_decide.py` for `decide()`: under threshold → nothing (and `find_handle` not called); unreadable occupancy → nothing; over threshold with no events for the session → end to the handle; `planned_end` with no send yet → nothing; `sent_end` exit 0 then an `end` event later in the log → clear; an `end` event *before* the send does not count; an `end` with `continued: false` counts (clarification Q1); a `session-restart` for another session is ignored; `/end-session restart` is never planned twice for one session
- [X] T012 [P] [US1] Write failing tests in `tests/test_restart_send.py`: with a stub `workmux` on `PATH` that appends argv, its parent pid and a timestamp to a file, the worker waits for a still-running parent pid to exit before the first send, sends texts in order, appends one `session-restart-send` event per text with `session`, `text`, `exit`; a stub that exits 3 records `exit: 3`; a stub that sleeps past the timeout records `exit: -1`; the worker exits 0 in every case
- [X] T013 [P] [US1] Write failing tests in `tests/test_restart_hook_cli.py`: `wfctl hook session-restart` with a payload under threshold prints nothing, exits 0 and creates no state dir; over threshold with a stub `workmux list --json` naming the repo root, it writes a `session-restart` event with `decision: end` and spawns the worker detached — run the hook as a child process (`[sys.executable, "-c", "from wfctl._entry import main; main()", "hook", "session-restart"]`), not in-process, because the worker waits for its parent pid to exit and pytest's never does; assert the child exits before the stub's send timestamp; garbage stdin, a non-dict payload and an exception inside `decide` each exit 0 with no output; `_entry.main` dispatches exactly `["hook", "session-restart"]` without importing `wfctl.cli`
- [X] T014 [P] [US1] Write failing tests in `tests/test_restart_end_session.py`: the text `_restart` sends for *end* is exactly `/end-session restart`; `wfctl/agents/skills/end-session/SKILL.md` has a section keyed on `restart` that names `wfctl end --continued` and names steps 6 and 7 as skipped; `wfctl/agents/commands/end-session.md` carries `$ARGUMENTS`

### Implementation for User Story 1

- [X] T015 [US1] Implement `Decision` and `decide()` for the nothing/end/clear rules of `data-model.md` in `wfctl/_restart.py`, taking `find_handle` as a zero-arg callable invoked only on a send path; verify with `uv run pytest tests/test_restart_decide.py -q`
- [X] T016 [US1] Implement `find_handle(repo_root)` in `wfctl/_restart.py`: `workmux list --json` with a timeout, match `path` to the repo root, return `handle` or `None` on no match, non-zero exit, `OSError` or bad JSON (research R5); verify with a stub-`workmux` case in `tests/test_restart_hook_cli.py`
- [X] T017 [US1] Create `wfctl/_restart_send.py` runnable as `python -m wfctl._restart_send '<json plan>'`: parse the plan, poll the parent pid (cap 10 s), sleep 2 s, `workmux send` each text under `subprocess.run(timeout=10)`, append `session-restart-send`, sleep 5 s between texts, exit 0 always (research R6; record `371-the-session-restart-sends-from-a-detached-worker`); verify with `uv run pytest tests/test_restart_send.py -q`
- [X] T018 [US1] Implement `run_hook(stdin_bytes, environ) -> str | None` in `wfctl/_restart.py`: parse payload, threshold, occupancy early-return, resolve repo root via `git -C cwd rev-parse --show-toplevel`, branch, state dir with `create=False`, events, `decide`, append `session-restart` for any non-nothing decision, spawn the worker with `start_new_session=True` and `DEVNULL` stdio for end/clear, return the stdout JSON or `None`; the whole body under one `except Exception`; verify with `uv run pytest tests/test_restart_hook_cli.py -q`
- [X] T019 [US1] Wire `["hook", "session-restart"]` into `wfctl/_entry.py`'s fast path and register a `session-restart` command on `hook_app` in `wfctl/cli.py` that calls `run_hook` (so `--help` lists it); a terminal on stdin prints one usage line to stderr and exits 0; verify with `uv run pytest tests/test_restart_hook_cli.py tests/test_guard_entry.py -q`
- [X] T020 [US1] Add `_SESSION_RESTART = "session-restart"`, `RESTART_HOOK_COMMAND = f"{MANAGED_PREFIX}{_SESSION_RESTART} 2>/dev/null || true"`, its `(STOP_EVENT, RESTART_HOOK_COMMAND)` pair in `MANAGED_HOOKS`, and its `_HOOK_GONE` text in `wfctl/cli.py`; verify with `uv run pytest tests/test_install_hook_merge.py -q`
- [X] T021 [US1] Add a `## User Input` block with `$ARGUMENTS` to `wfctl/agents/commands/end-session.md`, and a section to `wfctl/agents/skills/end-session/SKILL.md` that applies only when the input is exactly `restart`: run `wfctl end --continued` at step 3, fill the summary in full, skip steps 6 and 7, and write in the summary that the tree was left as found; any other input changes nothing (record `371-the-session-restart-instruction-lives-in-end-session`); verify with `uv run pytest tests/test_restart_end_session.py tests/test_skill_commands.py tests/test_skill_cross_references.py -q`
- [X] T022 [US1] Install and exercise: `uv run wfctl install-skills --agent claude --yes`, `uv run wfctl doctor` exits 0, `.claude/settings.json` Stop carries both rows, and `/end-session restart` typed by hand in this worktree records `"continued": true` and asks no commit or tracker question; verify by the `events.jsonl` tail and the settings file
- [X] T023 [US1] Validate User Story 1 with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` — merge gate

**Checkpoint**: A restart over the threshold hands off, clears and resumes.

---

## Phase 4: User Story 2 — A restart that cannot finish safely says so in the pane (Priority: P2)

**Goal**: Hold when no stop landed, skip when there is no pane, report a `/clear` that did not take or a send that never went — each once, never retried.

**Independent Test**: With `workmux` stubbed, drive `decide` and `run_hook` through each unsafe condition; each yields its `systemMessage` once and no send.

**Verification**:

- Automated: `tests/test_restart_decide.py` (US2 rules), `tests/test_restart_hook_cli.py` (stdout contract)
- Manual: `quickstart.md` § Decide by hand with a stub `workmux` that exits 1
- Evidence: one `session-restart` event per reported condition; `systemMessage` text matches `contracts/hook-session-restart.md`

### Tests for User Story 2 ⚠️

- [X] T024 [P] [US2] Add failing tests to `tests/test_restart_decide.py`: `sent_end` exit 0 and no later `end` → hold, then nothing on the next Stop, then clear once an `end` lands; over threshold with `find_handle` → `None` → skip, then nothing; landed with no handle → skip once; `planned_clear` with no send → nothing (FR-010a); `sent_clear` exit 0 from the same session → not-taken once, then nothing; `sent_clear` exit ≠ 0 → not-taken carrying the exit; `sent_end` exit ≠ 0 → not-taken, and `/end-session restart` is not planned again; threshold `0` → nothing even with a restart in progress
- [X] T025 [P] [US2] Add failing tests to `tests/test_restart_hook_cli.py`: each of hold, skip, not-taken exit 0 and not-taken exit ≠ 0 prints exactly `{"systemMessage": …}` with the text in `contracts/hook-session-restart.md`, including the `/clear` send's `HH:MMZ` and the failed send's text and exit

### Implementation for User Story 2

- [X] T026 [US2] Extend `decide()` in `wfctl/_restart.py` with the hold, skip and not-taken rules and the `reported(d)` derivation from `data-model.md`; verify with `uv run pytest tests/test_restart_decide.py -q`
- [X] T027 [US2] Add the four message builders to `wfctl/_restart.py` and have `run_hook` emit them as `systemMessage` for the reporting decisions; verify with `uv run pytest tests/test_restart_hook_cli.py -q`
- [X] T028 [US2] Validate User Story 2 with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` — merge gate

**Checkpoint**: No unsafe condition clears, and each one is visible once.

---

## Phase 5: User Story 3 — A developer moves the threshold or turns the restart off (Priority: P3)

**Goal**: `WFCTL_RESTART_THRESHOLD` sets the number; `0` turns it off; 200000 otherwise.

**Independent Test**: `threshold()` and `run_hook` under unset, empty, digits, `0`, `-5`, `1e5`, `200_000`, `abc`.

**Verification**:

- Automated: `tests/test_restart_decide.py` (threshold cases), `tests/test_restart_end_session.py` (single definition)
- Manual: `quickstart.md` § Live step 2 — the restart fires at the exported value
- Evidence: `session-restart` event's `threshold` field equals the exported value

### Tests for User Story 3 ⚠️

- [X] T029 [P] [US3] Add failing tests to `tests/test_restart_decide.py`: `threshold()` is 200000 for unset, empty, `abc`, `-5`, `1e5`, `200_000`; the integer for `150000` and ` 150000 `; `0` for `0`; `run_hook` at 10,000,000 tokens with `0` prints nothing and writes nothing
- [X] T030 [P] [US3] Add a failing test to `tests/test_restart_end_session.py` that the literal `200000` appears exactly once across `wfctl/**/*.py`

### Implementation for User Story 3

- [X] T031 [US3] Adjust `threshold()` in `wfctl/_restart.py` to the strip-then-`isdigit` rule if T008 did not already, and remove any second `200000`; verify with `uv run pytest tests/test_restart_decide.py tests/test_restart_end_session.py -q`
- [X] T032 [US3] Validate User Story 3 with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` — merge gate

**Checkpoint**: The restart is tunable and can be turned off without a file edit.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T033 [P] Update `README.md`: add `session-restart` to the `hook` row (line ~164) and a `Stop` row to the managed-hooks table (line ~492), and `WFCTL_RESTART_THRESHOLD` to the environment table (line ~761); verify by `grep -n "session-restart\|WFCTL_RESTART_THRESHOLD" README.md`
- [X] T034 Measure the nothing path: time 20 runs of `wfctl hook session-restart` with an under-threshold payload on this branch's transcript and record the median in the PR description's testing section; verify median < 0.2 s (SC-004)
- [X] T035 Run `quickstart.md` § Live in a workmux Claude pane after removing `~/.claude/recycle-hook.sh` from user settings (a person's edit — ask); verify SC-001 by the new session quoting the restart turn's handoff, the continued `end`, the unchanged tree and the changed transcript id
- [X] T036 Validate the feature with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/ && uv run wfctl doctor` — merge gate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none
- **Foundational (Phase 2)**: after Setup; blocks all stories
- **US1 (Phase 3)**: after Foundational
- **US2 (Phase 4)**: after T015 and T018 (extends `decide` and `run_hook`); independent of T017, T021
- **US3 (Phase 5)**: after T008 and T018
- **Polish (Phase 6)**: after US1–US3; T035 needs a person for the user-settings edit

### Within Each Story

- Tests first, failing, then implementation
- `decide` (T015) before `run_hook` (T018) before wiring (T019, T020)
- T021 (skill) is independent of T015–T020

### Parallel Opportunities

- T003 ‖ T005 ‖ T007 (different test files); T004 and T006 are sequential (T006 calls T004's API)
- T011 ‖ T012 ‖ T013 ‖ T014
- T017 ‖ T021 once their tests exist
- T024 ‖ T025; T029 ‖ T030
- T033 anytime after T020

## Parallel Example: User Story 1

```bash
Task: "Write failing decide() tests in tests/test_restart_decide.py"
Task: "Write failing worker tests in tests/test_restart_send.py"
Task: "Write failing hook CLI tests in tests/test_restart_hook_cli.py"
Task: "Write failing end-session tie tests in tests/test_restart_end_session.py"
```

## Implementation Strategy

### MVP First

1. Phase 1, Phase 2 (installer identity is independently shippable)
2. Phase 3 → stop and run T022 and the live check
3. Phase 4 before enabling on-by-default in anyone else's pane: US1 alone clears after a handoff turn that recorded no stop is impossible (FR-003 is in US1), but it is silent on D/E/F

### Incremental Delivery

1. Foundational → one PR-sized slice (installer identity)
2. US1 + US2 → the restart and its guards
3. US3 + Polish

## Notes

- Tests assert on output: pin `NO_COLOR` where rich renders
- The classifier may refuse writing the spawn or the worker (plan § Risks); stop and `wfctl blocked`, do not route around it
- `pyproject.toml` version is not bumped
