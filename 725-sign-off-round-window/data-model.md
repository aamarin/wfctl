# Data model: sign-off round window

## Sign-off (`reviews/sign-off.json`, branch state folder)

| Field | Type | Meaning |
| --- | --- | --- |
| `sha` | string | The commit the user signed off through. Unchanged. |
| `at` | string | When, as an ISO time. Unchanged. |
| `rounds` | object, group name → whole number | New. Each group's round count when the user signed off, the larger of the branch's run records and the issue's tally. A group with no runs is left out. |

Validation: a missing `rounds`, or one that isn't an object, reads as `{}`. An entry that isn't a whole number of 0 or more is ignored. Either way the window falls back to the whole branch.

Lifecycle: each sign-off replaces the file, so only the latest sign-off's counts apply. Two sign-offs with no rounds between them record the same counts.

Example:

```json
{
  "sha": "4f1c2a9e…",
  "at": "2026-11-05T14:02:11+00:00",
  "rounds": { "security": 3, "code": 3 }
}
```

## Window count (derived, never stored)

`rounds_in_window(group) = max(0, max(runs_started, rounds_tallied) - rounds.get(group, 0))`

`start` refuses when this is at or above the cap and the sign-off doesn't cover every commit left. `_capped` reports a pending group capped under the same test.

## Unchanged

- Run records under `reviews/<group>/runs/NNN/`.
- The round tally under `rounds/<group>/` in the issue's state folder.
- The git note a sign-off writes. CI doesn't count rounds.
