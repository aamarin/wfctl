---
status: proposed
---

# `_io` owns how bytes reach disk, and nothing about wfctl's own files

## Context

`_io` sits at the bottom of the graph: five importers, imports nothing but the
standard library. That shape reads as a layer. Its contents do not.

```
   would be correct in a program        knows a wfctl filename
   that was not wfctl                   ──────────────────────
   ──────────────────────────           append_event      → events.jsonl
   write_json_atomic                    load_agentconfig  → current.json
   write_md_atomic
```

The membership test the current-state view gives the durability band — *"it
would be correct in a program that was not wfctl"* — returns two answers for one
module. That is the question this record exists to close, because the answer
decides the view's bottom band and therefore its top-level shape.

`events.jsonl` is not a write-only sink. Its path is spelled in three modules:

```
   _io.py:54       open(agent_dir / "events.jsonl", "a")     writes
   _session.py:49  agent_dir / "events.jsonl"                reads, for `start`
   cli `log`       agent_dir / "events.jsonl"                reads, for `log`
```

Three spellings of one path, and `_session.has_started` parses a field —
`event == "start"` — that `append_event` writes. `knowledge-placement` is in
force and says a fact with two homes has no owner. This one has three.

`load_agentconfig` has zero callers anywhere, tests included.

## Decision

`_io` is a real layer and its contents are mechanism only: atomic write,
durable append, and nothing that names a wfctl file or field.

The event log is a domain fact, not a durability one, and its owner is
`_session` — the path, the record shape, the append, and the reads. `_io` keeps
the atomic primitives the append is built on.

`load_agentconfig` is dead and goes with the move rather than being relocated.

Performing the move is phase 2 of #149.

## Owns truth

`_session` owns *"what is in this session's event log, and what does a line in
it mean?"*.

`_io` cannot compute it. Knowing that a line with `event == "start"` means the
session began is knowledge about wfctl's pipeline, and `_io`'s whole value is
that it holds none: the moment it knows one wfctl field, the band's membership
test stops being answerable and every later function gets placed by precedent
instead. The reader — `_session.has_started` — is already the module that
interprets the field, and a format whose reader and writer live in different
bands has its meaning in one place and its production in another.

## Considered

- **`_io` owns wfctl's on-disk formats as well as the mechanism — call it the
  persistence layer.** This is the smallest diff: nothing moves, and the band
  gets a wider name. It is a coherent design and plenty of systems are built
  this way. Rejected because it costs the band its membership test: a
  persistence layer that knows wfctl's fields
  has no membership test that excludes anything, so the bottom band would grow
  by default and the view's top-level shape would stop meaning anything within
  a few features.
- **A new `_events` module in the domain band.** One home for the format, no
  existing module's subject stretched, and every writer imports it sideways.
  Genuinely close, and it loses on fit rather than fault: the log is keyed by
  `agent_dir` and `_session` already holds both the directory's meaning and the
  only interpretation of a line in it, so `_events` would be a module whose
  entire content is what `_session` is for. A fourteenth module earns its place
  by holding something no existing one should; this holds something one already
  does.
- **Leave `append_event` in `_io` and move only `load_agentconfig`.** Deletes
  the dead function and stops there. Rejected: `load_agentconfig` is the easy
  half and not the one that costs anything. The three-way spelling of
  `events.jsonl` survives untouched, which is the actual finding.

## Consequences

`_tracker` and `_verify` gain imports of `_session`. Both are domain-band edges
running sideways, which the current-state view's bands allow; no new upward edge
is created.

`_io` drops to two functions. That is small enough to invite folding it into a
caller, and it should not be: five importers depending on one implementation of
atomic replacement is the property, and its size is evidence the boundary is
clean rather than an argument against it.

## Log

- 2026-09-04  proposed    — #149 phase 1, pass 3: is `_io` a real layer
