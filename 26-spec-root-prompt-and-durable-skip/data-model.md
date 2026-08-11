# Phase 1 Data Model: spec-root prompt and durable-spec skip

No database, no schema migration. The entities here are a manifest file, a
resolved-path decision, and the plan the archive builds before it copies
anything.

## Manifest (`.wf-skills-manifest.json`)

Gitignored, per-checkout, read from the primary checkout when the current one is
silent. Holds installed-layer entries alongside a small number of bare settings.

| Key | Type | Added by | Read by | Notes |
|---|---|---|---|---|
| `<layer>` | object | existing | `_layer_keys` | has `items`, `repo`, `ref`, `commit` |
| `tracker` | string \| null | existing | `_tracker` | `null` means "chose no tracker" |
| `spec_root` | string | existing (#25) | `_manifest_spec_root` | stored exactly as typed; `~` expanded on read |
| `spec_root_asked` | `true` | **new** | install prompt only | never consulted when resolving paths |

**Invariants**

- `spec_root_asked` MUST be added to `_NON_LAYER_KEYS` (`cli.py:604`). `_layer_keys`
  returns every key not in that set and callers do `manifest[key].get("items", [])`;
  a bare `true` raises `AttributeError` immediately in `doctor` and
  `install-skills`. This is the single highest-risk line in the change.
- `spec_root` absent and `spec_root_asked: true` is a valid, expected state — it
  is what choosing the in-repo default produces (FR-012, FR-017).
- Neither key affects `_layer_keys`, uninstall, or drift detection.

**State transitions**

```
never asked                      {}
   │  interactive setup, option 1
   ├────────────────────────────► {spec_root_asked: true}
   │  interactive setup, option 2/3
   └────────────────────────────► {spec_root_asked: true, spec_root: "<path>"}

any state ── wfctl spec-root <path> ──► spec_root set   (asked marker untouched)
any state ── wfctl spec-root --unset ─► spec_root absent (asked marker untouched)
```

`wfctl spec-root` deliberately does not touch the asked marker: it answers the
question directly, and re-asking someone who has used the command would be noise.
Setting the marker there is a defensible alternative but adds a write to a
command whose contract is currently "writes one key."

## Spec location resolution (unchanged)

Recorded here because the containment predicate depends on it and must not
introduce a second rule.

```
WFCTL_SPEC_DIR (env)
  └─► spec_root in this checkout's manifest
        └─► spec_root in the primary checkout's manifest
              └─► <repo_root>/specs        (default; the absence of a key)
```

The asked-marker read (FR-016) uses the same two-manifest walk, via the existing
`spec_root_declaration` (`_paths.py:222`), so the two cannot diverge.

## Archive plan entry

`_plan` already returns `list[tuple[Path, str]]` — source path, archived name.
**The shape does not change.** The containment predicate filters the list; it does
not annotate it.

| Field | Type | Meaning |
|---|---|---|
| source | `Path` | absolute path of the artifact to copy |
| archived name | `str` | destination relative to the archive directory |

Rejected alternative: adding a third field tagging each entry copy-vs-reference,
to allow index rows pointing at durable files. Dropped with the rescue decision —
under it, an artifact that was never at risk has no row to write.

**Containment predicate**

```
at_risk(source) := source is inside the worktree being removed
```

| Source | Inside worktree | In plan |
|---|---|---|
| `<spec_dir>/*`, default `<repo>/specs` | yes | yes |
| `<spec_dir>/*`, external `spec_root` | no | no |
| `<spec_dir>/*`, `spec_root` resolving back inside | yes | yes |
| `<worktree>/.agent/spec.md` (superseded) | yes | yes |

Path containment only. Never "is `spec_root` set" — row 3 is the case that
distinguishes them, and the one an on/off flag gets wrong.

## Archive result

| Field | Type | Meaning |
|---|---|---|
| archive dir | `Path \| None` | `None` when the plan was empty |
| mapped | `list[tuple[str, str]]` | archived name, source as displayed |

`(None, [])` is a normal outcome (FR-004), now reachable for a new reason: a
durable spec location with no superseded design document produces no archive
directory at all.

## Exit status

New. Previously the command never exited non-zero.

| Condition | Exit | Removal |
|---|---|---|
| nothing at risk (durable location, empty plan, missing worktree, non-git dir) | 0 | proceeds |
| at-risk artifacts, all copied | 0 | proceeds |
| **at-risk artifacts, copying failed** | **non-zero** | **refused (R-001)** |
| tool not installed | 0, via the hook's own branch | proceeds |
| tool installed but broken (import error, bad args) | non-zero, uncatchable | refused |

The last row is a consequence, not a design choice: a process that fails before
its own error handling runs cannot report an intended exit status. Under the
rescue framing it is the correct outcome anyway — absence of proof that nothing
was at risk is not proof that nothing was.
