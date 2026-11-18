# Feature Specification: Security control threat model

**Feature Branch**: `799-security-control-threat-model`
**Created**: 2026-11-18
**Status**: Draft
**Input**: User description: "#799: a change that adds, removes, or narrows a security control gets a threat model before code, as a section of a level-2 record the user accepts, and the security reviewers judge findings against it. design.md in the feature dir holds the direction."

## Clarifications

### Session 2026-11-18

- Q: Does a change that makes a control stricter need a threat model too? → A: Yes. Any change to what a control refuses or lets through counts, so the trigger is "adds, removes, loosens, or tightens".
- Q: What does the reviewer do with a form in none of the record's lists? → A: Judge it by "Defends against": a finding if that agent could reach it, a note otherwise, and either way ask for it to be added to a list.
- Q: Does the coordinator name the threat-model record in the brief? → A: No. The reviewer finds it by its heading.

## User Scenarios & Testing _(mandatory)_

A security control is a check that keeps an action with a person or keeps an
untrusted input out. In wfctl these are the worktree guard's refusals, the
terminal checks on `review sign-off`, `arch accept`, and `arch approve-imports`,
the `review` job on GitHub with its import check, and reading the reviewer
commands and round cap from the trunk.

### User Story 1 - The author writes a threat model before code (Priority: P1)

An agent starts a change that narrows a security control, such as loosening the
guard's accept check so it stops refusing commit messages. Step 1 of the design
passes sends the change through the spec pipeline. At level 2 the design skills
tell the agent to write a threat model as a section of the change's record,
following one reference, before any code. The user accepts the record.

**Why this priority**: #792 recorded "no significant design decision" for a
change that narrowed a control, and nothing asked for a threat model. Without
this story the other two have nothing to judge against.

**Independent Test**: Walk a pretend control change through the installed
`design-passes` and `design-levels` skills, and check that the agent reaches the
threat-model reference before any code.

**Acceptance Scenarios**:

1. **Given** a change that narrows the guard's accept check, **When** the agent
   answers step 1 of `design-passes`, **Then** the design-decision question reads
   yes and names the security control as the reason.
2. **Given** that change at level 2 of `design-levels`, **When** the agent writes
   its record, **Then** the skill sends it to the threat-model reference, and the
   record carries a `## Threat model` section with "Defends against", "Must keep
   catching", and "Accepts" parts.
3. **Given** a change that touches a control's file without changing what it
   refuses or lets through, such as a rename, **When** the agent answers step 1,
   **Then** the security sentence doesn't apply.
4. **Given** a change that makes a control stricter, so it refuses a form it let
   through before, **When** the agent answers step 1, **Then** the security
   sentence applies, the same as for a narrowing.

---

### User Story 2 - The security reviewer judges against the record (Priority: P1)

The coordinator starts the security group and sends each reviewer its id and
reports folder, with no security bar of its own. Each reviewer finds the threat
model for the control the commits change, judges each finding against it, and
names the record in its report. A form inside the record's "Accepts" list isn't
a finding. A change to a control with no threat model is a finding.

**Why this priority**: This is the loop #792 ran. A bar written fresh for each
run disagreed with the accepted one, and three rounds chased forms the guard
had already given up.

**Independent Test**: Read the installed `reviewing-security` and
`fanning-out-code-review` skills as a reviewer and as a coordinator would, on a
pretend control change, and check what each one says to do.

**Acceptance Scenarios**:

1. **Given** commits that change the accept check, **When** a security reviewer
   follows `reviewing-security`, **Then** it finds `accept-check-threat-model.md`
   by its `## Threat model` heading and names it in the report.
2. **Given** a form listed under "Accepts", **When** the reviewer finds that the
   change lets it through, **Then** the reviewer doesn't report it as a finding.
3. **Given** a form listed under "Must keep catching", **When** the change lets it
   through, **Then** the reviewer reports a finding and requests changes.
4. **Given** commits that narrow a control no record has a threat model for,
   **When** the reviewer follows the skill, **Then** it reports a finding saying
   the control changed with no threat model.
5. **Given** a coordinator following `fanning-out-code-review`, **When** it writes
   a security reviewer's brief, **Then** the skill tells it not to state a
   security bar or name the record, since the reviewer finds the record itself.
6. **Given** a form the change lets through that's in none of the record's lists,
   **When** the reviewer judges it, **Then** it reports a finding if an agent the
   "Defends against" part describes could reach the form, and a note otherwise.
   Either way it asks the author to add the form to a list.

---

### User Story 3 - The guard's threat model is a record (Priority: P2)

The accept check's threat model moves from research note R-013 into
`accept-check-threat-model.md`. `wfctl arch context` prints it on a branch that
lists the worktree guard, evidence and derivation, or architecture records. The
record lists the forms the check must keep catching, the forms it accepts, and
the ordinary commands it must let through. A test runs every listed form through
the guard.

**Why this priority**: It's the first record the new step produces, and #792's
fix needs it, but the step works without it.

**Independent Test**: Run the new test, then change one "Must keep catching"
entry to a form the guard lets through and check that the test fails.

**Acceptance Scenarios**:

1. **Given** the record, **When** the test runs each "Must keep catching" form
   through the guard, **Then** the guard refuses every one.
2. **Given** the record, **When** the test runs each "Must let through" form,
   **Then** the guard refuses none of them.
3. **Given** an entry added to either list, **When** the suite runs, **Then** the
   new entry is tested with no change to the test.

---

### Edge Cases

- A change adds a new control. The threat model is written the same way, and its
  "Must keep catching" list is the control's first tests.
- A change removes a control. The record's threat model says what the removal
  gives up, and "Must keep catching" is empty.
- The threat model is on the same branch and still proposed. The reviewer judges
  against it and says it's proposed.
- A record lists a form in "Must keep catching" that the guard lets through
  today. The test fails, which is the regression signal.
- A repository other than wfctl gets the skills but not the test that reads the
  accept check's record.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: Step 1 of `design-passes` MUST say that a change that adds,
  removes, loosens, or tightens a security control answers the design-decision
  question yes, and why. A change that leaves what the control refuses and lets
  through unchanged, such as a rename, doesn't count.
- **FR-002**: Level 2 of `design-levels` MUST send a security control change to
  the threat-model reference before any code.
- **FR-003**: The `architecture-decisions` skill MUST ship one reference that
  defines the `## Threat model` section and its four parts: "Defends against",
  "Must keep catching", "Accepts", and the optional "Must let through".
- **FR-004**: The reference MUST say that each "Must keep catching" form gets a
  test that fails if the control lets it through.
- **FR-005**: `reviewing-security` MUST tell the reviewer to find the threat model
  for each control the commits change, judge each finding against it, and name
  the record it judged against.
- **FR-006**: `reviewing-security` MUST say that a form inside "Accepts" isn't a
  finding, a "Must keep catching" form let through is one, and a "Must let
  through" form refused is one. A form in none of the lists is a finding when an
  agent the "Defends against" part describes could reach it, and a note
  otherwise, and either way the reviewer asks for it to be added to a list.
- **FR-007**: `reviewing-security` MUST report a change to a security control
  with no threat model as a finding.
- **FR-008**: `fanning-out-code-review` MUST tell the coordinator not to state a
  security bar or name a threat-model record in a reviewer's brief.
- **FR-009**: The suite MUST check that the reference and `reviewing-security`
  name the same four headings.
- **FR-010**: The suite MUST run every form in the accept check's "Must keep
  catching" and "Must let through" lists through the guard and check each result.
- **FR-011**: `accept-check-threat-model.md` MUST carry R-013's decision, its
  accepted gap, and both lists.
- **FR-012**: The branch MUST commit a release note for #799.
- **FR-013**: When the branch under review changes the lists of a threat model
  that's accepted on the trunk, `reviewing-security` MUST judge against the
  trunk's lists and report any form moved out of "Must keep catching" or into
  "Accepts" as a finding, since only the user moves the bar.

### Key Entities

- **Threat model**: a `## Threat model` section in a level-2 record, with four
  parts. The user accepts it with the record.
- **Security control**: a check that keeps an action with a person or keeps an
  untrusted input out.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A walkthrough of a pretend control change reaches the threat-model
  reference at level 2, before any code, in 1 pass with no prompting.
- **SC-002**: All 20 "Must keep catching" forms are refused and all 8 "Must let
  through" forms run, as checked by the suite.
- **SC-003**: The security group on this branch names the record it judged
  against in each of its reports.
- **SC-004**: Removing one heading from `reviewing-security` fails the suite.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy`.
- `uv run wfctl doctor` and `uv run wfctl arch accept --dry-run` on each new
  record.
- `uv run wfctl install-skills`, then a walkthrough of a pretend control change
  through the installed skills.
- A mutation check: break one listed form and one heading, and confirm the
  matching test fails.

## Assumptions

- Pre-specify design context loaded from `design.md` in the feature's spec folder.
- The three spec questions stay three, since `every-change-answers-spec-question.md`
  is accepted with three. The security case sits inside the design-decision
  question.
- `security-and-hardening` stays unedited, since it's vendored.
- Threat models for `review sign-off` and `arch approve-imports` are out of scope.
- #792's false refusals are out of scope, and its fix adds forms to the "Must
  let through" list.
