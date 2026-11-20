# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 3b40ef2fcc98f9e9bf7a226c61141af51b647963 | technical strategy |
| spec.md | 6a8d9e6d45789025365fa4df5d68fc954c73b692 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| AGENTS.md | 9bfca6ea27edb32fa4595b6f1987644c26278702 | project rules the plan borrows its gates from |
| design.md | 42f7cc7b18991dfbe7ee4255197c934411eaae66 | design-record index |
| docs/architecture/approval-mode-is-stored-intent.md | ed2f7c38306805b0ac8f61b36353d2627eca466c | level-2 record the plan is written against |
| docs/architecture/auto-approve-grant-asks-first.md | 46a42fe9863332db6274d8a89b388663ec67eb34 | level-2 record (proposed) the plan's Walkthrough fix 2 implements |
| research.md | c90081c79408c570ec0bb4eb2bf2b3fa7ee43027 | planning evidence |
| data-model.md | 4d19aede098fa663856e769b24c591f5801ec4b9 | planning evidence |
| contracts/cli.md | f923d6fce6a25b332ae4ab5860ca70f4a572eb1c | planning evidence |
| quickstart.md | f8895b19af541174beff1f26993f16e66da89a90 | planning evidence |
| plan-review.plan.md | a8ded9a59df0dcc36456e8f6f274fb581b4c47be | base of this re-review |

## Review scope

- Re-review: the plan copy's identity equals the earlier report's `plan.md` row
- Changed since the earlier report: `plan.md §Technical Context` (Testing),
  `§Constitution Check` (validation plan), `§Walkthrough fixes` 1 and 2, the
  new `§Second review fixes`, and `§Project Structure` (`evidence/`, the
  `test_install_hook_merge.py` entry). Reviewed together with `§Ownership` 5
  and `§Review-plan fixes` 2, which the walkthrough fixes amend
- Inputs that no longer match the earlier report, each re-read in full and the
  whole of `plan.md` reviewed against it: `spec.md`, `research.md`,
  `data-model.md`, `contracts/cli.md`, and
  `docs/architecture/auto-approve-grant-asks-first.md`. `design.md`,
  `quickstart.md`, `AGENTS.md` and `approval-mode-is-stored-intent.md` match
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification
- Conditional lenses: security and reliability applied. The feature lets an
  agent lower the approval bar, and the change adds a permission rule that is
  the control against an unasked grant, so it touches authorization and a trust
  boundary
- Design records: none. `design.md`'s `## Software design decisions` section
  carries no list entries. The level-2 records `approval-mode-is-stored-intent`
  and `auto-approve-grant-asks-first` were read because `design.md` names both
  in prose and the plan is written against them
- Claude Code's permission behavior was checked against the facts the caller
  supplied from its permissions and permission-modes docs: deny, then ask, then
  allow; ask rules prompt in every mode, `bypassPermissions` and auto mode
  included; `dontAsk` and headless `claude -p` deny instead; ask rules match
  past leading assignments and each part of a compound command; `env` isn't
  stripped and `bash -c` isn't matched. The plan and the record state these
  correctly
- Existing code inspected, to verify claims the plan makes:
  `wfctl/evidence/_mode.py` (`grant_auto_approve`, `revoke_auto_approve`,
  `revoked`), `wfctl/_io.py` `append_event` (raises on a failed open),
  `wfctl/_paths.py` `resolve_agent_dir(create=False)` and
  `extract_issue_key` (returns `"unknown"` with no issue),
  `wfctl/cli.py` `_resolve_context`, `_revocation_line`, `_apply_review_cap`,
  and `wfctl/_plan_review.py` `review_count` (restarts at every `mode` event
  with `auto_approve: true`). The branch changes no code
- Reviewers: the four lenses above, run in sequence by one agent
- No unresolved `[NEEDS CLARIFICATION` marker, TODO or placeholder stands in
  `spec.md` or the planning artifacts

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 2

No BLOCKER findings identified in this review. PR-004 to PR-013 are fixed,
PR-009 among them, so no MAJOR finding stands. The two new MINOR findings are
both in the bare command's second line, which the PR-005 fix rewrote as a set
of cases: the cases leave out the revoked mode, which research.md says should
still show who turned the mode on, and they print "turned off outside wfctl"
for a failed `on`, where the spec and the data model say "no grant on record".

## Findings

### PR-001: research.md says an ended session reads as "none", and the code reads it as "other"

- Priority: MAJOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `research.md §1`: `session_open_for` returns `"other"` both for a different
    conversation and for this conversation after `wfctl end`
  - `contracts/cli.md §wfctl auto-approve on`: the refusal is worded to be true
    for both
- Finding: Fixed in the earlier review, and still holds.
- Why it matters: An implementer would have tested the wrong behavior.
- Suggested response: Fixed by `plan.md §Review-plan fixes` 1, research.md §1,
  and the contract.
- Corroborated by: adversarial implementation, architecture and boundaries

### PR-002: Whether a repeated `auto-approve on` resets the review cap is unstated

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `spec.md §FR-001`, `research.md §3a`, `data-model.md §mode event`
  - `plan.md §Review-plan fixes` 2 and `§Walkthrough fixes` 1
- Finding: Fixed in the earlier review. The skip now reads the newest `mode`
  event, and the artifacts agree on it.
- Why it matters: The cap is the limit the record places on the agent's grant.
- Suggested response: Fixed by the sections above.
- Corroborated by: security and reliability, requirements and traceability

### PR-003: No named place for the rule that the agent grants only when a person asked

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Ownership` 5 and `§Review-plan fixes` 3
  - `spec.md §FR-012`
- Finding: Fixed in the earlier review, and still holds.
- Why it matters: It was the only control on the record's accepted case 1.
- Suggested response: Fixed by the sections above.
- Corroborated by: security and reliability, requirements and traceability

### PR-004: A partial grant can leave the mode on with no event

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `research.md §3a` Write order: the event is appended first, `mode.json`
    second, and either `OSError` prints `✗ Couldn't record the auto-approve
    change: <error>` and exits 1
  - `contracts/cli.md §wfctl auto-approve on`: the same error form and exit
  - `spec.md §Edge Cases`: the state dir case now states the order and the
    repair by the next `on` or `off`
  - `plan.md §Second review fixes` 2
- Finding: The write order and the error are stated, and a failed append
  changes nothing. PR-015 notes that the contract's output for the other half,
  a failed file write after `on`, disagrees with the spec.
- Why it matters: It produced the unattributed grant the feature makes visible.
- Suggested response: Fixed by the sections above.
- Corroborated by: single lens (security and reliability)

### PR-005: A hand-written mode file shows a stale change when older events exist

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `contracts/cli.md §wfctl auto-approve`: when the mode reads on and the
    newest `mode` event isn't a grant, the second line is `no grant on record`,
    including after a revocation
  - `spec.md §Edge Cases`: "even when an older grant or a revocation is in the
    event log"
  - `data-model.md §ModeChange`: `newest_is_grant` is read by both the skip and
    the bare command
- Finding: A hand-edited `mode.json` that reads on no longer shows an earlier
  change. PR-014 and PR-015 note two states the rewritten cases don't cover the
  way the other artifacts expect.
- Why it matters: The output attributed the mode to a session that didn't set
  it.
- Suggested response: Fixed by the sections above.
- Corroborated by: single lens (adversarial implementation)

### PR-006: The revoked mode line repeats "wfctl" and differs from `status`

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `contracts/cli.md §wfctl auto-approve`: `auto-approve off — <revocation
    reason>`, matching `_revocation_line`
  - `research.md §5`: the same form
  - `wfctl/cli.py` `_revocation_line`: `auto-approve off — {reason}`
- Finding: The doubled prefix is gone, and the line matches `status`.
- Why it matters: A test written against the contract would have pinned the
  doubled wording.
- Suggested response: Fixed by `plan.md §Second review fixes` 4 and the
  contract.
- Corroborated by: single lens (requirements and traceability)

### PR-007: The bare command is called read-only, and the context it resolves writes

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `contracts/cli.md §wfctl auto-approve`: looks up the state dir without
    creating it and skips the old-file cleanup; on a branch with no issue it
    reads that branch's state dir
  - `contracts/cli.md §wfctl auto-approve off`: no check runs, so it works on a
    branch with no issue
  - `wfctl/_paths.py` `resolve_agent_dir(create=False)` exists, and
    `extract_issue_key` returns `"unknown"` rather than exiting
- Finding: The read-only claim is now achievable, and the no-issue case is
  stated for both forms.
- Why it matters: A test of "never writes" would have failed against the
  obvious implementation.
- Suggested response: Fixed by `plan.md §Second review fixes` 5 and the
  contract.
- Corroborated by: single lens (adversarial implementation)

### PR-008: The creation hook inherits the launching session's identity

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `spec.md §Edge Cases`: the hook inherits the environment of whoever ran
    `workmux add`; an agent's run reads as "another session", a person's plain
    shell as "an unknown session"; the hook line doesn't clear identity
    variables because of `no-hardcoded-agent`
  - `auto-approve-grant-asks-first.md §Accepts` 6: the same relation
  - `plan.md §Second review fixes` 6
- Finding: The relation a creation-hook grant shows is stated and accepted,
  with its reason.
- Why it matters: User Story 2 exists so the user can tell how the mode was
  turned on.
- Suggested response: Fixed by the sections above.
- Corroborated by: single lens (security and reliability)

### PR-009: Nothing checks that Claude Code prompts on the ask rules, in the modes unattended sessions use

- Priority: MAJOR
- Category: Dependency / Feasibility
- Status: fixed
- Evidence:
  - `plan.md §Technical Context` Testing and `§Constitution Check`: a manual
    check that Claude Code prompts when the agent runs `wfctl auto-approve on`
    and `uv run wfctl auto-approve on`, in the default mode and in auto mode
  - `plan.md §Walkthrough fixes` 2 and `§Second review fixes` 1: ask rules
    prompt in every mode, `bypassPermissions` and auto mode included; `dontAsk`
    and headless `claude -p` deny instead, which leaves the mode off
  - `auto-approve-grant-asks-first.md §Defends against`: the same, plus that
    the auto mode classifier can't approve a call an ask rule matches
  - `auto-approve-grant-asks-first.md §Must keep catching`: forms 3 and 4
    (leading assignment, compound command) rest on the documented matcher
- Finding: The record states which modes ask and which deny, and both outcomes
  leave the mode off. The plan observes the prompt by hand in the two modes
  sessions here use. These statements agree with the documented behavior the
  review checked against. `spec.md §Validation Strategy` doesn't list the
  manual check, and the plan doesn't say where its result is written; neither
  forces a guess, since tasks are drawn from the plan.
- Why it matters: The control was asserted and never observed.
- Suggested response: Fixed by the sections above.
- Corroborated by: security and reliability, adversarial implementation

### PR-010: The deny rule's output names `cd`, and the plan says ask rules are treated "exactly" the same

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Walkthrough fixes` 2: the printed lines differ; each managed rule
    carries its own explanation; the announcement names the rules this run
    added rather than `DENY_RULE`
  - `contracts/cli.md §permissions.ask`: the `doctor` warning text for an ask
    rule, `it now denies:` or `it now asks for:` in the refusal, and the
    upgrade announcement text
- Finding: Every printed line on the shared path now has an ask-rule form, and
  an upgrade no longer re-announces `Bash(cd:*)`.
- Why it matters: The output gave a false reason on every existing repo at
  upgrade.
- Suggested response: Fixed by the sections above.
- Corroborated by: single lens (adversarial implementation)

### PR-011: The plan names no end-to-end tests for the ask rules

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Project Structure`: `tests/test_install_hook_merge.py` with the
    install refusal, `doctor` warning, and uninstall for a deleted ask rule,
    and the upgrade announcement
  - `plan.md §Second review fixes` 8
- Finding: The tests FR-015 and the record's form 5 need now have a named
  file, beside the deny rule's.
- Why it matters: A helper test observed none of the four call sites.
- Suggested response: Fixed by the sections above.
- Corroborated by: single lens (requirements and traceability)

### PR-012: The creation hook "isn't affected because the agent doesn't run it", and the agent usually runs `workmux add`

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §Walkthrough fixes` 2: neither a person nor an agent running
    `WFCTL_AUTO_APPROVE=1 workmux add` is prompted, and the record lists the
    agent's case as accepted
  - `auto-approve-grant-asks-first.md §Accepts` 6 and its paragraph: why no
    rule is added, since it would have to be `Bash(workmux add:*)`
  - `auto-approve-grant-asks-first.md §Must let through` 3: now "when a person
    runs it"
- Finding: The path is named and accepted with its reason, and the plan's
  sentence follows the record.
- Why it matters: It was an unlisted path around the new control.
- Suggested response: Fixed by the sections above.
- Corroborated by: single lens (security and reliability)

### PR-013: data-model.md says a grant is written only when the mode was off

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `data-model.md §mode event` 1: a grant is written when the mode was off, or
    when `mode.json` reads on and the newest `mode` event is not a grant
- Finding: The data model now states Walkthrough fix 1's rule.
- Why it matters: A test from the data model would have asserted no event in
  the hand-written case.
- Suggested response: Fixed by `data-model.md`.
- Corroborated by: single lens (requirements and traceability)

### PR-014: The bare command's second line has no case for a revoked mode, and research.md says it shows the grant

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `contracts/cli.md §wfctl auto-approve`: the second line is the last mode
    change a person made "when one is on record and it matches `mode.json`";
    the fallbacks are no change on record, mode on with the newest event not a
    grant, and mode off, not revoked, with the newest event a grant
  - `research.md §5`: after a revocation, the mode line is `_revocation_line`'s
    form, "Then the last mode change's line if one is on record", because "the
    person who granted the mode needs to see both that it stopped and who
    started it"
  - `wfctl/evidence/_mode.py` `revoke_auto_approve`: writes
    `{"auto_approve": false, "revoked": ...}` and an event with `by: "wfctl"`
- Finding: After the cap revokes, the last person's change is the grant, which
  set on, and `mode.json` reads off, so the grant doesn't match and the
  contract prints no second line. None of the three fallbacks covers the state
  either. research.md says the grant's line prints there. A hand edit to
  `{"auto_approve": false}` after a revocation is likewise covered by no case.
- Why it matters: The revoked state is the one a person reviewing an unattended
  run's PR is most likely to see, and User Story 2 exists to tell them who
  turned the mode on. The implementer has to pick between the two artifacts,
  and the test pins whichever they pick.
- Suggested response: Say in the contract that a revoked mode shows the last
  grant's line under the revocation line, or drop the sentence from
  research.md §5. Name what the line says for a mode off with no `revoked` and
  a revocation as the newest event.
- Corroborated by: single lens (adversarial implementation)

### PR-015: A failed file write after `on` prints "turned off outside wfctl", and the spec says "no grant on record"

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `spec.md §Edge Cases` first bullet: if the event lands and the file write
    fails, "the bare command says no grant is on record"
  - `data-model.md §mode event`: a failed file write after the append "leaves
    an event that `mode.json` doesn't match, which the bare command reports as
    no grant on record"
  - `contracts/cli.md §wfctl auto-approve`: "If the mode reads off, wasn't
    revoked, and the newest event is a grant", the line is `turned off outside
    wfctl`
  - `research.md §3a`: says "no grant on record" only for the failed `off`
- Finding: After a failed `on` from a mode that was off and not revoked, the
  newest event is the grant and `mode.json` still reads off, which is exactly
  the contract's "turned off outside wfctl" case. The spec and the data model
  say the bare command prints "no grant on record" for both halves. From a
  revoked mode, the same failure lands in PR-014's uncovered case.
- Why it matters: Two tests written from different artifacts expect different
  output for the same state. Low likelihood, and both outputs leave the mode
  off.
- Suggested response: Narrow the spec's and the data model's sentence to the
  failed `off`, and say a failed `on` reads as "turned off outside wfctl", or
  add a case to the contract.
- Corroborated by: single lens (adversarial implementation)

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Review-plan fixes 2, §Walkthrough fixes 1; research.md §3a; contracts/cli.md §on | covered |
| FR-002 | contracts/cli.md §off | covered |
| FR-003 | contracts/cli.md §bare; research.md §4, §5 | covered; PR-014, PR-015 |
| FR-004 | research.md §1; contracts/cli.md §on | covered |
| FR-005 | research.md §2; contracts/cli.md §on | covered |
| FR-006 | research.md §1 (`"unknown"` allowed) | covered |
| FR-007 | research.md §3; data-model.md §mode event | covered |
| FR-008 | research.md §8; contracts/cli.md §start | covered |
| FR-009 | plan.md §Project Structure (`test_auto_approve_command.py`) | covered |
| FR-010 | research.md §7; contracts/cli.md §.workmux.yaml | covered |
| FR-011 | research.md §6; data-model.md §Grant line | covered |
| FR-012 | plan.md §Ownership 5, §Review-plan fixes 3 | covered |
| FR-013 | plan.md §Project Structure (`using-wfctl`) | covered |
| FR-014 | research.md §3a; data-model.md §mode event | covered |
| FR-015 | plan.md §Walkthrough fixes 2, §Second review fixes 1, 7, 8; contracts/cli.md §permissions.ask | covered |
| SC-001 | contracts/cli.md §on | covered |
| SC-002 | test files and shell test in plan.md §Constitution Check | covered |
| SC-003 | research.md §3, §4 | covered |
| SC-004 | research.md §6; contracts/cli.md §bare | covered |
| SC-005 | plan.md §Project Structure | covered |
| Edge: unwritable state dir | research.md §3a; contracts/cli.md §on | covered; PR-015 for the bare output after a failed `on` |
| Edge: hand-written mode file | plan.md §Walkthrough fixes 1; contracts/cli.md §bare | covered |
| Edge: ended self-session | research.md §1; contracts/cli.md §on | covered |
| Edge: creation hook identity | spec.md §Edge Cases; record §Accepts 6 | covered |

## Assumptions challenged

- An `ask` rule prompts in every permission mode sessions here run in. Stated
  in the plan and the record, consistent with the documented behavior, and now
  observed by a manual check in the default and auto modes (PR-009).
- The documented exceptions, `dontAsk` and headless `claude -p`, fail closed.
  Stated in the plan and the record; both deny, so the mode stays off.
- "The next `on` or `off` repairs either" failed write. True. After a failed
  `off`, the mode reads on with an `off` event newest, so the next `on` writes
  a grant and `review_count` restarts. That is a fresh three reviews after a
  failed write, behind the ask prompt in Claude Code; low likelihood and not a
  finding.
- `append_event` raises on failure, so append-first can report the error.
  Verified in `wfctl/_io.py`, which opens the log without a guard.
- The bare command can resolve without creating on any branch. Verified:
  `resolve_agent_dir` takes `create=False`, and `extract_issue_key` returns
  `"unknown"` rather than exiting.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- The skip and the bare command both read `newest_is_grant`, so the two can't
  disagree on whether a grant stands behind the mode.
- Appending the event first means a failed write never leaves the mode on with
  no grant event, which was the unattributed-grant case.
- The record states which permission modes ask and which deny, and both fail
  closed, so the control's limits are written down rather than assumed.
- The ask rules reuse the deny rule's install, receipt, drift and uninstall
  path, with per-rule explanations, so the refusal over a deleted rule needs no
  new mechanism and prints no false reason.
- The plan keeps `approval-mode-is-stored-intent` unedited and puts the prompt
  in its own record, so the accepted record's checks stay where they were.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
