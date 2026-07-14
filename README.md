# wfctl

Workflow state CLI for agent session and pipeline tracking.

## Install

```bash
pip install git+https://github.com/MarinVentures/wfctl.git@v0.1.0
```

## Quickstart

```bash
# Start or resume a session in the current git worktree
wfctl start

# Check pipeline progress
wfctl status

# Write next actionable step to next-step.md
wfctl next

# End the session
wfctl end
```

## Commands

| Command      | Description                                          |
|--------------|------------------------------------------------------|
| `start`      | Initialize agent session context (idempotent)        |
| `status`     | Show pipeline progress inferred from spec artifacts  |
| `next`       | Write next actionable step to `next-step.md`         |
| `resume`     | Log a resume event and print current state           |
| `end`        | End the current session and write summary scaffold   |
| `checkpoint` | Save a numbered checkpoint artifact (diff + md)      |
| `promote`    | Interactively promote memory candidates to permanent |

Run `wfctl <command> --help` for options.

## Environment Variables

| Variable                | Description                                                  |
|-------------------------|--------------------------------------------------------------|
| `WFCTL_STATE_DIR`       | Override XDG state directory for the current session         |
| `WFCTL_BRANCH`          | Override branch detection                                    |
| `WFCTL_SPEC_DIR`        | Override spec directory root                                 |
| `WFCTL_REPO_ROOT`       | Override git repo root detection                             |
| `WFCTL_CANDIDATES_FILE` | Override path to `memory-candidates.md`                      |
| `XDG_STATE_HOME`        | Base for XDG state path (default: `~/.local/state`)          |
