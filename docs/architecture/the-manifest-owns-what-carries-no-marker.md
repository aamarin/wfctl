---
status: proposed
---

# The manifest owns whether wfctl added an entry that cannot carry a marker

## Context

`install-skills --agent claude` merges entries into `.claude/settings.json`, a
file the consumer owns. Ownership has one mechanism today and it is
self-describing: a hook is wfctl's when its command starts `wfctl hook `
(`MANAGED_PREFIX`). A consumer reading their own JSON can see which rows are not
theirs, and uninstall finds its own rows by reading the same file.

#136 adds a second kind of entry to that file. Alongside the `PreToolUse` hook
that runs the cross-worktree guard goes `permissions.deny: ["Bash(cd:*)"]` — the
blunt companion that closes the relative-path case the guard reads past. That
string is matched by the agent by exact equality, so it cannot carry a marker:
any decoration changes what it denies.

So for the first time wfctl installs an entry into a consumer-owned file that
does not announce itself, and uninstall has no way to tell wfctl's copy from an
identical one the consumer wrote themselves last year.

## Direct baseline

Leave the boundary where it is — ownership stays readable from the settings file
alone — and treat the shipped string as its own marker: uninstall removes
`Bash(cd:*)` from `permissions.deny` whenever it finds it, exactly as
`remove_hooks` removes any command starting `wfctl hook `.

Concretely, `_unmerge_hooks` gains a branch that drops the string, and nothing is
recorded at install time. One field fewer in the manifest, one code path, and the
existing round-trip test shape covers it.

Its fault is the whole reason this record exists: an identical string is not
evidence of authorship. A consumer who denied `cd` before they ever installed
wfctl loses that rule to an uninstall that believed it was cleaning up after
itself — and loses it silently, since the entry it removed is the one it was
about to report removing anyway.

## Decision

The manifest records, at install time, whether wfctl was the one that added the
unmarked entry. Uninstall removes it only when that record says wfctl added it
*and* the value on disk is still exactly what wfctl shipped. A consumer who
already had the rule keeps it; a consumer who edited it keeps their edit and
wfctl declines rather than overwrites.

The receipt is carried forward across re-installs from the prior record, not
re-derived from the file — the same handling `created` already gets, and for the
same reason: after the first install the entry is present either way, so asking
the file a second time answers a different question than the one recorded.

## Owns truth

The manifest owns **"did wfctl add this entry, or was it already the
consumer's?"**

The settings file cannot: the entry is matched by exact string equality, so it
cannot carry a marker without changing what it denies, and an identical string is
identical whoever wrote it. Authorship is a fact about the install, not a fact
about the file, and only the side that performed the install was ever in a
position to observe it.

Absence of a receipt reads as *not wfctl's*. That is the safe side of the guess —
it costs an entry left behind, where the other side costs a consumer's rule — and
it matches how `created` already degrades when the manifest is missing or
hand-edited.

## Considered

- **String equality as the marker** (the baseline above) — an identical string is
  not evidence of authorship, and the failure is silent in the direction that
  destroys the consumer's work rather than wfctl's.
- **Never remove it** — leaves wfctl's own entry behind after
  `uninstall-skills`, denying `cd` in a repo with nothing left to explain why.
  Uninstall's contract is that it leaves nothing of wfctl's behind, and this
  trades a rare wrong deletion for a certain wrong retention.
- **Do not install the deny entry; keep it in the README** — this is the state
  #129 argued against and #136 exists to end: a rule that lives in one person's
  config is not reviewable and does not survive a fresh install. It is also
  sound, and the reason it loses is scope rather than fault — it answers the
  ownership question by declining to ask it.
- **Teach the guard to resolve relative paths, so no deny entry is needed** —
  closes one of the three gaps `_guard.py` names and leaves two: `cd $VAR` and
  `cd $(…)` are indirection, where the command text never contains the path at
  all. A deny rule covers the verb regardless of how its argument was built, so
  this narrows the companion rule's job without removing it.

## Consequences

- A merged record gains a shape for entries that are not hooks. `_unmerge_hooks`
  today keys every record by `event`; an entry with no event needs its own key,
  and `_check_managed_hooks` must not read it as a hook whose event went missing.
- `doctor` can report the deny entry as present or gone, never as *behind*. It
  carries no version, so `⬆ … is behind this wfctl` has no meaning for it and the
  drift vocabulary needs a second shape.
- The receipt is only as durable as `.wf-skills-manifest.json`, which is
  gitignored by convention. A fresh clone has no manifest, so uninstall there
  removes nothing — which is already true of the managed hooks and is the
  degradation this record chose.

## Log

- 2026-09-08  proposed    — #136 installs the first entry into a consumer-owned
  file that cannot carry wfctl's marker, and uninstall needed an answer before
  the code was written.
