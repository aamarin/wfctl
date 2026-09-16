---
name: approval-settings
description: Use when the user wants to configure tool auto-approval in Bob Shell — explains the approval schema in ~/.bob/settings/settings.json, permission group IDs, and the allowedExecutors command allowlist/denylist.
---

# Approval Settings

Editing Bob Shell approval configuration in `settings.json`.

## Files

| Scope | Path |
|---|---|
| User (all projects) | `~/.bob/settings/settings.json` |
| Project (this repo) | `.bob/settings.json` |

Project settings take precedence over user settings. Changes take effect on the next Bob Shell session start.

## Schema

The two keys that control approvals:

**`tools.allowed`** — auto-approves specific tools or command prefixes. Each entry is `"tool_name"` (whole tool) or `"tool_name(prefix)"` (prefix-matched against the command string). This is the Bob Shell–native mechanism and works for any tool.

```json
{
  "tools": {
    "allowed": [
      "read_file",
      "run_shell_command(git status)",
      "execute_command(uv run)"
    ]
  }
}
```

**`approval.allowed_permissions`** — auto-approves entire permission groups (IDE + Shell). Valid group IDs:

| Group | Covers | Risk |
|---|---|---|
| `read` | File read, directory listing, search | Medium |
| `edit` | File write, create, delete | High |
| `execute` | Terminal/shell command execution | High |
| `mcp` | All MCP server tool calls | Medium-High |
| `skill` | Skill activation | Medium |
| `todo` | Todo list updates | Low |
| `subtask` | Subtask creation | Low |
| `subagent` | Subagent spawning | Low |
| `mode` | Mode switching | Low |

```json
{
  "approval": {
    "forbiddenApprovalGroups": [],
    "allowed_permissions": ["skill", "read"]
  }
}
```

## Workflow

### Adding an approval

1. Read the target settings file with `read_file`.
2. Determine the right key:
   - Approving a specific command prefix → `tools.allowed`, entry `"execute_command(prefix)"` or `"run_shell_command(prefix)"`.
   - Approving an entire tool group → `approval.allowed_permissions`, entry is the group ID string.
3. Check the entry isn't already present before adding.
4. Add the entry with `apply_diff` — never rewrite the whole file.
5. Tell the user the change takes effect on next session start.

### Removing an approval

1. Read the file.
2. Remove the exact entry string with `apply_diff`.
3. If the array becomes empty, leave it as `[]` — don't remove the key.

### Choosing `tools.allowed` vs `allowed_permissions`

- Use `tools.allowed` when the user wants to approve a **specific command** (e.g. `uv run wfctl`) without approving all `execute` commands.
- Use `allowed_permissions` when the user wants to approve **an entire class** of tool (e.g. all skills, all reads).
- Both can coexist — `tools.allowed` entries are honored even when the group is not in `allowed_permissions`.

## Common entries

```json
"execute_command(uv run)"         — any uv run … command
"execute_command(git)"            — any git subcommand
"execute_command(uv run wfctl)"   — any wfctl subcommand via uv
"run_shell_command(uv run)"       — same, for run_shell_command tool
"read_file"                       — all file reads
"list_files"                      — all directory listings
"glob"                            — all glob searches
"grep"                            — all grep searches
```

## Notes

- Prefix matching is left-anchored on the full command string. `"execute_command(uv)"` matches `uv run …` and `uv tool …` — be specific to avoid over-approving.
- `--yolo` flag (`bob --yolo`) auto-approves everything for a session; not a settings-file option.
- `approval.forbiddenApprovalGroups` blocks a group even if it appears in `allowed_permissions`. Leave it `[]` unless explicitly restricting.
