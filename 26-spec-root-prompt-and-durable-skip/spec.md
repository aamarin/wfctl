# Feature Specification: spec-root prompt and durable-spec skip

**Feature Branch**: `26-spec-root-prompt-and-durable-skip`
**Created**: 2026-08-10
**Status**: Draft
**Input**: Closes #26 (install-skills should ask where specs live on first setup) and #27 (archive-story should skip specs that are already durable). Pre-specify design context loaded from `design.md`.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Teardown stops destroying and stops duplicating (Priority: P1)

A developer finishes a branch and removes its worktree. If the branch's design
artifacts would be destroyed by that removal, they are preserved first — and if
preserving them fails, the removal does not happen. If the artifacts live
somewhere the removal cannot reach, nothing is copied and the developer is told
why.

**Why this priority**: This is the data-integrity half. It changes behaviour for
repos that exist today, in both directions: repos with a durable spec location
stop accumulating stale duplicates, and every repo stops silently losing
artifacts when preservation fails. It delivers value with no other story
shipped.

**Independent Test**: Set a spec location outside the worktree, run a branch
through teardown, and confirm the artifacts are untouched in place with no
duplicate created. Separately, make preservation fail on a repo using the
in-worktree default and confirm the worktree survives.

**Acceptance Scenarios**:

1. **Given** a repo using the default in-worktree spec location, **When** the
   worktree is removed, **Then** the artifacts are preserved exactly as they are
   today.
2. **Given** a repo whose spec location is outside the worktree, **When** the
   worktree is removed, **Then** no copy of those artifacts is made, and the
   report states the location was already durable.
3. **Given** a repo whose configured spec location happens to resolve back
   inside the worktree, **When** the worktree is removed, **Then** the artifacts
   are preserved — the test is where the files are, not whether a setting exists.
4. **Given** artifacts that would be destroyed and a preservation step that
   fails, **When** removal is attempted, **Then** removal is refused, nothing is
   lost, and the message names both how to retry and how to remove anyway.
5. **Given** a branch with a superseded-location design document inside the
   worktree, **When** the worktree is removed, **Then** that document is
   preserved, because removal would otherwise destroy it.

---

### User Story 2 - A new project is asked where its specs should live (Priority: P2)

Someone sets up the workflow tooling in a repo for the first time. Before they
can be surprised by it, they are shown where design artifacts will be kept, what
each option means when a worktree is removed, and asked to choose. They are asked
once.

**Why this priority**: Without it the durable location is unreachable in
practice — it exists but nothing points anyone at it, so the failure it prevents
keeps happening. It depends on nothing in Story 1 and can ship alone, but it only
matters *because* Story 1 makes the choice consequential.

**Independent Test**: Run first-time setup interactively in a fresh repo, choose
each option in turn, and confirm the recorded result matches. Re-run setup and
confirm no second prompt.

**Acceptance Scenarios**:

1. **Given** a repo that has never been asked, **When** setup runs interactively,
   **Then** the choice is presented alongside the existing tracker question.
2. **Given** the same repo, **When** setup runs non-interactively or with
   confirmation suppressed, **Then** no question is asked and no location is
   recorded.
3. **Given** a developer who chooses to keep specs in the repo, **When** setup
   finishes, **Then** no location is recorded and artifact resolution behaves
   identically to a repo that was never asked.
4. **Given** a developer who chooses a durable location, **When** setup finishes,
   **Then** the choice is recorded where it survives worktree removal, and every
   file touched is reported.
5. **Given** a repo that has already answered, **When** setup runs again for any
   reason, **Then** the question is not repeated.
6. **Given** a developer who chooses a location that does not exist yet, **When**
   setup finishes, **Then** the location is recorded, nothing is created or
   cloned, and the commands to create it are printed.

---

### User Story 3 - The command's name matches what it does (Priority: P3)

The preservation command is named for what it preserves. Existing automation that
calls it by its former name keeps working.

**Why this priority**: Clarity, not capability — it resolves an overlap with the
separate work-in-progress checkpoint mechanism. Last because nothing depends on
it, but it must not be deferred indefinitely: the longer the old name is wired
into project configs, the more expensive the eventual rename.

**Independent Test**: Invoke the command by both names and confirm identical
behaviour.

**Acceptance Scenarios**:

1. **Given** a project configuration calling the former name, **When** teardown
   runs, **Then** it behaves exactly as it does under the new name — no failure,
   no aborted removal.
2. **Given** a developer reading available commands, **When** they list them,
   **Then** the new name is shown and the former name is not advertised.

---

### Edge Cases

- **Configured location resolves inside the worktree** — treated as at risk and
  preserved. The rule is containment, never the presence of a setting.
- **Configured location does not exist** — recorded and reported without being
  created, cloned, or validated. A not-yet-existing location is a supported state.
- **Per-invocation location override in the environment** — obeyed, and the same
  containment test applies to whatever it resolves to.
- **Worktree already gone when teardown runs** — reported and skipped, exit
  success. Nothing can be at risk in a directory that does not exist.
- **Preservation tool absent entirely** — warn and allow removal to proceed.
  Blocking here would strand every worktree on a machine that never had the tool.
- **Preservation tool present but broken** (bad install, unparsable arguments) —
  removal is refused. Absence of proof that nothing was at risk is not proof that
  nothing was.
- **Repeat preservation of the same branch** — the previous result is set aside
  rather than deleted, and a same-instant repeat does not collide.
- **Nothing at all to preserve** — a normal outcome, reported as such, never an
  error.
- **A record of having been asked, with no location recorded** — resolution
  behaves as the default. The record only suppresses the question.
- **Storage exhausted or unwritable partway through preserving at-risk files** —
  removal is refused, and the previously preserved result is left exactly where
  it was, complete and in its canonical location. A failed attempt leaves no
  partial result behind at all. This matters because refusing the removal invites
  a retry, and a retry that displaced the good result with a partial one would
  turn the safety mechanism into the source of the damage.

## Requirements _(mandatory)_

### Functional Requirements

**Preservation scope**

- **FR-001**: The system MUST preserve only artifacts that the pending teardown
  would destroy, determined by whether the artifact's path lies inside the
  worktree being removed.
- **FR-002**: The system MUST NOT copy artifacts stored outside the worktree,
  regardless of how that location was configured.
- **FR-003**: The system MUST apply FR-001 by path containment alone, so a
  configured location that resolves back inside the worktree is still preserved.
- **FR-004**: When nothing is at risk, the system MUST report the reason and the
  resolved location, so an absent result is not read as a failure.
- **FR-005**: The system MUST continue to preserve at-risk artifacts stored at
  the superseded per-branch location, since declining to preserve them at
  teardown is equivalent to deleting them.

**Teardown safety**

- **FR-006**: The system MUST refuse the removal when at-risk artifacts existed
  and preserving them did not succeed.
- **FR-007**: The system MUST allow the removal to proceed when nothing was at
  risk, including when other parts of preservation failed.
- **FR-008**: When a removal is refused, the system MUST state how many artifacts
  were affected, how to retry, and how to remove the worktree manually — the
  removal tool offers no way to skip the check. The manual route MUST be stated
  completely: both commands it requires, the condition under which the first one
  refuses and needs overriding, and the cleanup it skips. A route that fails on a
  reachable input is not a route.
- **FR-009**: When the preservation tool is not installed, the system MUST warn
  and allow the removal to proceed.
- **FR-023**: A preservation attempt MUST leave the previously preserved result
  intact and in its canonical location unless the attempt succeeds in full, and a
  failed attempt MUST leave no partial result behind. Refusing a removal invites
  a retry; a retry that displaced a complete result with an incomplete one, or
  that accumulated incomplete ones indistinguishable from complete history, would
  make the safety mechanism the source of the damage.

**Choosing where specs live**

- **FR-010**: The system MUST offer the spec-location choice during first-time
  interactive setup, presented with the existing tracker question.
- **FR-011**: The system MUST NOT ask when setup is non-interactive, when
  confirmation is suppressed, or when the repo has already answered.
- **FR-012**: Choosing to keep specs in the repo MUST record no location, so
  resolution is indistinguishable from a repo that was never asked.
- **FR-013**: Choosing a durable location MUST record it where it survives
  worktree removal, and MUST report every file the choice modified.
- **FR-014**: The system MUST NOT create, clone, or check the existence of a
  chosen location; it MUST print the commands to create one instead.
- **FR-015**: The system MUST record that the question was asked, on any answer
  including the default, so it is never repeated.
- **FR-016**: The record in FR-015 MUST be found from any worktree of the
  project, not only from the checkout where the answer was given.
- **FR-017**: The record in FR-015 MUST NOT affect where artifacts resolve.

**Naming**

- **FR-018**: The preservation command MUST be named for the artifacts it
  preserves.
- **FR-019**: The former name MUST continue to work, without being advertised, so
  that project configurations written before the rename do not fail and cause
  refused removals.
- **FR-020**: The system MUST report project configurations still calling the
  former name, as non-fatal drift, so the compatibility shim required by FR-019
  has an observable end condition rather than becoming permanent.

**Documentation of intent**

- **FR-021**: The recorded rationale for preservation MUST state that copying is
  justified by risk of loss, replacing the superseded rationale that justified it
  as a presentation worth producing regardless of risk.
- **FR-022**: The requirement that tooling read exactly one artifact location
  MUST be reconciled with the preservation of superseded-location artifacts
  required by FR-005.

## Key Entities

- **Worktree**: the disposable checkout being removed. Its boundary is the single
  input to every containment decision.
- **Spec location**: the directory a project's per-branch design artifacts live
  under. Either inside the worktree (the default) or outside it (durable).
- **At-risk artifact**: an artifact whose path lies inside the worktree. The only
  category that is copied, and the only category whose failure refuses a removal.
- **Preserved result**: the set of copied artifacts plus a generated index. Read
  in pipeline order; explicitly not a tree meant to be copied back.
- **Location record**: the project's recorded spec location. Absent by default;
  read from the project's primary checkout so it outlives any single worktree.
- **Asked record**: the marker that the location question has been answered.
  Independent of the location record and never consulted when resolving paths.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A project whose specs live outside its worktrees produces zero
  duplicate copies of those specs over any number of worktree teardowns.
- **SC-002**: A project using the default in-worktree location preserves exactly
  the same set of artifacts after this change as before it — no additions, no
  omissions.
- **SC-003**: Zero design artifacts are lost to a failed preservation step; every
  such failure results in a refused removal instead.
- **SC-008**: After any number of failed attempts and retries, the canonical
  preserved result is complete, and the number of stored results equals the number
  of attempts that succeeded — a reader can never mistake a failed attempt's
  leftovers for a real one.
- **SC-004**: Every refused removal tells the operator how to proceed, in both
  directions, without consulting documentation.
- **SC-005**: A developer setting up a new project is presented with the spec
  location choice exactly once, and never sees it again on any later setup run,
  in any worktree.
- **SC-006**: A project that accepts the default choice behaves identically, in
  artifact resolution and teardown, to a project that predates the question.
- **SC-007**: Existing project configurations that call the command by its former
  name continue to complete teardown successfully with no change on their part.

## Assumptions

- Pre-specify design context loaded from `design.md`.
- **The removal tool refuses to remove a worktree when its pre-removal step
  fails.** FR-006 and FR-008 depend entirely on this. It is documented by that
  tool but has not been observed here; it is the first thing to confirm, before
  any implementation.
- The removal tool offers no supported way to skip its pre-removal step, which is
  why FR-008 requires a manual escape route in the message.
- A project configuration file is project-local, so copies predating the rename
  persist indefinitely. FR-019 follows from this, not from general caution.
- The default choice is represented by the absence of a recorded location, and
  this is deliberate — it is what makes FR-012's indistinguishability achievable
  rather than merely asserted.
- Setup that runs automatically during worktree creation is non-interactive and
  therefore silent under FR-011.
- The three presented options and their rendered form are settled in issue #26
  and adopted as specified; this specification does not re-open them.
- Rescuing untracked or uncommitted work from a worktree is a separate concern,
  tracked separately, and out of scope here. The boundary is structural rather
  than arbitrary: work that version control can see makes a worktree read dirty,
  and the removal tool already refuses on that basis. Design artifacts are
  deliberately excluded from version control, so they leave a worktree reading
  clean and no such check can ever see them. This feature covers exactly the
  artifacts nothing else can.
- The health check required by FR-020 is transitional, like the several
  superseded-path checks the project already carries. Their collective removal is
  tracked separately; this specification adds one more on the understanding that
  it is scaffolding with a defined end, not a permanent feature.

## Validation Strategy _(mandatory)_

- **Assumption first**: confirm the removal tool refuses removal on pre-removal
  failure, using a disposable worktree, before any implementation begins. If it
  does not hold, FR-006 through FR-008 must be redesigned.
- **Full test suite and type/lint checks** for the project must pass unchanged.
- **Containment behaviour**: one test per row of the FR-001/002/003 table —
  default location, durable location, and a configured location resolving back
  inside the worktree.
- **Regression guard**: a project with no configured location preserves an
  identical artifact set before and after the change.
- **Refusal path**: at-risk artifacts present and preservation forced to fail →
  non-success result, and the message contains both the retry and the manual
  removal route.
- **Compatibility**: the former command name dispatches identically to the new
  one, and a project configuration still calling it is reported as drift without
  affecting the health check's overall result.
- **Setup prompt**: asked on first interactive setup; silent when
  non-interactive, when confirmation is suppressed, and when already answered;
  default choice records no location; durable choices record to the primary
  checkout and report every file touched; a record made in the primary checkout
  suppresses the question from a worktree.
- **Manual end-to-end**: configure a durable location, run a branch through the
  pipeline, remove the worktree, and confirm the specs are untouched in place
  with no duplicate produced.
