# Plan review scan for #740

## Review 2026-11-14T14:40Z

- Verdict: satisfied
- Reviewed: plan.md 01bcacd41b56fd4d9c489fdcb4e5d616832e0fda, spec.md 11edd531fd59194aecd08d2094d2a4d1392a90c4, .specify/memory/constitution.md absent, design.md 7575e6e8fe6f530f3d78ebba7158c159fb6c0834, docs/architecture/design/740-one-drawing-reader.md cbce100ef658286191756a8975462a67bc5cd9c4, docs/architecture/design/740-drawing-style-one-file.md 8188b04cc03b1fa9726d8ae69e7bd45c7e2bc28e, docs/architecture/record-drawing-can-be-svg.md 0ac84f1b48e9d71b6391f5c1daa7c1d19cf3b1b3, research.md 917539d2b8adce135ce3e535b38f6e4aebd10294, data-model.md b78a77fdcc3685d99ba38a9eb7fa390312ca8100, contracts/cli.md 6fac42246ecb4750671e293ff4c7ab7bce42d801, quickstart.md 78521a9ad3d089dbc1095cd2ebb7f8a368c84fc4
- Review type: full (no earlier review)
- Open: BLOCKER 0 · MAJOR 7 · MINOR 7 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/740-svg-drawings/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-009, PR-010) |
| Requirements and traceability | Outstanding (PR-001, PR-003, PR-005, PR-012) |
| Architecture and boundaries | Outstanding (PR-004, PR-007) |
| Adversarial implementation and verification | Outstanding (PR-002, PR-006, PR-008, PR-011, PR-014) |
| Security and reliability | Outstanding (PR-013) |

### Findings

- **PR-001, MAJOR, open.** `contracts/cli.md` extends the `no drawing` line, and R-010's snapshot would then fail for the 38 records that print it today. Stands because the contract doesn't say whether the line changes for every record or only for one holding a non-SVG image.
- **PR-002, MAJOR, open.** Stands because the plan doesn't say what accept prints for a drawing with a problem. Since `bool(drawing)` is false, the record would also get `no drawing` or `doesn't draw one`, and no problem has a fix line.
- **PR-003, MAJOR, open.** Stands because `validate` repeats only `_repeat_refusals` and `_drawing_refusals`, so doctor never warns about a one-kind record's drawing problems, such as FR-001's "both" case.
- **PR-004, MAJOR, open.** FR-006 picks the failing-step message by format, while `740-one-drawing-reader` keeps format-specific code out of the checks. Stands because the plan doesn't reconcile them.
- **PR-005, MAJOR, open.** Stands because the plan doesn't edit the skills' existing mermaid-default prose in `design-levels/SKILL.md`, `architecture-decisions/SKILL.md`, and `model-the-domain/references/visual-language.md`.
- **PR-006, MAJOR, open.** Stands because a committed snapshot of live records, 44 of them proposed, fails any later branch that adds or edits a record.
- **PR-007, MAJOR, open.** Stands because with `drawings/` excluded, a branch can change or delete an accepted record's SVG and nothing notices, and neither the plan nor the level-2 record says so.
- **PR-008, MINOR, open.** Stands because the plan doesn't say where `drawings_dir` and the printed path come from, whether containment resolves symlinks, or how a leading-slash link is treated.
- **PR-009, MINOR, open.** Stands because the plan says `_records.py` already imports `_paths`, which it doesn't. The import is still allowed.
- **PR-010, MINOR, open.** Stands because `test_arch_labels.py` calls `_records._labels` 17 times, and the plan neither changes the test nor keeps the name.
- **PR-011, MINOR, open.** Stands because the "file missi" label was start-anchored at x=708, not end-anchored, so R-003 and the quickstart's recreation are wrong.
- **PR-012, MINOR, open.** Stands because each `_drawing` call re-reads the SVG, so "built once per drawing" doesn't hold.
- **PR-013, MINOR, open.** Stands because XML safety rests on the bundled expat while distribution Pythons may link the system's, and an `OSError` or decode error isn't mapped to a problem.
- **PR-014, MINOR, open.** Stands because two SVG images under one heading leave the second unchecked, the gap R-009 cites for a fence plus an SVG.

## Review 2026-11-14T14:59Z

- Verdict: satisfied
- Reviewed: plan.md 5e8ecfa36b15ecffae676e756a73765090cce783, spec.md 29a6bdb1f854c6da3ae66d3f1142fbb7621a517d, .specify/memory/constitution.md absent, design.md 7575e6e8fe6f530f3d78ebba7158c159fb6c0834, docs/architecture/design/740-one-drawing-reader.md cbce100ef658286191756a8975462a67bc5cd9c4, docs/architecture/design/740-drawing-style-one-file.md 8188b04cc03b1fa9726d8ae69e7bd45c7e2bc28e, docs/architecture/record-drawing-can-be-svg.md 0ac84f1b48e9d71b6391f5c1daa7c1d19cf3b1b3, research.md 2a73a397b540b53bb4d84de62c01ffb16c839110, data-model.md 39fae52e895f9ff796976a27b89d653db8350703, contracts/cli.md fe5cc6c5440b62943e3bb3c87855ed5eb2cd6464, quickstart.md 52280d4ad9adc8573df32536b69f79a9a92261b6, plan-review.plan.md 01bcacd41b56fd4d9c489fdcb4e5d616832e0fda (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 4 · Fixed since the earlier review: 14
- Detail: /Users/andremarin/Development/wfctl-specs/740-svg-drawings/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-015, PR-016, PR-017, PR-018) |
| Requirements and traceability | Outstanding (PR-015, PR-016, PR-017, PR-018) |
| Architecture and boundaries | Resolved (PR-004, PR-007, PR-009 fixed) |
| Adversarial implementation and verification | Outstanding (PR-015) |
| Security and reliability | Outstanding (PR-019) |

### Findings

- **PR-001 to PR-014, fixed.** Each is fixed in the planning artifacts. The contract rewords `no drawing` once and R-010 allows only that difference. A problem line replaces the missing-drawing line, and doctor repeats it for a one-kind record. The reader sets `failure_fix`. The skill-prose table lists every cited passage. R-010 is a scratchpad comparison. The accepted-SVG limit is stated and gets a doctor warning. Links print as written and resolve before the containment check. The `_paths` import is described correctly. `fence_labels` keeps the label tests unchanged. The edge fixture uses `x="708"`. FR-009 says "one reader per format". A DOCTYPE and read errors become problems. Two SVG links under one heading are refused.
- **PR-015, MAJOR, open.** `contracts/cli.md` rewords every `_DRAWING_FIX` entry. Stands because FR-011 names the `no drawing` line as the only wording change, and two exact-output tests in `tests/test_arch_diagram_kinds.py` that R-010 says run unchanged would break.
- **PR-016, MINOR, open.** Stands because `model-the-domain/SKILL.md:250` still says records are drawn in mermaid, and it's in neither the skill-prose table nor the quickstart grep. The planned `visual-language.md` text also moves domain documents to SVG, which the spec gives no folder.
- **PR-017, MINOR, open.** Stands because the doctor warning for an accepted record's broken SVG isn't in the spec, which describes every drawing warning as proposed-only.
- **PR-018, MINOR, open.** Stands because the spec's Validation Strategy still asks for a committed test over every record on disk, while R-010 commits nothing.
- **PR-019, MINOR, open.** Stands because a UTF-16 or UTF-32 SVG hides `<!DOCTYPE` from a raw-bytes check, and expat still parses the DOCTYPE.

## Review 2026-11-14T22:03Z

- Verdict: satisfied
- Reviewed: plan.md 3d072ea6b02691994745e126bb5dbd5925fa5f83, spec.md 14f2c09b337ca678b4cfd337cceca89a5fac9c5d, .specify/memory/constitution.md absent, design.md 7575e6e8fe6f530f3d78ebba7158c159fb6c0834, docs/architecture/design/740-one-drawing-reader.md cbce100ef658286191756a8975462a67bc5cd9c4, docs/architecture/design/740-drawing-style-one-file.md 8188b04cc03b1fa9726d8ae69e7bd45c7e2bc28e, docs/architecture/record-drawing-can-be-svg.md 9241aee3471d0d12e38497a602df952c3506d274, research.md 34f41d61e9a5cf0f3491047291aac2b39da56c7f, data-model.md 7f0e8d8868fc37c06b6c11bb298eb50e4ae0be08, contracts/cli.md ab5bad6ffabb5a862bab45f30ecfda4c5ef8c44f, quickstart.md b2e9f4e456091db369549d0abc3e8fb137197fb8, plan-review.plan.md 5e8ecfa36b15ecffae676e756a73765090cce783 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 4 · Fixed since the earlier review: 5
- Detail: /Users/andremarin/Development/wfctl-specs/740-svg-drawings/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-021, PR-022) |
| Requirements and traceability | Outstanding (PR-022, PR-023, PR-024) |
| Architecture and boundaries | Outstanding (PR-020) |
| Adversarial implementation and verification | Outstanding (PR-021, PR-024) |
| Security and reliability | Resolved (PR-019 fixed) |

### Findings

- **PR-015 to PR-019, fixed.** FR-011 lists both rewordings and the two test updates. The skill-prose table has `model-the-domain/SKILL.md:250`, and domain documents keep mermaid until #761. FR-021 puts the accepted-record warning in the spec. The validation strategy describes the uncommitted comparison. FR-025 and R-001 decode as UTF-8 before the DOCTYPE check.
- **PR-020, MAJOR, open.** Stands because a `redrawn` Log line edits the accepted record's file, so a branch carrying `arch none` gets its PR refused by the record gate, and once the exception is deleted the design gate counts a picture plus a Log line as the boundary answer. The plan mentions neither gate.
- **PR-021, MINOR, open.** Stands because the terminal check refuses every real accept through `CliRunner`, which breaks exit-0 tests in `test_arch_accept_drawing.py` and one in `test_arch_accept_dry_run.py`, and the dry-run parity tests need the check placed after every existing refusal.
- **PR-022, MINOR, open.** Stands because R-010 still says `test_arch_diagram_kinds.py` runs unchanged, the source tree leaves out `model-the-domain/SKILL.md`, and the plan says the record's Consequences "gains" text commit 320b19c already wrote.
- **PR-023, MINOR, open.** Stands because `architecture-decisions/SKILL.md`'s immutability section says only a status change and one Log line ever change, and the skill-prose table has no row for it.
- **PR-024, MINOR, open.** Stands because the redraw path doesn't say what happens to an SVG with no fingerprint, or whether a redraw reruns the failing-step rule.

## Review 2026-11-14T22:55Z

- Verdict: satisfied
- Reviewed: plan.md 9a22ac8d7c4959039542743db84ba9d4764f6d74, spec.md 53d6c195daeb4155426f8dc352066636e5d2a0c1, .specify/memory/constitution.md absent, design.md 7575e6e8fe6f530f3d78ebba7158c159fb6c0834, docs/architecture/design/740-one-drawing-reader.md cbce100ef658286191756a8975462a67bc5cd9c4, docs/architecture/design/740-drawing-style-one-file.md 8188b04cc03b1fa9726d8ae69e7bd45c7e2bc28e, docs/architecture/record-drawing-can-be-svg.md 9241aee3471d0d12e38497a602df952c3506d274, research.md e32104e0b7f3d158fbb4dd25e515917f8f69916a, data-model.md 7f0e8d8868fc37c06b6c11bb298eb50e4ae0be08, contracts/cli.md 15defcdca3236ce7984f107821f864f42665375f, quickstart.md bb539d2202504f520cb44fe408143e185af72137, plan-review.plan.md 3d072ea6b02691994745e126bb5dbd5925fa5f83 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 2 · MINOR 2 · Fixed since the earlier review: 4
- Detail: /Users/andremarin/Development/wfctl-specs/740-svg-drawings/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Resolved (PR-021, PR-022 fixed) |
| Requirements and traceability | Resolved (PR-022, PR-023, PR-024 fixed) |
| Architecture and boundaries | Outstanding (PR-020, PR-025, PR-027) |
| Adversarial implementation and verification | Outstanding (PR-020, PR-025, PR-026) |
| Security and reliability | Outstanding (PR-026) |

### Findings

- **PR-021 to PR-024, fixed.** Both accept test files patch `_at_terminal`, and R-013 places the terminal check after every refusal. R-010 is corrected, `model-the-domain/SKILL.md` is in the tree, and the record entry is reworded. The skill-prose table has a row for `architecture-decisions/SKILL.md:230-237`. FR-022 and the contract say an unfingerprinted SVG is redrawn and the redraw reruns every acceptance check.
- **PR-020, MAJOR, open.** The record gate half is fixed. Stands because the general boundary check in `_evidence._architecture_answered` and `cli._observe`'s Boundary line both call `touched_on_this_branch`, never `records_on_this_branch`, so the planned exclusion doesn't reach them. Neither is in the plan's file list, R-014 places `_observe` in `_evidence`, and no test covers a redraw-only branch with no exception present or the `record:` lines.
- **PR-025, MAJOR, open (new).** Stands because R-014's `redraw_only` diffs `trunk...head`, while `records_on_this_branch` also lists working-tree changes and works without a trunk. An uncommitted record has an empty committed diff, which reads as redraw-only, and the plan doesn't say what no trunk or a git failure does.
- **PR-026, MINOR, open (new).** Stands because the `redrawn` pattern is matched on a `-U0` diff with no section context, so a matching bullet in `## Decision`, or a `redrawn` line on a proposed record, would pass. A Log with no trailing newline turns a real redraw into a change.
- **PR-027, MINOR, open (new).** Stands because `_records._append_log` writes the line and `_paths.redraw_only` recognises it with a separate regex across the core boundary, with no test tying the two.

## Sign-off 2026-11-15T02:02Z

- Signed off: plan.md 2ce5cad62aa120acaa33ed11dae71aa0a0309d46
- Reason: Applied the fourth review's PR-020, PR-025, PR-026 and PR-027 as the review suggested; no new design.
- Reviewed copy: compared

## Review 2026-11-15T03:36Z

- Verdict: satisfied
- Reviewed: plan.md 9b28d25d3b45b251dfe7bc8c2e93f4667c53a8a5, spec.md 81f85cbca453832f227ac928bc10852632da2775, .specify/memory/constitution.md absent, design.md 7575e6e8fe6f530f3d78ebba7158c159fb6c0834, docs/architecture/design/740-one-drawing-reader.md cbce100ef658286191756a8975462a67bc5cd9c4, docs/architecture/design/740-drawing-style-one-file.md 8188b04cc03b1fa9726d8ae69e7bd45c7e2bc28e, docs/architecture/record-drawing-can-be-svg.md 9241aee3471d0d12e38497a602df952c3506d274, research.md e3c1f1831803b2e0221510603c6adbd781b275e7, data-model.md 7f0e8d8868fc37c06b6c11bb298eb50e4ae0be08, contracts/cli.md ae564e71737bd48779115ae8065619c13fb27982, quickstart.md 8b16046e12d96a3c95e571eb3c96f63565308b92, plan-review.plan.md 9a22ac8d7c4959039542743db84ba9d4764f6d74 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 2 · Fixed since the earlier review: 4
- Detail: /Users/andremarin/Development/wfctl-specs/740-svg-drawings/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-028) |
| Requirements and traceability | Outstanding (PR-028) |
| Architecture and boundaries | Resolved (PR-020, PR-025, PR-027 fixed) |
| Adversarial implementation and verification | Outstanding (PR-029) |
| Security and reliability | Resolved (PR-025, PR-026 fixed) |

### Findings

- **PR-028, MINOR, open.** The last bullet of `research.md §R-010` still says `accept_problems` doesn't carry the `no drawing` fix, which contradicts FR-011, the plan, the contract, and the code. The plan's Constitution Check says `arch/__init__.py` exports nothing new, while Project Structure and R-014 export `redraw_only`. Stands because neither line was updated with the change that made it untrue.
- **PR-029, MINOR, open.** R-014 gives `record_change` no None case for a record deleted in the working tree, which `records_on_this_branch` lists. Condition 3 says every added line matches `REDRAWN_LINE`, but condition 4's no-newline exception re-adds a line that doesn't. Stands because the contract text is wrong, though `test_redraw_only.py` pins the intended answer.
- **PR-020, MAJOR, fixed.** Fixed by `_architecture_answered` and `cli._observe` switching to `decided_on_this_branch` with `skip=arch.redraw_only`, with tests with and without a name list.
- **PR-025, MAJOR, fixed.** Fixed by `record_change` diffing the merge base to the working tree and returning None for no trunk, a git failure, or no file at the base.
- **PR-026, MINOR, fixed.** Fixed by `redraw_only` requiring an accepted record and the added lines inside `## Log`.
- **PR-027, MINOR, fixed.** Fixed by `REDRAWN_LINE` and `redraw_only` living in `_records.py` beside `_append_log`, with `_paths` taking a `skip` callable.

## Sign-off 2026-11-15T04:03Z

- Signed off: plan.md 915eec1c45a49824bacba6afba9b88a1dd567452
- Reason: Wording-only edits applying fifth plan review findings PR-028 and PR-029; no change to scope, design, or tasks' structure.
- Reviewed copy: compared
