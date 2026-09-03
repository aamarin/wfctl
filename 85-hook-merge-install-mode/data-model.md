# Data Model: merge install mode

Three entities, per `spec.md`'s Key Entities section. None are new persistent
storage wfctl owns outright — each is a shape imposed on a file wfctl already
touches or a file another feature (#111) already writes.

## Managed hook entry

One JSON object inside the consumer's `.claude/settings.json`.

```
.claude/settings.json
{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command", "command": "wfctl hook user-prompt" } ] }
    ]
  }
}
```

| Field | Value | Notes |
| --- | --- | --- |
| `type` | `"command"` | Claude Code's schema; only value this feature writes |
| `command` | `"wfctl hook user-prompt"` | fixed string — see `research.md`, command name decision |

**Identity**: an entry is wfctl's iff `command` starts with `MANAGED_PREFIX =
"wfctl hook "` (trailing space — without it, a consumer's own `wfctl hookup` or
similar would also match). Not a marker key, not position: the command itself is
the only signal, confirmed unreadable-safe by `_is_managed`'s type-checking (a
malformed entry is "not ours," never a crash).

**Lifecycle**: created on first `install-skills --agent claude` if absent;
replaced in place (same array position) if present and different; left alone if
present and already correct (no write); removed, with upward pruning, on
`uninstall-skills --agent claude`.

**Validation rules** (from FR-001 through FR-010):
- The file's other top-level keys, and every non-matching hook entry in
  `UserPromptSubmit` and every other event, are untouched byte-for-byte.
- At most one managed entry may exist per event after install; two is treated as
  a hand-edit and collapsed to one on the next install (variant C's rule,
  carried forward — see `research.md`).
- A settings file that fails to parse as JSON, or whose top level is not an
  object, is a refusal for that target alone — never a silent `{}`.

## Digest

The text a managed entry's command prints for one skill. Not a new file type
wfctl invents for this feature — the shape is already fixed by #111
(`conversation-response-shape/digest.md`, quoted in full in `research.md`).

| Property | Value |
| --- | --- |
| Location | `<skill-dir>/digest.md`, sibling to `SKILL.md` |
| Owner | the skill (vendored skills carry one via a layering skill, per `vendor-upstream-skills` — see `install-modes`' Consequences) |
| Source read at runtime | the repo's installed `.agents/skills/`, not the bundle — a worktree with an older install re-anchors what it has, not what wfctl currently ships |
| Absence | not an error; that skill contributes nothing to the hook's output |
| Size | no enforced limit in this feature; #111's own is 8 short lines. A digest this hook re-sends every turn is expected to stay short by the skill author's own discipline, not by validation here |

**State transitions**: none. A digest is read fresh on every hook invocation;
nothing about it is cached, versioned, or recorded in the manifest. This is what
makes "which skills are covered" require no re-install when it changes — the
manifest records that the *mechanism* is installed, never *which* skills it
currently covers.

## Merged-path record

Manifest bookkeeping, sibling to `items` inside a per-agent layer entry in
`.wf-skills-manifest.json`.

```json
{
  "claude": {
    "wfctl_version": "0.15.0",
    "content_hash": "...",
    "items": [ ... ],
    "merged": [
      {
        "path": ".claude/settings.json",
        "event": "UserPromptSubmit",
        "command": "wfctl hook user-prompt",
        "created": false
      }
    ]
  }
}
```

| Field | Meaning |
| --- | --- |
| `path` | repo-relative path of the merged file |
| `event` | the hook event this record covers |
| `command` | the exact command installed, for `doctor`'s comparison |
| `created` | whether wfctl created the file (empty on uninstall → delete it) vs. it already existed (empty on uninstall → leave `{}`, the consumer's file to keep or not) |

**Relationships**: keyed by `(path, event)`, one record per merged entry. Never
appears in the layer's `items` list (FR-014) — `uninstall-skills` deletes every
path in `items` outright, which would delete a file wfctl never owned outright.
Carried forward across installs (not recomputed from scratch) so `created`
survives from the install that actually created the file.

**Lifecycle**: written alongside `items` at the end of `install-skills`; read by
`uninstall-skills` to find what to unmerge; read by `doctor` to find what to
freshness-check. Removed from the manifest when the owning agent's whole layer
is uninstalled — same as `items`.
