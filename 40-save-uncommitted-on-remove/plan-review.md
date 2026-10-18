# Plan Review Report

Review state: completed
Review type: full

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 30652c4b4f26ff32f488196e5fdef6406e38d342 | technical strategy |
| spec.md | a4f526723c5c4a397b6bda38d5e4433098617c3c | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | b07cc23e4928d8826b3882ec507d96a444e52da5 | design-record index |
| docs/architecture/design/40-archive-is-a-command-group.md | 79ae3a3db168a99972214eaa5414aedec74e764c | design record (level 3, listed in design.md) |
| docs/architecture/worktree-removal-requires-saved-work.md | d1ed774aa90a28172cb415ef577d2c0b48dcadf1 | design record (level 2, cited by design.md and plan.md) |
| docs/architecture/removal-copy-destinations.md | dbaf6e77c11bb079a674879ced417c3a74e6050e | design record (level 2, cited by design.md and plan.md) |
| research.md | 515d3170c3af08e0100f5501c03357e7662b8e07 | planning evidence |
| data-model.md | c4a292059d76ce2958e0dc7b1f8a9c98731f5a7d | planning evidence |
| contracts/cli.md | 33637bc90f114318e64157ff95ad0abff533bf63 | planning evidence |
| quickstart.md | 9c0ed2bd50622b92599aab31db2d239d26c21177 | planning evidence |
| ../../../wfctl-specs/359-push-specs-to-trunk/plan.md | 51905313e32de76891bfd0e7addbd656ac0acedd | #359 plan, which research R1, R7, and R12 rely on |
| ../../../wfctl-specs/359-push-specs-to-trunk/data-model.md | 6ea70cff0e8568cd36ef2e88a3664910f3b8ad0f | #359 data model, which research R7 cites |
| ../../../wfctl-specs/359-push-specs-to-trunk/research.md | 9d45be6f7405e38e83ae923af49d616c9b359ab5 | #359 research, whose R6 this plan cites |

## Review scope

- Full review: no earlier report and no plan copy existed at the report and copy paths.
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification.
- Conditional lenses: security and reliability applied, because the feature
  sits in front of a destructive and irreversible operation (deleting a
  worktree and its branch). It crosses no authentication, tenant, or secrets
  boundary. An un-ignored `.env` is copied into the user's own state dir, which
  the spec's clarification accepts and the saved-file list makes visible.
- Design records: 1 listed in design.md, `docs/architecture/design/40-archive-is-a-command-group.md`.
  The two level-2 records named in design.md's prose were read as well, since
  the plan's ownership gates cite them.
- Existing code inspected: `wfctl/_archive.py`, `wfctl/_paths.py`
  (`is_bare_layout`, `trunk_branch`, `main_checkout`, `spec_root`,
  `resolve_spec_dir`), `wfctl/_workmux.py`, `wfctl/_entry.py`, `wfctl/cli.py`
  (`archive_specs_cmd`, `check_config_cmd`, `hook_app`, `_archive_destination`,
  `_check_workmux_hook`), the seeded template
  `wfctl/agents/configs/workmux/.workmux.yaml`, this repository's
  `.workmux.yaml`, pfms's `.workmux.yaml`, and `docs/ponytail-debt.md`.
- Behaviour probed in a scratch repository on git 2.44.0: what
  `git ls-files --others --exclude-standard` lists for a nested repository and
  a symlink, what `git merge-tree --write-tree` returns for a squash-merged
  branch, and whether git merges over an untracked file identical to the
  incoming one.
- Reviewers: the four lenses above, run in sequence by one agent.

## Summary

BLOCKER: 0
MAJOR: 4
MINOR: 9

No BLOCKER findings identified in this review. The four MAJOR findings cover
two themes.

1. The merge check and the stop decision. The squash-merge case fails once
   trunk has changed the same lines (PR-001), and the phase that decides a
   spec-file stop does so outside the store's result (PR-002).
2. Contracts and failure paths the plan leaves open. The shared `store()` entry
   point disagrees with #359's plan (PR-003), and a failed listing of untracked
   files has no stated outcome (PR-004).

The git behaviour R5 rests on was confirmed on git 2.44.0. A nested repository
is listed once as `nested/`, and a symlink, including one to a folder, is listed
as a path.

## Findings

### PR-001: The merge check stops a squash-merged branch once trunk has changed the same lines

- Priority: MAJOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `spec.md §SC-004`: "A squash-merged branch whose remote branch was deleted
    is removed without a stop in 100% of cases."
  - `spec.md §User Story 1`, acceptance scenario 4.
  - `research.md §R3`: the branch passes only when the merge is clean and its
    tree equals trunk's tree.
  - `plan.md §Source Code`, `test_archive_unsaved.py`: "a squash-merged branch
    whose remote branch was deleted passes" is the only squash case.
  - Probe on git 2.44.0. A branch squash-merged into an untouched trunk gives
    exit 0 and a tree equal to trunk's tree, so it passes. After a later trunk
    commit edits the line the branch changed, `git merge-tree --write-tree main
    HEAD` exits 1 with `CONFLICT (content)`, so the removal stops. A rebase
    merge behaves the same way, since its commits are also on no remote.
- Finding: A three-way merge compares the branch with its original fork point,
  not with the squash commit. When trunk has since changed a line the branch
  also changed, the merge conflicts or produces a tree that differs from
  trunk's, even though trunk holds the work. As a result, SC-004's "100% of
  cases" holds only while trunk leaves the branch's lines alone.
- Why it matters: The stop fails safe, since nothing is lost and the manual
  route works. But in this repository most branches touch `wfctl/cli.py`, which
  is 7,826 lines, and worktrees often outlive their merge by days. That makes
  this a likely path, and the planned test only builds the case that passes, so
  the suite would stay green while SC-004 fails.
- Suggested response: State the limit in research R3 and in the plan's Risks,
  and take SC-004's wording back to the spec. Add a test for a squash merge
  followed by a trunk edit to the same line, so the behaviour that ships is a
  choice rather than an accident.
- Corroborated by: adversarial implementation and verification; requirements
  and traceability (SC-004)

### PR-002: Phase 1 decides the spec-file stop outside `StoreResult`

- Priority: MAJOR
- Category: Boundary / Ownership Concern
- Status: open
- Evidence:
  - `plan.md §Constitution Check`, ownership: "`stops_removal` is computed by
    `StoreResult`, not by the hook, so `store specs` by hand and the hook can't
    disagree."
  - `spec.md §FR-003`: the hook "MUST decide from the store's result".
  - `research.md §R2`, phase 1: the hook "resolves the spec dir and the layout,
    compares the worktree's spec files against the main checkout's copy", and
    "`store()` repeats it in phase 2".
  - `plan.md §Source Code`: `store(worktree, branch, overwrite)` has no mode
    that checks without copying, and `_copy_out.plan(source, dest)` is called
    directly.
- Finding: To compare in phase 1, the hook has to work out the layout itself:
  whether there is a main checkout, whether the layout is bare, and whether the
  spec dir is inside the worktree. That is a second copy of the dispatch
  `store()` owns, and the `differs` stop is then decided from `_copy_out.plan`
  rather than from a `StoreResult`. R2 also doesn't say whether phase 2 reads
  `stops_removal` from `store()` before running the copy into `unsaved/`.
- Why it matters: The ownership claim the plan relies on doesn't hold in the
  phase where the stop is decided. Once #359 merges, `store()` gains layouts
  and outcomes, such as `not_applicable` for the `in_repo` layout, that the
  hook's own copy doesn't know about. If phase 2 then runs the `unsaved/` copy
  without reading `stops_removal` first, the removal stops after a copy, which
  FR-002 rules out.
- Suggested response: Give phase 1 a `StoreResult` to read, for example a
  `store()` call that checks without writing, so there is one dispatch. State in
  R2 that phase 2 reads `stops_removal` from `store()` before the `unsaved/`
  copy runs. Because that changes `store()`'s signature, settle it together
  with PR-003.
- Corroborated by: architecture and boundaries; requirements and traceability
  (FR-002, FR-003)

### PR-003: The `_spec_store.py` contract this plan builds against disagrees with #359's plan

- Priority: MAJOR
- Category: Dependency / Feasibility
- Status: open
- Evidence:
  - `plan.md §Source Code`: `StoreResult` with `outcome, spec_dir, inside,
    lines`, and `store(worktree, branch, overwrite)`.
  - `research.md §R1`: "both branches already agree on the result's field names
    (R7)". `research.md §R7`: "`StoreResult` has the fields #359's data model
    names".
  - #359 `plan.md §Source Code`: `StoreResult, store(spec_dir, branch,
    repo_root)`.
  - #359 `data-model.md §Store result`: it names outcomes and exit codes but no
    fields, and says "The CLI prints it", while this plan carries preformatted
    `lines` on the result.
  - `research.md §R12`: the three merge checks don't include the signature or
    the fields.
- Finding: The two plans give the shared entry point different parameters. #359
  has the caller resolve the spec dir and has no `overwrite`. This plan has
  `store()` resolve the spec dir from the worktree and take `overwrite`. The
  plans also put output formatting in different places. #359's data model names
  no fields at all, so there is nothing yet for the two branches to agree on.
- Why it matters: The three-module split (R1, Complexity Tracking) is justified
  by keeping the second merge to "a few dozen lines of dispatch". With two
  signatures, whichever branch merges second has to redesign the entry point
  and rewrite the other branch's calls and tests. PR-002 adds a third shape if
  `store()` gains a check-only mode.
- Suggested response: Agree the signature and the field list with #359 now,
  and write them down in one place both plans cite. Add the signature and the
  output ownership to R12's merge checks.
- Corroborated by: architecture and boundaries (dependency)

### PR-004: The plan doesn't say what happens when the untracked listing fails

- Priority: MAJOR
- Category: Missing Information
- Status: open
- Evidence:
  - `research.md §R4`: a failed `git status` "warns and passes".
    `research.md §R3`: a failed merge check warns and passes.
  - `research.md §R5`: lists `git ls-files --others --exclude-standard -z` with
    no rule for its failure.
  - `data-model.md §Unsaved check`: `warnings` is "one line per check git
    couldn't answer".
  - `research.md §R8`, exit rule 3: "Any other exception: a warning naming it,
    and exit 0."
  - `worktree-removal-requires-saved-work.md §Decision`: the two checks warn
    when git can't answer, and a failed copy stops the removal.
  - `spec.md §FR-013` and `§FR-021`.
- Finding: Listing the untracked files is neither one of the two checks nor the
  copy. If an implementer treats a failed `ls-files` as a check git couldn't
  answer, or lets it raise into R8's catch-all, the removal goes ahead and
  deletes every untracked file without saving it, behind one warning line. If
  they treat it as part of the copy, the removal stops. The same question
  applies to an unreadable `wfctl.json` while reading `save_on_remove`.
- Why it matters: These two readings have opposite outcomes for the work this
  feature exists to save, and the planned tests have no case for either.
- Suggested response: State in R5 which rule applies to a failed listing, in
  line with the level-2 record's split between checks and copies, and add a
  test.
- Corroborated by: security and reliability; adversarial implementation and
  verification

### PR-005: `not_applicable` with `inside` true is reachable in the main checkout

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `data-model.md §Store result`: "`not_applicable` with `inside` true ... On
    this branch that can't happen".
  - `data-model.md §Copy-out`: in the main checkout, the outcome is
    `not_applicable`.
  - `research.md §R7`: `inside` is true "when the spec dir is inside the
    worktree being removed". `wfctl/_archive.py` `is_inside` is plain path
    containment.
  - `contracts/cli.md §wfctl hook worktree-remove`: `WORKTREE` defaults to
    `$WM_WORKTREE_PATH`, "then the current repository".
- Finding: When `wfctl hook worktree-remove` or `archive-specs` runs by hand in
  the main checkout, the spec dir sits inside the `worktree` argument. If
  `inside` is computed with `is_inside`, the result is `not_applicable` with
  `inside` true, so `stops_removal` is true. The hook then exits 1 and prints
  `git worktree remove --force <main checkout> && git branch -D <trunk>`.
- Why it matters: No removal is at risk, but the data model asserts something
  false, and two implementers can define `inside` differently.
- Suggested response: Define `inside` for the main checkout, and correct the
  data-model sentence.
- Corroborated by: deterministic checks (artifact agreement)

### PR-006: `_paths.is_main_checkout` duplicates `_paths.is_bare_layout` with a different test

- Priority: MINOR
- Category: Boundary / Ownership Concern
- Status: open
- Evidence:
  - `plan.md §Source Code`: new `is_main_checkout(repo_root)`, "tells the main
    checkout from a bare layout".
  - `data-model.md §Copy-out`: the test is whether `--git-common-dir` is the
    worktree's own `.git`.
  - `wfctl/_paths.py`: `is_bare_layout` already answers the bare question from
    `core.bare`. The `main_checkout` docstring says a separate-gitdir layout
    also returns None.
- Finding: There would be two readers of "is this layout bare", built on
  different git facts. In a separate-gitdir clone, `main_checkout` is None and
  `is_bare_layout` is false, while the plan's test reads the layout as bare and
  returns `to_unsaved`. That outcome is harmless, since the spec files are
  saved under `unsaved/`, but the plan doesn't name it.
- Why it matters: Two answers to one question tend to drift apart.
- Suggested response: Use `is_bare_layout` for the bare case, or say why a
  second test is needed, and say what a separate-gitdir layout gets.
- Corroborated by: architecture and boundaries

### PR-007: Overlap between untracked files, `save_on_remove` folders, and the spec dir is undefined

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `research.md §R5`: the spec dir is dropped from the `ls-files` list only,
    and folders are copied with `shutil.copytree(symlinks=True)`.
  - `spec.md §FR-018`: spec files are not saved twice.
  - `data-model.md §save_on_remove`: no row for a listed folder that isn't
    ignored, or one that holds the spec dir.
- Finding: Suppose a listed folder isn't gitignored. Its files then appear in
  the `ls-files` output and are copied first, and `copytree` into the same
  staging path raises `FileExistsError` by default, which R5 turns into a
  refusal. Every removal in that repository then stops with "couldn't save
  unsaved files (File exists)" until someone edits `wfctl.json`. Separately, a
  listed `specs/` saves the spec files a second time, which FR-018 rules out.
- Why it matters: The plan leaves a small behavioural choice to the
  implementer, and the likely literal reading produces a removal that can never
  succeed.
- Suggested response: State the rule for overlaps. For example, drop untracked
  paths under a listed folder, and drop the spec dir from listed folders. Then
  add a test.
- Corroborated by: adversarial implementation and verification

### PR-008: Research R3 and the data model name different sets of commits

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `research.md §R3`: a stop "names the commits from step 1"
    (`git rev-list HEAD --not --remotes`).
  - `data-model.md §Unsaved check`: `unmerged` holds each commit on no remote
    "that a merge into trunk would bring in".
- Finding: Step 1 doesn't exclude trunk. In a repository with no remote, it
  lists the whole history. Where local trunk is ahead of its remote, it lists
  trunk's own unpushed commits. R3 prints that list as is, while the data
  model's wording implies a filter R3 never runs.
- Why it matters: A stop can bury the branch's one commit under trunk's
  commits. Test fixtures built without a remote will show this first.
- Suggested response: Exclude trunk in step 1, for example
  `git rev-list HEAD --not --remotes <trunk>`. Trunk survives the removal, so
  this changes nothing about what is safe. Then make R3 and the data model say
  the same thing.
- Corroborated by: deterministic checks (artifact agreement)

### PR-009: Comments and doc rows that describe the old hook are missing from the change list

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `wfctl/agents/configs/workmux/.workmux.yaml`: the comment above
    `pre_remove` describes the numbered archive and says "a teardown hook must
    never be the thing that stops a worktree from being removed".
  - This repository's `.workmux.yaml` `pre_remove` comment calls the hook "a
    forensic snapshot" and says "archive-specs exits non-zero only in that
    case".
  - `docs/ponytail-debt.md`: the inventory row for `_archive._plan` (the
    `.agent/` rescue) and the line locations in the `_FORMER_ARCHIVE_COMMAND`
    row.
  - `plan.md §Source Code`: the change list names only the template's
    `pre_remove` line and ponytail-debt rows 5 and 6.
- Finding: The template comment is seeded into every new repository and would
  say the opposite of what the hook now does. This repository's own comment and
  the inventory row go stale in the same way.
- Why it matters: A reader of a newly seeded `.workmux.yaml` is told the hook
  never stops a removal, which is the behaviour this feature removes.
- Suggested response: Add the template comment, this repository's comment, and
  the inventory row to the change list. Editing this repository's comment
  doesn't affect SC-005, which is about behaviour.
- Corroborated by: architecture and boundaries (scope)

### PR-010: The copy-out assumes `specs/` is gitignored in the default layout

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `spec.md §User Story 3` and `research.md §R6`: the copy-out copies every
    file under the spec dir.
  - `wfctl/cli.py` `archive_specs_cmd` docstring: "`specs/` is gitignored".
    Nothing in wfctl enforces that in a consuming repository.
  - Probe on git 2.44.0: `git merge` refuses with "untracked working tree files
    would be overwritten by merge", whether the untracked copy is identical to
    the incoming file or not.
- Finding: In a default-layout repository that commits `specs/`, the copy-out
  writes the branch's spec files into the main checkout as untracked files. The
  next pull that brings in the merged branch then fails until those files are
  deleted.
- Why it matters: Neither repository in use today has the default layout, which
  is why this is MINOR. A repository that follows Spec Kit's convention of
  committing specs would meet it on its first merged removal.
- Suggested response: State the assumption, or copy out only files git doesn't
  track, since tracked spec files are already covered by the edit and commit
  checks.
- Corroborated by: adversarial implementation and verification

### PR-011: SC-006 is tested only on the `copied` outcome

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `spec.md §SC-006` and `§FR-031`: zero removal messages contain "durable",
    in any layout.
  - `plan.md §Source Code`, `test_spec_store.py`: "copied prints 'nothing backs
    this copy up', never 'durable'".
  - `wfctl/cli.py` `archive_specs_cmd`: "durable" is printed today for a spec
    dir outside the worktree, which becomes `not_applicable`, the outcome both
    repositories in use will see.
- Finding: The planned assertion covers `copied`, not the outcome that printed
  the word before.
- Why it matters: The regression SC-006 guards against would most likely
  return on the `not_applicable` path.
- Suggested response: Assert that "durable" is absent from the hook's output
  for every outcome, `not_applicable` included.
- Corroborated by: adversarial implementation and verification

### PR-012: The manual test's handle carries issue #40's key

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `quickstart.md §4`: `workmux add 40-scratch --base main`, then two forced
    removals.
  - This repository's `.workmux.yaml`: `post_create` runs
    `uv run wfctl issue start`, and `pre_remove` runs `uv run wfctl issue stop`
    after the archive hook.
  - `wfctl/_paths.py` `resolve_spec_dir`: a branch with no exact match falls
    back to the spec dir whose name starts with its issue key.
- Finding: The scratch worktree's hooks write to issue #40's board column, and
  step 4.2's successful removal runs `issue stop` against the open #40. The
  scratch branch's spec dir also resolves by key to #40's own spec dir. Because
  that dir is outside the worktree, the store reports `not_applicable`, so the
  manual test never exercises the copy-out.
- Why it matters: A test of removal shouldn't move the live issue's column,
  and the step reads as covering more than it does.
- Suggested response: Use a handle whose key names no open issue, or note the
  board side effect and say that the copy-out isn't covered by step 4.
- Corroborated by: adversarial implementation and verification

### PR-013: `typer.Exit` is an `Exception`, so a stop raised inside the catch-all exits 0

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `research.md §R8`, exit rules 1 and 3: a refusal exits 1, and any other
    exception exits 0.
  - `typer.Exit.__mro__` in this environment: `Exit`, `RuntimeError`,
    `Exception`.
  - `wfctl/cli.py` `archive_specs_cmd`: today's code raises `typer.Exit(1)`
    from an `except` clause, outside the `try` that the catch-all
    `except (Exception, SystemExit)` guards.
- Finding: If the new hook raises `typer.Exit(1)` for a refusal inside the
  guarded block, the catch-all swallows it and the removal goes ahead. R8
  doesn't name this constraint.
- Why it matters: This bug turns every stop into a silent removal. The planned
  exit-code tests would catch it, which is why it is MINOR.
- Suggested response: State in R8 that refusals leave the guarded block before
  the exit is raised, as `archive_specs_cmd` does today.
- Corroborated by: security and reliability

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Source Code `hook worktree-remove`; research R2 | covered |
| FR-002 | research R2 | PR-002 |
| FR-003 | research R7, R8 | PR-002 |
| FR-004 | research R8 | covered |
| FR-005 | research R8 | covered |
| FR-006 | research R9 | covered; PR-009 for the template comment |
| FR-007 | research R9 | covered |
| FR-008 | plan.md §Source Code `hook_app help` | covered |
| FR-009 | research R4 | covered |
| FR-010 | research R3 | PR-001, PR-008 |
| FR-011 | research R3 | covered |
| FR-012 | research R3 | covered |
| FR-013 | research R3, R4 | PR-004 |
| FR-014 | contracts/cli.md | covered |
| FR-015 | research R5 | PR-004 |
| FR-016 | research R5, R10 | PR-007 |
| FR-017 | research R5 | covered |
| FR-018 | research R5 | PR-007 |
| FR-019 | research R5 | covered; listing confirmed on git 2.44.0 |
| FR-019a | research R5 | covered; listing confirmed on git 2.44.0 |
| FR-020 | research R5 | covered |
| FR-021 | research R5 | covered |
| FR-022 | data-model.md §Saved result | covered |
| FR-023 | research R5; contracts/cli.md | covered |
| FR-024 | research R6 | PR-010 |
| FR-025 | research R6 | covered |
| FR-026 | research R6; contracts/cli.md | covered |
| FR-027 | research R6 | covered |
| FR-028 | research R6 | covered |
| FR-029 | research R7 | PR-005 |
| FR-030 | research R7 | covered |
| FR-031 | research R11; data-model.md §Store result | PR-011 |
| FR-032 | research R7 | covered; PR-006 |
| FR-033 | research R11 | covered |
| FR-034 | research R10 | covered |
| FR-035 | research R11 | covered |
| SC-001 | research R3, R4 | covered |
| SC-002 | research R5 | covered |
| SC-003 | research R5 | covered |
| SC-004 | research R3 | PR-001 |
| SC-005 | research R8, R9 | covered |
| SC-006 | research R11 | PR-011 |

## Assumptions challenged

- workmux 0.1.268 runs `pre_remove` under `--force`. This is unverified, and
  the plan schedules the real removal in quickstart step 4 before the change
  goes to review, which is the right place for it.
- `git ls-files --others` lists a nested repository once as `dir/`, and an
  untracked symlink as a path. Both hold on git 2.44.0, including a nested
  repository inside an untracked parent (`outer/inner/`) and a symlink to a
  folder.
- A squash-merged branch passes the merge check. This holds while trunk leaves
  the branch's lines alone, and fails after a later edit to the same line
  (PR-001).
- Neither repository in use has `|| true` in `pre_remove`. This holds. This
  repository uses the block form, and pfms uses
  `! command -v wfctl >/dev/null || wfctl archive-specs …`.
- The two branches agree on `StoreResult`. #359's plan doesn't support this
  (PR-003).
- The hook can't see `--keep-branch`. This is unverified, and the spec accepts
  the consequence.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- The implementation order writes the two `ls-files` tests before any copy
  code, so the assumption R5 rests on is checked before anything is built on
  it.
- Putting `stops_removal` on the result rather than in the hook is the right
  shape. PR-002 asks only that phase 1 uses it too.
- The test asserting that the template's `pre_remove` block contains
  `REMOVE_HOOK` closes the drift that left `|| true` in the template.
- R13 carries forward the escaping and `soft_wrap` rules that keep a printed
  manual route pasteable.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
