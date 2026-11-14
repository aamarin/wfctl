# Plan review scan for #40

## Review 2026-10-15T11:22Z

- Verdict: satisfied
- Reviewed: plan.md 30652c4b4f26ff32f488196e5fdef6406e38d342, spec.md a4f526723c5c4a397b6bda38d5e4433098617c3c, .specify/memory/constitution.md absent, design.md b07cc23e4928d8826b3882ec507d96a444e52da5, docs/architecture/design/40-archive-is-a-command-group.md 79ae3a3db168a99972214eaa5414aedec74e764c, docs/architecture/worktree-removal-requires-saved-work.md d1ed774aa90a28172cb415ef577d2c0b48dcadf1, docs/architecture/removal-copy-destinations.md dbaf6e77c11bb079a674879ced417c3a74e6050e, research.md 515d3170c3af08e0100f5501c03357e7662b8e07, data-model.md c4a292059d76ce2958e0dc7b1f8a9c98731f5a7d, contracts/cli.md 33637bc90f114318e64157ff95ad0abff533bf63, quickstart.md 9c0ed2bd50622b92599aab31db2d239d26c21177, ../../../wfctl-specs/359-push-specs-to-trunk/plan.md 51905313e32de76891bfd0e7addbd656ac0acedd, ../../../wfctl-specs/359-push-specs-to-trunk/data-model.md 6ea70cff0e8568cd36ef2e88a3664910f3b8ad0f, ../../../wfctl-specs/359-push-specs-to-trunk/research.md 9d45be6f7405e38e83ae923af49d616c9b359ab5
- Review type: full (no plan copy from an earlier review)
- Open: BLOCKER 0 · MAJOR 4 · MINOR 9 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/40-save-uncommitted-on-remove/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-005, PR-008) |
| Requirements and traceability | Clear |
| Architecture and boundaries | Outstanding (PR-002, PR-003, PR-006, PR-009) |
| Adversarial implementation and verification | Outstanding (PR-001, PR-007, PR-010, PR-011, PR-012) |
| Security and reliability | Outstanding (PR-004, PR-013) |

### Findings

- **PR-001, MAJOR, open.** The merge check stops removal of a branch that was squash-merged when trunk has since changed the same lines. The reviewer reproduced it on git 2.44, where `git merge-tree` exits 1 with a conflict. It stands because SC-004 promises the check is right in every case, and the planned test only builds the case that passes.
- **PR-002, MAJOR, open.** Phase 1 of the hook works out the layout itself and decides the spec-file stop from `_copy_out.plan`. It stands because the plan also says the stop lives only on `StoreResult.stops_removal`, which matches FR-003, and research R2 doesn't say that phase 2 reads `stops_removal` before the `unsaved/` copy.
- **PR-003, MAJOR, open.** This plan calls `store(worktree, branch, overwrite)`, and #359's plan defines `store(spec_dir, branch, repo_root)`. It stands because #359's data model names no fields, so research R1 and R7 claim an agreement on field names that nothing backs, and R12's merge-order checks don't cover the signature.
- **PR-004, MAJOR, open.** The plan doesn't say what happens when `git ls-files --others` fails, or when `save_on_remove` can't be read. It stands because the two readings have opposite results. As an unanswerable check, or caught by the catch-all, the hook lets removal through and every untracked file is deleted. As a failed copy, it stops the removal.
- **PR-005, MINOR, open.** Running the hook by hand in the main checkout gives `not_applicable` with `inside` true, which the data model says can't happen. It stands because the hook would then exit 1 and print a "remove anyway" command aimed at the main checkout.
- **PR-006, MINOR, open.** The new `_paths.is_main_checkout` answers the same question as the existing `_paths.is_bare_layout`, from a different git fact. It stands because the plan doesn't say why a second test is needed. The two already disagree on a separate-gitdir clone, which the plan's test reads as bare and `is_bare_layout` does not. The result there is harmless, since the spec files are saved under `unsaved/`, but the plan doesn't name it.
- **PR-007, MINOR, open.** The plan has no rule for when untracked files, `save_on_remove` folders, and the spec dir overlap. It stands because a listed folder that isn't gitignored is copied twice, `copytree` raises `FileExistsError`, and every removal stops. Listing `specs/` also breaks FR-018.
- **PR-008, MINOR, open.** Research R3 prints every commit that is on no remote, and in a repo with no remote that is the whole history, trunk included. It stands because the data model implies a filter that R3 never applies. The suggested fix is to exclude trunk in step 1.
- **PR-009, MINOR, open.** The change list misses three places that describe the old hook. They are the seeded template's comment that a teardown hook must never stop a removal, the comment in this repo's `.workmux.yaml`, and the `ponytail-debt.md` row. It stands because the template comment is seeded into every new repository, and would tell its reader the hook never stops a removal, which is the behaviour this feature removes.
- **PR-010, MINOR, open.** The copy-out assumes `specs/` is gitignored in the main checkout. It stands because in a repo that commits `specs/`, the copies land there as untracked files and block the next merge. The reviewer checked that git refuses the merge even when the files are identical.
- **PR-011, MINOR, open.** SC-006, which says removal never prints "durable", is tested only on the `copied` outcome. It stands because `not_applicable` is the outcome that printed "durable" before, and it has no test.
- **PR-012, MINOR, open.** Quickstart step 4 uses the handle `40-scratch`, which carries issue #40's key. It stands because the removal hooks would then move #40's board column, and the spec dir resolves to #40's own, so the step never exercises the copy-out.
- **PR-013, MINOR, open.** `typer.Exit` is a subclass of `Exception`, so a stop raised inside the catch-all would be swallowed and exit 0, letting the removal through. It stands because research R8 doesn't mention it, though the planned exit-code tests would catch it.
