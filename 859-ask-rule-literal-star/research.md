# Research: Install asks before changing a settings file

The Technical Context has no open unknowns. Each item below is a choice the
plan rests on.

## How install tells whether a person is there

- Decision: `_interactive()`, which returns `sys.stdin.isatty()`.
- Rationale: It's the seam install already uses, and tests already patch it.
  The worktree creation hook, `/start-session`'s repair, and an agent's Bash
  call all run with stdin not a terminal.
- Alternatives considered: checking stdout as well, as the check at
  `wfctl/cli.py:7347` does. We didn't choose it because a user who pipes
  install's output through `tee` is still at the keyboard and can answer.

## What a yes covers

- Decision: One yes or no per settings file, covering every listed change.
- Rationale: `design/settings-changes-ask-once.md`. One install can change one
  file up to eleven times, and the user agreed to one question per file.
- Alternatives considered: one question per change, and a picker for choosing
  changes. Both were rejected in the design session: the first asks up to
  eleven times, and the second leaves wfctl's entries half-installed in a state
  no release shipped.

## Where each change's description comes from

- Decision: `_ManagedRule.cost` for rules and `_HOOK_GONE` for hooks, with a
  fixed line for removals.
- Rationale: Every shipped entry already carries one, `doctor` prints the same
  line, and the user agreed on 2026-11-23 to reuse them.
- Alternatives considered: a new description field per entry, which would
  drift from the cost line.

## What doctor reports

- Decision: Doctor runs the same passes on in-memory copies and prints the
  changes, replacing `_check_managed_hooks` and `_check_retired_permissions`.
- Rationale: The list doctor shows then matches the list install asks about.
  It also covers a shipped rule that was never added, which no check reports
  today.
- Alternatives considered: keeping both checks, downgrading them to warnings,
  and adding a third for never-added rules. We didn't choose this because it
  keeps three descriptions of the same pending state, and the existing ones
  already disagree with install in one case: a file with no hook receipts is
  never checked.
