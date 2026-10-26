# Feature Specification: Brainstorm holds until the software design question is answered

**Feature Branch**: `648-design-gate`
**Created**: 2026-10-25
**Status**: Draft
**Input**: Design at `design.md` in this feature folder, from `/speckit.brainstorm` on #648.

## Clarifications

### Session 2026-10-25

- Q: With auto-approve on and nobody watching, may the agent run the claim
  command itself when it decides the change makes no structural choice? → A:
  Yes. The human sign-off is the PR review, since the claim is a committed file
  carrying its reason, and a person merges every PR. This is the same check
  `wfctl arch none` gets.

## User Scenarios & Testing _(mandatory)_

Brainstorm already holds a branch until the architecture question is answered.
This feature adds the same hold for the software design question, which is
whether the change makes a structural choice worth recording. Examples of a
structural choice are which module owns a piece of logic, which pattern fits,
and whether a class is warranted at all.

### User Story 1 - A branch that skipped software design is held (Priority: P1)

An agent finishes brainstorm, writes `design.md`, and answers the architecture
question. It never answers the software design question. `wfctl status` shows
brainstorm as still in progress on a new `software-design` row, and tells the
user the two ways to answer it.

**Why this priority**: This is the whole problem. On #635 an agent answered
software design with a file layout, and the pipeline moved on because nothing
checked.

**Independent Test**: On a branch with `design.md` and an architecture answer
but no software design answer, run `wfctl status` and confirm brainstorm is the
current step and the `software-design` row is held with both answers printed.

**Acceptance Scenarios**:

1. **Given** a branch with `design.md` and an architecture answer, and no record
   under `docs/architecture/design/` and no claim on the pass, **When** the user
   runs `wfctl status`, **Then** brainstorm is current, the `software-design`
   row reads `no software design record for this change`, and the help under
   `next:` reads:

   ```
     Either record the structural choice this change makes — one file under:
         docs/architecture/design/
     or state that it makes none:
         wfctl step none brainstorm.software-design --reason "<why>"
   ```

2. **Given** the same branch, **When** the user runs `wfctl status --json`,
   **Then** brainstorm's `state` is `in_progress`, and its `reason` and `remedy`
   are the software design pass's own.

3. **Given** the same branch under `auto_approve`, **When** an autonomous run
   reaches the end of brainstorm, **Then** it stops at brainstorm rather than
   moving on to specify.

---

### User Story 2 - A design record releases the hold (Priority: P1)

The change makes a structural choice. The agent writes a record with the
`software-design-decisions` skill under `docs/architecture/design/` and commits
it. Brainstorm moves on.

**Why this priority**: A hold with no way out strands every branch. This is the
"yes" answer.

**Independent Test**: On a held branch, commit one file under
`docs/architecture/design/` and confirm the `software-design` row reads done and
specify becomes current.

**Acceptance Scenarios**:

1. **Given** a held branch, **When** the branch commits a file under
   `docs/architecture/design/`, **Then** the `software-design` row reads `●` and
   brainstorm no longer holds.
2. **Given** a design record that was already on `main` before the branch
   started, **When** the branch doesn't touch `docs/architecture/design/`,
   **Then** the pass stays held, because the old record answers some other
   change's question.

---

### User Story 3 - A claim releases the hold (Priority: P1)

The change makes no structural choice. The user runs
`wfctl step none brainstorm.software-design --reason "<why>"`. Brainstorm moves
on, and the reason travels with the branch for the reviewer to read.

**Why this priority**: Many changes have no structural choice, and stating that
with a reason is an answer a reviewer can disagree with. Without it, the only
way past the hold would be an empty record.

**Independent Test**: On a held branch, run the claim command and confirm the
row is hidden from `wfctl status`, shown by `wfctl status --all` as
`claimed: <reason>`, and specify becomes current.

**Acceptance Scenarios**:

1. **Given** a held branch, **When** the user runs
   `wfctl step none brainstorm.software-design --reason "no new module or pattern"`,
   **Then** `wfctl status` no longer shows the `software-design` row and
   brainstorm no longer holds.
2. **Given** that claim, **When** the user runs `wfctl status --all`, **Then**
   the row shows `claimed: no new module or pattern`.
3. **Given** a repository with no `wfctl.json`, **When** the user runs the same
   command, **Then** it succeeds, since the pass is one wfctl ships.
4. **Given** an autonomous run with auto-approve on, **When** the agent decides
   at level 3 that the change makes no structural choice, **Then** the agent runs
   the claim command itself with its reason and commits the claim, and the human
   reviewer reads that reason in the PR.

---

### User Story 4 - The skills ask the question the gate checks (Priority: P2)

An agent running `design-levels` reaches level 3. The skill's description of
level 3 leads with which module owns the logic and which pattern fits, and says
that a file layout or a schema alone doesn't answer it. The skill names
`wfctl step none brainstorm.software-design` as the "no" answer.

**Why this priority**: The gate checks that the question was answered, not that
the answer is right. The skill text is what steers the answer toward a
structural choice. Today level 3's form column leads with "Schemas, contracts",
which is plausibly why the #635 agent answered with a file layout.

**Independent Test**: After `uv run wfctl install-skills --agent claude`, read
the installed `design-levels`, `speckit-brainstorm`, and
`software-design-decisions` skills and confirm each names the claim where it
discusses a change with no structural choice.

**Acceptance Scenarios**:

1. **Given** the installed `design-levels` skill, **When** an agent reads level
   3's row, **Then** its form column leads with module ownership and pattern
   choice, and states that a file layout or schema alone doesn't answer level 3.
2. **Given** the installed `speckit-brainstorm` skill, **When** an agent
   re-enters brainstorm on a branch held by the software design pass, **Then**
   the re-entry paragraph covers that pass and names both answers.
3. **Given** the installed `software-design-decisions` skill, **When** it says a
   choice with no credible alternative earns no record, **Then** it names the
   claim command as the answer to give instead.

---

### User Story 5 - A repo where git can't answer is held until it says why (Priority: P2)

A repo keeps its architecture folder outside the project, so git can never
tell whether a branch added a record. Brainstorm holds the branch on both
checks and names the setting that turns them off. The maintainer sets
`design_record_checks` to `"off"` in `wfctl.json`, and both checks pass from
then on.

**Why this priority**: Previously, the architecture check let these branches
through without saying anything, so the repo never knew the check wasn't
running. Holding them makes the repo decide.

**Independent Test**: In a repo whose architecture folder is outside the
project, run `wfctl status` on a branch with `design.md`, and confirm brainstorm
is held with the remedy. Set `design_record_checks` to `"off"` and confirm both
checks read skipped.

**Acceptance Scenarios**:

1. **Given** a branch with `design.md` where wfctl finds no base branch, **When**
   the user runs `wfctl status`, **Then** brainstorm is held, and the remedy
   names `trunk` and `design_record_checks`.
2. **Given** the same branch, **When** the repo names its base branch with
   `trunk`, **Then** both checks compare against that branch.
3. **Given** a repo with `design_record_checks` set to `"off"`, **When** the user
   runs `wfctl status --all`, **Then** both checks read skipped and say the
   setting turned them off.

---

### Edge Cases

- A branch that already has `spec.md` isn't held by the pass, the same escape
  the architecture pass uses. This keeps branches that passed brainstorm before
  this feature shipped from moving backwards.
- A branch with no `design.md` reads brainstorm as not started, as it does today.
  The new pass doesn't change that.
- When git can't answer whether the branch changed `design/`, the pass holds,
  and so does the architecture pass. That happens in three cases: wfctl finds
  no base branch, the git command fails, or the architecture folder sits outside
  the project. The repo settles the first case by naming its base branch with
  `trunk` in `wfctl.json`, and the third by setting `design_record_checks` to
  `"off"`. A failing git command is a broken checkout, and the user fixes it
  outside wfctl.
- A repository that declares its own pass named `software-design` under
  brainstorm gets a `wfctl check config` finding, and its pass is dropped, as for
  any name that matches a built-in pass.
- Pass names in `wfctl status` line up with their glyphs, including the longest
  name. Today `plan-walkthrough` runs into its glyph.
- A claim and a record on the same branch: the claim wins, as it does for every
  claimed pass.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: Brainstorm MUST have a third built-in pass named
  `software-design`, ordered between `architecture` and `design-doc`.
- **FR-002**: The pass MUST read done when the branch has touched
  `<arch-root>/design/`, using the same branch-relative check the architecture
  pass uses for the arch root.
- **FR-003**: When the pass is outstanding, it MUST hold brainstorm with the
  reason `no software design record for this change`, and a remedy naming both
  answers, as shown in User Story 1.
- **FR-004**: The pass MUST accept a claim written by
  `wfctl step none brainstorm.software-design --reason "…"`, with no
  `wfctl.json` required.
- **FR-005**: The pass MUST NOT hold a branch that has `spec.md`.
- **FR-006**: When git can't answer, the pass and the architecture pass MUST
  both hold brainstorm. The reason MUST say that git couldn't answer, and the
  remedy MUST name `trunk` and `design_record_checks` in `wfctl.json`.
- **FR-006a**: When `wfctl.json` sets `design_record_checks` to `"off"`, the pass
  and the architecture pass MUST both read skipped without asking git, and
  `wfctl status --all` MUST show each one as turned off by that setting.
- **FR-006b**: `wfctl check config` MUST report a `design_record_checks` value
  other than `"on"` or `"off"`. It MUST also report an architecture folder
  outside the project when `design_record_checks` isn't `"off"`, since every
  branch there would be held.
- **FR-007**: `wfctl status` MUST size the pass name column to the longest pass
  name shown, so every glyph is separated from its name.
- **FR-008**: The `design-levels` skill MUST lead level 3's form column with
  module ownership and pattern choice, MUST state that a file layout or schema
  alone doesn't answer level 3, and MUST name the claim as the "no" answer.
- **FR-009**: The `speckit-brainstorm` skill MUST cover the software design pass
  in its re-entry paragraph, and MUST name the claim where it says a level was
  answered with no record.
- **FR-009a**: Under auto-approve, the `speckit-brainstorm` skill MUST let the
  agent write the claim itself, with a reason, and commit it so the human
  reviewer sees it in the PR. The skill MUST NOT add a separate sign-off step for
  the claim.
- **FR-010**: The `software-design-decisions` skill MUST name the claim where it
  says a choice with no credible alternative earns no record.
- **FR-011**: The change MUST commit a release note, `changes/648.change.md`,
  since a branch that used to leave brainstorm now stops there.

## Key Entities _(include if feature involves data)_

- **Software design record**: A file under `<arch-root>/design/` holding one
  structural choice, written by `software-design-decisions`. It is durable and
  never binding.
- **Claim**: A file written by `wfctl step none` that says a pass doesn't apply
  to this change, with a reason. wfctl reads it before the pass's own reader.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A branch with `design.md` and an architecture answer, and neither
  a software design record nor a claim, can't leave brainstorm. This holds in
  both attended and autonomous runs.
- **SC-002**: Each of the two answers releases the hold in one command or one
  commit, with no `wfctl.json` edit.
- **SC-003**: Every branch that already has `spec.md` reports the same pipeline
  position before and after this change.
- **SC-004**: All three skills that discuss a change with no structural choice
  name the same claim command.
- **SC-005**: A branch where git can't answer never leaves brainstorm silently.
  It is held with a remedy, or the repo has set `design_record_checks` to
  `"off"`.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, with new tests for each state: held, released by a record,
  released by a claim, not held past `spec.md`, held when git can't answer,
  turned off by `design_record_checks`, and the column width.
- `uv run ruff check wfctl/ tests/` and `uv run mypy`.
- `uv run wfctl verify` and `uv run wfctl doctor`.
- `uv run wfctl install-skills --agent claude`, then on a scratch branch with
  `design.md` and an architecture answer, confirm brainstorm holds on
  `software-design`, and that a design record and the claim each release it.

## Assumptions

- Pre-specify design context loaded from `design.md` in this feature folder.
- The "no" answer is `wfctl step none`, not a new verb. The reasoning is in
  `docs/architecture/design/software-design-none-is-a-claim.md`.
- This feature doesn't wait on #635. The claim moves with every other claim
  wherever #635 puts them. If #635 merges first, its gate ignores
  `declarations/`, so after the rebase this branch runs `wfctl arch none` again
  at the new location.
- The pass checks that the question was answered, not that the record is about a
  structural choice. That's the same limit the architecture pass has.
- Holding when git can't answer amends
  `docs/architecture/promised-evidence-blocks-on-silence.md`. Other checks that
  read git still let the branch through, because nothing in the repo can settle
  their question.
- Tying the check to the domain contexts a change touches is out of scope and
  tracked in #649.
