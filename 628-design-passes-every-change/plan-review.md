# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | d0740bdb4f336f0e3b6a0903bf03da1e8cd3d333 | technical strategy |
| spec.md | 45857b5e8860f32b30c89f06ca35601ac9ca3bba | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | d41fe5c87e60026e8f2db51caa0d1dcf3db43e18 | design-record index |
| docs/architecture/design/628-design-passes-own-skill.md | fa8c79b243f230b7ab9bfc0f0bbd03804a6b71ce | design record |
| docs/architecture/design/628-early-answer-in-commit-trailer.md | 068548995e0554924008460ed2153ac702637f5f | design record, marked as not taken |
| docs/architecture/design/628-spec-answer-in-pr-body.md | 010bc12a6c3450f2c3df65ad6054e5ad55ce68ae | design record |
| docs/architecture/every-change-answers-spec-question.md | b6eaf518b57c98aa47b0a796786528937379d931 | level-2 record the listed records build on |
| docs/architecture/a-rule-is-expressed-as-a-check.md | 81e9a7d67301935f73a6e3b97c9b06284310879f | accepted record the plan's gates cite |
| docs/architecture/required-sections-are-wfctls.md | d9e545e997c1a990b66e1790e9698b8e4297ca48 | accepted record on required sections |
| docs/architecture/scans/628-clarify.md | 15d82f295d378b3555e00371d1f9fd0639f28a8d | clarify scan, for its deferred row |
| research.md | 231a518874733dcd61700c672a68367b59df6374 | planning evidence |
| data-model.md | 601f44991139d0bb70b6f06e0b00aa0938a7f7b1 | planning evidence |
| quickstart.md | 48b694f6a7f77ae4b863073ee2ffe8cfb86ed241 | planning evidence |
| contracts/cli.md | 91236b8f9bab39707a4ac485469a05389c7c2ef6 | planning evidence |
| contracts/skills.md | 3d5fcb7369e5986761ed822d797127e352c09f2d | planning evidence |
| checklists/requirements.md | ecaadae4e34c4b62523600d25eca79e912b3bc96 | requirements-quality checklist |
| plan-review.plan.md | ca8c5cb89695e720737e3e2bef5df2f8507696b3 | base of this re-review |

## Review scope

- Re-review: the earlier report exists, and the plan copy's identity
  (`ca8c5cb…`) equals the earlier report's `plan.md` row.
- Changed since the earlier report, per the plan diff: `plan.md §Summary`
  (four "Not for" lines keyed on boundary movement, the panel's new bullet,
  and the bare yes-or-no finding), `§Source Code` (two new skill rows), and
  `§Order of work`, steps 4 and 5. Each was reviewed together with what it
  names: `contracts/skills.md §Routing between the skills` and
  `§fanning-out-code-review Step 2`, `contracts/cli.md`, `quickstart.md §5`,
  and the `§Technical Context` and `§Constitution Check` lines that describe
  the same scope.
- Inputs that changed since the earlier report, each re-read in full with the
  whole of `plan.md` reviewed against it: `spec.md`, `research.md`,
  `data-model.md`, `quickstart.md`, `contracts/cli.md`,
  `contracts/skills.md`, `docs/architecture/every-change-answers-spec-question.md`,
  and `docs/architecture/design/628-spec-answer-in-pr-body.md`. The invoking
  command named the same set. Unchanged: `design.md`, the other two listed
  records, `a-rule-is-expressed-as-a-check.md`,
  `required-sections-are-wfctls.md`, `scans/628-clarify.md`, and
  `checklists/requirements.md`.
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification. Verification, risk,
  dependency, and scope questions from the rubric were asked under those
  three.
- Conditional lenses: security and reliability did not apply. The feature
  reads local files (`wfctl.json`, a PR body file, and the PR templates found
  by a bounded directory walk) and writes none. The new panel bullet is
  instruction text for reviewers. Nothing adds authorization, a secret, a
  destructive operation, concurrent state, or a migration.
- Design records: 3 listed in `design.md`, all read earlier; the one that
  changed, `628-spec-answer-in-pr-body.md`, was re-read in full. The level-2
  record `every-change-answers-spec-question.md` is named only in prose and was
  re-read because every listed record builds on it.
- Constitution: `.specify/memory/constitution.md` is absent. `plan.md`'s
  Constitution Check takes its gates from `AGENTS.md` and the in-force records.
- Existing code and skills inspected, to check the new wording against the
  real text: `wfctl/agents/skills/` for `design-levels`, `architecture-design`,
  `architecture-decisions`, `model-the-domain`, `worktree-handoff`,
  `fanning-out-code-review`, and `requesting-code-review`;
  `tests/test_review_fanout_skill.py`; `AGENTS.md:391`; and the diff stat of
  the `622-security-review-panel` branch against `main`.
- Tested rather than read: the contract's fifth dispatch bullet, inserted
  verbatim into a copy of `fanning-out-code-review/SKILL.md` with "these four"
  changed to "these five", run through the regexes of
  `test_the_dispatch_list_requires_the_coverage_the_clean_row_reproduces`.
  Today's file counts 4 bullets for "four"; the edited copy counts 4 for
  "five", so the test fails (PR-020).
- Reviewers: the three lenses above, run in sequence by one agent with a fresh
  context.

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 17

No BLOCKER findings identified in this review. Both earlier MAJOR findings are
now fixed. `design-levels` keys its "Not for" line on state, behavior, and
boundary movement and keeps a change `design-passes` answered yes for
(PR-013), and `architecture-decisions` joins the routing section with a
boundary-keyed line (PR-014).

Everything open is MINOR. The open items fall into three groups:

1. The routing fix left a few loose ends. The yes-path clause depends on the
   agent remembering who sent it (PR-019). `AGENTS.md` keeps quoting the
   `design-levels` wording the plan deletes (PR-026).
2. The panel bullet as written breaks an existing test (PR-020). It touches a
   skill #622 is also redesigning (PR-022). Its stated benefit rests on a
   person reading the panel's table (PR-025).
3. The no-reason rule applies to every listed section, including sections
   where a bare yes or no is a complete answer (PR-023). It also misses an
   emphasized "**No.**" (PR-024).

Nine earlier MINOR findings are still open, unchanged.

## Findings

### PR-001: The repointed "Not for" lines send a boundary-moving fix back to `design-passes`

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `contracts/skills.md §architecture-design/SKILL.md:46-50` and
    `§model-the-domain/SKILL.md:125-129`: both lines exclude by boundary
    movement or term meaning, and say a bug fix that moves one belongs there.
  - `contracts/skills.md §design-levels/SKILL.md:174-177`: a skipped method
    goes on to level 3 "here".
- Finding: Fixed in the earlier review. The two lines it named alongside
  (PR-013, PR-014) are now fixed too.
- Why it matters: Routing is the mechanism User Story 1 depends on (#290).
- Suggested response: Fixed by `contracts/skills.md §Routing between the
  skills`.
- Corroborated by: adversarial implementation, architecture and boundaries

### PR-002: SC-005 has no verification, and the new section's comment isn't specified

- Priority: MAJOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `contracts/cli.md §The template comment the messages point at`: the full
    comment text, now also saying a yes or no with no reason fails the check.
  - `quickstart.md §4`: the SC-005 run.
- Finding: Still fixed. The comment now also covers the no-reason message,
  which points at it.
- Why it matters: SC-005 is the only criterion about whether the message
  works.
- Suggested response: Fixed by the artifacts above.
- Corroborated by: requirements and traceability

### PR-003: The cross-reference test can't fail when a route line stops naming `design-passes`

- Priority: MAJOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §The cross-reference tests`, test 1, unchanged. The rewritten
    `design-levels` paragraph in `contracts/skills.md` still opens with `Not
    for:`, still names `.agents/skills/design-passes`, and is still one
    paragraph, so the marker table holds.
- Finding: Still fixed.
- Why it matters: This is the gap the design record named in its
  Consequences.
- Suggested response: Fixed by `plan.md §The cross-reference tests`.
- Corroborated by: adversarial implementation, requirements and traceability

### PR-004: Git silently drops the `Needs-spec:` trailer in two ordinary commit shapes

- Priority: MAJOR
- Category: Dependency / Feasibility
- Status: fixed
- Evidence:
  - `spec.md §FR-005`: no commit trailer and no file.
  - `every-change-answers-spec-question.md §Considered`: the trailer is listed
    as not taken.
- Finding: Still fixed.
- Why it matters: A malformed, unread trailer would have been a record that
  looked present and wasn't.
- Suggested response: Fixed by dropping the trailer.
- Corroborated by: adversarial implementation

### PR-005: The reason given for leaving test-first unchecked doesn't match `a-rule-is-expressed-as-a-check`

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: open
- Evidence:
  - `docs/architecture/a-rule-is-expressed-as-a-check.md §Decision`
    (accepted): the sort turns on whether a violation is visible "in an
    artifact the work already produces", including "the diff and the tree".
  - `plan.md §Constitution Check`: "Level 3, test-first, and the refactor
    leave nothing a check can trust beyond the agent's word", unchanged.
  - `spec.md §Assumptions`: "Each would check a file only the agent vouches
    for", unchanged.
- Finding: Unchanged since the earlier review. A fix commit with no earlier
  test commit is visible in the branch's commit order. The real obstacle to a
  check is that a copy edit or a docs change has no test to write first.
- Why it matters: The gate is marked as passed on a reason the accepted record
  doesn't recognise.
- Suggested response: Reword the gate line, for example: "a missing test
  commit is visible in history, but whether the change needed one is a
  judgment, so it stays prose".
- Corroborated by: architecture and boundaries

### PR-006: `design.md` still shows the old check-body strings and the open key name

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `design.md §What changes for the agent and the reviewer`: the `⚠` messages
    and the `✓` line.
- Finding: Still fixed for the strings it named. The new no-reason message is
  missing from `design.md`, filed as PR-021.
- Why it matters: An implementer reading `design.md` for the strings gets the
  right ones.
- Suggested response: Fixed by the updated `design.md`.
- Corroborated by: requirements and traceability

### PR-007: Headings and HTML comments are handled in an order the plan doesn't fix

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `research.md §R4`: sections are found with `_md.walk`, which skips
    headings inside fences only.
  - `research.md §R5`, rewritten: "Strip every `<!-- … -->` comment, including
    multi-line ones, then whitespace." It still describes a section's content,
    not the body.
  - `plan.md §wfctl/_sections.py`: `body_findings` "applies research R4 and
    R5", in no stated order.
- Finding: Unchanged. A heading inside a multi-line comment counts as a
  heading if sections are found first, and doesn't if comments are stripped
  first.
- Why it matters: Both orders satisfy every scenario in `spec.md`, but a test
  written for one fails against the other.
- Suggested response: State the order in R4 or R5, and add the commented-out
  section to `tests/test_sections.py`.
- Corroborated by: adversarial implementation

### PR-008: "None" is the other half of the template's escape hatch, and it passes

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `contracts/cli.md §The template comment the messages point at`: "N/A and
    None aren't answers here".
  - `research.md §R5`: "None" stays out of the check on purpose.
- Finding: Still fixed.
- Why it matters: An agent following `opening-a-change` Step 4 literally meets
  an instruction against "None" in the section it is filling.
- Suggested response: Fixed by `contracts/cli.md`.
- Corroborated by: requirements and traceability

### PR-009: The plan doesn't say who writes the trailer when the answer is yes

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `spec.md §Key Entities`: the answer is written in one place, the PR's
    "Needs a spec?" section.
- Finding: Still fixed.
- Why it matters: Key Entities promises no record the branch may not carry.
- Suggested response: Fixed by dropping the trailer.
- Corroborated by: requirements and traceability

### PR-010: The domain-model path differs between the spec and the contract, and an absent model isn't covered

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `spec.md §User Story 1`, pass 1, and `§User Story 3`, Independent Test:
    `docs/architecture/domain/`.
  - `contracts/skills.md §design-passes`, step 2: "the domain model under
    `<arch-root>/domain/`".
- Finding: Unchanged. The Independent Test checks a literal path the contract
  wouldn't contain, and neither artifact says what level 2 does in a repo with
  no domain model.
- Why it matters: Most repos have no `domain/` folder, and an agent told to
  read one that isn't there has to guess whether to skip or stop.
- Suggested response: Align the spec with `<arch-root>`, and add one line to
  the contract saying that with no domain model, level 2 reads the records and
  goes on.
- Corroborated by: requirements and traceability

### PR-011: Two descriptions of `check-body`'s scope go stale, and the plan updates neither

- Priority: MINOR
- Category: Dependency / Feasibility
- Status: open
- Evidence:
  - `wfctl/cli.py` `check_body_cmd` docstring: "Only the drawing rule".
  - `wfctl/agents/skills/opening-a-change/SKILL.md §Step 5`: `check-body`
    "knows one thing and says so".
  - `contracts/cli.md §wfctl check config`: a docstring update for `check
    config` only.
  - `628-spec-answer-in-pr-body.md §Consequences`: "This is `check-body`'s
    first rule about what a section says."
- Finding: Unchanged. `check-body` now gains two kinds of section finding, and
  its docstring still says it checks only drawings.
- Why it matters: A reader of either description is told the command does
  less than it does.
- Suggested response: Add the `check_body_cmd` docstring to step 2 of the
  order of work, and name the `opening-a-change` Step 5 wording as a follow-up
  for #622.
- Corroborated by: architecture and boundaries

### PR-012: "Required sections" now means two things with opposite owners

- Priority: MINOR
- Category: Boundary / Ownership Concern
- Status: open
- Evidence:
  - `docs/architecture/required-sections-are-wfctls.md` (accepted): the
    sections a `spec.md` and a `plan.md` must carry are wfctl's.
  - `spec.md §Key Entities`: "Required PR sections", owned by the repo.
  - `plan.md §Constitution Check`: doesn't cite `required-sections-are-wfctls`.
- Finding: Unchanged.
- Why it matters: A later reader searching for "required sections" finds a
  rule that seems to contradict this feature.
- Suggested response: Add one gate line citing `required-sections-are-wfctls`
  and saying why the PR-body case belongs to the repo. Use "change sections"
  in prose.
- Corroborated by: architecture and boundaries

### PR-013: `design-levels`' top-level "Not for" line still excludes by kind, and now points a Spec Kit-routed bug fix back to `design-passes`

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `contracts/skills.md §design-levels/SKILL.md:22-24`: the line now excludes
    "a change that adds no new state or user-visible behavior and moves no
    boundary, whatever its kind". It adds "A change that
    `.agents/skills/design-passes` sent here was already answered 'needs a
    spec', so it runs the four levels here even when it's a bug fix, and isn't
    sent back."
  - The "already settled in an existing spec" clause is now its own sentence,
    after the pointer, so it no longer sends Spec Kit work to `design-passes`.
  - `spec.md §FR-004` and `§User Story 1`, scenario 7, require both.
  - `contracts/skills.md §design-passes`, step 1: "That yes is final, and
    brainstorm doesn't send the change back here."
- Finding: Both paths the earlier review named are closed. A bug fix a handoff
  routes to Spec Kit because it adds state is no longer excluded, since the
  line keys on state. A yes from `design-passes` is kept by the new sentence.
  A residual gap in how the agent knows it was sent is filed as PR-019.
- Why it matters: This was the line an agent reads first when brainstorm
  invokes the skill.
- Suggested response: Fixed by `contracts/skills.md §design-levels/SKILL.md:22-24`.
- Corroborated by: adversarial implementation, architecture and boundaries

### PR-014: `architecture-decisions` still says it isn't for bug fixes, at the end of the route a boundary-moving fix takes

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `contracts/skills.md §architecture-decisions/SKILL.md:29-31`: "Not for: a
    change that moves no boundary, whatever its kind … A bug fix that moves a
    boundary does get a record".
  - `contracts/skills.md §Routing between the skills`, item 3, and `plan.md
    §Source Code`: `architecture-decisions/SKILL.md` is now listed.
  - `spec.md §User Story 1`, scenario 6, and `§FR-004` now name it.
- Finding: The record step at the end of the route now accepts a bug fix that
  moves a boundary.
- Why it matters: The record is the only durable output of level 2.
- Suggested response: Fixed by the contract and the plan entries above.
- Corroborated by: adversarial implementation

### PR-015: The own-skill record on the branch and its copy in `design.md` disagree, and the branch's copy still describes the old verification

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `docs/architecture/design/628-design-passes-own-skill.md:160`: "Grepping
    for 'straight to implementation'" confirms it.
  - Same record, line 147: the cross-reference test "catches a pointer to a
    missing skill, but not a place that stops pointing to it".
  - `plan.md §The cross-reference tests`: test 1 is that test.
- Finding: Unchanged; the record's identity is the same as at the earlier
  review.
- Why it matters: A reviewer comparing the PR against the record finds a
  verification step the plan doesn't run, and a stated gap that no longer
  exists.
- Suggested response: Bring the branch's record into line with the copy in
  `design.md`, and update both copies' Consequences.
- Corroborated by: requirements and traceability

### PR-016: The handoff's route item keeps two sentences that contradict the new route

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `wfctl/agents/skills/worktree-handoff/SKILL.md:66-70`:
    "`.agents/skills/design-levels` owns where the line falls" and "A change
    that draws a boundary, moves who owns a piece of truth, or adds new state
    goes through the pipeline".
  - `contracts/skills.md §The four places`, `worktree-handoff` row: replaces
    only the opening and the ending, unchanged.
- Finding: Unchanged. After the edit the item says `design-levels` owns where
  the line falls and that `design-passes` decides it.
- Why it matters: The handoff criterion decides which branches ever reach
  `design-passes`.
- Suggested response: Give the full new text of item 3's first paragraph in
  the contract, naming who owns the spec line now.
- Corroborated by: requirements and traceability, architecture and boundaries

### PR-017: The quickstart's mutation step can't make the section test fail on `architecture-design`

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `quickstart.md §3`, unchanged: "Delete `.agents/skills/design-passes` from
    the `architecture-design` 'Not for' paragraph … The section test fails".
  - `contracts/skills.md §architecture-design/SKILL.md:46-50`: the paragraph
    names the path twice. The new `design-levels` paragraph names it twice
    too.
- Finding: Unchanged. Deleting one occurrence leaves the other, so test 1
  still passes.
- Why it matters: Done literally, the step shows the test can't fail, and the
  implementer may "fix" a correct test.
- Suggested response: Say to delete every occurrence in that paragraph, or run
  the mutation on the `AGENTS.md` paragraph, which names the skill once.
- Corroborated by: adversarial implementation

### PR-018: `model-the-domain`'s new line sends a skipped change to "level 3 of the skill that sent it", and one sender has no level 3

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `contracts/skills.md §Routing between the skills`: "Each method is called
    from two places", unchanged.
  - `wfctl/agents/skills/architecture-design/SKILL.md:52-58`: a capability that
    earns domain modeling goes to `model-the-domain` first.
  - `contracts/skills.md §model-the-domain/SKILL.md:125-129`: a skipped change
    "goes on to level 3 of the skill that sent it here".
  - The same gap now shows for `architecture-decisions`. Routing item 3 and the
    new line say `architecture-design` sends it a boundary, but
    `design-levels/SKILL.md:159-161` has `model-the-domain` hand "any other
    boundary straight to `architecture-decisions`".
- Finding: The contract's caller lists are incomplete. `architecture-design`
  also sends to `model-the-domain`, and `model-the-domain` also sends to
  `architecture-decisions`.
- Why it matters: The cost is small, since an agent can infer the way back,
  but the caller claims are the premise the new lines rest on.
- Suggested response: Name the extra callers in the routing section, and say
  that a change from `architecture-design` goes back there.
- Corroborated by: architecture and boundaries

### PR-019: The yes-path sentence in `design-levels` depends on the agent remembering who sent it

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `contracts/skills.md §design-levels/SKILL.md:22-24`: "A change that
    `.agents/skills/design-passes` sent here was already answered 'needs a
    spec', so it runs the four levels here".
  - `spec.md §FR-005` and `contracts/skills.md §design-passes`, step 1: the
    answer is written nowhere before the PR ("Don't write it down yet").
  - `spec.md §Edge Cases`: "A session restarts after the spec question but
    before the PR. The answer may be lost."
  - `AGENTS.md §Session state`: a `claude`-layer pane can be restarted mid
    session when the context fills.
- Finding: The sentence keys on who sent the change. Inside brainstorm, the
  only evidence of that is the conversation. After a restart, a bug fix that
  adds no state, behavior, or boundary reads the line's first half and is sent
  back to `design-passes`, which asks the spec question again. The earlier
  review suggested keying on something the agent can see, such as being run
  by brainstorm; `wfctl status` shows the pipeline step.
- Why it matters: The bounce is one hop, not a loop, because `design-passes`
  may answer differently the second time. But it reopens a decision step 1
  calls final, on a narrow path.
- Suggested response: Key the sentence on the change being in the Spec Kit
  pipeline: "A change brainstorm is running for has already been routed to
  the pipeline, so it runs the four levels here, whatever its kind."
- Corroborated by: adversarial implementation

### PR-020: The contract's fifth dispatch bullet, as written, fails an existing test the plan never names

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `contracts/skills.md §fanning-out-code-review Step 2`: the bullet opens
    `- **Report any design decision the diff makes that nothing on the change`
    and closes its bold on the next line, `covers:**`.
  - `tests/test_review_fanout_skill.py`,
    `test_the_dispatch_list_requires_the_coverage_the_clean_row_reproduces`:
    counts bullets with `^- \*\*(.+?)\*\*` under `re.MULTILINE` only, so a
    bold span that wraps a line isn't counted, and asserts the count equals
    the lead-in's word.
  - Tested: the bullet inserted verbatim with "these five" counts 4 bullets
    against "five", and the test fails.
  - `plan.md §Technical Context`, Testing: names four test files and not
    `test_review_fanout_skill.py`. Scale/Scope still says "edits to four
    skills", and the plan now edits six.
- Finding: Following the contract's wording literally turns the suite red. The
  fix is one rewrap, keeping the bold on one line, but the plan doesn't name
  the test that holds the dispatch list.
- Why it matters: The suite catches it, so nothing ships wrong. The
  implementer is told to use the contract's wording and then finds that it
  can't be used as written.
- Suggested response: Rewrap the bullet in the contract so its bold phrase
  sits on one line. Name `tests/test_review_fanout_skill.py` in `plan.md
  §Technical Context`, and correct the skill count.
- Corroborated by: adversarial implementation

### PR-021: `design.md` and research R1 don't carry the no-reason message or the panel bullet

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `research.md §R1`, Decision: lists three messages. The fourth, "answers
    yes or no with no reason", is in `contracts/cli.md` and `data-model.md`
    only.
  - `design.md` (unchanged): its level-1 walkthrough has no bare-answer state.
    Its copy of `every-change-answers-spec-question` says `check-body` fails a
    body "empty or N/A". Its MVP scope names only the `design-levels` and
    `architecture-design` lines, and nothing about the panel.
  - `every-change-answers-spec-question.md §Decision` and `§Consequences`, as
    committed now: a bare yes or no fails, and the panel reports an uncovered
    design decision.
  - `design.md`: "The file in `docs/architecture/` is the one that counts if
    the two ever differ."
- Finding: The record that counts is current, so nothing binding disagrees.
  The index and R1 describe the earlier design.
- Why it matters: An implementer reading `design.md` for the rendered strings
  or the scope misses one message and two edited skills.
- Suggested response: Add the fourth message to R1, and bring `design.md`'s
  walkthrough, record copy, and MVP scope into line.
- Corroborated by: requirements and traceability

### PR-022: The panel edit lands in a skill #622 is redesigning, and the plan's #622 constraint covers only `opening-a-change`

- Priority: MINOR
- Category: Dependency / Feasibility
- Status: open
- Evidence:
  - `design.md §Where this meets #622`: "#622 is redesigning
    `opening-a-change` and the review panel."
  - `plan.md §Technical Context`, Constraints: "No edit to
    `opening-a-change`, which #622 is redesigning." Nothing about
    `fanning-out-code-review`.
  - `contracts/skills.md §fanning-out-code-review Step 2`: "an in-place edit
    stays", argued against upstream vendoring only.
  - Branch `622-security-review-panel` adds
    `622-blocked-reviewer-relays-report.md`, which cites
    `fanning-out-code-review` Step 3, and `622-review-groups-list.md`.
- Finding: The plan protects the file #622 is redesigning and edits the other
  one `design.md` says #622 redesigns, without saying how the two meet.
- Why it matters: A conflict would surface at merge rather than silently. If
  #622 restructures how reviewers are dispatched, the fifth bullet may land
  in a list that no longer exists.
- Suggested response: Add a line to `design.md §Where this meets #622` or to
  the contract saying the Step 2 bullet is independent of #622's changes, or
  naming the follow-up if it isn't.
- Corroborated by: architecture and boundaries

### PR-023: The no-reason rule applies to every listed section, including one where a bare yes or no is the whole answer

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `research.md §R5`: "The rule applies to every listed section, not only
    'Needs a spec?', since a repo lists a section for a reader and a one-word
    answer gives the reader nothing."
  - `research.md §R1` and `628-spec-answer-in-pr-body.md §Decision`: wfctl
    hardcodes no section names, and R1 keeps section-specific instructions out
    of the messages.
  - `research.md §R1`, Alternatives: a per-entry `hint` object was not chosen,
    so `change_sections` has no per-section setting.
- Finding: Requiring a reason is a property of the "Needs a spec?" question,
  and R5 applies it to every section a repo lists. For a section such as
  "Breaking changes?", "No." is a complete answer, and every PR that gives it
  fails. A repo can't list such a section without opting into the rule.
- Why it matters: Today only this repo lists sections, so nothing breaks. The
  stated reason, that a one-word answer gives the reader nothing, doesn't hold
  for every yes-or-no question, and the record says it's built for a repo that
  lists a second section.
- Suggested response: Either state in R5 that a repo should list only sections
  whose yes or no needs a reason, or record the limitation in the PR-body
  record's Consequences.
- Corroborated by: architecture and boundaries

### PR-024: An emphasized bare answer such as "**No.**" passes the no-reason check

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `research.md §R5` and `data-model.md §Section finding`: the remainder must
    match `(yes|no)[.!]?`, after comments and whitespace are stripped.
    Nothing strips Markdown emphasis.
  - `spec.md §Edge Cases`: "no", "YES", and "No!" are bare answers.
- Finding: "**No.**", "*No*", and "_Yes._" don't match the pattern, so they
  pass as answered. Bolding a one-word answer is a common way to fill a
  template section.
- Why it matters: The rule exists to catch a bare answer, and the most common
  way of formatting one gets through. The same applies to the N/A pattern and
  "**N/A**".
- Suggested response: Strip surrounding `*` and `_` before matching, and add
  an emphasized case to `tests/test_sections.py`. Or name the gap in R5 as
  accepted.
- Corroborated by: adversarial implementation

### PR-025: The panel's benefit relies on a person reading the table, which an unattended run doesn't have

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `spec.md §User Story 2`: "The person sees the finding in the panel's table,
    and an agent other than the author has judged whether the 'No' holds."
  - `every-change-answers-spec-question.md §Consequences`: "So an agent other
    than the author judges whether a 'No' holds, and the finding reaches the
    person in the panel's table before the PR opens."
  - `contracts/skills.md §fanning-out-code-review Step 2`: the panel runs
    before the description is written, so a reviewer can't compare the diff
    with the PR's answer.
  - `fanning-out-code-review/SKILL.md` Steps 5 and 6: the coordinator, who is
    the author, verifies and disposes of each finding. The table goes to the
    conversation, and never into the change description.
- Finding: No reviewer sees the "No". The reviewer reports a design decision,
  and the author decides what that finding means for the answer. In an
  unattended run, the case #290 is about, nobody reads the table. The only
  reader of the finding is the agent that skipped the question.
- Why it matters: The spec and the record claim more than the mechanism gives,
  and a later reader may count on it as a check.
- Suggested response: Reword the claim in both places: the reviewer reports
  the decision, and a person attending the run sees it. Name the unattended
  case as uncovered.
- Corroborated by: adversarial implementation, requirements and traceability

### PR-026: The `AGENTS.md` row keeps quoting the `design-levels` exclusion the plan rewrites

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `AGENTS.md:391-393`: "`design-levels` excludes 'bug fixes, copy edits and
    other trivial changes that introduce no new state'".
  - `contracts/skills.md §The four places`, `AGENTS.md:391` row: "the same,
    plus 'Every change runs the design passes …'".
  - `contracts/skills.md §design-levels/SKILL.md:22-24`: that wording is
    replaced by an exclusion keyed on state, behavior, and boundary movement.
- Finding: After the edit, `AGENTS.md` quotes a sentence `design-levels` no
  longer has. The quote is the kind-keyed exclusion FR-004 removes.
  `speckit-brainstorm` reads `AGENTS.md` before it invokes `design-levels`.
- Why it matters: An agent in brainstorm on a yes-path bug fix reads that
  `design-levels` excludes bug fixes, and then reads the opposite in the skill.
  The skill's own line governs, so the cost is a contradiction, not a wrong
  route.
- Suggested response: Give the new `AGENTS.md` paragraph in full in the
  contract, quoting the new `design-levels` wording or none.
- Corroborated by: architecture and boundaries, adversarial implementation

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Source Code, contracts/skills.md §design-passes | covered |
| FR-002 | contracts/skills.md §design-passes, steps 2 - 5 | covered |
| FR-003 | contracts/skills.md §design-passes, step 1 | covered; PR-019 |
| FR-004 | contracts/skills.md §The four places, §Routing between the skills | covered; PR-016, PR-018, PR-019, PR-026 |
| FR-005 | contracts/skills.md §design-passes, steps 1 and 6 | covered |
| FR-006 | plan.md §wfctl/_sections.py; data-model.md §change_sections | covered |
| FR-007 | research.md §R1, §R4, §R5; data-model.md; contracts/cli.md | covered; PR-007, PR-021, PR-023, PR-024 |
| FR-008 | contracts/cli.md, first row | covered |
| FR-009 | research.md §R6, §R7; contracts/cli.md §check config | covered |
| FR-010 | contracts/cli.md §The template comment; plan.md §Order of work, step 3 | covered |
| FR-011 | contracts/skills.md §design-levels level 2 | covered; PR-010 |
| FR-012 | contracts/skills.md §design-passes, step 2 | covered |
| FR-013 | plan.md §Technical Context, Constraints | covered; PR-011, PR-022 |
| FR-014 | contracts/skills.md §fanning-out-code-review Step 2; plan.md §Order of work, step 4 | covered; PR-020, PR-022, PR-025 |
| SC-001 | quickstart.md §2 | covered |
| SC-002 | quickstart.md §1; tests/test_shape.py | covered; PR-024 |
| SC-003 | contracts/cli.md, first row; quickstart.md §1 | covered |
| SC-004 | plan.md §The cross-reference tests; quickstart.md §3 | covered; PR-017 |
| SC-005 | contracts/cli.md §The template comment; quickstart.md §4 | covered |
| US2 scenario 8 | quickstart.md §5 | covered by an agent run |

## Assumptions challenged

- A change `design-passes` sent to brainstorm can be recognised there
  (contracts/skills.md §design-levels). Only the conversation says so, and a
  restart loses it (PR-019).
- A one-word yes or no gives the reader nothing in any section a repo lists
  (research R5). Some yes-or-no questions are fully answered by one word
  (PR-023).
- The panel lets an agent other than the author judge a "No" (spec.md §User
  Story 2, the level-2 record). No reviewer sees the answer, and the author
  disposes of the finding (PR-025).
- `AGENTS.md`'s pipeline-skip paragraph can stay "the same" (contracts/skills.md
  §The four places). It quotes the line the plan rewrites (PR-026).
- The contract's wording can be used verbatim (plan.md §Order of work, step
  4). The fifth bullet can't, as written (PR-020).

## Reviewer disagreement

- None identified. PR-025 was weighed between MAJOR and MINOR. It sits at
  MINOR because the spec and the record both present the panel as reducing
  the risk, not removing it, and no implementation choice depends on the
  claim. PR-019 sits at MINOR because the failure is one extra hop through
  `design-passes`, not a loop.

## Strengths worth preserving

- `contracts/skills.md §Routing between the skills` now covers all four skills
  a bug fix can reach, and explains why no counter stops the bounce, so the
  wording carries the guarantee.
- Moving "already settled in an existing spec" out of the pointer's sentence
  in `design-levels` closes the path that would have sent Spec Kit work with a
  spec to `design-passes`.
- The no-reason check is specified the same way in `spec.md`, `research.md
  §R5`, `data-model.md`, `contracts/cli.md`, `quickstart.md §1`, and the
  PR-body record, with one message string throughout.
- `quickstart.md §5` checks the panel bullet in both directions, with a
  finding when nothing covers the setting and none once a record does.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the
current plan, and a new review is needed before it counts as current evidence.
