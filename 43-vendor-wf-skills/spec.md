# Feature Specification: Vendor wf-skills

**Feature Branch**: `43-vendor-wf-skills`
**Created**: 2026-08-16
**Status**: Draft
**Input**: [wfctl#43](https://github.com/aamarin/wfctl/issues/43) — "Vendor wf-skills into wfctl's package; stop cloning at install time"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Installing skills gives the same result every time (Priority: P1)

A developer sets up a repo and runs `wfctl install-skills`. Today the command
fetches from a remote branch that moves, so the same command run on two machines,
or on the same machine a month apart, can install different content. Nothing
records that divergence and nothing surfaces it.

After this change the skills are part of wfctl itself. The version of the tool
determines the content, so the same tool version always produces the same result.

**Why this priority**: This is the defect the whole feature exists to fix.
Everything else is either a consequence of it or a safeguard around it.

**Independent Test**: Install the same wfctl version on two clean machines with no
network access after installation, run `wfctl install-skills` on each, and compare
the resulting trees byte for byte. They must be identical.

**Acceptance Scenarios**:

1. **Given** wfctl is installed and the machine has no network access, **When** the
   user runs `wfctl install-skills`, **Then** the command completes successfully and
   installs the full set of skills, commands, trackers and runtime templates.
2. **Given** two repos on the same wfctl version, **When** `wfctl install-skills`
   runs in each, **Then** the installed content is identical regardless of when each
   was run.
3. **Given** a user passes `--repo` or `--ref`, **When** the command runs, **Then**
   it reports that the option no longer exists rather than silently ignoring it.
4. **Given** the machine has no network access, **When** the user runs
   `wfctl install-config workmux`, **Then** the config is seeded successfully.

---

### User Story 2 - Knowing when a repo has fallen behind the tool (Priority: P2)

A developer upgrades wfctl. Their repos still hold the skills installed by the
previous version, and nothing tells them. They keep working against stale
instructions until something behaves unexpectedly.

`wfctl doctor` must report, per repo, whether the installed skills match the wfctl
that is currently running, and name the one command that fixes it.

**Why this priority**: Vendoring creates this failure mode — the tool and the repo
can now diverge in a way that was previously impossible. Shipping the vendoring
without this check trades one silent drift for another.

**Independent Test**: Install skills, then replace the bundled content with
different content, then run `wfctl doctor`. It must report the repo as stale and
name the remedy.

**Acceptance Scenarios**:

1. **Given** a repo whose skills were installed by the running wfctl version,
   **When** the user runs `wfctl doctor`, **Then** it reports the skills as current.
2. **Given** a repo whose skills were installed by an older wfctl version, **When**
   the user runs `wfctl doctor`, **Then** it reports the skills as stale, names both
   versions, and instructs the user to run `wfctl install-skills`.
3. **Given** the machine has no network access, **When** the user runs
   `wfctl doctor`, **Then** the skills verdict is still reported accurately and only
   the release-availability check degrades to a warning.
4. **Given** a repo where the bundled content changed but the tool version did not,
   **When** the user runs `wfctl doctor`, **Then** it reports the skills as stale
   without implying a version upgrade is available.

---

### User Story 3 - Existing repos keep working (Priority: P3)

A developer has repos that installed skills before this change. Their records
describe a fetch that no longer happens. Nothing may crash, and no installed file
or backup pointer may be lost.

**Why this priority**: Silent breakage of existing repos would be worse than the
problem being solved, but it affects only repos installed before the change and is
resolved by a single command.

**Independent Test**: Take a repo with a pre-change record, run `wfctl doctor`, then
run `wfctl install-skills`, then `wfctl doctor` again. First run warns, last run
reports current, and `wfctl uninstall-skills` still restores correctly afterwards.

**Acceptance Scenarios**:

1. **Given** a repo with a pre-change installation record, **When** the user runs
   `wfctl doctor`, **Then** it emits one warning explaining the record predates the
   new check and instructs re-running `wfctl install-skills` — it does not crash.
2. **Given** that same repo, **When** the user runs `wfctl install-skills`, **Then**
   the record is rewritten in the new form and the obsolete fetch details are
   removed.
3. **Given** a repo migrated this way, **When** the user runs
   `wfctl uninstall-skills`, **Then** every pre-existing file backed up by the
   original installation is still restored.

---

### User Story 4 - Packaging regressions are caught before release (Priority: P4)

A maintainer renames a directory or adds a new content type. The published package
silently stops carrying it, and the existing test suite passes because it runs
against the source tree, where the files exist regardless.

Automated checks must exercise the built package, not the source tree.

**Why this priority**: It protects the other three stories rather than delivering
user value directly, but without it every one of them can regress invisibly.

**Independent Test**: Remove one entry from the packaging declaration and confirm
the automated checks fail.

**Acceptance Scenarios**:

1. **Given** a change that omits content from the built package, **When** automated
   checks run, **Then** they fail and name what is missing.
2. **Given** a correctly built package, **When** it is installed into a clean
   environment and skills are installed from it, **Then** the installed content
   matches the source tree.

---

### Edge Cases

- **Offline `doctor`** — the release-availability check warns; the skills verdict is
  unaffected and still authoritative.
- **Record with no fingerprint** — one warning, no crash, resolved by re-installing.
- **Development install pointing at a working copy** — the recorded version cannot
  change, so the fingerprint is what detects edits; the reported message must not
  claim an upgrade is available when both versions match.
- **Content that belongs to no install layer** — the tracker configuration is copied
  outside the layer target lists. Changing it must still be detected as staleness.
- **Layer that installs nothing** — an agent with no files of its own writes no
  record, and must not be reported as stale or missing.
- **Removed options** — `--repo` and `--ref` may exist in scripts or muscle memory;
  passing them must produce a clear error, not a silent no-op.
- **Renamed content** — a file moved from one path to another with identical bytes
  must register as a change.
- **Cross-platform and cross-version** — the fingerprint must be identical for
  identical content on macOS and Linux and on every supported Python version.

## Clarifications

### Session 2026-08-16

- No critical ambiguities detected.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: `install-skills` MUST source all installed content from the wfctl
  installation itself and MUST NOT contact any external service.
- **FR-002**: `install-config` MUST source its content from the wfctl installation
  itself and MUST NOT contact any external service.
- **FR-003**: The system MUST NOT retain any reference to `aamarin/wf-skills` as a
  runtime source in any command.
- **FR-004**: `install-skills` and `install-config` MUST NOT accept options
  selecting an external source; supplying one MUST produce an explanatory error.
- **FR-005**: The published package MUST carry every file that either command
  installs, including skills, commands, tracker configuration, repo configs, and
  runtime templates.
- **FR-006**: Installed destination paths MUST be unchanged by this feature; only
  the origin of the content changes.
- **FR-007**: `install-skills` MUST record, per installed layer, the wfctl version
  that performed the installation and a fingerprint of the content it installed
  from.
- **FR-008**: The fingerprint MUST cover every file the installation can source,
  including content that belongs to no layer target list.
- **FR-009**: The fingerprint MUST change when any file's contents change and when
  any file is renamed or moved.
- **FR-010**: The fingerprint MUST be identical for identical content across
  operating systems and supported language versions.
- **FR-011**: `doctor` MUST report, for each installed layer, whether the repo's
  installed content matches the running wfctl, without contacting any external
  service.
- **FR-012**: `doctor` MUST report a stale repo with both the installing and running
  versions, and MUST use a distinct message when those versions are equal.
- **FR-013**: `doctor` MUST name `wfctl install-skills` as the remedy for stale
  content.
- **FR-014**: `doctor`'s remaining network-dependent check MUST degrade to a warning
  on failure and MUST NOT prevent the content check from reporting.
- **FR-015**: `doctor` MUST handle a record that predates this feature with a single
  explanatory warning and MUST NOT fail.
- **FR-016**: `install-skills` MUST remove obsolete fetch details from the record
  when rewriting it, while preserving the per-item entries and backup pointers that
  uninstall depends on.
- **FR-017**: `install-config` MUST NOT record installation state and MUST NOT be
  subject to any staleness check, preserving its seed-once behavior.
- **FR-018**: Automated checks MUST verify the built package rather than the source
  tree, and MUST fail when installable content is missing from it.
- **FR-019**: Automated checks MUST verify that a change to any sourceable file
  changes the fingerprint.

## Key Entities

- **Bundled content**: The skills, commands, tracker configuration, repo configs and
  runtime templates carried inside wfctl. Read-only at runtime; the single source of
  truth for what a repo receives.
- **Installation record**: Per-repo state describing which layers are installed,
  which files each placed, what was backed up, the wfctl version that installed
  them, and the content fingerprint at that time.
- **Content fingerprint**: A single value derived from every sourceable file's path
  and contents. Equality means the repo was installed from the same content the
  running tool carries.
- **Layer**: An install grouping with a disjoint set of destinations, used for
  attribution on uninstall and restore. Unchanged by this feature.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: `wfctl install-skills` completes with the machine disconnected from
  the network, in 100% of attempts.
- **SC-002**: Installed content is byte-identical to the content carried inside the
  installed wfctl, verified against the built package rather than the source tree.
  (Two machines on the same version therefore agree by construction; comparing two
  machines directly is not something an automated check can perform.)
- **SC-003**: `wfctl install-skills` performs zero network round-trips, down from a
  clone that took roughly 15 seconds. Wall-clock time is a consequence of this, not
  a separately measured target — the check that protects it is SC-006.
- **SC-004**: A repo left behind by a tool upgrade is reported by `wfctl doctor`
  within one command, with no arguments and no network.
- **SC-005**: `wfctl doctor` produces an accurate skills verdict while offline, in
  100% of attempts.
- **SC-006**: Zero commands contact `aamarin/wf-skills`, verified by inspection of
  the shipped code.
- **SC-007**: A repo installed before this change reaches a fully current state in
  one command, with no file or backup loss.
- **SC-008**: Removing any single entry from the packaging declaration causes
  automated checks to fail.

## Validation Strategy _(mandatory)_

- **Type and lint check**: `uv run mypy` and `uv run ruff check .` pass.
- **Unit suite**: `uv run pytest -q` passes on both supported language versions.
- **Story 1**: A test asserting no command references the external source; a test
  asserting the removed options error; an offline install exercised by the packaging
  check below.
- **Story 2**: Tests covering current, stale, equal-version-stale, missing-record and
  offline paths of `doctor`, each asserting the exact remedy text.
- **Story 3**: A test starting from a pre-change record that asserts the warning,
  the rewrite, and that uninstall still restores backed-up files.
- **Story 4**: An automated packaging check that builds the package, installs it into
  a clean environment, installs skills into a scratch repo, and asserts the content
  matches the source tree. A fingerprint-coverage test that modifies one file in each
  sourceable directory and asserts the fingerprint changes each time. A cross-platform
  and cross-version fingerprint-stability check.

## Assumptions

- Pre-specify design context loaded from `design.md` alongside this file. The spec
  root is outside the repo — resolve it via `wfctl feature-paths`, never assume
  `specs/` in the working tree.
- Losing the ability to release skill changes independently of wfctl is accepted.
  The same author owns both, the upstream repo is being archived, and a release is a
  tag.
- `doctor`'s file-level "what changed" detail is not replaced. The remedy is the
  same command regardless of what changed.
- The packaging verification (Story 4) is treated as in scope for this feature
  rather than deferred, because it is the only thing that can detect a regression in
  FR-005 and every other requirement depends on it.
- The runtime templates currently carried are treated as content to vendor as-is.
  Replacing that arrangement is tracked separately and is out of scope here.
- Detecting hand edits to installed files in a repo is a related but distinct
  capability and is out of scope.
