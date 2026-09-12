# Quickstart — #299

## Build the two situations the issue was filed over

Both need a branch whose tasks are closed and whose definition of done passed.
The difference is one record's status field.

```bash
# 1. the situation as reported — work finished, architecture still proposed
uv run wfctl status
#    architecture accepted   ○  1 proposed — <slug>

# 2. a human accepts the record
uv run wfctl arch accept <slug> --agreed "<where the human agreed>"

# 3. the same branch, read again
uv run wfctl status
#    architecture accepted   ●  <slug>
```

Step 2 is a person's, not an agent's — `a-human-accepts-a-decision`, and the
citation is the field that would have to say so falsely. Under `auto_approve`
nobody has agreed, so an unattended run leaves situation 1 standing and that is
the correct outcome.

## Read one fact precisely

```bash
uv run wfctl status --json | python3 -c "
import json,sys
for f in json.load(sys.stdin)['facts']:
    print(f\"{f['value']:6} {f['name']}: {f['detail']}\")
"
```

## The states worth looking at

| To see | Do this |
| --- | --- |
| `n/a` on architecture | run `status` on a branch that touched no record |
| `n/a` on definition of done | run `status` in a repo whose `wfctl.json` declares no `verify` |
| `n/a` on integration | run `status` on the trunk |
| `unmet` on artifacts | run `status` on a branch with no feature directory |

## Definition of done

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
uv run wfctl doctor
```

`uv run` is not optional in this repository: two wfctls are on PATH and only
`uv run` answers whether the installed tree matches the source being edited.
