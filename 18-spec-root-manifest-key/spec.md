# Feature Specification: spec-root-manifest-key

**Feature Branch**: `18-spec-root-manifest-key`
**Created**: 2026-08-05
**Status**: Draft
**Input**: Issue #18 — "feature-paths hardcodes specs/ when the dir doesn't exist yet, so specs can't live outside the repo"

## Clarifications

### Session 2026-08-05

- Q: When a repository that already holds in-repo spec directories records a spec root, should resolution fall back to the repository's own `specs/`? → A: No fallback — the recorded root is the only root; the diagnostic command reports the condition when both locations hold spec directories, so the transition is visible rather than silent.
- Q: How should an existing but unparseable configuration file be treated? → A: Fail loudly, as today, in both locations — a malformed configuration is a broken repository, not a missing setting.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - New specs land in the configured location (Priority: P1)

A maintainer wants their project's specs stored outside the repository so they
survive worktree teardown. They record that location once for the repo. From then
on, starting a new feature writes the spec to that location instead of the
repository's own `specs/` directory.

Today only the *read* path honors a configured location: an existing spec
directory outside the repo resolves fine, but creating a new one always falls
back to `<repo>/specs/<branch>`. Every consumer of the pipeline routes through
the same path resolver, so this one fallback decides where every new spec is
written.

**Why this priority**: This is the defect. Without it nothing else in this
feature has an effect, and the workaround it removes (hand-made symlinks per
worktree) is what silently fails today.

**Independent Test**: Configure a spec root in a repo, ask the tool for the
current feature's paths on a branch that has no spec directory yet, and confirm
the reported directory is under the configured root. Ship this alone and a
maintainer can already relocate their specs by recording the setting in each
working copy.

**Acceptance Scenarios**:

1. **Given** a repo with a configured spec root and a branch with no spec
   directory, **When** the feature paths are requested, **Then** the reported
   feature directory is `<configured-root>/<branch>`.
2. **Given** a repo with a configured spec root and an existing spec directory
   under it, **When** the feature paths are requested, **Then** that existing
   directory is reported (unchanged matching behavior — exact branch name first,
   then issue-key match).
3. **Given** a repo with no configured spec root, **When** the feature paths are
   requested, **Then** the reported directory is `<repo>/specs/<branch>`, exactly
   as before this feature.
4. **Given** a configured spec root and the per-invocation environment override
   both set, **When** the feature paths are requested, **Then** the environment
   override wins.

---

### User Story 2 - Worktrees inherit the setting (Priority: P2)

A maintainer creates a fresh worktree for a new issue and runs the pipeline
immediately. The spec lands in the configured location without them configuring
anything in that worktree.

This matters because the file holding the setting is untracked and
per-working-copy, and worktree creation regenerates it from scratch. A setting
recorded only in the worktree cannot exist at the moment the pipeline first runs
there, so specs would fall back into the worktree and be destroyed with it — the
same failure this feature exists to remove.

**Why this priority**: Without it, P1 works but must be repeated in every
worktree, trading a manual symlink step for a manual configuration step. With
it, the setting is recorded once per project.

**Independent Test**: Record the setting in a project's primary working copy
only, then request feature paths from a fresh worktree of that project with no
setting of its own, and confirm the configured root is used.

**Acceptance Scenarios**:

1. **Given** a project whose primary working copy declares a spec root and a
   worktree that declares none, **When** feature paths are requested from the
   worktree, **Then** the primary working copy's spec root is used.
2. **Given** a worktree that declares its own spec root, **When** feature paths
   are requested from it, **Then** the worktree's own value is used and the
   primary working copy is not consulted.
3. **Given** a repository layout with no primary working copy (a bare clone or a
   detached git directory), **When** feature paths are requested, **Then** no
   configuration outside the repository is read and the default location is used.

---

### User Story 3 - Recording the setting (Priority: P3)

A maintainer records, inspects, or removes the spec root through a command rather
than by hand-editing a configuration file, so the feature is usable by anyone who
did not write it.

**Why this priority**: The setting is readable by P1 and P2 whether or not a
command exists — hand-editing works. The command makes the feature discoverable
and documentable for a public tool, and guarantees the value is recorded where it
persists rather than in a working copy that is about to be deleted.

**Independent Test**: Run the command with a path in a fresh clone, then request
feature paths and confirm the new root is in effect; run it with no argument and
confirm it reports the effective root and which location declared it.

**Acceptance Scenarios**:

1. **Given** any working copy of a project, **When** the maintainer records a
   spec root, **Then** it is written to the project's primary working copy and
   the command reports the file it wrote.
2. **Given** a project with a spec root recorded, **When** the maintainer asks
   for it with no argument, **Then** the effective root and its source are
   reported.
3. **Given** a project with a spec root recorded, **When** the maintainer removes
   it, **Then** subsequent path resolution returns to the default location.
4. **Given** a path that does not exist yet, **When** it is recorded, **Then** the
   command accepts it without error and without creating the directory.

---

### Edge Cases

- **Configured root does not exist yet** — accepted. A not-yet-existing directory
  is the exact case that broke today's create path; the pipeline's own setup step
  creates the feature directory when it writes to it.
- **Repository has no primary working copy** (bare clone, detached git directory)
  — no configuration outside the repository is read. The directory above a
  detached git directory is a container that may hold an unrelated project's
  configuration, and applying that silently would be worse than not resolving.
- **Configuration file is absent** — treated as "no setting recorded"; the
  default location is used.
- **Configuration file exists but cannot be parsed** — fails loudly and names the
  file, in both the current repository and the primary working copy. A malformed
  configuration is a broken repository, not a missing setting: defaulting
  silently would put specs back inside the worktree with no signal, which is the
  failure this feature exists to remove.
- **Repository already holds in-repo spec directories when a root is recorded** —
  the recorded root is the only root. Pre-existing `<repo>/specs/<branch>`
  directories are neither found nor migrated; the diagnostic command reports the
  condition so the transition is visible rather than silent.
- **Setting present but empty** — treated as not set.
- **Relative path recorded** — resolved against the directory of the
  configuration file that declared it, never the current working directory, so
  the same relative value means one shared location for every worktree.
- **Home-relative path recorded** (`~/...`) — stored as written and expanded when
  read, so the recorded value stays portable across machines and users.
- **Setting coexists with the per-invocation environment override** — the
  environment override wins, and remains a per-invocation escape hatch rather
  than persistent configuration.
- **Existing tooling reads the same configuration file** — adding this setting
  must not disturb the install, upgrade, uninstall, or diagnostic commands that
  iterate that file's entries.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST resolve one spec root for a repository and use it
  for both locating existing spec directories and choosing the location of new
  ones. Locating and creating MUST NOT be able to disagree.
- **FR-002**: The system MUST resolve the spec root in this order: the
  per-invocation environment override, then the repository's recorded setting,
  then the repository's own `specs/` directory.
- **FR-003**: The system MUST read the recorded setting from the current
  repository's configuration first, and from the project's primary working copy
  when the current repository declares none.
- **FR-004**: The system MUST NOT read configuration from outside the repository
  when the repository has no identifiable primary working copy.
- **FR-005**: The system MUST accept absolute, home-relative, and relative
  values; relative values MUST resolve against the directory of the configuration
  file that declared them.
- **FR-006**: The system MUST NOT create, validate the existence of, or otherwise
  require the configured root to exist.
- **FR-007**: The system MUST leave the matching of a branch to an existing spec
  directory unchanged — exact branch name, then issue-key match, then the same
  lookup against ancestor branches. Only the root under which matching happens
  changes.
- **FR-008**: A repository with no recorded setting MUST behave exactly as it did
  before this feature, including one that has never had a configuration file.
- **FR-009**: Recording, reading, and removing the setting MUST be possible
  through a command, without hand-editing the configuration file.
- **FR-010**: The command MUST record the setting where it persists for the
  project rather than in a working copy that will be discarded, and MUST report
  the location it wrote.
- **FR-011**: The setting MUST survive tool upgrades, installs, and uninstalls of
  unrelated components that rewrite the same configuration file.
- **FR-012**: Commands that enumerate the configuration file's installed
  components MUST NOT treat this setting as one, and MUST NOT fail when it is
  present.
- **FR-013**: When a spec root is recorded, it MUST be the only root consulted.
  The system MUST NOT fall back to the repository's own `specs/` directory, so
  one feature's artifacts can never be split across two locations.
- **FR-014**: The diagnostic command MUST report when a spec root is recorded and
  the repository's own `specs/` directory still holds spec directories. It
  reports only; it MUST NOT move, delete, or resolve to those directories.
- **FR-015**: The system MUST fail, identifying the offending file, when a
  configuration file exists but cannot be parsed — in the current repository and
  in the primary working copy alike. It MUST NOT treat an unparseable file as an
  absent setting.

### Key Entities

- **Spec root**: the directory under which a project's spec directories live. One
  per project. Recorded as a single value in the project's existing
  per-repository configuration file; absent for every project that does not use
  the feature.
- **Spec directory**: one feature's artifacts (spec, plan, tasks, analysis),
  named for the branch. Its name and contents are unchanged by this feature; only
  the directory it sits under is configurable.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A project can relocate its specs outside the repository by
  recording one setting once, with zero per-worktree steps — down from two manual
  steps (move the directory, create a symlink with a nesting-dependent relative
  path) repeated for every worktree.
- **SC-002**: A fresh worktree runs the full pipeline with no preparation beyond
  its normal creation, and every artifact it writes is outside the worktree and
  still present after the worktree is deleted.
- **SC-003**: Requesting the current feature's paths on a branch with no spec
  directory reports the configured root — the case that silently reported the
  repository's own `specs/` before this feature.
- **SC-004**: Every existing project, having recorded nothing, reports byte-identical
  paths before and after the change.
- **SC-005**: Install, upgrade, uninstall, and diagnostic commands complete
  successfully against a configuration file carrying the setting, and leave the
  setting intact.
- **SC-006**: A project that records a spec root while in-repo spec directories
  still exist is told so by the diagnostic command on the next run, rather than
  discovering it when an artifact turns up missing.

## Assumptions

- Pre-specify design context loaded from `.agent/spec.md`.
- One spec root per project is sufficient; no per-branch or per-epic override is
  needed, as the per-invocation environment override covers one-off cases.
- The project's primary working copy is a durable location for the setting. This
  holds for the working-copy-plus-worktrees layout this tool targets; layouts
  without one are handled by FR-004 rather than by guessing.
- The configuration file's existing behavior of preserving entries it does not
  recognize continues to hold, and is pinned by a test rather than assumed.
- Consumers of the path resolver already create the feature directory when
  writing to it, so the resolver never needs to.

## Validation Strategy _(mandatory)_

- `pytest` — full suite green, proving FR-008 (no behavior change without the
  setting) against the existing path and install tests.
- New tests covering: the configured root used for a branch with **no** existing
  spec directory (the core regression); worktree inheritance from the primary
  working copy; no outside read when no primary working copy exists; absolute,
  home-relative, and relative value handling; the environment override winning;
  and install/diagnostic commands running clean over a configuration file
  carrying the setting.
- New tests for the clarified behavior: a recorded root does not fall back to the
  repository's own `specs/` even when a matching directory exists there
  (FR-013); the diagnostic command reports that co-existence (FR-014); an
  unparseable configuration file raises rather than defaulting, in both
  locations (FR-015).
- `ruff check wfctl tests` and `mypy` — clean, per the repo's configured rule set.
- Manual: record a spec root in a consuming project, create a fresh worktree, run
  the specify step, and confirm the artifacts appear under the configured root
  with no symlink present.
