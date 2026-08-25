# Implementation Plan: Machine-checked done

**Branch**: `69-machine-checked-done` | **Date**: 2026-08-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/69-machine-checked-done/spec.md`

## Summary

`implement` reports complete when the agent that did the work says so — a
non-empty sentinel file, or every checkbox ticked. This adds a verdict wfctl
produces itself: a repository-level definition of done in a tracked file, a
command that runs it and records the outcome bound to the code it describes, and
a completion check that reads that record instead of the agent's assertion.

Approach: one new tracked config file, one new state file, one new CLI verb, one
new private module, and one branch in the existing step-inference function. That
branch needs no new plumbing — `_pipeline._infer_steps` already receives
`repo_root` and currently ignores it.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer`, `rich` — no new runtime dependency; `json` and
`subprocess` from the stdlib
**Storage**: JSON files. Config at the repository root, tracked. Record in the
XDG state dir beside `current.json` and `events.jsonl`, never tracked.
**Testing**: `uv run --frozen --extra dev pytest -q`, `uv run ruff check wfctl/
tests/`, `uv run mypy wfctl/`; plus `wfctl doctor` for install drift. New tests
land in `tests/test_verify.py`, with the step-inference cases extending
`tests/test_pipeline_commands.py`.
**Target Platform**: developer machines (macOS, Linux) and CI runners; no
network, no hosting provider assumed
**Project Type**: single-package CLI
**Performance Goals**: status executes zero commands from the definition of done and adds two git
queries, independent of how many commands the definition of done holds (SC-002)
**Constraints**: language-agnostic — wfctl never infers a project's commands;
absence of config degrades to current behavior byte-for-byte; commands run as
argument vectors, never through a shell; minimal-complexity bias
**Scale/Scope**: one definition of done per repository; one record per branch per
checkout

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. Gates below are
substituted from `AGENTS.md`, its documented conventions file. The substitution is
recorded in Complexity Tracking.

- [x] **Validation plan exists**: the project's three commands plus `wfctl
      doctor` (`AGENTS.md` § Definition of done), and the per-requirement checks
      named in the spec's Validation Strategy.
- [x] **Complexity is justified**: no new dependency and no new abstraction. One
      config file, one record file, one CLI verb, one private module, one branch
      in an existing function. The module is the only added unit, and the reason
      the simpler path — folding it into `_pipeline.py` — is insufficient is in
      Structure Decision and Complexity Tracking. Three rejected simplifications
      are recorded there.
- [x] **Ownership is stated**: see the spec's Key Entities and `design.md`'s
      Boundaries and Ownership. The command is owned by a human at config time
      because wfctl cannot know a project's language; the verdict and the code
      identity are owned by wfctl because an agent-supplied value of either is
      exactly as forgeable as the assertion being replaced.

**Repository-specific gates**, from `AGENTS.md`:

- [x] **Skills are source, not install output**: the change to the
      implementation step edits `wfctl/agents/skills/speckit-implement/SKILL.md`,
      never `.agents/`. Verified manually with `wfctl install-skills`, because the
      suite checks that skills ship, not that they read well.
- [x] **No drive-by lint expansion**: ruff stays at `E4`, `E7`, `E9`, `F`.
- [x] **Annotate new functions**: mypy runs with `disallow_untyped_defs`.
- [x] **Comments inform the next reader**: rationale for shape, not narration of
      the diff.
- [x] **No version bump**: bumping `version` in `pyproject.toml` on `main` ships
      a release, and this is not a release change.
- [x] **One PR closes one issue**: this closes #69 only.

## Project Structure

### Documentation (this feature)

```text
specs/69-machine-checked-done/
├── design.md            # Pre-specify design pass (four levels, gated)
├── spec.md              # /speckit.specify + /speckit.clarify output
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── wfctl-json.md            # the tracked config file
│   ├── verify-record.md         # the state-dir record
│   └── cli-verify.md            # the `wfctl verify` command surface
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit.tasks output — not created here
```

### Source Code (repository root)

```text
wfctl/
├── _verify.py           # NEW — config load, run, record write/read
├── _pipeline.py         # implement arm gains a verification branch
├── cli.py               # NEW `verify` command; doctor reports a bad config
├── _io.py               # unchanged; write_json_atomic and append_event reused
├── _paths.py            # unchanged; resolve_agent_dir gives the record's home
└── agents/skills/speckit-implement/SKILL.md   # runs verification at step 9c

tests/
├── test_verify.py               # NEW — config, run, record, staleness
└── test_pipeline_commands.py    # extended — the implement arm's new states

README.md                # the "phases can't be faked" claim, corrected
```

**Structure Decision**: single package, flat module layout, matching the existing
`_archive.py` / `_tracker.py` / `_workmux.py` pattern — one private module per
subsystem, imported lazily by `cli.py` inside the command function. `_verify.py`
is a new module rather than an addition to `_pipeline.py` because it shells out
and writes state, while `_pipeline.py` is pure inference over files; merging them
would make step inference untestable without a subprocess.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Gates substituted from `AGENTS.md` rather than a constitution | The repo has none, and the template forbids borrowing another project's | Leaving the gates blank makes the check decorative; `AGENTS.md` is this project's own documented convention set, so the substitution is sourced rather than invented |
| A second identity capture after the run (FR-016) | A multi-minute suite can be invalidated by an edit made while it runs, and one capture cannot distinguish that from a clean run | Capturing once is cheaper and reports a pass for a tree that changed underneath it — the defect this feature exists to remove, one layer down |
| A new module, `_verify.py` | It runs subprocesses and writes state; `_pipeline.py` is pure inference over files | Folding it into `_pipeline.py` makes step inference impossible to test without spawning a subprocess, and `_infer_steps` is the most heavily tested function in the package |
| `wfctl verify` streams child output instead of capturing it | A four-minute suite behind `capture_output=True` is indistinguishable from a hang | The tracker dispatch's buffered pattern suits sub-second commands; reusing it here trades the whole feature's usability for one line of consistency |
