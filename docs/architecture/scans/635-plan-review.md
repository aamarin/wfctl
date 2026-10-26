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

## Review 2026-10-26T10:56Z

- Verdict: satisfied
- Reviewed: plan.md aaff817f79ee1d0f216461909ac9f4115f186dfe, spec.md fd21899dbc01b9e61cf4237b06d282770fc4f2d9, .specify/memory/constitution.md absent, design.md adba5c0028c3f61f4b7200f1a2f140d0268f5169, docs/architecture/design-exceptions-live-with-specs.md 93babce89357bb3ebdd684717f1c5e79f9cd495d, docs/architecture/design/design-exceptions-module.md 8a09f5f0100ece4b9f9162b69168f98e6beb6cf2, research.md dd37e9f3d27bfd22f56ca7dd16e59193e8e88cc7, data-model.md c35bdb77a63bc44e80279f62ed278084612dfd37, contracts/cli.md 640b4d90c324b2ad8cdc3907d6d4b2cb643db225, quickstart.md c2e5eb290bb8cfb6a5ce06374365602228f9017f, docs/architecture/an-absent-artifact-is-claimed-not-inferred.md 2e919d537ab879730cb49f890311e1d825a50ce9, plan-review.plan.md 65858e944fe16f8609724b2dad26f48dfb9ad9b7 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 2 · Fixed since the earlier review: 5
- Detail: /Users/andremarin/Development/wfctl-specs/635-arch-folder-per-branch-notes/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Resolved (PR-010, PR-013 fixed) |
| Requirements and traceability | Resolved (PR-013 fixed) |
| Architecture and boundaries | Resolved (PR-009, PR-010 fixed) |
| Adversarial implementation and verification | Outstanding (PR-015; PR-009, PR-011, PR-012 fixed) |
| Security and reliability | Outstanding (PR-014) |

### Findings

- **PR-014, MINOR, open.** `plan.md §Order of work` step 7 stores each moved
  folder with `WFCTL_BRANCH=<branch> wfctl store specs`, which logs each push
  in that merged branch's state directory rather than this one. Stands because
  a restarted session on this branch can't see the 5 pushes, and step 7 doesn't
  say so or record them here.
- **PR-015, MINOR, open.** Step 7's level-3 grep says to confirm every hit is a
  call into `_design_exceptions`, but a call never matches the pattern, and a
  rewritten `--help` docstring naming `exceptions/boundary.md` would be a hit
  that isn't a call. Stands because the pass condition is ambiguous.
- **PR-009, MINOR, fixed.** Fixed by `research.md R8` item 8, which names the
  `tests/test_paths.py` import and test and the `test_pipeline_commands.py:341`
  docstring, and R4, which accepts the one-time `record:` line.
- **PR-010, MINOR, fixed.** Fixed by 024a991, which revises the level-2
  record's Consequences and Log, and by the level-3 grep added to step 7.
- **PR-011, MINOR, fixed.** Fixed by `research.md R11`, which states that an
  own folder replaces the epic's for every artifact.
- **PR-012, MINOR, fixed.** Fixed by step 7 and `research.md R10`, which name
  the store command once per folder.
- **PR-013, MINOR, fixed.** Fixed by the article edits across the plan,
  research, data model, contracts, and design.md.

## Review 2026-10-26T16:55Z

- Verdict: unsatisfied
- Reviewed: plan.md b7f4e9d5dfc298f659768eda1864cae678ab9a2d, spec.md bbacffe6230f4e0fb15b537c126afdcecdb9cc75, .specify/memory/constitution.md absent, design.md adba5c0028c3f61f4b7200f1a2f140d0268f5169, docs/architecture/design-exceptions-live-with-specs.md b76607ed4af18b7ec7b7678c33ac6ebbf8e4e5c5, docs/architecture/design/design-exceptions-module.md 8a09f5f0100ece4b9f9162b69168f98e6beb6cf2, research.md b63fdc4b666c5a9416feabe37ea6575ebfff87b6, data-model.md 480454f73c61f26c2f696f93e9bb0f5a643f31a1, contracts/cli.md dd2c1c43ae17379248f7572c0257f79cce3e4475, quickstart.md c2e5eb290bb8cfb6a5ce06374365602228f9017f, docs/architecture/an-absent-artifact-is-claimed-not-inferred.md 2e919d537ab879730cb49f890311e1d825a50ce9, plan-review.plan.md aaff817f79ee1d0f216461909ac9f4115f186dfe (base)
- Review type: re-review
- Open: BLOCKER 1 · MAJOR 3 · MINOR 7 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/635-arch-folder-per-branch-notes/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-016, PR-021) |
| Requirements and traceability | Outstanding (PR-019, PR-022) |
| Architecture and boundaries | Outstanding (PR-016, PR-017, PR-023) |
| Adversarial implementation and verification | Outstanding (PR-015, PR-018, PR-020) |
| Security and reliability | Outstanding (PR-014, PR-024) |

### Findings

- **PR-016, BLOCKER, open.** `spec.md §FR-016` and `§FR-017` scope the
  guard's two refusals to level-2 records, under the same rule as the
  "architecture accepted" fact. `plan.md §The callers` item 7 lists every path
  `git diff --name-only` reports outside `non_record_subtrees`, which takes in
  level-3 records under `design/`, `views/current-state.md`, and deleted
  files. Stands because, built that way, the guard refuses this branch's own
  PR on the deleted step claims and holds every branch that writes a level-3
  record.
- **PR-017, MAJOR, open.** `research.md R14` says proposed records on `main`
  hold no PR, but a branch that edits any of the 47 proposed records is held
  under the fact's rule. Stands because R14 doesn't say whether an edit holds
  the PR, and the design gate's `added_only` rule says it shouldn't.
- **PR-018, MAJOR, open.** `plan.md §The callers` item 7 reads records
  "between the trunk and `head`" without naming the range, and `_judge` holds
  a trunk name with `origin/` stripped. Stands because a two-dot diff or a
  stale local `main` lists records the branch never touched.
- **PR-019, MAJOR, open.** `spec.md §FR-015` and `plan.md §The callers` item 6
  compare every exception in the resolved spec folder, including an epic's.
  Stands because a sub-issue whose own record answers yes would have to quote
  the epic's "no new boundary" reason to pass `check-body`.
- **PR-014, MINOR, open.** Step 9 stores the 5 moved folders under
  `WFCTL_BRANCH`, which logs each push in that branch's state directory.
  Stands because step 9 doesn't record the pushes on this branch.
- **PR-015, MINOR, open.** Step 9's level-3 grep can only pass on an empty
  result, though it reads as if hits are expected. Stands because the pass
  condition is unchanged.
- **PR-020, MINOR, open.** The "own spec folder" test in item 7.1 compares
  against `spec_root / branch`, which misses a folder `resolve_spec_dir`
  matched by issue key. Stands because R13 then fails open for that branch.
- **PR-021, MINOR, open.** `contracts/cli.md` shows the new `check-body`
  findings with `✗`, and `check_body_cmd` prints every finding with `⚠`.
  Stands because the story 5 tests assert on the contract.
- **PR-022, MINOR, open.** `research.md R15` doesn't say how
  `architecture-decisions` learns the branch has a boundary exception, and R9's
  list of texts naming the folder leaves the skill out. Stands because the
  status payload carries no exception field.
- **PR-023, MINOR, open.** The plan moves `RULED_ON` to save loading modules
  "on every Bash call", but the guard loads them only on a command that opens
  or merges a PR, and `resolve_spec_dir` loads `rich` anyway. Stands because
  the stated reason is inaccurate.
- **PR-024, MINOR, open.** `research.md R14` presents the refusal as a human
  checkpoint, and an agent can run `wfctl arch accept` with any citation.
  Stands because R14 doesn't name the tamper-evident ceiling that
  `a-human-accepts-a-decision.md` accepts.
- **PR-001 to PR-013, fixed.** Each stays fixed, for the reasons the earlier
  review gave. The spec and research revisions leave their evidence intact.

## Review 2026-10-26T19:54Z

- Verdict: unsatisfied
- Reviewed: plan.md 4284a233b95e5b813ccbf37e287ad88505ccc18a, spec.md bbacffe6230f4e0fb15b537c126afdcecdb9cc75, .specify/memory/constitution.md absent, design.md adba5c0028c3f61f4b7200f1a2f140d0268f5169, docs/architecture/design-exceptions-live-with-specs.md b76607ed4af18b7ec7b7678c33ac6ebbf8e4e5c5, docs/architecture/design/design-exceptions-module.md 8a09f5f0100ece4b9f9162b69168f98e6beb6cf2, research.md b63fdc4b666c5a9416feabe37ea6575ebfff87b6, data-model.md 480454f73c61f26c2f696f93e9bb0f5a643f31a1, contracts/cli.md dd2c1c43ae17379248f7572c0257f79cce3e4475, quickstart.md c2e5eb290bb8cfb6a5ce06374365602228f9017f, docs/architecture/an-absent-artifact-is-claimed-not-inferred.md 2e919d537ab879730cb49f890311e1d825a50ce9, plan-review.plan.md b7f4e9d5dfc298f659768eda1864cae678ab9a2d (base)
- Review type: re-review
- Open: BLOCKER 1 · MAJOR 3 · MINOR 8 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/635-arch-folder-per-branch-notes/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-016) |
| Requirements and traceability | Outstanding (PR-016, PR-019, PR-022) |
| Architecture and boundaries | Outstanding (PR-016, PR-017, PR-023, PR-025) |
| Adversarial implementation and verification | Outstanding (PR-014, PR-015, PR-016, PR-018, PR-019, PR-020, PR-021, PR-025) |
| Security and reliability | Outstanding (PR-014, PR-016, PR-017, PR-024) |

### Findings

- **PR-016, BLOCKER, open.** `plan.md §The callers` item 7 now lists only
  `.md` files directly in the arch root and drops deleted files, the same set
  `_branch_records` reads, and step 8 tests it. `data-model.md §The guard's
  record checks` item 1 still lists every path `git diff --name-only` reports
  outside `non_record_subtrees`. Stands because the two artifacts give
  different record sets for a refusal that gates every PR, and `tasks` reads
  both. The fix belongs in `data-model.md`, which a revise run doesn't edit.
- **PR-017, MAJOR, open.** `research.md R14` says proposed records on `main`
  hold no PR, but a branch that edits any of the 47 proposed records is held
  under the fact's rule. Stands because R14 still doesn't state that cost, and
  step 8's new equality test makes the edits-included set the expected one.
- **PR-018, MAJOR, open.** `plan.md §The callers` item 7 still reads records
  "between the trunk and `head`" without naming the range, and `_judge` holds
  a trunk name with `origin/` stripped. Stands because a two-dot diff or a
  stale local `main` lists records the branch never touched, and no fixture in
  step 8 moves the trunk after the branch point.
- **PR-019, MAJOR, open.** `spec.md §FR-015` and `plan.md §The callers` item 6
  compare every exception in the resolved spec folder, including an epic's.
  Stands because a sub-issue whose own record answers yes would have to quote
  the epic's "no new boundary" reason to pass `check-body`.
- **PR-025, MINOR, open.** Item 7 doesn't say how the guard lists the arch
  root's subdirectories at `head`. Stands because copying `_branch_records`,
  which reads the working tree, would let a merge run from the `main`
  checkout list files under a subdirectory the branch adds.
- **PR-014, PR-015, PR-020 to PR-024, MINOR, open.** Each stands for the
  reason the 16:55Z review gave, since the text it cites didn't change.
- **PR-001 to PR-013, fixed.** Each stays fixed, for the reasons the earlier
  reviews gave.

## Review 2026-10-26T20:09Z

- Verdict: satisfied
- Reviewed: plan.md adfd05636fe410e3582bcf495a841812a495fb53, spec.md 24be2267182d5aa3b1e8cbe3556f701ffe8da888, .specify/memory/constitution.md absent, design.md adba5c0028c3f61f4b7200f1a2f140d0268f5169, docs/architecture/design-exceptions-live-with-specs.md b76607ed4af18b7ec7b7678c33ac6ebbf8e4e5c5, docs/architecture/design/design-exceptions-module.md 8a09f5f0100ece4b9f9162b69168f98e6beb6cf2, research.md 99477b1879c374eac3b8cd5c296ae0d3da578474, data-model.md 721a5a27cabc13facc346ffbb591d67819d4bf58, contracts/cli.md dd2c1c43ae17379248f7572c0257f79cce3e4475, quickstart.md c2e5eb290bb8cfb6a5ce06374365602228f9017f, docs/architecture/an-absent-artifact-is-claimed-not-inferred.md 2e919d537ab879730cb49f890311e1d825a50ce9, plan-review.plan.md 4284a233b95e5b813ccbf37e287ad88505ccc18a (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 9 · Fixed since the earlier review: 5
- Detail: /Users/andremarin/Development/wfctl-specs/635-arch-folder-per-branch-notes/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-021, PR-027) |
| Requirements and traceability | Outstanding (PR-022, PR-027) |
| Architecture and boundaries | Outstanding (PR-023, PR-026) |
| Adversarial implementation and verification | Outstanding (PR-015, PR-020, PR-028) |
| Security and reliability | Outstanding (PR-014, PR-024) |

### Findings

- **PR-026, MAJOR, open.** `research.md R14` and `plan.md §Complexity
  Tracking` say this PR waits on #635's two records. The guard holds it on
  `design-exceptions-live-with-specs.md` and on
  `an-absent-artifact-is-claimed-not-inferred.md`, which was proposed for #339
  and is edited on this branch, while the level-3 record never holds it.
  Stands because R14 also says an edit to a record held as proposed on purpose
  belongs on the branch that validates it, and `research.md R9` item 10 makes
  that edit here, so the plan doesn't say which of the two gives way.
- **PR-027, MINOR, open.** `data-model.md §"Moves a boundary?" PR section`
  still says `check-body` reports every exception. Stands because it lacks the
  inherited-exception skip FR-015 now requires.
- **PR-028, MINOR, open.** `plan.md §The callers` item 7 uses the trunk value
  before `_judge` strips `origin/`, and `_record_gate.refusal` takes no trunk
  argument. Stands because the plan doesn't say whether the trunk is passed in
  or looked up again.
- **PR-016, BLOCKER, fixed.** Fixed by `data-model.md §The guard's record
  checks`, which now uses the same range, deleted-file filter, and top-level
  `.md` rule as `plan.md §The callers` item 7.
- **PR-017, MAJOR, fixed.** Fixed by `research.md R14`, which now says an
  edit to a proposed record holds the PR, gives the reason, and names the cost.
- **PR-018, MAJOR, fixed.** Fixed by `plan.md §The callers` item 7 and
  `data-model.md`, which name the three-dot range from the unstripped
  `trunk_branch` value, and by the step 8 fixture where the trunk moves after
  the branch point.
- **PR-019, MAJOR, fixed.** Fixed by `spec.md §FR-015`, `research.md R12` and
  `plan.md §The callers` item 6, which skip an inherited boundary exception
  when the branch touches a level-2 record, with a step 7 test for both sides.
- **PR-025, MINOR, fixed.** Fixed by `plan.md §The callers` item 7, which keeps
  only diff paths whose parent is the arch root and that end in `.md`.
- **PR-014, PR-015, PR-020 to PR-024, MINOR, open.** Each stands for the
  reason the 16:55Z review gave, since the text it cites didn't change.
  PR-020's "named after the branch" test now also drives the R12 skip.
- **PR-001 to PR-013, fixed.** Each stays fixed, for the reasons the earlier
  reviews gave.
