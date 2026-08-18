# Implementation Plan: doctor exit-code contract

**Branch**: `41-doctor-exit-code-contract` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `41-doctor-exit-code-contract/spec.md` in the recorded spec root

## Summary

`doctor` runs five health checks under three different exit-code conventions, so
it reports problems and exits 0 — fine for a person reading output, wrong in CI.
This replaces the three conventions with one: each check returns `bool` meaning
"found drift", OR'd into the exit code, with "could not determine" returning
`False` so a flaky network never fails a build.

On that foundation, one check is deleted (its removal condition now met), one new
check is added to `doctor`, and one new check is added to the test suite. A bug
the vendoring introduced — the shipped workmux template naming a superseded
command — is fixed first, because it would otherwise make every freshly
configured repository fail the new contract.

## Technical Context

**Language/Version**: Python ≥3.11 (CI matrix: 3.11, 3.13)
**Primary Dependencies**: typer, rich. No new runtime dependency — the
nearest-match suggestion in FR-012 uses `difflib` from the standard library.
**Storage**: `.wf-skills-manifest.json` per repository; no database
**Testing**: `uv run pytest -q`; `uv run ruff check .`; `uv run mypy`. Baseline
before this work: 395 passing, ruff clean, mypy clean over 11 source files.
**Target Platform**: developer machines (macOS, Linux) and CI runners; a terminal
CLI invoked directly and from `/start-session`
**Project Type**: single Python package with a console entry point
**Performance Goals**: none specific. `doctor` already performs a network lookup;
a directory walk over tens of recorded entries is not a measurable addition.
**Constraints**: every test must pass offline (SC-006); `_check_wfctl_version`
must not be modified (FR-013); minimal-complexity bias
**Scale/Scope**: one repository at a time; ~56 recorded install entries and 8
pipeline steps in the reference repository

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. Gates below are
substituted from its own documented conventions — `pyproject.toml`, whose
comments state the rationale for each tool setting, and `.github/workflows/ci.yml`,
which is what actually blocks a merge. The substitution is recorded in Complexity
Tracking.

- [x] **Validation plan exists**: `uv run pytest -q` on 3.11 and 3.13,
      `uv run ruff check .`, `uv run mypy`, plus the wheel job. Feature-specific
      tests named per user story in [quickstart.md](./quickstart.md).
- [x] **Complexity is justified**: no new abstraction, module, or dependency. The
      contract is a return-type change on three functions; the two new checks are
      one function each. Explicitly rejected: a check registry (see
      Complexity Tracking).
- [x] **No new runtime dependency**: `pyproject.toml` carries typer and rich only.
      FR-012's nearest-match uses stdlib `difflib`.
- [x] **Type annotations on every function**: `disallow_untyped_defs = true`. The
      three converted checks gain `-> bool`; both new checks are annotated.
- [x] **Lint stays clean under the pinned rule set**: ruff `E4, E7, E9, F`, pinned
      `>=0.15,<0.16`.
- [x] **Tests run offline**: the autouse fixture in `tests/conftest.py` stubs the
      only network call. No test added here may reintroduce one.
- [x] **Deliberate shortcuts carry a stated removal condition**: the repository
      marks these with a `ponytail:` comment naming the trigger. Applies to
      anything left partial here.

_Post-Phase 1 re-check_: all gates still pass. Phase 1 added no module, no
dependency, and no abstraction — see [data-model.md](./data-model.md), which
describes states rather than new types.

## Project Structure

### Documentation (this feature)

```text
41-doctor-exit-code-contract/          # in the recorded spec root, not in-repo
├── design.md            # /speckit.brainstorm output
├── spec.md              # /speckit.specify + /speckit.clarify output
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── doctor-exit-code.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit.tasks output — not created here
```

### Source Code (repository root)

```text
wfctl/
├── cli.py               # doctor_cmd and all five checks; the whole change surface
├── _pipeline.py         # _STEP_COMMAND, the table Story 4 verifies
├── _workmux.py          # pre_remove_wired / pre_remove_uses_former_name
├── _bundle.py           # BUNDLE_ROOT, content_hash
├── _manifest.py         # load/save of the install record
└── agents/
    └── configs/workmux/.workmux.yaml   # the shipped template Story 2 corrects

tests/
├── conftest.py          # autouse stub keeping the suite offline
├── test_bundle.py       # bundle-content assertions, incl. Story 2's regression
├── test_install_skills.py   # existing doctor tests, incl. the one to rewrite
└── test_pipeline_commands.py  # new — Story 4
```

**Structure Decision**: A flat single-package layout, unchanged by this work. The
repository has no `src/` directory and no per-layer subpackages; modules are
prefixed `_` for internal and live directly under `wfctl/`. All behaviour changes
land in `cli.py`, which already holds `doctor_cmd` and every check. No new module
is created — see Complexity Tracking for why the two new checks do not warrant
one.

## Implementation Order

Dependency-ordered. Items 1–3 must land in sequence, and item 4 needs the
contract from item 3. Item 5 depends on nothing and can be done at any point —
it adds a test file and touches no production code.

1. **Correct the shipped workmux template** (Story 2) — `wfctl/agents/configs/`.
   Blocks item 2: while wfctl ships a template naming the superseded command, the
   check in item 2 has a live consumer and cannot be deleted. *Already applied on
   this branch, with its regression test.*
2. **Delete `_check_stale_archive_hook`** and its call site. Settles the set of
   checks before the contract is written against it.
3. **The contract** (Story 1) — convert the three remaining `_check_*(repo_root)`
   functions to `-> bool`, OR into `exit_code`, and state the
   could-not-determine rule where the convention is defined. Rewrite the existing
   test that asserts the superseded convention.
4. **The abandoned-entry check** (Story 3) — new function in `cli.py`, adopting
   the contract from item 3.
5. **The step-command test** (Story 4) — `tests/test_pipeline_commands.py`. Touches
   no production code.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Gates substituted from `pyproject.toml` and CI rather than a constitution | The repo has no `.specify/memory/constitution.md`, and the template requires a real source — a gate with no source is decorative | Inventing gates, or copying another project's, would assert conventions this repo has not adopted. `pyproject.toml` states rationale in comments for each setting and CI is what actually blocks a merge, so both are documented and enforced. |

**Considered and rejected — no violation, recorded so it is not re-proposed:**

- **A check registry** (list, `Protocol`, or decorator over the checks). Four
  calls in a row in `doctor_cmd` is the right amount of structure. A registry buys
  nothing until something needs to iterate over checks, and nothing does.
- **A new module for the two new checks.** `cli.py` is large, but every check and
  `doctor_cmd` itself already live there. Extracting two of seven would split one
  concept across two files and leave the caller importing back.
- **A severity tier** (`⚠` exits 0, `✗` exits 1). Rejected during design: it
  preserves the defect the feature exists to fix. The could-not-determine outcome
  covers the real case a tier was reaching for.
- **Removing abandoned entries rather than reporting them.** Correct for a genuine
  rename, destructive when the file was edited locally or its layer was
  intentionally deselected. FR-010 fixes reporting as the behaviour; a removal flag
  can follow if reports go unactioned.
