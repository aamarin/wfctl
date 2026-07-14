# wfctl

Workflow state CLI for agent session and pipeline tracking.

## Install

```bash
pip install git+https://github.com/MarinVentures/wfctl.git@v0.2.0
```

## Quickstart

```bash
# Start a session in the current git worktree
wfctl start

# Check pipeline progress
wfctl status

# Resume: re-infer step, write next-step.md, print state
wfctl resume

# End the session
wfctl end
```

## Commands

| Command      | Description                                                              |
|--------------|--------------------------------------------------------------------------|
| `start`      | Initialize agent session context (idempotent)                            |
| `status`     | Show pipeline progress inferred from spec artifacts                      |
| `resume`     | Re-infer step from filesystem, write `next-step.md`, print current state |
| `next`       | Write next actionable step to `next-step.md` (automation shortcut)       |
| `end`        | End the current session and write summary scaffold                       |
| `checkpoint` | Save a numbered checkpoint artifact (diff + md)                          |
| `log`        | Print color-coded event timeline for the current session                 |
| `state-dir`  | Print the active XDG state directory path                                |
| `promote`    | Interactively promote memory candidates to permanent                     |

### `resume` vs `next`

`resume` is the primary automation entry point: it re-infers the pipeline step
from the filesystem, updates `current.json`, writes `next-step.md`, and logs a
resume event. Use it when returning to a session or when a skill needs to
advance the pipeline.

`next` is a lighter variant: it writes `next-step.md` without requiring a prior
`wfctl start` (no `current.json` guard). Useful for one-shot step queries.

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
