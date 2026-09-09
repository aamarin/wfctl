# Phase 1 — data model

Two files, both already existing. This feature adds one key to one of them and
two entries to the other.

## The consumer's `.claude/settings.json`

Theirs. wfctl edits named entries inside it and owns nothing else in the file.

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "wfctl hook worktree-guard" }] }
    ],
    "UserPromptSubmit": [ … ],
    "Stop": [ … ]
  },
  "permissions": { "deny": ["Bash(cd:*)"] }
}
```

| Entry | Self-identifying | How wfctl finds it again |
|---|---|---|
| the three hooks | yes | command starts `wfctl hook ` (`MANAGED_PREFIX`) |
| `Bash(cd:*)` | **no** | only by the receipt in the manifest |

`PreToolUse` is the first managed event whose group carries a `matcher`. The
outer `hooks` map is event → *groups*; each group holds a `matcher` and a list of
hook entries. `UserPromptSubmit` and `Stop` have nothing to match on, so their
groups carry no matcher and `merge_hook` has never needed to read one.

## The manifest, `.wf-skills-manifest.json`

wfctl's. Gitignored by convention.

```json
{
  "claude": {
    "items": [ … ],
    "merged": [
      { "path": ".claude/settings.json",
        "event": "PreToolUse",
        "command": "wfctl hook worktree-guard",
        "created": false }
    ],
    "permissions": [
      { "path": ".claude/settings.json",
        "rule": "Bash(cd:*)",
        "added": true }
    ]
  }
}
```

`merged` is unchanged in shape and keeps its meaning: hooks only. `permissions`
is the new sibling.

### Fields

| Field | Meaning | Read at | Absent means |
|---|---|---|---|
| `path` | which settings file the rule is in | install, uninstall, doctor | — |
| `rule` | the exact string wfctl installed | uninstall (exact match), doctor (drift), the declined-removal report | — |
| `added` | did wfctl add it, or was it already there | uninstall | not wfctl's — leave it |

`added` is observed once, at the install that first writes the entry, and carried
forward from the prior record on every install after that. Re-deriving it from
the file would answer a different question: after the first install the rule is
present either way.

The whole `permissions` list absent — a manifest written before this ships —
reads as "wfctl added nothing". No migration.

## States the receipt distinguishes

| Receipt | Rule in the file | Install | Uninstall |
|---|---|---|---|
| none | absent | add it, record `added: true` | — |
| none | present | record `added: false`, touch nothing | leave it |
| `added: true` | exact match | nothing to do | remove it |
| `added: false` | exact match | nothing to do | leave it |
| any receipt | edited | **refuse** | leave it, and say so |
| any receipt | absent | **refuse** | — |

The last two rows are one rule: **a receipt exists and the file does not carry
that rule exactly.** Not "wfctl's copy went missing" — a receipt is wfctl's record
that it looked at this entry before, and the file no longer matching what it saw
is a change only a person can explain. Reading `added` at that moment would split
one question into two answers for no gain: the project is equally entitled to
delete a rule wfctl installed and one it merely noticed.

`--force` accepts the divergence, re-asserts the rule and records `added: true` —
wfctl put this one there.

## The one case that outranks the refusal

A settings file that will not parse. Drift cannot be established in a file wfctl
cannot read, so the refusal does not fire: the file is reported as a problem, the
entry is left untouched, and the rest of the install lands. Refusing there would
be refusing on a guess, and it would hold the whole skills tree hostage to a
stray comma.
