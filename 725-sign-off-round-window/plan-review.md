# Plan Review Report

Review state: completed
Review type: full

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 5308f603ecf7d4cd04d7a50aaa62f23e97b03f8e | technical strategy |
| spec.md | 462c493c021c50f6dc007e81b065111c33faf5d8 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | 4235f7b0e0803352376cb858fef0f1a1685c9b0e | design-record index |
| docs/architecture/design/725-sign-off-records-round-counts.md | fb2ea9d163146d42b6afb342f9d2a2e82bca6bc9 | design record (level 3) |
| docs/architecture/review-round-window.md | 8b5b4c73c4b0f4fd408f2faa322197027131f8ae | design record (level 2) |
| research.md | 35adc580c26928e4d8dc5e6e0da22623d0c77400 | planning evidence |
| data-model.md | 4ed64acd3dd7a685730011b97b244123d98dd88b | planning evidence |
| contracts/cli-output.md | 2732e6e9225c28ea96874a39ddab8fc7b3225d16 | planning evidence |
| quickstart.md | 4c3ca1eb7e3a12753b53987217f97f4415372ed7 | planning evidence |

## Review scope

- Full review: no earlier report
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification
- Conditional lenses: security and reliability applied, since the round cap is
  the control that stops an agent's review loop and only the user may open a
  window. The sign-off file the window reads sits in a state folder the agent
  can write.
- Design records: 1 listed in design.md, the level-3 record above. design.md's
  prose names the level-2 record, which the plan also cites, so it was read as
  the behavior the level-3 record implements.
- Existing code inspected, to check the plan's claims: `wfctl/_review.py`
  (`RoundCapReached`, `runs_started`, `rounds_tallied`, `_tally_round`,
  `Started`, `start`, `signed_off`, `sign_off`, `_read_json`, `pending_at_head`,
  `_capped`), `wfctl/cli.py` (`review start` output, `review sign-off`),
  `wfctl/_paths.py` (`resolve_round_dir`), `wfctl/_evidence.py` (the capped
  reason), and the names of the existing cap and sign-off tests in
  `tests/test_review.py`, `tests/test_review_cli.py`, `tests/test_review_gate.py`
  and `tests/test_review_rename.py`
- Skill text checked for the old rule: `wfctl/agents/skills/opening-a-change/SKILL.md`,
  `wfctl/agents/skills/fanning-out-code-review/SKILL.md`, `AGENTS.md`
- Reviewers: the four lenses above, run in sequence by one agent

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 7

No BLOCKER findings identified in this review. Every line number the level-3
record cites matches the code, and the plan follows both records with no
departure. The findings are about wording the spec asks for in two edge cases,
existing tests that flip and are not all named, two docs the plan leaves out of
scope, and how strictly the new `rounds` object is read.

## Findings

### PR-001: The "since the sign-off" wording is dropped for two cases FR-008 covers

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `spec.md §FR-008`: "After a sign-off, both say the count is since the
    sign-off and name its short commit"
  - `plan.md §Implementation notes 4`: `Started.since` is set only "when the
    sign-off recorded a count for that group, otherwise None"
  - `contracts/cli-output.md`: shows only the case where the sign-off recorded
    the group
- Finding: With a sign-off file from 0.26.0, or for a group the sign-off
  recorded no entry for, the plan prints today's wording although a sign-off
  exists. FR-008 read literally says the reverse.
- Why it matters: The plan's choice is the more truthful one, since in both
  cases the count really is the whole branch. But it is an unlabeled
  interpretation of a requirement, and a test written from the spec would fail
  against it.
- Suggested response: State the two cases in `contracts/cli-output.md` and in
  note 4 as the reading of FR-008, so the tests follow the plan.
- Corroborated by: requirements and traceability

### PR-002: Existing tests that flip are named only in part

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `plan.md §Implementation notes 8` and `research.md §R3`: only tests that
    "sign off at the cap and expect no run", and only in `tests/test_review.py`
  - `tests/test_review.py::test_start_at_the_cap_refuses_a_commit_made_after_the_sign_off`
    and `tests/test_review_cli.py::test_start_at_the_cap_with_a_commit_after_the_sign_off_still_refuses`
    sign off and then expect a refusal. Under the window, both now get a run.
  - `tests/test_review_cli.py::test_start_at_the_cap_with_a_sign_off_says_nothing_is_left_to_review`
    and `::test_start_past_a_lowered_cap_with_a_sign_off_says_so_in_the_same_words`
    flip too, and so does
    `tests/test_review.py::test_start_at_the_cap_allows_a_clean_merge_of_main_after_the_sign_off`
  - `plan.md §Technical Context, Testing`: the status test goes in
    `tests/test_review_gate.py` "or wherever `_capped` is tested today". The
    `_capped` tests are `test_coverage_for_status_*` in `tests/test_review.py`.
- Finding: The covered-at-the-cap path survives only once a window is used up,
  which a test reaches by signing off first and then starting the cap's number
  of runs at the signed head without completing them. The plan says this for
  one class of test and not for the refusal tests or the CLI ones.
- Why it matters: An implementer meeting a failing refusal test with no
  instruction may delete the assertion instead of moving the sign-off, and the
  property it proves, that a commit after the sign-off isn't covered, then has
  no test.
- Suggested response: List the five tests in note 8 with the same rewrite, and
  name `tests/test_review.py` for the status tests.
- Corroborated by: adversarial implementation and verification

### PR-003: Three spec edge cases have no test named

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `spec.md §Validation Strategy`: "new tests for each acceptance scenario and
    edge case above"
  - `spec.md §Edge Cases`: a cap changed after the sign-off; a group that had
    never started a round at the sign-off
  - `spec.md §FR-001`: the count is the larger of the run records and the
    issue's tally
  - `plan.md §Project Structure, tests/`: window counting, old sign-off file, no
    stacking, start after sign-off, wording, status
- Finding: No named test covers a cap that changes after the sign-off (FR-006),
  a group absent from the sign-off's `rounds`, or a sign-off whose count comes
  from the tally rather than the runs, which is the only case that exercises
  `cli.py` passing `resolve_round_dir` to `sign_off` (note 7). The rename, cap
  0, and nothing-unreviewed edge cases already have tests
  (`tests/test_review_rename.py::test_a_rename_drops_the_branchs_sign_off_and_the_cap_still_holds`,
  `tests/test_review.py::test_start_under_a_cap_of_zero_*`,
  `tests/test_review_cli.py::test_sign_off_with_nothing_unreviewed_needs_none`),
  which the plan doesn't say carry over.
- Why it matters: A dropped `rounds_dir` in `cli.py` records a count below the
  real one and shrinks the window with no test failing. That fails closed, so
  the risk is bounded.
- Suggested response: Add the three tests to the plan's test list, and name the
  existing tests that cover the other edge cases.
- Corroborated by: requirements and traceability, adversarial implementation
  and verification

### PR-004: Two docs keep describing the cap per branch

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `design.md §MVP Scope 4`: "`opening-a-change` and any skill text that says a
    sign-off doesn't reset the count"
  - `plan.md §Technical Context, Scale/Scope`: "one skill (`opening-a-change`)"
  - `AGENTS.md` (§Declaring reviewers): "`review.rounds` caps how many times each
    group runs on one branch"
  - `wfctl/agents/skills/fanning-out-code-review/SKILL.md` (Step on `review
    start` output): "When a sign-off covers every commit left at the cap,
    `review start` says nothing is left to review and exits 0", which after this
    change is reached only once a window is used up
- Finding: FR-009 names only `opening-a-change`, and the plan stops there. The
  two other passages describe the rule this change replaces, and agents read
  both.
- Why it matters: An agent reading `fanning-out-code-review` after a sign-off
  expects exit 0 and gets a run, and `AGENTS.md` tells the next contributor the
  cap is per branch.
- Suggested response: Add both passages to the plan's scope, or say why they
  stay.
- Corroborated by: requirements and traceability, architecture and boundaries

### PR-005: A recorded count above the current count opens an unbounded window

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `plan.md §Implementation notes 2`: only a value that "isn't a whole number
    of 0 or more" reads as no entry, and that "fails closed"
  - `plan.md §Implementation notes 3` and `data-model.md §Window count`:
    `max(0, used - recorded)`
  - `review-round-window.md §Consequences`: the counts are tamper-evident, not
    unforgeable
- Finding: An entry larger than the group's current count, such as one edited to
  99, passes validation and reads as a window of 0 on every start, so the cap
  never applies to that group until the next sign-off replaces the file. No path
  in wfctl writes such an entry, since both counts only grow.
- Why it matters: The record accepts that the file can be edited, but the
  plan's "fails closed" claim covers malformed entries only. Reading an entry
  above the current count as no entry would close this at no cost to a
  legitimate branch.
- Suggested response: Either add that rule to note 2 and `data-model.md`, or
  say the case is accepted under the record's tamper-evidence consequence.
  Also say that `start` now reads `sign-off.json` on every call, so an unreadable
  file fails `start` below the cap, where today it fails only at the cap.
- Corroborated by: security and reliability

### PR-006: The sign-off counts rounds outside the start lock

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `wfctl/_review.py` `start` counts and writes the run under `_start_lock`
  - `wfctl/cli.py` `review sign-off` calls `sign_off` after `input()` returns
  - `plan.md §Implementation notes 1`: `sign_off` counts the runs and the tally,
    with no lock named
- Finding: A run started while the user reads the sign-off prompt is counted in
  the sign-off's base, so it never counts against the new window, and the group
  gets one round past the cap.
- Why it matters: The effect is bounded to one round per sign-off and needs a
  start racing an interactive prompt, so it barely matters. It is still a gap in
  the count the cap exists to protect.
- Suggested response: Say whether `sign_off` takes each group's lock while it
  counts, or note the race as accepted.
- Corroborated by: security and reliability

### PR-007: data-model.md says groups with no runs are left out, FR-001 says runs or tally

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `spec.md §FR-001` and `plan.md §Implementation notes 1`: every group with
    runs on the branch or a round tally on the issue
  - `data-model.md §Sign-off`: "A group with no runs is left out"
- Finding: A group with a tally on the issue and no runs on this branch, such
  as after a rename or with a second branch on the issue, gets an entry under
  the plan and none under the data model.
- Why it matters: The two artifacts give different answers for that group's
  window, though the plan's is the one FR-001 requires.
- Suggested response: Change the data model's sentence to "A group with neither
  runs nor a tally is left out".
- Corroborated by: requirements and traceability

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Implementation notes 1 | covered; PR-007 |
| FR-002 | plan.md §Implementation notes 3, 4 | covered |
| FR-003 | plan.md §Implementation notes 4; research.md §R2 | covered |
| FR-004 | plan.md §Implementation notes 6 | covered |
| FR-005 | plan.md §Summary | covered; coverage code is unchanged |
| FR-006 | plan.md §Summary; research.md §R5 | covered; PR-003 |
| FR-007 | plan.md §Implementation notes 2 | covered; PR-005 |
| FR-008 | plan.md §Implementation notes 4, 5, 7; contracts/cli-output.md | PR-001 |
| FR-009 | plan.md §Project Structure | covered; PR-004 |
| FR-010 | plan.md §Project Structure | covered |
| SC-001 | quickstart.md | covered |
| SC-002 | plan.md §Project Structure, tests/ | covered; PR-002 |
| SC-003 | plan.md §Implementation notes 2; research.md §R4 | covered |

## Assumptions challenged

- Only `start` and `_capped` decide whether a group is at the cap (spec
  Assumptions, level-3 record §Assumed). Checked: `runs_started` and
  `rounds_tallied` are called only at `_review.py` `start` and `_capped`, and
  `_evidence.py` only words the capped reason.
- `_tally_round` keeps receiving the total count (note 4). Checked against
  `_tally_round`, which brings the tally up to `used` and then adds one past
  the larger of the two. The total is what lets a branch whose run records
  outnumber the tally bring the tally up to them; the window count would skip
  that step.
- The plan says the sign-off adds no git calls. Holds: `sign_off` and
  `rounds_in_window` read folders and one JSON file.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- `plan.md §Implementation notes 4` keeps `_tally_round` on the total count
  while `Started.rounds` moves to the window count, so the issue-keyed tally
  still catches up with the branch's run records.
- `research.md §R2` states that the covered-at-the-cap path now applies only
  once the window is used, which is the behavior change most likely to surprise
  an implementer.
- One function feeds both `start` and `_capped`, which is the level-3 record's
  decision and the reason SC-002 can hold.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
