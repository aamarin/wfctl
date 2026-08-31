# Feature Specification: deployment key metadata

**Feature Branch**: `59-deployment-key-metadata`
**Created**: 2026-08-30
**Status**: Draft
**Input**: Issue #59 — "Move the `deployment` frontmatter key under `metadata` to match the Agent Skills spec", refined through `/speckit.brainstorm` into a different direction (see Assumptions).

## Clarifications

### Session 2026-08-30

- Q: Is conformance to the Agent Skills frontmatter contract enforced by the test suite, or verified once by hand during implementation? → A: Enforced by the suite, offline — a test pins the allowed key set and exempts the vendored skill by name. Adopting the upstream reference validator itself stays with #60.
- Q: The vendored skill declines model-initiated invocation in its own frontmatter, so mirroring makes it listed but never self-invoking. Include it in the discoverable set anyway? → A: Yes, with the claim narrowed — loadable on request, not self-correcting. #108 remains open for the unprompted half, which needs a wfctl-owned layering skill.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Shipped skills pass a conformance check (Priority: P1)

Someone points a standards conformance checker at the skills wfctl installed
into their repo — their own CI, a client's loader, a reviewer's spot check. Every
skill wfctl authored comes back clean, so "wfctl ships valid Agent Skills" is a
true statement rather than an aspiration.

**Why this priority**: This is the defect. wfctl installs the same skill tree
into four different clients' directories, and the published spec is the only
contract those clients share. A non-spec key is what a conformance check exists
to reject, and today six skills carry one.

**Independent Test**: Run the reference validator over every shipped skill and
count failures. Delivers value on its own: the count drops from seven to one
whether or not any other story ships.

**Acceptance Scenarios**:

1. **Given** the shipped skill bundle, **When** each skill is checked against the
   Agent Skills frontmatter contract, **Then** every skill wfctl authored passes.
2. **Given** the same bundle, **When** the results are read, **Then** the only
   remaining failure is the vendored skill, whose non-spec key wfctl cannot
   remove without forking upstream.
3. **Given** a consumer repo installed before this change, **When** wfctl is
   upgraded and skills are reinstalled, **Then** the installed skills carry no
   non-spec key either.

---

### User Story 2 - A vendored skill can be made natively discoverable (Priority: P2)

A reader forty turns into a session notices replies have drifted long and asks
for the brevity rules back. The agent loads them from its own skill list rather
than the reader having to recall and type an exact command — and the decision
that made that possible sits somewhere an upstream update cannot erase.

**Why this priority**: This is most of issue #108's payload, and it falls out of
the same change rather than needing its own. Today the decision "this skill
should be natively discoverable" can only be written inside the skill's own file,
so for a vendored skill it has nowhere to live at any price.

What this does **not** deliver is unprompted self-correction. The vendored file
declares itself exempt from model-initiated invocation, and wfctl cannot change
that without forking a file it does not own. The reader still has to notice the
drift; what changes is that they no longer have to know the command's name.

**Independent Test**: Install for the Claude agent and confirm the vendored skill
appears in the native discovery path and is loadable by name. Replace the
vendored file with a copy carrying no wfctl annotation, reinstall, and confirm it
still appears.

**Acceptance Scenarios**:

1. **Given** a repo installed for the Claude agent, **When** the install
   completes, **Then** the vendored skill is present in the native discovery
   path alongside the six already there, and can be loaded by name on request.
2. **Given** the vendored skill's file is replaced wholesale by an upstream
   version containing nothing wfctl wrote, **When** skills are reinstalled,
   **Then** it is still natively discoverable.
3. **Given** the same repo, **When** the skills are uninstalled for that agent,
   **Then** every native copy is removed, including the vendored one.
4. **Given** a skill whose own frontmatter declines model-initiated invocation,
   **When** it is included in the discoverable set, **Then** it is listed but
   never invoked unprompted — membership does not override a skill's own
   invocation preference.

---

### User Story 3 - The discoverable set is one auditable list (Priority: P3)

A contributor asks "which skills does Claude pick up on its own?" and answers it
by reading one list, rather than by grepping frontmatter across twenty-eight
directories. Adding or removing one is a single edit, and a wrong entry is caught
by an automated check rather than by a skill quietly never appearing.

**Why this priority**: Real, but a maintainer convenience rather than a user
outcome. It matters mainly because the alternative failure — a skill that is
silently not discoverable — is invisible until someone notices its absence.

**Independent Test**: Read the discoverable set in one place; introduce a name that
matches no shipped skill and confirm an automated check fails.

**Acceptance Scenarios**:

1. **Given** the shipped bundle, **When** a contributor asks which skills are
   natively discoverable, **Then** the answer is readable in a single declaration.
2. **Given** a declared name that matches no shipped skill directory — a typo, or
   a skill renamed without updating the declaration — **When** the test suite
   runs, **Then** it fails and names the entry.
3. **Given** the accepted architecture records, **When** they are read after this
   change, **Then** none of them describes the removed mechanism as current.

---

### Edge Cases

- **A declared name matches no shipped skill.** Install proceeds and simply
  mirrors nothing for that name. The failure is silent by nature, so it is caught
  by an automated check at build time rather than at install time (FR-005).
- **Installing for an agent other than Claude.** No native copies are made at
  all; the reference copy every agent receives is unchanged.
- **Upgrading a repo installed under the old scheme.** The six previously
  discoverable skills stay discoverable, their files change content, and the
  vendored skill is added. Nothing is removed.
- **A skill is removed from the discoverable set in a future change.** Its native
  copy stops being installed and stops being recorded, but the directory remains
  on disk and no command reports it. Known gap, out of scope, tracked as #110.
- **Upstream later adds its own discoverability key to the vendored skill.** No
  effect: nothing outside wfctl's own declaration is consulted.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: No skill wfctl authors MUST carry a frontmatter key outside the
  Agent Skills allowed set (`allowed-tools`, `compatibility`, `description`,
  `license`, `metadata`, `name`). This states the property; FR-010 states the
  check that keeps it true.
- **FR-002**: The discoverable set MUST be declared in exactly one place, and
  that place MUST NOT be any skill's own file.
- **FR-003**: Installing for the Claude agent MUST place exactly the discoverable
  set into the native discovery path, in addition to the agent-neutral reference
  copy every agent receives.
- **FR-004**: A skill wfctl ships but does not own MUST be includable in that set
  without editing the skill's file, and the inclusion MUST survive an upstream
  replacement of that file.
- **FR-005**: An automated check MUST fail when a declared name does not
  correspond to a shipped skill directory.
- **FR-006**: Agents other than Claude MUST be unaffected — no native copies, no
  change to what they receive.
- **FR-007**: Uninstalling an agent's layer MUST remove that agent's native
  copies, including any added by this change.
- **FR-008**: Discoverability MUST NOT be read from a previously installed skill
  tree. The declaration and the code that reads it ship together, so no
  transitional or dual-read behavior is required. Falsifiable form, so this is a
  requirement rather than a note: a skill directory present in the installed tree
  but absent from the shipped bundle MUST NOT be placed in the native discovery
  path.
- **FR-009**: Architecture records that state the superseded behavior MUST be
  amended in the same change, so no accepted record describes a mechanism that no
  longer exists.
- **FR-010**: An automated check MUST fail when a skill wfctl authors carries a
  frontmatter key outside the Agent Skills allowed set. The check MUST run
  without network access, and MUST exempt vendored skills by name.

## Key Entities

- **Shipped skill bundle**: the twenty-eight skill directories wfctl distributes
  as package data. Each has a name, a body, and frontmatter constrained by the
  Agent Skills spec.
- **Vendored skill**: a shipped skill whose contents belong to an upstream
  project. Identified by carrying a license declaration. wfctl may distribute and
  reference it but never edits it; one exists today.
- **Discoverable set**: the named subset of the bundle that an agent's native
  loader picks up on its own. Everything outside it remains reachable only when
  the reader types its command.
- **Install record**: the per-layer manifest of what wfctl placed in a repo. It
  is what uninstall and drift detection read, and it gains an entry per native
  copy.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Conformance failures across the shipped bundle drop from 7 to 1,
  and the single remaining failure is the vendored skill.
- **SC-002**: Every skill wfctl authored passes conformance — 0 failures
  attributable to wfctl, down from 6.
- **SC-003**: Skills an agent can discover natively go from 6 to 7, the addition
  being the vendored skill that previously could not be included at any price.
  It is loadable on request rather than self-invoking, because its own frontmatter
  declines model-initiated invocation.
- **SC-004**: The question "which skills are natively discoverable?" is answered
  by reading one declaration of fewer than ten lines, down from frontmatter
  spread across twenty-eight directories.
- **SC-005**: A declaration naming a skill that does not exist is caught by the
  test suite rather than by a reader noticing an absent skill, moving a silent
  failure to a loud one.
- **SC-006**: Installs for every other agent are byte-identical before and after.
- **SC-007**: The change is net-negative in lines: the mechanism it removes is
  larger than the one it adds.

## Assumptions

- **Pre-specify design context loaded from `design.md`** in this feature
  directory (`wfctl feature-paths` → `FEATURE_DIR`). This repository records a
  spec root outside the working tree, so the literal path `specs/<branch>` does
  not apply here (#81).
- **The issue's own proposal was superseded during design.** #59 proposed moving
  the key under `metadata` in each skill's frontmatter. Brainstorming rejected
  that in favour of removing the key entirely and naming the discoverable skills
  in the installer. Two reasons, both recorded in `design.md`: the project has no
  YAML parser, so a nested key costs more parsing code than the flat key it
  replaces; and an accepted architecture record already assigns authority over
  layer contents to the installer, which frontmatter was contradicting.
- **The issue's Compatibility section does not apply.** It weighs a transitional
  dual-read against a drift check for a stale key. Neither is needed: the
  installer reads skills from the package it ships in, never from a previously
  installed tree, so the declaration and its reader can never disagree.
- **This change draws no new architectural boundary.** Declared via `wfctl arch
  none`; it stops the code contradicting a boundary an accepted record already
  drew.
- **Membership in the discoverable set does not override a skill's own invocation
  preference.** The vendored skill declines model-initiated invocation in its
  frontmatter, so being included makes it listed and loadable on request, not
  self-invoking. #108's remaining half — reloading without the reader asking —
  needs a wfctl-owned skill layering over it, which is that issue's work.
- **The vendored skill's own non-spec key stays.** Removing it means editing a
  file upstream replaces, which an accepted record forbids. It is the one
  permitted conformance failure and is excluded from FR-001 deliberately.
- **Two follow-ups are tracked and out of scope**: #110 (drift detection never
  covers the native path) and #60 (adopting the upstream reference validator
  itself, and the general vendored-exemption policy it needs). The offline key
  assertion in FR-010 is in scope here and does not pre-empt that decision.

## Validation Strategy _(mandatory)_

- `uv run pytest -q` — the full suite, including the four native-copy tests
  refounded on the new mechanism and the new declaration guard (FR-005).
- `uv run ruff check wfctl/ tests/` and `uv run mypy wfctl/` — the project's
  lint and type gates.
- `wfctl doctor` — reports drift between what wfctl installed in this repo and
  what it now ships; expected to report the six changed skills as behind until
  reinstalled.
- An offline conformance assertion over every shipped skill, failing when any
  non-vendored skill carries a frontmatter key outside the allowed set (FR-010,
  SC-001, SC-002). It runs inside `uv run pytest` with no network access; the
  upstream reference validator is used to confirm the counts once during
  implementation, but is not a test dependency.
- Manual, because the suite checks that skills ship and cross-reference
  correctly rather than that they behave: `wfctl install-skills --agent claude`
  in a scratch repo, confirming the vendored skill appears in the native path
  (FR-004); the same for `--agent bob` confirming nothing appears there (FR-006);
  and `wfctl uninstall-skills --agent claude` confirming removal (FR-007).
