# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | ebc35e9a4783c990cd4d19efa49fe1a4221660fc | technical strategy |
| spec.md | 3bcdde088920b7a5100f920662ff222bbb94561d | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | 4d8ca46eb24d58ca390eb8c9771522c11e831d93 | design-record index |
| docs/architecture/scans-live-in-spec-folder.md | c73458e7dbf74fe11d226504b17c28b2db267e4a | design record (proposed on this branch) |
| docs/architecture/the-scan-is-attested-where-the-reviewer-reads.md | f2cce1a1ee8a79e728bb639d4234b395129362fe | design record (superseded on this branch; status line only) |
| plan-review.plan.md | 8f51297eaf30e2557b7b126cfec4519dfa4dffe0 | base of this re-review |

## Review scope

- Re-review: the earlier report and the plan copy both exist, and the copy's
  identity equals the earlier report's `plan.md` row.
- Changed since the earlier report: `plan.md §Constitution Check` (complexity
  line) and `plan.md §Source Code` (`_evidence.py`, `_plan_review.py`,
  `cli.py`, `writing-a-scan-file`, the three wrappers, a new
  `opening-a-change` entry, AGENTS.md, a new `tests/conftest.py` entry, and the
  test list). Reviewed together with `plan.md §Summary`, `§Design records` and
  `§Structure Decision`, which name the helper and the path function.
- Inputs that no longer match the earlier report, re-read in full and the whole
  plan reviewed against each: `spec.md`, `design.md`, and
  `docs/architecture/scans-live-in-spec-folder.md`. The constitution is still
  absent. The superseded record is a new row, read for its status line only, to
  trace FR-010.
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification (with verification, risk,
  dependency and scope folded in as the rubric places them).
- Conditional lenses: security and reliability applied, for the earlier
  report's reason. The feature moves the one human-visible trace of two
  agent-written artifacts, the scan file and the plan sign-off, out of the pull
  request, and it now turns a held step from a stop into an automatic retry.
- Deterministic checks: `spec.md`, `plan.md` and `design.md` exist. No
  `[NEEDS CLARIFICATION` marker stands in `spec.md`. Every FR and SC traces to
  `plan.md` (table below). The plan, the spec, `design.md` and the record now
  agree on the command name, the routing, the texts, the fix lines, and where a
  sign-off reason is read.
- Existing code inspected: `wfctl/_evidence.py` (`Assessment` and its
  `renders`, `clarify`, `plan_review`, `analyze`, `CLARIFY_UNSCANNED`),
  `wfctl/_pipeline.py` (`_current_step_name`, `next_step_content`, the step
  construction and pass roll-up in `_infer_steps`, `_read_pass`, the routing in
  `build_report`, `collect_warnings`), `wfctl/_plan_review.py`
  (`append_sign_off`, `_events`, `sign_offs`, `review_count`), `wfctl/cli.py`
  (`_resolve_context`, `step_sign_off_cmd`, `_exception_findings`,
  `check_body_cmd`), `wfctl/_stall.py` (`COVERED`, `digest`),
  `tests/conftest.py` (`CLEAN_SPEC`, `write_plan_review`, `_STEP_ARTIFACTS`,
  `stage_upstream_of`), the mode table in
  `wfctl/agents/commands/plan-review.md §1`, the passages the plan cites in
  `speckit.analyze.md` and `speckit.clarify.md`, the exceptions bullet in
  `opening-a-change/SKILL.md`, and the session rule in
  `speckit-clarify/SKILL.md`.
- Reviewers: the lenses above, run in sequence by one agent.

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 3

No BLOCKER findings identified in this review. All ten earlier findings are
fixed. Three new MINOR findings remain: the plan's fixture change covers the
helpers but not the 61 call sites that write `CLEAN_SPEC` directly; the new
`/plan-review` mode row does not say whether it also matches a `done` pass that
carries the scan warning; and the switch from a stop to an automatic retry
names nothing that bounds a clarify run that keeps skipping its scan.

## Findings

### PR-001: The sign-off is named `review sign-off`, and the command is `step sign-off`

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-007` and `§User Story 4`: now name `wfctl step sign-off
    plan.plan-review`
  - `docs/architecture/scans-live-in-spec-folder.md §Consequences` and
    `design.md §MVP Scope`: the same verb
  - `plan.md §Source Code`: the `wfctl/cli.py` entry is headed `step sign-off`
  - `wfctl/cli.py`, `@step_app.command("sign-off")`: the command that takes
    `plan.plan-review`
- Finding: Every artifact named the plan-review sign-off by the verb of the
  review-group sign-off. All four now name the step sign-off.
- Why it matters: A test or AGENTS.md text written from the old name would have
  taught the person-only verb.
- Suggested response: Fixed by the revised spec, record, design and plan.
- Corroborated by: requirements and traceability, adversarial implementation

### PR-002: A held clarify or analyze is a blocked step, so an unattended run stops instead of being sent back

- Priority: MAJOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §Source Code`, `_scan_hold`: a held reading is
    `Assessment("in_progress", None, reason)`, with the text in `display`, and
    the plan says why
  - `spec.md §FR-005`, `design.md §Level 1` (`next: /speckit.clarify (auto)`),
    and the record's Consequences: the held reading carries no blocking reason
  - `wfctl/_pipeline.py`, `build_report`: `blocked` is the current step's
    `reason`, so a `None` reason routes through `next_step_content`'s last
    branch to the step's own command with its `_AUTOMATIC` flag
  - `wfctl/_pipeline.py`, `_infer_steps`: a step row takes
    `reading.renders()` as its annotation, so the display text still shows
  - `wfctl/_pipeline.py`, `_current_step_name`: the specify skip fires only on
    a marked spec, which the scan check never reaches, since clarify's marker
    branch comes first
- Finding: The plan used `reason` for the clarify and analyze holds, which
  made them blocked and never automatic. It now uses `display`, as plan review
  does, and the spec and record say the run is sent back.
- Why it matters: The design's case for the step reader rests on the run being
  sent back.
- Suggested response: Fixed by the revised `plan.md §Source Code` and
  `spec.md §FR-005`. PR-013 follows from it.
- Corroborated by: adversarial implementation, architecture and boundaries

### PR-003: The `/plan-review` wrapper has no mode for the three new held readings

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Source Code`, `plan-review.md §1`: a mode row for the three
    annotations that writes the scan section from the existing report, with no
    new review and no plan copy
  - `spec.md §FR-013`: the same requirement
  - `wfctl/_plan_review.py`, `review_count`: counts a `resume` whose report
    hash changed and each `sign-off` event, so a run that writes only the scan
    section leaves the report as it was and is not counted
- Finding: The wrapper had no row for the new readings and would have rerun a
  whole review for each. The plan now adds one, and the cap question answers
  itself, since the new mode writes no report.
- Why it matters: Each needless rerun spent a lap of the review cap.
- Suggested response: Fixed. PR-012 notes the `done` reading the new row does
  not clearly cover.
- Corroborated by: adversarial implementation, requirements and traceability

### PR-004: An agent's sign-off of the plan loses its only trace a person reads

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `spec.md §User Story 4` (scenario 4) and `§FR-012`: `wfctl check-body`
    reports a sign-off reason the PR body does not carry, and
    `opening-a-change` says to copy it
  - `docs/architecture/scans-live-in-spec-folder.md §Consequences`: names the
    loss and the PR body as its answer
  - `plan.md §Source Code`: `sign_off_reasons(agent_dir, branch)` in
    `_plan_review.py`, the `_exception_findings` addition in `cli.py`, the
    `opening-a-change` entry, and the AGENTS.md rule beside `step none`'s
  - `wfctl/cli.py`, `step_sign_off_cmd`: the `sign-off` event already carries
    `reason`, whitespace-collapsed, which is the form `_exception_findings`
    compares
- Finding: The sign-off's trace for a person was the scan section in the PR
  diff. It is now its reason in the PR body, checked the way a `step none`
  reason is, and the record says so.
- Why it matters: The sign-off is the one waiver of a BLOCKER.
- Suggested response: Fixed. The check reads every sign-off event on the
  branch, including ones over a plan a later review replaced; the plan says
  "each", which is a defensible reading.
- Corroborated by: security and reliability, architecture and boundaries

### PR-005: Wrapper and skill prose beyond the file lines still assumes the PR reviewer reads the scan

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Source Code`, the wrappers entry: every sentence saying the PR
    reviewer reads the scan changes, naming `speckit.analyze.md` around lines
    232, 287 and 333 to 341, and `speckit.clarify.md` around line 123; each
    cited line still holds the passage
  - `plan.md §Source Code`, `writing-a-scan-file`: the `#unknown` and
    out-of-tree refusals move under the evaluation section
- Finding: The passages that would have become false are now named, and the
  refusal that contradicted the new destination is scoped to evaluation.
- Why it matters: A self-contradicting wrapper is followed unevenly.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-006: The test fixtures that stage a finished step are not in the plan

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Source Code`, `tests/conftest.py`: a new `write_scan`, and
    `write_plan_review` and `stage_upstream_of` write the scans their steps
    produce
- Finding: The plan now names the helper change. What it leaves out is filed
  as PR-011.
- Why it matters: The helper choice decides how much of the suite changes.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-007: The reader keys on `- Verdict:`, and the shared skill does not require that form

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `spec.md §FR-014` and `plan.md §Source Code`, `writing-a-scan-file`: the
    skill states the `- Verdict: <value>` line and a coverage table as what the
    reader matches
- Finding: The line form is now stated where writers are told.
- Why it matters: A differently written Verdict line would have held the step.
- Suggested response: Fixed. The `scan file has no verdict` text still does
  not name the form, which the earlier response offered as optional.
- Corroborated by: adversarial implementation

### PR-008: The held and warning texts differ between design.md, the spec, and the plan

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Source Code`: the three constants as display text in all three
    steps, and `_scan_hold`'s `remedy=f"  run {command}"` on every warning
  - `spec.md §FR-005`, `§FR-006`, and `design.md §Level 1`: the same three
    texts and the same three fix lines
  - `wfctl/_pipeline.py`, `_infer_steps`: a step without an outstanding pass
    takes `reading.remedy`, and `collect_warnings` carries it
- Finding: The three artifacts now give one rendering, and every warning has
  its fix line.
- Why it matters: Tests pin console output.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-009: Whether the sign-off still refuses a branch with no issue key is unstated

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `spec.md §FR-007` and `§User Story 4` (scenario 5): no refusal, and a
    heading that names no issue
  - `plan.md §Source Code`: the refusal is dropped, and with issue `unknown`
    the heading is `# Plan review scan`
- Finding: Answered in both the spec and the plan.
- Why it matters: A test pins the current refusal, and the plan lists that
  test file.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-010: The fallback for older features is permanent, so SC-002 holds only for in-order runs

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `spec.md §SC-002`: now scoped to runs in pipeline order, and names the
    out-of-order run's warning as the trade the clarify reader already makes
- Finding: The success criterion now promises what the readers deliver.
- Why it matters: SC-002 had overstated the check.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-011: Tests that write `CLEAN_SPEC` or an analysis report directly fall outside the fixture change

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `plan.md §Source Code`, `tests/conftest.py`: "Every test that stages these
    steps through the helpers keeps passing"
  - `tests/conftest.py`, `CLEAN_SPEC`: a constant, written into `spec.md`
    directly by 61 call sites in 13 test files outside `conftest.py`, most in
    `test_storyctl.py` (24), `test_pipeline_state_names.py` (12) and
    `test_pipeline_commands.py` (8)
  - nine test files name `analysis-report.md`
- Finding: The plan's claim covers only the helpers. A test that writes
  `CLEAN_SPEC` with no `plan.md` now reads clarify held where it expected it
  done, and one with `plan.md` gains a `no scan file` warning in output it may
  pin. The plan does not say whether those call sites gain a `write_scan` call
  or have their expectations changed.
- Why it matters: It is the same choice PR-006 asked about, at the call sites
  the helpers do not reach, and the state-name and command tests sit among
  them.
- Suggested response: Say which, for example that every direct `CLEAN_SPEC`
  writer also calls `write_scan(spec_dir, "clarify")`, and that a test whose
  subject is the warning stages without it.
- Corroborated by: adversarial implementation

### PR-012: The new `/plan-review` mode row doesn't say whether it matches a `done` pass carrying the scan warning

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `plan.md §Source Code`, `plan-review.md §1`: "a mode row for `no scan
    file`, `scan file has no verdict`, and `scan file has no coverage rows`",
    with no state named
  - `spec.md §FR-013`: the scan-only mode applies "when the plan review pass
    holds"
  - `spec.md §FR-006` and `design.md §Level 1`: a feature with `tasks.md` and
    no scan reads `done` with the warning and the fix line `run /plan-review`
  - `wfctl/_pipeline.py`, `_pass_states`: a `done` pass's annotation is
    `renders()`, which is its reason, so the wrapper sees `done` with
    annotation `no scan file`
  - `wfctl/agents/commands/plan-review.md §1`: `done` maps to a re-review
- Finding: The warning's fix line sends the reader to `/plan-review`, and the
  wrapper's existing `done` row runs a whole re-review. The plan's new row
  names the annotations without a state, so one implementer puts it ahead of
  the `done` row and writes only the scan section, and another leaves the
  `done` row to win.
- Why it matters: Small, since it touches only features planned before this
  change, but the two readings differ in whether the fix line costs a review.
- Suggested response: Say in the plan which state the new row matches, and
  whether a `done` pass with a scan warning writes the section only.
- Corroborated by: adversarial implementation

### PR-013: Nothing named bounds an unattended clarify run that keeps skipping its scan

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `plan.md §Source Code`, `_scan_hold`: a held reading is automatic, so the
    loop re-runs the step's command on its own (PR-002's fix)
  - `wfctl/_stall.py`, `COVERED = ("spec.md", "plan.md", "tasks.md")`: the
    stall detector fires only while those three files stay byte-identical
  - `speckit-clarify/SKILL.md`: a clarify run that asks questions appends its
    answers under the session heading in `spec.md`
- Finding: Before the revision a missing scan would have stopped the run, and
  now it re-runs the step. An analyze or plan-review rerun leaves the three
  covered files as they were, so the stall detector ends a loop there. A
  clarify rerun that edits `spec.md` each time changes the digest, and the plan
  names nothing else that ends the loop.
- Why it matters: The case needs an agent that repeatedly skips the scan,
  which is the agent this check exists for. The cost is an unattended run that
  spends its context re-clarifying.
- Suggested response: State what bounds it: the stall detector as it stands,
  with that limit named, or the scan file added to what `_stall.digest` reads.
- Corroborated by: security and reliability

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Source Code, `writing-a-scan-file` and the three wrappers | covered |
| FR-002 | plan.md §Source Code, wrappers' commit sentences and allowed-tools | covered |
| FR-003 | plan.md §Source Code, the skill's Evaluation section | covered |
| FR-004 | plan.md §Source Code, `scan_reason` | covered |
| FR-005 | plan.md §Source Code, `_scan_hold` held arm | covered; PR-013 |
| FR-006 | plan.md §Source Code, `_scan_hold` warning arm and the three callers | covered; PR-012 |
| FR-007 | plan.md §Source Code, `wfctl/cli.py` step sign-off and `_plan_review.py` | covered |
| FR-008 | plan.md §Source Code, `scan_reason` matches all three values alike | covered |
| FR-009 | plan.md §Source Code, `_paths.py` | covered |
| FR-010 | plan.md §Design records | covered; the superseded record reads `status: superseded` |
| FR-011 | plan.md §Source Code, AGENTS.md | covered |
| FR-012 | plan.md §Source Code, `sign_off_reasons`, `_exception_findings`, `opening-a-change` | covered |
| FR-013 | plan.md §Source Code, `plan-review.md §1` | covered; PR-012 |
| FR-014 | plan.md §Source Code, `writing-a-scan-file` | covered |
| SC-001 | wrappers and skill | covered |
| SC-002 | readers | covered |
| SC-003 | readers' later-artifact check | covered |
| SC-004 | Constitution Check, the scan walked through the new path | covered by the walk-through, not by a test |

## Assumptions challenged

- A held reading with no reason routes automatically. Explicit in the plan,
  and verified against `build_report` and `next_step_content`.
- A scan-only `/plan-review` run does not count toward the cap. Not stated, and
  true of `review_count` as written, since the run leaves the report's hash as
  it was.
- The `sign-off` event carries the reason `check-body` needs. Not stated, and
  true: `step_sign_off_cmd` appends `reason=` to the event.
- `wfctl store specs` saves the whole folder, `scans/` included. Still assumed
  in `design.md §Level 3`, and verified only by the walk-through.
- A clarify loop ends on its own. Not stated (PR-013).

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- One private helper, `_scan_hold`, gives all three steps the same held and
  warning arms, so the routing fix for PR-002 lands once.
- `_paths.spec_scan` stays the one path both the sign-off and the readers use.
- The sign-off reason is checked by the mechanism `step none` reasons already
  use, rather than by a new one.
- The check still reads shape and leaves the verdict's value to #100.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
