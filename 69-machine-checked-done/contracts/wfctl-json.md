# Contract: `wfctl.json`

The repository's definition of done. Hand-authored, tracked, at the repository
root.

## Shape

```json
{
  "verify": [
    ["uv", "run", "--frozen", "--extra", "dev", "pytest", "-q"],
    ["uv", "run", "ruff", "check", "wfctl/", "tests/"],
    ["uv", "run", "mypy", "wfctl/"]
  ]
}
```

Each element is one command, as an argument vector. Order is the order they run.

## Accepted and rejected

| Input | Result |
| --- | --- |
| File absent | No verification configured |
| `{}` | No verification configured |
| `{"verify": []}` | No verification configured |
| `{"verify": [["pytest"]]}` | One command |
| `{"verify": "pytest -q"}` | **Error** — a string is not a list of argv |
| `{"verify": ["pytest -q"]}` | **Error** — element is a string, not an argv list |
| `{"verify": [[]]}` | **Error** — empty argv |
| `{"verify": [["pytest", 3]]}` | **Error** — non-string token |
| Not valid JSON | **Error** |
| `{"verify": [...], "future": 1}` | Accepted; unknown keys ignored |

The rejection that matters is `["pytest -q"]`. Splitting it on whitespace would
be convenient and is exactly how a token containing shell syntax becomes a shell
invocation. It is rejected with a message naming the fix, not silently split.

## Why a string is never accepted

```json
{"verify": [["sh", "-c", "pytest && rm -rf /tmp/x"]]}
```

This is allowed — the repository asked for a shell and got one, explicitly, in a
tracked file a reviewer reads. What is not allowed is wfctl deciding on its own
that a string should become a shell command. The difference is who chose.

## Not in this file

- No verdict, no timestamp, no result of any kind. Those live in the record,
  which is not tracked. A tracked verdict is a tracked claim about a working
  tree, and the point of the feature is that such claims are not accepted.
- No per-step or per-branch commands. One definition of done per repository.
- No placeholders. Unlike `.agents/trackers/<name>.json`, nothing is substituted.

## Version control

Tracked. `install-skills` builds its ignore list from the files it installs, and
it never installs this one, so no ignore entry is added — verified by a
regression test rather than by an exclusion rule.
