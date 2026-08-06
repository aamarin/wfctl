# Phase 1 Contract: command surface

wfctl's public interface is its commands. This records what `install-skills` and
`uninstall-skills` accept and guarantee after this feature, so `/speckit.tasks`
and the tests have one source for the surface.

## `wfctl install-skills`

```
wfctl install-skills [--repo URL] [--ref REF] [--agent NAME] [--tracker NAME] [--yes]
```

| Option | Default | Contract |
| --- | --- | --- |
| `--repo` | `https://github.com/aamarin/wf-skills` | Source repo, shallow-cloned once per run |
| `--ref` | `main` | Branch or tag; resolved SHA is pinned in the manifest |
| `--agent` | `none` | **Changed** — was `claude`. Selects the agent layer to add on top of the base layer |
| `--tracker` | unset | `github`, `none`, or a custom name. Unset means "leave the existing choice alone", and on a first interactive install triggers the prompt |
| `--yes` / `-y` | false | Skips the overwrite confirmation **and** suppresses the tracker prompt |

### `--agent` values

| Value | Layer written (in addition to the base layer) |
| --- | --- |
| `none` | nothing |
| `codex` | nothing — prints why, exits 0 |
| `claude` | `.agents/commands` → `.claude/commands`; plus `.claude/skills/<name>` for skills marked `deployment: skill` |
| `bob` | `.agents/skills` → `.bob/skills`; `.agents/commands` → `.bob/commands` |
| `copilot` | `.agents/skills` → `.github/skills` |
| anything else | exit 1, listing accepted names |

### Always installed, regardless of `--agent`

| Source | Destination |
| --- | --- |
| `.agents/skills` | `.agents/skills` |
| `.agents/commands` | `.agents/commands` |
| `.specify/scripts` | `.specify/scripts` |
| `.specify/templates` | `.specify/templates` |

### Guarantees

1. No destination is written by more than one layer.
2. A path recorded under any manifest entry is never backed up or prompted about.
3. A path not recorded under any entry, but present on disk, is backed up to `.wf-skills-backup/` and listed in the confirmation prompt (unless `--yes`).
4. Installed paths are appended to `.gitignore`; `.agents/trackers/*.json` is deliberately exempt.
5. Exit 0 for every supported `--agent`, including `codex`.

### Output

```
✓ Installed from <repo>@<ref>
  base     25 skills · 23 commands · 8 runtime · 1 tracker
  claude   23 commands · 3 skills
```

Per layer, per kind. Replaces the single `✓ Installed N item(s)` total, which
conflated skills, commands, runtime files, and the tracker config into a number
that reads as a skill count.

**Counting rules**:

| Figure | Counted from |
| --- | --- |
| `N skills` | items whose source is `.agents/skills` |
| `N commands` | items whose source is `.agents/commands` |
| `N runtime` | items whose source is one of `_RUNTIME_TARGETS` |
| `N tracker` | the tracker config, counted separately — it is appended outside the targets loop and has no source directory, so it cannot be classified by source like the others |

**Zero-item layers are omitted entirely.** `--agent none` and `--agent codex`
add no layer, so no second line is printed — not a line reading `0`. A kind with
zero items is likewise dropped from its layer's line rather than shown as
`0 commands`.

When no agent layer was added, the run also prints the opt-in hint naming
`--agent claude|bob|copilot`.

### Tracker prompt

Fires only when **all** of: no `--tracker` given, no `tracker` key in the
manifest, `--yes` not given, and stdin is a tty. Declining prints the route to
both the shipped backend and a custom one. Any non-interactive run writes no
tracker.

## `wfctl uninstall-skills`

```
wfctl uninstall-skills [--agent NAME]
```

| Option | Default | Contract |
| --- | --- | --- |
| `--agent` | `claude` | Unchanged. The layer to remove; `base` removes the agent-agnostic layer |

### Guarantees

1. Removes only the named entry's items, restoring each item's backup if it has one.
2. Never touches another entry's paths. **Changed**: removing `claude` no longer removes `.agents/skills`, because `base` owns it.
3. Removing an entry that does not exist reports that and exits 0.
4. The manifest file is deleted only when the resulting object is empty — a surviving `tracker` key keeps the file.
