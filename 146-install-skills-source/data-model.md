# Data model: install-skills source

One entity changes, and it gains one optional field.

## Manifest layer entry

`.wf-skills-manifest.json`, one object per installed layer, keyed by layer name
(`base`, `claude`, `bob`, `copilot`). Scalar keys beside them (`tracker`,
`spec_root`, `spec_root_asked`) are not layers and are skipped by `_layer_keys`.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `wfctl_version` | string | yes | The tool version that performed the install |
| `content_hash` | string | yes | Digest over the source's bundled trees at install time |
| `installed_at` | string | yes | ISO-8601 UTC timestamp |
| `items` | array | yes | Installed paths, each with its backup pointer |
| **`source`** | **string** | **no** | **Absolute path of the bundle root this layer was installed from. Absent means the default — the running tool.** |

### Rules

- **Absent means default.** Not "unknown". Before this feature the running tool
  was the only possible source, so every manifest predating it correctly reads as
  a default install. There is no migration and no unmeasurable state. This is the
  one way `source` differs from `content_hash`, whose absence *is* unmeasurable
  and warns.
- **Always absolute.** Written resolved, so the value means the same thing from
  any working directory (FR-004).
- **Written per install, never carried forward.** An install that names no source
  writes no `source` key, replacing any previous value (FR-014). The layer entry
  is already replaced wholesale rather than updated, so this needs no special
  handling — omitting the key drops it.
- **Per layer, independently.** Two layers installed at different times may carry
  different values. Each is evaluated against its own.

### Example

A repo whose base layer came from a PR checkout and whose Claude layer came from
the release:

```json
{
  "base": {
    "wfctl_version": "0.16.0",
    "content_hash": "aa4f24d2…",
    "installed_at": "2026-09-05T12:00:00+00:00",
    "source": "/Users/andremarin/Development/wfctl/wt/116-pr/wfctl",
    "items": [ { "path": ".agents/skills/…", "backup": null } ]
  },
  "claude": {
    "wfctl_version": "0.16.0",
    "content_hash": "bb1c88e0…",
    "installed_at": "2026-09-04T09:14:03+00:00",
    "items": [ { "path": ".claude/skills/…", "backup": null } ]
  }
}
```

`base` reports against the checkout; `claude` reports against the running tool.

## Source

Not persisted as an entity of its own — it is the field above plus the rules for
turning a user-supplied path into it.

| State | Produced by | Recorded as |
|---|---|---|
| Default | no source named | key absent |
| Named, package directory | a path holding `agents/` and `specify/` | that path, resolved |
| Named, checkout root | a path holding `wfctl/agents/` | `<path>/wfctl`, resolved |
| Invalid | a path holding neither | nothing — the install fails before copying |

## Derived, not stored

`doctor` computes the digest of a recorded source at read time and compares it to
the stored `content_hash`. Nothing about the comparison is persisted, consistent
with `session-state-is-re-derived`: what the manifest holds is the fact
re-derivation cannot reach — which source the caller chose at the moment of
copying.
