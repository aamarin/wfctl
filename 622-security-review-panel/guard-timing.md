# Worktree guard timing for SC-003

SC-003 says a command that matches none of the review check's patterns costs
under 1 ms more than it did before the check existed. This file holds the
baseline, measured before #637 changed any code, so #638's T040 can repeat the
same command once the check is wired into `_hook.py` and record the second
number beside it.

## The command

Run it from the worktree's root, so `os.getcwd()` is the worktree:

```bash
uv run python -c 'import json, os, timeit; from wfctl._hook import worktree_guard; p = json.dumps({"tool_input": {"command": "ls"}, "cwd": os.getcwd()}).encode(); t = timeit.repeat(lambda: worktree_guard(p), number=1000, repeat=5); print(f"{min(t) / 1000 * 1e6:.3f} us per call")'
```

It calls `worktree_guard` in process 1000 times, five times over, and prints the
fastest of the five divided by 1000. The payload is built with `json.dumps`
rather than written out, because the guard reads an escaped quote in the command
text as part of a path and refuses the command.

## Baseline

- Commit: `9208bc2` on `637-review-records`, before any #637 code change.
- Machine: Andre's Mac, Darwin 25.5.0, Python from `uv run`.
- Result: 1.136 µs per call, and 1.120 µs on the next run, which agree within 2%.

A first run printed 1.258 µs. It is left out because it was the first call into
a cold interpreter, and the two runs after it agreed with each other.

## After (#638, T040)

Not measured yet.
