---
status: proposed
governs: install-and-drift
---

# A context's tests stay in `tests/` after its code moves

## Context

Under #671, each context moves into its own package, and install and drift is
the first (`contexts-are-packages.md`). This move raises a question every
later move inherits: whether a context's tests move into its package beside
the code, or stay in the top-level `tests/` folder.

Two facts make the choice matter:

1. The install tests aren't only about install. `test_install_skills.py` and
   `test_issue_check.py` also import `cli`, `_tracker`, and `_issue_check`, and
   they depend on fixtures in `tests/conftest.py` that every other test uses.
2. #669 picks which tests to run based on the imports a change affects. It
   reads one test folder, so a second place for tests changes what it has to
   read.

Currently, `tests/` holds every test as a flat file named for what it covers,
such as `test_bundle.py` and `test_settings_merge.py`.

## Verified

- `pyproject.toml` sets `testpaths = ["tests"]`, so pytest collects nothing
  under `wfctl/` today.
- `tests/conftest.py` holds the autouse `bundle` and install-origin fixtures,
  which every install test depends on.
- `tests/test_install_skills.py` imports `wfctl.cli`, and
  `tests/test_issue_check.py` imports `wfctl._tracker` and
  `wfctl._issue_check`, which belong to other contexts.
- `.github/scripts/check_imports.py` reads only the code under `wfctl/`, and it
  skips the package-data folders `agents`, `specify`, and `contracts`.

## Assumed

- Later moves have the same mix of tests. If most contexts turn out to have
  tests that import only their own package, moving them becomes cheap, and
  this record should be revisited.
- #669 keeps reading one test folder. If it starts reading a test's location
  as the context it covers, tests inside the package would suit it better.

## Direct baseline

Leave every test where it is. The test files keep their names and their place
in `tests/`. Only their import lines change, from `wfctl._bundle` to
`wfctl.install._bundle`, and their patches move to the package, where callers
look the name up.

## Decision

We chose the baseline. A context's tests stay in `tests/` as flat files, and a
white-box test imports the internal module it covers by its full path, such as
`from wfctl.install import _provenance`. The package layout skill allows tests
this exception, and the import check doesn't read `tests/`.

A test that patches a name patches it on the package, as in
`monkeypatch.setattr(install, "read", ...)`, since that is where the CLI looks
it up.

## Diagram

```
           baseline (chosen)                 tests inside the package

stable     ┌──────────────┐                  ┌──────────────┐
           │ conftest.py  │                  │ conftest.py  │
           └──────────────┘                  └──────────────┘
              ▲  fixtures                       ▲  fixtures     ▲ fixtures
              │                                 │               │
           ┌──┴───────────┐                  ┌──┴───────────┐ ┌─┴──────────────┐
           │ tests/       │                  │ tests/       │ │ wfctl/install/ │
           │ test_*.py    │                  │ test_*.py    │ │ tests/ (new)   │
           └──────────────┘                  └──────────────┘ └────────────────┘
              │ imports                         │ imports        │ imports
════ the install package boundary ══════════════╪════════════════╪═════════════
              ▼                                 ▼                ▼
volatile   ┌──────────────┐                  ┌──────────────┐ ┌────────────────┐
           │ wfctl.install│                  │ wfctl.cli,   │ │ wfctl.install  │
           │ wfctl.cli …  │                  │ others       │ │ wfctl.cli …    │
           └──────────────┘                  └──────────────┘ └────────────────┘
```

The two graphs differ by one test folder and one fixture arrow. Tests inside
the package add a second folder that pytest, #669, and the fixtures all have to
reach. The install tests still import `cli` and the other contexts, so the new
folder's tests cross the same boundary the old ones did. As a result, moving
them changes nothing at the boundary and adds a second place to look.

## Considered

- **Move the tests into `wfctl/install/tests/`.** We didn't choose this because
  the install tests also import `cli` and two session modules, so the move
  would untangle those imports in the same PR as the code move. It would also
  ship the tests in the wheel unless the packaging excludes them, and give #669
  a second folder to read.
- **Mirror the packages inside `tests/`, as `tests/install/test_bundle.py`.**
  This keeps one test root and shows the context in the path. We didn't choose
  it now because it renames every install test file, and pytest needs an
  `__init__.py` or `rootdir`-relative names to keep two `test_bundle.py` files
  apart. It's a sound option once several contexts have moved and the flat
  folder gets hard to read.

## Consequences

Each move under #671 changes only the import lines and patch targets in its
tests. The test folder still doesn't show which context a test covers, so a
reader checks the import line to find it. A later move can switch to the mirrored
layout in its own PR once more contexts have moved, without undoing this one.

## Verification

- `uv run pytest -q` passes with the five modules under `wfctl/install/` and
  every test still in `tests/`.
- `grep -rn "wfctl\._\(bob_settings\|bundle\|provenance\|settings\|workmux\)"
  tests/ wfctl/` prints nothing, so no test names an old path.

## Log

- 2026-11-04  proposed  — #720: the first move under #671 settles where a context's tests live
