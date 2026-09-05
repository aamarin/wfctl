---
status: proposed
---

# The tracker owns what an issue key looks like, including the default

## Context

`_paths` and `_tracker` import each other. It is the only cycle in wfctl, and
everything crossing it is one string:

```
   current                                  the whole cycle
   ───────                                  ───────────────
   _paths.resolve_spec_dir                  _paths → _tracker
     └─► _tracker.load_key_pattern            load_key_pattern(repo_root)
                                            _tracker → _paths
   _tracker.load_key_pattern                  DEFAULT_KEY_PATTERN = r"\d+"
     └─► _paths.DEFAULT_KEY_PATTERN
```

Both imports are function-local, so the cycle does not break module load. Only
one of them says why: `_paths.py:379` carries *"lazy: avoids import cycle at
module load"*, and `_tracker.py:129` carries nothing at all. The cycle is
therefore survived rather than managed — a reader of `_tracker` has no way to
learn that the import's position inside the function is load-bearing, and
hoisting it to the top of the file is an obvious tidy-up that breaks the
package.

The cycle is also an upward edge. `_paths` answers "where is this on this
checkout"; `_tracker` runs the active backend's commands. The current-state view
puts them in different bands, and this is the one edge that runs the wrong way.

`extract_issue_key(branch, pattern)` already takes the pattern as a parameter.
`_paths` deliberately does not own the key *shape* — it owns parsing a branch
name given a shape. The default is the one piece of shape that stayed behind.

## Decision

`DEFAULT_KEY_PATTERN` moves to `_tracker`, beside `load_key_pattern`, the only
function that reads it. `_paths` keeps `extract_issue_key` and takes the pattern
from its caller. The `_tracker → _paths` edge disappears; the cycle with it.

This is a boundary decision, not a scheduled change. Moving the constant is
phase 2 of #149 and belongs to whichever branch does it.

## Owns truth

`_tracker` owns *"what shape is an issue key in this repo, when nothing declares
one?"*.

`_paths` cannot compute it. The shape is a property of the tracker backend —
GitHub issues are `\d+`, a Jira project is `[A-Z]+-\d+` — and `_paths` reads no
tracker configuration and has no way to know which backend is active. It holds
`r"\d+"` only because GitHub was the first backend and the default was written
where the parser lived. A path resolver that knows the default key shape is
answering a tracker question from memory.

## Considered

- **Leave the cycle.** The two lazy imports work.
  Rejected because the safety is unowned, not because it is absent today:
  import safety currently holds
  because two people noticed, and the next author to make either import eager
  breaks load with no test standing in the way. It also leaves "where is the
  default key shape defined" with a historical answer and no principled one.
- **Move `load_key_pattern` into `_paths`.** The opposite cut: `_paths` owns
  both the parser and the pattern, and `_tracker` keeps only command dispatch.
  This is not a worse design in the abstract — it makes `extract_issue_key` and
  its only source of patterns adjacent, which is a real property. It loses on
  the ranked drivers: `load_key_pattern` reads `.agents/trackers/<name>.json`,
  a format `_tracker`'s module docstring declares it owns, so this would put a
  second reader of that format in the band below. Cycle traded for a duplicated
  format reader.
- **Extract a third module for the key shape.** Rejected as a structure invented
  to break a cycle rather than to earn a property. One constant and one function
  do not need a module, and a third name in the graph makes the question "who
  owns the key shape" harder to answer, not easier.

## Consequences

**The cycle closes; the band violation does not.** `_paths → _tracker` survives
this decision and becomes *eager* rather than lazy, so the one upward edge in
the view is still there afterwards and is now unavoidable at module load. That
is accepted deliberately: a cycle is a defect at any layering, while an upward
edge is only a defect against a band model this record does not itself make
binding. Whoever wants that edge gone is asking a different question — whether
`_tracker` belongs in the domain band at all — and it needs its own pass.

`_paths` also gains `rich.Console` and `_io` transitively, on every path
resolution. `cli` already imports both, so the cost lands only on a caller
importing `_paths` alone — no such caller exists today, and one appearing later
is the signal to revisit.

`tests/test_key_pattern.py` imports `DEFAULT_KEY_PATTERN` from `_paths` and will
need its import updated by whoever performs the move.

## Log

- 2026-09-04  proposed    — #149 phase 1, pass 1: the only cycle in the graph
