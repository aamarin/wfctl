# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 8025c87f2e938ce2c1e9621d78175cc6d4762e42 | technical strategy |
| spec.md | e74eeb74c39372770956a48f0480040ebca61f86 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | 9147b9f95680548479042075fa4a61dff18dd8da | design-record index |
| docs/architecture/design/799-threat-model-in-the-record.md | 6d9c979ad7fad08f9ef5a903e21e024837e3b93d | design record |
| docs/architecture/security-change-needs-threat-model.md | 7cbe2d2d9099bd2d12319f074b1dd2855cec0362 | level-2 record the plan cites |
| docs/architecture/accept-check-threat-model.md | fccb089598778a7ed79a30f86b40ea1eb95afa76 | level-2 record the plan cites |
| research.md | 16d6346e97222ced454407b0b4d339b65ed2d4c1 | planning evidence |
| data-model.md | 85ddb31f68d413828b56e3a0f83eacaa71623ebc | planning evidence |
| quickstart.md | 190a709581198e245c009b93f8e75ed5cdff3fd6 | planning evidence |
| contracts/threat-model-section.md | 93be7d8cc51969c22f7aa5f77e86fe5844061542 | contract |
| tasks.md | ddb6ab026dbb93b96fef51b79ca0eee9b7d7f80c | read to see how earlier findings were carried; not a review input |
| plan-review.plan.md | 87869267c008b3e1aaa35a4824db3396be9f6a22 | base of this re-review |

## Review scope

- Re-review: the earlier report exists, the plan copy exists, and the copy's
  identity equals the earlier report's `plan.md` row
- Changed since the earlier report: `plan.md §Structure Decision` (the heading
  test reads the bundle through `files("wfctl")`), reviewed together with
  `plan.md §Source Code` (the two test files) and `contracts/threat-model-section.md`
  (the heading test's rename cases)
- Inputs that no longer match the earlier report: `spec.md`, which gained
  FR-013. Re-read in full, and the whole of `plan.md` reviewed against it.
  Every other earlier row matches its file now.
- `tasks.md` is new. It was read to see how PR-001 to PR-007 were carried. It
  changes no finding's status, since a finding is fixed only by the plan or its
  inputs.
- No `[NEEDS CLARIFICATION` marker in `spec.md`
- Design records: 1 listed in design.md
  `docs/architecture/design/799-threat-model-in-the-record.md`, plus the two
  level-2 records the plan cites
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification
- Conditional lenses: security and reliability applied, since the feature
  changes how the security reviewers decide what counts as a finding against
  the guard's accept check, which keeps an irreversible action with a person
- Existing code inspected: none beyond the earlier review; the earlier probe's
  results stand, since neither the record nor the worktree head (`29b7135`)
  changed
- Reviewers: the four lenses above, run in sequence by one agent

## Summary

BLOCKER: 0
MAJOR: 2
MINOR: 5

No BLOCKER findings identified in this review. PR-001 is fixed: FR-013 now
says the reviewer judges an accepted threat model against the trunk's lists.
The plan doesn't carry FR-013, though, and research R-002 still describes the
reviewer reading at the head only, which is the new MAJOR finding PR-008.
PR-002 remains the other MAJOR. The plan's reworded Structure Decision answers
part of PR-006; the rest of PR-006 and the other MINOR findings are unchanged,
since the files that hold them didn't change. `tasks.md` carries every finding,
which is why the gaps are narrow, but the plan and research still say what they
said.

## Findings

### PR-001: The reviewer reads the bar at the head, where the change under review can move it

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `spec.md §FR-013`: when the branch changes the lists of a threat model accepted on the trunk, `reviewing-security` judges against the trunk's lists and reports any form moved out of "Must keep catching" or into "Accepts" as a finding
  - `research.md §R-002`: unchanged, still reads at `<head>` only (carried as PR-008)
- Finding: The earlier review found no artifact saying what the reviewer does
  when the branch edits an accepted record's lists. The spec now says it, so
  the self-grading gap is closed at the requirement level.
- Why it matters: A branch could otherwise loosen the accept check and move
  the matching form into "Accepts" in the same commits.
- Suggested response: Fixed by `spec.md §FR-013`. The plan's side of it is
  PR-008.
- Corroborated by: security and reliability, adversarial implementation

### PR-002: The accept-check test drives `_review_gate.read`, not the guard the record names

- Priority: MAJOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `spec.md §FR-010`: run every listed form "through the guard"
  - `accept-check-threat-model.md §Must let through`: "The guard lets each of these run"
  - `research.md §R-003` and `design/799-threat-model-in-the-record.md §Verification`: the test runs each form through `_review_gate.read` and checks `ACCEPT_REFUSAL`
  - `plan.md §Ownership`: "Whether one command runs the accept | The guard's `read` function"
  - `wfctl/guard/_hook.py:189-195`: the hook calls `_review_gate.refusal` only when the command passes a substring prefilter, then runs the worktree check, which can also refuse
- Finding: Unchanged in the plan and research. The guard is three layers,
  and the planned test pins only `read`. A prefilter change that stops a "Must
  keep catching" form reaching `read` passes the test, and so does a "Must let
  through" form refused by a check other than the accept rule. `tasks.md` T008
  adds a `worktree_guard` assertion for the "Must keep catching" forms only, so
  even the tasks leave the "Must let through" side at `read`.
- Why it matters: The test is how the record's lists and the guard are kept in
  agreement, and pinning one layer leaves the other two unobserved.
- Suggested response: State in R-003 which surface the test drives for each
  list. `worktree_guard` with a JSON payload covers all three layers. If `read`
  is kept for either list, say so in the record's Verification and in FR-010's
  trace, and state what the test doesn't cover.
- Corroborated by: adversarial implementation, security and reliability

### PR-003: FR-006's full rule and FR-007 aren't traced into the plan

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `spec.md §FR-006`: four cases, "Accepts", "Must keep catching" let through, "Must let through" refused, and a form in none of the lists
  - `plan.md §Source Code`: `reviewing-security` is "find, judge against, and name the threat model"
  - `research.md §R-005`: covers the "Accepts" note and the missing-threat-model finding only
- Finding: Unchanged. The plan and research name two of FR-006's four cases,
  and leave the other two, and where their notes land in the report, to the
  implementer.
- Why it matters: The plan is the step where the report's shape for each case
  is fixed.
- Suggested response: Add the four cases and where each lands in the report to
  R-005 or the plan.
- Corroborated by: requirements and traceability

### PR-004: design.md's rendered skill text uses the superseded trigger "narrows"

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `spec.md §Clarifications`: the trigger is "adds, removes, loosens, or tightens"
  - `design.md §Level 1`: both rendered skill paragraphs say "adds, removes, or narrows"
  - `plan.md §Summary` and `research.md §R-004`: use the clarified wording, without saying design.md's strings are superseded
- Finding: Unchanged. An implementer copying design.md's rendered paragraphs
  ships a trigger that leaves out tightening.
- Why it matters: US1 scenario 4 would then fail the walkthrough.
- Suggested response: One line in the plan saying the clarified trigger
  replaces the wording in design.md's rendered text.
- Corroborated by: requirements and traceability

### PR-005: Two items in the spec's validation strategy aren't in the plan

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `spec.md §Validation Strategy`: `uv run wfctl arch accept --dry-run` on each new record
  - `spec.md §SC-003`: the security group on this branch names the record in each report
  - `plan.md §Technical Context` (Testing) and `§Constitution Check`: neither item
- Finding: Unchanged. The dry run on the two level-2 records and the SC-003
  check of the branch's own security reports have no step in the plan.
- Why it matters: SC-003 is the only end-to-end evidence that a reviewer
  follows the new instruction, and the dry run checks the records' shape before
  the user is asked to accept them.
- Suggested response: Add both to the plan's validation list.
- Corroborated by: requirements and traceability

### PR-006: The heading test's comparison is unspecified

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `spec.md §FR-009` and `§SC-004`: the reference and `reviewing-security` name the same four headings
  - `contracts/threat-model-section.md`: a rename of any of the four `###` headings "or of `## Threat model`" fails the heading test
  - `plan.md §Structure Decision`: now says the test reads the bundle through `files("wfctl")`, which answers the earlier half of this finding
- Finding: The plan now says how the test reaches the bundle. It still doesn't
  say how the test finds the headings in `reviewing-security` (prose names,
  backticked names, or `###` lines), whether it covers `## Threat model` as the
  contract promises while FR-009 names only four headings, or whether it is set
  equality or containment.
- Why it matters: Two implementers could write tests that disagree on the
  contract's rename case.
- Suggested response: State the comparison in the plan or research, and either
  include `## Threat model` or drop it from the contract.
- Corroborated by: adversarial implementation

### PR-007: data-model.md says each listed item carries exactly one backticked command

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `data-model.md §Validation` and its table: each item "carries exactly one backticked command" / "one backticked form"
  - `accept-check-threat-model.md §Must keep catching` items 16-19 and `§Must let through` item 8: two or three code spans each (earlier probe)
  - `research.md §R-003`: "the first last backtick span", and "five items name `--dry-run`", where four do and the fifth names `arch`
- Finding: Unchanged. R-003's last-span rule handles the record as written,
  but the data model states an invariant the record breaks, and R-003's wording
  still has the slip.
- Why it matters: A test written from data-model.md that asserts one span per
  item fails on the current record.
- Suggested response: Change the data model to "the last code span is the
  form", and fix R-003's wording.
- Corroborated by: adversarial implementation

### PR-008: FR-013 has no technical approach, and R-002 still reads the bar at the head only

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `spec.md §FR-013`: judge against the trunk's lists when the threat model is accepted on the trunk, and report a form moved out of "Must keep catching" or into "Accepts" as a finding
  - `research.md §R-002`: the reviewer runs `git grep -l '^## Threat model' <head> -- <arch-root>` and reads each hit at the head; nothing reads the trunk's version
  - `plan.md §Summary`, `§Source Code` (`reviewing-security`), and `§Ownership`: none names FR-013 or the trunk's version
  - `AGENTS.md §Declaring reviewers`: reviews read `trunk` from `wfctl.json` on the default branch, the one `origin/HEAD` names, which the reviewer would need to follow to find the trunk
- Finding: The spec gained a requirement the plan doesn't trace, and the one
  research decision on reading records describes head-only reading. An
  implementer working from the plan and research ships a reviewer that judges
  an edited accepted record against its edited lists, which is what FR-013
  forbids. The plan also leaves three questions open: which ref is the trunk
  (`origin/HEAD`, or the `trunk` declared in the default branch's
  `wfctl.json`), how the reviewer tells that a record is accepted on the trunk
  (its `status` read at that ref), and what it does when the branch also edits
  the record's status. `tasks.md` T006 answers the first two with
  `git show <trunk>:<path>` and `origin/HEAD`, but tasks don't fix a plan.
- Why it matters: FR-013 closes the self-grading gap on the control this
  feature protects. Left out of the plan, the gap returns as soon as anyone
  implements from research.
- Suggested response: Extend R-002 with a second step: for each record found,
  read it at the trunk with `git show`, and when its status there is accepted,
  judge against the trunk's lists and report each moved form. Name the trunk ref
  and how it's resolved, and add FR-013 to the plan's `reviewing-security` line.
- Corroborated by: requirements and traceability, security and reliability

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Source Code (design-passes); research.md §R-004 | covered; PR-004 |
| FR-002 | plan.md §Source Code (design-levels) | covered; PR-004 |
| FR-003 | plan.md §Source Code (architecture-decisions reference) | covered |
| FR-004 | plan.md §Source Code (reference); data-model.md | covered |
| FR-005 | plan.md §Source Code (reviewing-security); research.md §R-002, §R-005 | covered |
| FR-006 | plan.md §Source Code (reviewing-security); research.md §R-005 | PR-003 |
| FR-007 | research.md §R-005 | covered |
| FR-008 | plan.md §Source Code (fanning-out-code-review) | covered |
| FR-009 | plan.md §Source Code (test_threat_model_skills.py), §Structure Decision | PR-006 |
| FR-010 | plan.md §Source Code (test_accept_check_threat_model.py); research.md §R-003 | PR-002, PR-007 |
| FR-011 | plan.md §Summary, §Source Code (committed in brainstorm) | covered; record checked |
| FR-012 | plan.md §Source Code (changes/799.change.md) | covered |
| FR-013 | none | PR-008 |
| SC-001 | plan.md §Technical Context (walkthrough); quickstart.md | covered |
| SC-002 | research.md §R-003 | covered; 20 and 8 confirmed by the earlier probe |
| SC-003 | none | PR-005 |
| SC-004 | plan.md §Constitution Check (mutation check) | covered; PR-006 |

## Assumptions challenged

- `_review_gate.read` stands in for "the guard". True for all 28 forms at the
  earlier probe, not stated as an assumption (PR-002).
- The trunk a reviewer reads is `origin/HEAD`. Named only in `tasks.md`, and
  AGENTS.md says reviews read a declared `trunk` from the default branch's
  `wfctl.json`, which can differ (PR-008).
- A reviewer told to drop an "Accepts" form will do so. Named in design.md
  §Key Assumptions to Validate, with this branch's panel as the first test.
- `git grep` over `wfctl arch-root` at the head reaches every record. The
  level-3 record names this as assumed, and the failure direction (a missing
  threat model reported) is the safe one.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- The record's lists are the test's parameters, read from the file, with a
  non-empty assertion so a renamed heading can't turn the test into a test of
  nothing (`research.md §R-003`).
- The plan keeps the vendored skills unedited and puts the section's shape in
  one reference, with a test that catches the reviewer skill falling behind.
- FR-013 makes the user the only one who moves the bar, which matches the
  level-2 record's Owns truth.
- The Structure Decision now names `files("wfctl")`, so the heading test won't
  read the fake tree conftest's `bundle` fixture points at.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
