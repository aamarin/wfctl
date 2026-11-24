# Contract: the settings question and the skipped-change warning

These are the lines a user and an agent read. Tests assert on them with
`NO_COLOR` set.

## At a terminal

Printed once per settings file with changes, after the skills are copied:

```
.claude/settings.json needs these changes:
  + hook      PreToolUse wfctl hook worktree-guard
              nothing stops a Bash call reaching into a sibling worktree
  + ask rule  Bash(wfctl arch approve-imports:*)
              without it, the guard refuses wfctl arch approve-imports from the agent, since Claude Code wouldn't ask you first
  - ask rule  Bash(uv run --project * wfctl auto-approve on*)
              wfctl no longer ships this
Apply them? [y/N]:
```

1. The heading names the file by its path from the repo root.
2. One line per change: the sign, the kind padded to one column, and the entry.
3. One line under each change, indented to the entry's column, carrying `why`.
4. The default is no. An empty answer is a no.

After a yes: `✓ .claude/settings.json updated (3 changes)`.

If the file changed while the question waited, nothing is written, and the
warning below follows this line:

```
⚠ .claude/settings.json changed while the question was open, so wfctl didn't save over it.
```

A file install creates isn't asked about. The same change list prints without
the `Apply them?` line, followed by `✓ .claude/settings.json created (8 changes)`.

After a no:

```
⚠ .claude/settings.json left unchanged: 3 changes need your yes.
  Run in your terminal: wfctl install-skills --agent claude
```

## With no terminal

The question isn't printed. The warning above is printed instead, the same text
as after a no. Install exits 0 if nothing else failed.

## In `wfctl doctor`

The same block as the question, without the `Apply them?` line, followed by:

```
  Run in your terminal: wfctl install-skills --agent claude
```

Each line starts with `⚠` on the heading, and the run's exit code is unchanged.

## Wording of the `why` line for a hook

`_HOOK_GONE` lines start with "is gone —", since doctor prints them after the
hook's name. The question prints them on their own line, so the save step drops
the leading "is gone — " for hooks. A test checks that every `_HOOK_GONE` value
starts with that prefix, so a new hook's line can't break the trim.
