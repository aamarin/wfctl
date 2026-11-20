# Quickstart: Auto-approve has its own command

Run these in a worktree whose branch names an open issue, with a session
started by `/start-session`.

## Turn the mode on and off mid-session

```bash
uv run wfctl auto-approve on
uv run wfctl status --json | jq .auto_approve      # true
uv run wfctl auto-approve
#   auto-approve on — …
#     turned on <ts> UTC by this session
uv run wfctl auto-approve off
uv run wfctl status --json | jq .auto_approve      # false
```

## Start a worktree in the mode

From the main checkout, on a throwaway open issue:

```bash
WFCTL_AUTO_APPROVE=1 workmux add <issue>-auto-approve-check --base main
```

In the new worktree, `uv run wfctl status --json | jq .auto_approve` prints
`true`. A second worktree created without the variable prints `false`.

## See the missing-line note

In a repository whose `.workmux.yaml` predates this change:

```bash
wfctl auto-approve
#   ℹ .workmux.yaml has no auto-approve line, …
```

After adding the printed entry to `post_create`, the note no longer prints.
