# Data model: Install asks before changing a settings file

Nothing new is stored. The two types below exist only for the length of one
install or doctor run.

## Settings copy (`_SettingsCopy`)

One per settings file a run looks at.

| Field | Meaning |
| --- | --- |
| `rel` | The file's path from the repo root, such as `.claude/settings.json` |
| `existed` | The file, or a symlink at that path, was there when the run read it |
| `settings` | The parsed file, edited by the passes. `None` when it can't be parsed |
| `problem` | The parse error when `settings` is `None` |
| `read_bytes` | The file's bytes when the run read it, compared again before a save. `None` when the file didn't exist |
| `parsed` | `_read_settings` parsed the file. False for a zero-byte or whitespace-only file read as `{}` |
| `changes` | The changes the passes made to `settings`, in pass order |

Rules:

1. `settings` and `problem` are never both set.
2. A copy with no `changes` is never saved.
3. A copy with `existed` false is saved without asking.
4. A copy with `existed` true is saved only after a yes at a terminal.

## Settings change (`_SettingsChange`)

| Field | Meaning |
| --- | --- |
| `sign` | `+` added, `~` updated, `-` removed |
| `kind` | `hook`, `ask rule`, `deny rule`, or `tool approval` |
| `entry` | The hook's event and command, or the rule or approval text |
| `why` | The entry's cost line, or "wfctl no longer ships this" for a removal |

## Manifest receipts

Unchanged in shape. What changes is when a pass's receipts are written: only
for a file whose outcome is `saved` or `created`. For any other outcome, the
prior receipts for that path are written back as they were.

## Save outcomes

| Outcome | When | File | Receipts |
| --- | --- | --- | --- |
| `created` | File didn't exist | written | the passes' |
| `saved` | Yes at a terminal | written once | the passes' |
| `declined` | No at a terminal, or the prompt was interrupted (`Abort`, `EOFError`, `KeyboardInterrupt`) | untouched | prior |
| `skipped` | No terminal | untouched | prior |
| `failed` | Save raised `OSError`, or the file changed while the question was open | untouched | prior |
