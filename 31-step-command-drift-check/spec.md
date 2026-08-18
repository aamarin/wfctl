# Feature Specification: step-command drift check

**Feature Branch**: `31-step-command-drift-check`
**Created**: 2026-08-17
**Status**: Draft
**Input**: Issue [#31](https://github.com/aamarin/wfctl/issues/31) — "Nothing checks that `_STEP_COMMAND` names commands wf-skills actually installs"

## Clarifications

### Session 2026-08-17

- Q: Does the check cover only command existence, or also that the pipeline's
  three step-keyed tables agree with each other? → A: Neither — merge the tables
  so they cannot disagree, then check only command existence.

  The issue describes one drift shape: the table naming a command that does not
  exist. Two more surfaced while specifying, both worse than the first and
  neither visible to a check aimed at it:

  - A step present in the step-name list but **missing from the command table**
    yields an empty command, and the caller reads empty as *finished* — it
    announces "Story complete" partway through the pipeline. Demonstrated by
    dropping `plan` from the table: the session is told to open a PR, with plan,
    tasks, analyze, decompose and implement never run.
  - A step missing from the **automation table** silently reads as "not
    automatable", so orchestration pauses where it was meant to proceed.

  The first answer considered was an assertion that the three tables share one
  key set. Rejected in favour of removing the possibility: the three tables
  become one, keyed by step, holding command and automation flag together, with
  the step-name list derived from it. A step cannot then be added without both
  values, because they are one literal.

  This leaves exactly one thing a data structure cannot guarantee — that the
  command a step names exists as a file — and that is what the check covers.
  Scope note: this makes the feature a small production change rather than the
  test-only change the design assumed.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Drift fails the build (Priority: P1)

A maintainer renames a bundled command file, or edits the step→command table, and
changes only one of the two. Today nothing notices: the table keeps naming a
command that no longer exists, and the first symptom is a session being told to
run something that answers to nothing — caught, if at all, by a human reading
output days later. After this change the disagreement fails the test suite on the
commit that introduces it.

**Why this priority**: It is the whole feature. Detection is the value; everything
else is presentation.

**Independent Test**: Point the check at a command set missing one of the table's
entries and confirm it fails; point it at the real set and confirm it passes.

**Acceptance Scenarios**:

1. **Given** every command named in the step table has a matching bundled command
   file, **When** the suite runs, **Then** the check passes and prints nothing.
2. **Given** a bundled command file is renamed and the step table is not updated,
   **When** the suite runs, **Then** the check fails and names the step and the
   command that no longer resolves.
3. **Given** the step table gains an entry for a command that was never bundled,
   **When** the suite runs, **Then** the check fails and names that entry.
4. **Given** a pipeline step is added, **When** the author omits its command or
   its automation flag, **Then** the omission is a syntax or type error at the
   step table itself — not a runtime behaviour anything needs to detect.

---

### User Story 3 - A step cannot exist without its command (Priority: P1)

A maintainer adds or renames a pipeline step. Today that means editing three
separate tables keyed by the same step names, and missing one is silent: omit the
command and the session is told the story is complete with five steps left; omit
the automation flag and orchestration pauses where it should have run. After this
change the three are one table, so a step carries its command and its flag or it
does not parse.

**Why this priority**: It removes the two worst drift shapes rather than
reporting them, and it is the reason the check itself stays small — everything a
data structure can guarantee is no longer the check's job.

**Independent Test**: Confirm the pipeline behaves identically for every existing
step, and that the step-name list, command lookup and automation lookup all
resolve from the single table.

**Acceptance Scenarios**:

1. **Given** the merged table, **When** any existing step is looked up, **Then**
   the command and automation flag returned match today's values exactly.
2. **Given** a step name absent from the table, **When** it is looked up,
   **Then** the result is the same empty command and non-automatable flag as
   today, preserving the "story complete" path for a genuinely finished pipeline.
3. **Given** the pipeline's step order, **When** it is derived from the merged
   table, **Then** it matches the previously hand-maintained order.

---

### User Story 2 - The failure names which side moved (Priority: P2)

A renamed command and a wrong table entry are different fixes — one edits the
table, the other restores or re-renames a file. A bare "missing" list leaves the
reader to work out which happened. The failure message distinguishes them.

**Why this priority**: Detection without attribution still saves the week; it just
costs the reader ten minutes. Valuable, not load-bearing.

**Independent Test**: Trigger a failure and assert the message carries both the
unresolved entries and the shipped command names, so the reader can see which of
the two moved.

**Acceptance Scenarios**:

1. **Given** the check fails, **When** the reader looks at the message, **Then**
   it names every unresolved entry and lists the commands that are shipped.
2. **Given** a command was renamed, **When** the reader compares the two lists,
   **Then** the new name is visible among the shipped commands — no separate
   candidate suggestion is needed or offered.

---

### Edge Cases

- **The bundled command directory is missing or empty** (a partial or broken
  install): every entry reads as missing and the check fails loudly. Failing is
  correct — a bundle with no commands cannot satisfy the table — and it must not
  pass vacuously.
- **Bundled commands that no step names** (`speckit.checklist`, `speckit.brief`,
  `speckit.orchestrate` today): not drift. These are legitimately not step
  commands, so the check ignores them in that direction permanently.
- **A repo that has installed no skills**: unaffected. The check reads the tree
  shipped inside the tool, never an installed repo, so it cannot fail for a repo
  that installed nothing.
- **A step missing its command**: the empty command it produces is read by the
  caller as "pipeline finished", so the session is told the story is complete
  while five steps remain — the most damaging shape of this drift and the least
  visible, because nothing errors. Made unreachable by the merged table rather
  than detected.
- **A genuinely complete pipeline**: also yields an empty command, and must keep
  printing "story complete". The merged table must not turn this into an error —
  the two cases are distinguished by the step name being absent, which after the
  merge can only mean completion.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST verify that every command named in the pipeline's
  step→command table has a corresponding command file in the tree shipped with the
  tool.
- **FR-002**: The verification MUST run automatically as part of the existing test
  suite, on every commit, without any install step or network access.
- **FR-003**: On disagreement, the report MUST name each step and the command that
  failed to resolve.
- **FR-004**: On disagreement, the report MUST let the reader distinguish a renamed
  command from a wrong table entry, by showing both the unresolved entries and the
  set of commands that are shipped. It MUST NOT nominate a single likely candidate:
  measured against realistic drift, similarity scoring names an innocent file more
  often than the right one (see `research.md` R1).
- **FR-005**: The check MUST be silent when the table and the shipped commands
  agree.
- **FR-006**: The check MUST read the real shipped command tree, not a test
  fixture standing in for it. The suite installs an autouse fixture that repoints
  the bundle location at a fake tree; a check subject to it would report every
  command missing.
- **FR-007**: The check MUST NOT report shipped commands that no step names.
- **FR-008**: A pipeline step MUST carry its command and its automation flag in a
  single definition, so that adding a step without either is impossible rather
  than merely detectable.
- **FR-009**: The pipeline's step order MUST be derived from that single
  definition rather than maintained separately.
- **FR-010**: Looking up a step name that is not defined MUST continue to yield an
  empty command and a non-automatable flag, preserving the existing "story
  complete" behaviour for a finished pipeline.

## Key Entities

- **Step definition table**: one entry per pipeline step, holding the slash command
  that advances it and whether orchestration may proceed unattended. The pipeline's
  step order derives from it. One side of the comparison.
- **Shipped command set**: the command files vendored into the tool's package. The
  other side of the comparison, and the authority on what actually exists.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A mismatch between the two sides is detected on the commit that
  introduces it, rather than by a person reading output — the #23 case took a week.
- **SC-002**: 100% of the eight step commands are covered by the check.
- **SC-006**: Two of the three drift shapes found during specification become
  impossible rather than detectable — a step cannot be defined without its command
  or its automation flag.
- **SC-003**: A reader seeing the failure can tell which side moved without opening
  either file.
- **SC-004**: The check adds no measurable time to the suite and requires no
  network, so it cannot become a flake that gets skipped.
- **SC-005**: Zero false positives against the shipped tree as it stands: the check
  passes on the current commit unmodified.

## Validation Strategy _(mandatory)_

- `uv run pytest` — the full suite, including the new check, passes.
- The new check passes against the real shipped tree: verified during design —
  23 shipped commands, 0 of the 8 table entries missing.
- Negative case, per the issue's Verification section: rename a shipped command,
  confirm the check fails and names the mismatch, restore it.
- The failure message asserted to contain both sides, so FR-004 is covered by
  assertion rather than by inspection.
- The merged step table returns today's exact command and automation flag for all
  eight steps, and the derived step order matches the previous hand-maintained
  list — the restructure is behaviour-preserving or it is a regression.
- `wfctl status` and `wfctl next` produce unchanged output on this branch, since
  both read the pipeline through the restructured table.
- `uv run mypy` — the project's type check, unchanged. Invoked exactly as CI does
  (`.github/workflows/ci.yml`); a narrower `mypy wfctl` checks a different file
  set than the gate that actually runs.

## Assumptions

- Pre-specify design context loaded from
  `specs/31-step-command-drift-check/design.md`. That document predates the
  clarification above and describes a test-only change; the merged step table
  supersedes it.
- The restructure is contained. Verified: the three tables are referenced from
  seven lines, all inside `_pipeline.py`, with no test and no other module
  reading them.
- The commands shipped with the tool are the authority on what exists. Verified:
  wf-skills was vendored into the package in `271bb2c` and the upstream repo is
  archived, so there is no longer a second source that could disagree.
- The runtime direction of this drift — a repo whose *installed* commands lag the
  shipped ones — is already covered by the existing content-hash check in
  `doctor`, which reports `skills stale — run install-skills`. This feature does
  not duplicate it.
- Whether `doctor` exits non-zero on drift stays out of scope, per the issue;
  that is [#41](https://github.com/aamarin/wfctl/issues/41)'s decision.
