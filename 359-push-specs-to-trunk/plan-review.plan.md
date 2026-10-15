# Implementation Plan: wfctl stores a branch's spec dir on its spec store's remote

**Branch**: `359-push-specs-to-trunk` | **Date**: 2026-10-14 | **Spec**: `spec.md` in this feature directory
**Input**: Feature specification from `spec.md` in this feature directory

## Summary

wfctl stores a branch's spec dir itself and asks git whether it was stored, so
an unattended run backs up its own specs and removal stops calling an unstored
spec dir safe. The decision is the level-2 record `spec-storage-read-from-git`.

A new module, `_spec_store.py`, holds the git work: which layout the spec root
is in, which spec dirs are not stored, and the store itself, which commits one
folder, merges the upstream, and pushes under a file lock. Three callers use
it:

1. A built-in `store-specs` pass under `implement`, which names `/store-specs`
   as the next command until the spec dir is stored.
2. `wfctl check specs`, which lists every unstored spec dir and keeps branches
   that still have a worktree under a separate heading.
3. The removal command, which now runs the store and warns when it fails instead
   of printing "durable". Every removal hook calls `archive-specs` today. #40 is
   moving the hook to `wfctl hook worktree-remove`, with `archive-specs` as its
   hidden alias, and that command calls `store specs` too (research R11).

Design records read before this plan (via `reading-design-records`):

```
Design records: 3 listed in design.md
  docs/architecture/design/store-specs-implement-pass.md
  docs/architecture/design/store-specs-at-removal.md
  docs/architecture/design/store-specs-merges-before-push.md
```

The level-2 record `spec-storage-read-from-git` was read as the boundary this
plan implements. It is still `proposed`, and accepting it is Andre's call.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer`, `rich`, and `fcntl` from the standard
library; no new dependency
**Storage**: git history in the spec store, written only by `wfctl store specs`.
Nothing else is written; every state is read from git when asked (FR-014)
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy
wfctl/`, `uv run wfctl doctor`, and the real run in `quickstart.md`. New tests
build a bare remote and two clones in a temporary folder, the same setup the
brainstorm's scratch tests used
**Target Platform**: the `wfctl` CLI on macOS and Linux. `fcntl` makes the
store POSIX only, which matches CI and both repositories using wfctl (research
R5)
**Project Type**: CLI
**Performance Goals**: the pass adds under 0.5 seconds to `wfctl status`
(SC-006). It runs two git commands scoped to one folder, and only once
`implement` reads done (research R14)
**Constraints**: the store never rebases, stashes, or force-pushes (FR-004);
never stages a path outside this branch's spec dir (FR-001); never touches the
network to read state (FR-016); never prompts for credentials (research R7).
`pipeline-state-is-one-payload`, `session-state-is-re-derived`, `layer-model`,
and `no-hardcoded-agent` apply as accepted. Tests pin `NO_COLOR` for console
assertions. Minimal-complexity bias
**Scale/Scope**: one new module, one new reader and pass, two new commands, one
new command wrapper, one changed removal command (`archive-specs`, unless #40
merges first), one changed skill paragraph, one small refactor of
`_hook.committable`, and one routing change in `next_step_content`

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. The gates below come
from `AGENTS.md` and the accepted records `wfctl arch context` prints, and the
substitution is recorded under Complexity Tracking.

- [x] Validation plan exists: the definition of done in `AGENTS.md`, the new
      tests named under Project Structure, the payload snapshot regenerated with
      a reason, `uv run wfctl install-skills --agent claude` followed by a real
      `/store-specs` run, and every step in `quickstart.md`.
- [x] Complexity is justified: one module rather than logic spread across
      `cli.py`, because the store writes what three readers check (research R1).
      The lock is the one piece of new machinery, and it exists because two
      stores interleaving in one checkout is a real case at removal (FR-027).
- [x] Ownership is stated: wfctl owns whether a spec dir is stored, and computes
      it from git on every read. The agent shouldn't answer, because a
      self-report reads the same whether the push happened or not
      (`spec-storage-read-from-git`). The layout is computed by wfctl from git,
      using the same rule the worktree guard uses, so the two cannot disagree
      about where a commit is safe (research R2).
- [x] `pipeline-state-is-one-payload`: the pass's state reaches every view
      through the existing payload. No view reads git itself.
- [x] `session-state-is-re-derived`: nothing about the store is recorded by
      wfctl. Git history is the only record.
- [x] `layer-model`: the wrapper and the skill edit land under
      `wfctl/agents/`, then `uv run wfctl install-skills --agent claude`.
- [x] `no-hardcoded-agent`: no hook changes on this branch. Removal reaches the
      store through the `archive-specs` line both repositories already run,
      which #40 keeps working as a hidden alias of
      `wfctl hook worktree-remove`.
- [x] `vendor-upstream-skills`: no spec-kit-derived skill is edited.
      `end-session` is wfctl's own.
- [x] `a-rule-is-expressed-as-a-check`: "the store commits only this branch's
      folder" and "a store never touches another branch's edits" are visible in
      git after a run, so both are tests, not prose.
- [x] `wfctl-runs-the-verification`: unchanged. The pass reads git, not the
      agent's word, which is the same principle applied to a new question.

Re-checked after Phase 1: `data-model.md` adds no stored state, and
`contracts/cli.md` keeps the status payload's shape, so its version stays 1.3.
All gates still pass.

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
├── _spec_store.py                      new (research R1)
│   ├── Layout, layout(root, repo_root)  the four kinds (R2, data-model § Layout)
│   ├── owns_branch(root, here)          moved out of _hook.committable (R2)
│   ├── Unstored, unstored(root, paths)  the two git reads, grouped by folder (R3)
│   ├── describe(unstored)               "uncommitted: N files" / "committed, not pushed"
│   ├── StoreResult, store(spec_dir, branch, repo_root)
│   │                                    lock, add, commit, fetch, merge, push
│   │                                    (R5, R7, R8, R9); `MERGE_HEAD` tells a
│   │                                    conflict from a refused merge, and
│   │                                    `git diff --cached` then tells staged
│   │                                    files from unstaged edits (R8);
│   │                                    `stops_removal`, which removal reads
│   │                                    instead of the exit code (R6)
│   └── _lock(git_dir, timeout=10.0)     fcntl.flock, polled every 0.2 s (R5)
├── _hook.py
│   └── committable                      calls _spec_store.owns_branch per root;
│                                        behaviour unchanged
├── _evidence.py
│   └── store_specs(ev)                  the pass reader; display, never reason (R4)
├── _pipeline.py
│   ├── _STEPS["implement"]              sub_steps=(SubStep("store-specs",
│   │                                    "/store-specs", _AUTOMATIC,
│   │                                    _evidence.store_specs),)
│   └── next_step_content                a block filed for the outstanding pass's
│                                        own action routes to that pass, before
│                                        the `wfctl verify` fallback; any other
│                                        block routes as today. New
│                                        `block_action` argument, and the
│                                        docstring names the exception (R15)
├── cli.py
│   ├── next_cmd                         passes `block_action` from `by_step`,
│   │                                    as `build_report` does (R15)
│   ├── store_app + store specs          new group and command (contracts/cli.md);
│   │                                    records the store-specs action on
│   │                                    `stored` (R15)
│   ├── check_app help                   widened (FR-025)
│   ├── check specs                      new command (R10)
│   └── archive_specs_cmd                runs the store when the spec dir is
│                                        outside the worktree; "durable" line
│                                        removed (R6, R11). Dropped if #40's
│                                        `hook worktree-remove` lands first
└── agents/
    ├── commands/store-specs.md          new wrapper (FR-019)
    └── skills/end-session/SKILL.md      "Report only" paragraph names the store
                                         in a spec store with an upstream (R12)

tests/
├── test_spec_store.py                   new; bare remote and two clones
│   ├── merge --abort leaves another branch's edited and untracked files alone
│   │                                    (written first; the level-3 record's
│   │                                    open assumption)
│   ├── the commit holds only this folder; another staged path stays staged
│   ├── a moved remote is merged and pushed; other edits byte-for-byte unchanged
│   ├── an unreachable remote keeps the commit and reports not pushed, exit 1
│   ├── the next store from another branch pushes both commits
│   ├── a conflict in this folder is reported as a conflict, not as staged
│   │   files, though `git diff --cached` lists paths; it aborts, keeps the
│   │   commit, names the folder, and leaves no MERGE_HEAD
│   ├── another folder's file staged and a moved remote: the commit is kept,
│   │   the merge is refused, the output names the staged folder, exit 1
│   ├── storing the branch that owns the staged folder clears the index and
│   │   pushes the first branch's kept commit with its own; the first
│   │   branch's next store reads already_stored
│   ├── a merge blocked by an unstaged edit, with nothing staged, names the file
│   ├── a push refused after the merge keeps the merge commit
│   ├── a second store waits for the first, and fails after the timeout
│   ├── a deleted file is committed as a deletion
│   ├── already stored creates no commit
│   ├── the subject starts specs(<issue>): and names the files
│   ├── each layout kind is detected, including a worktree on the code's own
│   │   branch (in_repo) and a folder nested in another repo (unmanaged)
│   ├── not_applicable for a spec dir inside the worktree sets stops_removal
│   │   and still exits 0 by hand; every outcome for a spec dir outside it
│   │   leaves stops_removal false
│   └── no git call prompts: GIT_TERMINAL_PROMPT=0 is set on every call
├── test_store_specs_pass.py             new
│   ├── implement done with uncommitted files names /store-specs, in_progress
│   ├── committed and pushed reads done, with no fetch
│   ├── committed, not pushed reads in_progress
│   ├── each non-store layout reads skipped with its text and no warning
│   ├── the pass never routes to `wfctl verify` (no reason on the reading)
│   ├── a host block on store-specs routes to /store-specs with auto false,
│   │   not to `wfctl verify`, in `status --json` and in the `next-step.md`
│   │   that `wfctl next` writes (`resume` writes it too, and goes through
│   │   `build_report`, so reading its copy would not exercise `next_cmd`)
│   ├── a push or issue-close block on a finished implement, with store-specs
│   │   outstanding, still routes to `wfctl verify`
│   ├── a declared manual pass under implement, with a block filed for its
│   │   name, returns the qualified pass name with auto false
│   ├── a successful `wfctl store specs` after the block records the action,
│   │   lifts the hold, and the pass reads done
│   ├── `already_stored` records no action
│   └── `wfctl step none implement.store-specs` wins over the reader
├── test_check_specs.py                  new
│   ├── unstored dirs with no worktree are listed and exit 1
│   ├── a dir a worktree resolves to is under In progress and exits 0
│   ├── a prunable worktree does not keep its dir in progress
│   ├── all stored prints the one-line tick, exit 0
│   └── a non-store layout names the root and exits 0
├── test_archive_specs.py                updated, or moved onto
│   │                                    `hook worktree-remove` if #40 is first
│   ├── the durable test now asserts the store ran and "durable" is absent
│   ├── a failed push at removal warns and exits 0
│   ├── a lock timeout and a merge refusal at removal warn and exit 0
│   └── the in-worktree archive path is unchanged
├── test_hook*.py / test_worktree_guard.py
│                                        unchanged, and must stay green after
│                                        the owns_branch refactor
└── pipeline_payload_snapshot.json       regenerated; only the new store-specs
                                         entries move (R13)
```

**Structure Decision**: The single-package layout the repository already has.
The git work lives in `_spec_store.py`, `cli.py` only parses and prints, and the
reader in `_evidence.py` is a few lines that call the module, beside
`plan_review`, which it resembles.

### Implementation order

1. The `merge --abort` test, against a hand-built fixture, before any store
   code. If git touches another branch's edits there, the merge decision needs
   revisiting before anything is built on it.
2. `_spec_store.layout` and `owns_branch`, with `_hook.committable` moved onto
   `owns_branch`. Run the guard and hook tests unchanged to show the refactor
   moved no behaviour.
3. `unstored` and `describe`, with their tests.
4. `store`, without the lock, and its tests. Then the lock and its test.
5. `wfctl store specs`, then `wfctl check specs` and the group's help line.
6. The `store_specs` reader and the pass under `implement`, then the routing
   change in `next_step_content` and the action `store specs` records. Regenerate the
   payload snapshot and read the diff: only `store-specs` entries may appear.
7. `archive-specs`, and the updated archive tests. Check first whether #40's
   `wfctl hook worktree-remove` is on `main`. If it is, merge `main` in, skip
   the `archive-specs` edit, and point the removal tests at the hook instead.
   Check that the hook reads `stops_removal` rather than the exit code, so a
   failed push at removal still warns and goes ahead (research R6). The moved
   tests start from a clean worktree, because #40's `archive unsaved` refuses a
   dirty one whatever the store returned (contracts/cli.md). Whichever branch
   merges second also checks that the merged `store` runs #40's copy-out before
   it would return `not_applicable` in the default layout (research R6).
8. The `/store-specs` wrapper and the `end-session` paragraph. Then `uv run wfctl
   install-skills --agent claude` and read both installed files.
9. The definition of done: pytest, ruff, mypy, doctor. Then every step in
   `quickstart.md`, including the real store of this branch's own spec dir.

### Risks

- The #40 branch is changing removal at the same time. It moves the hook to
  `wfctl hook worktree-remove`, keeps `archive-specs` as a hidden alias, and
  drops `wfctl archive specs`. This plan touches only the outside-the-worktree
  half of `archive-specs` (research R11), and whichever branch merges second
  merges `main` in and resolves one function. #40's record says the hook stops
  removal when the store "refuses". Both branches read that as
  `StoreResult.stops_removal`, not as `store specs` exiting 1. #40 confirmed
  this in its record at `2e9f124`, and settled the exit code for
  `not_applicable` at `b3fc797` (research R6).
- A file staged anywhere in the spec store blocks every branch's merge while
  the remote has moved (research R8). The store can't clear it, because FR-001
  forbids touching another branch's staged files, so the output has to name the
  folder and the remedy.
- The refactor of `_hook.committable` runs before every Bash call an agent
  makes. It is a move with no change in behaviour, the existing guard tests are
  the check. `owns_branch` must keep the direction the guard already takes on an
  error: when git can't answer, the root is not a store, so the guard refuses
  the commit and the store commits nothing.
- The real run in `quickstart.md` step 3 pushes to `origin/specs-trunk`. It
  will also push commit `ed3f5e8`, 552's spec dir, which was committed by hand
  and never pushed. That commit belongs on the remote, which the spec's first
  edge case accepts.
- Running `wfctl store specs` from inside the agent's session is a push, and
  the host's permission layer may refuse it. That refusal is what
  `report-block` is for, and the wrapper says so. It is not something to route
  around.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| No constitution file; gates drawn from `AGENTS.md` and accepted records | the template requires gates with a source | borrowing another project's constitution would make every gate false |
| A file lock around the whole store | two removals or two unattended runs finishing together would fight over one index (FR-027) | retrying on git's own `index.lock` leaves gaps between git commands where two stores still interleave (research R5) |
