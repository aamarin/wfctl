# Feature Specification: A merge install mode for hooks in a consumer-owned settings file

**Feature Branch**: `85-hook-merge-install-mode`
**Created**: 2026-09-01
**Status**: Draft
**Input**: User description: "$ARGUMENTS" (no text supplied; pre-specify design context loaded from `specs/85-hook-merge-install-mode/design.md`)

## Clarifications

### Session 2026-09-01

- Q: Should #85 ship with a fallback digest, or block on #111, so the hook has
  visible content on day one — or is an initially-silent hook (populated once
  #111's `digest.md` lands separately) the intended rollout? → A: Ship #85
  independently. The hook reads installed digests at runtime (FR-012), so #85
  and #111 are decoupled regardless of merge order — confirmed in #111's own
  body, which names #85 as its missing half, and `digest.md` for
  `conversation-response-shape` already exists on #111's unmerged branch. An
  initially-silent hook is the designed degrade path, not a gap.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Install the hook without disturbing what's already there (Priority: P1)

A consumer running `install-skills` for a repo gets a `UserPromptSubmit` hook
added to `.claude/settings.json` that re-injects a skill's core rules every
turn — without losing any permission, hook, or setting they already had in
that file, and without having ever hand-edited it themselves.

**Why this priority**: This is the whole feature. Nothing else in scope has
value if install can silently destroy a consumer's own settings — that is
exactly the failure the two existing install modes have when pointed at this
file.

**Independent Test**: Start from a `.claude/settings.json` carrying the
consumer's own permissions and an unrelated hook. Run
`wfctl install-skills --agent claude`. Confirm the wfctl entry is present and
every other byte of the file is unchanged. Also test the file's absence: with
no `.claude/settings.json` at all, confirm install creates one containing only
the wfctl entry.

**Acceptance Scenarios**:

1. **Given** a `.claude/settings.json` with the consumer's own permissions and
   hooks, **When** `install-skills --agent claude` runs, **Then** a wfctl
   hook entry is added and every pre-existing entry is byte-identical to
   before.
2. **Given** no `.claude/settings.json`, **When** install runs, **Then** a
   valid file is created containing only the wfctl entry.
3. **Given** a `.claude/settings.json` that is not valid JSON, **When**
   install runs, **Then** that one target fails with a clear error, and every
   other install target (skills, commands, `.specify/`) still completes.

---

### User Story 2 - Reinstalling keeps the hook current, never duplicated (Priority: P2)

A consumer re-runs `install-skills` after wfctl ships a change — a new skill
with a digest, an updated digest command — and their settings file ends up
with exactly one wfctl entry per managed event, reflecting the current
bundle. `wfctl doctor` tells them when a previously-installed entry has
fallen behind.

**Why this priority**: The hook's entire reason to exist is that it stays
current as skills change (see Problem Statement in `design.md`) — a merge
mode that only handles the first install and then drifts silently defeats
the purpose as thoroughly as the two modes it replaces.

**Independent Test**: Install once, change what the bundle would produce (a
new skill digest becomes available), reinstall, and confirm the existing
entry is replaced in place rather than duplicated. Separately, run
`wfctl doctor` against a stale entry and confirm it is reported.

**Acceptance Scenarios**:

1. **Given** a wfctl hook entry already installed, **When**
   `install-skills --agent claude` runs again with nothing changed, **Then**
   the file is not opened for writing at all.
2. **Given** a wfctl hook entry whose command no longer matches what the
   current bundle would install, **When** install runs, **Then** that one
   entry is replaced in place and no second entry is added.
3. **Given** an installed entry that is missing or behind, **When**
   `wfctl doctor` runs, **Then** it reports the specific condition (missing
   vs. behind) and names the fix command.

---

### User Story 3 - Uninstall removes only what wfctl owns (Priority: P3)

A consumer running `uninstall-skills` gets wfctl's hook entries removed and
nothing else in `.claude/settings.json` touched — including a hand-written
hook that happens to share the same event group.

**Why this priority**: Lower than install and currency because a consumer
who never uninstalls never needs this, but it is the safety net for the ones
who do, and getting it wrong (deleting a foreign entry, or leaving wfctl's
behind) breaks trust in every other mode's uninstall too.

**Independent Test**: Install the hook alongside a hand-written hook in the
same event group, run `uninstall-skills`, and confirm wfctl's entry is gone,
the hand-written one remains, and the group itself is only pruned when
empty.

**Acceptance Scenarios**:

1. **Given** wfctl's hook is the only entry in its group, **When**
   `uninstall-skills --agent claude` runs, **Then** the entry is removed and
   the now-empty group is pruned.
2. **Given** the consumer's own command shares the group with wfctl's entry,
   **When** uninstall runs, **Then** wfctl's entry is removed, the group is
   kept, and the consumer's command is untouched.
3. **Given** no wfctl entry is present, **When** uninstall runs, **Then**
   the file is not opened for writing.

---

### Edge Cases

- A settings file with a `UserPromptSubmit` array that already contains a
  matcher group holding both a foreign command and a stale wfctl entry:
  install must replace only the wfctl one.
- No skill on disk carries a digest yet: the hook command must exit 0 with no
  output rather than printing something misleading or erroring.
- A consumer deletes the settings file's write permission or the path is
  read-only: install must report a clear failure for that target without
  aborting the rest of the run.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: Install MUST add or replace a single wfctl-owned entry per
  managed event in `.claude/settings.json` without modifying any other
  entry, permission, or setting already in the file.
- **FR-002**: Install MUST create a valid `.claude/settings.json` containing
  only the wfctl entry when no such file exists.
- **FR-003**: Install MUST find its own entry by the command it runs (a
  recognizable prefix) rather than by a remembered position, so a consumer
  editing around it does not strand or duplicate the entry.
- **FR-004**: Re-running install with an already-current entry MUST NOT open
  the file for writing.
- **FR-005**: Re-running install with a stale entry MUST replace that entry
  in place; it MUST NOT produce a second wfctl entry.
- **FR-006**: Uninstall MUST remove only entries matching wfctl's command
  pattern, leaving every other entry — including a consumer's own command in
  the same event group — untouched.
- **FR-007**: Uninstall MUST prune a matcher group only once it holds no
  entries other than wfctl's own.
- **FR-008**: Uninstall MUST NOT open the file for writing when no wfctl
  entry is present.
- **FR-009**: `wfctl doctor` MUST report, per agent, whether the managed
  entry is current, missing, or present but not matching what the current
  bundle would install.
- **FR-010**: A `.claude/settings.json` that fails to parse as JSON MUST
  fail loudly for that target alone and MUST NOT prevent any other install
  target from completing.
- **FR-011**: The installed entry MUST invoke a wfctl subcommand; it MUST
  NOT embed skill text directly in `settings.json`.
- **FR-012**: The subcommand the entry invokes MUST print the digest of
  every installed skill that carries one, and MUST produce no output when
  none are installed.
- **FR-013**: The merged path MUST NOT be added to the gitignored set that
  every mirrored install path uses.
- **FR-014**: The merged path MUST NOT be recorded in the manifest's
  mirrored-items list; its presence is recorded separately so uninstall can
  find and edit it without deleting the whole file.
- **FR-015**: Merge mode applies only to the Claude Code agent target in
  this scope; it MUST NOT be offered for agents whose settings schema does
  not define an equivalent hook mechanism.

## Key Entities

- **Managed hook entry**: one JSON object inside a consumer's
  `.claude/settings.json`, identified by a command prefix wfctl owns rather
  than by position or a marker key. Replaced on install, removed on
  uninstall, left alone by every other write to the file.
- **Digest**: the short, per-skill text a managed entry's command prints.
  Lives in a file next to the skill it belongs to, not in the skill's
  frontmatter and not pasted into `settings.json`.
- **Merged-path record**: manifest bookkeeping distinct from the mirrored
  `items` list — tracks that a merge entry exists so uninstall and doctor
  can locate it without treating the whole settings file as wfctl's.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: After install, 100% of the consumer's pre-existing
  `settings.json` content (permissions, other hooks) is unchanged, verified
  by comparing the file before and after with the wfctl entry excluded.
- **SC-002**: Any number of repeated installs leaves exactly one wfctl entry
  per managed event — never zero after a successful install, never more
  than one.
- **SC-003**: A consumer can determine the hook's state — current, missing,
  or behind — from a single `wfctl doctor` run, with no manual file
  inspection.
- **SC-004**: Uninstall removes 100% of wfctl's entries and 0% of the
  consumer's own, including when both share a matcher group.
- **SC-005**: The re-anchoring rule reaches the model on every turn of a
  session, not only at session start — verified by the hook firing on every
  `UserPromptSubmit` event, closing the decay gap named in the Problem
  Statement.

## Assumptions

- Pre-specify design context loaded from `specs/85-hook-merge-install-mode/design.md`;
  this spec reflects decisions already settled there rather than re-opening
  them.
- Reflowing the consumer's `settings.json` (key order, indentation) on the
  one install that changes something is an acceptable cost, matching how
  every JSON-writing config tool that owns part of a shared file behaves.
  Not yet confirmed with a consumer; carried forward from `design.md`.
- The digest each managed skill prints is supplied by #111 (`digest.md`
  per skill). This spec covers the mechanism that delivers whatever digest
  exists; it does not define digest content. #85 and #111 merge
  independently in either order — resolved in Clarifications above. Until
  #111 merges, the hook command runs correctly and prints nothing, which is
  intended behavior (FR-012), not a placeholder to remove later.
- Scope is limited to repo-local `.claude/settings.json` and the
  `UserPromptSubmit` event for the Claude Code agent, per the MVP scope in
  `design.md`. Global `~/.claude/settings.json`, additional events, and
  additional agents are explicitly out of scope for this feature.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`
  — the project's standing definition of done.
- A round-trip test per story: a settings file with pre-existing foreign
  entries → install → assert foreign entries byte-identical and the managed
  entry present and correctly formed → uninstall → assert the file matches
  the pre-install original.
- A malformed-JSON test: confirm that target fails alone and every other
  install target still completes.
- A `wfctl doctor` test per reported state: current, missing, behind.
- Manual: run a session against a repo with the hook installed and confirm
  it fires each turn and prints what `wfctl hook user-prompt` produces
  standalone.
