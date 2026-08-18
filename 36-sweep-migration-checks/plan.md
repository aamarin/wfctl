# Implementation Plan: Sweep the one-time migration checks

**Branch**: `36-sweep-migration-checks` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/36-sweep-migration-checks/spec.md`

## Summary

Remove the two health-check reports whose conditions can no longer be created,
correct the bundled teardown-hook template that was re-seeding a retired command
name, and give the two surviving compatibility paths an observable end condition
by having each announce itself when it fires. Net effect: a health check that
reports only live drift, and two shims whose removal becomes a decision on
evidence rather than on a comment nothing reads.

The work is subtractive. No new module, dependency, abstraction, or state is
introduced — the end condition is carried by two print statements on paths that
already run.

## Technical Context

**Language/Version**: Python ≥3.11 (`requires-python = ">=3.11"`)
**Primary Dependencies**: typer ≥0.12, rich ≥13 — both already present; none added
**Storage**: N/A — reads a repo-local `.workmux.yaml` and a JSON manifest; writes no new state
**Testing**: `uv run pytest -q`; `uv run ruff check .`; `uv run mypy`; plus `.github/scripts/check_wheel_contents.py` and `check_installed_tree.py` for the bundled template
**Target Platform**: developer workstations (macOS/Linux), invoked directly and from a `pre_remove` teardown hook
**Project Type**: single-package CLI
**Performance Goals**: no regression; the deletions remove filesystem probes from the health check's startup path and add none
**Constraints**: the archive command must never exit non-zero on anything but a failed rescue of at-risk artifacts, and must never abort a teardown; minimal-complexity bias
**Scale/Scope**: 3 source files, ~120 lines removed, ~10 added; one developer across several machines

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. Gates below are
substituted from its own documented conventions — `pyproject.toml`'s lint and
type configuration, and the commenting and simplification conventions the
codebase applies consistently. The substitution is recorded in Complexity
Tracking.

- [x] Validation plan exists: the project's type or build check plus the specific
      automated tests and checks needed for the changed surface are named.
      → Named in Technical Context and expanded in `quickstart.md`.
- [x] Complexity is justified: any added abstraction, infrastructure, or
      dependency has a measured or explicit reason the simpler path is
      insufficient.
      → Nothing added. The end-condition mechanism is two print statements on
      existing paths; the alternatives (a recorded migration flag, a dedicated
      audit subcommand) were rejected in `design.md` as permanent machinery for a
      temporary problem.
- [x] Lint and type gates stay clean: `ruff` (E4, E7, E9, F) and `mypy` with
      `disallow_untyped_defs`. Deleting a check's sole caller must not leave an
      unreferenced helper, which `F401`/`F811` would catch only for imports —
      so removal is verified by grep as well as by lint.
- [x] No new runtime dependency: the declared set stays `typer` + `rich`.
- [x] Deliberate simplifications carry a `ponytail:` comment naming a stated end
      condition. This feature's entire purpose is to make two such conditions
      observable, so the retained paths' comments must reference the output that
      proves them, not a date or a vague trigger.
- [x] Comments explain why, not what. The deleted checks' docstrings encode real
      reasoning about failure modes; where that reasoning still applies to a
      surviving path, it moves rather than disappears.

## Project Structure

### Documentation (this feature)

```text
specs/36-sweep-migration-checks/
├── design.md            # Brainstorm output (/speckit.brainstorm)
├── spec.md              # Feature spec (/speckit.specify, /speckit.clarify)
├── plan.md              # This file (/speckit.plan)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli.md           # Phase 1 output — command-surface contract
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

Flat single-package layout; no `src/` directory.

```text
wfctl/
├── cli.py                              # command surface + health-check functions
├── _archive.py                         # rescue planning and copying (read stays, untouched)
├── _workmux.py                         # .workmux.yaml parsing helpers
└── agents/configs/workmux/.workmux.yaml  # bundled teardown-hook template

tests/
├── test_remaining_commands.py          # health-check cases
├── test_workmux.py                     # hook-parsing helper cases
├── test_archive_specs.py               # archive command cases
└── test_install_config.py              # seeding cases

.github/scripts/
├── check_wheel_contents.py             # asserts the bundle ships in the wheel
└── check_installed_tree.py             # asserts the bundle lands on install
```

**Structure Decision**: Existing layout, unchanged. Every edit lands in a file
that already exists. The bundled template is a data file inside the package
(vendored by #43/#47), so correcting it is an in-repo edit that ships through the
wheel rather than a cross-repository dependency.

### Change sites

| # | Action | Site | Requirement |
|---|---|---|---|
| 1 | Delete `_check_legacy_agent_dir` and its call | `wfctl/cli.py:1673`, call at `:1887` | FR-001 |
| 2 | Delete `_check_stale_archive_hook` and its call | `wfctl/cli.py:1783`, call at `:1885` | FR-003 |
| 3 | Delete `pre_remove_uses_former_name` | `wfctl/_workmux.py:159` — sole caller was #2 | FR-005 |
| 4 | Keep `_check_spec_root_migration`; restate its docstring as recurring drift | `wfctl/cli.py:1819` | FR-002 |
| 5 | Keep `_check_workmux_hook` unchanged | `wfctl/cli.py:1714` | FR-004 |
| 6 | Retarget the bundled hook and its comment | `wfctl/agents/configs/workmux/.workmux.yaml:55,65` | FR-013 |
| 7 | Report the legacy rescue count | `wfctl/cli.py` archive command, after `_archive.archive` returns | FR-007, FR-008 |
| 8 | Report invocation under the retired name | `wfctl/cli.py:299` command signature + body | FR-010, FR-011 |
| 9 | Restate both retained paths' `ponytail:` comments in terms of emitted output | `wfctl/cli.py:299`, `wfctl/_archive.py:188` | FR-014 |
| 10 | Remove obsolete tests; add tests for the two new reports | `tests/test_workmux.py:225-249`, `tests/test_remaining_commands.py`, `tests/test_archive_specs.py` | FR-015 |

`wfctl/_archive.py`'s rescue logic (`:189`) is not modified — only its comment
(#9). The count for #7 is derived in `cli.py` from the returned `mapped` list, so
`_archive.py` continues to return data and own no console.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --------- | ---------- | ------------------------------------ |
| Constitution gates substituted from repo conventions rather than a constitution file | `.specify/memory/constitution.md` does not exist in this repository | A gate with no source is decorative, and borrowing another project's gates would be false. Substituted gates are drawn from `pyproject.toml`'s enforced lint/type settings and from conventions the codebase applies consistently. |
| Two compatibility paths retained rather than deleted, against issue #36's stated one-pass intent | Deleting them destroys a rescued file or produces a silently empty archive on any machine that predates the moves | One-pass deletion was rejected in `design.md`: the five checks' failure modes differ, and uniform treatment trades a real data-loss risk for a cosmetically shorter diff. Their removal is deferred to a follow-up with an observable trigger. |
