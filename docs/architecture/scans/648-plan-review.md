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
