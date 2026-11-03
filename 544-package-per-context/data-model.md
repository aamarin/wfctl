# Data model: Check imports against the Context Map

Everything here lives inside `check_imports.py` except the baseline file and
the note line. Nothing is cached, and every run re-reads the domain page, the
baseline, the source, and the notes.

## Domain

Read from `docs/architecture/domain/wfctl.md`.

- `contexts: dict[str, str]`: context name to package, from the Bounded Contexts
  table. Seven entries today.
- `shared: set[str]`: `core` and `tracker`, from the Shared packages table.
- `arrows: set[tuple[str, str]]`: (upstream context, downstream context), one
  per edge between two contexts, keyed by context name so a package rename
  doesn't change them. The rule check maps each name to its package through
  `contexts`. Edges touching a node labelled `(outside)` are
  dropped. Six entries today.

Rule: a package name appears once across `contexts` and `shared`.

When read from the merge base for the approval check, a row with no Package
column reads as a context with no package, and a missing Shared packages table
reads as an empty `shared`.

- `WIRING: tuple[str, ...]`: a constant in the script, `("cli.py", "_entry.py")`.
  The approval check never reads it. It compares the script's blob hash at the
  merge base and at `HEAD`, so a change to `WIRING` is a change to the script.
- `TRUSTED: tuple[str, ...]`: a constant in the script listing the two files
  CI runs the check with: the script and `.github/workflows/review.yml`. The
  approval check compares each one's blob hash at the merge base and at
  `HEAD`, and a file absent at the merge base counts as changed.

## Baseline

Read from `.github/scripts/check_imports.baseline`. Format in
`contracts/baseline.md`.

- `Placement(module, package, line)`: an unmoved flat module and the context or
  shared package it belongs to.
- `Violation(src, dst, line)`: a pair of modules whose import breaks a rule
  today.

Rules:

1. A placement names a package in `contexts` or `shared`.
2. A module has at most one placement.
3. A placement for a module that sits in a package, or no longer exists, is
   stale.
4. A violation that matches no failing import is stale.

## Import

- `Import(src, dst, line)`: one per import statement, or attribute access on a
  bound module, that reaches a wfctl module. `src` and `dst` are dotted module
  names, such as `wfctl._pipeline` or `wfctl.evidence._status`.

## Failure

- `Failure(kind, src, dst, line, contexts, action)`: `kind` is one of `no-arrow`,
  `internal-module`, `shared-imports-context`, `unplaced-module`,
  `stale-placement`, `stale-violation`, `reserved-name`, `unreadable-domain`,
  `unapproved-addition`.

## Approval

- The note line `imports approved <digest>` under `refs/notes/wfctl-review`, on
  any commit between the merge base and HEAD.
- `digest`: the first 12 hex characters of SHA-256 over the added lines, sorted
  and joined by newlines. An added arrow is written as `arrow <up> --> <down>`,
  an added shared package as `shared <name>`, an added context-to-package pair
  as `package <context> <package>`, and a changed trusted file as `changed
  <path> <full blob hash>` or `deleted <path>` in that input, so the five
  kinds can't collide. Only `main`'s
  copy of the script computes it.

State: an addition is unapproved until a note carrying its digest exists. Any
change to the set of additions produces a new digest, so an earlier approval
stops matching.
