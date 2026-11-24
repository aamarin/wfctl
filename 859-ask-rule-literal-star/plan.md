# Implementation Plan: Install asks before changing a settings file

**Branch**: `859-ask-rule-literal-star` | **Date**: 2026-11-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from the branch's `spec.md`

## Summary

`wfctl install-skills` asks once before it changes an existing
`.claude/settings.json` or `.bob/settings.json`, and leaves the file alone when
nobody is at a terminal. The four passes that edit those files today each read
and save the file themselves. They now edit one in-memory copy per file and
record each change, and one save step asks and writes
(`design/settings-changes-ask-once.md`). `wfctl doctor` runs the same passes
without saving and reports the pending changes as warnings, so the list doctor
shows is the list install would ask about.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `typer` and `rich`, already in use. Nothing new.
**Storage**: The project's settings files and `.wf-skills-manifest.json`. No new file.
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`
**Target Platform**: macOS and Linux terminals, and agent hosts with no terminal
**Project Type**: CLI
**Performance Goals**: None. A settings file is a few kilobytes, read once per install.
**Constraints**: An existing settings file stays byte-identical unless the user says yes. Minimal-complexity bias.
**Scale/Scope**: Two settings files, three hooks, eight rules, and the Bob Shell tool approvals.

## Constitution Check

This repo has no `.specify/memory/constitution.md`. The gates come from
`AGENTS.md` and the accepted records instead, as recorded in Complexity
Tracking.

- [x] Validation plan exists: the three `uv run` commands, plus one test per
      threat-model item and per doctor finding, listed under Tests.
- [x] Complexity is justified: one small dataclass and one save step replace
      four inline read-and-save loops. The direct baseline and why it lost are
      in `design/settings-changes-ask-once.md`.
- [x] Ownership is stated: the user decides whether a settings file changes,
      and wfctl decides what the change is, from its manifest
      (`settings-edit-asks-first.md`, `## Owns truth`).
- [x] `contexts-are-packages`: the work stays in `wfctl/cli.py` and
      `wfctl/install/`. No new import between contexts, so no baseline line or
      map arrow.
- [x] `change-carries-release-note`: `changes/859.fix.md` is rewritten.
- [x] `a-rule-is-expressed-as-a-check`: every "Must keep catching" and "Must
      let through" item becomes a test.

## Design

### The settings copy

A new dataclass in `wfctl/cli.py`, beside `_read_settings`:

```python
@dataclass
class _SettingsCopy:
    rel: str                      # e.g. ".claude/settings.json"
    existed: bool                 # the file (or a link) was there when read
    settings: dict | None         # None when the file can't be parsed
    problem: str | None           # the parse error, when settings is None
    read_bytes: bytes | None      # the bytes read, compared again before a save
    parsed: bool                  # _read_settings parsed it, not the zero-byte path
    changes: list[_SettingsChange]
```

```python
class _SettingsChange(NamedTuple):
    sign: str    # "+" added, "~" updated, "-" removed
    kind: str    # "hook", "ask rule", "deny rule", "tool approval"
    entry: str   # the event and command, or the rule text
    why: str     # the entry's cost line, or "wfctl no longer ships this"
```

`_load_settings(repo_root, rel)` builds one copy with `_read_settings`.
`existed` uses `exists() or is_symlink()`, the same test `_merge_hooks` uses for
`created` today.

If the file exists and holds zero bytes or only whitespace, `_load_settings`
reads it as `{}` instead of calling `_read_settings`. That way install asks
about it, as the spec's empty-file edge case requires. `_read_settings` stays
unchanged for its other callers.

The copy also keeps `read_bytes: bytes | None`, which holds the file's bytes as
`_load_settings` read them. The save step compares the file against it before
writing.

### The passes edit the copy

Each pass takes `copies: dict[str, _SettingsCopy]` and stops calling
`_read_settings` and `_write_settings`:

1. `_merge_hooks` calls `merge_hook` and `prune_unshipped` on the copy's
   `settings`. It appends `+` when the event had no managed entry for that
   subcommand, and `~` when it had one with a different command or matcher. A
   pruned predecessor is a `-` with "wfctl no longer ships this". The `why` for
   `+` and `~` is the hook's `_HOOK_GONE` line.
2. `_merge_permissions` calls `merge_permission` on the copy and appends `+`
   with the rule's `_ManagedRule.cost`.
3. `_retire_permissions` calls `remove_permission` on the copy and appends `-`.
   Its existing checks stay: the path has to be one wfctl ships rules into, and
   not a symlink or below one.
4. `_unmerge_bob_tool_allows` calls `remove_tool_allow` on the copy and appends
   `-`. Its outside-the-repo and symlink checks stay.

Each pass keeps returning the receipts it returns today. A pass that meets a
copy with `settings is None` skips the file and hands back the prior receipts,
as it does now for an unreadable file. The problem is reported once per file by
the save step, not once per pass.

If `merge_hook` or `merge_permission` raises a `ValueError` because `hooks` or
`permissions` isn't an object, that pass prints the problem as it does today.
The other passes still record their changes, and the question lists only
those.

`_merge_permissions` skips a managed rule the user removed, and it decides that
with the same test `_permission_drift` uses. That test moves into one helper,
`_rule_removed(copy, receipts, rule, kind)`, which both call. A rule counts as
removed only when all four hold:

1. The rule has a receipt, whatever its `added` value.
2. The file existed when `_load_settings` read it.
3. `_read_settings` parsed it. A zero-byte file that `_load_settings` read as
   `{}` doesn't count, since `_permission_drift` treats it as unparseable.
4. The rule isn't in the file.

This keeps three cases adding the rule as they do today: a committed manifest
with no settings file yet (a fresh clone or worktree), a zero-byte file, and an
unparseable one. Under `--force`, the pass re-adds a removed rule as it does
today. Without `--force`, install never reaches the passes when a rule is
removed, because `_permission_drift` refuses first. Doctor runs the passes
without `--force`, so the skip is what keeps a removed rule out of its pending
list (see Doctor).

### The save step

`_save_settings(copies, *, ask: bool) -> dict[str, str]` returns each changed
file's outcome: `saved`, `created`, `declined`, `skipped`, or `failed`.

1. A copy with no changes is not saved and gets no outcome.
2. A copy whose file didn't exist is saved without asking, and is `created`.
3. When `ask` is true, it prints the question (contract below) and calls
   `typer.confirm("Apply them?", default=False)`. A yes saves with
   `_write_settings`, and the outcome is `saved`. A no is `declined`. Each
   `entry` and `why` prints through `escape()` with `soft_wrap=True`, the same
   as the existing summary lines, because a removed entry's text comes from
   manifest receipts that a person can edit.
4. If the prompt raises `typer.Abort`, `EOFError`, or `KeyboardInterrupt`, the
   outcome is `declined`, and the save step moves on to the next file. The
   skills are already copied at this point, and the manifest write after the
   save step is what records them. If an interrupt skipped that write, the
   copied skills would have no record.
5. Before saving a yes, the save step reads the file again and compares it
   with `read_bytes`. If the file changed while the question waited, for
   example through Claude Code's `/permissions`, the outcome is `failed`, and
   nothing is written. The printed line says the file changed during the
   question. Saving anyway would overwrite the user's edit with wfctl's older
   copy.
6. When `ask` is false, the outcome is `skipped`, and the file isn't opened for
   writing.
7. An `OSError` on save is `failed`, printed with the path and the error.

A `saved` file prints the contract's `✓ <path> updated (N changes)` line. A
`created` file isn't asked about, so it prints the same change list the
question would have shown, followed by `✓ <path> created (N changes)`. That
keeps the explanation of each rule, including the `cd` deny rule, in front of
the user. The existing "Merged wfctl's managed entries into …" block is removed,
along with its "It also now denies", "asks", and "No longer asks" lines, since
the change list replaces it in both cases. The comment above the merge, which
says it runs without a prompt, is rewritten.

Every file that ends `declined`, `skipped`, or `failed` gets the contract's
`left unchanged` warning with its change count and the command to run, as
FR-008 requires. A `failed` file prints its reason line first, either the
`OSError` or the contract's changed-during-the-question line. Install's exit
code doesn't change for any of the three, so it exits 0 if nothing else
failed, which matches today's handling of a settings file it can't write.

Install calls it with `ask=_interactive()`. `--yes` is never passed in, so it
can't answer the question (FR-002). For every file whose outcome is `declined`,
`skipped`, or `failed`, install replaces the receipts the passes returned for
that path with the prior receipts from the manifest (FR-007). That keeps the
manifest describing the file as it is, since nothing changed in it.

For `declined` and `skipped`, install prints one warning per file:

```
⚠ .claude/settings.json left unchanged: 3 changes need your yes.
  Run in your terminal: wfctl install-skills --agent claude
```

The command comes from `_runner(repo_root)` and carries `--from` when the run
had one, the same way the `--force` line does today.

Uninstall keeps changing settings files without asking (FR-012). Its three
unmerge passes keep their own read and save, except `_unmerge_bob_tool_allows`,
which install now shares through the copy. Uninstall builds a copy for
`.bob/settings.json`, calls the pass, and saves it with `_write_settings`
directly.

### Doctor

A new `_check_pending_settings(repo_root, manifest) -> None` replaces
`_check_managed_hooks` and `_check_retired_permissions`. For each agent layer
on record that has a settings file (`claude`, `bob`), it builds the copies, runs
the same four passes with the manifest's receipts, and prints each file's
changes in the question's format, followed by the run-in-your-terminal line. It
never saves, and it never touches the exit code (FR-011).

It also reports an unparseable file once, which `_check_managed_hooks` did
before. Running the passes also covers a shipped rule that was never added
(FR-010), which no check reports today, since `_check_managed_permissions`
only looks at rules with a receipt.

A rule the user removed isn't a pending change. `_merge_permissions` skips it
(above), so it's absent from this list, and `_check_managed_permissions` is the
one place doctor reports it, with its `--force` line. That check now calls
`_rule_removed` instead of its own test, and it drops its `added` filter, so
doctor warns about every rule install refuses over. For a receipt with `added`
false, the warning says the rule is gone without saying wfctl installed it, the
same distinction `_permission_drift`'s refusal draws.

This changes what the accepted `install-modes.md` says in its merge-mode
section: "A managed hook missing or wrong is a finding and exits 1." Under
`settings-edit-asks-first.md` it's a warning that leaves the exit code alone.
FR-015 keeps `install-modes.md` unedited in this change, so the follow-up is an
amendment to it once this lands, filed as its own issue.

A file wfctl would create, because it doesn't exist, is not a pending change
and isn't reported here. The `ℹ no agent layer` notice already covers that
case.

### Docs and skills

- `changes/859.fix.md`: the next install asks before removing the old rule, and
  an install with nobody at a terminal leaves the file alone until the user
  runs install themselves.
- `wfctl/agents/skills/start-session/references/doctor-repair.md`: a new
  section saying a pending settings warning can't be repaired from the session.
  The agent reports it verbatim in step 7 and doesn't run install with a faked
  terminal.
- `docs/reference.md`, the merge mode section: install asks before changing an
  existing settings file, and `--yes` doesn't skip it.
- The `--yes` option's help text in `wfctl/cli.py`: it skips the overwrite
  prompt and never answers the settings question.

### Tests

New file `tests/test_settings_ask.py`, with `NO_COLOR` pinned and
`_interactive` patched for each case.

1. One test per "Must keep catching" item (6). Each starts from an existing
   settings file that needs a change, runs the command with stdin not a
   terminal, and compares the file's bytes before and after.
2. One test per "Must let through" item (4).
3. At a terminal, a yes with hooks and rules pending asks once and saves once.
   It counts `typer.confirm` calls and `_write_settings` calls per path.
4. At a terminal, a no leaves the file byte-identical and the manifest's
   receipts unchanged for that file.
5. With both settings files pending under `--agent bob` and then `--agent
   claude`, each file gets its own question. `--agent` takes one value, so one
   run touches one agent's file, and spec US1 scenario 5 is two runs.
6. Every line under a change carries a `why`. A test builds the copies for a
   `{}` settings file holding every retired rule and a pruned hook, so every
   kind of change is present, and asserts none has an empty `why`.
7. Doctor reports a pending hook, a pending rule that was never added, and a
   retired rule still present, prints the command, and exits 0.
8. An unparseable settings file is reported once by install and once by
   doctor, and is left byte-identical.
9. A zero-byte settings file is asked about, and a yes writes the managed
   entries into it.
10. `typer.Abort`, `EOFError`, and `KeyboardInterrupt` each raised from the
    patched confirm leave the settings file byte-identical, and the manifest
    still records the copied skills.
11. A file changed from inside the patched confirm, before a yes, is left as
    the user changed it, and the outcome is `failed` with the changed-file line.
12. Doctor doesn't list a receipted rule the user deleted as pending, and
    `_check_managed_permissions` warns about it once. The test runs with
    `added` true and with `added` false.
13. Rule text in a receipt holding rich markup prints literally in the
    question.
14. With a committed manifest and no settings file, install creates the file
    with every receipted rule. A zero-byte file with receipts gets every rule
    after a yes.

Existing tests that call `_check_managed_hooks` or `_check_retired_permissions`,
or assert doctor exits 1 on a stale hook or a retired rule, are rewritten to the
new check and exit code. Tests that run install on an existing settings file
and expect it changed get `_interactive` patched to true and a yes. The three
tests in `tests/test_install_hook_merge.py` that assert on the removed summary
block (near lines 927, 1446, and 1518) are rewritten to the change list.

## Validation

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`.
- `uv run wfctl install-skills --agent claude` in this worktree, at a desktop
  terminal, run by the user, to see the question and answer it.
- `uv run wfctl doctor` before and after that run.

## Project Structure

### Documentation (this feature)

```text
<spec folder>/
├── design.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/install-question.md
├── scans/clarify.md
└── tasks.md             # /speckit.tasks
```

### Source Code (repository root)

```text
wfctl/
├── cli.py                          # _SettingsCopy, the passes, _save_settings, doctor
└── agents/skills/start-session/references/doctor-repair.md
docs/reference.md
changes/859.fix.md
tests/
└── test_settings_ask.py            # new
```

**Structure Decision**: The settings code already lives in `wfctl/cli.py`
beside `install_skills_cmd`, and the pure merge functions are in
`wfctl/install/_settings.py`. Moving the passes into the `install` package is
part of #671 and isn't done here, so this change adds no import between
contexts.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| No constitution; gates taken from `AGENTS.md` and the accepted records | The repo carries none | A gate with no source is decorative |
