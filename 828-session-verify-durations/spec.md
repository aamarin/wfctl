# Feature Specification: wfctl measures feature time and verify cost

> **Scope change, 2026-11-20:** Peak memory moved to #840, and this feature now records durations only. On Linux, a command's `ru_maxrss` never reports less than wfctl's own peak, so the `os.wait4` measurement this document describes gave small commands the parent's size. `wfctl verify` times each command with `subprocess.run`, `wfctl timings` has no memory column, and the design record `828-verify-measures-each-child` was removed from the branch. Every mention of memory, `wait4`, or the largest process below is part of #840 now, not this feature.

**Feature Branch**: `828-session-verify-durations`  
**Created**: 2026-11-19  
**Status**: Draft  
**Input**: User description: "wfctl records how long each session and each verify command takes, and how much memory each command used at its peak, so a project can size the machine its agents run on from measurements instead of guesses." Loaded from `design.md`, which replaces session length with worktree lifetime.

## Clarifications

### Session 2026-11-19

- Q: How far back does `wfctl timings` look? → A: The last 30 days by default, with `--since` to change the window. Basis: the user chose C, since the test suite grows and old runs would pull the medians below what the machine needs today.
- Q: Does `wfctl timings` offer machine-readable output? → A: No, it prints the table only. Basis: the user chose A, since the event logs it reads are already JSON, and a `--json` flag can be added later without changing anything wfctl records.

## User Scenarios & Testing _(mandatory)_

A project that runs its agents on a shared machine has to decide how many worktrees can run at once. pfms runs on one 4-core, 16 GB codespace with a limit of 5 worktrees (MarinVentures/pfms#1200), and raising that limit needs two kinds of numbers nobody has today:

1. How long a feature keeps a worktree open, from the moment the worktree is created to the moment it's removed.
2. How long each `wfctl verify` command takes, and how much memory it uses at its peak.

On #1014, `wfctl verify` spent 14 minutes on lint before the machine stopped it for low memory, and that duration is only known because someone watched it.

### User Story 1 - See how long and how much memory each verify command takes (Priority: P1)

The user runs `wfctl verify` as usual. Each command's output streams to the terminal as it does today. When the run finishes, wfctl records how long the whole run took, and for each command, its exit code, how long it ran, and the peak memory of the largest single process it started.

**Why this priority**: Verify is the heaviest thing an agent runs, and it's what ran out of memory on #1014. Its numbers decide whether a machine can run another worktree.

**Independent Test**: Configure two commands in `wfctl.json`, the first using more memory than the second, run `wfctl verify`, and read the new `verify` event in the branch's event log. Each command has its own duration and peak memory, and the second command's peak is below the first's.

**Acceptance Scenarios**:

1. **Given** a `verify` list with three commands, **When** the user runs `wfctl verify`, **Then** the `verify` event carries the run's total duration and, for each command, its text, exit code, duration in seconds, and peak memory in bytes.
2. **Given** a first command that peaks at 300 MB and a second that peaks at 50 MB, **When** verify runs, **Then** the second command's recorded peak is close to 50 MB and isn't affected by the first.
3. **Given** a command whose executable doesn't exist, **When** verify runs, **Then** that command is recorded as failed with a duration and no peak memory, and the other commands still run.
4. **Given** a command that starts child processes and waits for them, **When** verify runs, **Then** the recorded peak is that of the largest single process among them.
5. **Given** a run whose tree changes partway through, **When** verify finishes, **Then** the event is marked inconclusive as today, and still carries every duration and peak.
6. **Given** any run, **When** it finishes, **Then** `verify.json` and the decision about whether `implement` is done are unchanged from today.

---

### User Story 2 - Record a worktree's lifetime when it's removed (Priority: P1)

The user finishes a feature and removes its worktree. The removal hook saves the specs as it does today. If it lets the removal go ahead, it also records when git created the worktree and when it was removed, in the branch's event log, which outlives the worktree.

**Why this priority**: How long a feature holds a worktree is the other half of sizing a machine. Without this event, the summary in User Story 3 has no feature time to report.

**Independent Test**: Create a worktree, note its creation time, remove it through the removal hook, and read the new `worktree-span` event in the branch's event log. Its creation time matches when git created the worktree, within a second, and its removal time matches when the hook ran.

**Acceptance Scenarios**:

1. **Given** a worktree created on 2026-11-19 at 18:31:46Z, **When** the removal hook lets its removal go ahead on 2026-11-22 at 10:15:03Z, **Then** the branch's event log gains one `worktree-span` event with `created` 2026-11-19T18:31:46Z and `removed` 2026-11-22T10:15:03Z.
2. **Given** a removal the hook refuses, **When** the hook exits, **Then** no `worktree-span` event is written.
3. **Given** a worktree whose git metadata no longer holds its creation record, **When** the hook lets the removal go ahead, **Then** no `worktree-span` event is written and the removal proceeds as today.
4. **Given** a branch whose worktree is removed and later created again, **When** each worktree is removed, **Then** each removal writes its own `worktree-span` event.
5. **Given** any failure while reading the creation time or writing the event, **When** the hook runs, **Then** the removal's outcome is the same as it would have been without this feature.

---

### User Story 3 - Summarize feature time and verify cost across the project (Priority: P1)

The user, or someone sizing the machine, runs `wfctl timings` from any checkout of the project. It reads every branch's event log and prints the spread of feature time and of each verify command's duration and peak memory over the last 30 days. `--since 90d` changes the window, and `--since all` uses every event. It stores nothing, and recomputes every number each time it runs.

```
wfctl timings — last 30 days, 41 branches

Feature time, worktree created to removed
  spans     23 across 21 branches · median 1d 4h · max 6d 2h
  open now  5 worktrees · oldest 3d 1h
  no span   14 branches: removed before this shipped, or removed by hand

Verify, 18 of 52 runs carry timings
  command                          runs  median  max     largest process, median / max
  uv run pytest -q                   18  2m 01s  3m 40s  870 MB / 1.4 GB
  uv run ruff check wfctl/ tests/    18      2s      4s   46 MB / 51 MB
  uv run mypy                        18     11s     29s  384 MB / 610 MB
  whole run                          18  2m 14s  4m 05s
```

**Why this priority**: The recorded events are only useful once someone can read them across branches. This summary is the number pfms takes into its sizing decision.

**Independent Test**: Build a fixture state folder holding several branches' event logs, with `worktree-span` events, `verify` events with and without timings, and a branch with no span. Run `wfctl timings` against it and check each line against the values worked out by hand.

**Acceptance Scenarios**:

1. **Given** branches with `worktree-span` events, **When** the user runs `wfctl timings`, **Then** the spans line prints the count of spans, the count of branches they came from, and the median and maximum span.
2. **Given** worktrees that exist right now, **When** the user runs `wfctl timings`, **Then** the open-now line prints how many there are and how long the oldest has been open.
3. **Given** branches with an event log and no `worktree-span` event, that aren't a trunk branch and have no open worktree, **When** the user runs `wfctl timings`, **Then** the no-span line counts them and names both possible causes.
4. **Given** `verify` events with timings, **When** the user runs `wfctl timings`, **Then** each command gets one row with its run count, median and maximum duration, and median and maximum peak memory, and a final row gives the whole run's median and maximum duration.
5. **Given** `verify` events written before this change, **When** the user runs `wfctl timings`, **Then** the verify heading counts them in "N of M runs carry timings" and the table leaves them out of every median and maximum.
6. **Given** failed and inconclusive verify runs with timings, **When** the user runs `wfctl timings`, **Then** their durations and peaks count in the table.
7. **Given** a project with no event logs, **When** the user runs `wfctl timings`, **Then** it says there is nothing to summarize and exits 0.
8. **Given** an event log line that isn't valid JSON, **When** the user runs `wfctl timings`, **Then** that line is skipped and the rest of the summary prints.
9. **Given** a verify run from 40 days ago and one from 10 days ago, **When** the user runs `wfctl timings`, **Then** only the run from 10 days ago counts, and the heading says the window is the last 30 days.
10. **Given** the same two runs, **When** the user runs `wfctl timings --since all`, **Then** both count, and the heading says every event was used.
11. **Given** a span whose worktree was created 45 days ago and removed 5 days ago, **When** the user runs `wfctl timings`, **Then** the span counts, since spans fall in the window by their removal time.

---

### Edge Cases

- A verify command that's interrupted with Ctrl-C leaves no child process running after wfctl exits, and writes no event, as today.
- A branch whose worktree was created on one machine and removed on another still gets one span, since both times come from the removal hook.
- A worktree removed by hand with `git worktree remove` or `rm -rf` writes no span, and its branch is counted under "no span".
- A verify command name can change between runs, such as after editing `wfctl.json`. Each distinct command text gets its own row.
- A worktree whose git metadata was rewritten after creation would record a later creation time. The plan checks which git commands do this.
- A `--since` value that isn't a whole number of days or `all`, such as `--since 3w`, is refused with a message naming the accepted forms, and nothing is printed.
- A `worktree-span` event whose removal time is before its creation time, such as after a clock change, is left out of the medians and counted on the no-span line.
- The removal hook runs before workmux removes the worktree, so a removal that fails afterward leaves a span for a worktree that still exists. `wfctl timings` leaves out a span whose creation time matches a worktree that's open now, comparing both times to the whole second. That match ignores the branch, since a worktree stopped mid-rebase records its span under a commit rather than its branch name. Among several spans with the same branch and creation time, `wfctl timings` keeps only the one with the latest removal time.
- If the removal hook fails partway with an unexpected error, it still lets the removal go ahead, so it still writes the span when it can read the creation time.
- If the removal hook can't work out which branch the worktree is on, it has no state folder to write to, so it writes no span. If the branch has an event log from other commands, it's counted on the no-span line, even though neither of the line's two causes applies.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: `wfctl verify` MUST record each command's duration in seconds and its peak memory in bytes in the `verify` event, along with the run's total duration.
- **FR-002**: The peak memory MUST be that of the largest single process the command started and waited for, measured for that command alone and unaffected by any other command or process wfctl ran.
- **FR-003**: `wfctl verify` MUST keep streaming each command's output to the terminal as it runs.
- **FR-004**: A command that can't be executed MUST be recorded as failed, with a duration and no peak memory.
- **FR-005**: The `verify` event MUST keep every field it carries today, and `verify.json` MUST NOT change.
- **FR-006**: An interrupted verify MUST stop the running command and leave no child process behind.
- **FR-007**: The worktree removal hook MUST write one `worktree-span` event, holding the worktree's creation and removal times, when it lets a removal go ahead.
- **FR-008**: The creation time MUST come from the time git created the worktree, read at removal, and not from any event wfctl wrote.
- **FR-009**: The removal hook MUST NOT write a `worktree-span` event when it refuses the removal, can't read the creation time, or can't work out the worktree's branch.
- **FR-010**: A failure to read the creation time or write the `worktree-span` event MUST NOT change whether the removal goes ahead or what the hook prints about it.
- **FR-011**: `wfctl timings` MUST read every branch's event log under the project's state folder, from any checkout of the project.
- **FR-012**: `wfctl timings` MUST print the span count, the number of branches they came from, and the median and maximum span.
- **FR-013**: `wfctl timings` MUST print how many worktrees are open right now and how long the oldest has been open.
- **FR-014**: `wfctl timings` MUST count, as one number, the branches with an event log, no span, and no open worktree, leaving out trunk branches, and name both possible causes.
- **FR-015**: `wfctl timings` MUST print one row per verify command with its run count and the median and maximum of its duration and peak memory, and a row for the whole run's duration.
- **FR-016**: `wfctl timings` MUST count verify events without timings in "N of M runs carry timings" and leave them out of every median and maximum.
- **FR-017**: `wfctl timings` MUST count failed and inconclusive runs in the verify figures.
- **FR-021**: `wfctl timings` MUST count only events from the last 30 days by default. `--since <N>d` MUST change the window to N days, and `--since all` MUST use every event. A verify run falls in the window by its timestamp, a span by its removal time, and the no-span line counts only branches with an event in the window. The open-now line always describes the worktrees open right now. The heading MUST name the window used.
- **FR-022**: `wfctl timings` MUST print the summary as a table only, with no `--json` flag. If you need the raw figures, read the event logs, which are already JSON.
- **FR-018**: `wfctl timings` MUST store nothing and recompute every figure each time it runs.
- **FR-019**: `wfctl timings` MUST NOT print per-branch figures. The summary is for sizing a machine, and a per-branch list is #830's.
- **FR-020**: The peak memory column MUST be labeled "largest process", so nobody reads it as the total across a command's parallel workers.

## Key Entities _(include if feature involves data)_

- **Verify event**: The line `wfctl verify` appends to a branch's event log after each run. It gains the run's total duration and one entry per command with its text, exit code, duration, and peak memory.
- **Worktree span event**: A new line the removal hook appends to a branch's event log, holding when git created the worktree and when it was removed. A branch can have several, one per worktree.
- **Timings summary**: What `wfctl timings` prints. It's computed from the event logs on every run and isn't saved anywhere.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: After one `wfctl verify` run in a pfms worktree, the recorded total duration is within 5 seconds of the wall-clock time the run took.
- **SC-002**: A command that allocates a known amount of memory records a peak within 20% of that amount, on both macOS and Linux.
- **SC-003**: A worktree's recorded creation time is within 5 seconds of when `workmux add` created it.
- **SC-004**: `wfctl timings` over a project with 200 branches prints in under 2 seconds.
- **SC-005**: Someone sizing the pfms codespace can read the median and maximum feature time and each verify command's median and maximum peak memory from one command, without opening an event log.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy`, all green.
- Tests for the new `verify` event fields, including two commands with different peaks, a missing executable, and an interrupted run that leaves no child process.
- A test on Linux in CI that checks a known allocation is recorded in bytes, to catch the unit difference between macOS and Linux.
- Tests for the removal hook: a span written on the success path, nothing written on a refusal or a missing creation record, and an unchanged removal outcome when the read or the write fails.
- Tests for `wfctl timings` over a fixture state folder, covering spans, open worktrees, the no-span count with a trunk branch left out, verify events with and without timings, failed and inconclusive runs, a malformed line, and events inside and outside the 30-day window.
- Manual: run `wfctl verify` in a pfms worktree, then `wfctl timings`, and check that the verify duration matches the wall-clock time.

## Assumptions

- Pre-specify design context loaded from `specs/828-session-verify-durations/design.md`.
- Session length is out of scope. The issue first asked for it, and `design.md` replaces it with worktree lifetime, since restarts leave the `start` and `end` events unpaired.
- The creation time comes from git's worktree metadata, as `worktree-span-read-from-git` decides, and the record is still proposed.
- Each command's duration and peak come from that command's own process, as `828-verify-measures-each-child` decides.
- wfctl runs on macOS and Linux only, as it already does through its use of POSIX file locks.
- Worktrees removed before this ships have no span, and are counted on the no-span line.
- "Across the project" means the event logs in this machine's state folder. A branch worked on another machine shows up only on the machine that holds its log.
- Verify runs on a trunk branch count in the verify table. Only the no-span line leaves trunk branches out, since a trunk branch has no worktree to remove.
