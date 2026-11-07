# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 571c94a9ed021ed8c77aee30e9f8d5b5338e4827 | technical strategy |
| spec.md | 040a074d1b14e88c1e88b6c0d2685a24aa3c5d3f | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | f2a7241ab5d56659020b8ae2623f9c92e7e515f6 | design-record index |
| docs/architecture/design/724-cross-layer-checks-in-rubric.md | 350e1f0c82b5097ad95e53a8305d40c159815fe9 | design record |
| docs/architecture/vendor-upstream-skills.md | 994c2021e811b43cdbc944453484e6873a2cdad6 | architecture record the plan's Constitution Check cites |
| research.md | 92725d018019c3d32f57eb315b65d2ac745c03fe | planning evidence |
| data-model.md | 92c3ef5f5b6598d8725615fb72c317bdbd503f1d | planning artifact |
| quickstart.md | b0f5d9459c7bbb801d4bd2c65d8067acef65907b | verification procedure |
| contracts/review-report.md | d22de129f40f57dec05ae53258a7805190b2b6ae | report contract |
| exceptions/design-method/boundary.md | 0f8d7a56e6c37a17b9644832be7e215f419bb2ae | level-2 boundary answer |
| checklists/requirements.md | f494fe4b228253869de069aa0319bfa6c135fc4a | requirements-quality checklist |
| plan-review.plan.md | 2164759ac53cc4dbbafa48e304ff3a7c48b8435b | base of this re-review |

## Review scope

- Re-review: the earlier report and the plan copy exist, and the copy's
  identity matches the earlier report's `plan.md` row.
- Changed since the earlier report: two lines in `plan.md`. The
  `vendor-upstream-skills` gate under `§Constitution Check` now says
  `requesting-code-review` is derived from obra/superpowers and that its edit
  drops the count. The `requesting-code-review/SKILL.md` row under
  `§Source Code` now reads `"the six-pass rubric" → "the rubric"`. These were
  reviewed together with `research.md §R3`, which the gate cites,
  `quickstart.md` step 3, which searches for the phrase, and the FR-012 trace
  row.
- Other inputs: every other row of the earlier report has the same identity
  today, so none was re-read in full against the whole plan.
- Inputs named as changed by the command: none.
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification, with dependency and scope
  folded into architecture, and verification and risk into adversarial.
- Conditional lenses: security and reliability did not apply. The change is
  prose in review skills plus one count in one test. It touches no
  authorization, secrets, sensitive data, destructive operation, concurrency,
  distributed state, or migration. The enforcement around reviews
  (`wfctl/_review.py` `judge`, the review notes) is unchanged, and the trail
  sits before the verdict line, so the report still ends on the verdict that
  `judge` reads.
- Design records: 1 listed in design.md
  `docs/architecture/design/724-cross-layer-checks-in-rubric.md` (status
  `proposed`).
- Existing code inspected: `wfctl/agents/skills/requesting-code-review/SKILL.md`
  (the "(the six-pass rubric)" phrase and the obra/superpowers attribution
  line), and `docs/architecture/vendor-upstream-skills.md` § Decision on
  layering over editing.
- Reviewers: the lenses above, run in sequence by one agent.

## Summary

BLOCKER: 0
MAJOR: 1
MINOR: 6

No BLOCKER findings identified in this review. PR-004 is fixed, since the plan
now states that `requesting-code-review` is derived and drops the count from
its one phrase. The other seven findings are open, because the plan change
does not reach them and none of their inputs changed. The one MAJOR finding,
PR-001, is still that the sibling-path pass has no source for earlier fixes in
any panel round after the first.

## Findings

### PR-001: The sibling-path pass has no source for earlier fixes after round one

- Priority: MAJOR
- Category: Missing Information
- Status: open
- Evidence:
  - `spec.md §FR-007` and User Story 2 scenario 2: report new code that brings
    back a pattern "an earlier commit on the branch fixed".
  - `spec.md §FR-006`: rules are read "from the diff and from the commit
    messages when the review covers commits".
  - `fanning-out-code-review/SKILL.md` Step 1: `run.json` lists "every commit
    since the group last completed a run". Step 2: the reviewer reviews "the
    commits listed in `run.json`", and is told not to build a range with
    `git diff` or `git log`.
  - `plan.md §Technical Context`, Constraints: no edits to `_review*.py`, so
    `run.json` cannot grow to cover the whole branch.
  - `quickstart.md` step 4: the only check runs over the full range
    `7cde6095..996f5e5c`, which is one first-round review.
- Finding: In round two or three, the fix an earlier round reviewed is not in
  the commits the reviewer is given. The PFMS shape (the paycheck guard, then
  the plan goal two commits later) passes unseen whenever those two commits
  land in different runs, because the round-two diff adds no rule to start the
  sibling search from. The artifacts do not say whether the pass should read
  the branch's history since the trunk for rules while still reporting only
  on the run's commits, or whether FR-007 is limited to the commits the run
  covers.
- Why it matters: The two readings produce different rubric text, and one of
  them quietly drops User Story 2 scenario 2 on every round but the first. No
  planned verification can tell them apart.
- Suggested response: Choose one reading in the plan. Either have pass 8 read
  rules from the branch's own commits since its merge-base with the trunk
  (non-merge, so it agrees with the dispatch rule) while findings stay limited
  to what is still there at the run's head, or narrow FR-007 to the commits
  the review covers and record the limit. Add a check that exercises a second
  round, or say why one is not needed.
- Corroborated by: requirements and traceability, adversarial implementation

### PR-002: The report contract carries an example from wfctl's own config

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `contracts/review-report.md`: the trail row
    `--rounds flag parser: int · check: ≥ 0 · wfctl.json: int`.
  - `research.md §R5`: the neutral examples are the username length and the
    comment-preview escaping, and only those two.
  - `research.md §R2`: the Step 5 report example is "extended to show" the
    trail, so the contract is what the implementer will copy.
  - `spec.md §FR-011`, `§FR-013`: neutral examples, and no rule or example
    that only one repository has.
  - `wfctl/` has no `--rounds` flag. The value is the `review.rounds` key in
    `wfctl.json`.
- Finding: The third example names wfctl's own config file and a flag that
  does not exist. Copied into the shipped rubric, it reads as a wfctl-specific
  case in a skill that reviews other projects' code.
- Why it matters: FR-013 is a MUST, and no verification step checks it.
- Suggested response: Replace the row with a generic CLI case (for example, a
  `--retries` flag parsed as any int, where the config schema caps it at 10),
  or drop it and keep R5's two examples.
- Corroborated by: requirements and traceability

### PR-003: The stale-count search misses two of the phrases the change edits

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `quickstart.md` step 3: `grep -rn "six-pass\|six lenses\|six passes"`.
  - `code-review/SKILL.md` Red flags: "ignoring the other five passes", which
    has to become seven.
  - `code-review/SKILL.md` and `commands/code-review.md` descriptions: each
    lists the six lens names, and FR-012 covers places that list the passes,
    not only count them.
- Finding: After the edit, a stale "five passes", or a description that says
  "eight" but still lists six names, passes the search.
- Why it matters: FR-012's only check would then report clean on a drift the
  change was meant to remove.
- Suggested response: Add `five passes` to the search, and check that both
  descriptions name the two new passes.
- Corroborated by: adversarial implementation and verification

### PR-004: R3 defers a question the accepted record already answers

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `plan.md §Constitution Check`: the `vendor-upstream-skills` gate now says
    `requesting-code-review` "is derived from obra/superpowers, so its edit
    drops the count rather than changing it, as research.md R3's alternative
    allows".
  - `plan.md §Source Code`: the row now reads
    `"the six-pass rubric" → "the rubric"`.
  - `requesting-code-review/SKILL.md` carries the obra/superpowers
    attribution line, and `vendor-upstream-skills.md` § Derived today lists
    the file.
- Finding: The earlier plan ticked the gate while leaving it to tasks to find
  out whether the file was derived. The plan now states that it is, and takes
  the edit that stays true through a later pass change.
- Why it matters: The gate now records a check that was made.
- Suggested response: Fixed by the revised `plan.md §Constitution Check` and
  `§Source Code`. `research.md §R3` still says tasks checks the attribution
  line and treats dropping the count as optional. Its alternative permits what
  the plan chose, so the two don't contradict, but tasks should follow the
  plan.
- Corroborated by: architecture and boundaries

### PR-005: The SC-002 and SC-003 runs leave their baseline and target unnamed

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `spec.md §SC-002`: the trail names every input "today's trace reviewer
    listed".
  - `quickstart.md` step 4 names the brief but not the trace reviewer's report.
    That report is `experiment-pfms-1011/reports/t1.md` under this branch's
    state dir, and it carries a `## Per-input trace` section.
  - `quickstart.md` step 5: "a docs-only commit in this repo", with no commit
    named and no brief, since the saved brief is written for PFMS.
- Finding: The checker has to find the SC-002 baseline alone, and has to pick
  a commit and write a brief for SC-003.
- Why it matters: The comparison SC-002 asks for is not repeatable as
  written. Two people running step 5 can give the reviewer different briefs.
- Suggested response: Name `reports/t1.md` as SC-002's baseline, and name the
  docs-only commit and the brief for step 5.
- Corroborated by: adversarial implementation and verification

### PR-006: SC-004 has no check

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `spec.md §FR-014`, `§SC-004`: groups, reviewer counts and the round cap
    are the same before and after.
  - `quickstart.md` and `spec.md §Validation Strategy`: no step for either.
- Finding: The constraint is stated in `plan.md §Technical Context`, but no
  step observes it.
- Why it matters: The constraint is cheap to observe, and it is the one
  promise to #725's branch.
- Suggested response: One step, `git diff --stat` against the trunk showing
  no change to `wfctl.json` or `wfctl/_review*.py`.
- Corroborated by: adversarial implementation and verification

### PR-007: "Adjacent layers" is undefined when a middle layer is unknown

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `spec.md §FR-004`: report only "a concrete contradiction between adjacent
    layers".
  - `spec.md §FR-003` and `contracts/review-report.md`: a layer can read
    `unknown (<reason>)`.
- Finding: When the server's limit is unknown, a form limit of 40 against a
  `varchar(32)` column is a contradiction between layers that are not
  adjacent. The artifacts do not say whether it is reported.
- Why it matters: Two implementers would write the pass differently, and the
  stricter reading suppresses a real finding exactly when the reviewer could
  not reach a layer.
- Suggested response: One sentence in pass 7. For example, compare across an
  unknown layer, and say in the finding which layer was unknown.
- Corroborated by: adversarial implementation

### PR-008: The plan does not say what a failed SC-001 run leads to

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `724-cross-layer-checks-in-rubric.md` § Assumed: falsified "by one
    reviewer, given the changed rubric, missing the rate cap or the overflow".
  - `quickstart.md` step 4: one run, with no next step on a miss.
- Finding: A single model run can miss through variance as well as through a
  weak rubric, and the record treats one miss as falsifying its design. The
  plan does not say whether a miss means revising the pass text, running
  again, or reopening the record.
- Why it matters: The record is `proposed`. An unplanned miss at implement
  time leaves the implementer to decide whether the design still stands.
- Suggested response: Say what a miss leads to. For example, revise the pass
  text and run once more, and reopen the record only if the second run also
  misses.
- Corroborated by: adversarial implementation and verification

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Summary, research.md §R1 | covered |
| FR-002 | plan.md §Summary, data-model.md Input | covered |
| FR-003 | data-model.md Layer, contracts/review-report.md | covered |
| FR-004 | contracts/review-report.md | PR-007 |
| FR-005 | research.md §R1 | covered |
| FR-006 | plan.md §Summary, data-model.md Rule | PR-001 |
| FR-007 | data-model.md Sibling | PR-001 |
| FR-008 | research.md §R2, contracts/review-report.md | covered |
| FR-009 | research.md §R2, contracts/review-report.md | covered |
| FR-010 | contracts/review-report.md | covered |
| FR-011 | research.md §R5 | PR-002 |
| FR-012 | plan.md §Source Code, quickstart.md step 3 | PR-003 (PR-004 fixed) |
| FR-013 | plan.md §Technical Context | PR-002 |
| FR-014 | plan.md §Technical Context | PR-006 |
| SC-001 | quickstart.md step 4 | PR-008 |
| SC-002 | quickstart.md step 4 | PR-005 |
| SC-003 | quickstart.md step 5 | PR-005 |
| SC-004 | none | PR-006 |

## Assumptions challenged

- No mechanical check on report contents (`research.md §R4`). Verified:
  `wfctl/_review.py` `judge` reads only the `Reviewed:` line and the verdict at
  the end, so the trail needs no code change, and placing it before `net:`
  keeps the verdict last.
- The pass-count test finds the new headings (`research.md §R1`). Verified:
  `**7. Input trace**` and `**8. Sibling paths**` match
  `^\*\*\d\. ([A-Za-z][A-Za-z &-]*)\*\*`. The `\d` is one digit, which holds
  up to nine passes.
- The new `requesting-code-review` edit leaves the stale-count search intact
  (`quickstart.md` step 3). Verified: once the phrase reads "(the rubric)",
  the file holds no count, so a later pass change cannot leave it stale, and
  a stale "six-pass" anywhere else under `wfctl/agents/` is still found.
- Three files besides the skill restate the count (`plan.md §Technical
  Context`). Verified by search. No other place in `wfctl/`, `docs/`,
  `README.md` or `AGENTS.md` states the code-review pass count.
- The plan builds on a design record whose status is `proposed`. Whether it is
  accepted is the person's call, and nothing in the plan depends on that
  having happened first.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- The passes are added after the six, so no existing number moves, and the
  severity floor sits in Step 5 rather than in pass 7, so severity has one
  home (`research.md §R1`, `§R2`).
- The contract puts the trail between the findings and `net:`, so
  `fanning-out-code-review`'s statement that a clean report ends at the
  metric and a verdict stays true.
- The boundary is held tight. No `_review*.py` edit, no new group, and the
  level-2 answer is on file in `exceptions/design-method/boundary.md`.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
