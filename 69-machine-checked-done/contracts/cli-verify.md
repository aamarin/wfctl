# Contract: `wfctl verify`

The command surface. This is what a user, a skill, and a CI step all call.

## Synopsis

```
wfctl verify
```

No flags. Every behavior it could gate is either always wanted or belongs to a
different command.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Every configured command exited 0, or nothing is configured |
| 1 | At least one configured command exited non-zero, or the run was inconclusive |
| 1 | The config file exists and is malformed |

Exit 0 on "nothing configured" (FR-019) so an unconditional caller — a worktree
setup hook, a CI step shared across repositories — does not break on a project
that has not adopted the feature.

## Output

**Nothing configured:**

```
$ wfctl verify
ℹ No definition of done configured — nothing to verify.
  Add a `verify` list to wfctl.json.
$ echo $?
0
```

**A passing run.** Each command's own output streams through untouched; wfctl
adds only the arrow before and the verdict after.

```
$ wfctl verify
→ uv run pytest -q
....................................................... [100%]
521 passed in 27.19s
→ uv run ruff check wfctl/ tests/
All checks passed!
→ uv run mypy wfctl/
Success: no issues found in 11 source files
✓ verified — 3 of 3 passed at a1b2c3d
$ echo $?
0
```

**A failing run.** Every command runs even after one fails (FR-013), so one run
reports every problem.

```
$ wfctl verify
→ uv run pytest -q
521 passed in 27.19s
→ uv run ruff check wfctl/ tests/
wfctl/_verify.py:42:1: F401 'hashlib' imported but unused
→ uv run mypy wfctl/
Success: no issues found in 11 source files
✗ failed — 1 of 3 at a1b2c3d
    uv run ruff check wfctl/ tests/
$ echo $?
1
```

**A dirty tree.** The run proceeds and is recorded, but cannot reach `●` — said at
the point of running rather than discovered later at status.

```
$ wfctl verify
…
✓ verified — 3 of 3 passed at a1b2c3d
⚠ working tree has uncommitted changes — commit to reach ● implement
```

**An inconclusive run.** The tree moved between the two captures.

```
$ wfctl verify
…
✗ inconclusive — the tree changed while verifying; re-run
$ echo $?
1
```

**A command that cannot be executed** (FR-023). Not a configuration problem — a
failed command, named, with the rest of the list still run.

```
$ wfctl verify
→ uv run pytest -q
521 passed in 27.19s
→ uv run mypyy wfctl/
✗ mypyy: no such executable
→ uv run ruff check wfctl/ tests/
All checks passed!
✗ failed — 1 of 3 at a1b2c3d
    uv run mypyy wfctl/
$ echo $?
1
```

**A malformed config:**

```
$ wfctl verify
✗ wfctl.json: 'verify' entry 2 must be a non-empty list of strings, got a string
— write it as argv, e.g. ["pytest", "-q"]
$ echo $?
1
```

**Interrupted:** nothing is printed by wfctl and nothing is written. Any existing
record is left byte-identical (FR-017).

## Side effects

| Effect | When |
| --- | --- |
| `verify.json` written to the state dir | Only after every command finishes |
| One line appended to `events.jsonl` | Only after every command finishes |
| Working directory of each command | The repository root, never the caller's cwd |
| Shell invocation | Never — argv only (FR-010) |

## What it does not do

- Does not read, write, or consult `checklists/implement-complete.md`.
- Does not modify `tasks.md`.
- Does not skip a command because a previous run passed it (FR-018).
- Does not require a spec directory, a tracker, or a network.
