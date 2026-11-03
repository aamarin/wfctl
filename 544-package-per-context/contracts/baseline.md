# Contract: `.github/scripts/check_imports.baseline`

Plain text, one entry per line. Blank lines and lines starting with `#` are
ignored. Any other line must match one of two forms, or the check fails and
names the line number.

```text
# Placement: an unmoved module and the package it belongs to.
_session.py session
_paths.py core

# Violation: an import that breaks a rule today.
_pipeline.py -> _session.py
_tracker.py -> _session.py
```

- A placement is `<file> <package>`, where `<file>` is a flat file directly
  under `wfctl/` and `<package>` is a context's package or a shared package.
- A violation is `<file> -> <file>`, using paths relative to `wfctl/`, such as
  `evidence/_status.py -> _session.py` once Evidence has moved.
- Entries are sorted, placements first, so a diff shows one added line per
  addition.

Each move under #671 deletes the placement lines for the modules it moves and
any violation lines it resolves. Adding a line needs `wfctl arch
approve-imports`.
