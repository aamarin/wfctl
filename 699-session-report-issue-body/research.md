# Research: Session report issue body

## Which condition hides the body

- Decision: The body is hidden whenever the report prints the `Handoff (session-summary.md)` heading, which is when `payload["handoff"]` is not `None`.
- Rationale: The user chose this in clarify. A worktree's first session often has a handoff already, and the handoffs this repo writes tell the agent to read the issue first. Using the same test as the `Handoff` section means the two sections can't disagree.
- Alternatives considered: Hiding the body only after the branch's first session. We didn't choose this because that session would load the issue twice, and the report would need a session count it doesn't compute today.

## How the section points at the full issue

- Decision: A flush-left line names `wfctl issue view <id>`.
- Rationale: The text `gh issue view` returns has no URL, and the `wfctl issue view` command already prints the full issue through whatever tracker the repo uses.
- Alternatives considered: Adding the issue's URL. We didn't choose this because it means changing the tracker's `view` command, and a bare `install-skills` never refreshes a tracker file that's already there, so every repo would need `install-skills --tracker github` first.

## Where the body is cut

- Decision: `_trim_issue` takes a `keep_body` keyword and returns the trimmed text together with whether it dropped a body. `render_session_report` passes `keep_body=payload["handoff"] is None`.
- Rationale: `_trim_issue` already finds the `--` line to trim empty header fields, so it is the one place that knows where the body starts. Returning whether it cut lets the renderer print the pointer line only when that's true, which covers text with no `--` line (FR-004).
- Alternatives considered: Cutting the body in `build_session_report`. We didn't choose this because the JSON must keep the body (FR-005). A second splitter in the renderer was also rejected, since two parsers of the same `--` line can disagree.
