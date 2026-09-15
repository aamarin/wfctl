---
status: proposed
---

# A managed hook entry is identified by its subcommand, not by its event

## Context

`install-skills --agent claude` merges wfctl's hooks into `.claude/settings.json`,
a file the consumer owns. `install-modes` draws wfctl's share as "one entry per
managed event", and the code holds it to that:

```
MANAGED_HOOKS              event → one command          cli.py
merge_hook                 >1 wfctl entry on an event   collapses them — "can only
                                                        come from a hand-edit"
managed_command            the first wfctl entry only   what doctor compares
```

That identity has held because no two wfctl features have shared an event.
`wfctl-performs-the-recycle` puts `wfctl hook recycle` on Stop, beside
`wfctl hook response-shape`. Under the current identity the second entry is
indistinguishable from a pasted duplicate: the next install deletes one of them,
and doctor never looks at whichever is second.

## Direct baseline

Keep one entry per event and fold the features sharing it into one subcommand.
Stop's entry becomes `wfctl hook stop 2>/dev/null || true`, which runs the reply
check and then the recycler. `MANAGED_HOOKS`, `merge_hook` and doctor are
untouched; the installed command changes name once, which doctor reports as
drift until the next install.

It couples two features that share nothing but a moment. The `|| true` that keeps
a reply check harmless also hides a recycler that threw, so a recycle that never
happens looks like one that was never due. And Claude Code reads one JSON object
from a hook's stdout, so the reply check's note and anything the recycler says
have to be merged into it, each feature knowing the other's output.

## Decision

A managed entry's identity is its subcommand: the first word after
`wfctl hook `. Under each event wfctl owns at most one entry per subcommand it
ships for that event. Install replaces an entry in place when its subcommand
matches, collapses two entries with the same subcommand as before, and removes a
wfctl entry whose subcommand this wfctl no longer ships under that event.

## Owns truth

The subcommand owns **"which wfctl feature is this row, and does this wfctl still
ship it here?"**

The event cannot answer it once two features share one: an identity keyed on the
event sees the recycler and the reply check as one row written twice, which is
the collapse that would delete the recycler. The full command string cannot
either — it carries the redirect and `|| true` after the name, and those change
between versions without the feature changing, so exact matching would read an
upgraded row as a foreign one and leave the old one behind.

The file stays the authority, as `install-modes` requires: the subcommand is
already written in every row wfctl installs, so no manifest field is added.

## Considered

- **Match the full command string** — the simplest per-feature identity, and
  wrong across an upgrade for the reason under `Owns truth`: a suffix change makes
  wfctl's own row unrecognisable to the next wfctl.
- **A distinct marker per feature** (`wfctl hook:recycle`, a name field) — Claude
  Code has no name field on a hook entry, and changing the prefix gives up the
  trailing space `_settings.MANAGED_PREFIX` relies on to not claim a consumer's
  `wfctl hookup`. The subcommand is already a per-feature marker.
- **Record entry positions in the manifest** — rejected once already by
  `install-modes`: a position goes stale the moment the consumer edits around it.

## Consequences

- `MANAGED_HOOKS` maps an event to its subcommands. The three call sites that read
  it as event → command change with it: the merge, the uninstall record, doctor.
- The removal of an unshipped subcommand is what keeps renames working. Today a
  renamed Stop subcommand is replaced for free, because any wfctl row on the event
  is "the" row; per-subcommand identity loses that unless install prunes.
- Doctor's per-event messages (`_HOOK_GONE`) become per subcommand — a missing
  recycler and a missing reply check cost different things.
- On acceptance, `install-modes` gets a `Log` line naming this record, as it did
  for `the-manifest-owns-what-carries-no-marker`: its "one entry per managed
  event" is then contradicted by the code.

## Log

- 2026-09-15  proposed    — #371 adds the first second wfctl hook on an event
  that already has one, and the installer would delete it as a duplicate.
