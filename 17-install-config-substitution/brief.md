# Active feature: install-config substitution (#17)

**Branch**: `17-install-config-substitution` · **Step**: plan complete → `/speckit.tasks`

## What we're building

`wfctl install-config workmux` should seed a config that needs no hand-editing,
and already-configured repos should have a way to catch up.

- **US1 (P1)** — seeded repos archive their specs at worktree teardown.
  **Delivered upstream by wf-skills#8**, not this branch.
- **US2 (P2)** — `wfctl doctor` reports a repo whose teardown hook is missing and
  offers a two-line fix on confirmation. *This branch.*
- **US3 (P3)** — the session prefix carries the real project name. *This branch.*

## Shape

New `wfctl/_workmux.py`: pure `str → str`, imports nothing from `wfctl.*`, no
`subprocess`. Caller resolves values and injects them as keyword arguments.

```python
patch_seed(text, *, agent, project) -> str
tmux_safe(name) -> str
pre_remove_wired(text) -> bool
wire_pre_remove(text) -> str | None      # None = refuse
```

Plus `_paths._project_name` → public `project_name` (rename only, one caller), and
two call sites in `cli.py`.

## Settled decisions — do not relitigate

- **D1** prefix is written **active**, not commented. Unlike `agent:`, which stays
  commented when unresolvable, a project name is derivable.
- **D2** retrofit is prompt-only. No `--fix` flag, no new command.
- **D3** sanitize `[.:]` → `_`; report only when the name actually changed.
- Placeholder check watches for a surviving `<project>`, not for a missing key.
- `doctor` reports `pre_remove` **only** — never the prefix. Cosmetic warnings
  dilute the data-loss one.
- No YAML parser. Line scans, matching `cli.py:1138`.
- `_workmux.py` is an internal seam, **not** a plugin boundary.

## Facts worth not rediscovering

- `pre_remove: []` **disables** workmux's node_modules fast-delete default; it is
  not an empty default.
- tmux silently rewrites `.` and `:` to `_` in session names, then fails to target
  the original — measured. Spaces, `$`, `-`, `_` survive.
- `_project_name` already exists (`_paths.py:194`) with zero test coverage.
- `<agent>` is workmux's own runtime token. Do not substitute it.
- Retrofit blast radius on real pfms config: 326 → 327 lines, one line replaced by
  two, nothing else altered.
- `~/.local/state/wfctl/pfms/` holds 22 branches and 0 archives.

## Verify

`uv run pytest -q` · `uv run ruff check .` · `uv run mypy`

## Artifacts

`specs/17-install-config-substitution/` — spec.md, plan.md, research.md,
quickstart.md, contracts/cli.md, checklists/requirements.md

## Open, not blocking

- File the "skill text drift" sweep in wf-skills (#6, #7, hardcoded `dev` trunk).
- Narrow wfctl#17's description to drop the Part 1 duplication of wf-skills#8.
- wf-skills carries 24 foreign-project references across 8 files, including the
  spec and plan templates this pipeline uses. wf-skills#3 covers one of them.
