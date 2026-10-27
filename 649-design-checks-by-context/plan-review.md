# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 052118b427ac11d993cf684778d9dfb5b43cc708 | technical strategy |
| spec.md | 9e4466af61c0c66b4cc01b8de12266a191a17ae4 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | 8f1a1ef55b9d0fd9742190c2401d3adcd4b2b7be | design-record index |
| docs/architecture/design/649-contexts-module.md | 0d1a60c0e6cb2819c8390d6cd4b960bbaebaadb8 | design record |
| docs/architecture/domain-page-names-contexts.md | 5aa73e748adccc3798b780c21f1ffe0371951f77 | accepted level-2 record the plan builds on |
| docs/architecture/promised-evidence-blocks-on-silence.md | 1c979cb4270a3c2a148363ae5b48dfa4a731b94f | record #648 amends, read for PR-012 |
| research.md | fa5daf450c9583405f80e13a2cc486ab65d8883c | planning evidence |
| data-model.md | 348ab147f89f686d144ef3f7a7a71fb6d37f465a | planning evidence |
| contracts/cli.md | 66e0635fe5399818d52791c219a7a3914f9f99c0 | planning evidence |
| quickstart.md | b5d38b715c8faf29213d352c88eacaf4e078725a | planning evidence |
| ../635-arch-folder-per-branch-notes/plan.md | 8ae93cbeb83f687d21b77b9d6536af1abf944a78 | unmerged dependency (#635) |
| ../635-arch-folder-per-branch-notes/data-model.md | 7ebd7b9c5c9dc37045542a180d37a7a5cc497009 | unmerged dependency (#635) |
| ../635-arch-folder-per-branch-notes/research.md | 666038c954094c11ba76fb573adcfbe687e6d72d | unmerged dependency (#635) |
| ../635-arch-folder-per-branch-notes/contracts/cli.md | dd2c1c43ae17379248f7572c0257f79cce3e4475 | unmerged dependency (#635), read for PR-015 and PR-017 |
| ../648-design-gate/plan.md | 917273ccd1741eff61dfe1348db5ca30abd3a6b7 | unmerged dependency (#648) |
| ../648-design-gate/research.md | e33d7568951e6ca8268bba5d3d0ed83d32b7a8aa | unmerged dependency (#648) |
| plan-review.plan.md | a224da8b4e7adee430a75d217b61b54973930404 | base of this re-review |

## Review scope

- Re-review: the plan copy's identity equals the earlier report's `plan.md`
  row, so the review diffed the copy against `plan.md`.
- Changed since the earlier report: `plan.md §Phase B item 4` (a new paragraph
  introducing `_evidence.context_gap`), `§Phase B item 7` (the Boundary line
  and guard bullets rewritten), `§Phase B item 8` (two new test bullets), and
  `§Project Structure` (the `cli.py` comment, a guard line, and two test
  files). They were reviewed together with the parts that refer to them:
  Phase B items 3 and 6, Phase C item 1, and the requirement trace.
- Inputs that changed, named by the caller and confirmed by identity:
  `spec.md` (FR-020, FR-021, and one new edge case) and `research.md` (R7 and
  R8). Each was re-read in full, and the whole of `plan.md` was reviewed
  against it.
- Inputs that changed and the caller didn't name: #635's `plan.md`,
  `data-model.md`, and `research.md`. Since the earlier review, #635 named the
  guard's module (`_record_gate.py`), added `_design_exceptions.path`, and
  added a sub-issue skip to `check-body` (R12). The plan and data model were
  re-read in full, and research R5, R6, and R11 to R15. #635's
  `contracts/cli.md` is a new row, read for the guard's refusal text and the
  Boundary line table.
- Unchanged since the earlier report, by identity: `design.md`, both design
  records, `promised-evidence-blocks-on-silence.md`, `data-model.md`,
  `contracts/cli.md`, `quickstart.md`, and #648's plan and research.
- Lenses: requirements and traceability, architecture and boundaries, and
  adversarial implementation and verification. Dependency and scope are folded
  into architecture, and verification and risk into adversarial.
- Conditional lenses: security and reliability applied, narrowly. The feature
  is an integrity control that the agent under review must not be able to
  bypass (SC-001), it turns a user-written name into a folder under the spec
  folder, and this revision extends the worktree guard.
- Design records: 1 listed in design.md,
  `docs/architecture/design/649-contexts-module.md`. The level-2 record the
  section names in prose, `domain-page-names-contexts.md`, was read as well.
- Existing code inspected: `wfctl/cli.py` (`_observe`, `_BOUNDARY`, `end_cmd`),
  and which test files cover `_guard` and `_review_gate`
  (`tests/test_worktree_guard.py`, `tests/test_review_gate.py`). The earlier
  review's code claims about `_paths`, `_pipeline`, and `_evidence` were not
  re-checked, since the branch's commits since then touch no code.
- Dependencies: #635 and #648 are still plans with no code under `wfctl/`.
  `wfctl/_record_gate.py` doesn't exist yet, so claims about the guard were
  checked against #635's plan, data model, research, and contract.
- Reviewers: the lenses above, run in sequence by one agent with a fresh
  context.

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 6

No BLOCKER findings identified in this review. PR-003 is fixed. The plan now
routes the session summary's Boundary line through `_evidence.context_gap`, the
same function the architecture check uses, without the `spec.md` exit that #635
R6 ruled out. It also restates the guard decision against what #635 R13
checks, and defines the per-context form of that check. PR-012, PR-013, and
PR-014 still stand. PR-012 now reaches the Boundary line too, since it lives in
the shared function, and PR-014 is narrower. Three new MINOR findings cover the
guard extension's details (PR-015), how `context_gap` picks a level's records
(PR-016), and the contract and data model, which don't carry the two new
readers (PR-017).

## Findings

### PR-001: Placed where the plan says, the per-context check never runs for a branch that touched a record

- Priority: MAJOR
- Category: Dependency / Feasibility
- Status: fixed
- Evidence:
  - `plan.md §Phase B item 4`: the per-context branch is step 3, ahead of
    #635's boundary exit and #648's git verdict, and nothing after it runs.
  - `plan.md §Phase C item 1`: the software design branch sits ahead of #648's
    `blocks`-false exit.
- Finding: The plan before the second review placed the branch after #648's
  exit for a satisfied verdict, so User Story 1's branch would have read done.
- Why it matters: That was the gap #649 exists to close.
- Suggested response: Fixed by `plan.md §Phase B item 4` and `§Phase C item 1`.
- Corroborated by: adversarial implementation, architecture and boundaries

### PR-002: A whole-pass claim still clears a context-checked pass at read time

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Phase B items 2 and 6`: with a name list, the bare commands
    refuse, and the claims dict drops both brainstorm passes before
    `_pass_states` reads it.
  - `plan.md §Phase B item 8`: `test_pipeline_state_names.py` tests both
    directions.
- Finding: The earlier plan enforced FR-011 only when a claim was written.
- Why it matters: Either claim would have let a branch leave brainstorm with no
  answer for any listed context.
- Suggested response: Fixed by `plan.md §Phase B items 2, 6 and 8`.
- Corroborated by: adversarial implementation, security and reliability

### PR-003: The session summary's Boundary line doesn't follow the per-context check, and the plan says it does

- Priority: MAJOR
- Category: Boundary / Ownership Concern
- Status: fixed
- Evidence:
  - `plan.md §Phase B item 4`, last paragraph: gathering the records, calling
    `pause`, and the git fallback now live in one function,
    `_evidence.context_gap(repo_root, arch, spec_dir, level)`, which the
    architecture reader and `_observe` both call.
  - `plan.md §Phase B item 7`, second bullet: with a name list and a
    `design.md`, `_observe` maps no gap to "answered", a gap to "unanswered",
    and a gap git couldn't check to "unknown", and it skips the `spec.md`
    exit. `spec.md §FR-020` and `research.md §R7` say the same.
  - `../635-arch-folder-per-branch-notes/research.md §R6`: rejects
    `_architecture_answered` because of its `spec.md` exit. `context_gap` has
    no such exit, so the plan no longer conflicts with R6.
  - `plan.md §Phase B item 7`, third bullet, and `research.md §R8`: the guard
    decision is now stated against what #635 R13 checks, a boundary exception
    in the branch's own spec folder together with a level-2 record the branch
    touches. The per-context form refuses only when the record governs the same
    context. `spec.md §FR-021` and the new edge case agree.
  - `plan.md §Phase B item 8`: `test_end_reports_observations.py` tests both
    readings the earlier finding named, and a guard test covers a matching and
    a non-matching record.
- Finding: Both parts of the earlier finding are addressed. The Boundary line
  and `wfctl status` now read from one function, and the guard can fire in a
  repo with a name list.
- Why it matters: The Boundary line is the first thing a restarted session
  reads. A "no" written early and contradicted by a later record no longer
  reaches the reviewer unchanged.
- Suggested response: Fixed by `plan.md §Phase B items 4, 7 and 8`. The guard
  extension's remaining details are filed as PR-015.
- Corroborated by: architecture and boundaries, adversarial implementation

### PR-004: `brainstorm` asks the changed function whether the step has started, and the `Contexts` line is written last

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Phase B item 4`, steps 3 and 4: the per-context branch runs only
    when `design.md` exists, so `brainstorm`'s pending-or-started probe is
    unchanged.
  - `plan.md §Phase A item 5`: `design-levels` decides the contexts at level 2,
    before any record.
- Finding: An earlier plan paused every branch with a record and no
  `design.md`, which read `pending`.
- Why it matters: `status` and `next` would have sent a half-done brainstorm
  back to its start.
- Suggested response: Fixed by `plan.md §Phase B item 4` and `§Phase A item 5`.
- Corroborated by: adversarial implementation

### PR-005: The bare-form refusal makes User Story 2 scenario 3 unreachable through the CLI, and the plan doesn't say how it's tested

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Phase B item 8`: the scenario is tested with `boundary.md`
    written through `_design_exceptions.write`.
- Finding: The scenario's setup was unnamed.
- Why it matters: The read side of FR-011 would have gone untested.
- Suggested response: Fixed by `plan.md §Phase B item 8`.
- Corroborated by: requirements and traceability

### PR-006: `opening-a-change` is told to fill a named section, and the skill forbids naming one

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `plan.md §Phase D item 2`: the skill names the line, not the section.
- Finding: Earlier wording had the skill name a section.
- Why it matters: `opening-a-change` Step 2 forbids a section list of its own.
- Suggested response: Fixed by `plan.md §Phase D item 2`.
- Corroborated by: architecture and boundaries

### PR-007: The done display's join, placement, and precedence are left open

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Phase B item 5` and `contracts/cli.md §wfctl status`: the
    separator, placement, and order are stated and agree.
- Finding: The separator, the placement, and the precedence were open.
- Why it matters: The contract and the code disagreed about where the display
  shows.
- Suggested response: Fixed by `plan.md §Phase B item 5`. Wrapping is PR-013.
- Corroborated by: adversarial implementation

### PR-008: FR-016's `--context` text has no phase, and skills naming a bare `arch none` aren't listed

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Phase A item 5` and `§Phase D item 3`: the text is placed, and a
    grep catches any instruction the list misses.
- Finding: The `--context` text had no phase.
- Why it matters: An agent would have met the refusal before the format.
- Suggested response: Fixed by `plan.md §Phase A item 5` and `§Phase D item 3`.
- Corroborated by: requirements and traceability

### PR-009: Phases B and C name no tests, and several scenarios have no named test

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Phase A item 7`, `§Phase B item 8`, `§Phase C item 4`, and
    `§Phase D item 3` name the tests and the checks by reading.
- Finding: Several negative paths had no named test.
- Why it matters: They were easy to leave out of a task list.
- Suggested response: Fixed by the test items above.
- Corroborated by: adversarial implementation, requirements and traceability

### PR-010: A context name becomes a directory with no shape check

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Phase A item 6`: `names` keeps only kebab-case entries, and
    `_check_arch_records` reports each dropped one.
- Finding: A name holding `/` or `..` could have written outside `exceptions/`.
- Why it matters: The list is committed repo content.
- Suggested response: Fixed by `plan.md §Phase A item 6`.
- Corroborated by: security and reliability

### PR-011: #635's records aren't listed for the layout change they describe

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `plan.md §Phase C item 5`: `design/design-exceptions-module.md` gets a Log
    line and a paragraph, or a superseding record.
- Finding: The record that owns the exceptions folder's layout would have kept
  describing a flat folder.
- Why it matters: A later reader of that record would miss the subfolders.
- Suggested response: Fixed by `plan.md §Phase C item 5`. Project Structure
  still doesn't list it (PR-014).
- Corroborated by: architecture and boundaries

### PR-012: The per-context branch decides what git's silence means itself, and asks the wrong call whether git can answer

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: open
- Evidence:
  - `plan.md §Phase B item 4`, the paragraph after the list: "When `pause`
    returns a gap and `touched_on_this_branch` is inconclusive, it returns
    #648's git-unanswered reason instead." The next paragraph moves this
    fallback into `context_gap`, unchanged.
  - `plan.md §Phase B item 7`, second bullet: `_observe` now maps "a gap git
    couldn't check" to "unknown", so the Boundary line inherits the same
    fallback.
  - `../648-design-gate/plan.md §wfctl/_evidence.py items 5 and 6`: each reader
    checks the verdict only after `blocks` has decided to hold, because
    handling `inconclusive` first would mean "the reader would be deciding for
    itself what git's silence means, which the amended record forbids".
  - `docs/architecture/promised-evidence-blocks-on-silence.md §Decision`
    (proposed): a gate "does not decide for itself what its own silence means".
  - `wfctl/_paths.py` `touched_on_this_branch`: returns `True` from
    uncommitted changes before it looks for a trunk, while
    `records_on_this_branch` returns only uncommitted records when there's no
    trunk. Unchanged since the earlier review.
  - `data-model.md §Check outcome`: the git-unanswered row still sits above the
    missing-line and unknown-name rows.
- Finding: All three parts of the earlier finding still hold, and the shared
  function now carries them into the Boundary line.
  1. `context_gap` returns the git-unanswered reason without asking `blocks`.
     The outcome is the same today, since `"repo-declared"` blocks on
     `inconclusive`, but it's the shape #648 rules out.
  2. With no trunk and one uncommitted change under the arch root, a record
     committed earlier on the branch is missing from the list. The pause names
     a context that already has a record, and the Boundary line reads
     "unanswered" for it.
  3. The git-unanswered reason also hides the missing-line and unknown-name
     pauses (FR-007, FR-008), which don't depend on git. On the Boundary line,
     a `design.md` with no `Contexts` line reads "unknown" rather than
     "unanswered" whenever git can't answer.
- Why it matters: Each case is bounded, but item 2 gives the agent and the
  next session a wrong reason, and items 1 and 3 send a fixable `design.md`
  problem through a trunk remedy first.
- Suggested response: Have `context_gap` return the git verdict alongside the
  gap, and let `_architecture_answered` hand it to
  `blocks(verdict, "repo-declared")`. Take "git can't list this branch's
  records" from `trunk_branch` being `None` or the arch root sitting outside
  the tree, not from `touched_on_this_branch`. Apply it only to the
  `unanswered` result, after the FR-007 and FR-008 checks. `_observe` can
  then read the same verdict without calling `blocks`, since it reports and
  doesn't gate.
- Corroborated by: architecture and boundaries, adversarial implementation

### PR-013: The joined display is one line, and a long one still wraps under the step table

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `plan.md §Phase B item 5`: answers are joined by `; ` "so a long list
    doesn't print as extra rows". Unchanged.
  - `contracts/cli.md §wfctl status`: the two-answer example row is about 100
    characters. Unchanged.
  - `wfctl/cli.py` status pass rows: `console.print` with no `soft_wrap`, so
    rich folds at the terminal width.
  - `wfctl/_evidence.py` `DRAWINGS_UNCHECKED` comment: "a wrapped line breaks
    under the step table and reads as a new row".
- Finding: Each answer carries its free-text reason, so two or three answers
  pass 80 columns, and the fold puts the rest of the line at column 0 under
  the table.
- Why it matters: It forces no behavior, but the contract's own example breaks
  the rule the existing comment states.
- Suggested response: Put only the context names on the row, such as
  `no: session-continuity, workmux`, and the reasons under `--all` or in the
  JSON annotation. Or print the row with `soft_wrap=True` and say so.
- Corroborated by: adversarial implementation

### PR-014: Project Structure no longer lists every file the phases change

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `plan.md §Project Structure` now lists `_observe` in the `cli.py` comment,
    a guard line, and the two new test files, which addresses part of the
    earlier finding.
  - Still missing: `wfctl/_pipeline.py` (`§Phase B item 6`),
    `_design_exceptions.reasons` in the `_design_exceptions.py` comment
    (`§Phase B item 7`), `test_pipeline_state_names.py` (`§Phase B item 8`),
    and `docs/architecture/design/design-exceptions-module.md`
    (`§Phase C item 5`).
  - New: the `_evidence.py` comment doesn't name `context_gap`
    (`§Phase B item 4`).
  - `plan.md §Phase A item 5` names `architecture-design` and `design-passes`,
    and Project Structure lists neither, nor `model-the-domain/SKILL.md`'s
    mentions of `arch none`, nor `wfctl/agents/commands/speckit.brainstorm.md`.
  - `wfctl/agents/skills/design-passes/SKILL.md` line 56 tells the agent not to
    run `wfctl arch none` on that route, while Phase A item 5 lists the skill
    among those that teach `arch none --reason`.
- Finding: The phases and Project Structure still disagree, and Project
  Structure is what a task list is most often built from.
- Why it matters: The grep in Phase A item 5 catches the skill texts. The
  `_pipeline` edit, `reasons`, `context_gap`, the record edit, and the
  claim-drop test have no such fallback.
- Suggested response: Bring Project Structure in line with the phases, and
  drop `design-passes` from the "teaches" list or say what changes there.
- Corroborated by: deterministic checks, requirements and traceability

### PR-015: The guard's per-context check names the wrong test file and leaves details #635 now specifies

- Priority: MINOR
- Category: Dependency / Feasibility
- Status: open
- Evidence:
  - `plan.md §Phase B item 8`: the guard tests go in `test_worktree_guard.py`.
    That file tests `wfctl/_guard.py`, the check on writes into other
    worktrees. The review gate is tested in `tests/test_review_gate.py`, and
    `../635-arch-folder-per-branch-notes/plan.md §Project Structure` puts the
    record checks in a new `wfctl/_record_gate.py`, tested in
    `tests/test_record_gate.py`.
  - `plan.md §Project Structure`: the guard line reads
    "(worktree guard, from #635)" and names no module.
  - `../635-arch-folder-per-branch-notes/data-model.md §_design_exceptions
    module`: `path(spec_dir, name)` is the one place that builds an exception's
    path, and `_record_gate` prints it in the refusal's `rm` line.
    `plan.md §Phase B item 1` gives a `context` argument to `write`,
    `boundary`, and `passes`, but not to `path`.
  - `../635-arch-folder-per-branch-notes/plan.md §The callers item 7`: the
    guard refuses for "the first of these that holds", the contradiction and
    then an unaccepted record (R14). The plan doesn't say where the
    per-context check sits in that order.
  - `plan.md §Phase B item 8`: the guard test expects `gh pr create` to be
    "allowed when the record governs only `install-and-drift`". Under #635
    R14, a record the branch touches that isn't accepted refuses the PR, so
    the test passes only if its fixture record is accepted, which the plan
    doesn't say.
  - `../635-arch-folder-per-branch-notes/research.md §R12`: `check-body` skips
    an inherited boundary exception when the branch touches a level-2 record.
    `plan.md §Phase B item 7`, first bullet, adds per-context reasons through
    `reasons` and doesn't say whether that skip covers an inherited
    per-context "no".
  - `plan.md §Phase B item 7`, third bullet: the check runs "with a name list"
    and doesn't say whether the guard reads the name list from the working
    tree or enumerates the subfolders of `exceptions/`. #635 R13 reads the
    records from the commit the command acts on, because the working tree can
    hold the wrong branch.
- Finding: The guard decision is sound, but its extension of #635's two readers
  leaves an implementer to work out the module, the path helper, the refusal
  order, the test file, the test fixture, and the `check-body` skip.
- Why it matters: Each item has one obvious answer once #635's plan is open,
  so no behavior is guessed. The test file and the fixture are the ones a task
  list copies as written, and both would fail on first run.
- Suggested response: Name `_record_gate.py` and `test_record_gate.py`, give
  `path` the same `context` argument, place the per-context check beside
  #635's contradiction check, state that the "allowed" fixture record is
  accepted, and say whether R12's skip applies to an inherited per-context
  "no".
- Corroborated by: architecture and boundaries, adversarial implementation

### PR-016: `context_gap` takes a level, and the plan doesn't say how the level picks the records

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `plan.md §Phase B item 4`, last paragraph: `context_gap(repo_root, arch,
    spec_dir, level)` gathers the records, calls `pause`, and applies the git
    fallback.
  - `plan.md §Phase B item 4`, the paragraph before it: the level-2 records
    come from `records_on_this_branch(repo_root, arch,
    exclude=[*non_record_subtrees(arch), arch / DESIGN_DIR])`.
  - `plan.md §Phase C item 1`: the level-3 records come from
    `records_on_this_branch(repo_root, arch / DESIGN_DIR)`, read from
    `arch / DESIGN_DIR`. It says "the same order as Phase B step 4" and doesn't
    say whether `brainstorm_software_design` calls `context_gap`.
  - `research.md §R2`: each `Level` constant carries the record noun, the pass
    name, and the "no" command, and nothing about where its records live or
    which folder the git check asks about.
- Finding: Since `context_gap` takes a level, it has to choose the record list
  and the `touched_on_this_branch` scope per level. Neither the `Level`
  constants nor the function say how. An implementer can branch on the level
  inside `context_gap`, add fields to `Level`, or have Phase C gather its own
  records and skip `context_gap`, which would put the gather-and-fallback rule
  in two places again.
- Why it matters: The choice is bounded and changes no behavior, but the third
  option undoes the reason `context_gap` exists.
- Suggested response: Say in Phase C item 1 that `brainstorm_software_design`
  calls `context_gap(..., SOFTWARE_DESIGN)`, and say where the per-level record
  folder and exclusions live, either on `Level` or as a mapping in
  `_evidence`, since `_contexts` doesn't call git.
- Corroborated by: adversarial implementation, architecture and boundaries

### PR-017: The contract and data model don't carry the two new readers

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `plan.md §Phase B item 7`: the Boundary line gets new readings with a name
    list, and the guard gets a new refusal that "names the record and the
    context, and prints the command that deletes that context's exception".
  - `contracts/cli.md`: has no `wfctl end` section and no guard section.
    `../635-arch-folder-per-branch-notes/contracts/cli.md §wfctl end` and
    `§Worktree guard` give both as a table and a literal refusal, so #649's
    contract is the place a user-visible change to them is written.
  - `data-model.md §Per-context "no"`: "Read by
    `_design_exceptions.boundary(spec_dir, context=…)` and `passes(…)`" names
    neither the guard nor `_observe`, which now both read per-context answers.
- Finding: Both artifacts were left as the earlier review read them, so the
  refusal text and the Boundary line's per-context rows exist only in the
  plan's prose.
- Why it matters: The plan's guard test asserts only refused or allowed, so
  without a contract the refusal's wording is decided during implementation.
- Suggested response: Add a `wfctl end` table for the name-list case and the
  per-context guard refusal to `contracts/cli.md`, in #635's form, and list the
  guard and `_observe` as readers in `data-model.md`.
- Corroborated by: deterministic checks

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Phase A items 1 and 6 | covered |
| FR-002 | plan.md §Phase B item 4 step 4, data-model.md §Check outcome | covered |
| FR-003 | plan.md §Phase A item 1 (`listed`) | covered |
| FR-004 | plan.md §Phase A item 2, §Phase C item 1 | covered |
| FR-005 | plan.md §Phase B items 3 and 4 | covered; PR-012 |
| FR-005a | plan.md §Phase B item 4 step 3 | covered |
| FR-006 | plan.md §Phase C items 1 and 3 | covered; PR-012, PR-016 |
| FR-007 | plan.md §Phase B item 3 (`pause`) | covered; PR-012 |
| FR-008 | plan.md §Phase B item 3 (`pause`) | covered; PR-012 |
| FR-009 | contracts/cli.md §wfctl status | covered |
| FR-010 | plan.md §Phase B item 2 | covered |
| FR-010a | plan.md §Phase B item 5, §Phase C items 2 and 3 | covered; PR-013 |
| FR-011 | plan.md §Phase B items 2, 4 and 6 | covered |
| FR-012 | plan.md §Phase A items 2 and 3 | covered |
| FR-013 | plan.md §Phase B item 4 step 1, §Phase B item 8 | covered |
| FR-014 | plan.md §Phase A item 4 | covered |
| FR-015 | plan.md §Phase A item 5, §Phase D item 3 | covered |
| FR-016 | plan.md §Phase A item 5, §Phase D item 3 | covered; PR-014 |
| FR-017 | plan.md §Phase A item 5, §Phase D item 3 | covered |
| FR-018 | plan.md §Phase D items 1 and 2, §Phase B item 7 | covered; PR-015 |
| FR-019 | plan.md §Phase D item 4 | covered |
| FR-020 | plan.md §Phase B item 4 last paragraph, §Phase B items 7 and 8 | covered; PR-012, PR-017 |
| FR-021 | plan.md §Phase B items 7 and 8 | covered; PR-015, PR-017 |
| SC-001 | plan.md §Phase B items 2, 4 and 6, §Phase C | covered |
| SC-002 | plan.md §Phase B item 2 | covered |
| SC-003 | plan.md §Phase B item 4 step 4 | covered |
| SC-004 | plan.md §Phase B item 4 step 1, §Phase B item 8 | covered |
| SC-005 | spec.md §Validation Strategy grep | covered; see Assumptions challenged |

## Assumptions challenged

- The domain page and `wfctl.json` are read from the working tree, which the
  branch under review can edit. An agent that sets the domain page's `State` to
  `proposed`, or drops its `Contexts` line, turns the per-context check off.
  SC-001 holds only while those edits are visible in the PR diff. This is the
  same class of exposure #648 accepts, so it isn't filed.
- The guard's new check reads the `governs` field, which the agent writes. A
  record that decides something about a context but leaves that context out of
  `governs` passes the guard beside a "no" for the same context. The spec's
  "Who computes what" table gives `governs` to the agent on purpose, so this
  isn't filed.
- FR-021 covers level 2 only. A per-context "no" for `brainstorm.software-design`
  followed by a level-3 record governing the same context isn't checked, which
  matches #635's guard reading only level-2 records.
- FR-020 applies whether or not `spec.md` exists. Once this repo's domain page
  carries its list, a branch already past specify whose `design.md` has no
  `Contexts` line reads "unanswered" on the Boundary line at its next
  `wfctl end`, while its pipeline position is unchanged (SC-004). That follows
  from the requirement as written.
- SC-005's check is `grep -n "Contexts" wfctl/_evidence.py wfctl/_arch.py`.
  `context_gap` lives in `_evidence.py`, and a docstring there that names the
  `Contexts` line fails the grep with no reader present.
- An epic's sub-issues share one spec folder (#635 R11), so they share one
  `Contexts` line and one set of per-context "no" answers. Carried from the
  earlier reports, and still not stated in the plan.
- #635 and #648 merge as their plans describe. PR-012, PR-015, and PR-017 come
  from reading them, and each needs re-checking once they merge. #635's plan
  changed between the second review and this one, and may change again.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- One function, `context_gap`, now feeds both the architecture check and the
  Boundary line. That removes the disagreement PR-003 described and leaves #635
  R6's reason for avoiding `_architecture_answered` intact.
- The guard decision in research R8 records the alternative it rejected,
  treating any touched record as a contradiction, and why a "no" for one
  context stays true beside a record about another.
- Each new behavior has a test that covers both directions: "answered" and
  "unanswered" for the Boundary line, refused and allowed for the guard.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, a
material planning artifact, or the #635 or #648 plans change, this report no
longer describes the current plan, and a new review is needed before it counts
as current evidence.
