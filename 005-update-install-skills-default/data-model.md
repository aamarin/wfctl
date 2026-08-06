# Phase 1 Data Model: update-install-skills-default

The only persistent state this feature touches is `.wf-skills-manifest.json` at
the repo root — gitignored, machine-local, rewritten on every install.

## Entities

### Manifest (the file)

A single JSON object whose keys are either **layer names** or the reserved key
`tracker`. Everything that enumerates agents must skip reserved keys; today one
call site skips `tracker` (`cli.py:761`, `cli.py:944`), and `base` joins it.

| Key | Value | Notes |
| --- | --- | --- |
| `base` | Layer entry | **New.** The agent-agnostic layer. Present after any install. |
| `claude` / `bob` / `copilot` | Layer entry | Present only if that agent was installed. |
| `tracker` | string | Reserved, not a layer. The active tracker's name. |

### Layer entry

Unchanged in shape from today's per-agent entry — only the set of keys that can
hold one changes.

| Field | Type | Meaning |
| --- | --- | --- |
| `repo` | string | wf-skills source URL |
| `ref` | string | Branch or tag installed from |
| `commit` | string | Resolved SHA — pins what was installed |
| `installed_at` | ISO-8601 string | UTC timestamp |
| `items` | array of Item | What this layer owns |

### Item

| Field | Type | Meaning |
| --- | --- | --- |
| `path` | string | Repo-relative destination this layer owns |
| `backup` | string or null | Where the pre-existing file was parked, or null if the destination was empty |

## Ownership rule

Every `path` in the manifest belongs to exactly one layer. This is the invariant
that makes the cross-attribution bug unreachable, and it is enforced by an
assertion over `_BASE_TARGETS` + `_AGENT_TARGETS` destinations rather than by
convention (SC-006).

## State transition: old shape → new shape

The change is not a schema change — no field is added, removed, or retyped.
Paths **move between entries**.

```
before (this repo today, 59 items under one key)
{
  "claude": { ..., "items": [
      {"path": ".agents/skills/speckit-plan",  "backup": null},   ← moves to base
      {"path": ".claude/commands/speckit.plan.md", "backup": null} ← stays
  ]}
}

after a default install
{
  "base":   { ..., "items": [{"path": ".agents/skills/speckit-plan", ...},
                             {"path": ".agents/commands/speckit.plan.md", ...}] }
}

after `--agent claude`
{
  "base":   { ..., "items": [.agents/*] },
  "claude": { ..., "items": [.claude/commands/*, .claude/skills/*] }
}
```

**No migration step rewrites the old manifest.** The next install simply writes
the new shape. The one consequence that must be handled is detection: while
reading a manifest still in the old shape, `.agents/skills/*` is listed under
`claude` but is about to be written by `base`. Foreign-file detection therefore
unions items across *all* entries rather than reading only the current one
(FR-005). Without it, those paths look like files the user created, and the
install prompts to overwrite ~25 of its own directories and backs them up.

## Validation rules

- A reserved key (`tracker`) is never treated as a layer.
- An empty manifest object deletes the file rather than writing `{}` — existing
  behavior in `_save_manifest`, unchanged. A repo that installs, then uninstalls
  every layer, and has no tracker, ends with no manifest file.
- `uninstall-skills --agent <name>` removes only that entry's items and restores
  their backups; it never touches another entry's paths.
- An agent with no repo-local path (`none`, `codex`) writes no entry of its own,
  so uninstalling it reports nothing to remove rather than failing on a missing
  key.
