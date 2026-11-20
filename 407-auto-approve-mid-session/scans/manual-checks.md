# Manual checks for #407

## T025: a worktree created with `WFCTL_AUTO_APPROVE=1` starts with the mode on

Run on 2026-11-20 against throwaway issue #831, which is now closed. The agent
ran both `workmux add` commands from the `407-auto-approve-mid-session`
worktree, after the user asked it to.

The task said `--base main`. We used `--base 407-auto-approve-mid-session`
instead, since `main` has neither the new `post_create` line nor the
`auto-approve` command, so a worktree based on it couldn't grant the mode.

The worktree guard refuses running `uv run wfctl status --json` in another
worktree, so the result was read from each worktree's state dir. `status
--json` reads `auto_approve` from the same `mode.json`.

| Command | `mode.json` | `mode` event | Result |
|---|---|---|---|
| `WFCTL_AUTO_APPROVE=1 workmux add 831-auto-approve-check --base 407-auto-approve-mid-session` | `{"auto_approve": true}` | one grant, at 2026-11-20T02:06:39Z | pass |
| `workmux add 831-auto-approve-check2 --base 407-auto-approve-mid-session`, variable unset | absent, so off | none | pass |

The grant event carries the session ID of the agent that ran `workmux add`.
The hook inherits the agent's environment, so `wfctl auto-approve` in the new
worktree reports the grant as made by another session, not an unknown one.
This is the path `auto-approve-grant-asks-first` lists as one the prompt
doesn't catch.

## T034: Claude Code asks before the agent turns the mode on

Run on 2026-11-20 in this worktree, with both ask rules present in
`.claude/settings.json`. The installed `wfctl` was 0.29.0, which has no
`auto-approve` command, so its run exited with "No such command" after the
prompt. The prompt is what this check records.

| Command | Permission mode | Prompted |
|---|---|---|
| `uv run wfctl auto-approve on` | auto | yes, the user approved it (screenshot) |
| `wfctl auto-approve on` | auto | yes |
| `uv run wfctl auto-approve off` | auto | no, as intended |
| `uv run wfctl auto-approve on` | default | yes, and the mode turned on after the user approved |
| `wfctl auto-approve on` | default | yes |
| `uv run --project <worktree> wfctl auto-approve on` | auto | yes, after the PR review added the `--project` rules |

The first attempt ran both `on` commands back to back, and the user couldn't
say which one had prompted, so the results above come from a second run with
one command at a time.

## T041: Codex asks and Bob Shell refuses before the agent turns the mode on

Run on 2026-11-20 in this worktree, which Codex trusts through the main
checkout's entry in `~/.codex/config.toml`. Codex was v0.171.0.

The first Codex run showed a prompt, but it came from Codex's sandbox, since
`uv` needed its cache outside the worktree. This worktree had only the Claude
layer installed, so `.codex/rules/wfctl.rules` didn't exist yet. After `uv run
wfctl install-skills --agent codex`, the second run prompted with the rule's
justification.

| Agent | Command | Result |
|---|---|---|
| Codex | `uv run wfctl auto-approve on` | prompted, with "Auto-approve lets the agent answer design gates and run through review stops, so you say yes first." The prompt offered no option to stop asking. |
| Codex, second run | `uv run wfctl auto-approve on` | prompted on each attempt, including the retry with cache access, and the mode turned on only after the user approved |
| Bob Shell | `uv run wfctl auto-approve on` | not run here. The user moved Bob Shell's guard refusal to its own change. |

Bob Shell's refusal left this branch on 2026-11-20, before its live check could
run, since the Bob Shell trial on this machine ran out. The guard code and its
tests are saved beside this file as `bob-shell-guard.patch`, and the record as
it read with Bob Shell is `auto-approve-grant-asks-first.with-bob.md`.
