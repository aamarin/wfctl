# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 2c48fb67420e4ceba6133eab0ec77a3a6f6c73f5 | technical strategy |
| spec.md | 7ce068f9e92660de37275028afce17360c86a37e | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | 8f1a1ef55b9d0fd9742190c2401d3adcd4b2b7be | design-record index |
| docs/architecture/design/649-contexts-module.md | fc4648ceb1732ebdf47f636f3d66fb1927b1739c | design record |
| docs/architecture/domain-page-names-contexts.md | 5aa73e748adccc3798b780c21f1ffe0371951f77 | accepted level-2 record the plan builds on |
| docs/architecture/promised-evidence-blocks-on-silence.md | 706e289280ece13c1ae6d1ede7f9fd57074b01d8 | record #648 amends, read for PR-012 |
| research.md | fa5daf450c9583405f80e13a2cc486ab65d8883c | planning evidence |
| data-model.md | 348ab147f89f686d144ef3f7a7a71fb6d37f465a | planning evidence |
| contracts/cli.md | 66e0635fe5399818d52791c219a7a3914f9f99c0 | planning evidence |
| quickstart.md | b5d38b715c8faf29213d352c88eacaf4e078725a | planning evidence |
| ../635-arch-folder-per-branch-notes/plan.md | 8ae93cbeb83f687d21b77b9d6536af1abf944a78 | dependency (#635, merged) |
| ../635-arch-folder-per-branch-notes/data-model.md | 915a7fa4060dc13fb09828af875325db6a9a53f2 | dependency (#635, merged) |
| ../635-arch-folder-per-branch-notes/research.md | 06fc373bdadcd690fd7b866267dca5f5d0cb2702 | dependency (#635, merged) |
| ../635-arch-folder-per-branch-notes/contracts/cli.md | dd2c1c43ae17379248f7572c0257f79cce3e4475 | dependency (#635, merged), read for PR-015 and PR-017 |
| ../648-design-gate/plan.md | 917273ccd1741eff61dfe1348db5ca30abd3a6b7 | dependency (#648, merged) |
| ../648-design-gate/research.md | e33d7568951e6ca8268bba5d3d0ed83d32b7a8aa | dependency (#648, merged) |
| plan-review.plan.md | 052118b427ac11d993cf684778d9dfb5b43cc708 | base of this re-review |

## Review scope

- Re-review: the plan copy's identity equals the earlier report's `plan.md`
  row, so the review diffed the copy against `plan.md`. Tasks already exist, so
  this is a late review; the cross-artifact job stays with `analyze`.
- Changed in `plan.md` since the earlier report: `§Phase B item 4` (the
  `_architecture_answered` order, with the `design_record_checks` "off" exit now
  ahead of the boundary exception) and `§Phase B item 8` (the guard test now
  goes in `test_record_gate.py`). Both were reviewed together with the parts
  that refer to them: Phase B items 3, 5 and 7, Phase C item 1, and the
  requirement trace.
- Inputs that changed by identity and were re-read in full, with the whole of
  `plan.md` reviewed against each:
  - `spec.md`: FR-002 gained an exception (a per-context "no" written while a
    list existed is still read by the guard and `check-body`), FR-018 gained a
    `check-body` skip rule for an inherited per-context "no", and one edge case
    was added (#653, decided 2026-10-27).
  - `docs/architecture/design/649-contexts-module.md`: amended by #652. It now
    lists `malformed`, `split_names`, `context_gap`, and the `Level` type.
  - `docs/architecture/promised-evidence-blocks-on-silence.md`: reworded, with
    the Decision unchanged on the point PR-012 uses.
  - #635's `data-model.md` and `research.md`: they now carry the guard's record
    checks and R12 to R15.
- Unchanged since the earlier report, by identity: `design.md`,
  `domain-page-names-contexts.md`, `research.md`, `data-model.md`,
  `contracts/cli.md`, `quickstart.md`, #635's `plan.md` and `contracts/cli.md`,
  and #648's `plan.md` and `research.md`.
- Existing code checked against the plan's claims, now that #635 and #648 are
  merged: `wfctl/_evidence.py` `_architecture_answered` (order is `spec.md`,
  `_design_exceptions.boundary`, `design_record_checks`, then git with
  `blocks(verdict, "repo-declared")`), `brainstorm_architecture` (reads
  `design_record_checks` first and returns `skipped` before it calls
  `_architecture_answered`), `wfctl/_record_gate.py` (`touched`, `refusal`), and
  `wfctl/_design_exceptions.py` (`path(spec_dir, name)`, `boundary`, `passes`,
  no `context` argument yet). `tests/test_record_gate.py`,
  `tests/test_review_gate.py` and `tests/test_worktree_guard.py` exist.
- Lenses: requirements and traceability, architecture and boundaries, and
  adversarial implementation and verification. Dependency and scope are folded
  into architecture, and verification and risk into adversarial.
- Conditional lenses: security and reliability applied, narrowly, for the same
  reasons as before: the feature is an integrity control the agent under review
  must not bypass (SC-001), a user-written name becomes a folder, and the guard
  is extended.
- Design records: 1 listed in design.md,
  `docs/architecture/design/649-contexts-module.md`. The level-2 record the
  section names in prose, `domain-page-names-contexts.md`, was read as well.
- `spec.md` holds no `[NEEDS CLARIFICATION` marker.
- Reviewers: the lenses above, run in sequence by one agent with a fresh
  context.

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 6

No BLOCKER findings identified in this review. The two plan edits hold against
the merged code. The reordered `_architecture_answered` list matches what the
function does today (`spec.md`, boundary exception, "off", git), and moving
"off" ahead of the boundary exception changes no result, since both return
answered. The guard test now names the file that tests the record check, which
removes part of PR-015. No earlier finding regressed. PR-016 is fixed: the
amended level-3 record says `context_gap` gathers records for both levels,
picks the folder from a mapping in `_evidence`, and is called by the
architecture pass, the software design pass and the Boundary line. PR-012,
PR-013, PR-014, PR-015 and PR-017 still stand. One new MINOR finding, PR-018,
covers the plan leaving out `_contexts.malformed`, which the amended record now
lists. A second, PR-019, covers two spec changes (FR-002's exception and
FR-018's skip rule) that the plan doesn't carry. That makes six open MINOR
findings and one earlier finding fixed since the earlier report.

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
  - `plan.md §Phase B item 4`, last paragraph, and `§Phase B item 7`, second
    bullet: `_observe` and the architecture reader both call
    `_evidence.context_gap`, and `_observe` skips the `spec.md` exit.
  - `docs/architecture/design/649-contexts-module.md §Decision` says the same.
  - `plan.md §Phase B item 8`: `test_end_reports_observations.py` tests both
    readings.
- Finding: Both parts of the earlier finding are addressed. The Boundary line
  and `wfctl status` read from one function.
- Why it matters: The Boundary line is the first thing a restarted session
  reads.
- Suggested response: Fixed by `plan.md §Phase B items 4, 7 and 8`. The guard
  extension's remaining details are in PR-015.
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
    fallback into `context_gap`, unchanged. The edit this round reordered the
    list and left that paragraph as it was.
  - `plan.md §Phase B item 7`, second bullet: `_observe` maps "a gap git
    couldn't check" to "unknown", so the Boundary line inherits the fallback.
  - `wfctl/_evidence.py` `_architecture_answered`, merged: it builds a
    `Verdict` from `touched_on_this_branch` and hands it to
    `blocks(verdict, "repo-declared")`, and only then picks
    `GIT_UNANSWERED_REASON`. Its comment names
    `promised-evidence-blocks-on-silence` as the reason.
  - `docs/architecture/promised-evidence-blocks-on-silence.md §Decision`
    (proposed): a gate "does not decide for itself what its own silence means".
  - `wfctl/_paths.py` `touched_on_this_branch`: returns `True` from
    uncommitted changes before it looks for a trunk, while
    `records_on_this_branch` returns only uncommitted records when there's no
    trunk.
  - `data-model.md §Check outcome`: the git-unanswered row still sits above the
    missing-line and unknown-name rows.
- Finding: The three parts of the earlier finding still hold, and the merged
  code now shows the shape the plan should follow.
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
  `unanswered` result, after the FR-007 and FR-008 checks. `_observe` can then
  read the same verdict without calling `blocks`, since it reports and doesn't
  gate.
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
  - `plan.md §Project Structure` lists `_observe` in the `cli.py` comment, a
    guard line, and the two new test files from the last round.
  - Still missing: `wfctl/_pipeline.py` (`§Phase B item 6`),
    `_design_exceptions.reasons` in the `_design_exceptions.py` comment
    (`§Phase B item 7`), `test_pipeline_state_names.py` (`§Phase B item 8`),
    and `docs/architecture/design/design-exceptions-module.md`
    (`§Phase C item 5`).
  - The `_evidence.py` comment doesn't name `context_gap` (`§Phase B item 4`).
  - New this round: the guard line reads "(worktree guard, from #635)" and
    names no module, and the tests list still carries `test_worktree_guard.py`
    for the per-context contradiction. `§Phase B item 8` now puts that test in
    `test_record_gate.py`, and `wfctl/_record_gate.py` exists with `refusal` as
    the record check.
  - `plan.md §Phase A item 5` names `architecture-design` and `design-passes`,
    and Project Structure lists neither, nor `model-the-domain/SKILL.md`'s
    mentions of `arch none`, nor `wfctl/agents/commands/speckit.brainstorm.md`.
  - `wfctl/agents/skills/design-passes/SKILL.md` line 56 tells the agent not to
    run `wfctl arch none` on that route, while Phase A item 5 lists the skill
    among those that teach `arch none --reason`.
- Finding: The phases and Project Structure still disagree, and the edit this
  round made one more row stale (the guard test file).
- Why it matters: Project Structure is what a task list is most often built
  from. The `_pipeline` edit, `reasons`, `context_gap`, the record edit, and
  the claim-drop test have no grep fallback like the skill texts do.
- Suggested response: Bring Project Structure in line with the phases: name
  `wfctl/_record_gate.py` and `tests/test_record_gate.py` for the guard, and
  drop `design-passes` from the "teaches" list or say what changes there.
- Corroborated by: deterministic checks, requirements and traceability

### PR-015: The guard's per-context check leaves details the merged guard now fixes

- Priority: MINOR
- Category: Dependency / Feasibility
- Status: open
- Evidence:
  - Fixed this round: `plan.md §Phase B item 8` names `test_record_gate.py`,
    which tests `_record_gate.refusal`.
  - `plan.md §Phase B item 1` gives a `context` argument to `write`,
    `boundary`, and `passes`, but not to `path`.
    `wfctl/_record_gate.py` `refusal` prints the `rm` line through
    `_design_exceptions.path(spec_dir, BOUNDARY)`, and #635's `data-model.md`
    says `path` is the one place that builds an exception's path.
  - `wfctl/_record_gate.py` `refusal`: the order is the contradiction check,
    then the unaccepted-record check (R14), and it returns early when the
    branch touches no record. `plan.md §Phase B item 7`, third bullet, doesn't
    say where the per-context check sits in that order.
  - `plan.md §Phase B item 8`: the guard test expects `gh pr create` to be
    "allowed when the record governs only `install-and-drift`". Under R14, a
    touched record that isn't accepted refuses the PR, so the test passes only
    if its fixture record is accepted. The plan doesn't say so.
  - `plan.md §Phase B item 7`, third bullet: the check runs "with a name list".
    `spec.md §FR-002` now says the guard still reads a per-context "no" when no
    list exists, so the guard has to enumerate the subfolders of `exceptions/`
    rather than ask `_contexts.names`. The plan doesn't say which.
  - `wfctl/_record_gate.py` module docstring: the guard imports neither `typer`,
    `rich` nor `_evidence`, since it runs before every Bash call. The plan
    doesn't say whether the per-context check reads `governs` through
    `_arch.parse_record` on `git show` text, which is the only import it needs.
- Finding: The guard decision is sound, and the merged module makes the module
  and test file certain. The path helper, the refusal order, the fixture
  status, and how the subfolders are enumerated are still left to the
  implementer.
- Why it matters: Each item has one obvious answer once `_record_gate.py` is
  open, so no behavior is guessed. The fixture and the enumeration are the two
  a task list copies as written, and the first would fail on first run.
- Suggested response: Give `path` the same `context` argument, place the
  per-context check beside the contradiction check, state that the "allowed"
  fixture record is accepted, and say the guard enumerates `exceptions/*/`
  without consulting the name list.
- Corroborated by: architecture and boundaries, adversarial implementation

### PR-016: `context_gap` takes a level, and the plan doesn't say how the level picks the records

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `docs/architecture/design/649-contexts-module.md §Decision`: `context_gap`
    "gathers this branch's records for either level", reads the arch root
    excluding `design/` for level 2 and `design/` for level 3, and "a mapping in
    `_evidence`, keyed by `level`, picks the folder". The architecture pass, the
    software design pass and the Boundary line all call it.
  - `plan.md §Phase C item 1`: "the same order as Phase B step 4", with the
    level-3 folder named, and `plan.md §Phase B item 4` places record gathering
    inside `context_gap`.
- Finding: The amended record now answers where the per-level folder lives and
  that Phase C goes through `context_gap`, so the gather-and-fallback rule has
  one home. The plan's wording is looser than the record's, but the two don't
  conflict.
- Why it matters: The third option the earlier finding feared, Phase C
  gathering its own records, is now ruled out by the binding record.
- Suggested response: Fixed by the amended record. A task list should cite the
  record's `§Decision` for this.
- Corroborated by: adversarial implementation, architecture and boundaries

### PR-017: The contract and data model don't carry the two new readers

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `plan.md §Phase B item 7`: the Boundary line gets new readings with a name
    list, and the guard gets a new refusal that "names the record and the
    context, and prints the command that deletes that context's exception".
  - `contracts/cli.md` (unchanged): has no `wfctl end` section and no guard
    section. #635's `contracts/cli.md §wfctl end` and `§Worktree guard` give
    both as a table and a literal refusal, so #649's contract is the place a
    user-visible change to them is written.
  - `data-model.md §Per-context "no"` (unchanged): "Read by
    `_design_exceptions.boundary(spec_dir, context=…)` and `passes(…)`" names
    neither the guard nor `_observe`, which now both read per-context answers.
  - `spec.md §FR-021`: the refusal "MUST name the record and the context, and
    print the command that deletes that context's 'no'".
- Finding: Both artifacts were left as the earlier review read them, so the
  refusal text and the Boundary line's per-context rows exist only in the
  plan's prose.
- Why it matters: The plan's guard test asserts only refused or allowed, so
  without a contract the refusal's wording is decided during implementation.
- Suggested response: Add a `wfctl end` table for the name-list case and the
  per-context guard refusal to `contracts/cli.md`, in #635's form, and list the
  guard and `_observe` as readers in `data-model.md`.
- Corroborated by: deterministic checks

### PR-018: The plan leaves out `_contexts.malformed`, which the amended record lists

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `docs/architecture/design/649-contexts-module.md §Decision`, item 2:
    `malformed(arch)` returns each entry on a domain page that isn't a valid
    name, "so `doctor` can report it". The record counts six functions in
    `_contexts`.
  - `plan.md §Phase A item 1`: `_contexts` gets `names` and `listed` only.
    `§Phase A item 6`: `names` keeps only kebab-case entries and
    `_check_arch_records` "reports each dropped entry". `§Project Structure`'s
    `_contexts.py` comment lists no `malformed`.
  - `spec.md §Edge Cases`: a malformed domain-page entry is "left off the list
    and reported by `wfctl doctor`".
- Finding: Something has to hand `_check_arch_records` the dropped entries.
  The record names it `malformed` in `_contexts`. The plan names no function
  and no test for it, and Phase A item 7's `names` test list covers only the
  dropped entry, not the reporting.
- Why it matters: An implementer can add the function, duplicate the shape
  check in `cli.py`, or have `names` return the dropped entries. The second
  puts the name rule in two places, which `a-rule-is-expressed-as-a-check`
  warns about.
- Suggested response: Add `malformed(arch)` to Phase A item 1, to the
  Project Structure comment, and to the `test_contexts.py` list.
- Corroborated by: deterministic checks, architecture and boundaries

### PR-019: The spec's FR-002 exception and FR-018 skip rule have no plan text or test

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `spec.md §FR-002`: with no name list, the worktree guard and `check-body`
    "MUST still read" a per-context "no" written while a list existed.
  - `spec.md §FR-018`: on a sub-issue branch that inherits its parent's spec
    folder, `check-body` "MUST skip an inherited per-context 'no' only when a
    level-2 record the branch adds or edits governs that same context".
  - `plan.md §Phase B item 7`, first bullet: `reasons` returns every label and
    reason across the branch-wide and per-context files, and says nothing about
    the skip. The guard bullet says "with a name list".
  - #635's `research.md §R12`: the skip applies to the branch-wide boundary
    exception, "when the branch touches a level-2 record", with no per-context
    form.
  - `plan.md §Phase B item 8`: no test sets up a per-context "no" with the list
    since removed, and none sets up an inherited per-context "no".
- Finding: Both spec changes are new since the earlier report. The plan's
  `check-body` text copies #635's rule, which skips on any touched record. FR-018
  says skip only for the same context, and the plan's tests would pass either
  way.
- Why it matters: The wrong reading lets a sub-issue's PR body omit an
  inherited "no" for a context its record doesn't cover, which is the case
  FR-018 exists to keep. The FR-002 case is a repo that dropped its list after a
  branch wrote a "no", so it is narrow.
- Suggested response: In Phase B item 7, say `check-body`'s skip compares the
  record's `governs` with the exception's context, and that the guard reads
  per-context "no" answers whether or not a list exists. Add two tests: an
  inherited per-context "no" skipped for a governed context and reported for
  another, and the guard refusing after the list is removed.
- Corroborated by: requirements and traceability, adversarial implementation

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Phase A items 1 and 6 | covered; PR-018 |
| FR-002 | plan.md §Phase B items 4 and 7 | covered for the checks; PR-019 for the guard and `check-body` exception |
| FR-003 | plan.md §Phase A item 1 (`listed`) | covered |
| FR-004 | plan.md §Phase A item 2, §Phase C item 1 | covered |
| FR-005 | plan.md §Phase B items 3 and 4 | covered; PR-012 |
| FR-005a | plan.md §Phase B item 4 step 3 | covered |
| FR-006 | plan.md §Phase C items 1 and 3 | covered; PR-012 |
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
| FR-018 | plan.md §Phase D items 1 and 2, §Phase B item 7 | covered for the PR body; PR-019 for the skip rule |
| FR-019 | plan.md §Phase D item 4 | covered |
| FR-020 | plan.md §Phase B item 4 last paragraph, §Phase B items 7 and 8 | covered; PR-012, PR-017 |
| FR-021 | plan.md §Phase B items 7 and 8 | covered; PR-015, PR-017 |
| SC-001 | plan.md §Phase B items 2, 4 and 6, §Phase C | covered |
| SC-002 | plan.md §Phase B item 2 | covered |
| SC-003 | plan.md §Phase B item 4 step 4 | covered |
| SC-004 | plan.md §Phase B item 4 step 1, §Phase B item 8 | covered |
| SC-005 | spec.md §Validation Strategy grep | covered; see Assumptions challenged |

## Assumptions challenged

- The reorder in `plan.md §Phase B item 4` is sound. `brainstorm_architecture`
  already returns `skipped` on "off" before it calls `_architecture_answered`,
  so the new step 2 only matters to `brainstorm`'s own pending-or-started read
  and to `design_block`, and for both the old and new order return answered.
  The plan's claim that the move changes no result holds against the merged
  code.
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
  matches the merged guard reading only level-2 records.
- FR-020 applies whether or not `spec.md` exists. Once this repo's domain page
  carries its list, a branch already past specify whose `design.md` has no
  `Contexts` line reads "unanswered" on the Boundary line at its next
  `wfctl end`, while its pipeline position is unchanged (SC-004). That follows
  from the requirement as written.
- SC-005's check is `grep -n "Contexts" wfctl/_evidence.py wfctl/_arch.py`.
  `context_gap` lives in `_evidence.py`, and a docstring there that names the
  `Contexts` line fails the grep with no reader present. The amended record's
  own check greps `"Contexts:"` with the colon, so the two greps differ.
- An epic's sub-issues share one spec folder (#635 R11), so they share one
  `Contexts` line and one set of per-context "no" answers. Carried from the
  earlier reports, and still not stated in the plan. FR-018's new skip rule
  depends on it.
- #635 and #648 are merged now, and the plan's "after #635 merges" and "after
  #648 merges" headings are met. The plan still describes them as pending in
  its Summary, which is wording and not a finding.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- One function, `context_gap`, feeds the architecture check, the software
  design check and the Boundary line, and the amended record now says so for
  all three.
- The plan states the `_architecture_answered` order twice, as it stands and as
  it will be, so an implementer can check the move against the code.
- Each new behavior has a test that covers both directions: "answered" and
  "unanswered" for the Boundary line, refused and allowed for the guard.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, a
material planning artifact, or the #635 or #648 plans change, this report no
longer describes the current plan, and a new review is needed before it counts
as current evidence.
