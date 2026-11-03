# Quickstart: checking the issue section by hand

The suite checks the strings. These two runs check the change on real branches, since the case that still needs the body is the one easiest to skip.

## A branch with a handoff

In the `699-session-report-issue-body` worktree, which has a `session-summary.md`:

```bash
uv run wfctl status --session
```

The `Issue (tracker text)` section shows the header fields, then `Body left out, since the handoff below names the work. `wfctl issue view 699` prints it.`, and none of the issue's Why, Measured, or Scope text.

## A branch with no handoff

Point the state dir at an empty folder, so the report finds no `session-summary.md` for this branch:

```bash
XDG_STATE_HOME="$(mktemp -d)" uv run wfctl status --session
```

The section prints the header and the body, and the report ends with `Handoff: none on this branch`.
## JSON

```bash
uv run wfctl status --session --json
```

`issue_view` holds the full text, body included, in both runs.
