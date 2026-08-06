# Feature Specification: gitignore glob dedup

**Feature Branch**: `11-gitignore-glob-dedup`
**Created**: 2026-08-04
**Status**: Draft
**Input**: Issue #11 — "install-skills appends .gitignore lines already covered by an existing glob"

## Clarifications

### Session 2026-08-04

- Q: Checking coverage once per path costs measurably more than checking all
  paths at once (measured: 684 ms vs 46 ms for 57 paths). Take the simple
  per-path approach, the batched one, or the simple one with tests that would
  survive a later switch? → A: The simple per-path approach, with tests written
  against observable outcomes rather than how coverage is determined, plus a
  recorded marker naming the cost ceiling and the trigger for revisiting it.
- Q: Should an install report how many entries it skipped as already covered? →
  A: Yes — a count only, printed only when the count is non-zero. Without it,
  "the ignore file did not change" is indistinguishable from "the step was
  skipped entirely". The skipped paths themselves are not listed; standard
  version control tooling already attributes each one to the source file, line,
  and pattern that covers it.

## User Scenarios & Testing _(mandatory)_

The user throughout is a **developer working in a repo that has wfctl skills
installed**. The value at stake is a working tree that stays clean, and an
ignore file that only ever changes when something genuinely new happened.

### User Story 1 - A new worktree starts clean (Priority: P1)

A developer creates a worktree. A setup hook installs the skills into it. The
developer runs `git status` and sees nothing — no modified `.gitignore`, no
untracked install artifacts. They begin work on a clean tree.

Today the opposite happens: the install appends one ignore line per installed
path, every one of which the repo's existing broader patterns already cover.
The developer's first `git status` on a brand-new worktree shows a modified
`.gitignore` they did not touch and would not want to commit. Because the lines
are not worth committing, they are never committed, so the next worktree
appends them again.

**Why this priority**: This is the reported defect and the only story that
delivers value on its own. Fixing it removes recurring noise from every
worktree in every consuming repo.

**Independent Test**: Seed a repo's ignore file with a broad pattern, install,
and confirm the ignore file is byte-identical afterward.

**Acceptance Scenarios**:

1. **Given** a repo whose ignore file already covers an install path via a
   broader pattern, **When** skills are installed, **Then** no line is added
   for that path.
2. **Given** a repo whose ignore file covers every install path, **When**
   skills are installed, **Then** the ignore file is byte-identical to before.
3. **Given** a clean tree, **When** skills are installed twice in a row,
   **Then** the ignore file is byte-identical after the second install.

---

### User Story 2 - Repos without broad patterns keep working (Priority: P2)

A developer works in a repo whose ignore file enumerates paths individually
rather than using broad patterns, or has no ignore file at all. Installing
skills still produces working ignore rules, exactly as it does today.

**Why this priority**: This is the no-regression story. The change narrows when
lines are written, so the risk is narrowing too far and leaving install
artifacts exposed. P2 because it protects existing behavior rather than adding
value, but it must ship with P1.

**Independent Test**: Install into a repo with no ignore file and confirm one
is created containing every install path.

**Acceptance Scenarios**:

1. **Given** a repo with no ignore file, **When** skills are installed,
   **Then** an ignore file is created listing every installed path.
2. **Given** a repo whose ignore file covers none of the install paths,
   **When** skills are installed, **Then** every path is added, unchanged from
   today's behavior.
3. **Given** a path recorded in directory form (a trailing separator), **When**
   the coverage check runs, **Then** it resolves the same way it does today and
   the entry is neither duplicated nor dropped.
4. **Given** a repo where the worktree directory is configured, **When** the
   config seeding command runs, **Then** its ignore entry behaves exactly as it
   does today.

---

### User Story 3 - A genuinely new artifact is surfaced for review (Priority: P3)

wfctl gains support for a new assistant whose files land under a directory no
existing pattern covers. A developer installs it, sees exactly one new line in
the ignore file, and decides whether to commit it or replace it with a broader
pattern of their own.

**Why this priority**: The desirable half of today's behavior, and the reason
the ignore file remains the right place to record these rules rather than a
local, uncommitted alternative. P3 because it falls out of P1 and P2 rather
than needing work of its own — but it is the property that must survive, so it
is stated rather than assumed.

**Independent Test**: Install with a target whose destination no pattern covers
and confirm exactly one line is added.

**Acceptance Scenarios**:

1. **Given** an install target under a directory no pattern covers, **When**
   skills are installed, **Then** exactly one line is added for it and it is
   visible in the working tree for the developer to review.
2. **Given** an install where some entries were already covered, **When** the
   install finishes, **Then** the developer is told how many were skipped.
3. **Given** an install where nothing was covered, **When** the install
   finishes, **Then** no skip report appears.

---

### Edge Cases

- **Path already tracked in version control, and a pattern matches it.** Ignore
  rules have no effect on a tracked file, so a line written for one is inert.
  The coverage check must treat such a path as already handled rather than
  appending a line that does nothing.
- **Command run somewhere that is not a repository.** The coverage check cannot
  produce an answer. It must fail closed — treat the path as not covered, write
  the line as today — and must not print diagnostic output to the terminal.
- **Ignore file exists but has no trailing newline.** The appended line must not
  be concatenated onto the last existing line.
- **Ignore file covers a path through a negation or a later-overriding
  pattern.** Coverage is whatever the version control system itself concludes,
  not what a simple pattern reading would suggest.
- **Two installs where the second adds a new target.** Only the new target's
  line is added; the previously covered ones stay absent.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST NOT add an ignore entry for a path that the
  repository's existing ignore configuration already covers, whether the
  coverage comes from an exact entry or a broader pattern.
- **FR-002**: The system MUST determine coverage by consulting the version
  control system's own evaluation of its ignore rules, not by comparing text.
- **FR-003**: The system MUST add an ignore entry for any path that is not
  already covered, preserving today's behavior.
- **FR-004**: The system MUST create an ignore file when none exists and the
  path is not otherwise covered.
- **FR-005**: The coverage determination MUST work for paths that do not exist
  on disk. Installed files are copied before their entries are written, but the
  backup directory is recorded whether or not a backup occurred, and the
  worktree directory is recorded before any worktree exists.
- **FR-006**: The system MUST treat a path as covered when an ignore entry for
  it would have no effect, including a path already tracked in version control.
- **FR-007**: The coverage check MUST NOT leak the version control system's own
  diagnostic or error output to the user's terminal, including when the check
  cannot be performed. This constrains pass-through output only; wfctl's own
  summary reporting is governed by FR-011 and FR-012.
- **FR-008**: When the coverage check cannot be performed, the system MUST fall
  back to adding the entry rather than skipping it.
- **FR-009**: Repeated runs against an unchanged repository MUST leave the
  ignore file byte-identical.
- **FR-010**: The change MUST apply uniformly to every caller that records an
  ignore entry, including the install record, the backup directory, each
  installed path, and the worktree directory written during config seeding.
- **FR-011**: When one or more entries are skipped as already covered, the
  system MUST report how many were skipped, so a developer can tell "nothing
  needed writing" apart from "nothing was attempted". The report MUST NOT
  enumerate the skipped paths or name the covering patterns — that detail is
  already available from standard version control tooling (SC-005), and
  reproducing it would put a second, drifting explanation in the output.
- **FR-012**: When no entries are skipped, the system MUST NOT report a
  zero count, so the common clean case adds no output.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: In a repository whose ignore file already covers the install
  paths, an install produces **zero** ignore-file changes. Measured today in
  this repository: an install considers **84** entries and appends **83** of
  them; **83** are already covered by an existing pattern, so the target is
  **1**. (The 84th, the install record, is the one case today's literal
  comparison already catches — which is why it appends 83 rather than 84.)
- **SC-002**: A newly created worktree shows **zero** modified files
  attributable to skill installation.
- **SC-003**: Two consecutive installs against an unchanged repository produce a
  byte-identical ignore file, for **100%** of the scenarios in User Stories 1
  and 2.
- **SC-004**: **Zero** regressions in existing behavior: every install path that
  is ignored today remains ignored after the change.
- **SC-005**: A developer can determine why a path was skipped using only
  standard version control tooling, with no wfctl-specific diagnostics.
- **SC-006**: Coverage checking adds no more than **1.5 s** to a full install.
  Measured cost of the accepted approach is ~12 ms per path, ~1.0 s for the 83
  entries this repository writes. The budget is set against an install whose
  dominant cost is a network fetch of roughly 15 s; if that fetch is ever
  removed, this budget must be revisited rather than inherited.
- **SC-007**: After an install in this repository, the developer is told that
  **83** entries were skipped and can confirm the remaining **1** in the ignore
  file diff — the two numbers summing to the **84** entries the install
  considered. The report is self-checking: if skipped + written does not equal
  the number of paths considered, something was neither reported nor written.

## Assumptions

- Pre-specify design context loaded from `.agent/spec.md`.
- The version control system in use provides a way to query whether a given path
  is ignored, including for paths that do not exist on disk. Verified against
  the version in use (2.44.0) during design; the automated tests pin the
  behavior for whatever version runs them.
- Existing callers all want "ensure this path is ignored" rather than "ensure
  this exact text is present in the file". The four call sites were read during
  design and all match the former reading.
- Redundant entries already committed into consuming repositories are left in
  place. They become inert once this ships, and rewriting a file a human may
  have edited is riskier than leaving dead lines behind.
- Removing ignore entries during uninstall is out of scope. It does not happen
  today; this change does not alter that.
- Checking each path separately is accepted as a deliberate simplification, not
  an oversight. The cheaper batched form is a known, measured alternative
  (~46 ms versus ~684 ms for 57 paths) that is not worth its larger change
  surface while a network fetch dominates install time. This is recorded in the
  code as a durable marker naming the cost, the trigger, and the replacement, so
  the decision is auditable rather than rediscovered. The trigger is issue #1
  (removing the runtime fetch); if it lands, this becomes roughly half of
  install time instead of a small fraction.

## Validation Strategy _(mandatory)_

- **Automated**: `uv run pytest tests/test_install_skills.py tests/test_install_config.py`
  — covering: a glob-covered path is not appended; an uncovered path is
  appended; a repo with no ignore file gets one created; the worktree-directory
  entry is unchanged; two installs leave the file byte-identical.
- **Manual**: run an install in this worktree, then inspect the ignore-file
  diff. Expect exactly one added entry (the backup directory) and none of the
  other 83.
- **Evidence**: the version control system's own ignore-check reports the broad
  pattern as the reason an install path is covered, and no enumerated duplicate
  is present.
- **Test altitude**: assertions target the resulting contents of the ignore file
  — which entries are present and absent — never how coverage was determined or
  how many times it was consulted. A switch to the batched form must therefore
  pass the same tests unchanged. Any test that would break on that switch is
  testing the mechanism and should be rewritten.
- **Full suite**: `uv run pytest` must pass with no new failures.
