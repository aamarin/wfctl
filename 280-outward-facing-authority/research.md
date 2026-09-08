# Phase 0 research: notify authority (#280)

One unknown was carried out of `clarify` deliberately — where the grant is
stored. Everything else the spec settled. This resolves it.

## The question

The local grant needs a home in the state dir. `mode.json` already lives there
and holds `auto_approve`. Two shapes:

- **A — a second key on `mode.json`**: `{"auto_approve": true, "notify": …}`
- **B — a second file**, `notify.json`, beside it

## What the code actually says

Checked, not assumed:

- `MODE_NAME = "mode.json"` and its comment calls it *"the one per-feature
  setting, and the only file in the state dir that holds a choice rather than a
  reading."* It names `verify.json` as the shape it copies — *"named, JSON, one
  writer, one reader."*
- `grant_auto_approve` writes `{"auto_approve": granted}` through
  `write_json_atomic`, which is tempfile + `os.replace`. Full-file replacement.
- `auto_approve()` guards three failure shapes and returns `False` for all of
  them, with a docstring explaining why the conservative direction is the point.
- Both the value write and the event append happen in one function, two lines
  apart.

## Decision: B, a second file

`notify.json`, beside `mode.json`, with its own reader and its own writer.

The handoff that opened this issue recommended A, on the grounds that a second
file "duplicates the event-log wiring for no gain." Two things move the answer
the other way, and neither was visible when that recommendation was written.

**One writer, one reader is the shape `mode.json` documents about itself.** Its
own comment names that as the property it copies from `verify.json`. Adding a
second key makes it a file with two writers, and the first thing that costs is
the read-merge-write FR-006 already demands — every write now has to load the
other value, preserve it, and hand both back. That is not a line of code, it is
a new failure mode: a malformed file currently makes `auto_approve` read `False`
and stop for a human, which is safe; under A the same malformed file either
loses the neighbouring value on the next write or has to fail the write, and
neither is obviously right.

**The two values are no longer the same kind of thing.** When the handoff was
written, both were booleans set by the same flag on the same command. They are
not any more. `notify` carries its source — label or local (FR-005) — because
two places can now grant it and the reader has to know which answered. So the
second key is not a second boolean beside the first; it is a record with its own
shape, sharing a file with a bare boolean, under a filename that means *approval
mode*.

**The duplication is real and it is small.** B repeats an `append_event` call and
a read guard — roughly the twelve lines `auto_approve` and `grant_auto_approve`
already occupy. A saves those twelve lines and spends them on merge logic plus a
decision about what a partially-corrupt file means. That is the trade, stated
plainly, and it is the one `install-modes` and `verify.json` both already made in
this repo.

**Rejected: folding into the tracker only, with no local file.** FR-012 requires
the grant to be expressible where no tracker is configured, and the clarify
session put the local command in every repo, not only those.

## Resolution order, since two places can grant

Settled in `clarify` and restated here because the storage shape has to serve it:

```
label absent   + local unset    → refused   (nobody said anything)
label present  + local unset    → granted, source: label
label absent   + local granted  → granted, source: local
label present  + local denied   → refused, source: local deny
```

An explicit deny wins from either place. A missing label says nothing, not no.
`notify.json` therefore stores three states, not two — granted, denied, unset —
and unset is not the same value as denied. This is the `--allow-notify /
--deny-notify / neither` tri-state reaching storage, and it is why a bare boolean
would not have served even without the source field.

## Read timing, and what it costs

FR-014 fixes the read at run start. The label read is a network call
(`gh issue view`), so it happens once per run and its result is held for the
run's duration.

**FR-015 exists because of this.** A failed read decides the whole run, so
"could not reach the tracker" must be recorded distinctly from "no grant was
found." Both resolve to refused; only one of them means a person withheld
authority.

## Ownership

Named here because the constitution gate asks for it, per state introduced:

| State | Computed by | Why not the other side |
|---|---|---|
| Is this branch granted? | wfctl, at run start | The agent asking itself is the claim the grant exists to check (`wfctl-runs-the-verification`). The harness matches command strings and cannot express "may this feature's run notify people" |
| Which source granted it | wfctl, from the resolution order above | Only wfctl reads both places; neither surface knows the other exists |
| Whether a read failed | wfctl | Distinguishing a network failure from an absent grant needs the reader, not the caller |
| What actions were taken with it | wfctl's event log (FR-010) | The agent is the actor; an actor's own account of what it did is the thing the record exists to check |

## Still open, deliberately

- The exact wording of the refused status line. Cosmetic, and `tasks` can carry
  it.
- Whether `--json` gains a `granted_by` field or the source appears only in the
  console line. Affects one test either way.
- **Accepted risk, not resolved**: the two notification assumptions. Declined on
  2026-09-08. Neither outcome changes who may grant or where it is stored, which
  is what made skipping affordable — see `spec.md` Assumptions for what rides on
  each.
