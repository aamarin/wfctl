# Data Model: spec-root-manifest-key

The feature adds one persisted field and one resolution function. There is no
database, no schema migration, and no serialized object beyond an existing JSON
file gaining a key.

## Persisted: `spec_root` in `.wf-skills-manifest.json`

| Property | Value |
|---|---|
| Location | `<repo-root>/.wf-skills-manifest.json` (gitignored, untracked, per working copy) |
| Type | `string` |
| Cardinality | 0..1 per repository |
| Default | absent — meaning "not recorded", never an empty string |
| Owner | the maintainer, via `wfctl spec-root`; never written by `install-skills` |

**Shape** — a sibling of the existing `tracker` scalar, alongside the layer objects:

```json
{
  "base":    { "repo": "...", "ref": "main", "commit": "...", "items": [...] },
  "claude":  { "...": "..." },
  "tracker": "github",
  "spec_root": "~/Development/pfms-specs"
}
```

**Validation rules**

- Stored verbatim as typed. `~` is **not** expanded at write time, so the value
  stays portable across machines and users.
- Absent, `null`, or empty string → treated as not recorded (FR-004 default path).
- No existence check, and the directory is never created (FR-006, D7).
- Classified as a non-layer key (`_NON_LAYER_KEYS`), so no code that enumerates
  installed layers treats it as one (FR-012, D4).
- An unparseable manifest raises rather than defaulting (FR-015, D6).

**Lifecycle**

| Event | Effect on `spec_root` |
|---|---|
| `wfctl spec-root <path>` | written to the main checkout's manifest |
| `wfctl spec-root --unset` | key removed; resolution returns to the default |
| `wfctl install-skills` (install or upgrade) | untouched — only layer entries are rewritten |
| `wfctl uninstall <agent>` | untouched — only that agent's key is deleted |
| worktree created | worktree's own manifest is regenerated without it; the main checkout's value is what resolves (D2) |
| worktree removed | no effect; the value never lived in the worktree |

## Resolved: the effective spec root

Not persisted — computed per invocation by `spec_root(repo_root) -> Path`.

**Inputs, in precedence order**

| # | Source | Condition |
|---|---|---|
| 1 | `WFCTL_SPEC_DIR` | set and non-empty |
| 2 | `spec_root` in `<repo-root>/.wf-skills-manifest.json` | key present and non-empty |
| 3 | `spec_root` in `<main-checkout>/.wf-skills-manifest.json` | git common dir is named exactly `.git`, and the key is present and non-empty |
| 4 | `<repo-root>/specs` | always — the default |

**Path interpretation**

| Recorded value | Resolves to |
|---|---|
| `/abs/path` | `/abs/path` |
| `~/rel/path` | `<home>/rel/path` |
| `rel/path` | `<dir of the manifest that declared it>/rel/path` |

A relative value anchors to its declaring manifest's directory — never the
current working directory — so one relative value declared in the main checkout
means one shared location for every worktree.

## Unchanged: the spec directory

The directory a feature's artifacts live in. Its name (the branch, or an
issue-key match) and its contents are untouched by this feature; only the parent
it resolves under becomes configurable. `resolve_spec_dir`'s matching order —
exact branch name, then issue-key glob, then the same lookup against ancestor
branches — is preserved verbatim (FR-007).
