# Feature Specification: version check — default branch and fork

**Feature Branch**: `21-version-check-master-and-fork`
**Created**: 2026-08-17
**Status**: Draft
**Input**: Issue #21 — "doctor reports 'latest' against release tags only, hiding merged-but-unreleased work", refined through `/speckit.brainstorm` into `design.md`.

## Clarifications

### Session 2026-08-17

- Q: For a fork install, which repository is the source of release tags, given the one-query requirement? → A: Tags always come from the canonical upstream repository; the branch tip comes from the recorded origin. A second query is made only when those differ.
- Q: With two queries possible, how should the report handle one of them failing? → A: Exactly one warning line per report, whose text names whichever checks could not run. No check fails silently, and no report grows a second warning line.
- Q: #35 B1 asks that a fork point the version check at its own releases, which contradicts FR-009. Which holds? → A: FR-009 holds — tags stay upstream, because the alternative reintroduces a silent "latest" for contributor forks. B1's underlying harm is addressed instead by FR-012: every remedy command names the recorded origin, so doctor never instructs a fork user to install from upstream.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A branch build learns it is stale (Priority: P1)

A developer installed wfctl the way the README prescribes — from the default
branch — some weeks ago. Merges have landed since, without a release. They run
`wfctl doctor` expecting it to answer "am I current?". Today it answers `✓
latest`, because the version string in their build matches the newest tag. They
carry on running replaced logic and stale bundled skills, with nothing in the
report to suggest otherwise.

After this change, the same command tells them their build predates the branch
tip, names both commits, and prints the command that fixes it.

**Why this priority**: This is the entire defect. It has already caused two
observed incidents — PR #20's pipeline-inference change, and this session's own
start, where a build three commits behind reported itself current. Every other
story here exists to keep this one from being noisy.

**Independent Test**: Install from a commit behind the branch tip, run `wfctl
doctor`, and confirm the report distinguishes "behind the newest release" from
"behind the branch tip" and names the correct remedy for each.

**Acceptance Scenarios**:

1. **Given** an install whose recorded commit differs from the default branch tip, and whose version equals the newest release tag, **When** `wfctl doctor` runs, **Then** it reports the build as behind the branch, shows both short commits, states that bundled skills come from the same build, prints a reinstall command, and exits non-zero.
2. **Given** an install whose recorded commit equals the default branch tip, **When** `wfctl doctor` runs, **Then** the tool line is unchanged from today's output and the exit code is zero.
3. **Given** an install whose version is older than the newest release tag, **When** `wfctl doctor` runs, **Then** the existing upgrade line is reported alone and the branch-drift line is suppressed, because the prescribed reinstall resolves both.

---

### User Story 2 - Installs that cannot drift are not nagged (Priority: P2)

Not every install is a branch build. Someone pinned a tag deliberately. Someone
works from an editable checkout. Someone installs from a fork. A future user
installs from a package index (issue #2). None of these should be told they are
behind a branch they did not install from.

**Why this priority**: A freshness line that cries wolf is worse than no line —
it trains the reader to skip the row that matters in Story 1.

**Independent Test**: Run the check against each install shape and confirm the
branch comparison is silently skipped, or targeted correctly, in every case.

**Acceptance Scenarios**:

1. **Given** an install with no recorded source-control origin (package index, source archive), **When** `wfctl doctor` runs, **Then** only the release-tag line is reported and the exit code is unchanged from today's behavior.
2. **Given** an editable or local-path install, **When** `wfctl doctor` runs, **Then** the branch comparison is skipped without a warning, because a working checkout is not drift.
3. **Given** an install pinned to a specific tag or revision, **When** `wfctl doctor` runs, **Then** the branch comparison is skipped, because the pin is deliberate.
4. **Given** an install recorded as originating from a fork, **When** `wfctl doctor` runs, **Then** drift is measured against that fork's default branch, while release freshness is still measured against the canonical upstream repository's tags — a fork is authoritative about its own branch, never about upstream's releases.
5. **Given** a fork install and any remedy the report prints — the upgrade line as well as the reinstall line — **When** `wfctl doctor` runs, **Then** every printed command names the fork the build came from, never the canonical upstream repository, so that following any of them keeps the user on their own lineage.

---

### User Story 3 - The check degrades quietly when it cannot run (Priority: P3)

The comparison needs one network round trip, or two for a fork install. On a
plane, behind a proxy, or against a repository that has moved, it will fail.

**Why this priority**: Existing behavior already covers this; the requirement is
that adding the branch comparison does not introduce a second failure mode or a
second warning line.

**Independent Test**: Make each query fail, independently and together, and
confirm the report carries exactly one warning line whose text names the
comparisons that could not run, at exit zero. The text deliberately differs from
today's — it must name what is missing rather than say only "couldn't check
latest" — so an existing assertion on the old string changes with it.

**Acceptance Scenarios**:

1. **Given** every query fails, **When** `wfctl doctor` runs, **Then** one warning line reports that neither comparison could be performed, and the exit code is zero.
2. **Given** the release query succeeds and the branch query fails, **When** `wfctl doctor` runs, **Then** one warning line reports the release verdict alongside the branch check that could not run — never a silent omission, and never a second warning line.
3. **Given** the branch query succeeds and the release query fails, **When** `wfctl doctor` runs, **Then** one warning line reports the branch verdict alongside the release check that could not run.
4. **Given** an upstream install and a responding remote, **When** `wfctl doctor` runs, **Then** the report is produced from exactly one remote query, no more than today.

### Edge Cases

- **Recorded commit is ahead of the branch tip.** Comparing two commit
  identifiers proves difference, never direction. This is accepted imprecision:
  an install resolves the branch tip at install time, so drift only accumulates
  in one direction, and the local-path installs that could be ahead record no
  source-control origin and are skipped by FR-004.
- **Default branch is renamed** (for example `master` to `main`). The check must
  follow the rename without a code change; nothing may hardcode a branch name.
- **The repository has no tags yet.** The release comparison already tolerates
  this; the branch comparison must be independent of it.
- **Recorded origin is unreachable while the tag source is reachable** (a deleted
  or private fork). Reported as the release verdict plus a named branch-check
  failure, in one warning line — never silently dropped, since a missing drift
  line otherwise reads as "no drift".

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: `wfctl doctor` MUST compare the installed build's origin commit against the current tip of the default branch of the repository it was installed from, in addition to the existing release-tag comparison.
- **FR-002**: The build's origin commit and origin repository MUST be read from local install metadata, with no network access and no change to how the package is built or published.
- **FR-003**: The default branch MUST be resolved from the remote rather than assumed, so a rename requires no code change.
- **FR-004**: The branch comparison MUST be skipped, silently and without affecting the exit code, when the install records no source-control origin, records a local directory, or records a deliberate pin to a tag or revision. A pin suppresses **only** the branch comparison: the recorded origin is still known and still governs FR-012, since a pinned fork build has a lineage that its remedies must respect.
- **FR-005**: When drift is found, the report MUST name both the installed and current commits, state that bundled skills originate from the same build, and print a reinstall command that is verified to re-resolve the branch.
- **FR-006**: Drift MUST produce a non-zero exit code, consistent with the existing stale-release and stale-skills reporting.
- **FR-007**: When a newer release tag exists, the branch-drift line MUST be suppressed, so the report never presents two competing upgrade instructions.
- **FR-008**: The report MUST NOT state a number of commits of drift, since the available data proves difference only.
- **FR-009**: The check MUST make one remote query per repository it consults, and at most two: release tags MUST always be read from the canonical upstream repository, and the branch tip from the recorded origin. An upstream install therefore costs exactly one query, as today; a fork install costs two.
- **FR-009a**: When any query fails, the check MUST report exactly one warning line whose text names which comparisons could not be performed. A comparison that could not run MUST NOT be silently omitted, because its absence would otherwise be indistinguishable from a healthy result. The exit code is zero **unless a comparison that did run found something actionable** — a failed query must not bury a verdict that succeeded. (Amended during code review: as first written this said "MUST exit zero" unconditionally, which contradicted FR-006 whenever the branch query proved drift while the tag query failed — a state reachable on any fork install. FR-006 wins: suppressing a positively identified stale build is the worse failure, and is the exact defect this feature exists to remove.)
- **FR-010**: Project documentation describing `wfctl doctor` as comparing the installed version against the latest release tag MUST be updated to describe both comparisons.
- **FR-011**: The behavior MUST be covered by tests that run offline, isolated from the suite's existing suppression of this check, covering at minimum: drift found, at tip, deliberate pin, no recorded origin, fork targeting, the remedy URLs required by FR-012, and each partial-failure state named in FR-009a.
- **FR-012**: Every remedy command the report prints — the existing upgrade line as well as the new reinstall line — MUST name the repository the build was actually installed from. A report MUST NOT instruct a user to install from a repository other than their own origin, since following that instruction would silently replace their build with a different lineage.
- **FR-013**: `wfctl doctor`'s tool-freshness check MUST report its verdict as a boolean "found drift", folded into the command's exit code by the caller, rather than returning an exit code of its own. This requirement is inherited from issue #41, which defines one exit-code contract across all of doctor's checks and assigns this conversion to this branch; it is recorded here so the work is traceable and verifiable alongside the rest of the feature.

### Key Entities

- **Installed build identity**: what the running wfctl was built from — an origin repository, an origin commit, and optionally the revision that was requested at install time. Present for source-control installs, absent otherwise.
- **Remote branch state**: the default branch's name and current tip commit, as reported by the origin repository at check time.
- **Freshness report**: the two independent verdicts doctor renders about the tool — one against published releases, one against the branch — and the single exit code they combine into.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A build installed from a commit behind the default branch tip is identifiable as stale from `wfctl doctor`'s output alone, with no manual comparison against the repository.
- **SC-002**: Reading doctor's output tells a stale user exactly one action to take, and running that action makes the drift report disappear.
- **SC-003**: The four install shapes that cannot drift — no metadata file recorded, metadata recording a local directory rather than a source-control origin, a deliberate pin to a tag or revision, and unreadable metadata — produce no drift report, in 100% of runs.
- **SC-004**: A fork build reports drift against its own origin and therefore reaches a clean report after reinstalling; it never reports drift that a reinstall cannot clear.
- **SC-005**: An upstream install performs the same number of network round trips as before the change; a fork install performs at most one more. The full test suite continues to run offline.
- **SC-006**: The stale build present on the development machine at the time of writing — three commits behind the branch tip, reporting `✓ latest` — is reported as drift by the new output. This is the reproducible half of the motivating evidence; PR #20's untagged merge is the same shape and is recorded as history in issue #21 rather than as a test, since it cannot be re-run.

## Validation Strategy _(mandatory)_

- `pytest` — full suite offline, including the new cases registered under the marker that exempts them from the suite-wide suppression of this check.
- `ruff check` and `mypy` — the project's configured lint and type gates.
- Manual end-to-end against the live discrepancy already present on this machine: the installed build predates the branch tip, so `wfctl doctor` must move from reporting current to reporting drift, and must return to reporting current after the printed reinstall command runs.
- Manual verification of the reinstall command itself: confirm the recorded origin commit advances to the branch tip after running it. This gates FR-005 — a remedy that does not re-resolve makes the report unactionable.

## Assumptions

- Pre-specify design context loaded from `design.md` in this feature directory.
- Install metadata for source-control installs is written by the standard Python
  install tooling and is readable from the installed package. **Verified during
  planning** for both installers this project's users have (research.md R1, R2).
- A deliberate pin is distinguishable from a branch install in that metadata.
  **Verified during planning** (research.md R3): a pinned install records the
  requested revision and a branch install does not. The tag-matching fallback
  previously proposed here is therefore dropped, not implemented.
- The issue tracker check was skipped: no tracker is configured for this repo, so
  `wfctl issue view 21` no-ops. Issue #21 was confirmed to exist by direct read.
