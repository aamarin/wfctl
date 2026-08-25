# Contract: the verification record

`verify.json` in the branch's state directory. Written by wfctl, read by wfctl,
never tracked, never authored by hand.

## Shape

```json
{
  "command": [
    ["uv", "run", "--frozen", "--extra", "dev", "pytest", "-q"],
    ["uv", "run", "ruff", "check", "wfctl/", "tests/"]
  ],
  "exit": 1,
  "failed": [["uv", "run", "ruff", "check", "wfctl/", "tests/"]],
  "sha": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
  "dirty": false,
  "inconclusive": false,
  "at": "2026-08-24T14:02:11Z"
}
```

## How a reader uses it

The completion check answers one question — *is this record a current, passing
verdict for the configured definition of done?* — by five comparisons, in this
order:

```
record missing or unparseable ──► never verified
record.inconclusive           ──► re-run
record.exit ≠ 0               ──► failed, name record.failed
record.command ≠ config.verify──► definition changed
record.sha ≠ HEAD             ──► commit moved
record.dirty or tree dirty    ──► tree dirty
otherwise                     ──► current and passing
```

Reading it costs one file read, one `git rev-parse HEAD`, one `git status
--porcelain`, and one config read. No configured command is executed (FR-009).

## Guarantees

| Guarantee | How |
| --- | --- |
| A record that exists describes a completed run | Written once, after every command finishes (FR-017) |
| A reader never sees a partial file | `write_json_atomic` — tempfile plus `os.replace` |
| A stale record is never mistaken for current | `sha`, `dirty`, and `command` all compared on every read |
| A record cannot certify a different definition of done | `command` is stored and compared, not just the verdict |

## What it deliberately omits

- **Command output.** It streamed when it ran. Storing it turns a fixed-size file
  into an unbounded one for no reader that needs it.
- **A schema version.** Any record that does not parse into every field above is
  treated as absent, which is the safe direction. `current.json` has no version
  either.
- **Per-command timings.** Not needed by any requirement.
- **The second identity capture.** Its only product is the `inconclusive` flag.

## Forgeability

Anything with write access to the state directory can write this file. That is
the stated bar: tamper-evident, not unforgeable. What the shape buys is that a
forgery must name a commit and a clean tree, and it stops being accepted the next
time either changes — so a fabricated record expires rather than persisting.
