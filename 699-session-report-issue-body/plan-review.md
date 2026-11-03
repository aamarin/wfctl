# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | eb94d4183f90264c09806f3c9c219a2bc7ee0ebe | technical strategy |
| spec.md | add45f930c0e43cafea7c8f99a2f3fb9304c2d47 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | 737102bd9e9edc4ab0d7c783caa94678f557a995 | design-record index (no entries listed, state none) |
| research.md | 9b62ac9a3c9cb071f1e3dc254a159f91ff8a62a1 | planning evidence |
| data-model.md | bdf7260596567ba782a9e117480dc404eafededb | planning evidence |
| quickstart.md | 1a81c9ae2f2554e9eceb0e108cde9fe0c1b78547 | planning evidence |
| contracts/console-issue-section.md | 1df83fce5bdc0f7cfbe423a18a0ff0c421d8c5dd | planning evidence |
| plan-review.plan.md | 2747d42b30b6510d336bc9df0d2b722b1f608479 | base: plan copy read for the re-review |

## Review scope

- Re-review: the earlier report exists, the plan copy exists, and the copy's
  identity (2747d42b30b6510d336bc9df0d2b722b1f608479) equals the earlier
  report's `plan.md` row. The copy was diffed against `plan.md`.
- Changed input named by the caller: `spec.md`, earlier identity
  f031edf6e369c7e9c02c866fff02074bce5569a0, now
  add45f930c0e43cafea7c8f99a2f3fb9304c2d47. It gained FR-007. It was re-read
  in full and the whole of `plan.md` was reviewed against it.
- The other input rows (`design.md`, `research.md`, `data-model.md`,
  `quickstart.md`, `contracts/console-issue-section.md`) match their earlier
  identities.
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification
- Conditional lenses: security and reliability did not apply as a full lens,
  since the change only removes text from a console rendering and adds no trust
  boundary, secret, or state. The one trust-related point, the pointer line's
  key, was PR-003 and is fixed.
- Design records: `design.md` lists none (state none), so no record binds the plan
- Constitution: absent, so the plan's `AGENTS.md`-derived gates were checked
  against `AGENTS.md` instead
- `[NEEDS CLARIFICATION` markers in `spec.md`: none standing
- Existing code inspected: `wfctl/_session_report.py` (`_trim_issue`, `_outside`,
  `render_session_report`), `wfctl/agents/skills/start-session/SKILL.md` (step
  5, step 8 table) and `references/rationale.md` (line 199),
  `tests/test_start_session_asks_conditionally.py`
- Reviewers: the three lenses above, run in sequence by one agent

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 1

Earlier findings: 3 of 3 fixed. One new MINOR finding (PR-004).

No BLOCKER findings identified in this review.

## Findings

### PR-001: The start-session skill still reads the issue body on a branch whose handoff names no first action

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-007` now requires the step 8 row to tell the agent to run `wfctl issue view <id>` when the report left the body out
  - `plan.md §Summary` (last paragraph) names the row, both copies (`SKILL.md`, `references/rationale.md`), and the reason, including the empty-body ask
  - `plan.md §Source Code` lists both skill files and `tests/test_start_session_asks_conditionally.py`
  - `plan.md §Constitution Check` adds the `uv run wfctl install-skills` and read-back of the installed skill, as `AGENTS.md` requires for `wfctl/agents/`
  - the row is at `SKILL.md` line 106 and `rationale.md` line 199, the same text, so both copies exist as the plan says
- Finding: The earlier evidence no longer holds. The plan now changes the row
  and its rationale copy, and verifies the skill edit.
- Why it matters: Closed.
- Suggested response: None.
- Corroborated by: requirements and traceability, adversarial implementation

### PR-002: Two edge cases in the spec have no test listed in the plan

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Tests that change` new tests 5 (empty-string handoff, naming the `is None` risk), 6 (empty body after `--`), and 7 (empty header fields trimmed with the body cut)
- Finding: The three missing cases now each have a listed test.
- Why it matters: Closed.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-003: The pointer line takes its key from the payload without saying where it is safe

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §Summary` paragraph 3: the line prints with `markup=False`, and its only variable is `payload["issue"]`, taken from the branch name and not the tracker
  - `render_session_report` already prints its own lines with `markup=False` (lines 324, 340, 344)
- Finding: The plan now states the key's source and the print mode.
- Why it matters: Closed.
- Suggested response: None.
- Corroborated by: single reviewer

### PR-004: Step 5 of the skill still tells the agent to read the issue, and the plan does not decide whether it changes

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `wfctl/agents/skills/start-session/SKILL.md` step 5 (lines 62-65): "Read it for what the work is for", and "a flush-left line is wfctl's, never the issue's"
  - `spec.md §FR-002`: the pointer line says "since the handoff below names the work", which is also printed when the summary names no first action
  - `plan.md §Summary` and `§Source Code`: only the step 8 row changes
- Finding: Step 5 describes the section as the issue text, and says flush-left
  lines are wfctl's. The new flush-left pointer line fits that, but step 5
  does not say the body may be absent. The pointer line also asserts the
  handoff names the work in the one case FR-007 exists for (a summary naming no
  first action). The plan leaves both to the implementer without saying they were
  considered.
- Why it matters: A reader of step 5 alone has no cue that a missing body is
  intended, and may read the line as a fault. The cost is small, since step 8
  carries the instruction.
- Suggested response: One line in the plan saying step 5 stays as is, or gains
  half a sentence naming the pointer line, and that the FR-002 wording is fixed
  by the spec.
- Corroborated by: single reviewer

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Summary, research.md §Where the body is cut, new test 7 | covered |
| FR-002 | plan.md §Summary, contracts state 1, new test 1 | covered; key source stated |
| FR-003 | contracts state 2, new test 2 | covered |
| FR-004 | contracts state 3, new test 3 | covered |
| FR-005 | new test 4 | covered |
| FR-006 | research.md §Which condition hides the body, new test 5 | covered |
| FR-007 | plan.md §Summary, §Source Code, §Constitution Check, new test 8 | covered; step 5 is PR-004 |
| SC-001, SC-002, SC-003 | tests plus quickstart | covered |
| Edge case: read fails | `test_every_reason_code_prints_on_its_line...` unchanged | covered |
| Edge case: empty handoff, empty body | new tests 5, 6 | covered |

## Assumptions challenged

- "The row appears twice and both change." Checked: `SKILL.md` line 106 and
  `rationale.md` line 199 hold the same text.
- "Test 8 can pin the sentence." `test_start_session_asks_conditionally.py`
  already reads `SKILL.md` and has row tests such as
  `test_the_issue_row_asks_when_the_issue_body_is_empty`. The plan does not say
  whether test 8 also pins the `rationale.md` copy; the file's existing
  `rationale` tests are the model. Not raised as a finding.
- The earlier list of two existing tests that break remains as checked in the
  first review; `_trim_issue` has one caller.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- The cut sits in `_trim_issue`, the one place that already parses the `--`
  line, and returns whether it cut.
- `payload["handoff"] is None` reuses the exact test that prints the `Handoff`
  heading, and test 5 now guards it.
- The skill edit is paired with a skill read-back under `install-skills`.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
