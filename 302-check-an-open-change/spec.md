# Feature Specification: check an open change

**Feature Branch**: `302-check-an-open-change`
**Created**: 2026-09-09
**Status**: Draft
**Input**: Issue #302 — "An open PR's sidebar is prose in a skill, so it is skipped and nothing disagrees." Pre-specify design context loaded from `design.md` in this feature directory.

## Clarifications

### Session 2026-09-09

- Q: What bounds the two tracker calls the check makes? → A: 15s per call,
  matching the bound the existing tracker read already carries.
- Q: The change's fields read fine but the issue's read fails — what does the
  check do? → A: report the failure, print what could still be checked, and exit
  non-zero.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Find out what the change is missing (Priority: P1)

Someone has just opened a change. The description is written, the checks pass,
and every attribute beside it is blank — no labels, no owner, not on the board.
Today nothing says so, and the omission surfaces days later when a person happens
to look. They run one command against the open change and are told, field by
field, what is unset and where the expectation came from.

**Why this priority**: This is the whole feature. Without it the rule stays prose
and keeps being skipped, which is the recorded history across several worktrees.

**Independent Test**: Open a change with an empty sidebar, run the command, and
confirm it names every field that the issue carries or the repository requires.
Fill those fields, run it again, and confirm it goes quiet. The second half is
what proves the check can pass.

**Acceptance Scenarios**:

1. **Given** an open change whose issue carries a label the change does not,
   **When** the check runs, **Then** it reports that field as a finding, names
   the value the issue carries, and exits non-zero.
2. **Given** an open change carrying every field its issue carries and every
   field the repository requires, **When** the check runs, **Then** it reports
   each of those fields as satisfied and exits zero.
3. **Given** an open change whose labels include the ones its issue carries plus
   one earned in its own right, **When** the check runs, **Then** the extra label
   is not a finding — the comparison asks whether the issue's set is covered, not
   whether the two sets are equal.

---

### User Story 2 - Say nothing about fields this repository does not use (Priority: P1)

Someone works in a repository whose triage they do not control, and in another
where they assign every change to themselves. The same command runs in both. In
the first it never mentions an owner, because nothing there ever said an owner
was expected. In the second a blank owner is a finding, because the repository
said so in a file that is committed and reviewable.

**Why this priority**: Equal to Story 1, and inseparable from it. A check that
reports every blank field is noisy, and a noisy check is learned around and then
ignored — which loses the prose and the check together.

**Independent Test**: Run the check in a repository that declares no
requirements, against an issue with no fields set, and confirm it reports nothing
and exits zero. Add one required field, run it again, and confirm exactly that
field is now reported.

**Acceptance Scenarios**:

1. **Given** a repository that declares no required fields and an issue with no
   fields set, **When** the check runs, **Then** it reports that there was
   nothing to check, and exits zero.
2. **Given** a repository that declares one required field, **When** that field
   is blank on the change, **Then** it is reported as required by the repository
   rather than as inherited from the issue.
3. **Given** a repository that declares a required field the tracker never
   reports, **When** the check runs, **Then** it reports the mismatch by name and
   exits non-zero, rather than silently treating the field as satisfied.
4. **Given** a tracker that does not implement the field-reading capability,
   **When** the check runs, **Then** it says so and exits zero.

---

### Edge Cases

- The branch carries no issue key, so there is nothing to inherit from. Required
  fields are still checked; the absence of an issue is stated, not treated as a
  failure.
- The change identifier names a change that does not exist, or the tracker call
  fails or exceeds its bound. The failure is reported with what the tracker said,
  and is distinct from the tracker having declined the capability.
- One read returns and the other does not. Whatever the returned read makes
  checkable is still reported, alongside the failure, and the run exits non-zero —
  a run that saw half of what it needed never looks like a clean one.
- No tracker is configured at all. Nothing is checked and nothing fails.
- The tracker's field-reading command returns a nested structure rather than
  plain values. This is a misconfiguration and is reported as one, naming the
  configuration file — never surfaced as a crash.
- A field is set on the change but neither required nor present on the issue. It
  is not reported at all, in either direction.
- A field is a single value on one side and a list on the other. The comparison
  is chosen from the shape the tracker returned, not from the field's name.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST report, for one open change, which fields carry an
  expectation and are unset on that change.
- **FR-002**: The system MUST treat a field as expected when the repository
  declares it required, or when the branch's issue has that field set.
- **FR-003**: The system MUST report nothing about a field that is neither
  declared required nor set on the issue.
- **FR-004**: The system MUST obtain field names and values from the configured
  tracker, and MUST NOT contain any tracker-specific field name of its own.
- **FR-005**: The system MUST read the repository's required-field declaration
  from a file that is committed to the repository, so that the declaration
  survives reinstallation of generated configuration.
- **FR-006**: The system MUST report a required field that the tracker does not
  report at all as a finding, naming both what was required and what the tracker
  reports.
- **FR-007**: For a field whose value is a list, the system MUST report it as a
  finding when the issue's values are not all present on the change, and MUST NOT
  report additional values on the change as a finding.
- **FR-008**: For a field whose value is a single value, the system MUST report it
  as a finding only when it is unset on the change.
- **FR-009**: The system MUST exit non-zero when it reports at least one finding,
  and zero otherwise.
- **FR-010**: The system MUST distinguish, in its output, a field it verified and
  found satisfied from a field it could not check at all.
- **FR-011**: The system MUST continue without failing when no tracker is
  configured, when the tracker does not implement field reading, or when the
  branch carries no issue key.
- **FR-012**: The system MUST report a tracker whose field-reading command returns
  values it cannot compare as a configuration problem, naming the configuration
  file.
- **FR-013**: The system MUST validate a tracker configuration that declares the
  field-reading capability, and MUST reject one that declares a capability the
  contract does not define.
- **FR-014**: The skill that governs opening a change MUST invoke the change check
  as a step, in the same manner as it already invokes the description check.
- **FR-015**: Each read the system makes from the tracker MUST be bounded at 15
  seconds, the same bound the existing tracker read carries, so that a skill
  invoking the check unattended cannot hang on an unreachable tracker.
- **FR-016**: When a read the system attempted does not return, the system MUST
  report the failure with what the tracker said, MUST still report whatever it
  could check without that read, and MUST exit non-zero. A read that failed MUST
  NOT be treated as a source that had nothing to say.

## Key Entities

- **Change**: an open unit of work under review — a pull request, a patchset. It
  carries fields beside its description, and those fields are what is checked.
- **Issue**: the tracked work the change answers to, identified by the branch's
  name. Its fields are one of the two sources of expectation.
- **Required-field declaration**: a committed, per-repository list naming which
  fields must be set on a change regardless of what the issue carries.
- **Field payload**: the flat set of field names and values a tracker reports for
  one change or one issue. Names and shapes are the tracker's; the system reads
  them as plain values.
- **Finding**: one field, the expectation behind it, and which source stated that
  expectation.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A change opened with no fields set, in a repository whose issue
  carries fields, produces at least one finding and a non-zero exit.
- **SC-002**: The same change, after its fields are set, produces no findings and
  a zero exit. Both halves are required; only the second shows the check can pass.
- **SC-003**: In a repository that declares no required fields and whose issue has
  none set, the check produces no findings and names no field.
- **SC-004**: No field name belonging to any particular tracker appears in the
  system's own source, verifiable by searching it.
- **SC-005**: Every state the check can reach — findings, satisfied, nothing to
  check, tracker declined, no tracker, no issue key, misconfigured payload, a read
  that failed, a read that exceeded its bound — terminates with an exit code and a
  message, and none produces a stack trace.
- **SC-006**: Every field the branch's issue carries and the change does not is
  named on a single run — the check never reports one field per invocation.
- **SC-007**: An unreachable tracker returns the check within a bounded time
  rather than hanging, and the run that hit the bound exits non-zero.

## Validation Strategy _(mandatory)_

The repository's declared definition of done, all four:

```
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
uv run wfctl doctor
uv run wfctl verify
```

Story-specific validation beyond that:

- Unit coverage over the comparison, exercising each state named in SC-005 with
  the payload supplied directly, so the states are testable without a tracker.
- Contract validation that a tracker configuration declaring the field-reading
  capability passes, and one declaring an undefined capability is rejected.
- A live exercise, which no unit test can substitute for: open a throwaway change
  with an empty sidebar, run the check, confirm it names every unset field, then
  set them and confirm it goes quiet. An exercise that ran only the first half has
  not tested that the check can pass.
- A change to any installed skill requires reinstalling skills and exercising the
  changed skill by hand; the suite checks that skills ship, not that they read
  correctly.

## Assumptions

- Pre-specify design context loaded from `design.md` in this feature directory.
  Its decisions are treated as settled: the two-source expectation model, the
  tracker owning field vocabulary and payload shape, invocation rather than
  automatic running, and the finding-or-silence severity split.
- The branch's issue is the correct comparison target. The change identifier is
  supplied by the caller, and the skill that invokes the check supplies the change
  it has just created, so the two agree by construction.
- Issue #306 — a decision record whose `Considered` section is empty passes every
  check — was found during this feature's design pass and is filed separately. It
  is **not** in this change: `speckit-delivery-plan` holds that one PR closes
  exactly one issue, and the two share no code, so #306 goes to its own branch
  off `main` rather than a stack. Nothing here depends on it.
