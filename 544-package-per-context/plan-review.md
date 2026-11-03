# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 093b12ca362a6366c8689a6818c6fb685050296e | technical strategy |
| spec.md | fc5b1b331bdf85e67cf3c044810d29ffdf0bc8a2 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | 4ec1a176dddf9c8559af96bc8a3b7bafbcb43fff | design-record index |
| docs/architecture/contexts-are-packages.md | 0d88f1de34373a012ff4c913aaf4c73c67ab925e | accepted level-2 record |
| docs/architecture/domain/wfctl.md | e8364d902f83f1bebc79d8d55e103d1bc2d2b441 | domain page the check reads |
| research.md | fec00fa13992b9d6dc7745f674b3d2a01c6e442f | planning evidence |
| data-model.md | fc1ed1480fafc43139d0ba212f422ddc7b03c66b | planning evidence |
| quickstart.md | 8f200a771c4227e7dba0481d00b08ebcde60f2fe | planning evidence |
| contracts/baseline.md | 61471aa12f66b721f4d7505e62bed6bce3e9327e | contract |
| contracts/failure-output.md | 3fe11b41764fe2a40e96a11c3dff84f9215a45fe | contract |
| checklists/requirements.md | ca7200ba81541e45366a10151368381417d90d32 | requirements checklist |
| checklists/analysis-report.md | b3cc03a189181a50c0bd49813e6cb0907520b07e | analysis report, read for what changed |
| exceptions/architecture-records/brainstorm.software-design.md | 1899c8677c81446cb9527810b27b2c6f75ad9613 | design exception |
| plan-walkthrough.md | e20d1eba2965f05fb46faece1c49bb9fb33663a3 | walkthrough record |
| tests/test_review_workflow.py | a6d5264c9b6ab7173753fb6efa2974158cea5b82 | existing code a changed item relies on |
| .github/workflows/review.yml | a06f9be1d38aeeabd4b7825744137a9c3be45ebb | existing code a changed item relies on |
| plan-review.plan.md | 9426017ebf75890336e4526d89921639e2f5a7c7 | base of this re-review |

## Review scope

- Re-review: the earlier report and the plan copy both exist, and the copy's
  identity equals the earlier report's `plan.md` row.
- Changed since the earlier report, in `plan.md`: Phase B item 4.1, where the
  strict map reader now skips a blank line and strips backticks from a Package
  cell. Phase D item 13 and Project Structure, where
  `tests/test_review_workflow.py` gains tests for the new `lint` and `review`
  steps. The diff was reviewed with the sections that refer to it: Phase A
  item 1, which parses the shared packages table "the same way"; Phase C items
  6.2 and 6.3.4, where the merge base's page goes through the same reader and
  a Package cell change is an addition; Phase D items 11 and 12, the two steps
  the new tests cover; research R2; and `data-model.md §Domain`.
- Changed since the earlier report, outside `plan.md`: `spec.md`. The identity
  comparison found it. The analysis report (`checklists/analysis-report.md`,
  finding B1) says the edit is to SC-002, which now says "each refused case"
  instead of "each of the five refused cases", and "the contexts involved"
  instead of "both contexts". No copy of the earlier `spec.md` exists to diff,
  so `spec.md` was re-read in full and the whole of `plan.md` was reviewed
  against it. Every other row matches the earlier report.
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification.
- Conditional lenses: security and reliability applied. Item 13's new tests
  cover the `review` job, which runs under `pull_request_target` with the base
  repository's token, and an existing test in the same file limits what that
  job may run from the PR's checkout.
- Design records: none at level 3. `design.md § Software design decisions`
  records none. The level-2 record `contexts-are-packages.md` governs.
- Constitution: `.specify/memory/constitution.md` is absent. The plan says so in
  its Constitution Check.
- Unresolved markers: no `[NEEDS CLARIFICATION` marker, TODO, or TBD in
  `spec.md` or `plan.md`.
- Existing code inspected: `docs/architecture/domain/wfctl.md`, where the
  Context Map block has a blank line between its nodes and its edges, every
  node and edge line is indented four spaces, and every Package cell is in
  backticks. `tests/test_review_workflow.py`, for what the existing tests
  assert about the `review` job's steps. `.github/workflows/review.yml`, for
  which step sets `working-directory: pr`.
- Reviewers: the four lenses above, run in sequence by one agent.

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 1

No BLOCKER findings identified in this review. Every earlier finding stays
fixed, and none was open before this run. Both edits to item 4.1 match the real
domain page and research R2. The SC-002 edit narrows wording the plan never
quoted, and item 13's test per acceptance scenario still covers it. One new
MINOR finding, PR-042: an existing test refuses any `review` step that sets
`working-directory: pr` other than the reviews check, and the plan's new step
runs the script in `pr` without saying how it gets there.

## Findings

### PR-001: The suite's real-tree test can't run the same check without an approval

- Priority: MAJOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `spec.md §FR-013` and `plan.md §Phase D items 10 and 13`.
- Finding: Unchanged, and still fixed.
- Why it matters: The suite and `verify` can be green before any approval.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-002: The CI step's git environment and its failure mode are unstated

- Priority: MAJOR
- Category: Dependency / Feasibility
- Status: fixed
- Evidence:
  - `plan.md §Phase C item 6` and `§Phase D item 12`.
- Finding: Still fixed.
- Why it matters: A short history can't turn the approval check off.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-003: The domain page on `main` can't be read by the strict reader

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Phase C item 6.2` and `data-model.md §Domain`.
- Finding: Still fixed.
- Why it matters: The comparison doesn't depend on a guess about the older
  page.
- Suggested response: Fixed.
- Corroborated by: deterministic checks

### PR-004: A pull request can edit the CI step that runs `main`'s copy

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Phase D item 12` and `§Phase C item 6.3.5.2`.
- Finding: Still fixed.
- Why it matters: One workflow edit no longer turns a check green.
- Suggested response: Fixed.
- Corroborated by: security and reliability

### PR-005: Running `main`'s copy can hold a branch whose fix is in the script

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Phase E item 14.1` and `research.md §R11 Limit`.
- Finding: Still fixed.
- Why it matters: A move under #671 that needs a script fix has a way through.
- Suggested response: Fixed.
- Corroborated by: security and reliability

### PR-006: A branch can add a shared package without anyone's approval

- Priority: MAJOR
- Category: Boundary / Ownership Concern
- Status: fixed
- Evidence:
  - `spec.md §FR-015` and `plan.md §Phase C item 6.3.3`.
- Finding: Still fixed.
- Why it matters: A new shared package waits for a person.
- Suggested response: Fixed.
- Corroborated by: architecture and boundaries

### PR-007: How `approve-imports` reaches the script, and whose code it runs, is unstated

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Phase C item 8.4`.
- Finding: Still fixed.
- Why it matters: The person doesn't run the branch's copy of the script.
- Suggested response: Fixed.
- Corroborated by: security and reliability

### PR-008: The failed `lint` job isn't rerun after the approval

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Phase C item 7`.
- Finding: Still fixed.
- Why it matters: The check goes green after the approval.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-009: Rule 1 allows every wiring import before rule 6 can refuse one

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Phase B item 4.5`.
- Finding: Still fixed.
- Why it matters: US2 scenario 3 is testable.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-010: `wfctl/__init__.py` has no placement, and the count is off by one

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Phase B item 4.3.4` and `research.md §R7`.
- Finding: Still fixed.
- Why it matters: SC-001 can pass on the shipped baseline.
- Suggested response: Fixed.
- Corroborated by: deterministic checks

### PR-011: Importing a private module through the package's name isn't covered

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Phase B item 4.4`.
- Finding: Still fixed.
- Why it matters: Rule 3 of the record can't be passed by that spelling.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-012: `_entry.py` as wiring extends FR-006 and the record without a spec change

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-006` and `contexts-are-packages.md §Decision rule 5`.
- Finding: Still fixed.
- Why it matters: A reader of either finds both wiring files.
- Suggested response: Fixed.
- Corroborated by: architecture and boundaries

### PR-013: FR-011 points at drawings in `design.md` that predate the amended record

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-011` and `plan.md §Phase B item 4.8`.
- Finding: Still fixed.
- Why it matters: The output follows the contract.
- Suggested response: Fixed.
- Corroborated by: deterministic checks

### PR-014: Phase A's description of the Shared packages table and the vocabulary row disagree with the spec

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Phase A items 1 and 2`.
- Finding: Still fixed.
- Why it matters: The parser and the page agree.
- Suggested response: Fixed.
- Corroborated by: deterministic checks

### PR-015: The release note category understates what ships

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `research.md §R9` and `plan.md §Phase E item 15`.
- Finding: Still fixed.
- Why it matters: The release notes show the new command.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-016: This branch's own additions get no approval the spec or the record recognizes

- Priority: MAJOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `spec.md §FR-015`, `contexts-are-packages.md §Log`, and `plan.md §Phase D`,
    closing paragraphs.
- Finding: Still fixed.
- Why it matters: A task written from FR-015 doesn't assert behaviour this
  branch can't have.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability, security and reliability

### PR-017: For a stacked PR the base branch isn't `main`, and the two digests disagree

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Phase D item 12`, `§Phase C item 8.3`, and `research.md §R5`.
- Finding: Still fixed.
- Why it matters: A person's approval of a stacked PR matches CI's digest.
- Suggested response: Fixed.
- Corroborated by: security and reliability, adversarial implementation

### PR-018: The context-to-package mapping can change with no approval

- Priority: MAJOR
- Category: Boundary / Ownership Concern
- Status: fixed
- Evidence:
  - `spec.md §FR-015` and `plan.md §Phase C item 6.3.4`.
- Finding: Still fixed.
- Why it matters: A module's context can't change without moving the file.
- Suggested response: Fixed.
- Corroborated by: architecture and boundaries, security and reliability

### PR-019: The "no copy on `main`" pass outlives the bootstrap

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Phase D item 12`, closing paragraph.
- Finding: Still fixed.
- Why it matters: Deleting the script doesn't turn the check off.
- Suggested response: Fixed.
- Corroborated by: security and reliability

### PR-020: The rule check in the `review` job follows symlinks in the PR checkout

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Phase B item 4.10` and `§Phase D item 13`.
- Finding: Still fixed.
- Why it matters: Nothing outside the checkout reaches the public log.
- Suggested response: Fixed.
- Corroborated by: security and reliability

### PR-021: The plan still says a rule fix lands with the change that needs it

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Summary item 1`, `§Complexity Tracking`, `§Phase E item 14.1`.
- Finding: Still fixed.
- Why it matters: A task writer plans the #671 PRs correctly.
- Suggested response: Fixed.
- Corroborated by: deterministic checks

### PR-022: Where the rule check finds the tree is unstated, and the `review` step depends on it

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Phase B item 4.9` and `§Phase D item 13`.
- Finding: Still fixed.
- Why it matters: The `review` job can't silently check the wrong tree.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-023: Rule 1's "moved package" leaves the shared packages' internals open

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Phase B item 4.5 rule 1`.
- Finding: Still fixed.
- Why it matters: The first move of `core` doesn't pick an answer by accident.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-024: The script is an input nobody approves, and only one of its lists is gated

- Priority: MAJOR
- Category: Boundary / Ownership Concern
- Status: fixed
- Evidence:
  - `plan.md §Phase C item 6.3.5.1`.
- Finding: Still fixed. The script is still on `TRUSTED`, which it holds.
- Why it matters: The script can't be loosened through a PR that changes no
  imports.
- Suggested response: Fixed.
- Corroborated by: architecture and boundaries, security and reliability

### PR-025: The bootstrap pass never runs on this branch, and its detection is unstated

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Phase D item 12` and its closing paragraphs.
- Finding: Still fixed.
- Why it matters: The step's behaviour on a missing script is one answer.
- Suggested response: Fixed.
- Corroborated by: security and reliability, deterministic checks

### PR-026: Where the trusted script's temporary copy is written is unstated

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Phase D item 12.2 and 12.3` and `§Phase C item 8.4`.
- Finding: Still fixed.
- Why it matters: The CI step can't run branch code through an import.
- Suggested response: Fixed.
- Corroborated by: security and reliability

### PR-027: The person's local base can still differ from CI's

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §Phase C item 8.3` and `research.md §R5`.
- Finding: Still fixed.
- Why it matters: An approval matches CI's digest when both sides see the same
  commits.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-028: Research R4 says `approve-imports` exits 0 where the plan says 1

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `research.md §R4 Limit` and `plan.md §Phase C item 8.6`.
- Finding: Still fixed.
- Why it matters: A test written from R4 asserts the right code.
- Suggested response: Fixed.
- Corroborated by: deterministic checks

### PR-029: The record's Decision and title lag the spec

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `contexts-are-packages.md` title and `§Decision` approval list.
- Finding: Still fixed. Item 5 now names the script and the workflow, matching
  FR-015.
- Why it matters: `wfctl arch context` projects the rule as enforced.
- Suggested response: Fixed.
- Corroborated by: architecture and boundaries

### PR-030: The separate-PR route PR-024 closed for the script still reaches the workflow that runs it

- Priority: MAJOR
- Category: Boundary / Ownership Concern
- Status: fixed
- Evidence:
  - `plan.md §Phase C item 6.3.5.2`: `review.yml` stays on `TRUSTED`.
- Finding: Still fixed. The guard and notes modules left the list by decision,
  and the limit covers them (PR-034).
- Why it matters: The workflow can't be loosened without a person.
- Suggested response: Fixed.
- Corroborated by: architecture and boundaries, security and reliability

### PR-031: `approve-imports` itself is branch code when run the way this repo runs wfctl

- Priority: MAJOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §Phase C item 8.1`, `§Phase E item 14`, and
    `contracts/failure-output.md`: the person runs the installed `wfctl`.
- Finding: Still fixed.
- Why it matters: The person approves from code the branch didn't write.
- Suggested response: Fixed.
- Corroborated by: security and reliability, adversarial implementation

### PR-032: A script change reaches the approver as a hash

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Phase C item 8.5`.
- Finding: Still fixed.
- Why it matters: The person reads the change they approve.
- Suggested response: Fixed.
- Corroborated by: security and reliability

### PR-033: The approval is computed from local `HEAD`, and nothing checks it is the PR's head

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §Phase C item 8.2`.
- Finding: Still fixed.
- Why it matters: An approval doesn't sit on a commit CI never reads.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-034: The `TRUSTED` list misses the files that decide whether the guard runs at all

- Priority: MAJOR
- Category: Boundary / Ownership Concern
- Status: fixed
- Evidence:
  - `plan.md §Phase C item 6.3.5`, last paragraph: "The worktree guard, the
    hook that installs it, and the approval command are wfctl code an agent
    can edit ... They don't stop an agent set on getting around them, for
    example ... by merging a PR that weakens the guard."
  - `spec.md §FR-015`, `research.md §R11 Limit`, and
    `contexts-are-packages.md §Decision`, the paragraph after item 5: the same
    limit.
- Finding: The list no longer claims to cover the guard, so `_entry.py`,
  `_settings.py`, and the guard's imports aren't gaps in it. They sit inside a
  limit that names both the guard and the hook that installs it, and names a
  PR that weakens the guard as one way around it.
- Why it matters: A reader of any of the four sources gets the same boundary.
- Suggested response: Fixed.
- Corroborated by: architecture and boundaries, security and reliability

### PR-035: Leaving `cli.py` off contradicts FR-015, and the limit understates what `cli.py` holds

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-015`: "any change to the two files CI runs the check with",
    and the local refusals stated as weaker.
  - `plan.md §Phase C item 6.3.5`: the "only dispatches" wording is gone, and
    the approval command is inside the limit.
  - `plan.md §Phase C item 7`: `run_approve_imports` carries the terminal
    check, and `approve_imports` repeats it.
- Finding: FR-015 and the plan now say the same thing about which files are
  gated, so a task written from either gates the same two. The terminal
  check's home is stated.
- Why it matters: The spec and the plan no longer give a task writer two
  answers.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability, architecture and boundaries

### PR-036: An agent's own Python process can write the approval, and the guard never sees it

- Priority: MAJOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §Phase C item 9`: "Neither refusal sees an agent that calls the
    approval function from its own Python."
  - `plan.md §Phase C item 7`: the terminal check in `approve_imports`
    "narrows the gap item 6.3.5 states, and doesn't close it".
  - `spec.md §FR-015` and `contexts-are-packages.md §Decision` name the same
    case.
- Finding: The plan no longer claims the route is closed, and every source
  names it as the limit's example. PR-041 covers four other sentences that
  still claim more.
- Why it matters: The limit is stated where an implementer reads the guard
  work.
- Suggested response: Fixed.
- Corroborated by: security and reliability, adversarial implementation

### PR-037: The worktree-source refusal is enforced by the code it distrusts

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §Phase C item 8.1`: resolved paths, and "This refusal catches an
    honest mistake only, since a tampered branch can delete it."
- Finding: The refusal is described as what it is, and the protection is
  named as running the installed `wfctl`.
- Why it matters: A reader doesn't take the refusal as the protection.
- Suggested response: Fixed.
- Corroborated by: security and reliability

### PR-038: The upstream refusal leaves two cases unstated

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Phase C item 8.2`: compares with `origin/<current branch>`, and
    refuses with "push first" when that ref doesn't exist.
- Finding: Both cases are now stated, and the configured upstream isn't used.
- Why it matters: The refusal gives the right advice on a branch tracking
  `origin/main`.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-039: The bootstrap exception names the baseline, and this branch also changes four trusted files

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-015`: "approves its baseline and its two trusted files by
    merging its PR by hand".
  - `plan.md §Phase D`, closing paragraph: the user reads both diffs before
    merging.
  - `contexts-are-packages.md §Log`: "the bootstrap exception covers both
    files".
- Finding: Under the narrowed list, this branch changes two trusted files,
  and the exception and the pre-merge check name both.
- Why it matters: The hand merge covers what the exception says it covers.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-040: A path-keyed `TRUSTED` list meets the #671 moves

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Phase C item 6.3.5`: a file absent at the merge base and present
    at `HEAD` is `changed`, and both paths sit under `.github/`.
  - `data-model.md §Domain`: the same.
- Finding: Neither trusted path moves under #671, and the missing case is
  defined.
- Why it matters: The moves need no script PR to keep the list current.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-041: Four sentences still claim more than the stated limit allows

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence (the first four bullets quote the earlier text):
  - `contracts/failure-output.md`, the block for an addition with no
    approval: "Whether to keep these is the user's decision, and an agent can't
    approve them."
  - `plan.md §Complexity Tracking`, second row: "FR-015 requires that an agent
    can't approve its own addition".
  - `plan.md §Constitution Check`, `review-record-in-git-notes`: "the guard's
    existing refusal of hand-written notes covers it".
  - `research.md §R4 Rationale`: the approval "reuses three protections", with
    no mention of the limit R11 now states.
  - `spec.md §FR-015` and `plan.md §Phase C item 6.3.5`: the local refusals
    "stop an agent from taking a shortcut, but not one set on getting around
    them".
  - Now: the contract says "only the user approves them"; the Complexity
    Tracking row says "FR-015 requires that only the user approves an
    addition. The command and the guard refuse an agent that runs the
    command, within the limit item 6.3.5 states"; the Constitution Check row
    ends "within the limit item 6.3.5 states"; R4 Rationale ends "Those
    protections refuse an agent that runs the command, not one that calls the
    approval code from its own Python. R11 and plan item 6.3.5 state that
    limit."
- Finding: All four sentences now match FR-015, R11 Limit, and plan items
  6.3.5, 7, and 9. A search of every input finds no other sentence saying an
  agent can't approve or that a refusal covers the approval outright.
- Why it matters: A task written from the contract or the Complexity Tracking
  row asserts the same guarantee the spec makes.
- Suggested response: Fixed.
- Corroborated by: deterministic checks, requirements and traceability

### PR-042: The existing workflow test refuses the new step if it runs with `working-directory: pr`

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `plan.md §Phase D item 12.3`: the step "runs that file with `python3 -I`
    in `pr`". Item 4.9 needs the current directory to be the PR's tree.
  - `plan.md §Phase D item 13`: `tests/test_review_workflow.py` "already
    checks that the `review` job runs nothing from `pr/`, and it gains tests"
    for the new step.
  - `tests/test_review_workflow.py`,
    `test_nothing_from_the_prs_checkout_is_executed`: every step with
    `working-directory: pr` must fully match
    `uv run --project ../trusted wfctl check reviews --base "$BASE_REF"`.
  - `.github/workflows/review.yml`: only the reviews check sets
    `working-directory: pr` today. Items 12.1 and 12.2 use `git -C pr`.
- Finding: The plan presents the existing test as compatible with the new
  step, but the test's allow-list rejects any `pr` step other than the reviews
  check. An implementer who sets `working-directory: pr` turns that test red
  and then has to widen a security test the plan never mentions. One who runs
  `cd pr` inside `run` passes the test, but its allow-list then no longer
  covers the new step. The plan picks neither.
- Why it matters: The test guards what the `review` job runs with the base
  repository's token. Widening it is a change a reviewer should see stated in
  the plan, not one an implementer makes to get a red test green.
- Suggested response: State in item 12.3 or item 13 how the step reaches `pr`.
  If it sets `working-directory: pr`, say that the existing test's allow-list
  gains exactly the `python3 -I "$RUNNER_TEMP/…"` command line, in both
  modes. If it uses `cd pr` inside `run`, say that a new test pins that
  command line.
- Corroborated by: adversarial implementation, security and reliability

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Phase B item 4.1, 4.5 rule 5 | covered |
| FR-002 | plan.md §Phase A item 1, §Phase B item 4.1 | covered |
| FR-003 | plan.md §Phase B item 4.5 rule 5 | covered |
| FR-004 | plan.md §Phase B item 4.4, 4.5 rule 6 | covered |
| FR-005 | plan.md §Phase B item 4.5 rules 3 and 4 | covered |
| FR-006 | plan.md §Phase B item 4.3.3, 4.5 rules 1 and 2 | covered |
| FR-007 | plan.md §Phase B item 4.3 | covered |
| FR-008 | plan.md §Phase B items 4.3.5 to 4.3.7 | covered |
| FR-009 | plan.md §Phase B item 4.7 | covered |
| FR-010 | plan.md §Phase B item 4.1, §Phase C item 6.2 | covered |
| FR-011 | plan.md §Phase B item 4.8, contracts/failure-output.md | covered |
| FR-012 | plan.md §Phase B item 4.6 | covered, on fixtures only |
| FR-013 | plan.md §Phase D items 10 - 13 | covered; PR-042 for item 13's workflow tests |
| FR-014 | plan.md §Phase B item 5, research.md §R7 | covered |
| FR-015 | plan.md §Phase C items 6 - 9, §Phase D item 12 and closing paragraphs | covered |
| SC-001 | plan.md §Phase B item 4.1, §Phase D item 13 | covered; item 4.1 now reads the real page |
| SC-002 | plan.md §Phase D item 13 | covered |
| SC-003 | plan.md §Technical Context | covered |
| SC-004 | plan.md §Phase B item 4.1 | covered |
| SC-005 | plan.md §Phase B item 5 | covered |

## Assumptions challenged

- Item 4.1 lists the node and edge forms without saying that leading
  whitespace is allowed, and every node and edge line on the real page is
  indented four spaces. The real-tree test (SC-001) fails at once on a reader
  that rejects the indent, so the gap can't ship silently. It isn't raised as
  a finding.
- Item 4.1 strips backticks from "a Package cell". Phase A item 1 says the
  shared packages table is parsed the same way as the contexts table, so the
  strip applies to both tables. Item 6.2 reads the merge base's page with the
  same reader, so a cell that only gains or loses backticks isn't a new
  context-to-package pair.
- SC-002 now says "the contexts involved". In `contracts/failure-output.md`,
  the unplaced-module block names no context, since the module has none, and
  the shared-package block names the imported module rather than its
  context's name. Both follow FR-011's wording, which the earlier reviews
  traced as covered, and the SC-002 edit brings the criterion in line with it.
- The revision notes at the end of `plan.md` carry no entry for the analyze
  edits. Read in order, the plan still agrees with itself, and nothing a task
  depends on is missing.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- `plan.md §Phase C item 6.3.5` draws the line where CI's enforcement ends and
  says plainly what lies past it, rather than widening a list that couldn't
  close.
- `plan.md §Phase B item 4.1` gives the reason for each of its two new
  allowances in terms of the real page, so a later reader can tell them from
  leniency.
- `plan.md §Phase D item 13` gives the `review` step a test before merge, which
  is the only check that step gets on this branch, since it doesn't run on
  this PR.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
