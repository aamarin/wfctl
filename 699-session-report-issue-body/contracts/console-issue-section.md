# Contract: the console `Issue (tracker text)` section

`wfctl status --session` prints this section after the `Records` line. Tracker text is indented two spaces, and wfctl's own lines are flush left. The section can be in one of four states.

## 1. Handoff printed, tracker text has a `--` line

The header fields print with empty ones trimmed. The `--` line and the body don't print. One flush-left line follows:

```
Issue (tracker text)
  title:        Session report prints the issue body only on a branch's first session
  state:        OPEN
  number:       699
Body left out, since the handoff below names the work. `wfctl issue view 699` prints it.
```

## 2. No handoff (`Handoff: none on this branch`)

Unchanged from today. The header with empty fields trimmed, then the `--` line and the body, all indented. No pointer line.

## 3. Handoff printed, tracker text has no `--` line

Unchanged from today. The whole text, indented. No pointer line, since nothing was left out.

## 4. The issue read returned a reason code

Unchanged from today: `Issue (tracker text): <code>` on one line.

## JSON

`wfctl status --session --json` is unchanged in every state, and `issue_view` holds the whole tracker text.
