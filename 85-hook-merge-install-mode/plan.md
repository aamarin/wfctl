# Implementation Plan: A merge install mode for hooks in a consumer-owned settings file

**Branch**: `85-hook-merge-install-mode` | **Date**: 2026-09-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/85-hook-merge-install-mode/spec.md`

## Summary

Add a third install mode, `merge`, to `wfctl install-skills --agent claude`: it
writes one self-identifying `UserPromptSubmit` hook entry into the consumer's
`.claude/settings.json` (command `wfctl hook user-prompt`) and touches nothing
else in that file. The command it installs reads every installed skill's sibling
`digest.md` at call time and prints whatever it finds, so the hook's content
tracks the installed tree without the settings file recording which skills are
covered. `uninstall-skills` removes only entries matching that command; `doctor`
reports when the entry is missing or no longer matches what the current wfctl
would install.

## Technical Context

**Language/Version**: Python 3.11+ (repo floor; no feature needs a newer one)
**Primary Dependencies**: `typer`, `rich` — both already runtime deps; no new
dependency. JSON parsing is stdlib `json`.
**Storage**: The consumer's `.claude/settings.json` (JSON, consumer-owned, never
gitignored) plus the existing `.wf-skills-manifest.json` (a new `merged` list per
agent, sibling to `items`).
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy
wfctl/` — the project's standing definition of done. Feature-specific: a
dict-literal unit suite for the merge/unmerge functions (no repo, no fixtures —
`test_settings_merge.py`'s pattern), a filesystem round-trip suite through
`install-skills`/`uninstall-skills --agent claude`, and a `doctor` suite per
reported state (current / missing / behind).
**Target Platform**: Wherever wfctl runs today — a CLI installed via `uv tool
install` or `pip`, invoked in a git repo.
**Project Type**: Single project, CLI (`wfctl/`, flat modules, no
src-layout split).
**Performance Goals**: None beyond "a JSON file measured in KB parses and writes
without perceptible delay" — no target worth stating for a file this size.
**Constraints**: `wfctl arch context` in force: `install-modes` (this feature's
third value), `no-hardcoded-agent` (the entry never names an agent — its file
location already scopes it), `vendor-upstream-skills` (a vendored skill's digest
ships as a sibling `digest.md`, never an edit to the skill), `layer-model`
(generated paths stay gitignored — `.claude/settings.json` explicitly does not,
per FR-013). Plus minimal-complexity bias.
**Scale/Scope**: One consumer file, one event (`UserPromptSubmit`), one agent
(`claude`) in this scope — per spec Assumptions, global settings, other events,
and other agents are out of scope.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

No `.specify/memory/constitution.md` exists in this repo. Substituted below with
this repo's own documented conventions — `wfctl arch context` (the accepted
architecture records) and `AGENTS.md` — recorded here rather than silently, per
the template's own instruction that an unrecorded substitution is a gate with no
source.

- [x] Validation plan exists: `uv run pytest -q` / `ruff check` / `mypy` plus the
      feature-specific suites named in Technical Context > Testing.
- [x] Complexity is justified: the third mode is not an added abstraction for its
      own sake — `install-modes` already documents why neither existing mode
      (managed mirror, seed-once) can reach a file the consumer owns without
      destroying or freezing it. See that record's Considered section.
- [x] Ownership is stated: `install-modes`' Owns truth section states it per
      mode; this feature's slice — consumer owns the file, wfctl owns entries
      whose command carries its prefix, the skill owns the injected text — is
      restated in `spec.md`'s Key Entities.

## Project Structure

### Documentation (this feature)

```text
specs/85-hook-merge-install-mode/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── contracts/
│   └── hook-command.md   # Phase 1 output — the `wfctl hook user-prompt` contract
└── tasks.md              # Phase 2 output (/speckit.tasks — not this command)
```

### Source Code (repository root)

**Structure Decision**: Single project. wfctl is a flat-module CLI (`wfctl/*.py`,
no `src/` layout, no service split) — this feature adds one new module and
extends three existing ones, following the shape `_workmux.py` /
`_tracker.py` already set for a domain concern kept out of `cli.py`.

```text
wfctl/
├── cli.py            # install_skills_cmd, uninstall_skills_cmd, doctor_cmd,
│                      # new `hook` command — all extended, not replaced
├── _settings.py       # NEW — pure JSON-merge functions over an already-parsed
│                      # settings dict; no I/O, no wfctl.* imports (matches the
│                      # constraint _workmux.py already holds)
└── _manifest.py       # unchanged — `merged` is a new key inside an existing
                        # per-layer dict, not a schema change to this module

tests/
├── test_settings_merge.py       # NEW — dict-literal unit suite for _settings.py
├── test_install_hook_merge.py   # NEW — filesystem round-trip through the CLI
└── test_skill_cross_references.py  # extended — digest.md discovery
```

## Complexity Tracking

No Constitution Check violations. Table omitted per template instruction (fill
only on a violation).

## Post-Design Constitution Check

Re-checked after Phase 1 (`data-model.md`, `contracts/hook-command.md`,
`quickstart.md`). Unchanged from the pre-design check: no new dependency, no new
abstraction beyond the one entity (`_settings.py`) that the pre-design check
already justified against `install-modes`, and ownership is now stated three
times over — once per entity in `data-model.md`, matching `spec.md`'s Key
Entities and `install-modes`' Owns truth section. All three gates still pass.
