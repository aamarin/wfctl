# Feature Specification: Read review.commands from the trunk

**Feature Branch**: `711-review-commands-from-trunk`
**Created**: 2026-11-03
**Status**: Draft
**Input**: User description: "From design.md for #711: review start reads review.commands from the trunk's wfctl.json and warns on a branch difference."

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A branch can't change the reviewer command its own review runs (Priority: P1)

A repository declares a command for each model other than Claude under
`review.commands` in `wfctl.json`. The review skill runs that command. When a
branch changes the command, `wfctl review start` on that branch prints the
trunk's command for each reviewer, so the branch's review runs the command the
trunk holds. A warning names the model, the branch's command, and the trunk's,
so the user can see the branch wants a different reviewer.

**Why this priority**: This is the hole #711 closes. On #710 a branch added a
command and its own panel ran it before the change merged.

**Independent Test**: Commit a `wfctl.json` with `"codex": "codex exec --sandbox read-only"`
on `main`, change it to a different command on a branch, and run `wfctl review start security`.
The roster shows the trunk's command, and a `⚠` line names the difference.

**Acceptance Scenarios**:

1. **Given** the trunk sets `codex` to command A and the branch sets it to command B, **When** the user runs `wfctl review start <group>` with codex reviewers, **Then** the roster prints command A beside each codex reviewer, `run.json` records command A, and a warning names codex, command B, command A, and the trunk ref.
2. **Given** the branch and the trunk set the same commands, **When** the user runs `wfctl review start`, **Then** no warning about commands is printed.

---

### User Story 2 - A model the trunk has no command for is left out (Priority: P2)

When a branch adds reviewers for a model the trunk has no command for, those
reviewers can't run until the change merges. `review start` marks them
unavailable, the same way as a reviewer whose program isn't on `PATH`, and the
run completes on the reviewers that can run.

**Why this priority**: Without it, a new model's command would come from the
branch after all, or the run would fail outright.

**Independent Test**: On a branch that adds a `gemini` command and gemini
reviewers, with no `gemini` command on `main`, run `wfctl review start`.

**Acceptance Scenarios**:

1. **Given** the branch sets a command for gemini and the trunk sets none, **When** the user runs `wfctl review start` for a group with gemini reviewers, **Then** those reviewers read `✗ unavailable`, a `⚠` line says gemini has no command on the trunk and names the ids left out, and a warning says the branch's gemini command waits on the merge.
2. **Given** the trunk lists a custom group with codex reviewers and a codex command, and the branch removes both the group and the command, **When** the user runs `wfctl review start` for that group, **Then** the codex reviewers print the trunk's command and a warning says the branch sets no command for codex. A branch that keeps codex reviewers without a command is refused by `load`, as today, so a group the branch removed is the only way to reach this case.

---

### User Story 3 - A broken trunk file is refused as it is today (Priority: P3)

When the trunk's `wfctl.json` can't be read, or its `review.commands` isn't
valid, `review start` refuses with a `✗` line naming the file, as it already
does. The same file lists the groups the branch must review, and CI can't read
that list from a broken file either, so a run started anyway would end in a PR
CI refuses (`test_start_refuses_when_the_trunks_file_cannot_be_read`).

The #711 handoff asked for a warning and a fallback to Claude reviewers here,
by analogy with `review.rounds`. That analogy doesn't hold: the group check
validates the trunk's commands before `review start` reads them, and the round
cap is the one key it leaves unchecked. Making the fallback reachable would
mean changing the reader the worktree guard and CI share, which this change
stays out of.

**Why this priority**: It's the failure path, and it keeps today's behavior.

**Independent Test**: Commit a `wfctl.json` on `main` whose `review.commands`
isn't an object of strings, and run `wfctl review start` on a branch.

**Acceptance Scenarios**:

1. **Given** the trunk's `review.commands` isn't valid, **When** the user runs `wfctl review start`, **Then** it exits 1 with a `✗` line naming `wfctl.json` on the trunk and the problem, and writes no run.
2. **Given** the trunk has no `wfctl.json` or no `review.commands`, **When** the user runs `wfctl review start`, **Then** the trunk has no commands, so every non-Claude reviewer is unavailable, and a branch command gets the difference warning.

### Edge Cases

- The branch's own `wfctl.json` is invalid: `review start` refuses before reading the trunk, as it does today.
- The trunk names Claude in `review.commands`: that's not a valid declaration, so `review start` refuses as for any invalid trunk file.
- The trunk ref can't be found at all: `review start` refuses as it does today for `review.rounds`, since the commit range needs the same trunk.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: `wfctl review start` MUST take each non-Claude reviewer's command from `review.commands` in `wfctl.json` on the trunk ref `trunk_rounds` reads, not from the working tree.
- **FR-002**: When the working tree's `wfctl.json` sets a valid `review.commands`, `review start` MUST print one warning per model whose command differs from the trunk's, naming the model, both values or the missing side, and the trunk ref. A branch whose file sets no `review.commands` gets no command warning, the way a branch that sets no `review.rounds` gets no cap warning, since a branch cut before the trunk added a command would otherwise warn on every start.
- **FR-003**: A non-Claude reviewer whose model has no command on the trunk MUST be recorded and printed as unavailable, with a reason naming the trunk ref.
- **FR-004**: When the trunk's `wfctl.json` can't be read or its `review.commands` isn't valid, `review start` MUST keep refusing as it does today, through the group check.
- **FR-005**: A trunk with no `wfctl.json`, no `review` key, or no `review.commands` MUST give no commands, with no warning of its own.
- **FR-006**: The groups, skills, and reviewer counts MUST keep coming from the same sources they do today.
- **FR-007**: `wfctl check config` MUST keep validating the working tree's `review.commands` unchanged.

## Key Entities _(include if feature involves data)_

- **Reviewer command**: the shell command that starts one model other than Claude, keyed by model name under `review.commands`.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: On a branch whose `wfctl.json` sets a different command than the trunk, 100% of the commands `review start` prints and records are the trunk's.
- **SC-002**: On a branch that sets `review.commands`, every difference from the trunk's produces exactly one warning line.
- **SC-003**: A broken trunk file stops `review start` exactly as it does today, with no new refusal and no new fallback.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, with new tests for each acceptance scenario above, written failing first.
- `uv run ruff check wfctl/ tests/` and `uv run mypy`.
- A manual run of `uv run wfctl review start security` in this worktree, with `WFCTL_STATE_DIR` pointing at a scratch folder so the run uses none of the branch's review rounds, after editing `review.commands` in its `wfctl.json`. It confirms the output prints `main`'s command, and the edit is reverted after.

## Assumptions

- Pre-specify design context loaded from specs/711-review-commands-from-trunk/design.md.
- The decisions in User Stories 1 and 3 come from the #711 handoff, which settled them before the branch existed.
- The groups stay on the branch (design.md, Not doing).

## Clarifications

### Session 2026-11-03

- Q: Which models does the difference warning compare, every model either side's `review.commands` sets or only the models in the group being started? → A: Every model either side sets. Basis: the issue asks for a warning whenever "the branch's copy sets a different command", and the `review.rounds` warning prints whichever group starts. A branch that adds a command ahead of the reviewers that use it would otherwise never be warned about.
- Q: When the trunk's commands can't be read, does `review start` also print a difference warning per model? → A: No, only the fallback warning. Basis: comparing against a file wfctl couldn't read would say the trunk sets no command, which may be false, and the fallback warning already says every non-Claude reviewer is left out. (Superseded after the plan review: a broken trunk file is refused before any warning prints, so neither warning applies. See User Story 3.)
