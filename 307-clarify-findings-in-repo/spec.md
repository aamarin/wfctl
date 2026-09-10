# Feature Specification: Scan receipts for clarify and analyze

**Feature Branch**: `307-clarify-findings-in-repo`
**Created**: 2026-09-09
**Status**: Draft
**Input**: Issue #307 — clarify and analyze write their findings outside the
repository, so a thorough run and a skipped one look identical in the PR.

Pre-specify design context loaded from `<spec-root>/307-clarify-findings-in-repo/design.md`.

## Clarifications

### Session 2026-09-09

- Q: Does a scan step verify its file is reachable, or only write it? → A: It commits the file and runs `wfctl arch check` on it, as `/speckit.brainstorm` already does for its records
- Q: Two features claiming one issue key would collide on one filename — key by issue or by branch? → A: By issue, and the collision stays `wfctl doctor`'s finding
- Q: "scan file", "scan receipt" or "attestation"? → A: "scan file" for the artifact; "attestation" only for the fact it carries
- Q: FR-011 keys a session by date — do two runs on one day collide? → A: the second extends that day's section, as `/speckit.clarify` already does in `spec.md`

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A reviewer can tell whether the spec was scanned (Priority: P1)

A reviewer opens a pull request produced by the wfctl pipeline. Among the changed
files is `docs/architecture/scans/<issue>-clarify.md`. They read one table and
know which categories the clarification scan examined, what status each was given,
and what it asked. They form a judgement about the scan's thoroughness without
leaving the diff.

**Why this priority**: This is the whole of #307. Every other story depends on the
file existing and being readable in the change under review.

**Independent Test**: Run `/speckit.clarify` on a feature whose spec has a real
ambiguity, commit, and confirm the scan file appears in `git status` and names the
ambiguity. Delivers reviewer-visible evidence on its own, with no other story
built.

**Acceptance Scenarios**

1. **Given** a spec with an under-specified requirement, **When** `/speckit.clarify`
   runs, **Then** a scan file is written under the arch root naming that category
   and the question asked about it.
2. **Given** the scan file is committed, **When** `wfctl arch check` is run against
   it, **Then** it exits 0 and reports that this change adds it.
3. **Given** the scan file is written but not committed, **When** `wfctl arch check`
   is run against it, **Then** it exits 1 and says the change would open without it.

### User Story 2 - An empty result says it looked (Priority: P1)

A reviewer opens a pull request where the clarification scan found nothing. The
scan file carries a full coverage table with every category marked `Clear`, and a
findings section that says no question met the bar. The reviewer can disagree with
a specific row.

**Why this priority**: Equal to story 1 and separately testable. The empty result is
the case the issue was filed over — told to auto-choose, an agent stops generating
questions at all, so "no findings" is the output of both a thorough scan and no
scan. Story 1 alone does not distinguish them.

**Independent Test**: Run `/speckit.clarify` on a spec with nothing ambiguous in it
and confirm the scan file carries every taxonomy row and states that the scan
looked and found nothing.

**Acceptance Scenarios**

1. **Given** a spec with no material ambiguity, **When** `/speckit.clarify` runs,
   **Then** the scan file carries one row per taxonomy category and a findings
   section stating that no question met the bar.
2. **Given** a scan file with a verdict and no coverage table, **When** a reviewer
   reads it, **Then** the absence of the table is visible in the diff without any
   tool being run.

### User Story 3 - The same evidence exists for analyze (Priority: P2)

A reviewer opens a pull request that reached the analyze step. A second scan file
reports which of the six detection passes ran, the requirement-to-task coverage,
and any CRITICAL findings.

**Why this priority**: `analyze` has the same defect for the same reason, and #307
names it explicitly. It is P2 rather than P1 because analyze runs later in the
pipeline, so a branch can demonstrate the feature before reaching it.

**Independent Test**: Run `/speckit.analyze` on a feature with `tasks.md` present
and confirm a second scan file lands in the repository.

**Acceptance Scenarios**

1. **Given** `spec.md`, `plan.md` and `tasks.md` all exist, **When**
   `/speckit.analyze` runs, **Then** a scan file is written naming each detection
   pass and its result.
2. **Given** one of the three artifacts is missing, **When** `/speckit.analyze`
   runs, **Then** the scan file's verdict is `inconclusive` and names which
   artifact could not be read.

### Edge Cases

- **The scan file already exists from an earlier run of the same step.** The step
  replaces it whole. It is one file with one writer, so there is no merge to get
  wrong.
- **A repository that declares `arch_root` elsewhere.** The scan directory follows
  it, because the path is derived from `wfctl arch-root` rather than written in.
- **A repository with no git.** `wfctl arch check` reports that no change carries
  the record and returns success — the absence of a reviewer is not a failure.
- **A change that draws no boundary and has no level-3 record.** The scan file is
  unaffected: it does not live in `design/` and does not depend on a record
  existing.
- **The step runs, and the agent writes a full coverage table it did not compute.**
  Out of scope to detect. The artifact is then a false claim rather than an absent
  one, which a reviewer can dispute and an empty section could not.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: `/speckit.clarify` MUST write a scan file at
  `<arch-root>/scans/<issue>-clarify.md` on every run, including a run that asks no
  question.
- **FR-002**: `/speckit.analyze` MUST write a scan file at
  `<arch-root>/scans/<issue>-analyze.md` on every run, including a run that reports
  no finding.
- **FR-003**: A scan file MUST carry a verdict that is exactly one of `satisfied`,
  `unsatisfied` or `inconclusive`, using those words with the meanings
  `_predicates.Verdict` gives them.
- **FR-004**: A scan file MUST carry a coverage table with one row per category the
  step examines — the ten clarification taxonomy categories for `clarify`, the six
  detection passes plus requirement coverage for `analyze` — each with exactly one
  of the statuses `Clear`, `Resolved`, `Deferred` or `Outstanding`. That is
  `speckit-clarify`'s own *reporting* vocabulary; its internal scan vocabulary
  (Clear / Partial / Missing) is not written to the file, because a reader wants
  what the scan concluded and not what it saw first.
- **FR-005**: A scan file MUST carry a findings section, and where the scan found
  nothing that section MUST state that the scan looked and found nothing rather
  than being absent or empty.
- **FR-006**: A scan file MUST name the path of the full artifact in `FEATURE_DIR`
  rather than restating its contents.
- **FR-007**: The arch root MUST be resolved by asking `wfctl arch-root`, never by
  writing `docs/architecture` into a skill.
- **FR-008**: The instruction to write the scan file MUST live in the command
  wrapper (`speckit.clarify.md`, `speckit.analyze.md`) and not in the derived
  `SKILL.md` files, so an upstream pull cannot revert it silently.
- **FR-009**: The change MUST NOT alter `_predicates.clarify`,
  `_predicates.analyze`, or any entry in `_STEPS`.
- **FR-010**: The change MUST NOT introduce a gate that refuses a step for a
  missing or `unsatisfied` scan file.
- **FR-011**: A scan file MUST carry one `## Session YYYY-MM-DD` section per scan
  session, appended. A re-run MUST NOT discard an earlier session's coverage or
  findings — a later scan that finds nothing is only meaningful given what an
  earlier one found. A second run on a date already present MUST extend that
  section rather than open a new one, matching how `/speckit.clarify` already
  merges same-day runs in `spec.md`. `##` and not the `###` that file uses:
  `###` is spent here on `Coverage`, `Findings` and `Deferred` within a session.
  What is never merged is two *steps* into one file; each step owns its own.
- **FR-012**: wfctl's own suite MUST assert that both wrappers ship and that each
  carries the scan-writing instruction, since a change under `wfctl/agents/` is
  otherwise unverified by the suite.
- **FR-013**: A scan step MUST commit its scan file and then run
  `wfctl arch check` against it, so a file written where the branch does not carry
  it is reported at the moment it is written rather than at review. `arch check`
  refuses an uncommitted file by design, so writing without committing would make
  the check permanently unusable at this step.
- **FR-014**: A scan file MUST be named for the issue key, `<issue>-<step>.md`,
  matching `<arch-root>/design/` and `<arch-root>/declarations/`. Two features
  claiming one key is a condition `wfctl doctor` already reports, and this feature
  does not restate it.
- **FR-015**: The artifact MUST be called a *scan file* throughout. "Receipt" names
  a manifest entry under `136-the-receipt-is-a-sibling-of-merged` and "record"
  names an architecture record; "attestation" names the fact the file carries, not
  the file.

### Key Entities

- **Scan file**: one markdown document per step per change, living under the arch
  root, committed on the branch by the step that wrote it. Holds a verdict, a coverage table, a findings
  section and a pointer. Written by the step, read by a human.
- **Coverage table**: one row per category the step examines, with the status that
  category was given. The document's evidentiary content — what separates a scan
  that found nothing from one that never ran.
- **Verdict**: `satisfied`, `unsatisfied` or `inconclusive`. Stated so a later gate
  can read it through `blocks(verdict, "repo-declared")`; nothing reads it today.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A reviewer opening a pipeline-produced pull request can answer "was
  this change scanned, and what did the scan cover?" from the diff alone, without
  running a command or opening a path outside the repository.
- **SC-002**: A `/speckit.clarify` run that asks no question produces a file whose
  coverage table has one row for every taxonomy category — currently ten, every one
  `Clear` — and zero findings.
- **SC-003**: A run that never scanned produces a file with no coverage table, and
  that difference is visible in the diff with no tool.
- **SC-004**: `wfctl arch check <scan file>` exits 0 for every committed scan file
  and 1 for one written and not committed.
- **SC-005**: `wfctl arch context` lists the same records before and after the
  feature — the scan directory adds nothing to the set of decisions in force.
- **SC-006**: The pipeline reaches every step it reached before, with the same
  state at each, for a feature that produces scan files and one that does not.
- **SC-007**: `wfctl arch check` exits 0 against every scan file at the moment its
  step finishes, because the step committed it.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/` and
  `uv run wfctl doctor` — the repo's definition of done, all four green.
- A test asserting both command wrappers ship and each carries the scan-writing
  instruction, in the shape the existing skill-shipping tests use.
- A test asserting `wfctl arch context` is unchanged by a file under
  `<arch-root>/scans/`, pinning `NO_COLOR`.
- Manual, because the suite cannot see it: `uv run wfctl install-skills`, then
  `/speckit.clarify` on a feature with a real ambiguity — confirm the scan file
  lands inside the repository and appears in `git status`. Then `/speckit.clarify`
  on a spec with nothing ambiguous — confirm the file says it looked and found
  nothing.
- This branch is its own first subject: its own clarify and analyze steps must
  produce scan files in the pull request that closes #307.

## Assumptions

- Pre-specify design context loaded from
  `<spec-root>/307-clarify-findings-in-repo/design.md`; the decisions there are
  taken as made, including the destination and the coverage-table-as-body choice.
- The bets this feature rests on, and what would falsify each, are in
  `docs/architecture/design/307-the-coverage-map-is-the-evidence.md` § Assumed.
  Named by path rather than restated: that record is the copy a reviewer opens, and
  this file is gitignored, so a second list here would drift where nobody could see
  it.
