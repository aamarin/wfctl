# Install asks before changing a settings file
Contexts: install-and-drift, consumer-repo

## Problem Statement

`wfctl install-skills` changes an existing settings file only after the user
says yes at a terminal. An install with nobody watching leaves the file alone
and says what it skipped, and `wfctl doctor` reminds the user until they run
install themselves.

## Recommended Direction

Previously, install merged wfctl's hooks and permission rules into
`.claude/settings.json` and `.bob/settings.json` without asking, and printed a
summary afterwards. Currently, most installs run unattended. The worktree
creation hook runs install in every new worktree, and `/start-session` runs it
with `--yes` to repair what `doctor` reports, so nobody reads the summary.
#859 made this visible. Fixing an ask rule that Claude Code read with a literal
`*` meant removing the old rule, and the first version of the fix removed it
from the user's file with nobody asked.

Install now asks first, for every add, update, and removal. The question shows
each change with the line `doctor` already prints for that entry, saying what
the user loses without it. A yes saves the file once. A no, or no terminal,
leaves the file byte-identical. `--yes` doesn't answer the question, because
the worktree hook and `/start-session` pass it with nobody there.

A settings file that doesn't exist yet is created without a question. A new
worktree has no settings file, since `.claude/` is gitignored, and asking there
would leave it without the worktree guard's hook and the ask rules.

`doctor` reports pending settings changes as a warning, not a failure, with the
install command for the user's own terminal. `/start-session` can't apply the
change, so a failure would repeat at every session start.

## Boundaries and Ownership

The user decides whether their settings file changes, by answering install's
question at a terminal. wfctl decides what the change would be, from the
manifest's record of what it added. The agent shouldn't decide, since it would
be approving a change to its own permissions. `settings-edit-asks-first.md`
records this boundary and its threat model.

## Software design decisions

- docs/architecture/design/settings-changes-ask-once.md — every pass edits one in-memory copy per settings file, and install asks once and saves once

## Key Assumptions to Validate

- [ ] `sys.stdin.isatty()` is false for the worktree creation hook and for an
      agent's Bash call. A test with stdin from `/dev/null` covers both.
- [ ] Whether Claude Code's `!` prefix gives install a terminal on desktop is
      still unknown. If it does, the user can answer from the chat. Test with
      `! [ -t 0 ] && echo terminal || echo no terminal`.
- [ ] Each shipped hook and rule already carries a cost line. The existing
      `assert` covers hooks, and `_ManagedRule.cost` is a required field.

## MVP Scope

In scope:

1. One in-memory copy per settings file, shared by the hooks, ask rules,
   retire, and Bob Shell passes.
2. One question per changed file, listing every change with its cost line.
3. No save on a no or with no terminal, with the prior manifest receipts kept.
4. `doctor` turns pending settings changes into a warning with the install
   command, including the managed hook check that exits 1 today.
5. `changes/859.fix.md` says the next install asks before removing the old rule.
6. A test for each "Must keep catching" and "Must let through" item in the
   threat model.

## Not Doing (and Why)

- Letting the agent apply the change after the user approves it at Claude
  Code's prompt. That's a new command that waits on the user, with its own
  threat model and guard checks, and #860 tracks it.
- Asking before `uninstall-skills` removes wfctl's entries. Running uninstall
  is the request, and the threat model accepts it.
- Asking before creating a settings file that doesn't exist. A new worktree
  would come up without the guard's hook.
- Changing `.codex/rules/wfctl.rules`. wfctl owns that whole file, so it holds
  none of the user's entries.

## Open Questions

None. The split with #860 was decided on 2026-11-23, after the user confirmed
Claude Code's approval prompt works on mobile in default mode.
