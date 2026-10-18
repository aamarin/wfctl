# Implementation Plan: Save unsaved work when a worktree is removed

**Branch**: `40-save-uncommitted-on-remove` | **Date**: 2026-10-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/Users/andremarin/Development/wfctl-specs/40-save-uncommitted-on-remove/spec.md`

## Summary

Removing a worktree with `--force` deletes untracked files, uncommitted edits,
and commits that were never pushed or merged. After this change, the removal
hook calls `wfctl hook worktree-remove`, which saves what it can copy safely
and stops the removal for what it can't.

1. It checks first, and copies nothing until every check has passed. An
   uncommitted edit, a commit on no remote that trunk doesn't hold, or spec
   files that differ from the main checkout's copy stop the removal, and the
   output lists all of them with the manual route (research R2 - R4, R6).
2. Spec files inside the worktree are copied to the branch's spec dir in the
   main checkout, through `wfctl store specs`, which #359 is also building
   (research R6, R7).
3. Untracked files, and the ignored folders a repository lists under
   `save_on_remove`, are copied to `unsaved/` in the branch's state dir, through
   `wfctl archive unsaved` (research R5, R10).

`archive-specs` becomes a hidden alias for the hook command, so both live
repositories get this without editing `.workmux.yaml`. The numbered archive and
the `.agent/` rescue are deleted (research R11).

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer` and `rich`, already in use. `difflib`,
`shutil` and `os` from the standard library. No new dependency.
**Storage**: Files only. The main checkout's spec dir and `<state dir>/unsaved/`.
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`,
`uv run mypy wfctl/`. Tests build real git repositories and worktrees under
`tmp_path`, as `tests/test_archive_specs.py` already does.
**Target Platform**: macOS and Linux, git 2.38 or later for the merge check
(older git warns and goes ahead).
**Project Type**: CLI
**Performance Goals**: None beyond today's hook. The checks are four git
commands, and there is no size cap (spec Assumptions).
**Constraints**: The hook must never leave a worktree stuck over an unrelated
error, and must never let a removal go ahead after a failed copy. Minimal
complexity: no new abstraction beyond the three modules in research R1.
**Scale/Scope**: Two repositories in use (wfctl and pfms). Untracked sets
measured across live worktrees were a handful of files.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repository has no `.specify/memory/constitution.md`. The gates below come
from `AGENTS.md` and the in-force architecture records instead, which Complexity
Tracking records.

- [x] Validation plan exists: the definition of done (`pytest`, `ruff`, `mypy`,
      then `uv run wfctl doctor`), `uv run wfctl check config` for the new key,
      the tests listed under Source Code, and `quickstart.md`, whose step 4 is
      the real removal Andre runs.
- [x] Complexity is justified: three modules, each with a reason in research
      R1. No new dependency, no new storage, and no new hook mechanism, since
      one function under three command names is what `archive-specs` already
      does.
- [x] Ownership is stated:
  - Whether a removal stops is computed by wfctl's hook, from git, at removal
    time. workmux can't compute it, because `--force` turns off its own check
    and it doesn't look at commits (`worktree-removal-requires-saved-work`).
  - `stops_removal` is computed by `StoreResult`, not by the hook, so
    `store specs` by hand and the hook can't disagree (research R7).
  - Which ignored folders are worth keeping is the repository's, through
    `save_on_remove`. wfctl can't tell a notes folder from `node_modules/`
    (`removal-copy-destinations`).
  - Trunk is `_paths.trunk_branch`, the one answer `wfctl start` already uses.
- [x] `install-modes`: `.workmux.yaml` is seed-once, so the hook keeps
      `archive-specs` working as an alias instead of asking repositories to
      edit it. The template fix reaches only repositories seeded afterwards
      (research R9).
- [x] `no-hardcoded-agent`: the seeded hook names no agent.
- [x] `a-rule-is-expressed-as-a-check`: a bad `save_on_remove` entry is a
      `check config` finding, not only a sentence in a doc (research R10).
- [x] `session-state-is-re-derived`: nothing about a run is recorded. Every
      value is read from git and the filesystem when the hook runs.
- [x] `layer-model`: nothing under `.agents/` or `.claude/` is edited by hand.
      This feature changes no skill under `wfctl/agents/skills/`; it changes
      the seeded config under `wfctl/agents/configs/`.

Re-checked after Phase 1: the data model and contract add no state, store, or
dependency beyond the above. All gates still pass.

## Project Structure

### Documentation (this feature)

```text
<FEATURE_DIR>/
├── design.md
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/cli.md     # Phase 1
└── tasks.md             # /speckit.tasks, not this command
```

### Source Code (repository root)

```text
wfctl/
├── _archive.py                          rewritten for `archive unsaved` (R1)
│   ├── is_inside                        kept; the store uses it too
│   ├── declared_folders(repo_root)      save_on_remove, with problems (R10)
│   ├── check(worktree, spec_dir)        tracked edits (R4), unmerged
│   │                                    commits (R3), untracked list and
│   │                                    folders (R5); copies nothing
│   ├── save(check, state_dir, extra)    staging, move aside, rename (R5);
│   │                                    `extra` is the spec dir in the bare
│   │                                    layout (R7)
│   ├── SaveFailed                       replaces ArchiveIncomplete
│   └── deleted: _SPEC_MAP, _render_index, _plan, archive,
│                _LEGACY_DEST_PREFIX (R11)
├── _copy_out.py                         new (R1, R6)
│   ├── plan(source, dest)               missing / same / different, with diffs
│   └── apply(plan, overwrite)           copies; raises on failure
├── _spec_store.py                       new, small; #359 extends it (R1, R7)
│   ├── StoreResult                      outcome, spec_dir, inside, lines;
│   │                                    stops_removal, exit_code
│   └── store(worktree, branch, overwrite)
│                                        copy-out, to_unsaved, not_applicable,
│                                        no_spec_dir
├── _paths.py
│   └── is_main_checkout(repo_root)      new; tells the main checkout from a
│                                        bare layout when main_checkout is None
├── _workmux.py
│   ├── REMOVE_HOOK                      renamed from ARCHIVE_HOOK; calls
│   │                                    `wfctl hook worktree-remove` (R9)
│   └── pre_remove_wired                 accepts all three names (FR-007)
├── cli.py
│   ├── hook_app help                    widened to workmux hooks (FR-008)
│   ├── hook worktree-remove             new; checks, then store, then save
│   │                                    (R2, R8); also registered hidden as
│   │                                    archive-specs and archive-story
│   ├── archive_app + archive unsaved    new group and command
│   ├── store_app + store specs          new group and command; #359 adds its
│   │                                    layouts to the same command
│   ├── check config                     adds declared_folders problems (FR-034)
│   ├── _check_workmux_hook              names the new command and unsaved/
│   │                                    (R9)
│   ├── _archive_destination             points at unsaved/
│   └── archive_specs_cmd                deleted; its function is the hook's
├── _completion.py                       comment naming _SPEC_MAP removed
└── agents/configs/workmux/.workmux.yaml pre_remove becomes REMOVE_HOOK's block,
                                         no `|| true` (R9)

docs/
├── reference.md                         archive-specs row replaced (R11)
└── ponytail-debt.md                     row 6 resolved, row 5 updated (R11)

tests/
├── test_archive_unsaved.py              new
│   ├── git ls-files lists a nested repository as one dir/ entry, and an
│   │   untracked symlink as a path (written first; R5's assumption)
│   ├── an untracked file lands at the same relative path, byte for byte
│   ├── a nested repository is copied whole, with its .git
│   ├── a symlink is copied as a link with the same target
│   ├── a save_on_remove folder is copied; an unlisted ignored folder is not
│   ├── a listed folder that doesn't exist is skipped without a warning
│   ├── an entry outside the repository is skipped with a warning
│   ├── the spec dir is never saved, even when it isn't ignored
│   ├── an earlier unsaved/ is moved aside under a timestamp
│   ├── a failed copy raises SaveFailed and leaves no unsaved/ or staging
│   ├── nothing to save creates no folder
│   ├── an unstaged edit and a staged edit each refuse, naming the file
│   ├── a commit on no remote, not merged, refuses and is named
│   ├── a pushed commit that isn't merged passes
│   ├── a squash-merged branch whose remote branch was deleted passes
│   ├── a branch whose merge would conflict refuses
│   ├── no trunk warns and passes
│   └── the output prints 20 paths, then "and N more"
├── test_copy_out.py                     new
│   ├── a missing file is copied; an identical one is left alone
│   ├── a differing file refuses with its diff; nothing is written
│   ├── --overwrite replaces only the differing files
│   ├── a file only in the destination is untouched, with and without
│   │   --overwrite
│   ├── a non-UTF-8 file reports "binary file differs"
│   └── a copy that raises returns copy_failed
├── test_spec_store.py                   new; #359 adds its own cases here
│   ├── stops_removal for every outcome, inside and outside the worktree
│   ├── not_applicable inside the worktree stops removal and exits 0 by hand
│   ├── the main checkout reads not_applicable; a bare layout reads to_unsaved
│   └── copied prints "nothing backs this copy up", never "durable"
├── test_worktree_remove.py              replaces test_archive_specs.py
│   ├── a clean worktree with untracked files: spec files copied out,
│   │   unsaved/ written, exit 0
│   ├── differing spec files and an uncommitted edit: both listed, nothing
│   │   copied, exit 1, manual route printed
│   ├── a refusal from either check copies no spec files (FR-002)
│   ├── the bare layout saves the spec dir under unsaved/
│   ├── archive-specs and worktree-remove give the same result on the same
│   │   fixture, and archive-specs prints no notice
│   ├── archive-story prints its notice and still works
│   ├── an unexpected exception warns and exits 0
│   └── wfctl --help lists neither alias; hook --help lists worktree-remove;
│       archive --help lists unsaved
├── test_workmux.py                      updated
│   ├── the template's pre_remove block contains REMOVE_HOOK, with no
│   │   `|| true`
│   └── pre_remove_wired accepts each of the three names
└── test_paths.py                        save_on_remove findings in check config,
                                         beside the trunk findings; a missing
                                         folder is not one
```

**Structure Decision**: The single-package layout the repository already has.
`cli.py` parses and prints. The checks and the copy live in `_archive.py`, the
copy-out in `_copy_out.py`, and the result both callers read in
`_spec_store.py`.

### Implementation order

1. The two `git ls-files` tests from `test_archive_unsaved.py`, against a
   hand-built fixture, before any copy code. If git lists a nested repository
   file by file, research R5's copy rules need revisiting first.
2. `_archive.check`: tracked edits, then the merge check and its four cases
   (pushed, squash-merged, conflicting, no trunk).
3. `declared_folders`, and its findings in `check config`.
4. `_archive.save`, with the staging, the move aside, and every copy rule.
5. `_copy_out.plan` and `apply`, then `_paths.is_main_checkout`, then
   `StoreResult` and `store()`.
6. `wfctl store specs` and `wfctl archive unsaved` in `cli.py`.
7. `wfctl hook worktree-remove` with the two-phase order, then the two
   aliases. Delete `archive_specs_cmd` and the old archive code in the same
   commit, and move `test_archive_specs.py`'s still-relevant cases into
   `test_worktree_remove.py`.
8. `REMOVE_HOOK`, the template, `pre_remove_wired`, and `doctor`'s messages.
9. Help text, `docs/reference.md`, `docs/ponytail-debt.md`, and the
   `_completion.py` comment.
10. Check whether #359 has merged. If it has, merge `main` in and run the three
    checks in research R12.
11. The definition of done: `pytest`, `ruff`, `mypy`, then `uv run wfctl
    doctor` and `uv run wfctl check config`. Then `quickstart.md` steps 1 - 3,
    and hand step 4 to Andre.

### Risks

- workmux 0.1.268 might no longer run `pre_remove` under `--force`. This was
  only verified on 0.1.211, and nothing here can test it except the real
  removal in `quickstart.md` step 4. If it fails, the whole feature needs a
  different trigger, so step 4 should run before the change is opened for
  review, not after.
- The outer catch-all exits 0 on an unexpected exception, so a bug in the
  check phase would let a removal go ahead without saving. That is the rule the
  design keeps on purpose, so an unrelated bug never leaves a worktree stuck.
  The tests for each check are what stand in front of it.
- #359 is building the same `store specs` command and `_spec_store.py` at the
  same time. The overlap is kept to one small file and one command (research
  R1, R12), and both branches already agree on `stops_removal`.
- The hook can't see `--keep-branch`, so a removal that keeps the branch still
  stops on unmerged commits. The manual route covers it, and the spec accepts
  it.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| No constitution; gates taken from `AGENTS.md` and the in-force records | The repository has no `.specify/memory/constitution.md` | Leaving the section with only the template's gates would check nothing specific to this repository |
| Three modules instead of one | Keeps the add/add conflict with #359 to a small file (research R1) | One module would put both features' store code in one conflicting file |
