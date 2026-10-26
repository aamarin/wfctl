# Implementation Plan: Mirror below recorded dir

**Branch**: `293-mirror-below-recorded-dir` | **Date**: 2026-10-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `spec.md` in this feature directory

## Summary

wfctl records the speckit runtime scripts by file name, so a script it stops
shipping is reported by the next install and removed by `--prune`. Today the
install record names `.specify/scripts/bash` as one folder entry, and the
comparison between the last install and this one cannot see inside it.

The change has two parts.

1. The runtime target moves one level down, from `specify/scripts` to
   `specify/scripts/bash`, so the installer plans one row per script. The
   comment above `_RUNTIME_TARGETS` says why it names `bash/` and not its parent.
2. Tests cover every acceptance scenario that names a command, as mapped in
   Test Plan below.

No code retires the old folder entry. Each repository installed before this
change is redone by hand once: uninstall every layer, agent layers first, then
install again. A repository that is not redone loses the scripts at its next
pruning install and gets them back at the one after, which the record accepts
while Andre is the only user.

A fresh install now writes one `.gitignore` line per script where it wrote one
for the folder. A repository that already ignores `.specify/scripts/bash` or a
parent of it writes none, since `_ensure_gitignored` asks git whether the path is
already covered. Where the lines are new, a developer's own script in that folder
is no longer ignored and shows in `git status`. That is the visible change, and
it matches the record: the developer's file is theirs, not wfctl's.

The decision is `docs/architecture/deletion-follows-recorded-files.md`,
proposed. Retiring the old entry in code was the plan until the plan review,
and Andre chose the manual redo over it.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `typer` and `rich`, already in use; nothing added  
**Storage**: `.wf-skills-manifest.json` in the consuming repository, read and
rewritten by `install-skills`; no schema change  
**Testing**: `uv run pytest -q`, with new cases in `tests/test_install_skills.py`
and `tests/test_bundle.py`; `uv run ruff check wfctl/ tests/`;
`uv run mypy wfctl/`  
**Target Platform**: macOS and Linux developer machines, CI on Python 3.11 and
3.13  
**Project Type**: CLI  
**Performance Goals**: N/A. The installer plans three rows where it planned
one.  
**Constraints**: In a repository that has been redone or freshly installed, a
path wfctl cannot show it wrote is never deleted
(`deletion-follows-recorded-files`, and `_check_abandoned_entries`' own rule).
A repository not redone can still lose one at a pruning install, which the
record accepts as a cost.
Minimal-complexity bias: no migration code, no upgrade guard, no new `doctor`
check.  
**Scale/Scope**: One target-table entry, its comment, and the 12 tests in Test
Plan.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repository has no `.specify/memory/constitution.md`. The gates below come
from `AGENTS.md` and the accepted records instead, and Complexity Tracking
records the substitution.

- [x] Validation plan exists: the three `AGENTS.md` commands, the tests in
      Test Plan, and the manual upgrade exercise in `quickstart.md`.
- [x] Complexity is justified: nothing is added beyond one table entry. The
      upgrade guard and the fuller migration were considered and dropped.
- [x] Ownership is stated: the install record owns "did wfctl write this file,
      and does it still ship it?". The disk cannot answer it, since a script
      wfctl dropped and a script a developer added are the same bytes.
- [x] `install-modes` holds: the runtime scripts are a managed mirror, and the
      unit wfctl owns is the whole file. This change makes the record agree with
      that unit, where the folder entry claimed the directory.
- [x] `layer-model` holds: the source stays under `wfctl/specify/`, and the
      change touches no generated directory by hand.
- [x] `a-rule-is-expressed-as-a-check` holds: the rule that a runtime source
      holds only files is a test, since a violation shows up in the source tree.
- [x] `AGENTS.md` test conventions: new tests pin `NO_COLOR` where they assert
      on output, carry sentence names, and say in their docstrings which failure
      they catch.
- [x] `AGENTS.md` code style: no ruff rule set change, and every new function is
      annotated for mypy.

Re-checked after Phase 1: unchanged. Phase 1 added no entity, contract, or
dependency.

## Project Structure

### Documentation (this feature)

```text
293-mirror-below-recorded-dir/
├── design.md            # brainstorm output
├── spec.md              # /speckit.specify output, with Clarifications
├── plan.md              # this file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks, not created here)
```

No `contracts/`. The change adds no command, flag, or message; every string a
developer sees is one `install-skills` and `doctor` already print. The one
visible difference is the `.gitignore` lines Summary describes.

### Source Code (repository root)

```text
wfctl/
└── cli.py                    # _RUNTIME_TARGETS and its comment

tests/
├── test_install_skills.py    # dropped script, manual redo, developer's own script
└── test_bundle.py            # every runtime source directory holds only files
```

**Structure Decision**: The code change stays in `wfctl/cli.py`, at
`_RUNTIME_TARGETS` on line 2939. `_scanned_dirs` and `_planned_dirs` read the
same table and move down with it. The bundle-shape test goes in
`tests/test_bundle.py`, which already holds tests about what the bundle
contains.

## Test Plan

Every acceptance scenario that names a command gets a test, and so do FR-006
and SC-004. Each test adds the scripts it needs to the fixture bundle, since the
autouse `bundle` fixture builds no `specify/` tree. All of them go in
`tests/test_install_skills.py`, which already holds the install, doctor, and
uninstall tests, except FR-006, which goes in `tests/test_bundle.py`.

| Requirement | What the test does |
| --- | --- |
| US1 scenario 1 | Install, drop one script from the bundle, install again; the warning names the script by full path. |
| US1 scenario 2 | The same, with `--prune`; the dropped script is gone and the others remain. |
| US1 scenario 3 | The same, then `doctor` before reinstalling; it reports the script as no longer shipped and exits 1. |
| US2 scenario 1 | Old record with a `.specify/scripts/bash` folder entry, then uninstall and install; all three scripts on disk, the record names each script and no folder, and `doctor` exits 0. This is FR-003 and FR-007. |
| US2 scenario 2 | Old record, then `doctor`; no dropped-path finding, the three scripts listed as not on record, exit 0. |
| US2 scenario 3 | Old record, then `install-skills --prune --yes`; the scripts are gone. A second install puts them back, recorded per file. |
| US3 scenario 1 | Untracked developer script in the folder, then `doctor`; it is named as not on record and left alone, exit 0. |
| US3 scenario 2 | The same script, then `install-skills --prune`; the script remains. |
| US3 scenario 3 | The same script, then `uninstall-skills`; the three recorded scripts are gone and the developer's remains. |
| US3 scenario 4 | A committed developer script, then `doctor`; nothing is said about it. |
| FR-006 | Walk the sources `_RUNTIME_TARGETS` names in the real package, not the fixture bundle; each holds only files. |
| SC-004 | A fresh install's record has no folder entry under `.specify/`. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Gates taken from `AGENTS.md` and the accepted records | The repository has no constitution file | A gate with no source is decorative, and these two sources are what the repository binds work to |
