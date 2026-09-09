---
status: proposed
---

# The permission receipt is a sibling of `merged`, not a second shape inside it

## Context

`the-manifest-owns-what-carries-no-marker` decided that wfctl records, at install
time, whether it added `permissions.deny: ["Bash(cd:*)"]` to a consumer-owned
`.claude/settings.json`. That record settles *who owns the fact*. It does not
settle where the fact is written, and the obvious home is the list that already
holds every entry wfctl merged into that file.

The pressure is that `merged` is not a general list of edits. Every record in it
is a hook, and three call sites read it as one: `_merge_hooks` keys its
carry-forward map by `(path, event)`, `_unmerge_hooks` reaches for
`record["event"]` unconditionally, and the uninstall path counts changed files
off the same iteration. A permission entry has no event and never will.

## Verified

- `_unmerge_hooks` (`cli.py:1995`) calls `_settings.remove_hooks(settings,
  record["event"])` with no guard — a record lacking `event` raises `KeyError`.
- `_merge_hooks` (`cli.py:1901`) builds `prior` as `{(m["path"], m["event"]): m}`
  in `install_skills` (`cli.py:2733`) — the same unconditional read.
- `_merge_hooks` re-reads the settings file inside its per-target loop
  (`cli.py:1937`), so `.claude/settings.json` is already opened once per managed
  event, not once per install.
- `_settings.py`'s module docstring states the constraint a new function inherits:
  *"pure functions over already-parsed data, no `wfctl.*` imports and no I/O."*
- The live manifest carries `merged` as four-key records — `path`, `event`,
  `command`, `created` — and `created` is read back as `p.get("created", False)`
  (`cli.py:1926`), the same defensive shape a new receipt needs.
- `permissions` in a settings file is an object of string lists — the user's own
  global settings holds `permissions.allow` as `["Bash(sed *)", …]`.

## Assumed

- Claude Code matches a `permissions.deny` string by exact equality, so
  `Bash(cd:*)` cannot be decorated to carry wfctl's marker. Falsified if the
  matcher turns out to normalise or glob the rule text, in which case a marked
  variant becomes possible and the level-2 record above is the one to revisit,
  not this one.
- No consumer keeps a `permissions` value that is not an object. Falsified by a
  file in the wild; the cost is a `ValueError` surfaced as a merge problem, which
  is the arm `merge_hook` already uses for a malformed `hooks` key.

## Direct baseline

Put the receipt in `merged`, discriminated by which keys a record carries:
`{"path": …, "permission": "Bash(cd:*)", "added": true}` beside the existing
hook records, and branch on `"event" in record` at each of the three readers.

Concretely: one manifest key instead of two, one iteration in uninstall instead
of two, and no new function in `_settings.py` beyond the pure merge itself. The
cost is that three call sites stop having one shape each. `_unmerge_hooks` grows
a branch whose two arms share no code, and its name stops being true.

## Decision

The receipt is a sibling list, `manifest[agent]["permissions"]`, holding records
of the form `{"path": …, "rule": "Bash(cd:*)", "added": true}`. `merged` keeps
its meaning — hooks only — and every reader of it is untouched. Install and
uninstall each gain one small pass over the new list, and `_settings.py` gains
`merge_permission` / `remove_permission` alongside the two it already has.

The second pass re-reads and re-writes the same settings file. That is not a new
failure mode: the existing hook merge already reads it once per managed event.

## Diagram

```
              baseline                              decision

stable  ┌──────────────────────┐          ┌──────────────────────┐
        │ _settings.py         │          │ _settings.py         │
        │  merge_hook          │          │  merge_hook          │
        │  merge_permission    │          │  merge_permission    │
        └──────────────────────┘          └──────────────────────┘
             ▲            ▲                    ▲             ▲
════ pure / I-O ══════════╪════════════════════╪═════════════╪════════
             │ calls      │ calls              │ calls       │ calls
volatile ┌───┴────────────┴───┐          ┌─────┴──────┐ ┌────┴───────────┐
         │ _merge_hooks       │          │_merge_hooks│ │_merge_permis…  │
         │ _unmerge_hooks     │          │_unmerge_h… │ │_unmerge_permis…│
         │  └ branches on     │          └─────┬──────┘ └────┬───────────┘
         │    "event" in rec  │                │ reads/      │ reads/
         └─────────┬──────────┘                │ writes      │ writes
                   │ reads/writes         ┌────▼─────┐  ┌────▼────────┐
            ┌──────▼───────────┐          │ merged[] │  │permissions[]│
            │ merged[]         │          │ hooks    │  │ rules       │
            │ hooks + rules    │          └──────────┘  └─────────────┘
            └──────────────────┘
```

The graphs differ by one thing: whether a reader has to ask what kind of record
it is holding. On the left every reader of `merged` carries that question; on the
right no reader carries it, at the price of a second list and a second pass.

## Considered

- **Discriminate inside `merged`** (the baseline) — sound, and cheaper by one
  manifest key. It loses because the branch lands in `_unmerge_hooks`, whose
  whole body is one loop with one shape, and a second shape there is read by
  every future change to hook handling.
- **Reuse `event` as a generic slot name** — `{"event": "permissions.deny"}` would
  need no new key at all. Rejected: `_check_managed_hooks` iterates `MANAGED_HOOKS`
  and would look for a hook event by that name, and the value stops meaning what
  the settings schema means by it.
- **Do the permission merge inside `_merge_hooks`'s existing loop** — avoids a
  second read of the file. Rejected for what it costs at the call site rather than
  for a fault: the loop is over `(path, event, command)` targets, and an entry
  with no event has to ride in as a special case of a tuple it does not fit.
- **No receipt in `_settings.py`; do it inline in `cli.py`** — the rule is one
  string in one list and the logic is four lines. Rejected: it is the same class
  of pure decision the module exists to hold, and inline it cannot be tested the
  way `test_settings_merge.py` tests the rest.

## Consequences

- Uninstall edits `.claude/settings.json` from two places, and its "settings
  file(s)" count must union the two rather than add them — both passes touch the
  same file, and adding gives `2` for one file.
- A manifest written before this ships has no `permissions` key. `.get(…, [])`
  reads that as "wfctl added nothing", which is the safe side and needs no
  migration.
- `doctor` gains a second vocabulary. A rule carries no version, so it is present
  or gone and never *behind* — the existing `⬆ … is behind this wfctl` line
  cannot be reused for it.

## Verification

- `test_settings_merge.py` gains the round-trip the hooks already have: a
  consumer file with their own `permissions.deny` entries in, install, uninstall,
  byte-compare.
- A test that installs into a settings file already carrying `Bash(cd:*)`,
  uninstalls, and asserts the rule is still there — the receipt reading `false`
  is the whole decision, and it is invisible in any test that starts from an
  empty file.
- `grep -n 'record\["event"\]' wfctl/cli.py` returns only hook call sites after
  the change; a hit inside a permissions pass means the shapes were merged after
  all.

## Log

- 2026-09-08  proposed  — #136 adds a manifest record that is not a hook, and the
  list it would naturally join is read as hooks by three call sites.
