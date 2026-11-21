# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 9961891f8d7e35c6eed1f72c732c78d3ef4a28ee | technical strategy |
| spec.md | 6bbaff42a2ec1529a4ea7dde5ee47d51b09c5318 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | c4cd4077024eb83527a869bbe1bce498027d10d7 | design-record index |
| docs/architecture/design/prompted-spellings-one-table.md | fe7e80871ca3745c1109e62a0b919acf89424264 | design record (level 3, proposed) |
| docs/architecture/prompt-approves-person-commands.md | a9de0f51e2e91f1ac6f5f404171b21dfc3340765 | level-2 record carrying the threat model |
| docs/architecture/accept-check-threat-model.md | f2e35654505027d1dda08b36026c994d0ceaeccb | superseded record whose items 1 - 20 the level-2 record keeps |
| docs/architecture/guard-catches-literal-accept.md | 01a32d319ab38e1432fc9514316c21b05e8dd7dc | superseded record the Records section reads |
| research.md | a545d35cda60953761971321c8a9116a6a4efbed | planning evidence |
| data-model.md | 75a508b9d0d5562d0c699da0e064fc66c567d4ec | planning evidence |
| contracts/cli.md | 43f18b513386228ce99cd7bd01bbfbc0be2c6e05 | planning evidence |
| quickstart.md | 27f626f680460b51fb2a0ac4e88ab2b4edcb562e | planning evidence |
| plan-review.plan.md | 59f75d5ed10a296faa1a22e1ff0e3ed13215e8ad | base of this re-review |

## Review scope

- Re-review: the earlier report and the plan copy both existed, and the copy's identity matched the earlier report's `plan.md` row.
- Changed in `plan.md`: §Technical Context (the cost line now says one small file read) and §The commands item 1 (the redraw's Log line is `redrawn — …` and "drawing signed off" is the console text; a new paragraph for FR-017's re-accept of an amended record). Reviewed together with §The guard's cost sentence, §Tests, §Project Structure, and the requirement trace, which refer to the changed sections.
- Inputs changed since the earlier report: `spec.md` (FR-004, SC-003, and User Story 5 scenario 1 now say `doctor` prints a `⚠` line and leaves the exit code alone) and `contracts/cli.md` (the redraw now logs `redrawn — …` and prints "drawing signed off"). Each was re-read in full, and the whole of `plan.md` was reviewed against it. `design.md`, `research.md`, `data-model.md`, `quickstart.md`, the level-3 record, the level-2 record, and the two superseded records match their earlier rows.
- Lenses: requirements and traceability, architecture and boundaries, adversarial implementation and verification.
- Conditional lenses: security and reliability applied, since the change removes one of the guard's refusals on three person-only commands, and FR-017 changes what `arch accept` does to an accepted record.
- Existing code inspected: `wfctl/cli.py` near lines 3075 - 3250 (`needs_reaccept` is checked before `needs_redraw`, so a re-accept takes the place of a redraw; the dry run prints "amendment would be accepted" and the write prints "amendment accepted — <citation>"; a redraw prints "drawing signed off"), `wfctl/arch/_records.py` near line 881 (`needs_reaccept` is true when the last Log line is `amended`), and the `tests/` listing (`test_arch_accept.py` exists). The branch already carries an implementation commit (59aac67); the review judges the planning artifacts, and reads code only to test their claims.
- Reviewers: the four lenses above, run in sequence by one agent in a fresh context.

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 5

No BLOCKER findings identified in this review. PR-022, PR-023, and PR-024 are fixed.

The spec now says what the contract and `quickstart.md` step 9 already said: a missing rule prints a `⚠` line in `doctor` and leaves the exit code alone, which is what reusing #407's `_ManagedRule` path gives (PR-022). The plan now carries FR-017, with its output, its dry run, its interaction with a redraw, and its tests, and the code agrees with each claim (PR-023). The redraw's Log line has one spelling across the plan, the contract, and the data model (PR-024).

The open MINOR findings are four older ones (PR-008 narrowed again, PR-017, PR-021, PR-025) and one new lag: the contract has no output for the re-accept, and the plan's file list leaves out the test file it names (PR-026).

## Findings

### PR-001: The shlex-based match lets quoted and backslashed spellings through

- Priority: BLOCKER
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `plan.md §The guard` pass check items 1 - 3, unchanged.
- Finding: Fixed in an earlier review. Unchanged.
- Why it matters: The forms the record lists as refused stay refused.
- Suggested response: None.
- Corroborated by: requirements and traceability, security and reliability

### PR-002: The guard keeps refusing the search for the sign-off command

- Priority: BLOCKER
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §The guard`, "Sign-off and approve-imports get the accept's reader", unchanged.
- Finding: Fixed in an earlier review. Unchanged.
- Why it matters: FR-009 and SC-002 can be met as planned.
- Suggested response: None.
- Corroborated by: requirements and traceability, adversarial implementation

### PR-003: The walk in Claude Code runs the installed wfctl, not the branch

- Priority: MAJOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `quickstart.md` steps 0 and 12, `plan.md §Validation`, unchanged.
- Finding: Fixed in an earlier review. Unchanged.
- Why it matters: The walk exercises the branch's guard and commands.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-004: Every child process inherits `CLAUDECODE`, including agents that run no guard

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §The commands`, second paragraph, unchanged.
- Finding: Fixed in an earlier review. Unchanged.
- Why it matters: The residual risk is named for the user to confirm.
- Suggested response: None.
- Corroborated by: security and reliability, adversarial implementation

### PR-005: The superseded record's items 1 - 20 lose their tests, and two of them have no settled answer

- Priority: MAJOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Tests` item 1, unchanged.
- Finding: Fixed in an earlier review. Unchanged.
- Why it matters: A regression on items 3 - 20 fails the suite.
- Suggested response: None.
- Corroborated by: requirements and traceability, adversarial implementation

### PR-006: The suite's terminal-refusal tests change behavior inside Claude Code

- Priority: MAJOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Tests` item 6, unchanged.
- Finding: Fixed in an earlier review. Unchanged.
- Why it matters: Results don't depend on the shell running the suite.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-007: The dry-run prompt stalls unattended runs

- Priority: MAJOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §The commands` item 2, `contracts/cli.md §wfctl arch check-accept`, unchanged.
- Finding: Fixed in an earlier review. The new FR-017 dry-run text reaches `check-accept` too, since it runs what the dry run runs.
- Why it matters: An unattended brainstorm doesn't stop at a prompt nobody answers.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-008: The pass check's inputs and costs don't fit `read()`

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - Fixed part: `plan.md §Technical Context` now says "one small file read", which matches `§The guard`'s "A matching one pays one small file read".
  - `plan.md §The guard` item 5, unchanged: "a repository git can't name is refused", so the check still asks git for the repository root before it reads `.claude/settings.json`. Neither cost line counts that call, and the plan doesn't say it runs under `_review_gate.TIMEOUT`.
- Finding: The two cost lines now agree, and both still leave out the git call that finds the repository, with no bound named for it.
- Why it matters: Small. A git call with no bound in a hook the host kills on its own timeout exits without code 2, and the command then runs, which is the failure the pass check exists to close.
- Suggested response: Say the repository lookup runs under `TIMEOUT`, and count it in both cost lines.
- Corroborated by: single reviewer

### PR-009: The host check's name and export disagree across the plan

- Priority: MINOR
- Category: Boundary / Ownership Concern
- Status: fixed
- Evidence:
  - `plan.md §The table` and `§Source Code`, unchanged.
- Finding: Fixed in an earlier review. Unchanged.
- Why it matters: A test for FR-011 has one reading to follow.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-010: The refusal wording differs between the plan and the contract

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §The guard` and `contracts/cli.md §Worktree guard refusals` give the same four reasons in the same order, unchanged.
- Finding: Fixed in an earlier review. Unchanged.
- Why it matters: Tests and skills quote one text.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-011: Two `--agreed` cases have no behavior

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §The commands` item 1 and `contracts/cli.md §wfctl arch accept`.
- Finding: Fixed in an earlier review. The redraw case's wording now agrees too (PR-024).
- Why it matters: Both Log lines have a stated form.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-012: The Log-line claim is loosely defined and departs from the accepted record

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `plan.md §Records`, unchanged.
- Finding: Fixed in an earlier review. Unchanged.
- Why it matters: The reading clears only the intended warning.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-013: Some negative paths in the spec have no test or walk step

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `quickstart.md` steps 6, 7a, and 8, and `plan.md §Tests` item 7, unchanged.
- Finding: Fixed in an earlier review. Unchanged.
- Why it matters: An auto mode that skips `ask` rules would show up in the walk rather than in use.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-014: The level-3 design record still decides the split-word match the threat model refuses

- Priority: BLOCKER
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `prompted-spellings-one-table.md §Decision` item 2, unchanged.
- Finding: Fixed in an earlier review. PR-025 tracks the record's cost line.
- Why it matters: The level-3 record decides the same pass rule the plan uses.
- Suggested response: None.
- Corroborated by: architecture and boundaries, security and reliability

### PR-015: The walk's sign-off signs off the implementation's own commits

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `quickstart.md` steps 6 - 8, unchanged.
- Finding: Fixed in an earlier review. Unchanged.
- Why it matters: The review panel still has to run on this branch.
- Suggested response: None.
- Corroborated by: adversarial implementation, security and reliability

### PR-016: Planning artifacts still describe what the revision replaced

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `data-model.md §Accept Log line`, unchanged.
- Finding: Fixed in an earlier review. Unchanged.
- Why it matters: Tasks generated from the table see every case the contract names.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-017: The kept refusal headline contradicts the new reason line

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `plan.md §The guard` item 2, unchanged: "the refusal lists the characters to remove from the command".
  - `contracts/cli.md` reason 4, unchanged by this round's edit: a fixed example list, "such as $ ; & | < > ( ) or a backslash or backtick", with no newline and no unquoted `#`.
- Finding: The plan and the contract still describe the not-plain reason line differently, and the contract's text gives an agent refused for a newline or an unquoted `#` nothing to act on.
- Why it matters: Small. Tests quote this text, and an agent that can't see what to change spends a round guessing.
- Suggested response: Pick one: print the characters found, or print the full list from items 2 and 3, including the newline and an unquoted `#`. Make the plan and the contract say the same.
- Corroborated by: single reviewer

### PR-018: The repository's own citation form is refused

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §The guard` item 3, unchanged.
- Finding: Fixed in an earlier review. Unchanged.
- Why it matters: An issue reference, the usual citation here, can be passed.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-019: The plan decides how items 16 and 19 of the old list are read

- Priority: MINOR
- Category: Boundary / Ownership Concern
- Status: fixed
- Evidence:
  - `plan.md §Tests` item 1, unchanged.
- Finding: Fixed in an earlier review. Unchanged.
- Why it matters: The user sees what counts as a regression before the change lands.
- Suggested response: None.
- Corroborated by: requirements and traceability, security and reliability

### PR-020: The generalized reader's coverage for sign-off and approve-imports has no test

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Tests` item 1, unchanged.
- Finding: Fixed in an earlier review. Unchanged.
- Why it matters: A site left hard-coded to the accept fails a test.
- Suggested response: None.
- Corroborated by: adversarial implementation

### PR-021: Stripping leading whitespace assumes Claude Code's rule matches the stripped form

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `plan.md §The guard` item 1, unchanged: "The raw command, with leading and trailing whitespace removed, starts with one `PROMPTED` entry's words", and "That is the form Claude Code's rule matches too."
  - `quickstart.md`, unchanged, still has no step with a leading space.
- Finding: Leading whitespace can change a prefix match, and nothing in the artifacts shows Claude Code trims it before matching `Bash(wfctl arch accept:*)`. If it doesn't, ` wfctl arch accept s` passes the guard and runs with no prompt.
- Why it matters: The failure direction is the one the threat model exists to close, though an agent that isn't hiding what it runs rarely writes a leading space.
- Suggested response: Strip only trailing whitespace, so a leading space fails closed. Or keep the strip and add a quickstart step that runs a leading-space accept and records whether the prompt appears.
- Corroborated by: security and reliability, adversarial implementation

### PR-022: The contract and the spec disagree on whether `doctor` exits 1 for a missing rule

- Priority: BLOCKER
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-004` now: "report a missing rule with a `⚠` line naming what losing it costs, and leave the exit code alone, as for every managed rule".
  - `spec.md §SC-003` now: removing a rule makes `doctor` "print a `⚠` line naming it and the guard refuse that spelling".
  - `spec.md` User Story 5 scenario 1 now: "prints a `⚠` line naming the rule. It leaves the exit code alone".
  - `contracts/cli.md §wfctl doctor` and `quickstart.md` step 9 say the same, and `plan.md §Rules` gets that behavior by reusing #407's `_ManagedRule` path.
- Finding: Fixed in `spec.md`. All four artifacts now describe a warning that leaves the exit code alone, which is what the plan's mechanism does.
- Why it matters: A test written from any of them asserts the same behavior.
- Suggested response: None.
- Corroborated by: requirements and traceability, adversarial implementation

### PR-023: FR-017 has no place in the plan

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §The commands` item 1 now covers FR-017 and #838: on an accepted record whose last Log line is `amended`, the accept writes a new `accepted` line and prints "amendment accepted", the dry run prints "amendment would be accepted", a re-accept takes the place of a redraw because its `accepted` line carries the drawing fingerprints, and any other last line still reads as already accepted. `tests/test_arch_accept.py` covers the amended record, a third accept refused, and the dry run.
  - `wfctl/cli.py` near lines 3080 - 3245 matches each of these claims, and `check-accept` reaches the same dry-run text through PR-007's rule.
  - `data-model.md §Accept Log line`, last row, gives the appended line.
- Finding: Fixed. The requirement now has a technical approach, its interaction with a redraw, and tests. PR-026 tracks the contract, which still gives no output for it.
- Why it matters: Tasks generated from the plan now carry FR-017.
- Suggested response: None.
- Corroborated by: requirements and traceability, security and reliability

### PR-024: The redraw's Log line has two spellings

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §The commands` item 1 now: the redraw's Log line is `redrawn — …at the permission prompt`, and "Drawing signed off" is only the console text.
  - `contracts/cli.md §wfctl arch accept` now: a redraw "logs `redrawn — …at the permission prompt`, and prints 'drawing signed off'".
  - `data-model.md §Accept Log line` redraw row, unchanged, and `wfctl/cli.py` near line 3242 agree.
- Finding: Fixed. The plan, the contract, the data model, and the code give one Log line and one console line.
- Why it matters: A test written from the contract asserts the line `_records.py` reads.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-025: Three planning inputs still describe the auto-approve check the plan removed

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `research.md §R-004`, unchanged: "Where the guard finds the auto-approve mode", deciding `wfctl.evidence.auto_approve(agent_dir)`.
  - `design.md §MVP Scope` item 3, unchanged: the guard lets a command through only when "wfctl's auto-approve is off".
  - `prompted-spellings-one-table.md §Consequences`, unchanged: "The guard reads `.claude/settings.json` and the auto-approve mode file … two small file reads".
  - `plan.md §The guard`: "wfctl's auto-approve isn't checked", and now one file read in both cost lines.
- Finding: The plan, the spec, the contract, and the amended level-2 record agree that auto-approve is no longer a condition. The research decision, the design brief, and the proposed level-3 record still describe it as one.
- Why it matters: Small. The level-3 record is still proposed, so a user reading it before accepting it sees a mode-file read that no longer exists, and a task generated from `research.md` would build the dead call.
- Suggested response: Mark R-004 as no longer used, note the change in `design.md`, and amend the level-3 record's Consequences to one file read before it is put to the user.
- Corroborated by: architecture and boundaries

### PR-026: The contract has no output for FR-017, and the file list leaves out its test

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `plan.md §The commands` item 1: the re-accept prints "amendment accepted", and the dry run prints "amendment would be accepted".
  - `contracts/cli.md §wfctl arch accept`, changed this round only for the redraw line: no output for a re-accept or its dry run.
  - `plan.md §Project Structure` lists `tests/test_arch_accept_dry_run.py` and not `tests/test_arch_accept.py`, which §The commands item 1 names for the FR-017 tests.
- Finding: The plan names console text and a test file that the contract and the plan's own file list don't carry.
- Why it matters: Small. A task generated from the contract has no output line to assert for the re-accept, and one generated from the file list puts the tests elsewhere.
- Suggested response: Add the two re-accept lines to `contracts/cli.md §wfctl arch accept`, and add `tests/test_arch_accept.py` to §Project Structure.
- Corroborated by: requirements and traceability

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §The table | covered |
| FR-002 | plan.md §Rules | covered, through #407's `_ManagedRule` |
| FR-003 | plan.md §Rules, §Tests item 3 | covered |
| FR-004 | plan.md §Rules, §Tests item 3 | covered; the exit code is left alone, as the `_ManagedRule` path does |
| FR-005 | plan.md §The guard, pass check items 1 - 3 | covered; PR-021 |
| FR-006 | plan.md §The guard (auto-approve isn't checked), §Tests item 2 | covered |
| FR-007 | plan.md §The guard, pass check item 4 | covered |
| FR-008 | plan.md §The guard, pass check item 5 | covered; PR-008 |
| FR-009 | plan.md §The guard, §Tests items 1, 2, 5 | covered |
| FR-010 | plan.md §The guard, contracts/cli.md | covered; PR-017 |
| FR-011 | plan.md §The commands, §Tests items 4, 6, 7 | covered |
| FR-012 | plan.md §The commands items 3 - 4 | covered |
| FR-013 | plan.md §The commands item 1 | covered |
| FR-014 | plan.md §The commands item 4 | covered |
| FR-015 | plan.md §Records | covered |
| FR-016 | plan.md §The commands item 2, §Tests item 8 | covered |
| FR-017 | plan.md §The commands item 1 | covered; PR-026 |
| SC-001 | plan.md §Validation, quickstart.md | covered |
| SC-002 | plan.md §Tests items 1 - 2 | covered |
| SC-003 | plan.md §Tests items 2 - 3, quickstart.md step 9 | covered |
| SC-004 | plan.md §The commands item 1 | covered |

## Assumptions challenged

- A missing managed rule never reaches `doctor`'s exit code. Checked earlier in `_check_managed_permissions`; the spec now relies on it, and the guard's refusal is what makes a missing rule visible in use.
- A re-accept of an amended record carries the drawing fingerprints, so a changed drawing on an amended record needs no separate redraw. Checked: `cli.py` computes `redraw` only when `reaccept` is false, and its comment says the same.
- wfctl's auto-approve doesn't turn off Claude Code's prompt. Unchanged from the earlier review, and walked in `quickstart.md` step 8.
- Claude Code's `ask` rule matches every command the raw-text prefix check passes. Leading whitespace is still the one normalization nobody has checked (PR-021).
- The repository lookup is cheap and bounded. It calls git, and the plan doesn't give it the gate's timeout (PR-008).
- #407 merges first. Stated in `plan.md §Summary`.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- The `doctor` change was made in the spec, where the cause was, so the plan's reuse of #407's path now meets FR-004 and SC-003 as written.
- The FR-017 paragraph says how the re-accept interacts with a redraw and with the dry run, which are the two cases an implementer would otherwise guess.
- The pass check refuses on any operator character, and on a comment `shlex` reads differently from the plain split, so a form the guard can't read fails closed.
- `read(command, cwd=None, payload=None)` and `refusal(command, cwd, payload=None)` keep today's behavior for every caller that passes no payload.
- The walk's sign-offs and import approval stay off the feature branch.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
