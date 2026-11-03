# Session report leaves out the issue body once a handoff exists

Contexts: session-continuity

## Problem Statement

`wfctl status --session` prints the branch's issue in full on every session. Once the branch has a handoff, the handoff already names the work, so the body costs tokens on every session start without adding anything. In the #432 worktree the body was about 2.4k of the 9.4k tokens `/start-session` printed.

## Recommended Direction

When the report prints a handoff, the `Issue (tracker text)` section prints the issue's header fields and leaves out the body. A flush-left line under the header says the body was left out and names the command that prints it. When the report has no handoff, the section prints the body as it does today.

This reverses one clarify answer from #432, which printed the issue in full on every session. We went with the issue's Scope ("has a handoff") rather than its title ("first session"). The first session on a branch often has a handoff already, because `worktree-handoff` copies the handoff that created the worktree into `session-summary.md`. Those handoffs tell the agent to read the issue anyway, so printing the body as well loads it twice.

### What the section prints

With a handoff:

```
Issue (tracker text)
  title:        Session report prints the issue body only on a branch's first session
  state:        OPEN
  author:       aamarin (Andre A. Marin)
  comments:     0
  projects:     wfctl (In Progress)
  number:       699
Body left out, since the handoff below names the work. `wfctl issue view 699` prints it.
```

Each state the section can reach:

1. The report prints a handoff, and the tracker's text has a `--` line. The section prints the header fields and the line above, which is true, since the handoff prints below it.
2. The report prints `Handoff: none on this branch`. The section prints the header and the body, unchanged from today.
3. The report prints a handoff, but the tracker's text has no `--` line. The report can't tell the header from the body, so it prints the whole text, the same as `_trim_issue` does today.
4. The tracker read fails or times out. The section prints the reason code on one line, unchanged from today.

The JSON output keeps the body in every state, the same way it keeps the handoff sections the console output trims. Another reader of the JSON might need the body, and cutting it there saves no tokens at session start.

### Why a command and not a link

The handoff for this branch asked the section to keep the issue's URL. `gh issue view` prints no URL in the text the tracker returns, so adding one would mean changing the tracker's `view` command. A bare `install-skills` never refreshes a tracker file that is already there, so every repo would need `install-skills --tracker github` before the link showed up. The `wfctl issue view <id>` command already prints the full issue, and an agent can run it directly.

## Boundaries and Ownership

The session report decides whether the body prints, using the handoff it already reads for its own `Handoff` section. That keeps the two sections consistent: the body is hidden exactly when the handoff prints. The tracker is asked for nothing new, and the JSON payload is unchanged.

No boundary moves. This was recorded with `wfctl arch none --context session-continuity`, and the reason goes in the PR body. The accepted record `session-start-reads-branch-progress` already makes the report the one command that builds this output.

## Software design decisions

No level-3 record. The body is cut in the same step that already trims the issue's empty header fields, and no other placement was a real option. This was recorded with `wfctl step none brainstorm.software-design --context session-continuity`.

## Key Assumptions to Validate

Checked against the code and the live report:

- [x] The tracker's text separates the header from the body with a `--` line. `_trim_issue` already relies on it, and this branch's report shows it.
- [x] `payload["handoff"]` is `None` exactly when the report prints `Handoff: none on this branch`.
- [x] `build_session_report` stores the raw issue text before the console trims anything, so the JSON keeps the body.
- [x] `wfctl issue view <id>` exists and prints the full issue.
- [x] GitHub is the only tracker wfctl ships, and its `view` verb is `gh issue view {id}`.

Still to check by hand, since the suite checks strings and not what a session does with them:

- [ ] `uv run wfctl status --session` in this worktree prints no issue body.
- [ ] The same command on a branch with no `session-summary.md` prints the body.

## MVP Scope

1. The console section hides the body when the report prints a handoff, and prints the line naming `wfctl issue view <id>`.
2. Tests cover the four states above, and that the JSON keeps the body.
3. A release note, `changes/699.change.md`, since every session start prints less.

## Not Doing (and Why)

- Adding the issue's URL. It needs a tracker config change that every repo has to reinstall, and the command does the same job.
- Trimming the body in the JSON. The JSON saves no session tokens, and another reader may need the body.
- Shortening the body instead of hiding it, such as printing its first paragraph. A partial body reads as the whole issue, and the agent can't tell what was cut.
- Changing which records print at session start. That is #700's scope, and #700 waits on this branch.

## Open Questions

None. The first-session question and the URL question were settled during brainstorm, as described above.
