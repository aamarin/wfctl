# Implementation Plan: step-command drift check

**Branch**: `31-step-command-drift-check` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/31-step-command-drift-check/spec.md`

## Summary

`_pipeline.py` maps each pipeline step to the slash command that advances it, and
nothing verifies those commands exist. The table can name a command that was
renamed or never shipped; the first symptom is a session told to run something
that answers to nothing — which happened once already (#23) and took a week to
notice by eye.

Two changes. The three step-keyed tables (`_STEP_NAMES`, `_STEP_COMMAND`,
`_STEP_AUTO`) merge into one, so a step cannot be defined without both its command
and its automation flag. Then one test asserts the remaining thing a data
structure cannot guarantee: that each step's command exists as a shipped file.

The check is a plain unit test rather than a `doctor` lint — the option the issue
favoured — because the premise it rested on expired. wf-skills was vendored into
the package in `271bb2c` and archived upstream, so both sides now live in one
repo at one commit and CI can see them. The runtime direction the lint was meant
to cover is already reported by `doctor`'s content-hash check.

## Technical Context

**Language/Version**: Python 3.11 and 3.13 (the CI matrix)
**Primary Dependencies**: none added. `pathlib` and the existing test suite.
**Storage**: N/A
**Testing**: `uv run pytest -q`; `uv run ruff check .`; `uv run mypy`
**Target Platform**: the wfctl package, wherever installed — the check reads the
tree shipped inside it, so it holds for a wheel install as well as a checkout
**Project Type**: single-package CLI
**Performance Goals**: no measurable addition to suite runtime; no network, no
subprocess, no filesystem writes — a check that becomes slow or flaky gets skipped
**Constraints**: the assertion must read the real shipped tree despite an autouse
fixture repointing the bundle path; the restructure must be behaviour-preserving
**Scale/Scope**: 8 pipeline steps, 23 shipped commands, 2 files touched

No unresolved unknowns. The two open at Phase 0 — whether similarity scoring can
attribute the drift, and how to reach the shipped tree — are settled in
`research.md` R1 and R2.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repo has no `.specify/memory/constitution.md`. Gates below are substituted
from its own documented conventions — `.github/workflows/ci.yml` and
`.github/pull_request_template.md` — and the substitution is recorded in
Complexity Tracking, since a gate with no source is decorative.

- [x] Validation plan exists: `pytest`, `ruff`, `mypy` named, plus the
      feature-specific negative case (rename a shipped command, confirm the check
      fails) and the behaviour-preservation check on the merged table.
- [x] Complexity is justified: no abstraction, infrastructure or dependency
      added. The feature removes two structures and adds one test.
- [x] Tests prove the change (PR template: "I have added tests that prove my fix
      is effective"). The check is itself the test; the restructure is covered by
      asserting all eight steps resolve to today's values.
- [x] No new warnings or errors (PR template). `ruff` and `mypy` unchanged.
- [x] Hard-to-understand areas commented (PR template). Two need it: why the
      check bypasses `_bundle.BUNDLE_ROOT`, and why an unknown step must return
      an empty command rather than raise.

**Post-Phase 1 re-check**: unchanged. The design added no dependency, no module
and no abstraction; `data-model.md` describes one dict replacing three, and
`quickstart.md` fits the whole diff on one screen.

## Project Structure

### Documentation (this feature)

```text
specs/31-step-command-drift-check/
├── design.md            # /speckit.brainstorm output (partly superseded — see spec Assumptions)
├── spec.md              # /speckit.specify output
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── checklists/
│   └── requirements.md  # spec quality checklist
└── tasks.md             # /speckit.tasks output — not created here
```

### Source Code (repository root)

```text
wfctl/
├── _pipeline.py         # MODIFIED: three step-keyed tables → one; next_step_content
└── agents/commands/     # unchanged; the authority the check reads

tests/
├── conftest.py          # unchanged; its autouse `bundle` fixture constrains the check
└── test_pipeline_commands.py   # NEW: the drift check
```

**Structure Decision**: single package, existing layout, no new directories. The
test lands beside the suite's other module-scoped tests and is named for the
module it guards, matching `test_paths.py` and `test_workmux.py`.

No `contracts/` directory. The feature exposes no new interface — `wfctl status`,
`wfctl next` and `wfctl resume` keep their exact output, which is the acceptance
bar for the restructure rather than a new contract to document.

## Phase 0: Research

Complete — see [research.md](./research.md).

- **R1**: similarity scoring cannot attribute the drift. Measured on five cases;
  the default cutoff is wrong on three, twice naming an innocent file where
  nothing was renamed. Raising the cutoff drops the #23-shaped renames first.
  Decision: show both sides, nominate nothing. FR-004 amended accordingly.
- **R2**: the check reads `Path(wfctl.__file__).parent / "agents" / "commands"`.
  `_bundle.BUNDLE_ROOT` is repointed by an autouse fixture and yields one fake
  command. Verified by probe.
- **R3**: the merged table changes no observable behaviour. Seven references, one
  file, no test or module outside it; insertion order is guaranteed on both CI
  interpreters; the `("", False)` fallback for an unknown step is preserved
  because a finished pipeline depends on it.

## Phase 1: Design

Complete — see [data-model.md](./data-model.md) and [quickstart.md](./quickstart.md).

- **data-model.md**: the merged step definition table, its eight values as they
  must remain, and the shipped command set with its 8-of-23 relationship.
- **quickstart.md**: the concrete diff for both files, the verification commands,
  and the three regressions to watch for.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from CI config and the PR template | Repo has no `.specify/memory/constitution.md`; the template requires the substitution be recorded rather than left implicit | Borrowing another project's gates would assert standards this repo never adopted; omitting them would leave the gate decorative |
| Feature includes a production change, where the approved design said test-only | The three parallel tables permit two drift shapes worse than the one filed — one prints "story complete" mid-pipeline. Merging removes both; asserting they agree only detects them | Keeping three tables plus an agreement assertion is more code guarding a structure that should not exist. Measured cost of the merge: 7 lines, 1 file, 0 external references |
