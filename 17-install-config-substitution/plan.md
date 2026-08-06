# Implementation Plan: install-config substitution

**Branch**: `17-install-config-substitution` | **Date**: 2026-08-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/17-install-config-substitution/spec.md`

## Summary

Make `wfctl install-config workmux` produce a config that needs no hand-editing,
and give already-configured repos a way to catch up.

Three moving parts: the upstream template gains a working teardown hook
(wf-skills#8, not this branch); seeding substitutes the real project name into the
session prefix; and `wfctl doctor` reports a repo whose teardown hook is missing
and offers a two-line fix on confirmation.

Technically this is a new `wfctl/_workmux.py` holding pure `str → str` transforms,
one private-to-public rename in `_paths.py`, and two call sites in `cli.py`. No
new dependency, no YAML parser — line scanning, matching the existing `agent:`
patch at `cli.py:1138`.

## Technical Context

**Language/Version**: Python ≥3.11 (`pyproject.toml:11`)
**Primary Dependencies**: `typer>=0.12`, `rich>=13` — runtime total. Dev: `pytest>=8`,
`ruff>=0.15,<0.16`, `mypy>=1.11,<3`. **This feature adds none.**
**Storage**: Filesystem only. Repo-root `.workmux.yaml`; archives under
`$XDG_STATE_HOME/wfctl/<project>/<branch>/`. No database.
**Testing**: `uv run pytest -q` (269 tests: 227 baseline + 42), `uv run ruff check .`,
`uv run mypy` — the three CI jobs in `.github/workflows/ci.yml`.
**Target Platform**: macOS and Linux CLI, invoked directly and from workmux hooks.
**Project Type**: Single Python package (`wfctl/`), flat module layout.
**Performance Goals**: Not a factor. The health check adds one file read to a
command that already makes network calls; seeding adds one `git rev-parse`.
**Constraints**:
- No new runtime dependency — rules out `ruamel.yaml`, so config edits stay line scans.
- Agent-agnostic — nothing may assume a particular assistant.
- A teardown hook must never strand a worktree, so every archive path exits 0.
- `.workmux.yaml` is repo-owned after seeding; writes to it are narrow and consented.

**Scale/Scope**: Single-user developer tool. Two known consumer repos (`wfctl`,
`pfms`); the retrofit backlog is one file.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

**This repository has no `.specify/memory/constitution.md`.** The template's stock
gates are inherited from an unrelated project (workspace isolation, ZenStack
policy enforcement, `.zmodel` tier placement, `pnpm type-check`) and none of them
have a referent here — this is a Python CLI with no database, no policy layer and
no web tier. Rather than record six vacuous passes, the gates below are the
constraints this repository actually enforces, evidenced from `pyproject.toml`,
`.github/workflows/ci.yml`, and in-repo design comments.

- [x] **No new runtime dependency.** Runtime deps stay `typer` + `rich`.
      `ruamel.yaml` was considered and rejected (spec, Out of Scope).
- [x] **No interface with one implementation.** `_workmux.py` is an internal seam
      like `_paths` / `_tracker` / `_archive`, not a plugin boundary. The
      pluggable worktree adapter is explicitly out of scope.
- [x] **Teardown can never be blocked.** This feature adds no code to the teardown
      path; the retrofit runs inside `doctor`. The hook it writes carries both a
      `command -v` guard and `|| true`.
- [x] **Repo-owned files are written narrowly and with consent.** The retrofit
      replaces one line, only on confirmation, and refuses when the hook has been
      customized.
- [x] **Validation named.** `uv run pytest -q`, `uv run ruff check .`, `uv run mypy`.
- [x] **Complexity justified.** The one new module replaces four would-be
      duplicate parsing sites (seed-time prefix, seed-time agent, health-check
      read, retrofit write) and makes all of them testable without git, network,
      or a temp repo.

**Post-design re-check**: unchanged. Phase 1 added no dependency, no abstraction,
and no new command surface — the retrofit is reachable only through the existing
`doctor` prompt (FR-012b).

## Project Structure

### Documentation (this feature)

```text
specs/17-install-config-substitution/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli.md           # Phase 1 output — command + output contracts
└── checklists/
    └── requirements.md  # From /speckit.specify
```

**No `data-model.md`.** This feature introduces no entities, fields,
relationships, or state transitions — it transforms lines of a text file. An
empty data-model document would be noise. Input/output shapes for the transforms
are specified in `contracts/cli.md` instead.

### Source Code (repository root)

```text
wfctl/
├── _workmux.py          # NEW — pure str→str transforms for .workmux.yaml
├── _paths.py            # _project_name → project_name (public); one caller
├── cli.py               # install-config: substitution; doctor: lint + retrofit
├── _archive.py          # unchanged
├── _tracker.py          # unchanged
├── _pipeline.py         # unchanged
├── _session.py          # unchanged
└── _io.py               # unchanged

tests/
├── test_workmux.py      # NEW — pure unit tests, no fixtures
├── test_paths.py        # + project_name under a real linked worktree
├── test_install_config.py  # + prefix substitution end-to-end
└── test_remaining_commands.py  # + doctor lint, both TTY paths
```

**Structure Decision**: Flat single-package layout, unchanged. `_workmux.py` sits
beside the existing underscore-prefixed internal modules and follows their
convention: focused responsibility, no CLI imports, no `subprocess`. The pattern
mirrors `_archive.py`, extracted from `cli.py` in `e64d047` for the same reason.

**Out-of-repo**: the template edit behind User Story 1 lives in wf-skills
(`.agents/configs/workmux/.workmux.yaml:54`) and is tracked as wf-skills#8. No
file in this repository changes for it.

## Complexity Tracking

No Constitution Check violations. Table omitted.

## Phase 2 note

`/speckit.tasks` will decompose this. The natural ordering is bottom-up:
`_workmux.py` and its unit tests first (they depend on nothing), then
`project_name` plus its worktree test, then the two `cli.py` call sites, then
integration tests. Stories 2 and 3 are independent of each other and can land in
either order.
