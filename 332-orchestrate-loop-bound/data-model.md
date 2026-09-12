# Data model: orchestrate loop bound

## The pass record

`wfctl resume` already appends one line per pass. It gains one field.

```json
{"ts": "2026-09-10T15:57:26Z", "event": "resume",
 "step": "brainstorm", "command": "/speckit.brainstorm", "auto": true,
 "digest": "a3f91c2b8d04"}
```

`digest` — a short hex digest over the artifact text the same inference already
read: `spec_text`, `plan_text` and `tasks_text` off `Evidence`, in that fixed
order, with a separator between them so that moving a byte from one file to the
next changes the result.

Absent on every line written before this change, and on any line whose report was
built without a feature directory. Absent is not a value to compare — two passes
are only comparable when both carry a digest.

## The verdict

One field on `PipelineReport`, rendered by every view of it.

| Field | Meaning |
| --- | --- |
| `step` | the step that repeated |
| `passes` | how many consecutive passes shared a digest |
| `unchanged` | which artifacts the digest covered, for the report to name |

Absent when the run is progressing, which is the common case. Present means the
loop has been asked to stop.

## The rule

Read the event log's `resume` lines from the end. Take the run of lines that
share both `step` and `digest`, stopping at the first line that differs in
either, or that carries no digest.

- Fewer than three such lines — the run is progressing. No verdict.
- Three or more — a stall on that step.

Older logs wrote two `resume` lines per pass with identical timestamps. Two lines
sharing a timestamp are one pass, and collapse to one before the run is counted;
without that a single legacy pass reads as two and the bound fires a pass early.

A line that cannot be parsed is skipped, and skipping it does not break the run —
the lines on either side are compared as neighbours. This is FR-011, and it
matches how `session_started` already reads the same file.
