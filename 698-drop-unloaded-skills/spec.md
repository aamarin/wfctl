# Feature Specification: Drop unloaded skills

**Feature Branch**: `698-drop-unloaded-skills`  
**Created**: 2026-11-03  
**Status**: Draft  
**Input**: User description: "Design is in design.md for #698."

## User Scenarios & Testing _(mandatory)_

Every session in a project that installs wfctl's Claude layer loads a listing of
the skills and commands it can call. Each entry costs tokens whether or not the
session uses it. This feature takes out the entries no session uses and lists
each pipeline step once.

### User Story 1 - A new session loads a shorter listing (Priority: P1)

A developer starts a session in a project with wfctl's skills installed and types
a one-word prompt. The listing no longer carries `using-superpowers`,
`verification-before-completion`, or `brainstorm`, and the brainstorm step
appears once, as `/speckit.brainstorm`.

**Why this priority**: The listing is the part of every session's starting cost
that wfctl controls, and this is the whole point of the issue.

**Independent Test**: Install the Claude layer into a clone, run a one-word
headless session, and compare the context size and the listed names with the
same run on `main`.

**Acceptance Scenarios**:

1. **Given** a fresh install of this branch's skills, **When** a session starts,
   **Then** none of the three dropped names is listed, and the brainstorm step
   is listed once.
2. **Given** the same project, **When** `wfctl status` prints
   `/speckit.brainstorm` as the next step and the agent invokes it, **Then** the
   brainstorm workflow loads.
3. **Given** a session that has finished level 4 of `design-levels`, **When** it
   reads what comes next, **Then** it is sent to `wfctl verify` and
   `code-review`, and every skill it is sent to still ships.

---

### User Story 2 - A project that already has a dropped skill loses it (Priority: P1)

A project installed wfctl before this change, so it has the dropped skills under
`.agents/` and `.claude/`. It also has a skill of its own beside them. The
developer upgrades wfctl and runs a session.

**Why this priority**: If the listing shrinks only in fresh installs, every
existing project keeps paying for the dropped entries.

**Independent Test**: Install from `main` into a scratch repo, add a
hand-authored skill, install from this branch, then run `doctor` and the
`--prune` repair.

**Acceptance Scenarios**:

1. **Given** an existing install, **When** `install-skills --agent claude` runs
   without `--prune`, **Then** it lists each dropped path in both layers as no
   longer shipped and removes nothing. A run without `--agent` doesn't diff the
   Claude layer, and `doctor` reports that layer's paths instead.
2. **Given** that state, **When** `doctor` runs, **Then** it reports each dropped
   path and prints the `--prune` command for each layer.
3. **Given** that state, **When** `install-skills --prune` runs for each layer,
   **Then** every dropped path is gone from both layers, the hand-authored skill
   is still there, the tracker config is still there, and `doctor` is green.

---

### Edge Cases

- A project overwrote one of the dropped skills with its own copy before wfctl
  installed. `--prune` puts the project's original back from the backup rather
  than deleting the path.
- A repo's `wfctl.json` declares a pass whose `command` is one of the dropped
  wrappers. `wfctl check config` reports the command as uninstalled, which is
  the correct finding once the command no longer ships.
- An agent calls `Skill(speckit-brainstorm)` by name. The call fails, and
  `wfctl status` still prints `/speckit.brainstorm`, which works.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: wfctl MUST NOT ship the `using-superpowers`,
  `verification-before-completion`, or `brainstorm` skills, or their command
  wrappers.
- **FR-002**: The Claude layer MUST NOT install `speckit-brainstorm` under
  `.claude/skills/`. The skill MUST still ship under `.agents/skills/`, since
  `/speckit.brainstorm` reads it there.
- **FR-003**: `/speckit.brainstorm` MUST stay model-invocable, and its
  description MUST name the moment the dropped `brainstorm` skill fired on: a
  new feature or major change that needs design thinking before code.
- **FR-004**: No file wfctl ships MUST name a dropped skill as something to load
  or read. `design-levels` and `python-pattern-selection` MUST name `wfctl
  verify` where they named `verification-before-completion`.
- **FR-005**: The third-party notices and the `vendor-upstream-skills` record
  MUST stop listing the two dropped superpowers skills.
- **FR-006**: An install over a project that has a dropped skill MUST follow the
  existing orphan rule: report it on a bare run, and remove it on `--prune`, only
  when wfctl's manifest recorded the path.
- **FR-007**: A test MUST cover FR-006 for a mirrored skill across both layers,
  with a hand-authored skill and the tracker config left in place.
- **FR-008**: `model-the-domain`, `receiving-code-review`,
  `python-pattern-selection`, and `python-package-layout` MUST keep shipping and
  stay in the Claude listing.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A one-word session in a clone with this branch installed loads
  fewer tokens than the same session in a clone of `main` (39,789 on
  2026-11-03).
- **SC-002**: The Claude listing has four fewer entries than on `main`, and the
  brainstorm step appears once.
- **SC-003**: Every skill and command wfctl ships has either a recorded load in
  the five weeks the issue measured, or a skill that names it.
- **SC-004**: After the upgrade and one `--prune` repair, an existing project
  has none of the four removed `.claude/skills/` entries, and keeps every file it
  wrote itself.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy`.
- `uv run wfctl install-skills --agent claude --prune --yes`, then `uv run wfctl
  doctor`, in this worktree.
- The scratch-repo upgrade from User Story 2, run by hand with this branch's
  bundle.
- `claude -p hi --output-format stream-json` in a clone of `main` and in a clone
  with this branch installed, with both context sizes in the PR.

## Assumptions

- Pre-specify design context loaded from `specs/698-drop-unloaded-skills/design.md`.
- The load counts in the issue are taken as given. They cover one user's
  sessions, which is why `model-the-domain` stays.
- `/start-session` keeps running the `--prune --yes` repair when `doctor`
  reports drift, which is how existing projects lose a dropped skill without a
  person running anything.

## Clarifications

### Session 2026-11-03

- Q: Should a bare `install-skills` remove a dropped skill without `--prune`? → A: No. The existing orphan rule stands: a bare run reports it, and `--prune` removes it. Basis: the manifest records paths and backups but no content, so a bare removal would delete a copy the project edited (`install-modes`, the orphan comment in `cli.py`), and `/start-session` already runs the `--prune --yes` repair. Asked and answered unattended from the repository.
- Q: Should the `brainstorm` command wrapper keep shipping for agents that read `.agents/commands/`? → A: No, it is dropped with its skill. Basis: `/speckit.brainstorm` ships to the same directory and leads to the same step, and nothing in `wfctl/` or this repo's `wfctl.json` names `/brainstorm`.
- Q: What is SC-001 measured against? → A: A clone of `main` measured the same day with the same command, 39,789 tokens on 2026-11-03. Basis: the issue's 38.8k came from an earlier `main`, and the harness grew about 1k since then, so the absolute number would measure changes this branch didn't make. The PR reports both numbers.
