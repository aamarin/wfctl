# Contract: what the check prints

Exit 0 prints one line, `✓ imports follow the Context Map (N modules, M
baseline lines)`. Exit 1 prints one block per failure, a blank line between
blocks, then a count. Every block names the file and line, the contexts
involved, why the rule exists, and what to do (FR-011). Module names below are
examples.

## No arrow on the map

```text
✗ wfctl/evidence/_status.py:41 imports wfctl.session

  ┌ Evidence and derivation ┐           ┌ Session continuity ─┐
  │                         │◀──────────│                     │  allowed, the map draws it
  │ _status.py ─────────────┼─────✗────▶│ wfctl.session       │  refused, no arrow this way
  └─────────────────────────┘           └─────────────────────┘

  Move what you need into Evidence and derivation. If the dependency is
  meant, ask the user to add the arrow in docs/architecture/domain/wfctl.md.
```

## A module inside another context's package

```text
✗ wfctl/session/_handoff.py:12 imports wfctl.evidence._paths

  ┌ Session continuity ─┐           ┌ Evidence and derivation ┐
  │                     │──────────▶│ wfctl.evidence          │  allowed
  │ _handoff.py ────────┼─────✗────▶│ _paths                  │  refused, internal
  └─────────────────────┘           └─────────────────────────┘

  Import it from wfctl.evidence. If the package lacks what you need, export
  it from its __init__.py.
```

## A shared package importing a context

```text
✗ wfctl/_tracker.py:309 imports wfctl._session

  _tracker.py is in tracker, which any context may import. A shared package
  that imports a context makes every context depend on that one. Pass in what
  you need from the caller instead.
```

## Anything but wiring importing wiring

```text
✗ wfctl/_tracker.py:4 imports wfctl.cli

  wfctl.cli is wiring, the layer above the contexts, and only wiring may
  import it. Move what you need into a context's package or a shared package.
```

## Package data in the import graph

```text
✗ wfctl/specify/into.py is package data, which the check doesn't place, and
  it imports a wfctl module or one imports it. Move the code into its
  context's package.
```

## A module that isn't valid Python

```text
✗ wfctl/_session.py:2 isn't valid Python (invalid syntax), so the check
  can't read its imports.
```

A module with a null byte fails the same way, and names its file even though
Python's own error names none. That error carries no line either, so the
failure leaves the line out:

```text
✗ wfctl/_session.py isn't valid Python (source code string cannot contain
  null bytes), so the check can't read its imports.
```

## A file that isn't UTF-8

This covers a module, the domain page, and the baseline.

```text
✗ wfctl/_session.py isn't UTF-8 (byte 5), so the check can't read it
```

The approval check reads each commit's copy of the page and the baseline,
and names the commit:

```text
✗ .github/scripts/check_imports.baseline at HEAD isn't UTF-8 (byte 97), so
  the check can't read it
```

## Baseline and placement

```text
✗ wfctl/_new.py has no package and no placement line in
  .github/scripts/check_imports.baseline. Put it in its context's package, or
  ask the user to approve a placement line for it.

✗ _pipeline.py -> _session.py is on the baseline, and no import matches it any
  more. Delete the line so it can't come back unnoticed.
```

## An addition nobody approved

```text
merge base 4e1c0a7d9b2f
✗ This branch adds 4 lines the check reads, and nobody has approved them:

    baseline  _new.py evidence
    map       arrow session --> evidence
    trusted   changed .github/scripts/check_imports.py 9f3b2c1a07de4b6e8a0c2d4f6b8e0a2c4d6f8b0e
    trusted   deleted .github/workflows/review.yml

  Whether to keep these is the user's decision, and only the user approves
  them. An agent may instead revert them and make the change another way, such
  as moving the code into the importing context. To keep them, ask the user to
  run, in their own terminal, with the installed wfctl rather than `uv run`:

    wfctl arch approve-imports
```

A `trusted` line names a file on the script's `TRUSTED` list. `approve-imports`
prints that file's diff before it asks the user to confirm.

## A page the check can't read

```text
✗ docs/architecture/domain/wfctl.md:158: the Context Map block has a line the
  check can't read:

    EV ==> SC

  Use `A --> B` or `A -->|"label"| B`. The check doesn't skip a line it can't
  read, because a skipped arrow refuses imports with no visible cause.
```

## A reserved name

```text
✗ wfctl/evidence/__init__.py exports `load_record`. A bare "record" means an
  architecture or design decision, so outside arch, name what it loads, such
  as `load_verdict`.
```
