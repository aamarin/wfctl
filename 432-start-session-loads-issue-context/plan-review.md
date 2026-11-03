# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 3760ae0b55bb3571da07116562d8fe0bd811718d | technical strategy |
| spec.md | 1127054e19c589e19e11118729f1d1d5c7373b0d | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | 0a40c207c4e79d1e975de2a1d8fb0add27ac48d7 | design-record index |
| docs/architecture/session-start-reads-branch-progress.md | 2daed3fb97456b5e17d2c0d8bddada80bd0de4a2 | design record (level 2, accepted) |
| docs/architecture/session-report-built-in-code.md | bc2062733f0519deb6290bba018e4e863804cfb6 | design record (level 2, superseded) |
| docs/architecture/tracker-reads-report-failure.md | 4ae2a0acfeea8c78c04b08b1bf1acfa83218c44e | design record (level 2, accepted) |
| docs/architecture/backend-tracker-reads-parent-and-change.md | 25d89fafff72aed51b6bb74c2d81821c60c9b47c | design record (level 2, superseded) |
| docs/architecture/design/432-session-report-is-a-status-flag.md | 1827b3ed682cee92720784c21a4cf09677de6553 | design record (level 3) |
| docs/architecture/design/432-doctor-session-scopes-claim-notices.md | 8fd2c2a28d9e4f0644589a813226e882f90e3233 | design record (level 3) |
| docs/architecture/backend-tracker-maps-issue-state.md | 0665c13189597a580a7a5767373d740caf08fc9a | record the earlier plan cited as a gate (PR-007) |
| wfctl/agents/skills/architecture-decisions/SKILL.md | 756693e68065f92f17f0114a71236e62d7824d5e | rule cited by PR-001, PR-017, PR-020, and PR-028 |
| research.md | b8015c26ddb60b7da79e333e5c34ee0037a8b556 | planning evidence |
| data-model.md | 558d1f2a5f9a8a18c1adfbaa0e283b1017fe1eb0 | planning evidence |
| contracts/cli.md | ba10fb462fa5dac38c200fcceba23351b2873022 | contract |
| contracts/tracker.md | f5d28911cc16479aabc462a560f26c3ac316f9b0 | contract |
| quickstart.md | 4565ddc30710c7dcf2f5f7eb329884aac2da4528 | planning evidence |
| exceptions/agent-host/brainstorm.software-design.md | a998dc5aa9f87b23c0ecb6eba0c4578597bd7d79 | design exception |
| exceptions/trackers/brainstorm.software-design.md | b0356fa11d015809abafac069ab35f882ce045d8 | design exception |
| checklists/requirements.md | 8b423183151c00ad8350355ee6667f0707d18870 | requirements-quality checklist |
| plan-review.plan.md | c11a401c257500ea2b6c98269a245d2f899cd4f9 | base of this re-review |

## Review scope

- Re-review: the plan copy's identity matches the earlier report's `plan.md`
  row (`c11a401c…`), so the copy is the base, and the diff against it is the
  plan change reviewed here
- Changed in `plan.md` since the earlier report: `§Summary` 1 (the commit
  count) and 4 (the last row's split, the three passages outside the table,
  the PR rerun line), the `design.md` note under `§Summary`, `§Technical
  Context` Constraints (the `OSError` and whitespace mapping, the tab and `\r`
  note), the new `§Constitution Check` gate, the ownership table's first and
  last rows, the `test_session_report.py`, `test_start_session_commands.py`,
  and `test_start_session_asks_conditionally.py` entries, the removed
  `session-report-built-in-code.md` entry, `§Tests the skill rewrite breaks` 4,
  `§The skill's allowed-tools`, and `§Risks` 5. Reviewed together with the
  sections that refer to them: the FR trace, the reason-code tests, and
  `§Tests the skill rewrite breaks` 1 and 3
- Inputs named as changed by the caller, each re-read in full with the whole
  of `plan.md` reviewed against it: the new accepted record
  `session-start-reads-branch-progress.md`, the now-superseded
  `session-report-built-in-code.md`, `spec.md`, `design.md`, `research.md`,
  `quickstart.md`, `data-model.md`, and `contracts/cli.md`. Every other input
  row of the earlier report matches its file
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification
- Conditional lenses: security and reliability applied, because the issue body
  is text anyone with tracker access can write, and it now helps decide what an
  agent does first on an issue branch, possibly with no person present
- Design records: the 2 level-3 records and the 2 level-2 records `design.md`
  lists, plus the two records they supersede, read for what changed
- Constitution: `.specify/memory/constitution.md` is absent; the plan takes its
  gates from AGENTS.md and the accepted records instead
- Unresolved markers: no `[NEEDS CLARIFICATION` marker stands in `spec.md` or
  `plan.md`
- Existing code inspected: `wfctl/_review.py review_trunk` and
  `wfctl/_paths.py trunk_branch`, to check the claim that the commit count
  reads the trunk "as reviews read it"; `start-session/SKILL.md` frontmatter,
  step 1's doctor re-run, and steps 7 and 8, to check PR-019, PR-030, and
  PR-031; `tests/test_start_session_asks_conditionally.py`; and rich's
  `console.print` with the plan's arguments on `a\tb\r\nc\x07d`, which printed
  `a       b\ncd`
- Reviewers: the four lenses above, run in sequence by one fresh-context agent

## Summary

BLOCKER: 0
MAJOR: 1
MINOR: 5

No BLOCKER findings identified in this review. PR-028 is fixed: the change
now has its own accepted record, `session-start-reads-branch-progress`, which
supersedes the one whose Decision said the step 8 table was unchanged. Eight
earlier findings are fixed in this round: PR-024, PR-026 to PR-032.

One new MAJOR finding: the artifacts give three definitions of the trunk the
commit count runs against, and the existing code the contract points at
("as reviews read it") falls back where the spec says "trunk not found" and
raises in cases the spec never maps, so the implementer has to choose (PR-033).
Two new MINOR findings: `design.md` still holds the size-limit question open
(PR-034), and the plan doesn't carry the spec's empty-issue-body case (PR-035).
PR-018, PR-019, and PR-025 stay open, each narrower than before.

## Findings

### PR-001: FR-021 edits the body of an accepted record

- Priority: BLOCKER
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `spec.md §FR-021`: the old record is now superseded by
    `session-start-reads-branch-progress.md`, rather than amended
- Finding: No deliverable edits an accepted record's body.
- Why it matters: The task list carries no deliverable that breaks the record
  rule.
- Suggested response: Fixed. The supersession also closes PR-028.
- Corroborated by: architecture and boundaries, requirements and traceability

### PR-002: No wfctl verb can make the #432 issue edits FR-021 asks for

- Priority: MAJOR
- Category: Dependency / Feasibility
- Status: fixed
- Evidence:
  - `spec.md §FR-021` and `plan.md §Risks` 4: the user makes the two issue
    edits, the agent drafts the text, and the PR waits for them
- Finding: The spec and plan say who makes the edits and how, with no `gh`
  route.
- Why it matters: The task for these edits has an owner and an order.
- Suggested response: Fixed by `spec.md §FR-021` and `plan.md §Risks` 4.
- Corroborated by: adversarial implementation, architecture and boundaries

### PR-003: Verbatim handoff and tracker text is not protected from rich markup

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `spec.md §FR-004`, `plan.md §Technical Context` Constraints,
    `contracts/cli.md §Console`, and the `test_session_report.py` entry
- Finding: The markup risk is named, with a requirement, a contract line, and
  a test.
- Why it matters: A bracket in the handoff no longer drops words or ends the
  report with a traceback.
- Suggested response: Fixed.
- Corroborated by: security and reliability, adversarial implementation

### PR-004: The step-3 pins on the last-stop read have no planned replacement

- Priority: MAJOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Tests the skill rewrite breaks` 1 - 3, and the
    `test_session_stopped_not_finished.py` entry
- Finding: Each protection the step 3 prose tests carry has a named code test.
- Why it matters: A regression in `last_stop()` that picks the wrong step 8
  row on trunk fails a test.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation and verification

### PR-005: The scaffold-tracker skill is not in the plan

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Project Structure`: `scaffold-tracker/SKILL.md`, and the
    `test_tracker.py` scaffold test covering `ALLOWED_CHANGES`
- Finding: Both verbs reach the skill, and its test extends to `changes`.
- Why it matters: A backend author learns that `branch` exists.
- Suggested response: Fixed.
- Corroborated by: single reviewer

### PR-006: The `#<key>` rule for digit keys is wfctl's own, not the key pattern's

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `spec.md §Assumptions`: the `#<key>` rule and its Azure DevOps failure case
- Finding: The rule is a labeled assumption with its known failure case.
- Why it matters: A later reader can tell a deliberate limit from an oversight.
- Suggested response: Fixed.
- Corroborated by: single reviewer

### PR-007: The Constitution Check cites a proposed record as an accepted gate

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `plan.md §Constitution Check`: both level-2 gates cite records that are
    accepted
- Finding: No gate presents a proposed record as binding.
- Why it matters: No reader takes a proposed record as in force.
- Suggested response: Fixed.
- Corroborated by: single reviewer

### PR-008: The "likely done" alignment item disappears without the spec saying so

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-019` and `plan.md §Summary` 4 both drop the item
- Finding: The spec and plan both say the item goes.
- Why it matters: The implementer doesn't have to guess.
- Suggested response: Fixed.
- Corroborated by: single reviewer

### PR-009: The no-`origin/HEAD` fallback marks no commit on an issue branch

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §Edge Cases`: the last 20 commits, none marked
- Finding: The exception sits in the spec, and research agrees.
- Why it matters: A test written from the spec covers this case.
- Suggested response: Fixed. How this case meets the existing trunk resolver
  is PR-033.
- Corroborated by: single reviewer

### PR-010: Three serial tracker reads can hold session start for 45 seconds

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Technical Context` Constraints: the reads run in a
    `ThreadPoolExecutor`
- Finding: A hang costs 15 seconds.
- Why it matters: A hanging network costs session start 15 seconds, not 45.
- Suggested response: Fixed.
- Corroborated by: single reviewer

### PR-011: The `branch` verb's answer is undefined when more than one PR matches

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §2` and `contracts/tracker.md`
- Finding: The selection rule is stated in research and in the contract.
- Why it matters: The PR line can't name another person's fork.
- Suggested response: Fixed.
- Corroborated by: single reviewer

### PR-012: design.md still says the report gives the handoff's path

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `design.md §Recommended Direction` 3: the report prints "the whole handoff"
- Finding: `design.md` itself now agrees with the spec.
- Why it matters: An implementer reading `design.md` first meets the current
  behaviour.
- Suggested response: Fixed.
- Corroborated by: single reviewer

### PR-013: Nothing checks the skill's command list

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Project Structure`: `test_start_session_commands.py`
- Finding: The command list has a test.
- Why it matters: A later edit that adds a list command back fails.
- Suggested response: Fixed.
- Corroborated by: single reviewer

### PR-014: `--session --json` carries the status version but not its shape

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `contracts/cli.md §JSON`: the ten session keys, and this document as their
    only contract
- Finding: The contract says what covers the session keys and when that
  changes.
- Why it matters: A future consumer knows where the shape is defined.
- Suggested response: Fixed. The key count now includes `commits_ahead`, and
  the example shows ten keys.
- Corroborated by: single reviewer

### PR-015: `markup=False` alone still changes the handoff, and commit subjects are unprotected

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `spec.md §FR-004` and `plan.md §Technical Context` Constraints
- Finding: The plan names every kind of outside text, and the arguments do
  what it claims for brackets, emoji codes, and long lines.
- Why it matters: A commit subject carrying `[/x]` no longer ends the report
  with a traceback.
- Suggested response: Fixed. The remaining byte changes are PR-018.
- Corroborated by: security and reliability, adversarial implementation

### PR-016: The skill's `allowed-tools` line still grants the list commands

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §The skill's allowed-tools` and the `test_start_session_commands.py`
    entry
- Finding: The plan says which grants go, and the test reads the frontmatter.
- Why it matters: A list command can't come back without a permission prompt
  and a failing test.
- Suggested response: Fixed. The kept list's own gap is PR-019.
- Corroborated by: single reviewer

### PR-017: The accepted record also says the skill runs one command

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `spec.md §FR-021`: `session-report-built-in-code.md` is superseded by a
    record that "no longer promises a size check or a skill that runs one
    command"
- Finding: The superseding record carries the change, so no Log line is
  needed.
- Why it matters: A reader of the record in force finds why the skill runs
  four commands.
- Suggested response: Fixed.
- Corroborated by: architecture and boundaries

### PR-018: The planned print call still turns tabs into spaces

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `plan.md §Technical Context` Constraints: the call "expands a tab to spaces
    and drops a `\r`, which FR-004 allows, since neither changes what the agent
    reads"
  - `spec.md §FR-004`: outside text "MUST print as written"; it names brackets,
    emoji codes, and long lines, and allows no byte change.
    `contracts/cli.md §Console` says the same and names no tab
  - `plan.md §Project Structure`, `test_session_report.py`: a handoff, issue
    body, and commit subject carrying "a tab … print as written"
  - Checked here: the plan's call prints `a\tb\r\nc\x07d` as `a       b\ncd`,
    so it drops BEL as well, which the plan doesn't name
- Finding: The plan now states the behaviour, which the earlier finding asked
  for, but it says `FR-004` allows it, and `FR-004` doesn't. The planned test
  then asserts that a tab prints "as written", which the planned call can't
  pass if "as written" means the bytes.
- Why it matters: The implementer has to decide which of the plan's two
  statements the tab test asserts. A test written to the spec fails against
  code written to the plan.
- Suggested response: Either add one line to `spec.md §FR-004` and
  `contracts/cli.md §Console` saying tabs print as spaces and carriage returns
  and other control characters are dropped, and make the test assert that, or
  print outside text with plain `print`. Name BEL with `\r` in either case.
- Corroborated by: security and reliability, adversarial implementation

### PR-019: The kept grants don't cover the doctor re-run a `uv run` repair calls for

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `plan.md §The skill's allowed-tools`: now keeps `uv run wfctl doctor` "since
    the repair reference re-runs doctor through `uv run` in this repository",
    and still keeps `uv run --project * wfctl install-skills`
  - `start-session/SKILL.md` frontmatter: grants `Bash(uv run --project *
    wfctl install-skills*)`; step 1: "run `wfctl doctor` again and check it is
    green"
- Finding: The in-repository case is covered. The `uv run --project <path>`
  repair, which the kept grant exists for, still has no matching doctor grant.
- Why it matters: A session that repairs a layer installed from another source
  path can't re-run doctor through the same wfctl unattended, and a bare
  `wfctl doctor` compares against a different bundle (AGENTS.md §Definition of
  done).
- Suggested response: Add `Bash(uv run --project * wfctl doctor*)`, or say in
  the plan that the `--project` re-run is left to a prompt on purpose.
- Corroborated by: single reviewer

### PR-020: `not checked` and `couldn't check` contradict the accepted tracker-reads record

- Priority: BLOCKER
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `spec.md §FR-012`, `contracts/cli.md`, `contracts/tracker.md`,
    `data-model.md §SessionReport`, and `plan.md §Technical Context` carry the
    seven codes of `tracker-reads-report-failure`
- Finding: The plan and its contracts match an accepted record.
- Why it matters: Tasks built on this plan implement what the in-force record
  decides.
- Suggested response: Fixed.
- Corroborated by: architecture and boundaries, requirements and traceability

### PR-021: The three-outcome mapping leaves some `_read_verb` returns unnamed

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Technical Context` (`read_text()`), `contracts/tracker.md`, and
    the `test_session_report.py` entry
- Finding: Each `_read_verb` return has an answer.
- Why it matters: A broken script reads as `failed`, not as "unsupported".
- Suggested response: Fixed, with PR-026.
- Corroborated by: adversarial implementation and verification

### PR-022: The plan carries only the first-action half of FR-022

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Summary` 4 and the `test_start_session_commands.py` entry
- Finding: The plan and its test carry the authority half of FR-022.
- Why it matters: An instruction in the issue body is covered wherever in the
  session the agent meets it.
- Suggested response: Fixed.
- Corroborated by: security and reliability, requirements and traceability

### PR-023: `data-model.md` has no `tracker_reads` field

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `data-model.md §SessionReport`: a `tracker_status` row
- Finding: The data model, contract, research, and plan agree on the field.
- Why it matters: The JSON can tell "no PR" from "the lookup failed".
- Suggested response: Fixed.
- Corroborated by: single reviewer

### PR-024: The trunk-branch story still says the report has no tracker lines

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §User Story 2`: "each tracker line reads `not-applicable`", and
    Acceptance Scenario 1: the three lines "each read `not-applicable`, and the
    report makes no tracker call"
  - `design.md §Recommended Direction` agrees
- Finding: The story, FR-008, the record, and the contracts agree.
- Why it matters: A test written from User Story 2 matches the contract.
- Suggested response: Fixed by `spec.md §User Story 2`.
- Corroborated by: requirements and traceability, architecture and boundaries

### PR-025: Planning artifacts still cite or describe the superseded record

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: open
- Evidence:
  - Fixed since the earlier review: `design.md §MVP Scope` 2 now says a
    missing or failing verb "prints a reason code"; neither `design.md` nor
    `spec.md §FR-012` says "once accepted"; `research.md §3` cites
    `tracker-reads-report-failure`; the plan's override note is replaced by
    "`design.md` was updated on 2026-11-02"
  - Still standing: `exceptions/trackers/brainstorm.software-design.md`: "The
    two tracker verbs and their optional, silent-on-failure behaviour are
    decided in backend-tracker-reads-parent-and-change … with no structural
    alternative weighed"
  - `plan.md §Technical Context`: a new `read_text()` sits beside `_read_verb`
    rather than changing the shape `fields` and `state` rely on, which is a
    structural choice in `_tracker.py` with its alternative stated
  - Also stale: `exceptions/agent-host/brainstorm.software-design.md` says the
    skill "keeps the step 8 table"; the table's last row now splits by branch
    kind
- Finding: Left for a person, as the caller said, and it still stands. The
  trackers exception gives as its reason a record that is superseded and a
  behaviour, silence on failure, that the record in force reverses. Its claim
  that no structural alternative was weighed is also contradicted by the plan's
  own `read_text()` choice. The agent-host exception describes the step 8 table
  as kept, which `FR-017` and `FR-022` no longer say.
- Why it matters: An exception is the reason a design pass did not run. Both
  reasons now describe a design that is not the one being built, so a reviewer
  reading them in the PR body checks a claim that no longer holds.
- Suggested response: Have a person decide, for each exception, whether to
  restate its reason against the current records or let the pass run. For the
  trackers one, `read_text()` beside `_read_verb` is the candidate level-3
  choice.
- Corroborated by: architecture and boundaries

### PR-026: `read_text()`'s mapping leaves two `_read_verb` outcomes unnamed

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Technical Context` Constraints: "An `OSError` when the script
    launches is `failed`, and output is stripped before the check for `none`"
  - the `test_session_report.py` entry covers both
- Finding: Both outcomes have a code and a test.
- Why it matters: A missing script reads `failed`, and a blank line can't
  print as an answer.
- Suggested response: Fixed. The next sentence reads "`read_text()` and
  `_read_verb` keeps its current shape for `fields` and `state`", which looks
  like an editing slip for "`_read_verb` keeps …"; worth correcting when the
  plan is next touched.
- Corroborated by: adversarial implementation and verification

### PR-027: The skill plan says nothing about what the agent does with a `failed` or `timeout` line

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Summary` 4: "A `PR: failed` or `PR: timeout` line tells the
    agent to run `wfctl status --session` again before it relies on the PR's
    state", and the issue line with no answer makes the agent ask
- Finding: The skill change carries the record's rerun instruction for the PR
  line, and a rule for the issue line.
- Why it matters: Step 8 no longer starts work with `PR: timeout` unread.
- Suggested response: Fixed. No planned test reads the rerun line; adding it
  to `test_start_session_commands.py` would keep it from being dropped.
- Corroborated by: adversarial implementation and verification, security and
  reliability

### PR-028: The step 8 change contradicts the accepted `session-report-built-in-code` record

- Priority: BLOCKER
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `docs/architecture/session-report-built-in-code.md`: status `superseded`,
    Log "superseded — by session-start-reads-branch-progress"
  - `docs/architecture/session-start-reads-branch-progress.md`: accepted,
    `supersedes: session-report-built-in-code`; its Decision states the issue
    branch rule
  - `spec.md §FR-021`, `§FR-022`, `design.md §Architecture decisions`, and
    `plan.md §Constitution Check` all cite the new record
- Finding: The step 8 change is a decision in its own accepted record, and the
  record that said the table was unchanged is no longer in force.
- Why it matters: Tasks built from this plan ship a skill that matches the
  record in force.
- Suggested response: Fixed by the new record.
- Corroborated by: architecture and boundaries, requirements and traceability

### PR-029: design.md, SC-003, User Story 3, and quickstart still say the step 8 row stays the same

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §SC-003`: the same row "except on an issue branch whose handoff
    names no first action"; `§User Story 3` narrative and Acceptance
    Scenarios 3 and 4 state the change
  - `quickstart.md` step 4 names the one exception
  - `design.md §Key Assumptions`, `§Out of scope` 1, and `§Recommended
    Direction` all name the issue-branch change
  - `contracts/cli.md §Console`: the heading is now `Issue (tracker text)`
- Finding: Every artifact that described the old row now names the exception.
- Why it matters: The quickstart run and SC-003 no longer report the intended
  change as a regression.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability, architecture and boundaries

### PR-030: The step 8 change has substring tests only, and the plan doesn't say which row-bound tests it breaks

- Priority: MAJOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Tests the skill rewrite breaks` 4: names
    `test_a_state_dir_with_no_answer_in_it_is_still_asked`,
    `test_a_continued_stop_does_not_relax_the_quote_gate`, and
    `test_step_seven_reports_which_row_step_eight_took`, and what each becomes
  - The same item: new tests "read the table row by row", checking that the
    issue row and the trunk row differ, that the issue row names the three
    pieces of evidence and asks on a mismatch, and that the trunk row still asks
- Finding: The plan names how the last row splits, which tests change, and
  row-bound tests for both rows.
- Why it matters: A skill with the two rows swapped fails a test.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation and verification, requirements
  and traceability

### PR-031: The skill prose around the table still states the quote rule, and the issue-lookup failure case is undefined

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Summary` 4: names step 8's "The gate on the summary is the
    quote", step 8's "Two limits", and step 7's Next bullet, and says what each
    becomes
  - `plan.md §Summary` 4 and `spec.md §FR-022`: the agent asks "when the
    evidence disagrees or the issue line has no answer"
- Finding: The plan rewrites each passage that stated the old rule, gives step
  7 the evidence the agent used, and states the fallback.
- Why it matters: Two implementers produce skills that behave the same on an
  unattended issue session with no handoff.
- Suggested response: Fixed. The empty-body case the spec adds is PR-035.
- Corroborated by: adversarial implementation and verification, requirements
  and traceability

### PR-032: Risk 5's mitigation now covers only push, comment, and PR, while issue text directs every other action

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `spec.md §FR-022`: the agent "MUST NOT run a command, URL, script, or
    package named in the issue, or push, comment, or open a PR because the
    issue says to, at any point in the session"
  - `plan.md §Risks` 5: the first action is always the next pipeline command,
    nothing named in the issue is run, and the agent asks on disagreement; a
    test reads the sentence in step 8
  - `session-start-reads-branch-progress.md §Considered`: letting the issue
    name the first action directly was weighed and not chosen
  - `contracts/cli.md §Console`: `Issue (tracker text)`, and the paragraph
    under it states the same bound
- Finding: The issue can only shape the work of a step the pipeline already
  chose, and the bound is in the spec, the record, the contract, and a test.
- Why it matters: Text in the issue body can't direct an unattended session
  to run a script or fetch a URL.
- Suggested response: Fixed.
- Corroborated by: security and reliability, adversarial implementation and
  verification

### PR-033: Three definitions of the trunk the commit count runs against, and the existing resolver disagrees with the spec

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `spec.md §FR-005` and `contracts/cli.md §Console`: the trunk is the
    `trunk` that `wfctl.json` declares on the default branch, "as reviews read
    it", or the default branch when none is declared;
    `session-start-reads-branch-progress.md §Consequences` says the same
  - `research.md §5`: "The trunk is what `origin/HEAD` names, as the skill uses
    today", with no declared trunk
  - `spec.md §Edge Cases` and `contracts/cli.md`: with no `origin/HEAD`, the
    count reads `Commits: trunk not found` and lists the last 20 commits
  - `wfctl/_review.py review_trunk`, which is how reviews read it: with no
    `origin/HEAD`, it falls back to `_paths.trunk_branch`, which reads the
    working tree's `trunk`, then a bare HEAD, then local `main`, `master`, or
    `dev`, so it finds a trunk where the spec says none is found. It also
    raises `ReviewError` when `origin/HEAD` names a ref the clone lacks, and
    `NoTrunk` when a declared trunk can't be resolved
  - `plan.md` names neither function, and its only statement of the
    resolution is the test entry "against a declared trunk, against the
    default branch, and `trunk not found`"
  - `data-model.md`: `commits` has the empty case "empty list", while the
    contract lists the last 20 commits when the trunk can't be found
- Finding: The implementer has to choose between reusing `review_trunk`, which
  contradicts the spec's no-`origin/HEAD` case, writing a third resolver, and
  following `research.md`. Whichever is chosen, the plan doesn't say which of
  `review_trunk`'s raises become `trunk not found`, or whether the merge base
  is taken against `origin/<trunk>` or the local branch, which can be behind.
- Why it matters: An unmapped `ReviewError` or `NoTrunk` ends `status
  --session` with a traceback, which breaks `FR-004`'s "MUST NOT stop the
  report" and the contract's exit 0. The count is the first of the three
  pieces of evidence `FR-022` uses to choose a first action, so a count taken
  against a stale local `main` misleads the agent on the sessions nobody is
  watching.
- Suggested response: In `plan.md §Technical Context`, name the resolver and
  how each of its failures maps to `trunk not found`, and say which ref the
  merge base uses. Correct `research.md §5` to `FR-005`'s definition. If the
  no-`origin/HEAD` case should follow `review_trunk`'s fallback instead, that
  is a `spec.md §Edge Cases` edit. Give `data-model.md`'s `commits` row the
  last-20 case.
- Corroborated by: requirements and traceability, adversarial implementation
  and verification

### PR-034: design.md still holds the size-limit question open

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `design.md §MVP Scope`, out of scope 2: "The issue's done-when still lists
    it, so it needs the user's call before the issue changes"; `§Open
    Questions`: "Whether the issue's done-when keeps the size limit test"
  - `spec.md §Clarifications`: answered, the test moves to #693; `§FR-021`:
    the done-when drops it, and the user makes the edit
- Finding: The spec settled the question `design.md` still lists as open.
- Why it matters: An implementer reading `design.md` first, as the pipeline
  orders, may hold the FR-021 issue edit for a call already made.
- Suggested response: Point `design.md §Open Questions` and out of scope 2 at
  the spec's clarification, or say in `plan.md` that the spec settles it.
- Corroborated by: single reviewer

### PR-035: The plan doesn't carry the spec's empty-issue-body case

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `spec.md §Edge Cases`: "The issue line reads `failed`, `timeout`,
    `unsupported`, `no-tracker`, or `bad-config`, or the issue body is empty.
    The agent has only the commit count and the pipeline position, so it asks."
  - `plan.md §Summary` 4: the agent asks "when the evidence disagrees or the
    issue line has no answer"; `§Tests the skill rewrite breaks` 4: the issue
    row "says it asks on a mismatch"
  - `contracts/cli.md`: `view` output prints as the backend wrote it, and the
    GitHub `view` prints the title and fields even when the body is empty, so
    the issue line has an answer
- Finding: An issue with an empty body gives the issue line an answer, so the
  plan's wording starts work there, while the spec asks.
- Why it matters: The skill's wording decides what an unattended session does
  on a freshly filed issue with no description, which is a common case for a
  new worktree.
- Suggested response: Add "or the issue's body is empty" to the step 8
  wording in `plan.md §Summary` 4, and to the issue-row test.
- Corroborated by: single reviewer

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Summary 1, §Project Structure (`cli.py`, `test_cli_status.py`) | covered |
| FR-002 | contracts/cli.md §JSON, data-model.md §SessionReport | covered |
| FR-003 | data-model.md (`last_stop`), `test_session_stopped_not_finished.py` | covered |
| FR-004 | plan.md §Technical Context, contracts/cli.md §Console, `test_session_report.py` | covered; PR-018 |
| FR-005 | plan.md §Summary 1, data-model.md `commits_ahead`, contracts/cli.md, `test_session_report.py` | partial; PR-033 |
| FR-006 | data-model.md `accepted_records` | covered |
| FR-007 | research.md §1 - 3, contracts/tracker.md | covered |
| FR-008 | contracts/cli.md §Console on a trunk branch, data-model.md `tracker_status` | covered |
| FR-009 | contracts/cli.md | covered |
| FR-010, FR-011 | contracts/tracker.md, `_tracker.py`, `scaffold-tracker/SKILL.md` | covered |
| FR-012 | plan.md §Technical Context (`read_text()`), contracts, `test_session_report.py` | covered |
| FR-013, FR-014 | data-model.md §ClaimNotice filter, `test_doctor_session.py` | covered |
| FR-015, FR-016 | plan.md §Summary 4, §The skill's allowed-tools, `test_start_session_commands.py` | covered |
| FR-017 | plan.md §Summary 4, `SKILL.md` entry, §Tests the skill rewrite breaks 4 | covered |
| FR-018 | research.md §7, `references/doctor-repair.md`, `test_start_session_notice_quotes.py` | covered; PR-019 |
| FR-019 | research.md §4 - 5, spec.md §Edge Cases and §Assumptions | covered |
| FR-020 | `changes/432.change.md` | covered |
| FR-021 | plan.md §Summary 5, §Risks 4; record superseded | covered; PR-034 |
| FR-022 | plan.md §Summary 4, §Risks 5, §Tests the skill rewrite breaks 4, contracts/cli.md §Console, `test_start_session_commands.py` | covered; PR-035 |
| SC-001, SC-002 | plan.md §Constitution Check, quickstart.md step 5 | covered |
| SC-003 | plan.md §Tests the skill rewrite breaks, quickstart.md step 4 | covered |
| SC-004 | research.md §7 | covered |
| SC-005 | data-model.md §ClaimNotice filter | covered |

## Assumptions challenged

- The commit count reads the trunk "as reviews read it" (`contracts/cli.md`,
  `FR-005`). Checked against `review_trunk`: it agrees when `origin/HEAD`
  exists and resolves, and disagrees with the spec when it doesn't (PR-033).
- `console.print` with the four arguments changes nothing the agent reads
  (`plan.md §Technical Context`). It changes tabs, `\r`, and BEL, and the
  spec's "as written" doesn't allow that yet (PR-018).
- An issue line with an answer is enough evidence to start from. Not for an
  issue with an empty body, which the spec treats as no evidence (PR-035).
- The first action is always the next command the pipeline position names
  (`plan.md §Risks` 5). On an issue branch with no spec folder, #679's
  paragraph still runs the spec question first, and the plan keeps that
  paragraph, so the two compose: the row decides the step, and the paragraph
  decides the route.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- The step 8 change now has its own accepted record, with the direct baseline
  and the "proceed and report the mismatch" alternative weighed, so the plan
  no longer argues with a record in force.
- The issue's influence is bounded by the pipeline: it shapes the work of the
  step wfctl's position already names, and never names the step itself.
- `§Tests the skill rewrite breaks` 4 names each old row-bound test and its
  replacement, and keeps the trunk protection those tests carried.
- `read_text()` sits beside `_read_verb` rather than changing the shape
  `fields` and `state` rely on.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
