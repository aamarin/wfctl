# CLI contract: Agent accepts with approval

## `wfctl arch accept <slug> [--agreed TEXT] [--dry-run]`

- `--agreed` becomes optional when there is no terminal and `CLAUDECODE` is set.
- Output on success with no citation:

  ```
  ✓ <slug> is accepted — approved at the permission prompt
    Logged: - 2026-11-20  accepted    — approved at the permission prompt · drawing …
  ```

- With no terminal and no `CLAUDECODE`, the refusal is unchanged.
- At a terminal with no `--agreed`, it exits 1 naming the option.

- A blank `--agreed ""` counts as absent.
- A redraw with no terminal and `CLAUDECODE` set logs `drawing signed off — approved at the permission prompt`.

## `wfctl arch check-accept <slug>` (new)

Runs exactly what `wfctl arch accept --dry-run -- <slug>` runs, with the same
output and exit code. It sits outside every `ask` rule, so it never prompts.

## `wfctl review sign-off`

- With no terminal and `CLAUDECODE` set, it lists the pending commits and signs off without asking for the short sha. Exit codes and the note write are unchanged.
- At a terminal, unchanged.

## `wfctl arch approve-imports`

- With no terminal and `CLAUDECODE` set, it lists the additions and approves without asking for the digest.
- The worktree refusal for `uv run wfctl` is unchanged.

## `wfctl install-skills --agent claude`

Adds five `ask` rules to `.claude/settings.json`:

```
Bash(wfctl arch accept:*)
Bash(uv run wfctl arch accept:*)
Bash(wfctl review sign-off:*)
Bash(uv run wfctl review sign-off:*)
Bash(wfctl arch approve-imports:*)
```

## `wfctl doctor`

A missing rule prints a `✗` line naming the rule and the command that stops prompting, and exits 1, as #407's rule does.

## Worktree guard refusals

A refused person command prints a first line and one reason line. When
several reasons apply, the first in this list prints:

1. Auto-approve:
   `✗ wfctl arch accept is for a person to run in their own terminal, not an agent.`
   `  wfctl's auto-approve is on. Turn it off, or run it in your own terminal.`
2. Bob Shell:
   `✗ wfctl arch accept is for a person to run in their own terminal, not an agent.`
   `  Bob Shell can't ask you first.`
3. Rule missing:
   `✗ wfctl arch accept needs your approval at Claude Code's prompt.`
   `  .claude/settings.json is missing the rule that makes Claude Code ask. Run wfctl install-skills --agent claude.`
4. Not plain:
   `✗ wfctl arch accept needs your approval at Claude Code's prompt.`
   `  Run it plainly, as wfctl arch accept <slug>, with no wrapper or second command, and with no shell characters such as $ ; & | < > ( ) or a backslash or backtick.`

For sign-off and approve-imports, the lines name `wfctl review sign-off` or
`wfctl arch approve-imports`.
