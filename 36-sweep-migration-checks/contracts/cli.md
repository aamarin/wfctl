# CLI Contract: Sweep the one-time migration checks

The user-visible surface this feature changes. Command names, exit codes, and
argument shapes are unchanged; only emitted output changes.

## `wfctl doctor`

### Before

Emits up to four drift reports before the skills-freshness section:

```
⚠ .workmux.yaml: pre_remove does not call `wfctl archive-specs` …
⚠ .workmux.yaml: pre_remove calls `wfctl archive-story`, renamed to …
⚠ spec_root is set, but <path> still holds N spec directories …
⚠ `.agent/` exists — the superseded per-branch artifact path.
```

### After

Two reports survive; two are gone:

```
⚠ .workmux.yaml: pre_remove does not call `wfctl archive-specs` …   [retained]
⚠ spec_root is set, but <path> still holds N spec directories …     [retained]
```

### Contract

| Aspect | Guarantee |
|---|---|
| Exit code | Unchanged. Neither removed report ever affected it, and neither retained report affects it. Exit code reflects tool/skills freshness only. |
| Ordering | Retained reports keep their relative order and their position before the manifest gate. |
| Retired-hook repos | No longer reported here. Coverage moves to `archive-specs`, which reports at the moment the hook actually runs. |
| Superseded directory | No longer reported anywhere. The rescue path handles it where it matters. |

## `wfctl archive-specs` / `wfctl archive-story`

### Invocation

```
wfctl archive-specs [WORKTREE] [HANDLE]
wfctl archive-story [WORKTREE] [HANDLE]   # retained, hidden
```

Both names remain accepted. Arguments, defaults (`$WM_WORKTREE_PATH`,
`$WM_HANDLE`), and exit semantics are unchanged.

### New output — retired-name notice

Emitted when, and only when, invoked as `archive-story`:

```
⚠ invoked as `archive-story`; renamed to `archive-specs`.
  Re-seed the hook: wfctl install-config
  The alias is retired once this line stops appearing.
```

The third line is not decoration. Without it the reader learns to fix their hook
but not what the *silence* afterwards means, and the silence is the whole signal
— SC-005 requires the removal condition be decidable from output alone, not from
the source comment.

| Aspect | Guarantee |
|---|---|
| Trigger | `ctx.info_name == "archive-story"` |
| Suppression | Never printed under the current name |
| Effect on archiving | None — archiving proceeds identically |
| Effect on exit code | None |

### New output — legacy rescue notice

Emitted when, and only when, at least one file was rescued from the superseded
directory:

```
⚠ rescued N file(s) from legacy `.agent/` — a superseded path
  kept only to rescue them. Nothing else reads it.
  The read is retired once this line stops appearing.
```

| Aspect | Guarantee |
|---|---|
| Trigger | ≥1 entry in `mapped` whose destination starts with `extra/legacy-agent` |
| Count | `N` equals the number of such entries |
| Suppression | Not printed when the directory is absent or empty |
| Effect on exit code | None |

### Interaction

The two notices are independent. A worktree that both holds a superseded
directory and is torn down by a hook naming the retired command emits both, in
either order, and neither suppresses the other.

Existing output is unchanged: the durable-spec-dir notice, the
`no speckit artifacts` line, and the `archived N artifact(s) → <path>` summary
all keep their current wording and conditions. The rescue notice is additional to
the summary, not a replacement — rescued files are counted in both, because the
summary reports what was archived and the notice reports where it came from.

### Exit-code contract (unchanged, restated because it constrains the new output)

| Condition | Exit |
|---|---|
| At-risk artifacts existed and copying failed | non-zero — teardown aborts |
| Everything else, including internal errors | zero — a teardown is never stranded |

Neither new notice may raise an exception or alter this. Both are emitted after
the archive call returns.

## `wfctl install-config`

Behavior unchanged: still seed-once, still refuses to overwrite. The file it
seeds now names `archive-specs` in both the hook line and its comment.

| Aspect | Guarantee |
|---|---|
| Newly seeded repos | Contain zero occurrences of the retired command name |
| Already-seeded repos | Untouched; protected by the retained alias |
| Distribution | The corrected template reaches a machine by tool upgrade, since the bundle ships in the wheel |
