# Plan review scan for #648

## Review 2026-10-25T23:43Z

- Verdict: satisfied
- Reviewed: plan.md 8575811afa5ff2ff5c9de11ca4ea4ad26f5f742b, spec.md ae42f4b2c0ed202dadaa19a0ee16710eca1f7c02, .specify/memory/constitution.md absent, design.md 510ffe34b040c75951545755604a01f517c11eee, docs/architecture/design/software-design-none-is-a-claim.md c217a83b3a517bd3cb516abd105a4371599a43c7, docs/architecture/declarations/648-design-gate.md 8358208e0cc21da4a35f3dc336d376f18fa8b8fa, research.md 56478efff25203231d2d0354f630f78c02faeaec, data-model.md fd750e351c657a53ed5c920c197a6c75bcf6e675, contracts/cli.md b1be720b606fcc4dce73891a4a2a81e06698b048, quickstart.md 022916e04e304b6e1b10085fcb6a64045a46bbbf, checklists/requirements.md 5d24c2763686d2b8e4a90fa6867b32d57f7b5efa, AGENTS.md 506b62be5f7860aad3ead6ba5bae864db68b15ba, docs/architecture/vendor-upstream-skills.md 4d6b0177ffe76f882118423926af27d76b74e934
- Review type: full (no earlier report, so there was no base to diff against)
- Open: BLOCKER 0 · MAJOR 2 · MINOR 10 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/648-design-gate/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Outstanding (PR-004, PR-008, PR-010, PR-011) |
| Architecture and boundaries | Outstanding (PR-006, PR-012) |
| Adversarial implementation and verification | Outstanding (PR-002, PR-003, PR-005, PR-007, PR-009) |
| Security and reliability | Outstanding (PR-001) |

### Findings

- **PR-001, MAJOR, open.** FR-009a has the agent run `wfctl step none brainstorm.software-design` under auto-approve, but neither `speckit-brainstorm/SKILL.md` nor `commands/speckit.brainstorm.md` grants that command in `allowed-tools`. An unattended run then gets a refusal or a prompt nobody answers. The plan also leaves the width of the grant open, and a broad `wfctl step none*` would let the agent claim away `plan.plan-review` too. Stands because the plan names no grant and leaves the wrapper file out of Project Structure.
- **PR-002, MAJOR, open.** Test 8 expects an absolute-path remedy when the arch root is outside the tree. That case can't happen, since `touched_on_this_branch` returns None outside the tree and the pass doesn't hold on None, which FR-006 agrees with. Stands because the contract line and R4's reason for moving `arch_location` both rest on that case.
- **PR-003, MINOR, open.** `contracts/cli.md` shows `design-doc` as done while the pass holds, but the `_pass_states` cascade makes it `pending`. The `plan-walkthrough` row also has one space before its glyph, which test 9 forbids, and the README edit doesn't say which state the new row shows. Stands because the contract wasn't updated.
- **PR-004, MINOR, open.** R7's width floor of 16 never applies, since the built-in `software-design` pass always makes the width 19. As a result, every repo's pass rows move, including the one `tests/test_cli_status.py:56` checks. Counting hidden passes departs from FR-007's "shown", and the plan doesn't call it a departure. Stands because R7 is unchanged.
- **PR-005, MINOR, open.** No planned test covers US1 acceptance 3 (auto-approve stops at brainstorm) or US2 acceptance 2 (a record already on `main` doesn't release the pass). Stands because the test list omits both.
- **PR-006, MINOR, open.** SC-004 says all three skills name the claim, and only a manual quickstart read checks it. `a-rule-is-expressed-as-a-check` calls for a test here, and `test_skill_cross_references.py:220` already has one for `arch none`. Stands because the plan adds no test.
- **PR-007, MINOR, open.** Quickstart steps 3 - 6 run the bare `wfctl` from PATH instead of the working tree, so they report a false failure. Step 4's commit and reset steps are also loosely specified. Stands because quickstart.md is unchanged.
- **PR-008, MINOR, open.** The table at `design-levels` line 88, which an unattended run follows to find where each gate's answer goes, gets no row for the claim. The insertion at line 410 doesn't cover a branch whose only structural choice was a boundary, which the pass also holds. Stands because the plan edits neither place.
- **PR-009, MINOR, open.** R9 says the snapshot holds the payload's pass list, but it holds no `sub_steps`. What changes is the verdict of the `design-with-record` row, which breaks `test_the_matrix_reaches_both_design_states`. R9 also treats `storyctl_dir` as having no trunk when it has one. Stands because R9 is unchanged.
- **PR-010, MINOR, open.** The plan's validation list leaves out `uv run wfctl verify` and `uv run wfctl doctor`, which spec.md's Validation Strategy names. Stands because the list is unchanged.
- **PR-011, MINOR, open.** `design.md` names `changes/648.addition.md` and the spec names `648.change.md`. The plan follows the spec, but R8 says the old value came from the spec. Stands because R8 is unchanged.
- **PR-012, MINOR, open.** Four docstrings or comments still count brainstorm's passes as two: `brainstorm_architecture`, `brainstorm_design_doc`, the `Step` docstring, and `test_declared.py:20`. Stands because the plan doesn't list them.

## Review 2026-10-26T11:03Z

- Verdict: satisfied
- Reviewed: plan.md 59e4d6c932a82e2d70d358bb79e9b05865bb79a0, spec.md ae42f4b2c0ed202dadaa19a0ee16710eca1f7c02, .specify/memory/constitution.md absent, design.md 5b70b93efa85d2ea8df1ffebc08e3907829c2dac, docs/architecture/design/software-design-none-is-a-claim.md c217a83b3a517bd3cb516abd105a4371599a43c7, docs/architecture/declarations/648-design-gate.md 8358208e0cc21da4a35f3dc336d376f18fa8b8fa, research.md 96eb2b48a8fa83966e391a344f6c563bb9c0e9ed, data-model.md fd750e351c657a53ed5c920c197a6c75bcf6e675, contracts/cli.md dfb247a73319f0c47cddf662af68ce9ac7d8b457, quickstart.md 8cc6853b66ebb2a5c2b0c8c5600c4bca27fa9bbe, checklists/requirements.md 5d24c2763686d2b8e4a90fa6867b32d57f7b5efa, AGENTS.md 506b62be5f7860aad3ead6ba5bae864db68b15ba, docs/architecture/vendor-upstream-skills.md 4d6b0177ffe76f882118423926af27d76b74e934, plan-review.plan.md 8575811afa5ff2ff5c9de11ca4ea4ad26f5f742b (base)
- Review type: re-review (the plan copy matched the earlier review's plan.md identity; design.md, research.md, contracts/cli.md, and quickstart.md also changed and were re-read in full)
- Open: BLOCKER 0 · MAJOR 0 · MINOR 7 · Fixed since the earlier review: 12
- Detail: /Users/andremarin/Development/wfctl-specs/648-design-gate/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-019) |
| Requirements and traceability | Resolved (PR-004, PR-008, PR-010 fixed) |
| Architecture and boundaries | Resolved (PR-006 fixed) |
| Adversarial implementation and verification | Outstanding (PR-013, PR-014, PR-017, PR-018) |
| Security and reliability | Outstanding (PR-015, PR-016) |

### Findings

- **PR-001, MAJOR, fixed.** Fixed by `plan.md §allowed-tools`, which gives both brainstorm frontmatters the narrow `Bash(wfctl step none brainstorm.software-design *)` grant, says why the broad form was rejected, and adds test 14.
- **PR-002, MAJOR, fixed.** Fixed by test 8, which now checks that an arch root outside the tree doesn't hold the pass. The contract and R4 agree with it.
- **PR-003, MINOR, fixed.** Fixed by `contracts/cli.md`, which shows `design-doc` as pending at the computed width, and by `plan.md §README.md`, which says the new row shows done.
- **PR-004, MINOR, fixed.** Fixed by R7, which drops the floor, calls out the departure from FR-007, and lists `tests/test_cli_status.py`.
- **PR-005, MINOR, fixed.** Fixed by tests 11 and 12.
- **PR-006, MINOR, fixed.** Fixed by test 13, which checks that all three skills name the claim command.
- **PR-007, MINOR, fixed.** Fixed by `quickstart.md`, which runs the working tree's wfctl through `$WFCTL` and commits only the record in step 4.
- **PR-008, MINOR, fixed.** Fixed by `plan.md §design-levels`, which adds the claim to the line-88 table and covers the boundary-only case at line 410.
- **PR-009, MINOR, fixed.** Fixed by R9, which corrects the snapshot and `storyctl_dir` claims, and by test 15.
- **PR-010, MINOR, fixed.** Fixed by `plan.md §Technical Context`, which adds `wfctl verify` and `wfctl doctor`.
- **PR-011, MINOR, fixed.** Fixed by `design.md`, which now names `changes/648.change.md`, and by R8's corrected attribution.
- **PR-012, MINOR, fixed.** Fixed by `plan.md §_evidence.py` item 4, which lists every site the finding named.
- **PR-013, MINOR, open.** Three more comments still count brainstorm's passes as two: `tests/test_cli_status.py:44`, `tests/test_pipeline_state_names.py:249`, and a second sentence in the `brainstorm_architecture` docstring. Stands because item 4 doesn't list them.
- **PR-014, MINOR, open.** `test_a_written_record_with_no_design_doc_leaves_exactly_one_pass_outstanding` writes an architecture record with no `design.md` on `storyctl_dir`, so it will read two outstanding passes. R9's rule for which tests break misses it, and the quickest repair would remove what the test checks. Stands because R9 doesn't name it.
- **PR-015, MINOR, open.** Test 14 checks only that the exact string `Bash(wfctl step none*)` is absent, so a broad grant written another way, such as `Bash(wfctl step none *)` or `Bash(wfctl*)`, would still pass. Stands because the test doesn't match command lines the way `test_provenance.py` does.
- **PR-016, MINOR, open.** The narrow grant doesn't stop brainstorm's agent from claiming another pass, since its unrestricted `Write` can create a claim file directly. The PR review is the control that catches it, so only the rationale's wording needs to change. Stands because the plan says the grant prevents it.
- **PR-017, MINOR, open.** No planned test fails if the width is hard-coded to `.ljust(20)`, and "20 in every repository" is false once a repo declares a pass name longer than 16 characters. Stands because test 9 only uses built-in names.
- **PR-018, MINOR, open.** Quickstart step 6 gives no command or path for removing the claim, and step 7 reads `.claude/skills/` while the shell is still in the scratch repository. Stands because quickstart.md is unchanged there.
- **PR-019, MINOR, open.** The design record's Verification section says `status` prints the remedy under `how:`, while the spec and contract say it goes under `next:`. Stands because the record wasn't updated.

## Review 2026-10-26T20:13Z

- Verdict: satisfied
- Reviewed: plan.md 85a62d65e623aa2a9231e744809e60414aa982b5, spec.md 2c9c89ffdad0c1ac38363061140b52d7bebb3519, .specify/memory/constitution.md absent, design.md 5b70b93efa85d2ea8df1ffebc08e3907829c2dac, docs/architecture/design/software-design-none-is-a-claim.md c217a83b3a517bd3cb516abd105a4371599a43c7, docs/architecture/declarations/648-design-gate.md 8358208e0cc21da4a35f3dc336d376f18fa8b8fa, docs/architecture/promised-evidence-blocks-on-silence.md 970abb8f55ac25118a36d9e71ef3d2220f662666, research.md 1efe6afae5de4efc4261b3f0db3c152c0bee3ea6, data-model.md 643113cb11c28e27dc808f047b5f9b08781e5625, contracts/cli.md 1a11576d8914c89c7978c85b38977ffd1dbcabc2, quickstart.md 8cc6853b66ebb2a5c2b0c8c5600c4bca27fa9bbe, checklists/requirements.md 5d24c2763686d2b8e4a90fa6867b32d57f7b5efa, AGENTS.md 506b62be5f7860aad3ead6ba5bae864db68b15ba, docs/architecture/vendor-upstream-skills.md 4d6b0177ffe76f882118423926af27d76b74e934, plan-review.plan.md 59e4d6c932a82e2d70d358bb79e9b05865bb79a0 (base)
- Review type: re-review (the plan copy matched the earlier review's plan.md identity; spec.md, research.md, data-model.md, contracts/cli.md, and the amended record changed and were re-read in full)
- Open: BLOCKER 0 · MAJOR 3 · MINOR 12 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/648-design-gate/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-019, PR-023) |
| Requirements and traceability | Outstanding (PR-021, PR-022) |
| Architecture and boundaries | Outstanding (PR-020, PR-024) |
| Adversarial implementation and verification | Outstanding (PR-013, PR-014, PR-017, PR-018, PR-025, PR-026, PR-027) |
| Security and reliability | Outstanding (PR-015, PR-016) |

### Findings

- **PR-001 to PR-012, fixed.** Still fixed. The revision for the git hold didn't touch them, and test 8 now asserts the hold that the rewritten FR-006 requires.
- **PR-013 to PR-019, MINOR, open.** Carried from the earlier review unchanged, since the revision didn't touch them.
- **PR-020, MAJOR, open.** Plan item 5.4 returns the git reason for an `inconclusive` verdict before calling `blocks`, so the reader decides what git's silence means itself, which the amended record forbids. Stands because `test_every_inconclusive_verdict_goes_through_blocks` only checks that `blocks` is called somewhere in the function.
- **PR-021, MAJOR, open.** `Assessment("skipped", CHECKS_OFF_REASON)` puts the text in `reason`, which `collect_warnings` turns into a warning on every `wfctl status`, `next`, and `resume`. The contract shows the rows only under `--all`. Stands because the plan doesn't use `display=`, the pattern `DRAWINGS_UNCHECKED` follows.
- **PR-022, MAJOR, open.** `check_config_cmd` returns "no configuration to check" when `wfctl.json` is missing (`cli.py:6637-6639`). An outside arch root is declared in the manifest or `WFCTL_ARCH_DIR`, so the FR-006b finding never prints in the repo it's written for. Stands because the plan adds the finding after that early return.
- **PR-023, MINOR, open.** FR-006a and US5 acceptance 3 say the turned-off checks read done, and the plan, data model, and contract read them as `skipped`, with no label on the departure.
- **PR-024, MINOR, open.** R10 and Complexity Tracking say a held architecture check has no way out without the new key, but `wfctl step none brainstorm.architecture` releases it, since claims are read from disk. The stronger reason for the key is that a claim is needed on every branch and is never committed.
- **PR-025, MINOR, open.** Item 6.5 is wrong in two cases: with no `design.md` and git unable to answer, `brainstorm` reads `pending`, and with the checks off, a branch with nothing in it never reads `pending`. Item 6.3 doesn't say whether the setting is read before or after the `spec.md` escape.
- **PR-026, MINOR, open.** Five existing tests fail with the architecture check's source changed, and R10 misses `test_design_gate_drawing.py:584` and `test_pipeline_commands.py::test_an_unreadable_arch_root_advances_the_design_step`. Item 6.4 also misses the `DRAWINGS_UNCHECKED` comment (`_evidence.py:161-167`), whose rationale the change contradicts.
- **PR-027, MINOR, open.** `quickstart.md` has no end-to-end step for User Story 5, a repo held because its architecture folder is outside the project and then released with `"off"`.
