# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | a4d092957e4cdfddc1c51ea3261cc5d53e6fcf30 | technical strategy |
| spec.md | 035adf2d6a5940794e05e63c544645b121d64c88 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | e744aedcd3f7ec78a5e51232521e8339d529138c | design-record index |
| docs/architecture/design/issue-edit-one-field-per-call.md | b5fabc9a07e7c99deebabb74001a8bd3958e33bd | design record |
| research.md | 63e88d8acc812ec6cb9fac944342903b7d6591f0 | planning evidence |
| data-model.md | 5273cc44470967a399cbf48cf8a1d5891310a7d4 | planning artifact |
| quickstart.md | 18321b477b921bcfd2bf3cd01363e57f5c6604c3 | planning artifact |
| contracts/cli.md | b4bd7502471d2fd55cd46634c8a3fd46dd7815ca | contract |
| contracts/tracker-verb.md | 9201df87cdcf64104b2950158c2b698117a3727a | contract |
| plan-review.plan.md | 59e167be327efa4cc8d5a758f49e6da873a26809 | base of this re-review |

## Review scope

- Re-review: the plan copy matches the earlier report's `plan.md` row, so the
  review diffed the copy against `plan.md`.
- Changed in `plan.md`: `§Constitution Check` (complexity gate),
  `§Project Structure` (`_tracker.py` comment), and `§Complexity Tracking`
  (the `dispatch` row). Each now says `dispatch` splits into two helpers.
  These were reviewed together with `research.md §2` and `§3`, which describe
  the helpers, and `§Structure Decision`, which places the edit function.
- Changed inputs, each re-read in full with the whole of `plan.md` reviewed
  against it: `spec.md`, `design.md`, `research.md`, `contracts/cli.md`, and
  `docs/architecture/design/issue-edit-one-field-per-call.md`. `data-model.md`,
  `quickstart.md`, and `contracts/tracker-verb.md` match their earlier rows.
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification, plus verification, risk,
  dependency, and scope from the rubric.
- Conditional lenses: security and reliability applied, for the same reason as
  before. The feature overwrites an issue's title or body in an external
  tracker, which wfctl can't undo, and passes caller text to a backend
  subprocess.
- Design records: 1 listed in `design.md`,
  `docs/architecture/design/issue-edit-one-field-per-call.md` (status
  `proposed`).
- Existing code inspected: `wfctl/_tracker.py` (`ALLOWED`, `_RECORDED_VERBS`,
  `_check_section`), `tests/test_tracker.py`
  (`test_scaffold_skill_documents_every_verb_the_contract_allows`), and
  `docs/reference.md` § Issue trackers.
- Reviewers: all lenses run in sequence by one agent.

## Summary

BLOCKER: 0
MAJOR: 1
MINOR: 6

No BLOCKER findings identified in this review. PR-002 is fixed, since the plan
now names both helpers that come out of `dispatch`. PR-001 stays open at MAJOR
with different evidence. `spec.md §FR-002` now requires `tracker-check` to
report an `edit` template missing `{id}`, `{field}`, or `{value}`, but the plan
has no step or test for that check, and `contracts/tracker-verb.md` still
lists only an unknown placeholder as a finding. Two MINOR findings are new:
the design record's Verification section still says the body is "not
changed", and `design.md` MVP Scope still puts the per-field calls in
`cli.py`.

## Findings

### PR-001: An `edit` template without `{field}` or `{value}` passes the config check

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `spec.md §FR-002`: `tracker-check` "MUST report an `edit` template that
    leaves out any of the three".
  - `plan.md §Project Structure`: `_tracker.py` gets "ALLOWED gains edit", and
    `test_tracker.py` gets "config validation for edit". Neither names a
    required-placeholder check.
  - `wfctl/_tracker.py` `_check_section`: reports only `used - allowed`.
    `ALLOWED` maps each verb to the placeholders it may use, and has no way to
    say which ones it must use.
  - `contracts/tracker-verb.md`: "Any other placeholder is a `tracker-check`
    finding", with nothing about a missing one.
  - `spec.md §User Story 3` and `§Validation Strategy`: still test only a
    template with all three and one with an unknown placeholder.
- Finding: The spec settled the question the earlier review raised, and the
  plan didn't follow. The check is a new rule for one verb, since no existing
  verb requires a placeholder. The plan doesn't say where that rule lives,
  such as a second map beside `ALLOWED` or a case inside `_check_section`, and
  lists no test for a template missing each placeholder.
- Why it matters: An implementer building from `plan.md` and the contracts
  ships the check that lets
  `["jira", "edit", "{id}", "--summary", "{value}"]` validate. Then
  `wfctl issue edit 445 --title T --body B` writes `B` into the summary, and
  wfctl reports both writes as successful.
- Suggested response: Add the required-placeholder rule to
  `plan.md §Project Structure` with the place it lives, a test for a template
  missing each of `{id}`, `{field}`, and `{value}`, and a line in
  `contracts/tracker-verb.md`. Adding a scenario to `spec.md §User Story 3`
  and its Validation Strategy would keep the spec consistent with its own
  FR-002.
- Corroborated by: requirements and traceability, security and reliability

### PR-002: `plan.md` and `research.md` disagree on how many helpers come out of `dispatch`

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Constitution Check`, `§Project Structure`, and
    `§Complexity Tracking`: each now says `dispatch` splits into two helpers,
    one that checks the tracker and prints its notice, and one that runs and
    records a write.
  - `research.md §2` and `§3`: describe the same two helpers.
- Finding: The earlier plan counted one helper where the research described
  two.
- Why it matters: An implementer reading the earlier plan could have recorded
  writes in the edit function, which `research.md §3` rules out.
- Suggested response: Fixed by the three revised `plan.md` sections.
- Corroborated by: deterministic checks

### PR-003: No planned test sends an empty value

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `spec.md §Edge Cases`: `--title ""` or `--body ""` "is sent as given".
  - `plan.md §Project Structure` and `spec.md §Validation Strategy`: the
    listed tests don't include an empty value.
  - `contracts/cli.md`: still has no row for an empty value.
- Finding: If the field check in `cli.py` tests truthiness rather than
  `is None`, `wfctl issue edit 445 --title ""` prints
  `✗ 'edit' needs --title, --body, or both` and exits 2, which contradicts
  the edge case.
- Why it matters: The behavior is specified, and no planned test would show a
  regression.
- Suggested response: Add a test where `--body ""` reaches the backend as an
  empty argument, and a row for it in `contracts/cli.md`.
- Corroborated by: adversarial implementation

### PR-004: The existing scaffold test checks only the verb name, not what `FR-011` requires

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `plan.md §Constitution Check`, `a-rule-is-expressed-as-a-check`: still
    says the existing test "covers the new row".
  - `tests/test_tracker.py`
    `test_scaffold_skill_documents_every_verb_the_contract_allows`: passes when
    the string `` `edit` `` appears anywhere in the skill.
  - `spec.md §FR-011`: the row lists `edit` with its placeholders and the
    script note.
- Finding: The test proves the verb is mentioned. It doesn't check the
  placeholders or the script note, so the gate claims more coverage than the
  test gives.
- Why it matters: The script note is the only guidance a non-GitHub backend
  author gets for mapping field names, and the test still passes without it.
- Suggested response: Reword the gate to say the test covers the name only,
  or add an assertion on the row's placeholders.
- Corroborated by: verification

### PR-005: User-facing docs that list the verbs and recorded writes aren't in the plan

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `docs/reference.md` § Issue trackers: the `Verbs` line and the list of
    recorded writes (`issue-comment` through `issue-close`) leave out `edit`.
  - `AGENTS.md` § Safety: "`wfctl issue comment`, `create`, `label` and
    `close` run when you run them".
  - `plan.md §Project Structure`: still lists no documentation file.
- Finding: Both passages become incomplete once `edit` ships. `FR-012` asks
  only for the help text.
- Why it matters: A reader of the reference page won't learn that `edit`
  exists or that it records `issue-edit`.
- Suggested response: Add `docs/reference.md` and the `AGENTS.md` Safety line
  to `plan.md §Project Structure`, or say why they stay as they are.
- Corroborated by: requirements and traceability

### PR-006: The plan builds on a design record that is still `proposed`

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `docs/architecture/design/issue-edit-one-field-per-call.md`: front matter
    still `status: proposed`.
  - `plan.md §Summary`: "This plan builds that decision", with no note of the
    record's status.
- Finding: The plan treats the field-and-value shape as settled without
  saying the record hasn't been accepted. The record's Log says the user
  agreed to the shape during the brainstorm, so the risk of it changing is
  low.
- Why it matters: If the record changes before implementation, the backend
  contract, the `github.json` entry, and the tests change with it.
- Suggested response: Note the record's status in `plan.md` and who accepts
  it, or accept it before tasks.
- Corroborated by: architecture and boundaries

### PR-007: The design record's Verification still says the body is "not changed"

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `docs/architecture/design/issue-edit-one-field-per-call.md §Verification`:
    the partial-failure test "asserts that the output names the title as
    changed and the body as not changed".
  - The same record's `§Decision`, revised in commit 6046fad: wfctl "reports
    that the title changed and the body write failed".
  - `spec.md §Clarifications` Q2 and `research.md §4`: the line says which
    call failed, because a write that times out can still land.
- Finding: Commit 6046fad updated the Decision and left the Verification
  section on the old wording.
- Why it matters: A test written from the record's Verification section would
  assert a claim the spec deliberately dropped. The spec's exact line and
  `contracts/cli.md` both give the right text, so an implementer is unlikely
  to follow the record here.
- Suggested response: Change the record's Verification line to "the body write
  as failed".
- Corroborated by: deterministic checks

### PR-008: `design.md` MVP Scope puts the per-field calls in `cli.py`

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `design.md §MVP Scope` item 2: `wfctl issue edit` in `wfctl/cli.py`
    "dispatches once per field, title first, and stops at the first failure".
  - `plan.md §Structure Decision`: the per-field calls go in `_tracker.py`,
    and `cli.py` keeps to argument checks and routing.
  - `research.md §2`: calling `dispatch` once per field prints the notice
    twice, which clarify Q1 ruled out.
- Finding: The plan departs from the brainstorm's MVP Scope, for a reason
  `research.md` gives, without saying that it overrides `design.md`.
- Why it matters: A reader who starts from `design.md` builds the loop in
  `cli.py` around `dispatch` and fails `FR-009`. The plan's own text is clear,
  so this forces no choice.
- Suggested response: Note in `plan.md §Structure Decision` that it replaces
  `design.md` MVP Scope item 2, or update that item.
- Corroborated by: architecture and boundaries

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Project Structure (`cli.py`) | covered |
| FR-002 | plan.md §Project Structure (`ALLOWED`); contracts/tracker-verb.md | PR-001 |
| FR-003 | plan.md §Summary; research.md §2 | covered |
| FR-004 | research.md §2, §4; contracts/cli.md | covered |
| FR-005 | research.md §4; contracts/cli.md | covered, PR-007 |
| FR-005a | research.md §4; contracts/cli.md | covered |
| FR-006 | plan.md §Project Structure (`_RECORDED_VERBS`, the run-and-record helper); research.md §3; data-model.md | covered |
| FR-007 | research.md §5; contracts/cli.md | covered, PR-003 |
| FR-008 | research.md §5; contracts/cli.md | covered |
| FR-009 | plan.md §Complexity Tracking; research.md §2; contracts/cli.md | covered, PR-008 |
| FR-010 | plan.md §Project Structure (`github.json`) | covered |
| FR-011 | plan.md §Project Structure (`scaffold-tracker/SKILL.md`) | covered, PR-004 |
| FR-012 | plan.md §Project Structure (`cli.py` help text) | covered, PR-005 |
| SC-001 | plan.md §Summary | covered |
| SC-002 | data-model.md §Recorded write; tests in plan.md §Project Structure | covered |
| SC-003 | contracts/cli.md | covered |
| SC-004 | plan.md §Technical Context (Testing); quickstart.md | covered |

## Assumptions challenged

- `ALLOWED` can express the required-placeholder rule. It can't, since it
  lists what a verb may use and not what it must use. See PR-001.
- The empty-string case needs no test because `issue_cmd` already filters with
  `is not None`. True for the existing filter, and not verified for the new
  field check. See PR-003.
- A recorded write that holds only the name is enough for this feature.
  Stated in `spec.md §Key Entities`, which tracks recording the issue and
  field for every verb in #746. `data-model.md` agrees, and records the action
  name with its branch only.
- Each value reaches the backend as one argument and never through a shell.
  Verified in the earlier review, and the plan's helper split keeps the same
  `subprocess.run` call.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- The plan's two-helper split keeps the notice text and the success record
  each in one function, so `dispatch` and the edit can't drift apart on
  either (`research.md §2`, `§3`).
- The partial-failure lines say which call failed rather than what the issue
  holds, and every artifact except the record's Verification section now
  agrees on them (`spec.md §FR-005`, `§FR-005a`; `research.md §4`;
  `contracts/cli.md`; `design.md`).
- `contracts/cli.md` gives every case its output, exit code, and recorded
  writes in one table, which makes the tests mechanical to write.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
