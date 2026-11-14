# Implementation Plan: Move the old review scans into their spec folders

**Branch**: `759-move-old-scans` | **Date**: 2026-11-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `spec.md` in this folder, and `design.md` beside it.

## Summary

A new command, `wfctl store scans`, moves the review scans committed under
`<arch-root>/scans/` into each feature's spec folder as `scans/<step>.md`. It
stores each folder it wrote to with the same `store` function `wfctl store
specs` uses, and deletes a scan from the code repository only after its folder
is stored.

The command runs in four phases. It finds the review scans, places each one in
a folder, writes the scans into their folders, and then stores each folder and
deletes its scans. Placement and writing are pure functions over the file
system, so each acceptance scenario can be tested without a remote. Only the
last phase calls git.

The folder comes from the scan's `Detail` line first. The command takes the
first path segment that starts with an issue key and a hyphen, and falls back
to the one folder whose name starts with the scan's issue number
(`759-scan-names-its-folder`, and the spec's Clarifications). Scans are handled
in ascending issue-number order, so a re-review appends after the review it
follows.

A scan is deleted only when its own write succeeded and its folder is stored,
so a conflicted scan stays even when the rest of its folder moves (research
R6). A rerun after a failed store finds the files it already wrote and stores
them again (R5). The first failed store stops storing for the rest of the run,
since an unreachable remote or a stuck merge would fail every folder after it
the same way (FR-014, R8). Each push is
recorded in the session's event log (R9).

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `typer` and `rich`, which wfctl already uses. Nothing new.
**Storage**: Files only. The scans move from the code repository's working tree
to the spec store, a git repository wfctl already commits to and pushes from.
**Testing**: `uv run pytest -q`, with a new `tests/test_store_scans.py`. Its
git tests build a temporary code repository and a spec store cloned from a bare
remote under `tmp_path`, the way `tests/test_spec_store.py` does, so conftest's
remote guard covers them. Also `uv run ruff check wfctl/ tests/`, `uv run
mypy`, and `python3 .github/scripts/check_imports.py`.
**Target Platform**: macOS and Linux, the same as `wfctl store specs`, whose
lock uses `fcntl`.
**Project Type**: CLI
**Performance Goals**: Storing wfctl's 45 folders finishes in a few minutes.
Each store fetches and pushes once, under a 60-second network timeout.
**Constraints**: The command must never leave a scan in neither the code
repository nor a stored folder (SC-004). It adds no dependency, and keeps the
worktree guard's import cost unchanged. Minimal-complexity bias.
**Scale/Scope**: 114 review scans from 46 issues in wfctl, landing in 45
folders, since #656's scan joins #649's folder and `650-bob-pr-review-guard`
is created. pfms runs it once after the
release. A later release removes the command.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. The gates below come
from its own documented conventions instead: `AGENTS.md` (definition of done,
imports and the Context Map, testing conventions) and the accepted records that
`wfctl arch context` prints for this branch. That substitution is recorded in
Complexity Tracking.

- [x] Validation plan exists: `uv run pytest -q`, `uv run ruff check wfctl/
      tests/`, `uv run mypy`, `python3 .github/scripts/check_imports.py`, and
      `uv run wfctl doctor` are named, and `tests/test_store_scans.py` covers
      every acceptance scenario (see quickstart.md).
- [x] Complexity is justified: one new module and no new dependency. The
      store, the layout check, the issue-key match, and the scan path all reuse
      existing functions. The one new abstraction is the package
      `wfctl/evidence/`, which `contexts-are-packages` already requires for
      new evidence code (research R2).
- [x] Ownership is stated: the command decides each scan's folder from the
      scan's own text, the spec store's `store` function decides whether a
      folder is stored by asking git, and the user decides each conflict. No
      state outlives a run (data-model.md).
- [x] Contexts follow the map (`contexts-are-packages`): the new module sits in
      `wfctl/evidence/` and imports only `_spec_store` (evidence), `_paths`,
      and `_tracker` (both shared). `cli.py` imports it through the package.
- [x] The change commits a release note (`change-carries-release-note`):
      `changes/759.addition.md`.
- [x] The record the branch amends stays accurate
      (`scans-live-in-spec-folder`): its Consequences say the old review scans
      move to their spec folders, and `scans/` stays on
      `_paths.non_record_subtrees` for the evaluation and spike scans (FR-013).
      `AGENTS.md` and the comment above `SCANS_DIR` in `_paths.py` say the
      same, since both still say the old scans stay under the arch root.
- [x] Tests pin `NO_COLOR` where they read the table, and each test name is a
      sentence whose docstring says why it exists (`AGENTS.md`, Testing
      conventions).

Re-checked after Phase 1: unchanged. The data model adds no persistent state,
and the CLI contract adds one subcommand to an existing group.

## Project Structure

### Documentation (this feature)

```text
759-move-old-scans/
├── design.md            # /speckit.brainstorm output
├── spec.md              # /speckit.specify and /speckit.clarify output
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli.md           # Phase 1 output: the command, its flags, output, and exit codes
├── scans/
│   └── clarify.md       # /speckit.clarify scan
└── tasks.md             # Phase 2 output (/speckit.tasks, not created here)
```

### Source Code (repository root)

```text
wfctl/
├── evidence/
│   ├── __init__.py          # new: lazy re-exports, the pattern wfctl/arch/__init__.py uses
│   └── _scan_move.py        # new: find, place, write, store-and-delete, and the report
├── _spec_store.py           # unchanged: store(), layout(), and report_lines() are called as they are
├── _paths.py                # the comment above SCANS_DIR says scans/ stays listed for evaluation and spike scans
└── cli.py                   # new `store scans` command on store_app, beside `store specs`;
                             # records each push as `store-scans` (research R9)

AGENTS.md                    # Architectural constraints: the old review scans move to their spec folders

tests/
└── test_store_scans.py      # new: every acceptance scenario in spec.md

docs/architecture/
├── scans-live-in-spec-folder.md        # amended Consequences (FR-013)
├── design/759-scan-names-its-folder.md # already written by /speckit.brainstorm
└── scans/                              # 114 review scans deleted by running the command

changes/
└── 759.addition.md          # release note
```

**Structure Decision**: The command's logic goes in a new module,
`wfctl/evidence/_scan_move.py`, and `cli.py` only parses flags, calls it, and
prints. A separate module keeps a temporary command out of `_spec_store.py`,
which the worktree guard imports before every shell command, and makes its
later removal a deletion of one module, one CLI function, and one test file.
Research R2 says why the module goes in a new package rather than flat beside
`_spec_store.py`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Gates come from `AGENTS.md` and the accepted records, not a constitution | The repository has no `.specify/memory/constitution.md` | Leaving the gate section with only the template's three gates would skip the import map and release note rules this repository enforces in CI |
| First module in `wfctl/evidence/` | `contexts-are-packages` puts each context's code in its package, and the import check fails a new flat module that has no baseline line | A flat `_scan_move.py` needs a new baseline placement line, which waits for the user to run `wfctl arch approve-imports`, and adds a line #671 later has to delete |
