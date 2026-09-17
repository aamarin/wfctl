# CLI contract: reporting verbs

## Added

### `wfctl report-action <action>`

Records that this run took `<action>`. It takes no options and never refuses.

| Situation | Output | Exit |
| --- | --- | --- |
| No hold stands on `<action>` | `✓ recorded: <action>` | 0 |
| A hold on `<action>` holds step `<s>` | `✓ recorded: <action>` then `  lifted the hold on <s> — it reads from its own artifacts again` | 0 |
| A hold on `<action>` holds no step (no spec dir) | `✓ recorded: <action>` then `  lifted the hold on <action>` | 0 |

Event: `notify-action {action}`.

### `wfctl report-block <action> --reason "<text>"`

Records that the host refused `<action>`. Apart from the name and the missing
`--clear`, this is byte-for-byte what `wfctl blocked` does today.

| Situation | Output | Exit |
| --- | --- | --- |
| `--reason` missing | `✗ --reason is required — a block with no reason holds a step and says nothing` | 1 |
| A spec dir exists | `✓ recorded: <action> blocked — holding `<step>`` then `  Your host refused this, not wfctl. Re-running the step will be refused again.` | 0 |
| No spec dir | `✓ recorded: <action> blocked — no step is being held` | 0 |

Event: `blocked {branch, action, reason, step}`. The step is inferred when the
command runs. If the pipeline is complete, the last step is held.

## Removed, no aliases

| Surface | After |
| --- | --- |
| `wfctl notify <action> [--declined --reason]` | `No such command 'notify'`, exit 2 |
| `wfctl blocked <action> [--reason | --clear]` | `No such command 'blocked'`, exit 2 |
| `wfctl start --allow-notify` / `--deny-notify` | `No such option`, exit 2 |

## Changed

### `wfctl issue comment | create | label`

These never refuse for lack of permission. On exit 0 they record
`notify-action {action: "issue-<verb>"}`. They used to record the bare `<verb>`.

### `wfctl issue close`

On exit 0 it records `notify-action {action: "issue-close"}`. It used to record
nothing.

### `wfctl start`

It prints no notify line, writes no `notify-resolved` event, and makes no
tracker call.

### `wfctl status` (plain)

```
#384  384-strip-allow-notify
will never merge, force-push, close an issue, or delete a branch
or worktree — those are yours, and no setting changes it
your agent decides which commands may run — wfctl can't see
its rules and says nothing about them
────────────────────────────────────
…steps…
────────────────────────────────────
artifacts written          …
definition of done         …
architecture accepted      …
next: …
```

A held step's remedy names `wfctl report-action <action>` where it used to
name `wfctl blocked <action> --clear`.
