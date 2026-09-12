# Feature Specification: install-skills source

**Feature Branch**: `146-install-skills-source`
**Created**: 2026-09-05
**Status**: Draft
**Input**: Issue #146 — "install-skills has one hardcoded source, so a branch, a PR, and a hand-placed skill are all unreachable"

## Clarifications

### Session 2026-09-05

- Q: What does a default install record as its source? → A: A sentinel meaning "the default" — no location is stored, and the freshness check keeps today's behavior for those installs.
- Q: Does a recorded source persist across later installs that name none? → A: No. Naming a source affects only the install it is given on; a later install that names none uses the default and overwrites the record.
- Q: When a bare install replaces a named-source install, should the installer say so? → A: Yes — print a line naming the source being replaced, then proceed. It must survive the non-interactive path.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Install skills from a checkout you name (Priority: P1)

Someone wants the skills from a specific checkout of the tool — a pull request
they are reviewing, a colleague's branch, or a development tree — installed into
the project they are working in. Today the installer only ever copies from the
copy of the tool that is running, so there is no way to ask for this. They name
the checkout, the install copies from there, and the record of the install says
where it came from.

**Why this priority**: This is the capability the feature exists to add. Nothing
below is reachable without it, and for a project that has no development tree of
its own there is currently no mechanism at all.

**Independent Test**: Point an install at a checkout that differs from the
running tool's, then confirm the installed files match that checkout and the
freshness check reports the project as current rather than drifted.

**Acceptance Scenarios**:

1. **Given** a project and a second checkout whose skills differ from the running
   tool's, **When** the user installs naming that checkout, **Then** the
   installed files match the named checkout, not the running tool.
2. **Given** that install has completed, **When** the user runs the freshness
   check, **Then** it reports the project as current and names the source it was
   installed from.
3. **Given** a user who names no source, **When** they install, **Then** behavior
   is identical to today's — the running tool is the source, and the freshness
   check output is unchanged.

---

### User Story 2 - Be told when the named source has moved on (Priority: P2)

Someone developing a skill edits it in their checkout, installs, tests, and edits
again. The installed copy is now behind the checkout it came from. Nothing
watches for this, so the next test silently exercises the previous version. The
freshness check should notice, and the repair it offers should reinstall from the
same source rather than replacing it with the released one.

**Why this priority**: This is the loop a person is in for the entire duration of
developing a skill, and the failure is silent. It is also where the existing
freshness check actively causes harm: its repair instruction discards the work.

**Independent Test**: Not independent of User Story 1 — it reads a record only
that story writes. Given a completed named-source install: change a file in that
checkout, run the freshness check, and confirm it reports the difference and that
the command it prints names the same checkout.

**Acceptance Scenarios**:

1. **Given** a project installed from a named checkout, **When** that checkout's
   skill files change and the freshness check runs, **Then** it reports the
   project as behind its source.
2. **Given** that report, **When** the user runs the command the check printed,
   **Then** the project is reinstalled from the same named checkout, not from the
   running tool.
3. **Given** a project installed from the running tool, **When** the running tool
   is upgraded and the freshness check runs, **Then** it reports as it does today
   and prints the plain repair command.

---

### User Story 3 - Get a truthful answer when the source is unreachable (Priority: P3)

A named checkout can be deleted, renamed, or live on a drive that is not mounted.
The freshness check then cannot answer its question. It must say so rather than
guessing, and must not report a healthy project as broken.

**Why this priority**: Reachable and certain to happen — checkouts are routinely
disposable — but it degrades an answer rather than blocking work.

**Independent Test**: Not independent of User Story 1, for the same reason as
User Story 2. Given a completed named-source install: delete the checkout, run the
freshness check, and confirm it reports the source as unreachable and does not
report the project as failed.

**Acceptance Scenarios**:

1. **Given** a project whose recorded source no longer exists, **When** the
   freshness check runs, **Then** it warns that the source is unreachable and
   names it.
2. **Given** that same state, **When** the freshness check finishes, **Then** its
   overall result is not a failure on account of this condition alone.

---

### Edge Cases

- **The named location is not a skills source.** A path holding neither the
  expected content nor a nested copy of it must fail, naming what was looked for
  and where — never silently falling back to the running tool, which would
  install something the user did not ask for and report success.
- **The name is relative and the check runs from elsewhere.** A source named
  relative to the current directory must still resolve when the freshness check
  is run from a different directory later.
- **The named source is the running tool.** Recorded like any other named
  source, and reported as one — `(from /path/to/wfctl)`, not `(wfctl 0.16.0)`.

  This edge case originally required the opposite: that naming the location the
  default would have used behave exactly as the default, output included. That
  was wrong, and the implementation contradicts it deliberately. FR-003 makes
  *absence* mean the default, so that upgrading the tool does not read as the
  source having changed. It says nothing about a caller who names a path,
  because naming one is a request to track that path — and an editable checkout
  named explicitly is a source that really does change under the install, which
  is the whole condition #146 exists to detect. Recording nothing there would be
  the tool discarding what the caller typed and reporting success over a source
  it chose for itself, which is the failure this feature opens with.

  It is not hypothetical: `quickstart.md` step 8 runs `uv run --project
  <worktree> wfctl install-skills --from <worktree>`, where the named source and
  the running tool are one checkout. Reporting that as `(wfctl 0.16.0)` would
  hide the only thing the step is checking.
- **Different parts of the project installed from different sources.** A later
  install of an additional agent's paths may name a different source than the
  first install did. Each recorded part must be reported against the source that
  produced it.
- **A bare install over a named-source install.** Installing without naming a
  source, in a project whose record names one, replaces the installed content with
  the default and the record along with it. This is the specified behavior, not an
  error — but it is silent, and it is what FR-013 exists to keep an automated
  repair from doing by accident. FR-015 makes it visible when it happens anyway.
- **A source that is missing content the record still lists.** Pruning removes
  paths the record holds that the source no longer provides; it must judge that
  against the named source, not against the running tool.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The installer MUST accept an optional named source location and
  copy the installed content from it.
- **FR-002**: When no source is named, the installer MUST behave exactly as it
  does today, using the running tool as the source.
- **FR-003**: The installer MUST record, for each part of the project it installs,
  which source produced it, alongside the fingerprint it already records. An
  install that names no source MUST record a value meaning "the default" rather
  than the running tool's own location, so that upgrading the tool does not read
  as the source having changed.
- **FR-004**: The recorded source MUST be stored in a form that resolves
  identically regardless of the directory a later command is run from.
- **FR-005**: The recorded source MUST be stored where it does not become part of
  the project's committed content, because it describes one checkout rather than
  the project.
- **FR-006**: The freshness check MUST compare the installed content against the
  recorded source, not against the running tool. Where the record means "the
  default", it MUST compare against the running tool exactly as it does today,
  including the wording of what it reports.
- **FR-007**: The freshness check MUST report which source a part was installed
  from whenever that source is not the default.
- **FR-008**: When the freshness check reports that a part is behind, the repair
  command it prints MUST name the recorded source, so that running it does not
  replace the installed content with the default.
- **FR-009**: When a recorded source is unreachable — deleted, renamed, or on a
  volume that is not mounted — the freshness check MUST report it as unreachable
  and MUST NOT count that condition alone as a failure.
- **FR-010**: The installer MUST reject a named source that does not contain the
  expected content, reporting what it looked for and where, and MUST NOT fall
  back to the default.
- **FR-011**: Where a named source is a checkout that nests the expected content
  one level down, the installer MUST accept the enclosing directory as well, so
  that naming the checkout root works.
- **FR-012**: Pruning MUST evaluate what the project no longer needs against the
  named source rather than the default.
- **FR-013**: The session-start routine MUST instruct that the repair command
  printed by the freshness check governs, so an automated repair cannot substitute
  a default-source install for a named-source one. Given FR-014, this instruction
  is the only safeguard against that substitution and MUST be explicit rather than
  implied by the examples it sits beside.
- **FR-014**: Naming a source MUST affect only the install it is given on. A
  later install that names no source MUST use the default and MUST overwrite the
  recorded source accordingly — there is no remembered source and nothing to
  clear.
- **FR-015**: When an install that names no source runs in a project whose record
  names one, the installer MUST report which source it is replacing before
  proceeding. This report MUST NOT be suppressed by the option that skips
  confirmation prompts, because the unattended session-start refresh is the case
  it exists for.

## Key Entities

- **Install record**: The per-project record of what was installed. Already holds,
  for each installed part, the tool version, a content fingerprint, an install
  time, and the list of installed paths. Gains the source that produced it.
- **Source**: A location holding the installable content. Either the running tool
  (the default) or a location the user named.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A person can install skills from a checkout other than the running
  tool's in a single command, with no manual file copying and no hand-editing of
  any record.
- **SC-002**: After such an install, the freshness check reports the project as
  current — zero drift findings attributable to the choice of source.
- **SC-003**: In every state the freshness check can reach, the repair command it
  prints, when run, leaves the project installed from the source it was installed
  from. Zero cases where following the printed instruction discards the user's
  chosen source.
- **SC-004**: When a named source changes after an install, the next freshness
  check reports it. The window in which a person can test a stale copy without
  being told closes at the next check rather than never.
- **SC-005**: A project with no development tree of its own can install skills
  from a branch or pull request. This is currently impossible; success is that it
  becomes possible.
- **SC-006**: The hand-held discipline currently documented for this repository —
  choose one of the two tools and use it for both installing and checking —
  becomes unnecessary for correctness, because the check derives the answer from
  the record instead of from which tool was invoked.
- **SC-007**: No install silently changes which source a project is installed
  from. Every such change is either requested on the command line or reported in
  the output of the run that made it.

## Assumptions

- Pre-specify design context loaded from
  `<spec_root>/146-install-skills-source/design.md`.
- A named source is a location on the local filesystem. Resolving a revision
  identifier or a pull request number is deliberately excluded — see the design
  document's *Not Doing*.
- Where a later install names a different source than an earlier one, each
  installed part is reported against its own recorded source. This is an informed
  default: the record is already kept per part, and reporting a part against a
  source that did not produce it would be false.
- The condition "installed before source recording existed" behaves like the
  existing "installed before fingerprinting existed" condition — a warning that
  the answer is unavailable, cleared by reinstalling, and not a failure.
- The second half of issue #146 — leaving hand-placed skills alone — is not part
  of this feature. It is split to a separate issue.

## Validation Strategy _(mandatory)_

- The project's recorded checks, all three green:
  `uv run --frozen --extra dev pytest -q`,
  `uv run --frozen --extra dev ruff check wfctl/ tests/`,
  `uv run --frozen --extra dev mypy wfctl/`.
- Unit coverage for source resolution: a valid source, a nested source, and a
  location holding neither — the third must raise rather than fall back.
- Unit coverage for the record: the source is written for each installed part, is
  stored resolved, and a default install records the default.
- Unit coverage for each of the freshness check's four reachable states, asserting
  on the printed text, including that the repair command carries the named source.
- **End-to-end, because the suite cannot cover it**: install from a named
  location, run the freshness check, and confirm it reports the source as a state
  and not as drift; then install from the default and confirm the drift finding
  returns. A run that only installed from the default has not exercised the
  feature.
