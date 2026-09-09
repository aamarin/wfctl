# Feature Specification: seed-guard-hook

**Feature Branch**: `136-seed-guard-hook`
**Created**: 2026-09-08
**Status**: Draft
**Input**: Issue #136 — make `install-skills` seed the cross-worktree guard into a consumer's `.claude/settings.json`, so the four lines everyone adds by hand become managed entries wfctl can install, update and remove.

Pre-specify design context loaded from `specs/136-seed-guard-hook/design.md`.

## Clarifications

### Session 2026-09-09

- Q: When the directory-change rule is gone but wfctl's record says it added it, what should the health check do? → A: Report it as gone with a warning marker, leaving the exit code alone. Removal is a choice the project is entitled to make; a missing guard hook stays an exit-1 failure because nothing is enforcing isolation without it.
- Q: After the project deletes the directory-change rule, does the next install put it back? → A: Neither — the install refuses to proceed and names the choice. Installs are not always deliberate (`/start-session` runs one unattended when the mirror is stale), and silently re-adding or silently skipping both hide a decision the project made. This does not contradict reporting an unparseable settings file as a warning: an unparseable file is an accident wfctl cannot read, while a drifted rule is a decision someone made.
- Q: Does that refusal cover every managed entry, or only the directory-change rule? → A: Only the directory-change rule. A managed hook announces itself as wfctl's, so re-asserting it is wfctl correcting its own row; the rule is a bare string the project may have authored. Extending refusal to hooks would change behaviour for every existing consumer and is its own issue.
- Q: When uninstall declines to remove an edited directory-change rule, does it say so? → A: Yes, naming the file, the text it found, and the exact rule wfctl originally installed — the receipt already holds that string to compare against, and it is what lets a reader tell a deliberate narrowing from a stale leftover.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - The guard arrives switched on (Priority: P1)

Someone installs wfctl into their project. The cross-worktree guard starts
protecting them immediately, without them reading a README section and copying
JSON into a config file.

**Why this priority**: This is the whole feature. A safety rule that ships
switched off protects nobody, and the hand-copied version is unreviewable and
does not survive a fresh checkout.

**Independent Test**: Install into a project with no settings file, then issue a
Bash command naming a sibling worktree and confirm it is refused.

**Acceptance Scenarios**:

1. **Given** a project with no settings file, **When** the install runs for the
   Claude layer, **Then** the file is created carrying the guard hook scoped to
   Bash commands, and the companion rule that blocks directory changes.
2. **Given** the install has run, **When** a command tries to run something in a
   sibling worktree, **Then** it is refused with the guard's explanation.
3. **Given** a project whose settings file exists but has no tool-event hooks,
   **When** the install runs, **Then** the guard entry is added and every key the
   project already had is unchanged.

---

### User Story 2 - Their own settings survive (Priority: P1)

Someone who has spent months tuning their own hooks and permissions installs
wfctl, later re-installs it, and eventually uninstalls it. Nothing they wrote is
lost at any point.

**Why this priority**: Equal to P1 above. The file belongs to the project, not to
wfctl, and a single lost permission rule ends the trust that lets wfctl write
there at all.

**Independent Test**: Take a settings file carrying hand-written tool hooks and
permission rules, run install → re-install → uninstall, and compare its parsed
content to the original.

**Acceptance Scenarios**:

1. **Given** a settings file with the project's own Bash tool hook, **When** the
   install runs, **Then** their hook is still present and wfctl's is a separate
   entry beside it.
2. **Given** the install has already run, **When** it runs again, **Then**
   nothing is duplicated and the file is not rewritten at all.
3. **Given** wfctl's entries are installed, **When** the uninstall runs,
   **Then** only wfctl's entries are removed and the project's own hook remains.
4. **Given** a project that already blocked directory changes before wfctl was
   ever installed, **When** wfctl is installed and later uninstalled, **Then**
   that rule is still there.
5. **Given** wfctl added the directory-change rule and the project has since
   edited its text, **When** the uninstall runs, **Then** their edited version is
   left in place rather than removed.
6. **Given** the uninstall left an edited directory-change rule in place, **When**
   it reports, **Then** it names the file, the text it found and the rule wfctl
   originally installed, rather than reporting that only their own entries remain.

---

### User Story 3 - Drift is visible (Priority: P2)

Someone whose config has fallen out of step with the wfctl they are running is
told so, and told how to fix it.

**Why this priority**: Below the two above because nothing is lost when it is
missing — but without it a guard silently deleted or left behind by an upgrade is
indistinguishable from a guard that is working.

**Independent Test**: Delete wfctl's entries by hand and confirm the health check
names each one and prints a repair command.

**Acceptance Scenarios**:

1. **Given** the guard entry has been deleted by hand, **When** the health check
   runs, **Then** it reports the entry as gone, says what protection was lost,
   and names the command that restores it.
2. **Given** the guard entry names an older command than the running wfctl
   installs, **When** the health check runs, **Then** it reports the entry as
   behind and names the repair command.
3. **Given** wfctl added the directory-change rule and it has since been removed,
   **When** the health check runs, **Then** it reports that rule as gone — never
   as "behind", which has no meaning for a rule carrying no version.
4. **Given** every managed entry matches what the running wfctl installs,
   **When** the health check runs, **Then** it says nothing about the settings
   file.

---

### User Story 4 - A hand-wired guard is corrected, not just claimed (Priority: P2)

Someone who followed the README and wired the guard themselves — but scoped it to
the wrong set of tools — has it corrected by the install rather than adopted as-is.

**Why this priority**: Below P1 because it affects only people who acted on the
old README, but it is the one state where the install currently reports success
over a config that does not work.

**Independent Test**: Hand-write the guard scoped to every tool, install, and
confirm the scope is corrected in place.

**Acceptance Scenarios**:

1. **Given** a hand-written guard entry scoped to the wrong tools, **When** the
   install runs, **Then** the scope is corrected and the entry keeps its original
   position in the file.
2. **Given** a hand-written guard entry already scoped correctly, **When** the
   install runs, **Then** nothing changes and the file is not rewritten.

### Edge Cases

- The settings file exists but cannot be parsed: the install reports the problem,
  leaves the file untouched, and everything else in the install still lands.
- The settings file's `permissions` value is not the shape the schema expects:
  the install reports it rather than overwriting whatever the project meant by it.
- The record of what wfctl installed is missing or was edited by hand: the
  uninstall treats the unmarked rule as the project's and leaves it, rather than
  guessing.
- The project deleted wfctl's directory-change rule deliberately, then re-installs:
  the rule returns, because that is what a managed entry means.
- More than one copy of the guard entry exists after a hand-edit: they collapse to
  a single entry rather than leaving a second for the next install to fight over.
- A record written before this feature shipped carries no receipt at all: read as
  "wfctl added nothing", needing no migration.


### The eight consumer states

SC-003 is measured against this table. One row per state, with the state named
the way a test can pin it.

| # | The project's settings file | What installing does |
|---|---|---|
| 1 | absent | creates it: three managed hooks and the directory-change rule |
| 2 | exists, no tool-event hooks | adds wfctl's group; every existing key untouched |
| 3 | has their own tool-event hook | theirs survives; wfctl's is a separate group |
| 4 | carries a hand-wired guard scoped wrongly | scope corrected in place, position kept |
| 5 | already carries the directory-change rule | nothing added; the receipt records that wfctl did not add it |
| 6 | already installed, nothing changed | nothing written; the file is not reflowed |
| 7 | a receipt exists and the rule no longer matches it | refuses, naming both ways forward |
| 8 | the guard hook deleted by hand | reinstated; the health check names it while it is gone |

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: Installing the Claude layer MUST add the cross-worktree guard as a
  managed hook on Bash tool calls in the project's settings file.
- **FR-002**: Installing the Claude layer MUST add the companion rule that blocks
  directory changes to the project's permission denials.
- **FR-003**: Installing MUST leave every hook, permission and setting the project
  already had exactly as it was.
- **FR-004**: Re-installing MUST replace wfctl's own managed hooks in place rather
  than duplicating them, and MUST NOT rewrite the file when nothing changed.
- **FR-005**: Installing MUST record whether wfctl was the one that added the
  directory-change rule, at the moment it installs.
- **FR-006**: A recorded receipt MUST be carried forward across re-installs rather
  than re-derived from the file, which after the first install can no longer
  answer the question.
- **FR-007**: Uninstalling MUST remove the directory-change rule only when the
  record says wfctl added it AND its text is still exactly what wfctl installs.
- **FR-008**: Uninstalling MUST leave a hand-written hook in the same array as
  wfctl's untouched.
- **FR-009**: Absence of a receipt MUST be read as "not wfctl's", leaving the rule
  in place.
- **FR-010**: Installing over a hand-written guard entry MUST correct its tool
  scope, and MUST keep the entry in its original position in the file.
- **FR-011**: The health check MUST report a managed hook that is missing or
  behind the running wfctl, naming what was lost and the command that repairs it.
- **FR-012**: The health check MUST report the directory-change rule as present or
  gone only, never as behind, and MUST report its absence as a warning that does
  not change the exit code — unlike a missing guard hook, which remains a failure.
- **FR-013**: The health check MUST stay silent about the settings file when every
  managed entry is current.
- **FR-014**: An unparseable or wrongly-shaped settings file MUST be reported as a
  problem without failing the rest of the install. This outranks the refusal in
  FR-017: drift cannot be established in a file that will not parse, and refusing
  on an unknown is refusing on a guess.
- **FR-015**: The README MUST stop instructing people to add the guard by hand,
  and say that installing does it.
- **FR-016**: The guard entry MUST be installed only for the Claude layer, whose
  schema it belongs to, and never in the agent-agnostic base layer.
- **FR-017**: Installing MUST refuse to proceed when a receipt exists for the
  directory-change rule and the settings file does not carry that rule exactly —
  whether it was removed or edited, and whether or not wfctl was the one that
  added it. A receipt is wfctl's record that it looked at this entry before; the
  file no longer matching what it saw is a change only a person can explain. The
  refusal MUST name both ways forward: restore the rule, or pass an explicit flag
  that accepts the divergence and re-asserts it.
- **FR-018**: That refusal MUST apply only to the directory-change rule. A managed
  hook that drifted MUST continue to be corrected in place without refusing.
- **FR-019**: The refusal message MUST be where a project learns its options, since
  no mechanism exists today for recording a standing preference that differs from
  wfctl's default.
- **FR-020**: When uninstall declines to remove the directory-change rule because
  its text no longer matches, it MUST say so — naming the file, the text found,
  and the rule wfctl originally installed.
- **FR-021**: Uninstall's summary MUST account for a directory-change rule it
  removed, not only for the hooks. A line naming hooks alone under-reports what
  the run changed in a file the project owns.

## Key Entities

- **Managed hook entry**: an entry in the project's settings file that runs a
  wfctl subcommand. Self-identifying — its command text begins with a fixed
  prefix, so anyone reading the file can see which entries are not theirs.
- **Managed permission rule**: a plain string in the project's permission
  denials. Carries no marker and cannot carry one, because it is matched by exact
  text. This document calls it the *directory-change rule* throughout; the plan,
  the tasks and the code call it by its literal value, `Bash(cd:*)`. One name per
  surface, and this line is the mapping.
- **Receipt**: the record, written at install time, of whether wfctl added a
  managed permission rule or found it already there. The only surviving evidence
  of authorship for an entry that cannot identify itself.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A fresh install leaves the guard active with zero manual config
  steps — the README's four-line block is no longer needed by anyone.
- **SC-002**: Install → re-install → uninstall over a project's own settings file
  returns it to its original parsed content, with every key, hook and permission
  the project had still present and no key wfctl invented left behind. Not byte
  equality: the install that first adds an entry rewrites the file, and a JSON
  round trip normalises indentation.
- **SC-003**: Every one of the eight consumer states in the table below is covered
  by a test that fails if its behavior changes. The table is in this document
  rather than only in the design notes, because those live outside the repository
  and a criterion measurable only against them cannot be checked by a reviewer.
- **SC-004**: A project that blocked directory changes before wfctl existed still
  has that rule after a full install-and-uninstall cycle, in 100% of cases,
  including when wfctl's record is missing.
- **SC-005**: The health check produces no output about the settings file on a
  clean install, so a run that does say something is worth reading.

## Validation Strategy _(mandatory)_

- `uv run pytest -q` — the suite, including new round-trip cases over a settings
  file carrying the project's own hooks and permission rules.
- `uv run ruff check wfctl/ tests/` and `uv run mypy wfctl/`.
- `uv run wfctl doctor` — no finding that still stands.
- A by-hand round trip on a scratch repo, which the suite cannot cover: install
  into a real hand-authored settings file, confirm its rows survive byte-for-byte,
  re-install, confirm nothing duplicated, uninstall, confirm the file returns to
  what it was.
