# Data Model: Session report issue body

This feature adds no data and no persistent state. It changes how the console prints two values the payload already carries.

- **`issue_view`** (string or `None`): The tracker's `view` output, stored as written. On GitHub it is a header of `field:\tvalue` lines, a `--` line, and the body. `None` when `tracker_status["issue_view"]` is a reason code. The JSON keeps it unchanged.
- **`handoff`** (string or `None`): The branch's `session-summary.md`, or `None` when the file can't be read. When it is not `None`, the report prints the `Handoff (session-summary.md)` heading and now also hides the issue body.
- **`issue`** (string): The branch's issue key, used in the pointer line's `wfctl issue view <id>`.
