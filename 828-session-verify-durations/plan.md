# Implementation Plan: wfctl measures feature time and verify cost

**Branch**: `828-session-verify-durations` | **Date**: 2026-11-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `spec.md` in this folder

## Summary

wfctl records how long each verify command takes and how much memory it uses at its peak, records how long each worktree stays open, and adds `wfctl timings` to summarize both across the project. pfms needs these numbers to decide how many worktrees one 16 GB codespace can run.

The change has three parts:

1. `wfctl verify` runs each command with `subprocess.Popen` and `os.wait4`, and adds each command's duration and peak memory, and the run's total duration, to the `verify` event (`828-verify-measures-each-child`).
2. The removal hook reads the worktree's creation time from git's `commondir` file and writes a `worktree-span` event on its success path (`worktree-span-read-from-git`).
3. `wfctl timings` reads every branch's event log and git's worktree folder, and prints medians and maximums for the last 30 days by default. It stores nothing.

A probe confirmed that no git command a worktree normally sees rewrites `commondir` (research R1), and reading all 260 of this repository's event logs takes 0.11 seconds (R4).

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)  
**Primary Dependencies**: `typer` and `rich`, as today. `os.wait4`, `resource`, and `statistics` come from the standard library. No new dependency.  
**Storage**: The branch's existing `events.jsonl` in the state folder. No new file.  
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, plus the manual steps in `quickstart.md`  
**Target Platform**: macOS and Linux. `os.wait4` is POSIX only, as `fcntl` already is.  
**Project Type**: CLI  
**Performance Goals**: `wfctl timings` prints in under 2 seconds over 200 branches (SC-004). The measured read is 0.11 seconds over 260.  
**Constraints**: Verify output keeps streaming. The removal hook's outcome never depends on the span. `verify.json` doesn't change. Minimal-complexity bias.  
**Scale/Scope**: One project's state folder, about 300 branches today. Four source files changed (`_verify.py`, `cli.py`, `evidence/__init__.py`, `evidence/_events.py`) and one added (`evidence/_timings.py`).

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repository has no `.specify/memory/constitution.md`. The gates come from its accepted architecture records and `AGENTS.md`, as Complexity Tracking records.

- [x] Validation plan exists: the three commands above, plus the tests listed under Validation below, and `quickstart.md` for the manual checks.
- [x] Complexity is justified: no new abstraction, class, or dependency. One new module for the summary, since `_events.py` holds readers and writers of single events, and the summary is a different job.
- [x] Ownership is stated: see Ownership below.
- [x] `session-state-is-re-derived`: `wfctl timings` recomputes every figure from the logs on each run and keeps no cache (FR-018).
- [x] `wfctl-runs-the-verification`: the verdict and `verify.json` are unchanged. The new fields are measurements beside the verdict, never an input to it (FR-005).
- [x] `contexts-are-packages`: the new code is in `wfctl/evidence/`, and `cli.py` reaches it through the package. Evidence imports only `core` (`_io`, `_paths`), so no baseline line or map arrow is added (research R7).
- [x] `change-carries-release-note`: `changes/828.addition.md`.
- [x] `knowledge-placement`: the two records hold the boundary decisions. Code comments hold facts about one file, such as why `commondir` and not `gitdir`.

**Post-design re-check**: still passing. Phase 1 added no stored value and no import across contexts.

### Ownership

| Value | Computed by | Why not the other side |
| --- | --- | --- |
| Worktree creation time | git, read by the removal hook | No wfctl command that writes an event runs at creation in a consumer repo |
| Worktree removal time, and whether the removal went ahead | the removal hook | No other wfctl code runs at removal, and only the hook knows whether it refused |
| Each command's duration and peak | `run_verification`, from that command's `os.wait4` | The shared `RUSAGE_CHILDREN` counter only goes up, so it reports the wrong peak after the largest command |
| Every median, maximum, and count | `wfctl timings`, at read time | A stored figure would go stale as soon as another run lands |

## Project Structure

### Documentation (this feature)

```text
<spec folder>/828-session-verify-durations/
├── design.md
├── spec.md
├── plan.md              # this file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── wfctl-timings.md
│   └── events.md
├── scans/
│   └── clarify.md
└── tasks.md             # /speckit.tasks writes it
```

### Source Code (repository root)

```text
wfctl/
├── _verify.py               # run_verification measures each command; perform adds the fields
├── cli.py                   # worktree_remove_cmd writes the span; new `timings` command
└── evidence/
    ├── __init__.py          # re-exports record_worktree_span and the timings entry point
    ├── _events.py           # record_worktree_span
    └── _timings.py          # new: read logs, compute the summary, render it

tests/
├── test_verify.py           # extended: per-command fields, missing executable, interrupt, Linux bytes
├── test_worktree_remove.py  # extended: span on success, none on refusal or missing commondir, failure isolation
└── test_timings.py          # new: fixture state folder, every contract case

changes/
└── 828.addition.md
```

**Structure Decision**: The existing single-package layout. The measurement change stays in `_verify.py`, which the import baseline already places in evidence, rather than moving it under #768 in the same change.

## Design by part

### Part 1: verify measures each command

1. `run_verification` returns a list of `CommandResult(argv, exit, seconds, peak_bytes)`, a `NamedTuple`, one per command. It starts each command with `subprocess.Popen(argv, cwd=repo_root)`, reads `time.monotonic()` around `os.wait4(proc.pid, 0)`, and sets `proc.returncode` from the status.
2. A missing executable gives exit 127 and a non-executable one gives 126, with the duration measured and `peak_bytes` set to `None` (research R2).
3. `_peak_bytes(ru_maxrss)` multiplies by 1024 unless `sys.platform == "darwin"`.
4. The `try` starts on the line after `Popen` returns. On `KeyboardInterrupt` during the wait, it gives the child 0.25 seconds to exit on its own, polling `os.wait4(pid, os.WNOHANG)`, then kills it, reaps it, and re-raises. No event is written and no child is left running (FR-006). The 0.25-second grace matches what `subprocess.run` does today. The terminal sends Ctrl-C to the child too, so most children exit within the grace and get to clean up, such as pytest printing its interrupted summary.
5. `perform` builds `failed` and the exit code from the results, reads `time.monotonic()` around the whole run, and passes `seconds` and `commands` to `append_event`. `write_record` and `verify.json` are untouched.

### Part 2: the removal hook writes a span

1. `record_worktree_span(agent_dir, worktree_root)` in `evidence/_events.py` runs `git rev-parse --absolute-git-dir` in the worktree, reads `<git dir>/commondir`'s modified time, and appends the event. It returns without writing when the file doesn't exist, which covers the main checkout.
2. `worktree_remove_cmd` calls it on both paths that let the removal go ahead (FR-007):
   1. After `_save_unsaved`, the last step of the success path.
   2. In the catch-all `except (Exception, SystemExit)`, after its warning, since that path also exits 0 and workmux then removes the worktree. If the failure came before `repo_root` and `branch` were resolved, there's no worktree to read, and the hook writes nothing.

   Each call sits inside its own `try`. A failure prints one `⚠` line naming the span and changes nothing else the hook prints or decides (FR-010). The refusal path, `raise typer.Exit(1)`, never calls it (FR-009).
3. The state folder is `resolve_agent_dir(repo_root, branch)`, the same one the branch's other events use.

### Part 3: `wfctl timings`

1. `_timings.py` holds three functions: one that loads every branch's events from the project state folder (research R3), one that computes the summary from those events, the open worktrees, and the trunk name, and one that renders it. The compute function takes `now` as an argument so the tests fix the clock.
2. The open-now line reads `<git common dir>/worktrees/*/` directly (research R5). Each open worktree yields its creation time and, where it can be read, its branch, from the admin folder's own files (research R8).
3. The no-span line leaves out `trunk_branch(repo_root)` and the branches of open worktrees (research R6).
4. Before computing the span figures, the summary drops a span whose `created` equals an open worktree's creation time, and keeps only the latest `removed` among spans with the same branch and `created` (research R9).
5. Every field is read by type. A `verify` event whose `seconds` isn't a number counts as a run without timings. A command entry whose `seconds` or `peak_bytes` has the wrong type is left out of that command's figures. A span whose `created` or `removed` won't parse is left out and its branch counts on the no-span line. No event line can make `wfctl timings` raise.
6. `cli.py` adds `@app.command("timings")` with `--since`, parses the window, and prints the rendered lines with `markup=False`.

## Validation

- `tests/test_verify.py`:
  1. Two commands with different peaks, where the second's peak is below the first's.
  2. A missing executable recorded with exit 127 and a null peak.
  3. An interrupt that leaves no child process. The test starts a real `sleep 30` child and patches `os.wait4` to raise `KeyboardInterrupt` on its first blocking call and pass through after that. It then checks that `os.kill(pid, 0)` raises `ProcessLookupError` and that no `verify` event was written. This replaces `test_interruption_writes_nothing_and_preserves_the_previous_record`'s patch of `subprocess.run`, which the `Popen` change bypasses.
  4. A real 200 MB allocation recorded within 20% in bytes, on whichever platform runs the suite: Linux in CI, macOS on the maintainer's machine.
  5. `_peak_bytes` with `sys.platform` patched to `darwin` and to `linux`, so both conversions are tested on every run, even though CI runs only Linux (SC-002).
  6. The existing tests updated for the new return type.
- `tests/test_worktree_remove.py`: one span on the success path, with `created` matching `commondir`'s modified time. One span on the catch-all path. None on a refusal. None in the main checkout. An unchanged removal outcome when the read or the write raises.
- `tests/test_timings.py`: a fixture state folder with nested branch names, spans, open worktrees made with a real `git worktree add` in `tmp_path`, verify events with and without timings, failed and inconclusive runs, a malformed line, wrong-typed fields, a reversed span, a span matching an open worktree, two spans with the same `created`, a detached worktree mid-rebase, events inside and outside the 30-day window, `--since all`, a refused `--since 3w`, and an empty project. `NO_COLOR` is pinned.
- SC-004: a test builds 200 branch logs and asserts the summary computes in under 2 seconds.
- Manual: `quickstart.md`.

## Risks

1. A git release that rewrites `commondir` on `repair --relative-paths` would move a span's start forward. Git 2.44 lacks the option, so the probe couldn't check it (research R1). The effect is a shorter span on the worktrees that ran it, not a failure. The same option can write `gitdir` as a relative path, which research R5 resolves against the admin folder.
2. A test runner whose workers outlive their parent would read a lower peak. The "largest process" label and the pfms check in `quickstart.md` step 4 cover it.
3. Both records are still proposed. Implementation starts after the user accepts or rejects them.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from the architecture records and `AGENTS.md` | The repository has no `.specify/memory/constitution.md` | A gate with no source is decorative, and one borrowed from another project is false |
