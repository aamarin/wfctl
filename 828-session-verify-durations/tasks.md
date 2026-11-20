# Tasks: wfctl measures feature time and verify cost

**Input**: Design documents from the `828-session-verify-durations` spec folder: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Design records**: `docs/architecture/design/828-verify-measures-each-child.md` (level 3) and `docs/architecture/worktree-span-read-from-git.md` (level 2). Both are proposed, so implementation waits for the user to accept or reject them.

**Tests**: Every story writes its tests first and checks that they fail before the implementation lands. Tests that touch console output pin `NO_COLOR`. Test names are sentences, and each docstring names the failure the test catches.

**Plan review carry-over**: the second plan review left five MINOR findings open (PR-008 to PR-012). The spec half of PR-008 and PR-010 is fixed in `spec.md`. The rest lands here, and each task that resolves one names it.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel with the other [P] tasks in its phase (different files, no dependency on an incomplete task)
- **[Story]**: the user story the task serves (US1, US2, US3)

---

## Phase 1: Setup

**Purpose**: the release note every change carries.

- [x] T001 Create `changes/828.addition.md` with `uv run towncrier create 828.addition.md --content "…"`, saying what a wfctl user notices: `wfctl verify` records each command's duration and peak memory, the removal hook records how long each worktree was open, and `wfctl timings` summarizes both. Load `writing-style` first. Verify with `uv run python .github/scripts/check_release_note.py` or the `release-note` step of `uv run wfctl verify`.

---

## Phase 2: Foundational

**Purpose**: the one helper US2 and US3 share. The span's `created` and an open worktree's creation time have to come from the same function, or the read-time drop in US3 compares two differently rounded values (PR-010).

- [x] T002 Add a test in `tests/test_timings.py` that makes a real linked worktree with `git worktree add` in `tmp_path`, sets its `commondir` modified time to a value with a fractional second via `os.utime`, and checks that the helper returns that time floored to the whole second as a timezone-aware UTC `datetime`, and returns `None` for an admin folder with no `commondir`. Run it and confirm it fails.
- [x] T003 Add `worktree_created(admin_dir: Path) -> datetime | None` to `wfctl/evidence/_events.py`. It reads `<admin_dir>/commondir`'s `st_mtime`, floors it with `int()`, and returns it as UTC. It returns `None` when the file doesn't exist. A comment says why `commondir` and not `gitdir` (research R1: `git worktree move` and `repair` rewrite `gitdir`, nothing a worktree normally sees rewrites `commondir`). Verify with T002.

**Checkpoint**: T002 passes. `uv run ruff check wfctl/ tests/` and `uv run mypy` are green.

---

## Phase 3: User Story 1 - Each verify command's duration and peak memory (Priority: P1) 🎯 MVP

**Goal**: `wfctl verify` records the run's total duration and, for each command, its exit code, duration, and the peak memory of the largest single process it started, without changing `verify.json` or the verdict.

**Independent Test**: configure two commands in `wfctl.json`, the first using more memory than the second, run `wfctl verify`, and read the new `verify` event. Each command has its own duration and peak, and the second's peak is below the first's.

**Verification**:

- Automated: `uv run pytest -q tests/test_verify.py`
- Manual: `quickstart.md` step 1
- Evidence: the last `verify` line in the branch's `events.jsonl` carries `seconds` and one `commands` entry per command, matching `contracts/events.md`

### Tests for User Story 1

> Write these first and confirm they fail.

- [x] T004 [P] [US1] In `tests/test_verify.py`, test that two commands, the first allocating about 300 MB and the second about 50 MB, record the second command's `peak_bytes` below the first's and within 20% of 50 MB plus the peak of a child that allocates nothing. The docstring names the failure: the shared `RUSAGE_CHILDREN` counter only goes up, so the baseline reports 300 MB for both. Add a second test: a command that starts a grandchild allocating about 300 MB and waits for it records a peak within 20% of 300 MB, since the largest process it waited for counts (acceptance scenario 4 of User Story 1).
- [x] T005 [P] [US1] In `tests/test_verify.py`, test that a missing executable is recorded with `exit` 127, a `seconds` value, and `peak_bytes` `None`, that a file without the execute bit is recorded with `exit` 126, and that the commands after each still run (research R2).
- [x] T006 [P] [US1] In `tests/test_verify.py`, replace `test_interruption_writes_nothing_and_preserves_the_previous_record`'s patch of `subprocess.run`, which the `Popen` change bypasses. The new test starts a real `sleep 30` child, patches `os.wait4` to raise `KeyboardInterrupt` on its first blocking call (flags `0`) and pass through after that, and checks three things: `os.kill(pid, 0)` raises `ProcessLookupError`, no `verify` event was written, and `verify.json`'s bytes are unchanged from before the run (PR-012).
- [x] T007 [P] [US1] In `tests/test_verify.py`, test that a child allocating 200 MB records a `peak_bytes` within 20% of 200 MB, on whichever platform runs the suite. It stays in the default suite and runs on every CI run, since the user chose that over a skip-by-default marker or a manual quickstart step. The docstring names the failure: Linux reports `ru_maxrss` in kilobytes and macOS in bytes, so a missed conversion is off by 1,024.
- [x] T008 [P] [US1] In `tests/test_verify.py`, test `_peak_bytes` with `sys.platform` patched to `darwin` and to `linux`, so both conversions run on every platform even though CI runs only Linux (SC-002).
- [x] T009 [P] [US1] In `tests/test_verify.py`, test that the `verify` event carries `seconds` as a float with one decimal and `commands` in `verify` list order, with `command` joined by spaces the same way `failed` is, and that `verify.json` holds exactly the keys it held before (FR-005). Also check with `capfd` that a command's own output line reaches the terminal while it runs, since `Popen` inherits stdout (FR-003).

### Implementation for User Story 1

- [x] T010 [US1] In `wfctl/_verify.py`, add `CommandResult(argv, exit, seconds, peak_bytes)` as a `NamedTuple` and `_peak_bytes(ru_maxrss: int) -> int`, which multiplies by 1024 unless `sys.platform == "darwin"`. Verify with T008.
- [x] T011 [US1] In `wfctl/_verify.py`, change `run_verification` to return `list[CommandResult]`. Start each command with `subprocess.Popen(argv, cwd=repo_root)`, read `time.monotonic()` around `os.wait4(proc.pid, 0)`, and set `proc.returncode` from `os.waitstatus_to_exitcode(status)` so the `Popen` object never reaps the child again. `FileNotFoundError` and `NotADirectoryError` record 127, and `PermissionError` records 126, each with the elapsed time and `peak_bytes=None`. Keep the console lines, the inherited output, and the run-every-command behaviour. Update the docstring to say the measurement comes from the child's own `wait4` result. Verify with T004, T005, and T007.
- [x] T012 [US1] In `wfctl/_verify.py`, handle an interrupt in `run_verification`. The `try` starts on the line after `Popen` returns. On `KeyboardInterrupt`, poll `os.wait4(pid, os.WNOHANG)` for up to 0.25 seconds, matching `subprocess.run`, then kill the child, reap it with `os.wait4(pid, 0)`, set `proc.returncode`, and re-raise. Verify with T006.
- [x] T013 [US1] In `wfctl/_verify.py`, change `perform` to build `exit_code` and `failed` from the results, read `time.monotonic()` from before the first `code_identity` call to after the last, and pass `seconds=round(total, 1)` and `commands=[{"command", "exit", "seconds", "peak_bytes"}, …]` to `append_event`. Leave `write_record` and the record's keys unchanged. Verify with T009.
- [x] T014 [US1] Update every existing test in `tests/test_verify.py` and any other caller of `run_verification` for the new return type. Find callers with `grep -rn run_verification wfctl/ tests/`. Verify with `uv run pytest -q tests/test_verify.py`.
- [x] T015 [US1] Validate User Story 1 with `uv run pytest -q tests/test_verify.py`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate.

---

## Phase 4: User Story 2 - A worktree's lifetime, recorded at removal (Priority: P1)

**Goal**: when the removal hook lets a removal go ahead, it writes one `worktree-span` event with the worktree's creation time from git and its removal time. A refusal, a missing `commondir`, or an unknown branch writes nothing, and no span failure changes what the hook decides or prints about the removal.

**Independent Test**: create a worktree, remove it through the removal hook, and read the new `worktree-span` event in the branch's event log. `created` matches `commondir`'s modified time to the second, and `removed` matches when the hook ran.

**Verification**:

- Automated: `uv run pytest -q tests/test_worktree_remove.py`
- Manual: `quickstart.md` step 3, run by the user, since the worktree guard refuses an agent that creates or removes a second worktree
- Evidence: one `worktree-span` line per allowed removal, matching `contracts/events.md`

### Tests for User Story 2

> Write these first and confirm they fail.

- [x] T016 [P] [US2] In `tests/test_worktree_remove.py`, test that a removal the hook allows on its success path writes exactly one `worktree-span` event to `resolve_agent_dir(repo_root, branch)`, with `created` equal to the worktree's `commondir` modified time floored to the second, and `removed` equal to the event's `ts`.
- [x] T017 [P] [US2] In `tests/test_worktree_remove.py`, test that an unexpected exception raised after `repo_root` and `branch` are resolved reaches the catch-all, prints its existing `⚠ worktree-remove failed` line, exits 0, and still writes one span (FR-007).
- [x] T018 [P] [US2] In `tests/test_worktree_remove.py`, test that no span is written in three cases: a refused removal (`typer.Exit(1)`), the main checkout (no `commondir`), and an exception raised before `branch` is assigned, such as `get_repo_root` raising `SystemExit`. The third case must not raise `NameError` from the catch-all (PR-008, FR-009).
- [x] T019 [P] [US2] In `tests/test_worktree_remove.py`, test that when reading the creation time or writing the event raises, the hook prints one `⚠ couldn't record this worktree's lifetime (<reason>)` line, its exit code is unchanged, and every other line it prints is the same as without the failure (FR-010). Cover both the success path and the catch-all path.
- [x] T020 [P] [US2] In `tests/test_worktree_remove.py`, test that a worktree detached mid-rebase writes its span to the folder `resolve_branch` names for it, the short SHA, the same folder `_save_unsaved` uses for that worktree (PR-009). The docstring says why: the span follows the hook's other writes, and `wfctl timings` matches it to an open worktree by creation time alone, so the folder name doesn't affect the drop.

### Implementation for User Story 2

- [x] T021 [US2] In `wfctl/evidence/_events.py`, add `record_worktree_span(agent_dir: Path, worktree_root: Path) -> bool`. It runs `git rev-parse --absolute-git-dir` in `worktree_root`, calls `worktree_created` (T003) on that folder, and returns `False` without writing when it gets `None`. Otherwise it appends `worktree-span` with `created` and `removed` as `%Y-%m-%dT%H:%M:%SZ` strings, `removed` taken from the same clock read as `ts`, and returns `True`. Export it from `wfctl/evidence/__init__.py` in `TYPE_CHECKING`, `_LAZY`, and `__all__`. Verify with T016 and T018.
- [x] T022 [US2] In `wfctl/cli.py` `worktree_remove_cmd`, set `repo_root = None` and `branch = None` before the outer `try` (PR-008). Add a small local helper that, given both are set, calls `record_worktree_span(resolve_agent_dir(repo_root, branch), repo_root)` inside its own `try` and prints the one `⚠` line from T019 on any exception. Call it after `_save_unsaved` on the success path, and at the end of the catch-all `except (Exception, SystemExit)` after its warning. The helper does nothing when either value is `None`. The refusal path (`raise typer.Exit(1)`) never calls it. Import `record_worktree_span` through `wfctl.evidence`, inside the `try` like the hook's other imports. Verify with T016 to T020.
- [x] T023 [US2] Validate User Story 2 with `uv run pytest -q tests/test_worktree_remove.py tests/test_archive_unsaved.py`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and `uv run python .github/scripts/check_imports.py` — merge gate.

---

## Phase 5: User Story 3 - `wfctl timings` summarizes both across the project (Priority: P1)

**Goal**: `wfctl timings` reads every branch's event log and git's worktree folder, and prints the spread of feature time and of each verify command's duration and peak memory for the last 30 days by default. It stores nothing.

**Independent Test**: build a fixture state folder holding several branches' event logs, run `wfctl timings` against it, and check each line against values worked out by hand.

**Verification**:

- Automated: `uv run pytest -q tests/test_timings.py`
- Manual: `quickstart.md` steps 2 and 4
- Evidence: output matching `contracts/wfctl-timings.md`, including each case in its table

### Tests for User Story 3

> Write these first and confirm they fail. All of them go in `tests/test_timings.py`, call the compute function with a fixed `now`, and pin `NO_COLOR` wherever they read rendered output.

- [x] T024 [P] [US3] Test the loader: event logs at nested paths (`release/v0.30.0/events.jsonl`) are found and named by their path relative to the project state folder, `.issues` is skipped, a non-JSON line is skipped, and with `WFCTL_STATE_DIR` set the single log is read and the heading says so (research R3). Running from the main checkout and from a linked worktree of the same repository finds the same logs (FR-011).
- [x] T025 [P] [US3] Test the spans line: count, branch count, median, and maximum over spans whose `removed` is in the window, including a span created 45 days ago and removed 5 days ago, which counts (acceptance 11). A reversed span and a span whose times won't parse are left out of the figures.
- [x] T026 [P] [US3] Test the open-worktree drop and dedupe (research R9, PR-010). A span whose `created` equals an open worktree's creation time is dropped, whatever folder it sits in. Two spans with the same branch and `created` count once, with the later `removed`. Use a real `git worktree add` in `tmp_path` so the open worktree's time comes from `worktree_created`.
- [x] T027 [P] [US3] Test the open-now line and the branch read (research R5 and R8): the line prints the count of open worktrees and the oldest one's age (FR-013), a worktree whose `gitdir` target is gone isn't open, a relative `gitdir` resolves against the admin folder, and a worktree detached mid-rebase takes its branch from `rebase-merge/head-name` or `rebase-apply/head-name`. With no open worktree the line reads `open now  none`.
- [x] T028 [P] [US3] Test the no-span line: it counts branches with an event in the window, no valid span in the window, and no open worktree, and leaves out the trunk. A branch with one valid span and one malformed span has a span and isn't counted (PR-011, FR-014). With no such branch the line is left out.
- [x] T029 [P] [US3] Test the verify table: "N of M runs carry timings", where events without `seconds` count toward M only; failed and inconclusive runs count; one row per distinct `command` text, ordered by first appearance; a command whose every peak is null prints `—`; the whole-run row; and the three contract cases with no runs or no timings.
- [x] T030 [P] [US3] Test the malformed shapes (PR-011). Each of these is handled without raising:
  1. A `verify` event whose `seconds` isn't a number counts toward M only.
  2. A `verify` event with a numeric `seconds` and a `commands` value that isn't a list counts toward N and the whole-run row, and adds no command rows.
  3. A command entry whose `command` isn't a string is dropped whole.
  4. A command entry whose `seconds` isn't a number is left out of that command's duration figures only, and one whose `peak_bytes` isn't a number is left out of its memory figures only. The entry still counts in that command's run count.
  5. An event whose `ts` won't parse is skipped, since it can't be placed in the window.
- [x] T031 [P] [US3] Test the window and the command: the default 30 days, `--since 90d`, `--since all` with its heading, `--since 3w` refused with exit 1 and the contract's message, an empty project printing the nothing-to-summarize line with exit 0, no figure naming a branch (FR-019), and the state folder's files unchanged after a run (FR-018).
- [x] T032 [P] [US3] Test the formatting rules in `data-model.md`: durations in days and hours, hours and minutes, minutes and zero-padded seconds, and seconds; memory in 1024-based MB and GB.
- [x] T033 [P] [US3] Test SC-004: 200 branch logs built in `tmp_path` compute in under 2 seconds.

### Implementation for User Story 3

- [x] T034 [US3] Create `wfctl/evidence/_timings.py` with the loader: walk `project_state_dir(repo_root)` with `rglob("events.jsonl")`, skip anything under `.issues`, name each branch by its relative parent path, and parse lines the way `read_events` does. Handle `WFCTL_STATE_DIR` as one log. Verify with T024.
- [x] T035 [US3] In `wfctl/evidence/_timings.py`, add the open-worktree reader: list `<git common dir>/worktrees/*/` from one `git rev-parse --git-common-dir` call, keep entries whose `gitdir` target exists (resolving a relative path against the admin folder), and return each one's creation time from `worktree_created` and its branch from `HEAD` or the rebase `head-name` files, or `None`. Verify with T027.
- [x] T036 [US3] In `wfctl/evidence/_timings.py`, add the compute function. It takes the loaded events, the open worktrees, the trunk name, the window, and `now`, and returns a plain summary value. It reads every field by type as T030 lists, drops a span matching an open worktree's creation time without matching the branch, then keeps the latest `removed` per branch and `created`. It counts the no-span line over branches with no valid span. Verify with T025, T026, T028, T029, and T030.
- [x] T037 [US3] In `wfctl/evidence/_timings.py`, add the renderer, which turns the summary into the lines in `contracts/wfctl-timings.md`, with the column labeled `largest process, median / max` (FR-020). Verify with T029, T031, and T032.
- [x] T038 [US3] Export the timings entry point from `wfctl/evidence/__init__.py`, and add `@app.command("timings")` with `--since` to `wfctl/cli.py`. The command parses the window, refuses a bad value with the contract's `✗` line and exit 1, gathers the inputs, and prints each rendered line with `markup=False`. Verify with T031 and T033.
- [x] T039 [US3] Validate User Story 3 with `uv run pytest -q tests/test_timings.py`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and `uv run python .github/scripts/check_imports.py` — merge gate.

---

## Phase 6: Polish and cross-cutting

- [x] T040 Add `wfctl timings` to the command reference in `docs/reference.md` and to `README.md` if it lists commands, with `writing-style` loaded. Verify by reading the rendered section beside `contracts/wfctl-timings.md`.
- [x] T041 Run `quickstart.md` steps 1 and 2 in this worktree, and hand step 3 to the user, since the worktree guard refuses an agent creating or removing a second worktree. Step 4 runs in pfms after release. Verify by recording each step's result in the session summary.
- [x] T042 Run `uv run wfctl verify` and `uv run wfctl doctor` — merge gate for the feature.

---

## Dependencies and execution order

- **Setup (T001)** has no dependency.
- **Foundational (T002, T003)** blocks US2 and US3, since both read creation time through `worktree_created`. US1 doesn't need it.
- **US1 (T004 to T015)** depends only on Setup. It changes `_verify.py` and `test_verify.py`, which no other story touches.
- **US2 (T016 to T023)** depends on Foundational.
- **US3 (T024 to T039)** depends on Foundational. It reads spans in the shape US2 writes, but its tests build fixture logs, so it can be built before US2 lands.
- **Polish (T040 to T042)** depends on all three stories.

Within each story, tests come first and fail, then the implementation tasks run in order.

## Parallel opportunities

- US1 can run beside Foundational, since it touches different files.
- Within each story, every test task marked [P] can be written at once. They share a test file, so they're parallel in thought rather than in edits.
- Once Foundational is done, US2 and US3 can proceed side by side. They share `wfctl/evidence/__init__.py` and `wfctl/cli.py`, so their edits to those two files are made one after the other.

### Parallel example: User Story 3

```text
Task: "T025 spans line tests in tests/test_timings.py"
Task: "T027 open-now and branch read tests in tests/test_timings.py"
Task: "T032 formatting tests in tests/test_timings.py"
```

## Implementation strategy

1. US1 first. It is the number pfms needs most, it stands alone, and it doesn't depend on either proposed record's boundary beyond its own.
2. Foundational, then US2, so spans start accumulating as soon as the change ships.
3. US3 last, since it reads what the other two write.

Implementation of any story waits until the user accepts or rejects `worktree-span-read-from-git` and `828-verify-measures-each-child`.

## Notes

- The plan's source-tree comments are out of date in two places, and these tasks supersede them (PR-012). `cli.py` calls `record_worktree_span` on two paths, the success path and the catch-all, as T022 says. `tests/test_worktree_remove.py` also covers the catch-all path, the unresolved branch, and the mid-rebase folder, as T017, T018, and T020 say.
- `contracts/wfctl-timings.md` reading rule 4 and `data-model.md` validation 3 say a malformed span's branch counts on the no-span line. T028 and T036 follow FR-014 instead: a branch counts there only when it has no valid span in the window, so one bad span beside a good one doesn't move it (PR-011).
- The plan's Part 3 step 5 says a wrong-typed field is "left out of that command's figures", which reads either way. T030 settles it per figure, as contract reading rule 6 says: a bad `seconds` leaves the duration figures, and a bad `peak_bytes` leaves the memory figures.
- The plan is unchanged, so the third and last plan review round hasn't been used.
- `wfctl timings` matches a span to an open worktree by creation time alone, as the spec's edge case says. A mid-rebase span lands in a folder named for a commit, so matching the branch would miss it.
