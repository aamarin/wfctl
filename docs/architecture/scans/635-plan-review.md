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
