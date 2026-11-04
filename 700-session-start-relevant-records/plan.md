# Implementation Plan: Session start loads the records for the branch's contexts

**Branch**: `700-session-start-relevant-records` | **Date**: 2026-11-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/Users/andremarin/Development/wfctl-specs/700-session-start-relevant-records/spec.md`

## Summary

`wfctl arch context` prints only the accepted records that apply to the
contexts the branch lists in `design.md`, plus every record with no `governs`
field. It prints every accepted record whenever it can't tell which ones apply,
and `--all` prints every one on request. The session report's `Records` line
gives the same counts, and `status --json --session` gains `applying_records`.

One pure function, `_contexts.select`, holds the rule. One gathering function,
`_evidence.records_for_branch`, reads the name list, the branch's `Contexts`
line, and the accepted records, and calls it. `arch context` and the session
report both call `records_for_branch`
(`docs/architecture/design/700-one-function-selects-records.md`).

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `typer`, `rich`, no new ones  
**Storage**: files only; reads the domain page, `design.md`, and the records  
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `uv run python .github/scripts/check_imports.py`  
**Target Platform**: macOS and Linux shells where agents run  
**Project Type**: CLI  
**Performance Goals**: no new git or tracker call; the selection reads three kinds of file that `arch context` and the design checks already read  
**Constraints**: no new import-baseline line; `cli.py` changes stay inside `arch_context_cmd` (#711 edits `review start` in the same file); minimal-complexity bias  
**Scale/Scope**: 28 accepted records today, 5 with a `governs` field

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repository has no `.specify/memory/constitution.md`. The gates below come
from `AGENTS.md` and the accepted records, and Complexity Tracking records the
substitution.

- [x] Validation plan exists: the three commands in `AGENTS.md`'s Definition of
      done, the import check, a test per acceptance scenario, and the by-hand
      check in `quickstart.md`.
- [x] Complexity is justified: two functions and one `NamedTuple`. The level-3
      record gives the reason the baseline of two copies loses.
- [x] Ownership is stated: wfctl computes which records apply, from the
      branch's `Contexts` line and each record's `governs` field. The agent
      shouldn't choose, since it would be deciding which rules bind its own
      work (`docs/architecture/branch-contexts-select-records.md`).
- [x] `contexts-are-packages`: the session report reaches the selection
      through `_evidence`, following the map's `EV --> SC` arrow, and
      `_evidence` reaches `_contexts` through `AR --> EV`.
- [x] `change-carries-release-note`: `changes/700.change.md`.
- [x] `vendor-upstream-skills`: the skill edits are to `start-session` and
      `architecture-decisions`, both wfctl's own.
- [x] `session-state-is-re-derived`: the selection is computed on every read
      and stored nowhere.

Re-checked after Phase 1: all still hold.

## Project Structure

### Documentation (this feature)

```text
700-session-start-relevant-records/
├── design.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli.md
└── tasks.md             # /speckit.tasks
```

### Source Code (repository root)

```text
wfctl/
├── _contexts.py          # Selection, select()
├── _evidence.py          # records_for_branch()
├── _session_report.py    # Readers.records, Records line, applying_records key
├── cli.py                # arch_context_cmd only: --all, header, footer lines
└── agents/skills/
    ├── start-session/SKILL.md            # step 2, step 7
    └── architecture-decisions/SKILL.md   # governs left out for every change

tests/
├── test_contexts.py           # select()
├── test_evidence.py           # records_for_branch()
├── test_remaining_commands.py # arch context output
├── test_session_report.py     # Records line, applying_records
└── test_cli_status.py         # session JSON key set, arch context vs status --session --json

.github/scripts/check_imports.baseline   # drop `_session_report.py -> _arch.py`
changes/700.change.md
```

**Structure Decision**: single project. The rule sits in `_contexts`, which
already holds the name-list and `Contexts` line readers and never calls git.
The gathering sits in `_evidence` beside `context_gap`, which has the same
shape for the design checks.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| No constitution; gates taken from `AGENTS.md` and the accepted records | the repo has no `.specify/memory/constitution.md` | an empty Constitution Check would gate nothing |
