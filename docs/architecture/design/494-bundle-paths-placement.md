---
status: proposed
---

# `bundle_paths()` lives in `_bundle.py` alongside `content_hash()`

## Context

`doctor`'s new orphan check needs the set of file paths the current bundle ships,
to compare against manifest-recorded paths. That set could be computed inline in
`_check_abandoned_entries()` in `cli.py`, or extracted into `_bundle.py` beside
`content_hash()`, which already walks the same trees for the same reason.

`_bundle.py` exists specifically to keep bundle-reading logic out of `cli.py`:
its own module docstring names the reason — "`install-skills` and `doctor` both
read it, and `content_hash` is the one piece of real logic here worth exercising
without importing typer, rich and every command."

## Verified

- `_bundle.py:content_hash()` walks `TREES = ("agents", "specify")` with `rglob`
  and hashes every file; the walk is the full bundle enumeration.
- `_bundle.py` module docstring explicitly names "worth exercising without importing
  typer, rich and every command" as the reason for the module split.
- `test_bundle.py` tests `content_hash()` directly without any cli import.

## Assumed

- The same two trees (`agents`, `specify`) remain the complete bundle. A third tree
  added to `TREES` would automatically be covered by both `content_hash()` and
  `bundle_paths()` with no change to either caller.

## Direct baseline

Compute the path set inline inside `_check_abandoned_entries()` in `cli.py`:

```python
bundle_files = {
    p.relative_to(root).as_posix()
    for tree in _bundle.TREES
    for p in (root / tree).rglob("*")
    if p.is_file()
}
```

This puts bundle-walking logic in `cli.py`, duplicating the traversal pattern
already in `_bundle.content_hash()` and making it untestable without importing
the full cli module.

## Decision

`bundle_paths(root) → frozenset[str]` is added to `_bundle.py`. It walks the same
`TREES` as `content_hash()` and returns source-relative POSIX paths. The baseline
inline approach was rejected.

## Diagram

```
         baseline                        decision

stable   ┌─────────────┐                ┌─────────────┐  ┌──────────────┐
         │  _bundle.py │                │  _bundle.py │  │  _bundle.py  │
         │content_hash │                │content_hash │  │bundle_paths  │(new)
         └─────────────┘                └─────────────┘  └──────────────┘
                                                ▲                ▲
════ install-modes boundary ════════════════════╪════════════════╪════
                                                │                │
volatile ┌──────────────────────────┐   ┌───────────────────────────────┐
         │        cli.py            │   │           cli.py              │
         │ _check_abandoned_entries │   │  _check_abandoned_entries     │
         │   + inline path walk     │   │   calls bundle_paths()        │
         └──────────────────────────┘   └───────────────────────────────┘
```

Baseline: bundle-walking logic lives in `cli.py`, one caller, untestable in
isolation. Decision: one additional export from `_bundle.py`, same pattern as
`content_hash()`, directly testable. The difference is one fewer duplication of
the tree-walk and one more independently-testable function.

## Considered

- Inline in `cli.py` — duplicates the traversal pattern; untestable without the
  full cli import weight; contradicts the stated reason `_bundle.py` exists.

## Consequences

`bundle_paths()` is independently testable without importing typer or rich.
Adding a third bundle tree requires editing `TREES` once; both `content_hash()`
and `bundle_paths()` pick it up automatically.

## Verification

A test in `test_bundle.py` exercises `bundle_paths()` directly, monkeypatching
`BUNDLE_ROOT` the same way `content_hash()` tests do.

## Log

- 2026-10-14  proposed  — written during brainstorm for #494
