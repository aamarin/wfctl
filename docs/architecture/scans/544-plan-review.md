# Plan review scan for #544

## Review 2026-11-02T16:29Z

- Verdict: satisfied
- Reviewed: plan.md d9975abd517a0829afefa9b9c0fa8c1159dee42f, spec.md 38b4e93408fb98cc12027a872d9f6c1d53186858, .specify/memory/constitution.md absent, design.md 4ec1a176dddf9c8559af96bc8a3b7bafbcb43fff, docs/architecture/contexts-are-packages.md 721846ce98f327776d7667b56fd6349a561a8550, docs/architecture/domain/wfctl.md e8364d902f83f1bebc79d8d55e103d1bc2d2b441, research.md d6f0da4a587ab9725b3c1791bebf77a8f2220533, data-model.md b3b658140932d6716616212c4d3c0dccd12f93bf, quickstart.md 07a90ac42d16d447240d016fa570c647c86bf202, contracts/baseline.md 61471aa12f66b721f4d7505e62bed6bce3e9327e, contracts/failure-output.md d86bed44e1c163ff2ad04bb271e1c547dcfab8b8, checklists/requirements.md ca7200ba81541e45366a10151368381417d90d32, exceptions/architecture-records/brainstorm.software-design.md 1899c8677c81446cb9527810b27b2c6f75ad9613
- Review type: full (no earlier review and no plan copy)
- Open: BLOCKER 0 · MAJOR 7 · MINOR 8 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/544-package-per-context/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-003, PR-010, PR-013, PR-014) |
| Requirements and traceability | Outstanding (PR-009, PR-015) |
| Architecture and boundaries | Outstanding (PR-006, PR-012) |
| Adversarial implementation and verification | Outstanding (PR-001, PR-002, PR-008, PR-011) |
| Security and reliability | Outstanding (PR-004, PR-005, PR-007) |

### Findings

- **PR-001, MAJOR, open.** The suite's test against the real tree can't run the same check that `verify` and CI run. With the comparison against `main` included, it fails on this branch until a person approves, and it fails in CI's shallow `test` job on every branch. Without the comparison, it no longer meets `spec.md §FR-013`. Stands because `plan.md` Phase C item 6 and Phase D item 13 don't say which form the test runs.
- **PR-002, MAJOR, open.** The plan doesn't describe the git state the CI step runs in. The `lint` checkout is shallow, `actions/checkout` sets no `origin/HEAD`, and on a PR `HEAD` is GitHub's merge commit. Stands because `plan.md` Phase C item 6, Phase D item 12, and `research.md` R5 don't say whether a failed merge-base or trunk lookup fails the check or skips the comparison.
- **PR-003, MAJOR, open.** The domain page at the merge base with `origin/main` has no `Package` column, no Shared packages list, and no Worktree guard row, so the strict `read_domain` rejects it. Stands because `plan.md` Phase C item 6 gives a fallback only for a missing baseline, and arrows compared by package name are undefined across a package rename.
- **PR-004, MAJOR, open.** `research.md` R11 runs `main`'s copy of the check script, but the `lint` job runs under `pull_request`, so a branch can edit `ci.yml` to run its own copy or drop the step. Stands because `plan.md` Phase D item 12 keeps the check in `lint`, while `review.yml` uses `pull_request_target` to prevent exactly this.
- **PR-005, MAJOR, open.** Because CI runs `main`'s copy and `lint` is required, a branch whose fix is in the check script can't merge. Stands because the plan names no recovery path, and the moves under #671 are the likely first case.
- **PR-006, MAJOR, open.** The Shared packages table is never compared with `main`, so a branch can add a third shared package and move code into it without approval. Stands because `plan.md` Phase C item 6 compares only the baseline and the Context Map, which leaves `spec.md §FR-002` and rule 4 of `contexts-are-packages.md` unenforced.
- **PR-007, MAJOR, open.** The plan doesn't say how an installed `wfctl arch approve-imports` loads the repo's script, which side computes the digest, or which copy runs. Stands because, as written in `plan.md` Phase C items 8 and 9, the person runs the branch's script in their own terminal, where the agent could have edited it and the guard doesn't run.
- **PR-008, MINOR, open.** The approval pushes the notes ref the way a sign-off does, but nothing reruns the failed `lint` job, so the required check stays red. Stands because `plan.md` Phase C item 8 doesn't call the rerun that `wfctl/_review_notes.py` already has.
- **PR-009, MINOR, open.** Rule 1 allows every import from a wiring module, and the rules apply in order, so rule 6, the negative path of `spec.md §FR-006`, can never fire. Stands because `plan.md` Phase B item 4.5 lists them in that order.
- **PR-010, MINOR, open.** `wfctl/__init__.py` has no placement line. Stands because `plan.md` Phase B says 40 placement lines while `research.md` R7 places 39 modules, so the shipped baseline would fail SC-001.
- **PR-011, MINOR, open.** The plan doesn't say that `from wfctl.evidence import _status` counts as an import of a private module. Stands because its module part names the package, so `plan.md` Phase B item 4.4 lets it pass rule 3.
- **PR-012, MINOR, open.** Treating `_entry.py` as wiring is a sound reading, but it widens `spec.md §FR-006` and rule 5 of the record, which name only `cli.py`. Stands because the change is recorded only in `research.md` R8, which already says the walkthrough confirms it.
- **PR-013, MINOR, open.** `spec.md §FR-011` says to draw failures as shown in `design.md`, and those drawings still show `wfctl.evidence.public` and a "public module", which the amended record replaced. Stands because the plan doesn't say that `contracts/failure-output.md`, which has it right, governs.
- **PR-014, MINOR, open.** `plan.md` Phase A calls `| Package | Pattern | Holds |` a two-column table, but it has three columns. The vocabulary row names 2 of the 4 reserved names in `spec.md §FR-012`. Stands because Phase A items 1 and 2 still say so.
- **PR-015, MINOR, open.** The release note category `none` understates the change, since every install gains a new command and a new guard refusal. Stands because `research.md` R9 picks `none`, while the Releasing section of `AGENTS.md` classes a new command as `addition`.

## Review 2026-11-02T16:44Z

- Verdict: satisfied
- Reviewed: plan.md c16ae0853e36f11a6fe7dc6b6030fb733c2892ed, spec.md 060b0ca73e917a2226f39e7f5c2cfb1716c02ed2, .specify/memory/constitution.md absent, design.md 4ec1a176dddf9c8559af96bc8a3b7bafbcb43fff, docs/architecture/contexts-are-packages.md 721846ce98f327776d7667b56fd6349a561a8550, docs/architecture/domain/wfctl.md e8364d902f83f1bebc79d8d55e103d1bc2d2b441, research.md 598dec050c0f0faac85206a2ff66b1d3e7e55e60, data-model.md a06d491cc6098b0ca0fc230f3f1c8d55e5112f50, quickstart.md 8f200a771c4227e7dba0481d00b08ebcde60f2fe, contracts/baseline.md 61471aa12f66b721f4d7505e62bed6bce3e9327e, contracts/failure-output.md d86bed44e1c163ff2ad04bb271e1c547dcfab8b8, checklists/requirements.md ca7200ba81541e45366a10151368381417d90d32, exceptions/architecture-records/brainstorm.software-design.md 1899c8677c81446cb9527810b27b2c6f75ad9613, plan-review.plan.md d9975abd517a0829afefa9b9c0fa8c1159dee42f (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 3 · MINOR 5 · Fixed since the earlier review: 15
- Detail: /Users/andremarin/Development/wfctl-specs/544-package-per-context/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-021; PR-003, PR-010, PR-013, PR-014 fixed) |
| Requirements and traceability | Outstanding (PR-023; PR-009, PR-015 fixed) |
| Architecture and boundaries | Outstanding (PR-016, PR-018; PR-006, PR-012 fixed) |
| Adversarial implementation and verification | Outstanding (PR-022; PR-001, PR-002, PR-008, PR-011 fixed) |
| Security and reliability | Outstanding (PR-017, PR-019, PR-020; PR-004, PR-005, PR-007 fixed) |

### Findings

- **PR-001 to PR-015, fixed.** The revision split the script into a rule check, which runs everywhere with the branch's copy, and an approval check, which runs only in the `review` job under `pull_request_target` and in `wfctl arch approve-imports`, both with `main`'s copy. It also required `--base`, failed closed on any git error, compared arrows by context name, counted shared packages as additions, reran the `review` job after an approval, and fixed the eight smaller mismatches. `spec.md` FR-006, FR-011, FR-013, and FR-015 changed to match.
- **PR-016, MAJOR, open.** `plan.md §Phase D` has this branch's additions approved by merging the PR, which `spec.md §FR-015` and the record's Decision don't allow. Stands because nothing makes the merge a person's act: the guard refuses a merge only while reviews are pending, so an agent could merge the 47 baseline lines and the new arrow.
- **PR-017, MAJOR, open.** On a stacked PR, `approve-imports` compares against the trunk from `origin/HEAD`, while the `review` job compares against `origin/$BASE_REF` and runs the base branch's copy of the script. Stands because the digests then disagree, and CI runs the parent branch's copy, which an agent may have edited.
- **PR-018, MAJOR, open.** Arrows compare by context name, so a branch can change which package a context maps to with no approval. Stands because, after the moves, swapping two Package cells in the domain page re-places whole directories with no file moving, and `plan.md §Phase B item 4.3` doesn't say how it treats a directory the table doesn't name.
- **PR-019, MINOR, open.** The `review` step passes when `main` has no copy of the script, and that code stays in `review.yml`. Stands because once a PR deleting or renaming the script merges, the check skips silently, which `research.md §R5` rules out.
- **PR-020, MINOR, open.** In the `review` job the rule check reads `pr`'s working tree, which follows symlinks, and failures quote the line they read. Stands because the default `persist-credentials` leaves the read-only token in `pr/.git/config`.
- **PR-021, MINOR, open.** `plan.md §Summary` and the third Complexity Tracking row still say a rule fix lands with the change that needs it. Stands because `§Phase D item 12` runs `main`'s rule check in `review`, and `§Phase E item 14` says to land the fix first.
- **PR-022, MINOR, open.** `plan.md §Phase B item 4` doesn't say the rule check finds the tree from the current directory, which `§Phase D item 12` depends on. Stands because a script that resolves from its own path would check `trusted` in the `review` job and pass every PR, and no test covers the step.
- **PR-023, MINOR, open.** `plan.md §Phase B item 4.5` rule 1 refuses `wiring` importing a module inside a "moved package", while FR-006 says "a context's package". Stands because once `core` and `tracker` move, `cli.py` would be refused their internals while every context may import them.

## Review 2026-11-02T20:14Z

- Verdict: satisfied
- Reviewed: plan.md cea3be57586b4a413abdfe83c26304852a84d52e, spec.md 1390b33061dabdf8c9de5c53b760281a3279729b, .specify/memory/constitution.md absent, design.md 4ec1a176dddf9c8559af96bc8a3b7bafbcb43fff, docs/architecture/contexts-are-packages.md cf0d19c54b113499d0bc1c70fcaf7027e1eeae2e, docs/architecture/domain/wfctl.md e8364d902f83f1bebc79d8d55e103d1bc2d2b441, research.md 0c9d4acd82e42a8604229d399e80c3a1db10b859, data-model.md 13efa432105f737f7e13c221a67734bfbb44824f, quickstart.md 8f200a771c4227e7dba0481d00b08ebcde60f2fe, contracts/baseline.md 61471aa12f66b721f4d7505e62bed6bce3e9327e, contracts/failure-output.md 880072639cbfa58ca664b9a4104dfa5bedf03691, checklists/requirements.md ca7200ba81541e45366a10151368381417d90d32, exceptions/architecture-records/brainstorm.software-design.md 1899c8677c81446cb9527810b27b2c6f75ad9613, plan-walkthrough.md e20d1eba2965f05fb46faece1c49bb9fb33663a3, plan-review.plan.md c16ae0853e36f11a6fe7dc6b6030fb733c2892ed (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 5 · Fixed since the earlier review: 8
- Detail: /Users/andremarin/Development/wfctl-specs/544-package-per-context/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-028; PR-021 fixed) |
| Requirements and traceability | Outstanding (PR-029; PR-023 fixed) |
| Architecture and boundaries | Outstanding (PR-024; PR-016, PR-018 fixed) |
| Adversarial implementation and verification | Outstanding (PR-025, PR-027; PR-022 fixed) |
| Security and reliability | Outstanding (PR-026; PR-017, PR-019, PR-020 fixed) |

### Findings

- **PR-001 to PR-015, fixed.** As the earlier review recorded.
- **PR-016, MAJOR, fixed.** Fixed by `spec.md §FR-015` and the record's Log, which name this branch as the one exception, and by `plan.md §Phase D`, whose closing paragraphs make the hand merge the user's act.
- **PR-017, MAJOR, fixed.** Fixed by `plan.md §Phase D item 12` and `research.md §R5` and `§R11`. CI and `approve-imports` both compare against the default branch, and CI reads that branch's copy of the script.
- **PR-018, MAJOR, fixed.** Fixed by `plan.md §Phase C item 6.3.4`, which lists a changed context-to-package pair as an addition, and `§Phase B item 4.3.7` and `spec.md §FR-008`, which fail a module under an unlisted directory.
- **PR-019, MINOR, fixed.** Fixed by `plan.md §Phase D item 12`. The pass fails once the default branch's `wfctl.json` lists the check.
- **PR-020, MINOR, fixed.** Fixed by `plan.md §Phase B item 4.10` and a test in item 13. A symlinked input fails without printing its target.
- **PR-021, MINOR, fixed.** Fixed by `plan.md §Summary` and the Complexity Tracking row, which now say a rule fix lands in its own PR first.
- **PR-022, MINOR, fixed.** Fixed by `plan.md §Phase B item 4.9` and a test in item 13. Both modes take the tree from the current directory.
- **PR-023, MINOR, fixed.** Fixed by `plan.md §Phase B item 4.5`. Rule 1 says "a context's package", and a shared package's modules are open to every module.
- **PR-024, MAJOR, open.** No person approves a change to `check_imports.py` itself. `plan.md §Phase C item 6.3.5` gates the `WIRING` list, but not the package-data skip list in `§Phase B item 4.3.5` or the rule logic. Stands because a PR that only edits the script passes the default branch's copy, and the guard lets an agent merge it once the review groups have run.
- **PR-025, MINOR, open.** `plan.md §Phase D item 12`'s step never runs on this PR, because `pull_request_target` runs `main`'s `review.yml`, which doesn't have it. Stands because the closing paragraph says the step passes here, and the step doesn't say how it tells a missing path from a failed `git show`.
- **PR-026, MINOR, open.** `plan.md §Phase D items 12.1 and 12.2` and `§Phase C item 8.2` don't say where the temporary copy of the trusted script is written. Stands because a copy inside `pr/` would put the PR's files first on `sys.path`, so a PR's `ast.py` would run with the job's token.
- **PR-027, MINOR, open.** `plan.md §Phase C item 8.1` fetches nothing, and `trunk_refs` prefers a declared trunk. Stands because a stale `origin/main` or a declared trunk gives a digest CI never matches.
- **PR-028, MINOR, open.** `research.md §R4` Limit says `approve-imports` exits 0 when the trunk has no script. Stands because `plan.md §Phase C item 8.4` now says it exits 1.
- **PR-029, MINOR, open.** The record's approval paragraph names only baseline lines and arrows, and its title still says "one public module". Stands because `spec.md §FR-015` now lists five kinds of addition, and `plan.md §Phase A item 3` describes as future work a record edit already committed.

## Review 2026-11-02T20:25Z

- Verdict: satisfied
- Reviewed: plan.md 7d654a2b01627efddcdcb0cd1f43d464e4b05a0f, spec.md b38fc30d8019a4cad0dd536f77e7587677a67d46, .specify/memory/constitution.md absent, design.md 4ec1a176dddf9c8559af96bc8a3b7bafbcb43fff, docs/architecture/contexts-are-packages.md b4d0809e48486882ae44761c0a52b61d8c110a25, docs/architecture/domain/wfctl.md e8364d902f83f1bebc79d8d55e103d1bc2d2b441, research.md 63cc5509e869d5d2fbb82294df200e94a34fd00b, data-model.md a86261b2553c26d483a1f5b1372763923f86d311, quickstart.md 8f200a771c4227e7dba0481d00b08ebcde60f2fe, contracts/baseline.md 61471aa12f66b721f4d7505e62bed6bce3e9327e, contracts/failure-output.md 407d4a7d1e5571a3195c9331e78704b1aac8813e, checklists/requirements.md ca7200ba81541e45366a10151368381417d90d32, exceptions/architecture-records/brainstorm.software-design.md 1899c8677c81446cb9527810b27b2c6f75ad9613, plan-walkthrough.md e20d1eba2965f05fb46faece1c49bb9fb33663a3, plan-review.plan.md cea3be57586b4a413abdfe83c26304852a84d52e (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 2 · MINOR 2 · Fixed since the earlier review: 6
- Detail: /Users/andremarin/Development/wfctl-specs/544-package-per-context/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Resolved (PR-028 fixed) |
| Requirements and traceability | Resolved (PR-029 fixed) |
| Architecture and boundaries | Outstanding (PR-030; PR-024 fixed) |
| Adversarial implementation and verification | Outstanding (PR-031, PR-033; PR-025, PR-027 fixed) |
| Security and reliability | Outstanding (PR-030, PR-031, PR-032; PR-026 fixed) |

### Findings

- **PR-001 to PR-023, fixed.** As the earlier reviews recorded, with no regression from this revision.
- **PR-024, MAJOR, fixed.** Fixed by `plan.md §Phase C item 6.3.5`. Any change to the script is one addition keyed by its blob hash, which covers `WIRING`, the package-data list, the rules, and a deleted script.
- **PR-025, MINOR, fixed.** Fixed by `plan.md §Phase D item 12`. The bootstrap pass is gone, the step checks that the ref resolves, and the closing paragraph says the step never runs on this branch's own PR.
- **PR-026, MINOR, fixed.** Fixed by `plan.md §Phase C item 8.2` and `§Phase D item 12.2`. Both callers write the trusted copy outside the repository and run it with `-I`.
- **PR-027, MINOR, fixed.** Fixed by `plan.md §Phase C item 8.1`. `approve-imports` fetches the default branch, never uses a declared `trunk`, and both callers print the merge base.
- **PR-028, MINOR, fixed.** Fixed by `research.md §R4`, which now says exit 1.
- **PR-029, MINOR, fixed.** Fixed by the record's title and approval paragraph, and by `plan.md §Phase A item 3`, which creates no task.
- **PR-030, MAJOR, open.** A PR that changes only `.github/workflows/review.yml` and drops the new step passes `main`'s step, and the guard lets an agent merge it once the panel has run. Stands because the plan neither gates the workflow file nor states it as a limit, and the guard and notes files are exposed the same way.
- **PR-031, MAJOR, open.** `approve-imports` run as `uv run wfctl` in the branch's worktree is branch code, so an edited `cli.py` could show the person fewer additions than the digest it writes. Stands because the plan doesn't say which wfctl the person runs, and an installed `wfctl` has no `approve-imports` until a release ships it.
- **PR-032, MINOR, open.** The person sees a script change only as a hash, never as a diff, and `contracts/failure-output.md` shows a 12-character blob and no `script deleted` line. Stands because `data-model.md` names the full hash.
- **PR-033, MINOR, open.** The approval is computed from local `HEAD`, and nothing checks that it is the PR's head. Stands because the check then stays red with a matching merge base and no hint why.

## Review 2026-11-02T21:04Z

- Verdict: satisfied
- Reviewed: plan.md 06247b039418604ea4cb419ea4d3fa5ed398be2c, spec.md c084e7e9dd86bf04b6f4194a20174898d7ddea3f, .specify/memory/constitution.md absent, design.md 4ec1a176dddf9c8559af96bc8a3b7bafbcb43fff, docs/architecture/contexts-are-packages.md d9ca14825d4977d442b38c3bef5347ec142ee325, docs/architecture/domain/wfctl.md e8364d902f83f1bebc79d8d55e103d1bc2d2b441, research.md 4018f91a2992f509a3c51c1cc18bfb6845860c1a, data-model.md f698540812e27c660497d6679f80248eb40d7ec9, quickstart.md 8f200a771c4227e7dba0481d00b08ebcde60f2fe, contracts/baseline.md 61471aa12f66b721f4d7505e62bed6bce3e9327e, contracts/failure-output.md b5a1c6832446a6c9adec9d7e3c70a85e65db2e5d, checklists/requirements.md ca7200ba81541e45366a10151368381417d90d32, exceptions/architecture-records/brainstorm.software-design.md 1899c8677c81446cb9527810b27b2c6f75ad9613, plan-walkthrough.md e20d1eba2965f05fb46faece1c49bb9fb33663a3, plan-review.plan.md 7d654a2b01627efddcdcb0cd1f43d464e4b05a0f (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 3 · MINOR 4 · Fixed since the earlier review: 4
- Detail: /Users/andremarin/Development/wfctl-specs/544-package-per-context/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Outstanding (PR-035, PR-039) |
| Architecture and boundaries | Outstanding (PR-034, PR-035; PR-030 fixed) |
| Adversarial implementation and verification | Outstanding (PR-036, PR-038, PR-040; PR-031, PR-033 fixed) |
| Security and reliability | Outstanding (PR-034, PR-036, PR-037; PR-032 fixed) |

### Findings

- **PR-001 to PR-029, fixed.** As the earlier reviews recorded, with no regression.
- **PR-030, MAJOR, fixed.** Fixed by `plan.md §Phase C item 6.3.5`. `review.yml` and the guard and notes modules are on `TRUSTED`.
- **PR-031, MAJOR, fixed.** Fixed by `plan.md §Phase C item 8.1` and `§Phase E item 14`. The person runs the installed `wfctl`.
- **PR-032, MINOR, fixed.** Fixed by `plan.md §Phase C item 8.5` and `contracts/failure-output.md`. A changed trusted file's diff is printed, and the line carries the full blob hash.
- **PR-033, MINOR, fixed.** Fixed by `plan.md §Phase C item 8.2`. The command refuses unless `HEAD` equals the upstream.
- **PR-034, MAJOR, open.** `TRUSTED` misses `_entry.py`, `_settings.py`, and `cli.py`'s `GUARD_HOOK_COMMAND`, which decide whether the guard runs, and the modules the guard imports. Stands because the reason for leaving files off holds for `cli.py` only.
- **PR-035, MAJOR, open.** Leaving `cli.py` off contradicts `spec.md §FR-015`, and neither the spec nor the record names the exception. Stands because `cli.py` also holds the command name the guard matches and the hook command.
- **PR-036, MAJOR, open.** An agent can call `approve_imports` from `uv run python -c`, which the guard doesn't match, and the function does no checking. Stands because `plan.md §Phase C item 9` says the hand-written route is closed, and the existing person-only command for review groups has the same gap today.
- **PR-037, MINOR, open.** The worktree-source refusal runs in the branch's own `_review_notes.py`, so a tampered branch skips it, and the plan doesn't compare resolved paths. Stands because only the instruction to run the installed `wfctl` protects the person.
- **PR-038, MINOR, open.** `plan.md §Phase C item 8.2` doesn't say what happens with no upstream, or an upstream of `origin/main`. Stands because it should compare against `origin/<current branch>`.
- **PR-039, MINOR, open.** `spec.md §FR-015` and the record's Log say the bootstrap exception approves "its baseline", and this branch also adds or changes four trusted files. Stands because the user's pre-merge check covers only the placement lines.
- **PR-040, MINOR, open.** `TRUSTED` is keyed by path, and the #671 moves relocate four trusted modules. Stands because a file absent at the merge base and present at `HEAD` is undefined.

## Review 2026-11-02T21:15Z

- Verdict: satisfied
- Reviewed: plan.md 8eaa11fa456f8e623ca9d65b6b1b9e91ecfcaba1, spec.md eb89fbd20e94ffcbc733a0b6f7d76fdf33a85b01, .specify/memory/constitution.md absent, design.md 4ec1a176dddf9c8559af96bc8a3b7bafbcb43fff, docs/architecture/contexts-are-packages.md 0d88f1de34373a012ff4c913aaf4c73c67ab925e, docs/architecture/domain/wfctl.md e8364d902f83f1bebc79d8d55e103d1bc2d2b441, research.md 9fcbf2c459b70d3882c3b2cee93b808725be4dbf, data-model.md fc1ed1480fafc43139d0ba212f422ddc7b03c66b, quickstart.md 8f200a771c4227e7dba0481d00b08ebcde60f2fe, contracts/baseline.md 61471aa12f66b721f4d7505e62bed6bce3e9327e, contracts/failure-output.md 709a35cef432950850cc1b67bc82ecd537f5d884, checklists/requirements.md ca7200ba81541e45366a10151368381417d90d32, exceptions/architecture-records/brainstorm.software-design.md 1899c8677c81446cb9527810b27b2c6f75ad9613, plan-walkthrough.md e20d1eba2965f05fb46faece1c49bb9fb33663a3, plan-review.plan.md 06247b039418604ea4cb419ea4d3fa5ed398be2c (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 1 · Fixed since the earlier review: 7
- Detail: /Users/andremarin/Development/wfctl-specs/544-package-per-context/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-041) |
| Requirements and traceability | Outstanding (PR-041; PR-039 fixed) |
| Architecture and boundaries | Resolved (PR-034, PR-035 fixed) |
| Adversarial implementation and verification | Resolved (PR-038, PR-040 fixed) |
| Security and reliability | Resolved (PR-036, PR-037 fixed) |

### Findings

- **PR-001 to PR-033, fixed.** As the earlier reviews recorded, with no regression from the narrowing.
- **PR-034, MAJOR, fixed.** Fixed by `plan.md §Phase C item 6.3.5`. `TRUSTED` holds the two files CI takes from the default branch, and the guard and its hook fall under the stated limit.
- **PR-035, MAJOR, fixed.** Fixed by `spec.md §FR-015` and `plan.md §Phase C items 6.3.5 and 7`, which gate the same two files and say where the terminal check lives.
- **PR-036, MAJOR, fixed.** Fixed by `plan.md §Phase C items 7 and 9`. Item 9 no longer claims the route is closed, and the repeated terminal check narrows the gap.
- **PR-037, MINOR, fixed.** Fixed by `plan.md §Phase C item 8.1`, which compares resolved paths and catches an honest mistake only.
- **PR-038, MINOR, fixed.** Fixed by `plan.md §Phase C item 8.2`, which compares against `origin/<current branch>` and refuses when it doesn't exist.
- **PR-039, MINOR, fixed.** Fixed by `spec.md §FR-015`, the record's Log, and the bootstrap paragraph, which cover this branch's two trusted files.
- **PR-040, MINOR, fixed.** Fixed by `plan.md §Phase C item 6.3.5`. A file absent at the merge base counts as changed, and both paths sit under `.github/`.
- **PR-041, MINOR, open.** Four sentences still state the stronger claim the limit replaced: the failure contract's "an agent can't approve them", Complexity Tracking row 2, the Constitution Check's `review-record-in-git-notes` row, and `research.md §R4`'s rationale. Stands because the contract text is printed to the agent that hit the failure.

## Review 2026-11-02T21:26Z

- Verdict: satisfied
- Reviewed: plan.md 9426017ebf75890336e4526d89921639e2f5a7c7, spec.md eb89fbd20e94ffcbc733a0b6f7d76fdf33a85b01, .specify/memory/constitution.md absent, design.md 4ec1a176dddf9c8559af96bc8a3b7bafbcb43fff, docs/architecture/contexts-are-packages.md 0d88f1de34373a012ff4c913aaf4c73c67ab925e, docs/architecture/domain/wfctl.md e8364d902f83f1bebc79d8d55e103d1bc2d2b441, research.md fec00fa13992b9d6dc7745f674b3d2a01c6e442f, data-model.md fc1ed1480fafc43139d0ba212f422ddc7b03c66b, quickstart.md 8f200a771c4227e7dba0481d00b08ebcde60f2fe, contracts/baseline.md 61471aa12f66b721f4d7505e62bed6bce3e9327e, contracts/failure-output.md 3fe11b41764fe2a40e96a11c3dff84f9215a45fe, checklists/requirements.md ca7200ba81541e45366a10151368381417d90d32, exceptions/architecture-records/brainstorm.software-design.md 1899c8677c81446cb9527810b27b2c6f75ad9613, plan-walkthrough.md e20d1eba2965f05fb46faece1c49bb9fb33663a3, plan-review.plan.md 8eaa11fa456f8e623ca9d65b6b1b9e91ecfcaba1 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 0 · Fixed since the earlier review: 1
- Detail: /Users/andremarin/Development/wfctl-specs/544-package-per-context/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Resolved (PR-041 fixed) |
| Requirements and traceability | Resolved (PR-041 fixed) |
| Architecture and boundaries | Clear |
| Adversarial implementation and verification | Clear |
| Security and reliability | Clear |

### Findings

- **PR-001 to PR-040, fixed.** As the earlier reviews recorded, with no regression from this revision.
- **PR-041, MINOR, fixed.** Fixed by `contracts/failure-output.md`, which now says only the user approves the additions, and by `plan.md §Complexity Tracking` row 2, `plan.md §Constitution Check`'s `review-record-in-git-notes` row, and `research.md §R4`'s rationale, which each point at the limit in plan item 6.3.5.
- No new finding. The revision also adds a detached `HEAD` refusal to `plan.md §Phase C item 8.2`, which the review checked and found consistent.

## Review 2026-11-02T22:26Z

- Verdict: satisfied
- Reviewed: plan.md 093b12ca362a6366c8689a6818c6fb685050296e, spec.md fc5b1b331bdf85e67cf3c044810d29ffdf0bc8a2, .specify/memory/constitution.md absent, design.md 4ec1a176dddf9c8559af96bc8a3b7bafbcb43fff, docs/architecture/contexts-are-packages.md 0d88f1de34373a012ff4c913aaf4c73c67ab925e, docs/architecture/domain/wfctl.md e8364d902f83f1bebc79d8d55e103d1bc2d2b441, research.md fec00fa13992b9d6dc7745f674b3d2a01c6e442f, data-model.md fc1ed1480fafc43139d0ba212f422ddc7b03c66b, quickstart.md 8f200a771c4227e7dba0481d00b08ebcde60f2fe, contracts/baseline.md 61471aa12f66b721f4d7505e62bed6bce3e9327e, contracts/failure-output.md 3fe11b41764fe2a40e96a11c3dff84f9215a45fe, checklists/requirements.md ca7200ba81541e45366a10151368381417d90d32, checklists/analysis-report.md b3cc03a189181a50c0bd49813e6cb0907520b07e, exceptions/architecture-records/brainstorm.software-design.md 1899c8677c81446cb9527810b27b2c6f75ad9613, plan-walkthrough.md e20d1eba2965f05fb46faece1c49bb9fb33663a3, tests/test_review_workflow.py a6d5264c9b6ab7173753fb6efa2974158cea5b82, .github/workflows/review.yml a06f9be1d38aeeabd4b7825744137a9c3be45ebb, plan-review.plan.md 9426017ebf75890336e4526d89921639e2f5a7c7 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 1 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/544-package-per-context/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Clear |
| Architecture and boundaries | Clear |
| Adversarial implementation and verification | Outstanding (PR-042) |
| Security and reliability | Outstanding (PR-042) |

### Findings

- **PR-001 to PR-041, fixed.** As the earlier reviews recorded. Analyze's edits to `plan.md` items 4.1 and 13 and to `spec.md` SC-002 reopen none of them.
- **PR-042, MINOR, open.** `plan.md §Phase C item 12.3` runs the new script in the `pr` checkout, and item 13 relies on `tests/test_review_workflow.py` to show that the `review` job runs nothing from that checkout. That test only allows `uv run --project ../trusted wfctl check reviews --base "$BASE_REF"` in a step with `working-directory: pr`. Stands because the plan doesn't say how the new step reaches `pr`. Setting `working-directory: pr` fails the test, and a `cd pr` inside `run` puts the step outside what the test checks. Either way, the plan should state what the `review` job may now run, since that job runs with the base repository's token.
