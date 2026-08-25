# Quickstart: Machine-checked done

Adopting the feature in a project, and what changes when you do.

## Adopt it

Write `wfctl.json` at the repository root with the commands that prove your work
is finished, and commit it.

```bash
cat > wfctl.json <<'EOF'
{
  "verify": [
    ["uv", "run", "--frozen", "--extra", "dev", "pytest", "-q"],
    ["uv", "run", "ruff", "check", "wfctl/", "tests/"],
    ["uv", "run", "mypy", "wfctl/"]
  ]
}
EOF
git add wfctl.json && git commit -m "chore: declare the definition of done"
```

That is the whole adoption. There is nothing to install and no flag to enable.

## What changes immediately

```
$ wfctl status
implement    ▶  12/12 done  ← current
                unverified — run `wfctl verify`
```

A branch that read `●` yesterday reads `▶` today. That is the feature working:
the tasks were ticked and the sentinel written, and nothing had checked.

## Reach green

```bash
wfctl verify
```

```
→ uv run --frozen --extra dev pytest -q
521 passed in 27.19s
→ uv run ruff check wfctl/ tests/
All checks passed!
→ uv run mypy wfctl/
Success: no issues found in 11 source files
✓ verified — 3 of 3 passed at a1b2c3d
```

```
$ wfctl status
implement    ●  12/12 done
                verified at a1b2c3d
```

## What sends it back to `▶`

| You did | Status says |
| --- | --- |
| Committed anything | `stale — verified at a1b2c3d, HEAD is e4f5a6b` |
| Edited without committing | `stale — verified at a1b2c3d, tree dirty` |
| Added an untracked file | `stale — verified at a1b2c3d, tree dirty` |
| Changed `wfctl.json` | `stale — definition of done changed` |
| Cloned the repo elsewhere | `unverified — run wfctl verify` |
| Interrupted a run | whatever the previous record said — unchanged |

And what keeps it from ever going green in the first place:

| Situation | Status says |
| --- | --- |
| A command exited non-zero | `failed — 1 of 3 at a1b2c3d`, then the command |
| A command is not installed | same; a missing executable is a failed command |
| The tree changed mid-run | `inconclusive — re-run` |

Re-run `wfctl verify`. There is no resume; every command runs again.

## Reaching `●` requires a clean tree

This is the one consequence worth knowing before you adopt. A record taken on a
dirty tree describes code that is already not what is on disk, so it never reads
current. In practice: **commit, then verify.**

```
$ git status --porcelain
 M README.md

$ wfctl verify
…
✓ verified — 3 of 3 passed at a1b2c3d
⚠ working tree has uncommitted changes — commit to reach ● implement
```

A README typo blocks completion exactly as a source change does. That is
deliberate: the verification run cannot tell which uncommitted change matters.

## Not adopting

Do nothing and nothing changes. No `wfctl.json` means no verification configured,
and every pipeline state reads exactly as it does today. `wfctl verify` in such a
project says so and exits 0, so a shared setup hook or CI step that calls it
unconditionally does not break.

## For agents

The implementation step runs `wfctl verify` as its final action and reports the
verdict. An agent that finishes with a red build is told while it still holds the
context to fix it, rather than leaving the discovery to whoever opens the next
session.
