# Plan review scan for #759

## Review 2026-11-14T03:17Z

- Verdict: satisfied
- Reviewed: plan.md e898a78a17e60c9380870044d967ae271a6e5535, spec.md 6410e1ec65515dd36c1ac7e41ddd6cca3958f031, .specify/memory/constitution.md absent, design.md e6fb1d95b1f7883470001192b1269f88fc931458, docs/architecture/design/759-scan-names-its-folder.md 2465719147f6b3a3a3071cef3c02bae207558e81, docs/architecture/scans-live-in-spec-folder.md 6ba8ee6b8f6ea703939fad101702eb43415a9f99, AGENTS.md 81e97f405ca993195c2450a3dffeed74c67dd18a, research.md 3af0f66bd0e5f320cdc9541ae9aaefa1008e7c68, data-model.md 889e375d5ddfd623365dadc9a579b9b84aeb436f, contracts/cli.md 606e7079ba7be2d7598be16fd8711cab1a031f7c, quickstart.md f2ca5302128bcdb4d6dc0f713fdb7986d5ea1464
- Review type: full (no plan copy from an earlier review)
- Open: BLOCKER 0 · MAJOR 3 · MINOR 4 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/759-move-old-scans/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-004) |
| Requirements and traceability | Outstanding (PR-001, PR-005) |
| Architecture and boundaries | Outstanding (PR-002, PR-005, PR-007) |
| Adversarial implementation and verification | Outstanding (PR-001, PR-002, PR-003, PR-004, PR-006) |
| Security and reliability | Outstanding (PR-001, PR-003, PR-006) |

### Findings

- **PR-001, MAJOR, open.** Research R5 treats a destination that already ends with the appended block as written, but a rerun after folder 649's store fails reads `649-plan-review.md` as a conflict with the command's own earlier write. `--append` would then duplicate #649's sections, and `--overwrite` would drop #656's. Stands because R5 checks each scan against the destination alone, and US3-5 needs a rerun that writes nothing twice.
- **PR-002, MAJOR, open.** The design record's Consequences say a `Detail` path that isn't a spec folder is reported and left in place, while its Decision and the plan create any named folder. A worktree directory named `<issue>-<slug>` or a dated directory such as `2026-11-13` would match R3's rule, and R3 wrongly says the rule excludes a dated directory. Stands because either path would move a scan into an invented folder with no report, and pfms's paths haven't been read.
- **PR-003, MAJOR, open.** `Folder result.steps` in data-model.md is keyed by step, so it can't hold both #649's and #656's plan reviews. The deletion rule says "a folder's scans", so the kept 656 scan could be deleted when 649's store succeeds. Stands because no test covers a kept scan in a folder whose store succeeds, which is wfctl's real first-run state and the SC-004 risk.
- **PR-004, MINOR, open.** The record and R4 say 12 scans name no folder, but under R3's rule only 4 do; the 8 for #299, #307, #325, and #352 name `<spec-root>/<folder>/`. R3's regex also keeps backticks, and 16 scans wrap their `Detail` path in them. Stands because the plan's counts and regex don't match the data.
- **PR-005, MINOR, open.** `AGENTS.md` and the comment above `SCANS_DIR` in `_paths.py` both say the old scans stay under the arch root. Stands because the plan marks `_paths.py` unchanged and doesn't list `AGENTS.md`.
- **PR-006, MINOR, open.** The contract's Stored cell names "unreachable", which isn't a store outcome (the outcome is `not_pushed`), and drops the store's remedy lines for conflict and merge outcomes. Stands because a failure that holds every later store would repeat on all 45 rows, up to 60 seconds each.
- **PR-007, MINOR, open.** `store specs` records its push with `record_outward_action`. Stands because the plan doesn't say whether `store scans` records its pushes.

## Review 2026-11-14T13:00Z

- Verdict: unsatisfied
- Reviewed: plan.md a8fb98e4f92b5253b9250bf58bf294d4a8c77bb0, spec.md 824d6d0a303650af5366197852e2f45a27ef8989, .specify/memory/constitution.md absent, design.md e6fb1d95b1f7883470001192b1269f88fc931458, docs/architecture/design/759-scan-names-its-folder.md 885d515bcf2c32e473906ef2f01d5596f39b5910, docs/architecture/scans-live-in-spec-folder.md 6ba8ee6b8f6ea703939fad101702eb43415a9f99, AGENTS.md 81e97f405ca993195c2450a3dffeed74c67dd18a, research.md c87c2a2c32dfd7100a34b4cfde726044b121c25a, data-model.md 51cbd244eaee0e82c2aec37093f1a68f918a4971, contracts/cli.md b622ef0876842e735e461d967bf9880c61a13bce, quickstart.md 75cd11df05509aa5f4169b5a1e55662fe0c432fa, plan-review.plan.md e898a78a17e60c9380870044d967ae271a6e5535 (base)
- Review type: re-review
- Open: BLOCKER 1 · MAJOR 0 · MINOR 5 · Fixed since the earlier review: 7
- Detail: /Users/andremarin/Development/wfctl-specs/759-move-old-scans/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-008, PR-012) |
| Requirements and traceability | Outstanding (PR-008, PR-012) |
| Architecture and boundaries | Outstanding (PR-013) |
| Adversarial implementation and verification | Outstanding (PR-008, PR-009, PR-010, PR-011) |
| Security and reliability | Outstanding (PR-009, PR-011) |

### Findings

- **PR-008, BLOCKER, open.** `spec.md §User Story 3, scenario 1` says the other folders' scans move when one folder's store fails as unreachable, and research R8 stops storing after `not_pushed`. Stands because no FR or spec scenario covers the stop, and the quickstart's US3-1 and stop-storing rows assert opposite outcomes.
- **PR-009, MINOR, open.** R8 carries on past `conflict` and `merge_refused`, which the store's own text says stop every store. Stands because each later folder would repeat the same failure, and "distinct failure" isn't defined.
- **PR-010, MINOR, open.** The reused `report_lines` remedies tell the user to run `wfctl store specs`, which never deletes the moved scans. Stands because the right rerun is `wfctl store scans`.
- **PR-011, MINOR, open.** `--overwrite 656-plan-review.md` on a first run replaces #649's text before it's stored, and #649's scan is still deleted. Stands because its write still reads `written`.
- **PR-012, MINOR, open.** pfms has 91 tracked review scans on `dev`, not 89. Stands in spec Assumptions, the record, and quickstart.
- **PR-013, MINOR, open.** The first-match rule's real failure is a matching segment above the spec folder, such as a worktree named `<issue>-<slug>` holding an in-repo `specs/`, not a dated folder below it. Stands in R3 and the record.
- **PR-001 through PR-007, fixed.** R5's starts-with rule, the record's rewritten Consequences, the per-scan data model, the corrected counts and backtick stripping, the `AGENTS.md` and `_paths.py` edits, R8's labels and `report_lines`, and R9's `store-scans` record.

## Review 2026-11-14T13:14Z

- Verdict: satisfied
- Reviewed: plan.md 030437ab5926f381f6fe0fd27b62d6154159a9b7, spec.md f2230d4af73d0540c29cf7c98b718a5eaa3f84dc, .specify/memory/constitution.md absent, design.md e6fb1d95b1f7883470001192b1269f88fc931458, docs/architecture/design/759-scan-names-its-folder.md 88054a61096a687c2ae2ee817d4c3bbdb3a19f4b, docs/architecture/scans-live-in-spec-folder.md 6ba8ee6b8f6ea703939fad101702eb43415a9f99, AGENTS.md 81e97f405ca993195c2450a3dffeed74c67dd18a, research.md ddfa9e4c434f08c3644e565005870e7a93f21a80, data-model.md 6425079f26ddb49c39ce35d09cf61e14ca4f6d34, contracts/cli.md 197de9496df5cef3456980a0c39906d4d43af140, quickstart.md 90a95f558891b2afd899352bd870288facb526ea, plan-review.plan.md a8fb98e4f92b5253b9250bf58bf294d4a8c77bb0 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 4 · Fixed since the earlier review: 4
- Detail: /Users/andremarin/Development/wfctl-specs/759-move-old-scans/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-014, PR-016) |
| Requirements and traceability | Outstanding (PR-012, PR-014) |
| Architecture and boundaries | Resolved (PR-013 fixed) |
| Adversarial implementation and verification | Outstanding (PR-010, PR-015, PR-016) |
| Security and reliability | Outstanding (PR-015) |

### Findings

- **PR-014, MAJOR, open.** pfms moved its 91 review scans into `pfms-specs` by hand on 2026-11-13 (#1120). Stands because SC-005, the spec's pfms text and removal trigger, the quickstart's pfms section, and the record's pfms bullet describe a move that already happened.
- **PR-010, MINOR, open.** R8 swaps `wfctl store specs` for `wfctl store scans` in every remedy line, including the `merge_blocked_staged` line, where the right command on the other branch is `store specs`. Stands because the swap is unconditional.
- **PR-012, MINOR, open.** pfms's `dev` had 91 review scans, not 89. Stands in spec, record, and quickstart, unless PR-014 removes that text.
- **PR-015, MINOR, open.** On a rerun after a `– not tried` folder, #649's write reads `already_there`, so the same-run `--overwrite` guard doesn't fire and #649's unstored text is replaced. Stands because the guard keys on a write, not on any ready scan at the destination.
- **PR-016, MINOR, open.** The contract's example shows `✓` for scans in the `✗ not pushed` and `– not tried` rows, while the cell table says `✓` means stored. Stands because no mark is defined for a ready scan in an untried folder.
- **PR-008, BLOCKER, fixed.** FR-014 and User Story 3 now say the first failed store stops storing, and R8, the contract, and the test map agree.
- **PR-009, PR-011, PR-013, MINOR, fixed.** R8 stops on every failed outcome; the same-run `--overwrite` is held as a conflict; R3 and the record give the worktree-above-the-spec-folder case.
