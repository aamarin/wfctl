# Research: Security control threat model

## R-001: Where the threat model's shape lives

- Decision: one reference, `architecture-decisions/references/threat-model.md`,
  linked from `design-levels` and `reviewing-security`.
- Rationale: the threat model is a section of a level-2 record, and
  `architecture-decisions` owns the record format. One file means a change to
  the section edits one place, and the heading test catches a reviewer that
  falls behind.
- Alternatives considered: a description-triggered `threat-modeling` skill,
  which can fail to fire at the one point the step has to run. A
  `threat-model-template.md` beside `record-template.md`, equally sound but a
  second template for what's a section. The section in `record-template.md` for
  every record, which leaves an empty section on most records.
  (`design/799-threat-model-in-the-record.md`)

## R-002: How the reviewer finds the threat model

- Decision: the reviewer runs `wfctl arch-root` and searches that folder at the
  run's head for `## Threat model`, with `git grep -l '^## Threat model' <head> -- <arch-root>`.
  It reads each hit's `governs` field and Decision, and keeps the records whose
  control the commits change.
- Rationale: `reviewing-security` already allows read-only commands, and
  `git grep` at the head reads the branch's proposed records as well as the
  trunk's accepted ones, without the working tree. `wfctl arch context` prints
  only accepted records and only the first paragraph of Decision, so it would
  miss a threat model proposed on the same branch.
- Alternatives considered: `wfctl arch context --all`, which leaves out
  proposed records. The coordinator naming the records, rejected at clarify.

## R-003: How the accept-check test reads the record

- Decision: the test reads `docs/architecture/accept-check-threat-model.md`
  from the repository root, splits it at `### ` headings, and takes the first
  last backtick span of each numbered item under `Must keep catching` and
  `Must let through`. It runs each through `_review_gate.read` and checks
  `ACCEPT_REFUSAL` is or isn't among the refusals.
- Rationale: `tests/test_arch_records.py:654` already reads this repository's
  `docs/architecture` the same way. The last span, not the first, because five
  items name `--dry-run` in their description before the form. The forms hold
  no backtick, so the last code span is the whole command.
- Alternatives considered: copying the forms into the test's own parameter
  list, which leaves two lists to keep in step and loses the point of the
  test. Reading `Accepts` too and asserting each passes, rejected since a
  future tightening that catches an accepted form is fine and shouldn't fail.
- Check: the test also asserts each list is non-empty, so a renamed heading
  can't turn it into a test of nothing.

## R-004: How `design-passes` states the trigger

- Decision: one paragraph under the design-decision question, after the five
  categories, naming the trigger ("adds, removes, loosens, or tightens a
  security control"), what a security control is, and the reason it's a yes.
- Rationale: `every-change-answers-spec-question.md` is accepted with three
  questions, and the safety category already covers this. The paragraph makes
  the yes explicit so #792's "no significant design decision" can't recur.
- Alternatives considered: a fourth question, rejected in
  `security-change-needs-threat-model.md`.

## R-005: What the reviewer's report carries

- Decision: a `Judged against:` line per record under the `## security-and-hardening`
  heading, naming the record path and its status. A form inside `Accepts` goes
  under the line as a note, not as a finding. A control change with no threat
  model is a finding titled "Security control changed with no threat model".
- Rationale: wfctl counts a report by its `Reviewed:` line and its last-line
  verdict only (`reviewing-security`), so an extra line changes no count.
- Alternatives considered: a separate report section, which adds a heading
  the coordinator's reconciliation doesn't expect.
