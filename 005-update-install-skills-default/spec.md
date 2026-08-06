# Feature Specification: update-install-skills-default

**Feature Branch**: `005-update-install-skills-default`
**Created**: 2026-07-29
**Status**: Draft
**Input**: GitHub issue #5 — "default to agents-only, add `--agent copilot` target" — plus the tracker-consent work already on this branch, folded in as related infrastructure.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Install without declaring an agent (Priority: P1)

A developer sets up a new repo and runs `wfctl install-skills` with no flags. They get the skills and command definitions in one canonical, agent-agnostic place, and nothing that presumes which AI assistant they use. Today the same command writes `.claude/` shims whether or not Claude is in play, so a repo used with Copilot or Bob carries a second copy of every command that nothing reads — and a reader cannot tell which copy is authoritative.

**Why this priority**: This is the defect. Every other story in this spec is either a consequence of it or an opt-in built on top of it. Delivered alone, it removes the duplication that prompted the issue.

**Independent Test**: Run `wfctl install-skills` in a scratch repo. Confirm the repo contains agent-agnostic skills and commands, contains no assistant-specific directory, and that the recorded install manifest lists only agent-agnostic paths.

**Acceptance Scenarios**:

1. **Given** a repo that has never had skills installed, **When** the developer runs `wfctl install-skills` with no flags, **Then** the repo gains the agent-agnostic skills and commands, and no assistant-specific directory is created.
2. **Given** that same install, **When** the developer inspects the install summary, **Then** it reports how many skills, commands, and runtime files were installed as separate figures rather than one combined total.
3. **Given** that same install, **When** the developer looks for guidance, **Then** the output names the assistants that need their own paths and the exact command to add each one.

---

### User Story 2 - Upgrade an existing repo without alarm (Priority: P2)

A developer whose repo was set up under the old default upgrades wfctl and re-runs the install. The upgrade is silent: no prompt claiming their files are about to be overwritten, no backup copies of content wfctl itself installed.

**Why this priority**: Without this, story 1 makes every existing repo's first upgrade look like data loss — a prompt listing dozens of "existing files that will be overwritten," followed by a backup directory full of wfctl's own content. That converts a routine default change into an incident. It is separable from story 1 only in the sense that it can be built and tested after it.

**Independent Test**: Construct a repo whose install record has the old shape (agent-agnostic paths recorded as belonging to an assistant), run the install, and confirm the run completes with no overwrite prompt and no new backup entries.

**Acceptance Scenarios**:

1. **Given** a repo installed under the previous default, **When** the developer re-runs the install after upgrading, **Then** no overwrite confirmation is shown and no backup files are created.
2. **Given** a repo with a base install already present, **When** the developer adds an assistant layer, **Then** the shared agent-agnostic files are recognised as already owned and are not backed up.
3. **Given** a file the developer wrote themselves at a path wfctl wants, **When** the install runs, **Then** it is still detected, still backed up, and still restorable — the relaxation applies only to content wfctl installed.

---

### User Story 3 - Add support for a specific assistant (Priority: P3)

A developer whose assistant does not read the agent-agnostic layout adds it explicitly: one command, and that assistant's own paths appear alongside the canonical ones. A developer using an assistant that has no repo-local path is told so plainly and still gets a working install.

**Why this priority**: The opt-in half of story 1. Valuable only once the default is agent-agnostic, and each assistant is independently testable, so this can land incrementally — one assistant at a time.

**Independent Test**: Run the install once per supported assistant in separate scratch repos and confirm each produces that assistant's expected layout and nothing belonging to another.

**Acceptance Scenarios**:

1. **Given** any repo, **When** the developer installs for Claude, **Then** they get today's Claude layout unchanged, including native-skill mirroring for skills marked for it.
2. **Given** any repo, **When** the developer installs for Copilot, **Then** the skills appear in Copilot's repo-local skills location, unmodified in content.
3. **Given** any repo, **When** the developer installs for Codex, **Then** the command explains that Codex reads no repo-local command path, installs the agent-agnostic layer anyway, and reports success rather than failure.
4. **Given** a repo with two assistants installed, **When** the developer removes one, **Then** the other assistant's files and the shared agent-agnostic files are left intact.
5. **Given** an unrecognised assistant name, **When** the developer runs the install, **Then** it fails with the list of names it does accept.

---

### User Story 4 - Choose an issue tracker deliberately (Priority: P4)

A developer installing into a repo that has never chosen an issue tracker is asked once whether to add the shipped GitHub backend. Declining explains both ways to set one later. An automated run — a hook, CI — is never asked and never has a tracker chosen for it.

**Why this priority**: Same defect as story 1 in a different place: the tool deciding something repo-specific on the developer's behalf. Folded in because it shares the release, the documentation section, and the reasoning. Already implemented on this branch; carried here so the spec describes the whole change.

**Independent Test**: Run the install interactively and answer both ways; run it again with input redirected and confirm no prompt appears and no tracker config is written.

**Acceptance Scenarios**:

1. **Given** a repo with no tracker chosen, **When** a developer installs interactively, **Then** they are asked once, and answering yes installs the GitHub backend.
2. **Given** the same prompt, **When** the developer declines, **Then** the output names both routes to setting one later, and no tracker config is written.
3. **Given** a repo with no tracker chosen, **When** the install runs without an interactive terminal or with the skip-confirmation flag, **Then** no prompt appears and no tracker is chosen.
4. **Given** a repo that already chose a tracker and edited its configuration, **When** the install runs again, **Then** both the choice and the edits survive untouched.

---

### Edge Cases

- **Assistant layer installed into a repo with no base layer** — installing for an assistant always installs the agent-agnostic layer too, so a single command works on a fresh repo.
- **Removing the last assistant** — the agent-agnostic layer survives, because it is not owned by any assistant. This is a change from today, where removing the assistant takes the skills with it.
- **Removing an assistant that was never installed** — reports that there is nothing to remove rather than failing.
- **Source content missing from the upstream skills repo** — an expected source directory that is absent warns and is skipped; the rest of the install proceeds. Unchanged from today.
- **Two assistants installed in one repo** — supported, and the reason the layout rule below exists. No two layers may claim the same destination.
- **Copilot does not discover the skills location** — see Assumptions; the fallback is the assistant-specific command format the issue originally described, and it changes nothing else in this spec.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The install MUST always place skills and command definitions in an agent-agnostic location, regardless of which assistant is requested.
- **FR-002**: The install MUST NOT create any assistant-specific files unless that assistant is explicitly requested.
- **FR-003**: Requesting an assistant MUST add that assistant's files in addition to — never instead of — the agent-agnostic layer.
- **FR-004**: No two assistants, and no assistant and the agent-agnostic layer, may write to the same destination. This MUST be enforced by an automated check, not by convention. (Measured by SC-006.)
- **FR-005**: The install MUST treat any path it previously installed — under any assistant — as its own, and MUST NOT back it up or prompt to overwrite it.
- **FR-006**: The install MUST still detect, back up, and restore files the developer created at a destination path.
- **FR-007**: Removing an assistant MUST remove only that assistant's files.
- **FR-008**: Requesting an assistant with no repo-local command path MUST explain why, install the agent-agnostic layer, and report success.
- **FR-009**: Requesting an unrecognised assistant MUST fail and list the accepted names.
- **FR-010**: After an install that added no assistant layer, the output MUST name the supported assistants and the command to add each.
- **FR-011**: The install summary MUST report counts per layer and per kind of content, so the reported figures cannot be mistaken for a number of skills.
- **FR-012**: A repo that has never chosen an issue tracker MUST be asked once, interactively, before one is installed.
- **FR-013**: An install with no interactive terminal, or with confirmations suppressed, MUST NOT choose a tracker.
- **FR-014**: Declining the tracker MUST state how to add the shipped backend later and how to author a custom one.
- **FR-015**: An existing tracker choice, and local edits to its configuration, MUST survive later installs.
- **FR-016**: Documentation MUST describe the new default and the opt-in commands, and the release MUST be versioned as a breaking change to the default.

## Related Context and Decisions

- `.agent/spec.md` — the design this spec formalises, including the rejected alternatives and their reasons.
- GitHub issue #5 — original scope. This spec diverges from it in four places, listed in Assumptions.
- GitHub issue #6 — researches whether the per-assistant command layout is deprecated across vendors. Explicitly out of scope here; it may supersede parts of story 3 later.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A repo installed with no flags contains zero assistant-specific files.
- **SC-002**: Upgrading a repo installed under the old default produces zero overwrite prompts and zero backup files.
- **SC-003**: Adding support for an assistant takes exactly one command, and that command works whether or not the repo was set up before.
- **SC-004**: Every figure in the install summary matches something a developer can count on disk — no total that conflates skills, commands, and runtime files.
- **SC-005**: A repo that declines the tracker prompt, or never sees it, contains no tracker configuration.
- **SC-006**: Every destination across the agent-agnostic layer and all assistant layers is unique, verified automatically.
- **SC-007**: No existing capability regresses: the full test suite passes, and the Claude layout is byte-for-byte what it was before this change.

## Assumptions

- **"Assistant" is this document's word for what the code calls an agent.** The spec is written for a reader who does not know the codebase, so it names the concept rather than the flag. Everywhere downstream — plan.md, contracts/cli.md, tasks.md, and the code — the same thing is an *agent* (`--agent`, `_AGENT_TARGETS`, an agent layer). The two terms are interchangeable; the drift is deliberate, not an inconsistency.
- **Pre-specify design context loaded from `.agent/spec.md`.** That document carries the alternatives considered, the reasons for rejecting them, and the research into how comparable tools solve the same problem. This spec formalises its conclusions.
- **Divergences from issue #5**, all decided during design and recorded in `.agent/spec.md`: the agent-agnostic layer includes command definitions rather than skills alone; Copilot targets the skills location rather than the assistant-command format the issue names; the ownership collision is removed by construction rather than repaired; and the unsupported-assistant case informs and succeeds rather than failing.
- **Copilot discovers repo-local skills.** Inferred from how a comparable tool configures the same assistant, not observed directly. Validated during implementation by installing into a scratch repo and confirming discovery. If it fails, the fallback is the assistant-command format from issue #5, which changes nothing else in this spec.
- **Assistant-specific skill frontmatter degrades gracefully.** Skill metadata carrying assistant-specific keys is expected to be ignored, not rejected, by other assistants. Verified in the same scratch-repo check.
- **Template section removed.** `spec-template.md` is shared with a web application and mandates a PFMS Impact Assessment (workspace isolation, access policies, schema tiers) and a `pnpm type-check` validation step. None of those concepts exist in this repository, so the section was removed per the template's own instruction to drop inapplicable sections rather than mark them N/A. Its Related Context subsection was kept as a top-level section, and Validation Strategy names this project's checks. Section order and all other headings are preserved.

## Validation Strategy _(mandatory)_

- **Automated**: `uv run pytest` — the full suite. New cases cover the default install's contents, each assistant layer, the unsupported-assistant path, the unrecognised-assistant failure, removal leaving other layers intact, the silent upgrade from an old install record, and the uniqueness of every destination.
- **Manual**: install into a scratch repo with no flags and confirm no assistant-specific directory exists; repeat per assistant and confirm each layout; confirm Copilot discovers the installed skills (validates the assumption above).
- **Evidence**: the install record after a default install lists only agent-agnostic and runtime paths.
