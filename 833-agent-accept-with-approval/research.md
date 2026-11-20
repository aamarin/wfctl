# Research: Agent accepts with approval

## R-001: Which variable says the command runs under Claude Code

- Decision: `CLAUDECODE`, counted when set to any non-blank value. Claude Code sets it to `1`.
- Rationale: Claude Code sets it in every shell it starts, and it is the variable Claude Code documents for scripts to detect it. A session in this branch shows `CLAUDECODE`, `CLAUDE_CODE_SESSION_ID`, and `CLAUDE_CODE_ENTRYPOINT` all set. The user ruled out `WFCTL_AGENT` at clarify, since their profile sets it in every shell.
- Alternatives considered: `CLAUDE_CODE_SESSION_ID`, which wfctl already reads for session identity. It works too. We didn't choose it because `CLAUDECODE` exists to answer exactly this question, and the session id's job is identity.

## R-002: How the guard tells Claude Code from Bob Shell

- Decision: the payload's `tool_name`. Claude Code sends `Bash`, and Bob Shell sends `execute_command` or `run_shell_command`.
- Rationale: `tests/test_guard_entry.py:267` and `:288` already build Bob payloads with those names, and `cli.py:3718` installs the Bob hook with a matcher on them. No install change is needed.
- Alternatives considered: a `--host` flag on the hook command. It's the fallback if a real Bob payload disagrees, at the cost of rewriting every existing hook entry.

## R-003: Whether the dry run can avoid the prompt

- Decision: a new spelling, `wfctl arch check-accept <slug>`, that runs what the dry run runs. `--dry-run` keeps working and prompts.
- Rationale: Claude Code applies `deny`, then `ask`, then `allow`, so an `allow` rule for `wfctl arch accept --dry-run:*` loses to the `ask` rule for `wfctl arch accept:*`. Codex picks the most restrictive matching rule the same way. The dry run is also the design gate's own fix line, which an unattended run follows, so a prompt there stops a run nobody is watching (plan review PR-007).
- Alternatives considered: accept the prompt on every dry run. We didn't choose this because of the unattended runs above.

## R-004: Where the guard finds the auto-approve mode

- Decision: `wfctl.evidence.auto_approve(agent_dir)`, with `agent_dir` resolved from the payload's `cwd`.
- Rationale: `wfctl/evidence/_mode.py:27` is the function `status` reads, and `_review_gate.py` is in evidence, so the call adds no import arrow.
- Alternatives considered: reading the mode file directly. We didn't choose it because it would be a second reader of a format `_mode.py` owns.

## R-005: Clearing the warning on the second superseded record

- Decision: `_records.py` counts a superseded record as claimed when its last `superseded` Log line names a record that exists.
- Rationale: `supersedes` is a single string (`_records.py:250`), and the accepted `prompt-approves-person-commands.md` names `accept-check-threat-model` there. An accepted body isn't edited, so a list form would never reach this case. The `superseded` Log line on `guard-catches-literal-accept.md` already names the successor.
- Alternatives considered: let `supersedes` take a list. It helps the next record that replaces two, but not this one. A one-line record superseding `guard-catches-literal-accept` alone. We didn't choose it because it adds a record whose whole body points at another.

## R-006: Codex

- Decision: ship the Codex `prompt` rules from the table, and keep the terminal check in Codex.
- Rationale: the rules are harmless without the loosening, and `prompt-approves-person-commands.md` lists Codex as supported only after a session in Codex shows the prompt appears inside its sandbox. `prompted_host()` reads only `CLAUDECODE`.
- Alternatives considered: leave the Codex file out until the walk. We didn't choose it because the table test then has nothing to hold in step, and the walk needs the rules installed anyway.
