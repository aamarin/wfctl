# Plan review scan for #649

## Review 2026-10-26T20:43Z

- Verdict: satisfied
- Reviewed: plan.md 6b7e969b6c75c38127d6761e7a4a011c3a4276e3, spec.md b3cceba7f25b1c1fa18b05895b60a44d143ae3f1, .specify/memory/constitution.md absent, design.md 8f1a1ef55b9d0fd9742190c2401d3adcd4b2b7be, docs/architecture/design/649-contexts-module.md 0d1a60c0e6cb2819c8390d6cd4b960bbaebaadb8, docs/architecture/domain-page-names-contexts.md 5aa73e748adccc3798b780c21f1ffe0371951f77, research.md a4f80c38956946b7c7b5c771351dfd9484044208, data-model.md 16f85e9cce11389ab43980a25b345fc1356ece36, contracts/cli.md dc7805c3acfb26caab5d596702b5a5343d32d803, quickstart.md b5d38b715c8faf29213d352c88eacaf4e078725a, ../635-arch-folder-per-branch-notes/plan.md adfd05636fe410e3582bcf495a841812a495fb53, ../635-arch-folder-per-branch-notes/data-model.md 721a5a27cabc13facc346ffbb591d67819d4bf58, ../635-arch-folder-per-branch-notes/research.md 99477b1879c374eac3b8cd5c296ae0d3da578474, ../648-design-gate/plan.md 917273ccd1741eff61dfe1348db5ca30abd3a6b7
- Review type: full (no earlier report and no plan copy)
- Open: BLOCKER 0 · MAJOR 4 · MINOR 7 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/649-design-checks-by-context/plan-review.md

The review ran in a fresh-context subagent. #635 and #648 have no code yet, so PR-001 to PR-003 were checked against their plans and need checking again once they merge.

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-002, PR-005, PR-008) |
| Requirements and traceability | Outstanding (PR-002, PR-003, PR-005, PR-008, PR-009) |
| Architecture and boundaries | Outstanding (PR-001, PR-003, PR-006, PR-011) |
| Adversarial implementation and verification | Outstanding (PR-001, PR-002, PR-004, PR-007, PR-009) |
| Security and reliability | Outstanding (PR-002, PR-010) |

### Findings

- **PR-001, MAJOR, open.** `plan.md` Phase B item 4 places the per-context check after the git-unanswered exit, but #648's planned reader returns done at its earlier `blocks`-false exit once any record is touched. Stands because a record about the wrong context would still pass.
- **PR-002, MAJOR, open.** `_pipeline._pass_states` marks a claimed pass skipped before its reader runs, and the plan only refuses the bare form at write time. Stands because a claim already on disk still clears the pass, against FR-011 and SC-001.
- **PR-003, MAJOR, open.** #635's other readers of the exceptions folder (the `check-body` reason check, the session summary's Boundary line, and the guard's contradiction check) never see a per-context "no". Stands because the plan doesn't list them.
- **PR-004, MAJOR, open.** `brainstorm` uses `_architecture_answered` to tell pending from started, and in a repo with a name list a branch with a record and no `design.md` would read pending. Stands because the plan doesn't say when the skills write the `Contexts` line or how the pending reading is kept.
- **PR-005, MINOR, open.** The R3 refusal makes User Story 2 scenario 3's precondition unreachable through the CLI, and the R3 and R4 refusals are additions the spec doesn't list.
- **PR-006, MINOR, open.** Phase D names the "Moves a boundary?" section in `opening-a-change`, which says it never grows a section list.
- **PR-007, MINOR, open.** The per-context "no" display leaves its separator, whether it shows in plain `status`, and its precedence over `DRAWINGS_UNCHECKED` unspecified.
- **PR-008, MINOR, open.** No phase carries FR-016's `--context` skill text, or the skill text teaching a bare `arch none` that R3 refuses.
- **PR-009, MINOR, open.** Phases B and C name no tests for several scenarios and refusals.
- **PR-010, MINOR, open.** A context name becomes a directory under `exceptions/` with no shape check, so a name with `/` or `..` escapes the folder.
- **PR-011, MINOR, open.** #635's `design-exceptions-module.md` still describes a flat folder, and the plan lists no edit or follow-up for it.

## Review 2026-10-26T20:51Z

- Verdict: satisfied
- Reviewed: plan.md a224da8b4e7adee430a75d217b61b54973930404, spec.md 6eea00a0504c4ca503cedc2d18a8e42a48a7a608, .specify/memory/constitution.md absent, design.md 8f1a1ef55b9d0fd9742190c2401d3adcd4b2b7be, docs/architecture/design/649-contexts-module.md 0d1a60c0e6cb2819c8390d6cd4b960bbaebaadb8, docs/architecture/domain-page-names-contexts.md 5aa73e748adccc3798b780c21f1ffe0371951f77, docs/architecture/promised-evidence-blocks-on-silence.md 1c979cb4270a3c2a148363ae5b48dfa4a731b94f, research.md fc160de949fbc07866c097547577b9e53fec3d34, data-model.md 348ab147f89f686d144ef3f7a7a71fb6d37f465a, contracts/cli.md 66e0635fe5399818d52791c219a7a3914f9f99c0, quickstart.md b5d38b715c8faf29213d352c88eacaf4e078725a, ../635-arch-folder-per-branch-notes/plan.md adfd05636fe410e3582bcf495a841812a495fb53, ../635-arch-folder-per-branch-notes/data-model.md 721a5a27cabc13facc346ffbb591d67819d4bf58, ../635-arch-folder-per-branch-notes/research.md 99477b1879c374eac3b8cd5c296ae0d3da578474, ../648-design-gate/plan.md 917273ccd1741eff61dfe1348db5ca30abd3a6b7, ../648-design-gate/research.md e33d7568951e6ca8268bba5d3d0ed83d32b7a8aa, plan-review.plan.md 6b7e969b6c75c38127d6761e7a4a011c3a4276e3 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 3 · Fixed since the earlier review: 10
- Detail: /Users/andremarin/Development/wfctl-specs/649-design-checks-by-context/plan-review.md

The review ran in a fresh-context subagent after the plan was revised against the first review's findings.

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-014) |
| Requirements and traceability | Outstanding (PR-014) |
| Architecture and boundaries | Outstanding (PR-003, PR-012) |
| Adversarial implementation and verification | Outstanding (PR-003, PR-012, PR-013) |
| Security and reliability | Resolved (PR-002, PR-010 fixed) |

### Findings

- **PR-001, MAJOR, fixed.** Fixed by `plan.md` Phase B item 4, which puts the per-context branch ahead of #635's boundary exit and #648's git and `blocks` exits.
- **PR-002, MAJOR, fixed.** Fixed by Phase B items 2 and 6: the bare `step none brainstorm.architecture` is refused with a name list, and the claim lookup drops whole-pass claims on both passes.
- **PR-003, MAJOR, open.** `check-body` is fixed by `reasons`. Stands because the session summary's Boundary line reads `boundary()` and git, not `_architecture_answered`, in both today's `_observe` and #635's plan (R6), so the promised test would fail. The guard's contradiction check (#635 R13) also never fires with a name list, and its per-context form isn't addressed.
- **PR-004, MAJOR, fixed.** Fixed by Phase B item 4: the per-context branch runs only once `design.md` exists.
- **PR-005, MINOR, fixed.** Fixed by the test setup through `_design_exceptions.write` and the refusals added to the spec's Edge Cases.
- **PR-006, MINOR, fixed.** Fixed by Phase D item 2, which names the `Contexts:` line rather than the section.
- **PR-007, MINOR, fixed.** Fixed by Phase B item 5's `; ` join, plain-status display, and drawing-first order.
- **PR-008, MINOR, fixed.** Fixed by Phase A item 5's `--context` text and the grep in Phase D item 3.
- **PR-009, MINOR, fixed.** Fixed by the test lists in Phases A, B, and C.
- **PR-010, MINOR, fixed.** Fixed by Phase A item 6's name shape check and doctor finding.
- **PR-011, MINOR, fixed.** Fixed by Phase C item 5.
- **PR-012, MINOR, open.** When git can't answer, the per-context branch returns the git-unanswered reason without asking `blocks`, judges "can't answer" from `touched_on_this_branch` (which reads uncommitted changes as an answer when there's no trunk), and hides the FR-007 and FR-008 pauses, which don't depend on git.
- **PR-013, MINOR, open.** The `; `-joined display wraps under the step table past the terminal width, since the pass row prints without `soft_wrap`.
- **PR-014, MINOR, open.** Project Structure leaves out `_pipeline.py`, `_design_exceptions.reasons`, the `check-body` change, `test_pipeline_state_names.py`, `design-exceptions-module.md`, `architecture-design`, `design-passes`, `model-the-domain`'s `arch none` mentions, and `commands/speckit.brainstorm.md`. `design-passes` also tells the agent not to run `arch none`, so it doesn't belong in Phase A item 5's list.

## Review 2026-10-26T22:03Z

- Verdict: satisfied
- Reviewed: plan.md 052118b427ac11d993cf684778d9dfb5b43cc708, spec.md 9e4466af61c0c66b4cc01b8de12266a191a17ae4, .specify/memory/constitution.md absent, design.md 8f1a1ef55b9d0fd9742190c2401d3adcd4b2b7be, docs/architecture/design/649-contexts-module.md 0d1a60c0e6cb2819c8390d6cd4b960bbaebaadb8, docs/architecture/domain-page-names-contexts.md 5aa73e748adccc3798b780c21f1ffe0371951f77, docs/architecture/promised-evidence-blocks-on-silence.md 1c979cb4270a3c2a148363ae5b48dfa4a731b94f, research.md fa5daf450c9583405f80e13a2cc486ab65d8883c, data-model.md 348ab147f89f686d144ef3f7a7a71fb6d37f465a, contracts/cli.md 66e0635fe5399818d52791c219a7a3914f9f99c0, quickstart.md b5d38b715c8faf29213d352c88eacaf4e078725a, ../635-arch-folder-per-branch-notes/plan.md 8ae93cbeb83f687d21b77b9d6536af1abf944a78, ../635-arch-folder-per-branch-notes/data-model.md 7ebd7b9c5c9dc37045542a180d37a7a5cc497009, ../635-arch-folder-per-branch-notes/research.md 666038c954094c11ba76fb573adcfbe687e6d72d, ../635-arch-folder-per-branch-notes/contracts/cli.md dd2c1c43ae17379248f7572c0257f79cce3e4475, ../648-design-gate/plan.md 917273ccd1741eff61dfe1348db5ca30abd3a6b7, ../648-design-gate/research.md e33d7568951e6ca8268bba5d3d0ed83d32b7a8aa, plan-review.plan.md a224da8b4e7adee430a75d217b61b54973930404 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 6 · Fixed since the earlier review: 1
- Detail: /Users/andremarin/Development/wfctl-specs/649-design-checks-by-context/plan-review.md

The review ran in a fresh-context subagent after the plan walkthrough, where the user settled PR-003. The plan, spec, and research changed to match that decision. #635's plan, data model, and research had also changed since the earlier review, so the reviewer read them again, and it read #635's CLI contract for the first time.

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-014, PR-017) |
| Requirements and traceability | Outstanding (PR-014) |
| Architecture and boundaries | Outstanding (PR-012, PR-015, PR-016; PR-003 fixed) |
| Adversarial implementation and verification | Outstanding (PR-012, PR-013, PR-015, PR-016; PR-003 fixed) |
| Security and reliability | Resolved (PR-002, PR-010 fixed) |

### Findings

- **PR-001, PR-002, PR-004 to PR-011, fixed.** These are unchanged since the earlier review.
- **PR-003, MAJOR, fixed.** `_observe` now calls `_evidence.context_gap`, the function the architecture check calls, with no `spec.md` exit, so it no longer conflicts with #635 R6. The guard's per-context check is now stated against what #635 R13 checks. FR-020, FR-021, R7, R8, and two new tests agree with it.
- **PR-012, MINOR, open.** `context_gap` still takes git's silence from `touched_on_this_branch` without asking `blocks`, and applies it before the FR-007 and FR-008 pauses. Because the function is now shared, the Boundary line inherits the same faults.
- **PR-013, MINOR, open.** The `; `-joined display still wraps under the step table, and neither the plan nor the contract changed here.
- **PR-014, MINOR, open.** Project Structure still leaves out `_pipeline.py`, `reasons`, `test_pipeline_state_names.py`, `design-exceptions-module.md`, `architecture-design`, `design-passes`, `speckit.brainstorm.md`, and now `context_gap`. `design-passes` still contradicts its own Step 2.
- **PR-015, MINOR, open, new.** The guard's per-context check names `test_worktree_guard.py`, while #635 now puts the record checks in `_record_gate.py` and `test_record_gate.py`. It also leaves open a `context` argument on `_design_exceptions.path`, its order against #635 R14, whether the "allowed" test's record is accepted, whether R12's skip covers an inherited per-context "no", and where the name list is read from.
- **PR-016, MINOR, open, new.** `context_gap(…, level)` doesn't say how a level picks its record folder and git scope, since the `Level` constants don't carry either. Phase C item 1 doesn't say whether the software design check calls it.
- **PR-017, MINOR, open, new.** `contracts/cli.md` has no section for `wfctl end` or the guard's new reading and refusal, and `data-model.md` doesn't name either reader.
