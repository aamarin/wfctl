# Data model: issue edit verb

This feature adds no stored data of its own. It adds one value to two existing
things.

## Recorded write

- What it is: one `notify-action` event in the session's event log, written by
  `record_outward_action` after a tracker write succeeds.
- New value: `action = "issue-edit"`, with the branch it was made on.
- Rule: one event per successful field write. A two-field edit that fully
  succeeds writes two. A failed write writes none.
- Readers: `standing_blocks` and the restart handoff, which already read every
  `issue-<verb>` action by name.

## Field

- What it is: the name passed to the backend as `{field}`.
- Values: `title`, `body`. The order is fixed, title first.
- Rule: wfctl decides which fields to send. The backend translates the name to
  its own flag, which for `gh` is the same word.
