# Feature Specification: The design checks match records to the contexts a branch changes

**Feature Branch**: `649-design-checks-by-context`
**Created**: 2026-10-26
**Status**: Draft
**Input**: Design at `design.md` in this feature folder, from `/speckit.brainstorm` on #649.

## Clarifications

### Session 2026-10-26

- Q: In a repo with a name list, does a branch still have to pass today's general check as well as the per-context one? → A: No. The per-context check replaces it, so a branch whose listed contexts each have a record or a per-context "no" passes. Basis: `domain-page-names-contexts.md` keeps the general check for a repo without a name list, and FR-007 already pauses a branch that lists no contexts, so every branch in a repo with a list has at least one context that needs an answer.
- Q: Does the software design check match outside parties on the `Contexts` line, or only wfctl's own contexts? → A: Every name on the line, at both levels. Basis: `649-contexts-module.md` runs one match for both checks, which differ only in which records they pass in.
- Q: How does a per-context "no" show in `wfctl status` and in the PR body? → A: The check's row reads done only once every listed context is answered. `wfctl status --all` lists each per-context "no" with its context and reason, and the PR body lists them under "Moves a boundary?". Basis: #648 shows a claimed pass as `claimed: <reason>` under `--all`, and #635 puts pass exceptions in that PR section so the reviewer reads the reason.

## User Scenarios & Testing _(mandatory)_

A bounded context is a distinct part of a system with its own terms and rules. The domain page under `docs/architecture/domain/` lists wfctl's six contexts. For example, "install and drift" covers how wfctl installs its skills into a project and reports when they fall out of date, while "session continuity" carries work from one agent session to the next.

Currently, brainstorm's architecture check passes once a branch adds or edits any architecture record, and the software design check from #648 passes once a branch adds any record under `design/`. Neither check looks at which context the record is about. This feature ties both checks to the contexts a branch changes:

1. The domain page lists the short names in two header lines, `Contexts` and `Outside parties`.
2. A branch lists the contexts it changes in one `Contexts` line in `design.md`.
3. A record lists the contexts it governs in a `governs` field.

Every example below uses a repo whose domain page carries this header:

```
State: accepted
Contexts: evidence-and-derivation, architecture-records, design-method, install-and-drift, session-continuity, attention
Outside parties: workmux, trackers, spec-kit, agent-host, consumer-repo, upstream-projects
```

### User Story 1 - A record about the wrong context doesn't pass brainstorm (Priority: P1)

Branch `700-restart-handoff` changes the restart hook. Its `design.md` says `Contexts: session-continuity`. The agent adds a level-2 record whose frontmatter says `governs: install-and-drift`. `wfctl status` shows brainstorm paused and names the context that has no answer.

**Why this priority**: This is the gap #649 describes. Today the record about install and drift passes the check, and the restart change has no design answer.

**Independent Test**: On a branch with that `design.md` and that record, run `wfctl status` and confirm brainstorm is current with the reason naming `session-continuity`.

**Acceptance Scenarios**:

1. **Given** the branch above, **When** the user runs `wfctl status`, **Then** brainstorm is current and the `architecture` row reads `no architecture record governs session-continuity`.
2. **Given** the same branch, **When** the user runs `wfctl status --json`, **Then** brainstorm's `state` is `in_progress`, and its `remedy` names both answers: a record whose `governs` field names `session-continuity`, or `wfctl arch none --context session-continuity --reason "<why>"`.
3. **Given** a `Contexts` line that lists two contexts and records that govern only the second, **When** the user runs `wfctl status`, **Then** the reason names the first.

---

### User Story 2 - A matching record or a per-context "no" passes brainstorm (Priority: P1)

The agent answers each listed context in one of two ways. It adds a record whose `governs` field names the context, or it states that the context needs no record with `wfctl arch none --context <name> --reason "…"`. Once every listed context has one of these, brainstorm moves on.

**Why this priority**: A pause with no way out strands every branch. These are the "yes" and "no" answers.

**Independent Test**: On the branch from User Story 1, add `session-continuity` to the record's `governs` field and confirm brainstorm passes. Then, on a fresh copy, run the per-context `arch none` instead and confirm the same.

**Acceptance Scenarios**:

1. **Given** the branch from User Story 1, **When** the record's frontmatter says `governs: session-continuity, install-and-drift`, **Then** the `architecture` row reads done.
2. **Given** the branch from User Story 1, **When** the user runs `wfctl arch none --context session-continuity --reason "Copy change in the handoff template"`, **Then** the `architecture` row reads done.
3. **Given** a branch that lists `session-continuity`, **When** the only answer is a bare `wfctl arch none --reason "…"` with no `--context`, **Then** brainstorm stays paused on `session-continuity`, since a branch-wide "no" doesn't answer a listed context.
4. **Given** a record for `session-continuity` that was already on `main` before the branch started, **When** the branch adds no record of its own, **Then** brainstorm stays paused, since the check reads only records this branch adds or edits.

---

### User Story 3 - A bad or missing `Contexts` line pauses brainstorm (Priority: P1)

The agent misspells a context, or leaves the `Contexts` line out of `design.md`. Brainstorm pauses and says which, so the agent fixes the line instead of writing a record no check could match.

**Why this priority**: If a misspelled name or a missing line let brainstorm pass, an agent could skip the check by accident or on purpose.

**Independent Test**: Write `Contexts: session-continuty` in `design.md` and confirm the pause names the misspelled entry. Remove the line and confirm the pause says `design.md` lists no contexts.

**Acceptance Scenarios**:

1. **Given** `Contexts: session-continuty`, **When** the user runs `wfctl status`, **Then** brainstorm is paused with `session-continuty is not a context on the domain page`.
2. **Given** a `design.md` with no `Contexts` line, or one with no names after it, **When** the user runs `wfctl status`, **Then** brainstorm is paused with `design.md lists no contexts`.
3. **Given** `Contexts: session-continuity, workmux`, **When** both have answers, **Then** brainstorm passes, since an outside party is a valid name.

---

### User Story 4 - A repo with no name list sees no change (Priority: P1)

A repo whose domain page has no `Contexts` header line, or that has no domain page, keeps today's general check. A branch passes once it adds or edits any architecture record, or states with `wfctl arch none` that none is needed.

**Why this priority**: wfctl runs in repos that never modeled their domain. Pausing them on a name list they don't have would break every branch there.

**Independent Test**: In a repo with no name list, confirm a branch with `design.md` and one record passes brainstorm, with or without a `Contexts` line.

**Acceptance Scenarios**:

1. **Given** no accepted domain page with a `Contexts` header line, **When** the branch has `design.md` and no answer, **Then** the reason is `no architecture record for this change`, unchanged from today.
2. **Given** the same repo, **When** the branch adds any record, **Then** brainstorm passes, whatever the record's `governs` field says.
3. **Given** a domain page with the header lines whose `State` is `proposed`, **When** the user runs `wfctl status`, **Then** wfctl ignores its names, and the repo behaves as if it has no name list.

---

### User Story 5 - `wfctl doctor` reports a `governs` name that isn't on the list (Priority: P2)

A level-2 record says `governs: sesion-continuity`. `wfctl doctor` reports the record and the name, so the typo is found before a branch relies on the record.

**Why this priority**: A misspelled `governs` name makes a record that never matches anything. Doctor already validates records, so it is where the user looks.

**Independent Test**: Commit a level-2 record with an unknown `governs` name and confirm `wfctl doctor` reports it and exits 1.

**Acceptance Scenarios**:

1. **Given** a level-2 record whose `governs` field names something not on the list, **When** the user runs `wfctl doctor`, **Then** it reports the record's slug and the unknown name.
2. **Given** a repo with no name list, **When** a record carries a `governs` field, **Then** doctor reports nothing about it, since there is no list to check against.

---

### User Story 6 - The software design check matches the same way (Priority: P2)

#648 adds a software design check that passes once a branch adds a level-3 record under `design/`. With a name list, that check also pauses until every listed context has a level-3 record that governs it, or a per-context "no" given with `wfctl step none brainstorm.software-design --context <name> --reason "…"`.

**Why this priority**: The accepted level-2 record ties both checks to contexts at once, so the two checks give the same answer about the same branch. It depends on #648 merging first.

**Independent Test**: On a branch whose `Contexts` line lists `session-continuity`, with a level-2 answer for it, add a level-3 record governing `install-and-drift` and confirm the `software-design` row pauses on `session-continuity`.

**Acceptance Scenarios**:

1. **Given** that branch, **When** the user runs `wfctl status`, **Then** the `software-design` row reads `no software design record governs session-continuity`.
2. **Given** that branch, **When** the user runs `wfctl step none brainstorm.software-design --context session-continuity --reason "No structural choice"`, **Then** the row reads done.
3. **Given** a level-2 record that governs `session-continuity`, **When** no level-3 record does, **Then** the `software-design` row still pauses, since each check counts only its own level's records.

---

### User Story 7 - The skills write the names the checks read (Priority: P2)

An agent running `model-the-domain` writes the two header lines on the domain page. An agent running brainstorm writes the `Contexts` line in `design.md` and a `governs` field on every record it writes. An agent opening a PR copies the `Contexts` line into the PR body's "Moves a boundary?" section, since a reviewer reading the PR doesn't see `design.md`.

**Why this priority**: The checks only work if the names get written. Without the skill text, an agent learns the format from a pause instead of before it.

**Independent Test**: After `uv run wfctl install-skills --agent claude`, read each installed skill and template and confirm it names the line or field it writes.

**Acceptance Scenarios**:

1. **Given** the installed `model-the-domain` template, **When** an agent reads its header, **Then** it offers `accepted` as a `State` value and carries the `Contexts` and `Outside parties` lines.
2. **Given** the installed `design-levels` and `speckit-brainstorm` skills, **When** an agent writes `design.md`, **Then** the skills tell it to write the `Contexts` line.
3. **Given** the installed `architecture-decisions` and `software-design-decisions` templates, **When** an agent writes a record, **Then** the frontmatter carries a `governs` field.
4. **Given** the installed `opening-a-change` skill and this repo's PR template, **When** an agent opens a PR, **Then** the "Moves a boundary?" section carries the branch's `Contexts` line.

---

### Edge Cases

- A branch that already has `spec.md` isn't paused by either check, the same exception the architecture check has today. Branches that passed brainstorm before this ships don't move backwards.
- A name that appears on two accepted domain pages counts once. Names from every accepted page are combined.
- Names are compared exactly, after trimming spaces around each comma-separated entry. A repeated name on the `Contexts` line counts once.
- A record whose `governs` field names several contexts answers each of them.
- `repository` is not a built-in name. A repo that wants repo-wide records adds it to its own `Contexts` header line, and then it behaves like any other name.
- `wfctl arch none --context` and `wfctl step none --context` refuse a name that isn't on the list, and refuse the option when the repo has no name list, so a per-context "no" can't be written for a name no check will read.
- In a repo with a name list, `wfctl arch none`, `wfctl step none brainstorm.architecture`, and `wfctl step none brainstorm.software-design` without `--context` refuse and name the option, so the agent learns when the command runs rather than from a pause. A whole-pass claim written before the domain page had a list no longer answers either check.
- `wfctl step none --context` applies only to `brainstorm.software-design`, the one pass the context check reads, and refuses any other pass.
- A domain-page entry that isn't a lowercase name made of letters, digits, and hyphens is left off the list and reported by `wfctl doctor`, since each name becomes a folder name for its per-context "no".
- A per-context "no" for one context doesn't answer another. Running `arch none --context` once per listed context is how a branch with no boundary change answers all of them.
- A per-context "no" written early, followed later by a record that governs the same context, holds the PR at open until the "no" is deleted. The check runs at PR open because the record can arrive at any point, including during implementation.
- A level-3 record's misspelled `governs` name isn't reported by doctor, which reads only level-2 records. It appears as the context brainstorm pauses on.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: wfctl MUST read the name list from the `Contexts` and `Outside parties` header lines of every page under `<arch-root>/domain/` whose `State` header line is `accepted`, combining them into one list. Each line is a comma-separated list of names.
- **FR-002**: When no accepted domain page carries a `Contexts` header line, both design checks MUST behave exactly as they do today, and wfctl MUST NOT add any new finding or refusal. The one exception is a per-context "no" that a branch wrote while the list existed. The worktree guard and `check-body` MUST still read it, so a branch that said "no" for a context and then added a record governing that context is still refused. A per-context "no" can only be written while a list exists, so a repo that never had one sees no change (#653, decided 2026-10-27).
- **FR-003**: wfctl MUST read a branch's contexts from the `Contexts` line in its `design.md`.
- **FR-004**: A record MUST be able to carry a `governs` frontmatter field, a comma-separated list of names, and wfctl MUST read it from both level-2 records and level-3 records under `design/`.
- **FR-005**: With a name list, the architecture check MUST pause brainstorm until every context on the branch's `Contexts` line has a level-2 record this branch adds or edits whose `governs` field names it, or a per-context "no" for it. The reason MUST name the first context with neither.
- **FR-005a**: With a name list, the per-context check MUST replace the general check, so a branch whose listed contexts each have an answer passes with no branch-wide record or `arch none`.
- **FR-006**: With a name list, the software design check MUST apply the same rule to level-3 records this branch adds or edits, and to per-context "no" answers given for that pass. Both checks MUST match every name on the `Contexts` line, outside parties included.
- **FR-007**: With a name list, both checks MUST pause brainstorm when `design.md` has no `Contexts` line or the line lists no names, with the reason `design.md lists no contexts`.
- **FR-008**: With a name list, both checks MUST pause brainstorm when the `Contexts` line names something that isn't on the list, with the reason `<name> is not a context on the domain page`.
- **FR-009**: Each pause MUST carry a remedy naming both answers for the context it names, in the same form the architecture check prints today.
- **FR-010**: `wfctl arch none` and `wfctl step none` MUST accept `--context <name>`, writing a "no" for that context alone. Each MUST refuse a name that isn't on the list, and refuse the option in a repo with no name list.
- **FR-010a**: A per-context "no" MUST NOT hide the check's row in `wfctl status`. The row reads done once every listed context is answered, and `wfctl status --all` MUST list each per-context "no" with its context and reason.
- **FR-011**: A bare `wfctl arch none` or `wfctl step none` with no `--context` MUST NOT answer a listed context when the repo has a name list.
- **FR-012**: `wfctl doctor` MUST report a level-2 record whose `governs` field names something not on the list, giving the record's slug and the name.
- **FR-013**: Both checks MUST NOT pause a branch that already has `spec.md`.
- **FR-014**: `docs/architecture/domain/wfctl.md` MUST carry the two header lines for this repo's six contexts and six outside parties.
- **FR-015**: The `model-the-domain` template MUST offer `accepted` as a `State` value and carry both header lines.
- **FR-016**: The `design-levels` and `speckit-brainstorm` skills MUST tell the agent to write the `Contexts` line in `design.md`, and name `--context` as the per-context "no".
- **FR-017**: The `architecture-decisions` and `software-design-decisions` record templates MUST carry a `governs` field.
- **FR-018**: The `opening-a-change` skill MUST copy the branch's `Contexts` line into the PR body's "Moves a boundary?" section, and list each per-context "no" with its reason under it. This repo's PR template MUST carry the line there. On a sub-issue branch that inherits its parent's spec folder, `check-body` MUST skip an inherited per-context "no" only when a level-2 record the branch adds or edits governs that same context. An inherited "no" for any other context stays true, so the PR body still carries its reason (#653, decided 2026-10-27).
- **FR-019**: The change MUST commit a release note, `changes/649.change.md`, in the `change` category, since a branch that passes the checks today can pause after this ships.
- **FR-020**: With a name list and a `design.md`, the session summary's Boundary line MUST read "answered" exactly when the architecture check finds every listed context answered, whether or not `spec.md` exists.
- **FR-021**: The worktree guard MUST refuse `gh pr create` and `gh pr merge` when the branch's own spec folder holds a per-context "no" at level 2 and a level-2 record the branch adds or edits governs that same context. The refusal MUST name the record and the context, and print the command that deletes that context's "no". A record that governs only other contexts MUST NOT trigger it.

## Key Entities _(include if feature involves data)_

- **Name list**: The combined `Contexts` and `Outside parties` header lines from the accepted domain pages. The user writes it, and wfctl never adds a name of its own.
- **`Contexts` line**: One line in a branch's `design.md` listing the contexts the branch changes. The agent writes it.
- **`governs` field**: A frontmatter field on a record listing the contexts it applies to. The agent writes it on a new record.
- **Per-context "no"**: A design exception, kept in the branch's spec folder, saying one context needs no record at one level, with a reason.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: With a name list, a branch whose records govern none of its listed contexts, and with no per-context "no", can't leave brainstorm, in both attended and autonomous runs.
- **SC-002**: Each listed context is answered by one record edit or one command, with no `wfctl.json` edit.
- **SC-003**: In a repo with no name list, every branch reports the same pipeline position before and after this change.
- **SC-004**: Every branch that already has `spec.md` reports the same pipeline position before and after this change.
- **SC-005**: Exactly one module reads the `Contexts` line. A search of the other modules for the line's name finds no reader.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, with new tests for each acceptance scenario in User Stories 1 to 6, the doctor finding, and the `--context` refusals.
- `uv run ruff check wfctl/ tests/` and `uv run mypy`.
- `uv run wfctl verify` and `uv run wfctl doctor`.
- `uv run wfctl install-skills --agent claude`, then on a scratch branch: one listed context with a record for a different context pauses brainstorm, and a record for the listed context, or `wfctl arch none --context`, lets it pass.
- `grep -n "Contexts" wfctl/_evidence.py wfctl/_arch.py` finds no reader of the line.

## Assumptions

- Pre-specify design context loaded from `design.md` in this feature folder.
- The decisions behind this spec are in `docs/architecture/domain-page-names-contexts.md` (accepted) and `docs/architecture/design/649-contexts-module.md` (proposed).
- #648 merges first, with its software design check as a separate reader beside the architecture check. User Story 6 and FR-006 build on it.
- #635 merges first, with design exceptions kept in an `exceptions/` folder in the spec folder. A per-context "no" goes in one subfolder per context there, because #635 reads every `<step>.<pass>.md` file in that folder as a pass.
- The pause reasons in User Stories 1, 3, and 6 are the wording this spec proposes. The level-1 strings approved during brainstorm weren't saved, so these follow `design.md`.
- `--context` refusing a name not on the list, and refusing in a repo with no list, is a reasonable default this spec chose. Neither record states it, and writing a "no" that no check reads would hide a typo.
- Filtering `wfctl arch context` by the branch's contexts, adding `governs` to the existing accepted records, and the stricter level-3 bar from the domain page are out of scope, as `design.md` explains.
