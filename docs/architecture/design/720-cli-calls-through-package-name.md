---
status: proposed
governs: install-and-drift
---

# The CLI calls a context through the package's name

## Context

Before the move, `cli.py` imported each install module and called through it,
as in `_bundle.BUNDLE_ROOT` and `_settings.merge_hook(...)`. Wiring may now
import only the package (`contexts-are-packages.md`, rule 5), so each of those
51 call sites needs a new way to name what it calls. Every later move under
#671 faces the same choice for its own context.

The tests are why this choice matters. The `bundle` fixture in
`tests/conftest.py` points `BUNDLE_ROOT` at a fake tree for every test, and two
tests replace the install-origin `read` function. A patch reaches the CLI only
if it replaces the name where the CLI looks it up at call time. If the CLI binds
the name at import time instead, the patch never reaches the CLI, and a test reads
the real skills tree instead of the fake one. One test in
`test_install_skills.py` renames a file under `BUNDLE_ROOT`, so that test would
rename a file in the source tree.

## Verified

- `tests/conftest.py` patches `BUNDLE_ROOT` and `read` with `monkeypatch`
  before each test, after `cli` is already imported.
- `wfctl/install/_bundle.py` says callers must read `BUNDLE_ROOT` at call time
  and never bind it as a default argument, for the reason above.
- `wfctl/install/__init__.py` caches each name in the package's globals on
  first use, so a patch on the package replaces the value the CLI reads next.
- `.github/scripts/check_imports.py` treats `install.BUNDLE_ROOT` as an import
  of the package, and `from wfctl.install import _bundle` as an import of the
  internal module, which wiring may not do.

## Assumed

- The CLI keeps calling each context's names in many places, so a qualified
  name reads better than a long import list. If a context exports two or three
  names, either form reads fine.

## Direct baseline

`cli.py` imports each name at the top, as
`from wfctl.install import BUNDLE_ROOT, merge_hook, ...`, and each call site
uses the bare name. This is the form the package
layout skill shows, and it adds nothing new.

## Decision

`cli.py` imports the package once, as `from wfctl import install`, and each call
site names it, as in `install.BUNDLE_ROOT`, `install.merge_hook(...)`. The CLI looks
each name up on the package when the call runs, so a test patches the package
and the CLI sees the patch.

## Diagram

```
        baseline                                decision

  ┌──────────┐   ┌──────────┐            ┌──────────┐   ┌──────────┐
  │ cli.py   │   │ conftest │            │ cli.py   │   │ conftest │
  └────┬─────┘   └────┬─────┘            └────┬─────┘   └────┬─────┘
       │ copies       │ patches               │ reads on     │ patches
       │ names once,  │                       │ every call   │
       │ at import    │                       │              │
═══════╪══════════════╪═══════════════════════╪══════════════╪════ install package boundary
       ▼              ▼                       ▼              ▼
  ┌─────────────────────────┐            ┌─────────────────────────┐
  │ wfctl.install           │            │ wfctl.install           │
  └─────────────────────────┘            └─────────────────────────┘
```

The two graphs have the same components, the same boundary, and the same two
arrows. They differ by when the CLI reads the package. In the baseline, the CLI
copies each name once at import, before conftest patches it, so the patch never
reaches the CLI. In the decision, the CLI reads the package on every call,
so it sees whatever value conftest put there.

## Considered

- **Import names into `cli.py` (the baseline).** We didn't choose it because
  every patched name would need a second patch on `wfctl.cli` as well, and a
  test that forgot it would read the real skills tree with no error.
- **Re-export each module as a namespace, as `from wfctl.install import bundle
  as _bundle`.** This keeps every call site unchanged, so `cli.py` would differ
  only in its import lines. We didn't choose it because it makes every name in
  each module public, which is what the package's `__all__` exists to prevent.
- **Import the internal module, as `from wfctl.install import _bundle`.** The
  import check blocks this from wiring, so it isn't an option.

## Consequences

Each call site in `cli.py` changes its prefix, so this move changes 51 lines of
`cli.py` beyond its import line. A branch that edits one of those lines
conflicts with this one, though each conflict is a one-word prefix. Generic
names are less clear through the package than through their module. For
example, `install.read()` reads the install-origin record. A later PR can
rename them in `__init__.py` and `_LAZY` without changing any other caller.

## Verification

- `uv run pytest -q` passes with conftest patching `wfctl.install.BUNDLE_ROOT`
  and `install.read`, and no test reads the real skills tree.
- `python3 .github/scripts/check_imports.py` passes with no baseline line for
  `cli.py`.

## Log

- 2026-11-04  proposed  — #720: the first move under #671 settles how the CLI names a context's exports
