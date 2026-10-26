# Contract: `wfctl step complete`

```
wfctl step complete <step>
```

Records that a pipeline step is finished. Only `implement` is accepted.

## Success

Writes `checklists/implement-complete.md` in the feature directory, replacing
any record already there, and exits 0:

```
✓ Recorded implement complete, with a copy of tasks.md (12 tasks, 2 incomplete)
```

The counts are the tally of the copy just written, so the agent can see what
the record accepted as finished.

## Refusals

Every refusal exits 1 and writes nothing.

| Condition | Message |
| --- | --- |
| `<step>` is not `implement` | `✗ step complete records only implement, not plan` |
| No feature directory resolves for this branch | `✗ No feature directory for this branch, so there is no tasks.md to record` |
| The feature has no `tasks.md` | `✗ No tasks.md in <feature dir>, so there is nothing to record` |
| A step before `implement` is current | `✗ implement is not reached yet: analyze is the current step` |

The command runs when `implement` is the current step, and when the story is
already past it.

## Help

`wfctl step --help` lists `complete` beside `none` and `sign-off`. The group's
help text becomes:

```
Declare a pipeline pass inapplicable, sign off the plan without a review, or
record implement complete.
```
