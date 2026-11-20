# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 62de2301c794d75619d74d24d1918fde5fbff75c | technical strategy |
| spec.md | 5e5fae30f33b570680fc5130e5326e1019b72fec | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | c4cd4077024eb83527a869bbe1bce498027d10d7 | design-record index |
| docs/architecture/design/prompted-spellings-one-table.md | fe7e80871ca3745c1109e62a0b919acf89424264 | design record (level 3, proposed) |
| docs/architecture/prompt-approves-person-commands.md | 123694382ea580f76b47491c2d96a6ebc3e41577 | level-2 record carrying the threat model |
| docs/architecture/accept-check-threat-model.md | f2e35654505027d1dda08b36026c994d0ceaeccb | superseded record whose items 1 - 20 the level-2 record keeps |
| docs/architecture/guard-catches-literal-accept.md | 01a32d319ab38e1432fc9514316c21b05e8dd7dc | superseded record the Records section reads |
| research.md | a545d35cda60953761971321c8a9116a6a4efbed | planning evidence |
| data-model.md | 838940e2f4920504bb9f9723c44342c98e272062 | planning evidence |
| contracts/cli.md | f9373865f7f3c04acc7a6f7fd6f26a9507813441 | planning evidence |
| quickstart.md | d0a34220c750e9c3e2679ae8a91ee5c414b3cc73 | planning evidence |
| plan-review.plan.md | 816fcaf422aaef20c51a08629c55960935a22979 | base of this re-review |

## Review scope

- Re-review: the earlier report and the plan copy both existed, and the copy's identity matched the earlier report's `plan.md` row.
- Changed in `plan.md`: §Technical Context (the cost line), §The table (the export list), §The guard (pass check items 2 and 3, the reason-dependent first line, `read()`'s signature), §The commands (`prompted_host`'s reading of `CLAUDECODE`, the change list for `check-accept`), and §Tests item 1. Reviewed together with §Summary, §Source Code, and the requirement trace, which refer to the changed sections.
- Inputs changed since the earlier report: `docs/architecture/design/prompted-spellings-one-table.md` (amended for PR-014), `contracts/cli.md`, `quickstart.md`, `research.md`, and `data-model.md`. Each was re-read in full, and the whole of `plan.md` was reviewed against it. `spec.md`, `design.md`, and the three other records match their earlier rows.
- Lenses: requirements and traceability, architecture and boundaries, adversarial implementation and verification.
- Conditional lenses: security and reliability applied, since the feature loosens a security control (the worktree guard and the terminal checks on three person-only commands).
- Existing code inspected: `wfctl/_review_gate.py` (`refusal`, `read`, the three refusal constants, `_SIGN_OFF`, `_APPROVE_IMPORTS`, `_ACCEPT`, `_accepts`), `wfctl/guard/_hook.py` (the prefilter, the `refusal` call with `payload.get("cwd")`, the exception path that refuses), `wfctl/_review_notes.py` (`_at_terminal`, `approve_imports`, `_inside_a_worktree`, `_branch_matches_origin`, `run_approve_imports`), `wfctl/_paths.py` (`resolve_branch`, `resolve_agent_dir`, which call git), `wfctl/_evidence.py` (the dry-run fix line), and the files under `wfctl/agents/` that name the dry run.
- Reviewers: the four lenses above, run in sequence by one agent in a fresh context.

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 4

No BLOCKER findings identified in this review.

Seven of the ten findings the earlier report left open are fixed, including the BLOCKER (PR-014): the level-3 record now decides the raw-text comparison and two file reads, matching `plan.md §The guard`. The MAJOR finding on the walk's sign-off (PR-015) is fixed by a throwaway branch. Three MINOR findings stay open in narrowed form: the git calls the pass check makes (PR-008), the data model's Log table (PR-016), and the "not plain" reason line (PR-017). One new MINOR finding asks whether stripping leading whitespace before the prefix match agrees with Claude Code's rule (PR-021).

## Findings

### PR-001: The shlex-based match lets quoted and backslashed spellings through

- Priority: BLOCKER
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `plan.md §The guard` pass check items 1 - 3: a literal, case-sensitive prefix on the raw text, with no `$`, backtick, `\`, `;`, `&`, `|`, `<`, `>`, `(`, `)`, or newline, and no unquoted comment.
  - `prompt-approves-person-commands.md §Must keep catching` items 11 and 12: neither matches the prefix.
- Finding: Fixed in the earlier review, and the record now agrees (PR-014).
- Why it matters: The forms the record lists as refused stay refused.
- Suggested response: None.
- Corroborated by: requirements and traceability, security and reliability

### PR-002: The guard keeps refusing the search for the sign-off command

- Priority: BLOCKER
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §The guard`, "Sign-off and approve-imports get the accept's reader": one reader takes each command's words, and the two loose regexes go.
- Finding: Fixed in the earlier review. Unchanged.
- Why it matters: FR-009 and SC-002 can be met as planned.
- Suggested response: None.
- Corroborated by: requirements and traceability, adversarial implementation

### PR-003: The walk in Claude Code runs the installed wfctl, not the branch

- Priority: MAJOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `quickstart.md` steps 0 and 12, `plan.md §Validation`.
- Finding: Fixed in the earlier review. Unchanged.
- Why it matters: The walk exercises the branch's guard and commands.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-004: Every child process inherits `CLAUDECODE`, including agents that run no guard

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §The commands`, second paragraph.
- Finding: Fixed in the earlier review. Unchanged.
- Why it matters: The residual risk is named for the user to confirm.
- Suggested response: None.
- Corroborated by: security and reliability, adversarial implementation

### PR-005: The superseded record's items 1 - 20 lose their tests, and two of them have no settled answer

- Priority: MAJOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Tests` item 1.
- Finding: Fixed in the earlier review. Unchanged, and extended by the PR-019 and PR-020 additions to the same item.
- Why it matters: A regression on items 3 - 20 fails the suite.
- Suggested response: None.
- Corroborated by: requirements and traceability, adversarial implementation

### PR-006: The suite's terminal-refusal tests change behavior inside Claude Code

- Priority: MAJOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Tests` item 6.
- Finding: Fixed in the earlier review. Unchanged.
- Why it matters: Results don't depend on the shell running the suite.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-007: The dry-run prompt stalls unattended runs

- Priority: MAJOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §The commands` item 2, `research.md §R-003`, `contracts/cli.md §wfctl arch check-accept`.
- Finding: Fixed in the earlier review, and `research.md` now agrees.
- Why it matters: An unattended brainstorm doesn't stop at a prompt nobody answers.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-008: The pass check's inputs and costs don't fit `read()`

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `plan.md §The guard`: `read(command)` becomes `read(command, cwd=None, payload=None)`, and the 66 text-only calls in `tests/test_review_gate.py` keep working through the defaults. That part is fixed.
  - `plan.md §Technical Context` and `§The guard` now agree on "two small file reads".
  - `plan.md §The guard` item 6 and `research.md §R-004`: `agent_dir` is resolved from the payload's `cwd`. `wfctl/_paths.py` `resolve_branch` and `resolve_agent_dir` each run git subprocesses, and `resolve_branch` takes an optional `timeout` that the plan doesn't set. `_review_gate.TIMEOUT` (5 s) bounds the gate's other git calls.
- Finding: The signature is settled. The cost statement still leaves out the git calls the agent-dir lookup makes, and the plan doesn't say they get the gate's timeout.
- Why it matters: Small. A git call with no bound in a hook the host kills on its own timeout exits without code 2, and `_review_gate.py:42` notes the command then runs. The failure path is the one the pass check is meant to close.
- Suggested response: Say the agent-dir lookup runs under `TIMEOUT`, and count its git calls in the cost line.
- Corroborated by: single reviewer

### PR-009: The host check's name and export disagree across the plan

- Priority: MINOR
- Category: Boundary / Ownership Concern
- Status: fixed
- Evidence:
  - `plan.md §The table` now lists `prompted_host() -> bool` among the exports, matching `§Source Code`.
  - `plan.md §The commands` and `research.md §R-001`: `CLAUDECODE` counts when set to a non-blank value.
- Finding: Fixed.
- Why it matters: A test for FR-011 has one reading to follow.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-010: The refusal wording differs between the plan and the contract

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §The guard` and `contracts/cli.md §Worktree guard refusals` give the same four reasons in the same order.
- Finding: Fixed in the earlier review. Unchanged.
- Why it matters: Tests and skills quote one text.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-011: Two `--agreed` cases have no behavior

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §The commands` item 1 and `contracts/cli.md §wfctl arch accept`.
- Finding: Fixed in the earlier review. PR-016 tracks the data model's table.
- Why it matters: Both Log lines have a stated form.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-012: The Log-line claim is loosely defined and departs from the accepted record

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `plan.md §Records`.
- Finding: Fixed in the earlier review. Unchanged.
- Why it matters: The reading clears only the intended warning.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-013: Some negative paths in the spec have no test or walk step

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `quickstart.md` step 7a: with Claude Code in auto mode, the agent accepts a fresh throwaway record, and the walk confirms the prompt still appears.
  - `plan.md §Tests` item 7 and `quickstart.md` step 6 cover the other two parts, as before.
- Finding: Fixed. The mode the user runs in day to day is now walked.
- Why it matters: An auto mode that skips `ask` rules would show up in the walk rather than in use.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-014: The level-3 design record still decides the split-word match the threat model refuses

- Priority: BLOCKER
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `prompted-spellings-one-table.md §Decision` item 2 now reads: the raw text starts with one entry's words joined by single spaces, compared literally and case-sensitively, with no separator, substitution, redirect, quote-stripping backslash, or unquoted comment, and says why split words would let `wfctl "arch" accept s` through.
  - `prompted-spellings-one-table.md §Consequences` now says two small file reads, matching `plan.md §Technical Context` and `§The guard`.
  - The record's Log carries an `amended` line naming this finding.
- Finding: Fixed. The plan and the listed design record now agree on the pass rule and its cost, and both agree with `prompt-approves-person-commands.md §Must keep catching` item 11.
- Why it matters: The user can accept the record without recording a mechanism the threat model refuses.
- Suggested response: None.
- Corroborated by: architecture and boundaries, security and reliability

### PR-015: The walk's sign-off signs off the implementation's own commits

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `quickstart.md` step 6: the sign-off runs "on a throwaway branch cut from `main` with one empty commit, never the feature branch", and says why. The branch and its note are deleted afterwards.
  - `quickstart.md` step 7: the import approval runs on the same throwaway branch.
- Finding: Fixed. The sign-off and the import approval note land on a commit the feature branch doesn't contain, so neither covers the implementation.
- Why it matters: The review panel still has to run on this branch.
- Suggested response: None.
- Corroborated by: adversarial implementation, security and reliability

### PR-016: Planning artifacts still describe what the revision replaced

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - Fixed parts: `data-model.md §Prompted` now gives the raw-text match, `research.md §R-003` decides `check-accept`, `research.md §R-006` names `prompted_host()`, and `plan.md §The commands` item 2 now lists the brainstorm command wrapper and its grant, `drawing-style.md`, and the refusal texts in `_review_gate.py` and `cli.py`.
  - Still open: `data-model.md §Accept Log line` has no row for a blank `--agreed ""` and none for a redraw, which `plan.md §The commands` item 1 and `contracts/cli.md §wfctl arch accept` both define.
- Finding: One table in the data model still lags the plan and the contract.
- Why it matters: Small. Tasks generated from the data model's table would miss two cases the contract names, though the contract states them.
- Suggested response: Add the blank-citation and redraw rows to `data-model.md §Accept Log line`.
- Corroborated by: single reviewer

### PR-017: The kept refusal headline contradicts the new reason line

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - Fixed part: `plan.md §The guard` and `contracts/cli.md §Worktree guard refusals` now give the rule-missing and not-plain cases the first line "needs your approval at Claude Code's prompt", so no refusal says "not an agent" and then says to rerun.
  - Still open: `plan.md §The guard` item 2 says "the refusal lists the characters to remove from the command", which reads as the characters found. `contracts/cli.md` reason 4 prints a fixed example list, "such as $ ; & | < > ( ) or a backslash or backtick", which leaves out the newline from item 2 and the unquoted comment from item 3.
- Finding: The headline contradiction is fixed. The plan and the contract still describe the not-plain reason line differently, and the contract's text gives an agent refused for a newline or an unquoted `#` nothing to act on.
- Why it matters: Small. Tests quote this text, and an agent that can't see what to change spends a round guessing.
- Suggested response: Pick one: print the characters found, or print the full list from items 2 and 3, including the newline and an unquoted `#`. Make the plan and the contract say the same.
- Corroborated by: single reviewer

### PR-018: The repository's own citation form is refused

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §The guard` item 2 no longer forbids `#`. Item 3 refuses only when `shlex.split(text, comments=True)` and `shlex.split(text)` give different words, so `--agreed "agreed on #833"` passes and `wfctl arch accept s # x` doesn't.
  - Checked: `shlex` with comments on treats a `#` inside an unquoted word as a comment, where bash doesn't, so `--agreed a#b` is refused. That fails closed, and any comment bash would read also changes `shlex`'s words, so none passes.
- Finding: Fixed.
- Why it matters: An issue reference, the usual citation here, can be passed.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-019: The plan decides how items 16 and 19 of the old list are read

- Priority: MINOR
- Category: Boundary / Ownership Concern
- Status: fixed
- Evidence:
  - `plan.md §Tests` item 1: the reading of items 16 and 19 is the user's to confirm, and the PR body names it.
- Finding: Fixed. The reading goes to the user, as `prompt-approves-person-commands.md §Owns truth` requires.
- Why it matters: The user sees what counts as a regression before the change lands.
- Suggested response: None.
- Corroborated by: requirements and traceability, security and reliability

### PR-020: The generalized reader's coverage for sign-off and approve-imports has no test

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Tests` item 1: each of items 1 - 20 runs again with the accept's words replaced by sign-off's and approve-imports', where the item has a meaning for them, and `_runs_person_command` takes the words as a parameter at every site that names `arch` and `accept` today.
- Finding: Fixed. A site left hard-coded to the accept now fails a test.
- Why it matters: The deleted regexes' coverage is replaced by tests, not by assumption.
- Suggested response: None.
- Corroborated by: adversarial implementation

### PR-021: Stripping leading whitespace assumes Claude Code's rule matches the stripped form

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `plan.md §The guard` item 1: "The raw command, with leading and trailing whitespace removed, starts with one `PROMPTED` entry's words", and "That is the form Claude Code's rule matches too."
  - `prompted-spellings-one-table.md §Assumed`: the only stated assumption about the rule is that `:*` matches the start of the command, confirmed by a walk. `quickstart.md` has no step with leading whitespace.
  - `prompt-approves-person-commands.md §Threat model`: the guard's job is to refuse every form the host's rule wouldn't match, since that form runs with no prompt.
- Finding: Trailing whitespace can't change a prefix match. Leading whitespace can, and nothing in the artifacts shows Claude Code trims it before matching `Bash(wfctl arch accept:*)`. If it doesn't, ` wfctl arch accept s` passes the guard and runs with no prompt.
- Why it matters: The failure direction is the one the threat model exists to close, though an agent that isn't hiding what it runs rarely writes a leading space.
- Suggested response: Strip only trailing whitespace, so a leading space fails closed. Or keep the strip and add a quickstart step that runs a leading-space accept and records whether the prompt appears.
- Corroborated by: security and reliability, adversarial implementation

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §The table | covered |
| FR-002 | plan.md §Rules | covered, through #407's `_ManagedRule` |
| FR-003 | plan.md §Rules, §Tests item 3 | covered |
| FR-004 | plan.md §Rules, §Tests item 3 | covered |
| FR-005 | plan.md §The guard, pass check items 1 - 3 | covered; PR-021 |
| FR-006 | plan.md §The guard, pass check item 6 | covered; PR-008 |
| FR-007 | plan.md §The guard, pass check item 4 | covered |
| FR-008 | plan.md §The guard, pass check item 5 | covered |
| FR-009 | plan.md §The guard, §Tests items 1, 2, 5 | covered |
| FR-010 | plan.md §The guard, contracts/cli.md | covered; PR-017 |
| FR-011 | plan.md §The commands, §Tests items 4, 6, 7 | covered |
| FR-012 | plan.md §The commands items 3 - 4 | covered |
| FR-013 | plan.md §The commands item 1 | covered; PR-016 |
| FR-014 | plan.md §The commands item 4 | covered |
| FR-015 | plan.md §Records | covered |
| SC-001 | plan.md §Validation, quickstart.md | covered |
| SC-002 | plan.md §Tests items 1 - 2 | covered |
| SC-003 | plan.md §Tests items 2 - 3 | covered |
| SC-004 | plan.md §The commands item 1 | covered |

## Assumptions challenged

- Claude Code's `ask` rule matches every command the raw-text prefix check passes. True for forms with no quoting tricks or operators, which the check requires. Leading whitespace is the one normalization the plan makes that nobody has checked against the rule (PR-021).
- An `ask` rule prompts in Claude Code's auto mode. Now walked in `quickstart.md` step 7a.
- `CLAUDECODE` identifies a shell Claude Code started. True of its children too, which the plan names (PR-004).
- The agent-dir lookup is cheap and bounded. It calls git, and the plan doesn't give it the gate's timeout (PR-008).
- #407 merges first. Stated in `plan.md §Summary`.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- The pass check refuses on any operator character, and on a comment `shlex` reads differently from the plain split, so a form the guard can't read fails closed.
- An unresolvable agent dir, a malformed settings file, a missing `tool_name`, and an exception in the gate all refuse.
- `read(command, cwd=None, payload=None)` and `refusal(command, cwd, payload=None)` keep today's behavior for every caller that passes no payload.
- The reason-dependent first line keeps "for a person to run in their own terminal" only where an agent can't run the command at all.
- The walk's sign-off and import approval stay off the feature branch.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
