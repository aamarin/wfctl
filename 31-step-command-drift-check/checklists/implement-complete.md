Implementation complete: 2026-08-17

All 19 tasks executed. Two files changed:

- `wfctl/_pipeline.py` — three step-keyed tables merged into one `_STEPS`;
  `_STEP_NAMES` derived; `next_step_content` reduced to one lookup.
- `tests/test_pipeline_commands.py` — new, 7 tests.

Gates green on both CI interpreters: `pytest` 401 passed (3.11 and 3.13),
`mypy` clean over 11 source files, `ruff check .` clean.

Verified rather than assumed:

- T003/T004 passed against the pre-refactor three-table code before `_STEPS`
  existed, so they test behaviour rather than the structure that replaced it.
- `wfctl status` byte-identical to the T002 baseline; `wfctl next` resolves.
- The negative cases run as tests through `_unresolved`, mutating nothing.
