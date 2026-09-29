# Contract: declaring the pass, and what `wfctl status` reports

## The declaration

This repository's `wfctl.json` gains this entry (FR-020). The same snippet is
the example in `docs/reference.md` (FR-018).

```json
{
  "steps": {
    "plan": [
      { "name": "plan-walkthrough",
        "command": "/plan-walkthrough",
        "evidence": "plan-walkthrough.md",
        "needs_person": true }
    ]
  }
}
```

`wfctl check config` on it prints nothing and exits 0 once `install-skills` has
put `plan-walkthrough.md` in `.agents/commands/`.

## `wfctl check config` findings

| Declaration | Output line | Exit |
|---|---|---|
| `"needs_person": "yes"` | `plan.plan-walkthrough has a 'needs_person' that is not a boolean` | 1 |
| `"manual": true, "needs_person": true` | `plan.plan-walkthrough declares 'manual' and 'needs_person' — a manual pass already stops an autonomous run` | 1 |

## `wfctl status --json`

`version` moves from `"1.0"` to `"1.1"`. The pass under `plan`, with
`plan.md` present and no marker:

With `auto_approve` on:

```json
{ "name": "plan-walkthrough", "state": "skipped",
  "annotation": "needs a person; auto-approve is on",
  "command": "/plan-walkthrough", "manual": false, "claimed": null,
  "needs_person": true, "is_current": false }
```

With `auto_approve` off:

```json
{ "name": "plan-walkthrough", "state": "in_progress", "annotation": null,
  "command": "/plan-walkthrough", "manual": false, "claimed": null,
  "needs_person": true, "is_current": true }
```

Every built-in pass carries `"needs_person": false`.

With `auto_approve` on, `next_command` names the step after `plan`, and
`attention` is `null`.
