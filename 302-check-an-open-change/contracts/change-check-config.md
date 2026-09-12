# Contract: `change_check` in `wfctl.json`

The repository names the fields it requires on every change, whatever the issue
happens to carry.

```json
{
  "verify": [ ["uv","run","pytest","-q"] ],
  "change_check": ["assignees"]
}
```

`wfctl.json` and not the tracker config, because `.agents/` is gitignored and
rewritten by `install-skills` — a policy written there works for one session and
then vanishes with no error. This file is committed and reviewable, which is what
makes a requirement something a team agreed to rather than something one machine
has.

## Schema

| | |
| --- | --- |
| Type | array of strings |
| Entries | field names, as the backend's `fields` verb emits them |
| Absent | nothing is required; only the issue supplies expectation |
| `[]` | identical to absent |

Entries are the backend's spelling. `assignees`, not `assignee`, when that is
what the verb returns — the mismatch is a finding rather than silence (FR-006),
so the misspelling is visible on the first run rather than never.

## Malformed shapes

Read the way `_verify.load_config` reads `verify`: problems are returned, never
raised, and a half-valid config yields no requirements at all.

| Written | Reported |
| --- | --- |
| not an array | `change_check must be a list of field names` |
| an entry that is not a string | names the index and what was found |
| an empty string entry | names the index |
| duplicate entries | not an error; the duplicate is collapsed |

`wfctl.json` failing to parse is already reported by `doctor`; this reader
degrades to no requirements so that a broken file cannot make the check report
findings it cannot justify.

## Interaction with the issue

The two sources are independent and both apply:

```
required by wfctl.json, blank on the change   ──►  finding
set on the issue, missing from the change     ──►  finding
both                                          ──►  one finding, reported as required
neither                                       ──►  nothing printed
```

Reported as `required` when a key is both, because that is the source the reader
can act on directly — a file in their repository said so, and they can open it.
