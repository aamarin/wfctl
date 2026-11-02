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
