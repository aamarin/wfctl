Implementation complete: 2026-09-11

22 of 23 tasks. T022's two agent-side halves are open: running `/start-session`
against a branch whose last stop is continued, and against one whose last stop
was wrapped up, and observing which of them asks. Both need a session that did
not write the table — this one did, so its reading is not evidence.

The CLI halves of the quickstart all ran against a tree installed by
`uv run wfctl install-skills`, in an isolated state dir: the flag writes
`"continued": true`, the plain form writes `false`, both stops stayed on disk,
the placeholder warned, the filled handoff did not, and `wfctl status` and
`wfctl log` gained nothing.

`wfctl verify` is what decides, not this file: 3 of 3 passed at 2d73c76.
