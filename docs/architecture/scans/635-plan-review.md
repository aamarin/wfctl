# Plan review scan for #635

## Review 2026-10-25T22:48Z

- Verdict: satisfied
- Reviewed: plan.md ef0e3c8e6a6c484a6c2a4f0e7590a06c834d698d, spec.md f47a34de1f626076b2e3e11b7313eb498c0b9a5f, .specify/memory/constitution.md absent, design.md 28f5cd72a05cff93d06b8c3d9be004ac62c1c08e, docs/architecture/design-exceptions-live-with-specs.md 4050d8b683931fd8a1f34d539403abb11cb823a3, docs/architecture/design/claims-module.md e5e60214b2030525f1f880475adfed65c59a00b1, research.md 8e9630366424840bfb3dc36eee97a316f143b79c, data-model.md 6b0fb1cbbe77caafa264fe012cd1405af32d53ad, contracts/cli.md 0902aa10d1e35fff19f37172bc640ef79c7c7cd1, quickstart.md e11da251b31dfb4c5d33d176ddcdce90b2126c7e, docs/architecture/an-absent-artifact-is-claimed-not-inferred.md 2e919d537ab879730cb49f890311e1d825a50ce9
- Review type: full (no earlier review)
- Open: BLOCKER 0 · MAJOR 1 · MINOR 7 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/635-arch-folder-per-branch-notes/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Outstanding (PR-002, PR-005, PR-008) |
| Architecture and boundaries | Outstanding (PR-001, PR-006, PR-007) |
| Adversarial implementation and verification | Outstanding (PR-003, PR-004) |
| Security and reliability | Clear |

### Findings

- **PR-001, MAJOR, open.** `spec.md §Key Entities` keeps one boundary
  exception per branch, but `plan.md §The callers` stores claims per spec
  folder. `resolve_spec_dir` sends every sub-issue branch of a decomposed epic
  to the epic's folder (`_paths.py:854-867`), so one sibling's `step none` or
  `arch none` would apply to all of them. Stands because the plan doesn't
  mention the shared-folder case.
- **PR-002, MINOR, open.** `research.md R3` checks the claim before git, so a
  branch with a claim is released when git can't answer, where today it's held.
  Stands because SC-003 lists only the old-file case as a change in behavior,
  and no test covers this one.
- **PR-003, MINOR, open.** `tests/test_warnings_after_gate.py:271` writes a
  step claim by hand under the arch root and will fail once `_step_claims` is
  deleted. Stands because `research.md R8` doesn't list it.
- **PR-004, MINOR, open.** Spec scenarios 1.2, 1.3, and 2.2 and the two tests
  `claims-module.md §Verification` asks for have no named CLI test. Stands
  because the spec's Validation Strategy asks for one per scenario, and 1.2 is
  covered only by hand.
- **PR-005, MINOR, open.** The `arch_none_cmd` and `step_none_cmd` docstrings,
  which are the `--help` text, and `architecture-design/SKILL.md:69-71` still
  say the claim lands in the change under review. Stands because
  `research.md R9` leaves them unchanged, against FR-013.
- **PR-006, MINOR, open.** `an-absent-artifact-is-claimed-not-inferred.md`
  still says a claim is committed into the change under review, which the
  level-2 record reverses. Stands because the plan's file list doesn't include
  it.
- **PR-007, MINOR, open.** SC-004's "one edit in one module" holds only for
  code, since the skills and the PR template comment also name `claims/`.
  Stands because the plan doesn't say SC-004 is limited to code.
- **PR-008, MINOR, open.** The spec's Assumptions say #382 gets a comment, and
  `plan.md §Order of work` has no step for it.

## Review 2026-10-25T23:33Z

- Verdict: satisfied
- Reviewed: plan.md 65858e944fe16f8609724b2dad26f48dfb9ad9b7, spec.md fd21899dbc01b9e61cf4237b06d282770fc4f2d9, .specify/memory/constitution.md absent, design.md 7e9dcb35ff751dca0699c399d637e4ed52b4141e, docs/architecture/design-exceptions-live-with-specs.md 3c4ccb64482135474c453b7197f23676a5269e01, docs/architecture/design/design-exceptions-module.md 8a09f5f0100ece4b9f9162b69168f98e6beb6cf2, research.md a6b032a2261ef4638dad8fb040e0ea39191470e3, data-model.md cb488fc3bc980e88311b01fe3a4e665be854e404, contracts/cli.md 0b2b3cc3dc0f28d4b8e3d1f90606c7bd1cda4df8, quickstart.md c2e5eb290bb8cfb6a5ce06374365602228f9017f, docs/architecture/an-absent-artifact-is-claimed-not-inferred.md 2e919d537ab879730cb49f890311e1d825a50ce9, plan-review.plan.md ef0e3c8e6a6c484a6c2a4f0e7590a06c834d698d (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 5 · Fixed since the earlier review: 8
- Detail: /Users/andremarin/Development/wfctl-specs/635-arch-folder-per-branch-notes/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-010, PR-013) |
| Requirements and traceability | Outstanding (PR-013; PR-002, PR-005, PR-008 fixed) |
| Architecture and boundaries | Outstanding (PR-009, PR-010; PR-001, PR-006, PR-007 fixed) |
| Adversarial implementation and verification | Outstanding (PR-009, PR-011, PR-012; PR-003, PR-004 fixed) |
| Security and reliability | Clear |

### Findings

- **PR-009, MINOR, open.** Removing `STEP_CLAIMS_DIR` breaks
  `tests/test_paths.py`, which imports it at module level and asserts it at
  :1005, and `research.md R8` lists neither. The docstring at
  `tests/test_pipeline_commands.py:341` still names `step-claims/`. Deleting the
  5 step claims on this branch also makes `records_on_this_branch` print a
  `record:` line for a record nobody decided. Stands because the plan doesn't
  cover any of the three.
- **PR-010, MINOR, open.** The level-2 record's Consequences still says the 5
  step claims are deleted, against FR-012 and `research.md R10`, and the
  level-3 record's grep check has no step in the Order of work. Stands because
  the plan says it follows both records as written.
- **PR-011, MINOR, open.** A sub-issue's own spec folder replaces the epic's for
  every artifact, so the sub-issue also loses the epic's spec, plan, and tasks
  and starts again at brainstorm. Stands because the spec and plan say only
  that it starts with no exceptions, and nothing at write time warns that a
  sub-issue's exception applies to its siblings.
- **PR-012, MINOR, open.** Order of work step 7 doesn't say how the 5 moved
  folders reach `specs-trunk`, since `wfctl store specs` stores only the
  current branch's folder. Stands because no step names the command.
- **PR-013, MINOR, open.** The rename left "a exception" and "a `exceptions/`"
  across the plan, research, data model, contracts, and design.md, and the
  plan's "two docstrings" doesn't match the three test files it lists.
- **PR-001, MAJOR, fixed.** Fixed by `research.md R11`, the spec's edge cases
  and Key Entities, and `plan.md §Epic sub-issues`, which state that an epic's
  sub-issues share its folder on purpose.
- **PR-002, MINOR, fixed.** Fixed by SC-003, which now names the
  git-can't-answer case, and `research.md R8` item 9.
- **PR-003, MINOR, fixed.** Fixed by `research.md R8` item 8.
- **PR-004, MINOR, fixed.** Fixed by `research.md R8` item 10.
- **PR-005, MINOR, fixed.** Fixed by `research.md R9` items 8 and 9.
- **PR-006, MINOR, fixed.** Fixed by `research.md R9` item 10 and the plan's
  file list.
- **PR-007, MINOR, fixed.** Fixed by SC-004 and the closing paragraph of
  `research.md R9`.
- **PR-008, MINOR, fixed.** Fixed by `plan.md §Order of work` step 10.
