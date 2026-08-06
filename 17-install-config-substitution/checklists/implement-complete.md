Implementation complete: 2026-08-03

25 of 30 tasks done. All automated work is finished and green:
`uv run pytest -q` → 265 passed (227 baseline + 38 new) · `uv run ruff check .` →
clean · `uv run mypy` → clean (9 source files).

Five tasks remain open, none of them code:

- **T006, T007, T008** (US1) — blocked on `aamarin/wf-skills#8`. The template edit
  lives in another repository and has not landed; verification cannot run until it
  does.
- **T016** (US2) — runs `wfctl doctor` against `~/Development/pfms` and writes to
  that repo's committed `.workmux.yaml`. Left for the operator to invoke
  deliberately.
- **T025** (US3) — seeds from inside a linked worktree of a scratch repo.

The behavior T016 and T025 cover was smoke-tested against a throwaway repo during
implementation (both TTY paths, the applied patch, and the refusal path), but the
tasks as written target real repositories and are not marked done.
