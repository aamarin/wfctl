# wfctl measures feature time and verify cost

Contexts: session-continuity, evidence-and-derivation

## Problem Statement

A project sizes the machine its agents run on from measurements: how long a feature keeps a worktree open, and how long and how much memory each `wfctl verify` command takes. pfms needs those numbers to raise its limit of 5 worktrees on one 4-core, 16 GB codespace (MarinVentures/pfms#1200).

## Recommended Direction

wfctl records two new things and adds one command that summarizes them:

1. `wfctl verify` adds each command's duration and peak memory, and the run's total duration, to the `verify` event it already writes.
2. The worktree removal hook writes a `worktree-span` event holding the worktree's creation time, read from git, and its removal time.
3. `wfctl timings` reads every branch's event log in the project and prints medians and maximums. It stores nothing.

We dropped session length, which the issue first asked for. The user runs several sessions per context window, and an automatic restart writes `end` with no `start` after it, so pairing the two events gives lengths that match no real period of work. The worktree's lifetime is what a feature costs the machine, and `worktree-span-read-from-git` explains why git is where its start time comes from.

### How it works, on this branch

Each branch already has an event log at `<state dir>/events.jsonl`, where the state dir is what `wfctl state-dir` prints, such as `~/.local/state/wfctl/wfctl/828-session-verify-durations/`. Nothing new is written to the repository or the spec folder.

1. Git creates the worktree. `workmux add` runs `git worktree add`, which writes `.git/worktrees/828-session-verify-durations/commondir` once. Its modified time, 2026-11-19 18:31:46Z, is the creation time. wfctl writes nothing at this point.
2. The agent runs `wfctl verify`. Each command's output streams to the terminal as before. When the run finishes, wfctl appends one line to the event log:

   ```json
   {"ts": "2026-11-20T15:04:12Z", "event": "verify", "exit": 0, "sha": "8ac5dcb",
    "failed": [], "inconclusive": false, "seconds": 131.4,
    "commands": [
      {"command": "uv run pytest -q", "exit": 0, "seconds": 118.2, "peak_bytes": 912261120},
      {"command": "uv run ruff check wfctl/ tests/", "exit": 0, "seconds": 1.9, "peak_bytes": 48234496},
      {"command": "uv run mypy", "exit": 0, "seconds": 11.3, "peak_bytes": 402653184}
    ]}
   ```

   The first five fields are the ones the event carries today. `seconds` and `commands` are new. `verify.json`, which decides whether `implement` is done, doesn't change.
3. The PR merges and the user removes the worktree. `workmux remove` runs `wfctl hook worktree-remove`, which saves the specs as it does today. If the hook lets the removal go ahead, it reads the `commondir` file's modified time and appends:

   ```json
   {"ts": "2026-11-22T10:15:03Z", "event": "worktree-span",
    "created": "2026-11-19T18:31:46Z", "removed": "2026-11-22T10:15:03Z"}
   ```

   If the hook refuses the removal, or the `commondir` file is missing, it writes nothing. The event log outlives the worktree, since it's in the state dir.
4. Anyone runs `wfctl timings` from any checkout of the project. It reads every branch's event log under the project's state dir, and the live worktrees for the "open now" line:

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

   By default, the summary covers the last 30 days. `--since 90d` changes the window, and `--since all` uses every event. The numbers are recomputed on every run, so a branch removed a minute ago is already counted.

## Boundaries and Ownership

- Git records when a worktree was created. In a consumer repo, no wfctl command that writes an event runs at creation, so wfctl can't record it itself (`worktree-span-read-from-git`).
- The removal hook records when the worktree was removed, and only after it lets the removal go ahead. No other wfctl code runs at removal, and a span written elsewhere could record a removal the hook stopped.
- `wfctl verify` measures each command from that command's own process. wfctl can't get a correct per-command peak from the counter it shares with every other process it starts (`828-verify-measures-each-child`).
- `wfctl timings` owns no stored value. It recomputes every median and maximum from the event logs each time it runs (`session-state-is-re-derived`).

## Software design decisions

- docs/architecture/design/828-verify-measures-each-child.md — verify reads each command's duration and peak memory from that command's own process with `os.wait4`

## Key Assumptions to Validate

- [ ] No git command run during a worktree's life rewrites `commondir`. The plan tests `git worktree repair`, `git worktree move`, `git worktree lock`, and `git gc` against the file's modified time.
- [ ] A test runner's workers are waited for by their parent before the command exits, so their peaks reach `wait4`. A pfms `wfctl verify` run whose largest process reads close to its known pytest worker size confirms it.
- [ ] A codespace stop and start keeps `~/.local/state`. A rebuild probably doesn't, which would lose the event logs. pfms checks this on its side.

## MVP Scope

In scope:

1. The new `verify` event fields.
2. The `worktree-span` event, written by the removal hook on its success path.
3. `wfctl timings` with the three feature-time lines and the per-command verify table. A branch whose worktree was created more than once contributes one span for each, and the summary prints medians and maximums only, with no per-branch figures.

The `verify` events written before this change still read. The summary counts them in "N of M runs carry timings" instead of dropping them. Failed and inconclusive runs count too, since their durations are real. Trunk branches such as `main` are left out of the "no span" count, because they never get a worktree removed.

## Not Doing (and Why)

- Per-branch figures, such as a list of branches with their times, a total for each branch, or the branch behind a maximum. The summary is for sizing a machine, which needs the spread across all worktrees and not any one branch. A per-branch list would mainly serve estimating stories, and a worktree's lifetime is a poor measure of effort, since it includes nights, weekends, and time waiting on review. #830 covers that list, with a `--since` filter and the issue's `Estimate` field beside each branch.
- Session length. Restarts and repeated `/start-session` runs leave the `start` and `end` events unpaired, so the numbers would be wrong.
- Time in each GitHub Projects board column. GitHub records every column move, but the board is moved partly by hand and partly by automation, and steps get skipped. It shows how an issue moved through the board, not how long a machine was busy, so it gets its own issue.
- Splitting feature time by attended and unattended runs, using the `mode` events. It's useful, but it needs feature time to exist first, so it gets its own issue.
- The 12-hour codespace cap. A worktree span includes nights when nothing ran, so it says nothing about how close a single run comes to the cap.
- Total memory across a test runner's parallel workers. `wait4` reports the largest single process, so the column says "largest process". Measuring a whole machine's memory is pfms's job inside its codespace.
- A `wfctl hook worktree-create` step. Every consumer repo would have to change its workmux configuration, and worktrees open today would have no start time.

## Open Questions

- Where `wfctl timings` lives in the code. It reads event logs, which puts it in the evidence and derivation context beside `wfctl/evidence/_events.py`, and the plan confirms the module.
- Whether `workmux` goes on the `Contexts` line. The level-2 record governs it, but this change edits no workmux code or configuration, so it's left off for now.
