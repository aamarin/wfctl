Implementation complete: 2026-08-06

Feature: `11-gitignore-glob-dedup` (issue #11)
Tasks: 29/29 complete (T001–T029)
Commits: `17ea7ba` (fix + tests), `2c88daf` (the one .gitignore entry it produced)

## Gates

| Gate | Result |
| --- | --- |
| `uv run pytest -q` | 289 passed (baseline 279 + 10 new) |
| `uv run ruff check .` | All checks passed |
| `uv run --extra dev mypy` | no issues in 9 source files |

## Measured outcomes

| Criterion | Target | Actual |
| --- | --- | --- |
| SC-001 entries written on a covered repo | 1 | **1** (`.wf-skills-backup/`) |
| SC-003 second install byte-identical | yes | **yes** — 0 written, 84 skipped |
| SC-006 coverage-check cost | ≤1500 ms | **613 ms** (7.3 ms/path × 84) |
| SC-007 skipped + written = considered | 84 | **83 + 1 = 84** |

Before: an install appended 83 lines. After: 1, then 0.

## Verified, not assumed

- `--no-index` was removed from the guard and
  `test_install_skills_skips_tracked_path_covered_by_pattern` failed, then
  passed once restored. The flag is defended by a test, not only by a comment.
- `tests/test_install_config.py` is byte-for-byte unedited (`git diff` empty),
  which was T014's tripwire for the guard having changed something it should
  not have.
- The `wt/` call site at `cli.py:1169` is absent from the diff — only two hunks
  in `cli.py`, the function and the install call site.
