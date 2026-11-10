# Implementation Plan: issue edit verb

**Branch**: `445-issue-edit-verb` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from the `spec.md` in this spec folder

## Summary

`wfctl issue edit <id>` changes an issue's title, its body, or both, through the
tracker backend. The backend declares one `edit` verb taking `{id}`, `{field}`,
and `{value}`, and wfctl calls it once for each field given, title first. Each
successful call is recorded as `issue-edit`.

The design record `docs/architecture/design/issue-edit-one-field-per-call.md`
explains why the verb takes a field name and a value, and why optional
placeholders and two separate verbs lost. This plan builds that decision and
the two clarify answers: a missing verb or tracker prints its notice once, and a
failed title write says the body was not sent.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `typer` and `rich`, already in use. No new dependency.  
**Storage**: the session's event log in the XDG state directory, through the
existing `record_outward_action`. No new storage.  
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run
mypy`, then `uv run wfctl install-skills --tracker github`, `uv run wfctl
tracker-check`, and one real edit against a GitHub issue.  
**Target Platform**: macOS and Linux shells, wherever wfctl runs.  
**Project Type**: CLI  
**Performance Goals**: none beyond the existing verbs. Each field is one
tracker call.  
**Constraints**: minimal-complexity bias. The config format for every backend
stays as it is, apart from one new verb name.  
**Scale/Scope**: one verb, two fields, the GitHub backend, and the
`scaffold-tracker` skill.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repo has no `.specify/memory/constitution.md`. The gates below come from
`AGENTS.md` and the accepted records instead, as recorded in Complexity
Tracking.

- [x] Validation plan exists: the three definition-of-done commands, the new
      tests listed under Project Structure, `tracker-check` after a tracker
      reinstall, and one real edit with its `issue-edit` record checked.
- [x] Complexity is justified: no new abstraction. `dispatch` is split into two
      helpers, so the edit can check the tracker once and then run and record
      one write per field; see Research 2 and 3.
- [x] Ownership is stated: the tracker makes the write, and wfctl records it
      and reports which field landed. Both contexts recorded that no boundary
      moves (`wfctl arch none`), and the reason for each split is in
      `design.md` under Boundaries and Ownership.
- [x] `change-carries-release-note`: `changes/445.addition.md`.
- [x] `contexts-are-packages`: the change stays in `wfctl/_tracker.py`,
      `wfctl/cli.py`, and package data. No new import between contexts, so
      `check_imports.py` has nothing new to approve.
- [x] `layer-model`: `github.json` and `scaffold-tracker/SKILL.md` are edited
      under `wfctl/agents/`, never under `.agents/`.
- [x] `a-rule-is-expressed-as-a-check`: the existing test that compares the
      `scaffold-tracker` verb table against `ALLOWED` covers the new row.

## Project Structure

### Documentation (this feature)

```text
<spec folder>/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── cli.md           # the wfctl issue edit command
│   └── tracker-verb.md  # the edit entry in a tracker config
└── tasks.md             # Phase 2 (/speckit.tasks)
```

### Source Code (repository root)

```text
wfctl/
├── _tracker.py                  # ALLOWED gains edit; _RECORDED_VERBS gains edit;
│                                # dispatch splits into a helper that checks the
│                                # tracker and one that runs and records a write;
│                                # a new function runs one edit per field
├── cli.py                       # issue_cmd routes edit, checks id and fields, help text
└── agents/
    ├── trackers/github.json     # "edit": ["gh","issue","edit","{id}","--{field}","{value}"]
    └── skills/scaffold-tracker/SKILL.md   # a row for edit, and the script note

tests/
├── test_tracker.py                      # config validation for edit; dispatch cases
└── test_tracker_records_issue_verbs.py  # issue-edit recorded once per successful field

changes/445.addition.md
```

**Structure Decision**: the change lives where every other `wfctl issue` verb
lives. Orchestrating the per-field calls goes in `_tracker.py`, beside
`dispatch`, because only that module knows whether a write succeeded and
records it. `cli.py` keeps to argument checks and routing, as it does for the
other verbs.

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| Gates taken from `AGENTS.md` and accepted records, not a constitution | This repo has no constitution file | A gate with no source is decorative |
| `dispatch` split into two helpers: one resolves the tracker and prints its notice, the other runs and records a write | The edit has to check the tracker once before any write (clarify Q1), and record each write where success is known (Research 3) | Calling `dispatch` per field prints the notice once per field, which is the output clarify ruled out. Recording in the edit function would add a second place that decides success |
