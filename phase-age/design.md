# Design: report how long a feature has sat in its current phase

A feature that stalled in `plan` three weeks ago renders identically to one that
entered `plan` this morning. `wfctl status` should make the difference visible
in the line it already prints, so a stall is seen rather than remembered.

Levels 1 and 3 are below. Level 2 is answered in
`docs/architecture/phase-entry-is-observed-not-recorded.md`, which is the
authority for where the time comes from; the sketch here only summarises it.

## Decisions ledger

| # | Level | Decision |
|---|---|---|
| 1 | behavior | age annotates the current step only, never every step |
| 2 | behavior | unknown age renders as nothing — never `0d` |
| 3 | behavior | "stalled" is triggered by idle time, not by age in phase |
| 4 | behavior | under one day renders `today`, not `0d` |
| 5 | architecture | artifact mtimes own phase entry; nothing is recorded at transition |
| 6 | architecture | first phase has no predecessor artifact — git branch divergence answers it |
| 7 | design | only the named pipeline artifacts are stat'd, never a directory scan |
| 8 | design | `implement` excludes `tasks.md` from entry, because it edits it |
| 9 | design | git reaches `_pipeline` as an unevaluated callable, not an import |

## Level 1 — Behavior

Every reachable state, read as the literal line `status` prints, judged in that
state.

**Mid-pipeline, progressing.** Entered `plan` six days ago.

```
plan         ▶  6d in plan  ← current
```

True. The number answers the question that was asked.

**Mid-pipeline, stalled.** In `plan` 23 days, nothing touched for 20.

```
plan         ▶  23d in plan — stalled, idle 20d  ← current
```

True, and it is the line the feature exists to produce. `— stalled` carries the
step's colour so it reads before the words do.

**Entered today.**

```
plan         ▶  today  ← current
```

True. `0d in plan` would also be arithmetically true and would read as a bug,
which is why decision 4 exists.

**Implementing, boxes moving.** In `implement` 16 days; `tasks.md` edited an
hour ago.

```
implement    ▶  7/12 done · 16d in implement  ← current
```

True and correctly quiet. This is the state that forces decision 8: if entry
were the newest completed artifact including `tasks.md`, the line would say
`today in implement` after every ticked box — the phase would never appear to
age while the work was going nowhere slowly.

**Implementing, stalled.** In `implement` 16 days; nothing touched for 11.

```
implement    ▶  7/12 done · 16d in implement — stalled, idle 11d  ← current
```

True. `7/12 done` and `idle 11d` together say what one of them alone cannot:
work started and stopped.

**Nothing written yet.** Branch cut 19 days ago, no `design.md`, possibly no
spec directory.

```
brainstorm   ▶  19d in brainstorm  ← current
```

True, and it is the most valuable line here. A feature that was branched and
abandoned before producing an artifact is the stall most likely to go unnoticed,
and it is the one case with no artifact to read — hence decision 6.

**Nothing written, and git cannot answer.** Detached HEAD, or no trunk.

```
brainstorm   ▶  ← current
```

True by omission. Silence is the correct output; a `0d` here would assert the
feature started today, which is the fabricated-stall failure inverted.

**Clock skew.** An artifact mtime in the future, from a copy off another machine.

```
plan         ▶  today  ← current
```

Age clamps at zero. `-3d in plan` is never printed.

**Pipeline complete.** No current step, so no age anywhere. Out of scope below.

### Each level-1 decision, and what it costs at level 3

| Decision | Level-3 consequence |
|---|---|
| age on the current step only | no transition history is needed — one scan of completed artifacts answers it |
| unknown renders as nothing | the value stays `datetime \| None` to the renderer; no zero sentinel anywhere |
| stalled keys on idle, not age | two values from one scan; the second is rendered only when it fires |
| `implement` excludes `tasks.md` | the step→artifact relation must become data, not an `if/elif` chain |
| `brainstorm` falls back to git | `_pipeline` must receive a callable, since it may not import `subprocess` |

## Level 2 — the boundary, in one sketch

The record holds the argument. The line:

```
the session                       │  wfctl
──────────────────────────────────┼──────────────────────────────
agent writes plan.md              │
  (no wfctl command runs)      ───┼─►  nothing observes this
                                  │
`wfctl status`                    │    stats the named artifacts
  renders the line             ◄──┼─    newest completed → entered
                                  │     newest of any    → idle
                                  │
"I entered plan on the 4th"  ─────┼──✗  never accepted from the left
```

The bottom row is the decision. The row above it is why: the transition happens
on the left and is invisible there, so only a read on the right can date it.

## Level 3 — Design

### Checked against the code and the real spec root

```
checked                                    │ assumed — still a bet
───────────────────────────────────────────┼──────────────────────────────────
`specs/` is gitignored; the default root   │ a single global stall threshold is
has no artifact history at all             │ good enough for every phase —
                                           │ `plan` and `implement` plausibly
this project's durable root IS a git repo, │ want different ones
but commits batch design→decompose into    │
one, and archival commits land weeks late  │ no tool rewrites spec artifacts
                                           │ without meaning to; `install-skills`
Finder wrote `.DS_Store` into every spec   │ and `doctor` were checked and write
dir within one second; a "newest file in   │ only to `.agents/`/`.claude/`
the dir" scan called 9 features active     │
that were 11–19 days idle                  │ `speckit.specify` rewriting spec.md
                                           │ from template resets its mtime, and
directory mtimes are bulk-clobbered — 8    │ that is correct: re-specifying is
dirs stamped in the same second by a move  │ re-entering the phase
that left the files inside untouched       │
                                           │ mtime granularity and timezone
file mtimes did survive that move          │ handling are uniform enough that
                                           │ same-day comparisons hold
`_file_exists` already calls `path.stat()`,│
so mtime costs no new I/O and no new       │
dependency in `_pipeline`                  │
                                           │
`_infer_steps` names exactly 7 artifacts:  │
design.md, spec.md, plan.md, tasks.md,     │
delivery.md, checklists/analysis-report.md,│
checklists/implement-complete.md           │
                                           │
`design_gate` already takes git as an      │
unevaluated callable, for exactly the      │
reason that applies here                   │
                                           │
`_trunk_branch` and `merge-base` machinery │
exist in `_paths.py`                       │
                                           │
`steps_display` returns dicts, so new keys │
extend it without disturbing `annotation`  │
                                           │
`wfctl verify` does not exist in this tree │
— no verification record to date against   │
```

The asymmetry is the point: the expensive claims were checked, and two of them
came back false. The `.DS_Store` finding in particular would have shipped as a
silent, permanent under-report.

### What the derivation is

Two values, one scan of the seven named artifacts:

- **entered** — newest mtime among artifacts belonging to *completed* steps,
  excluding any artifact the current step also writes. Falls back to branch
  divergence when no completed step has an artifact. `None` when neither is
  available.
- **idle** — newest mtime among all seven named artifacts, present or not.
  `None` when none exist.

`stalled` is `idle` past the threshold. Age in phase is `now - entered`.

### The one structural change

`_infer_steps` encodes each step's artifact inline in an `if/elif` chain, so
"which artifacts does this step write" is not answerable as data. Decision 8
needs it, because `implement` both completes `tasks` and keeps editing
`tasks.md` — the only overlap in the pipeline.

Two ways, and the module's own precedent decides it. `_STEPS` exists as a single
table specifically because values keyed by the same names in separate tables let
an omission pass silently, and the docstring says so. Extending that table with
each step's artifacts follows the precedent; a named one-off exception for
`implement` is a smaller diff that reintroduces the shape the table was built to
prevent.

Recommend the table. It is a real refactor of `_infer_steps` and should be
sequenced before the age work, not tangled into it.

### Threshold

A constant, no configuration. Measured against the real spec root, idle times
cluster at 0–2.3 days for live work and 11–19 days for abandoned work, with one
at 5 and one at 10.9 — so anything in 7–14 separates them, and the gap is wide
enough that the exact value does not matter yet. Configuration is a surface with
its own ownership question and should wait for a repo that disagrees with the
default.

## Out of scope

- **Ageing a completed pipeline.** "Done but unmerged for three weeks" is an
  integration question, and #101 keeps integration human-owned. Different fact,
  different owner.
- **Listing stalled features across the repo.** Requires walking the spec root
  and mapping directories back to branches — a new command and a new resolution
  problem, not an annotation.
- **Configurable thresholds.** Above.
- **Recording transitions.** Rejected at level 2; see the record.

## Open questions

1. Does `— stalled` belong in `status` only, or should `next`/`resume` surface
   it too? `status` is the glanceable surface; the others are act-on surfaces
   and a stall does not change what to do next.
2. Should the age appear in `current.md`? It is derived, and `current.md` is
   write-once and already known stale (#42). Probably not until #42 lands.
