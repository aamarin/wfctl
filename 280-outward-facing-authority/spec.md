# Feature Specification: notify authority

**Feature Branch**: `280-outward-facing-authority`
**Created**: 2026-09-07
**Status**: Draft
**Input**: Issue #280 — nothing grants per-feature authority for notifying actions. Pre-specify design context loaded from `design.md`.

## Clarifications

### Session 2026-09-07

- Q: Where can the grant be set — label only where a tracker exists, or a local command everywhere? → A: Both, everywhere. Either place can grant; an explicit deny anywhere wins; a missing label says nothing, not no. Accepted cost: an agent can grant itself by running the local command, so the label's protection is advisory rather than structural.
- Q: `outward-facing` names a direction rather than a consequence — what is the class called? → A: **notify**. The flag is `--allow-notify/--deny-notify`, the label is `authority:notify`, and the three classes become reversible / notifying / irreversible, which puts them on one axis: what can you take back?
- Q: Is the grant read once per run, or re-read before each outward-facing action? → A: Once, at the start of the run. Revoking mid-run is not a use case — killing the run is the intervention. Re-reading per action buys a revocation nobody can currently perform and makes a tracker blip look like the agent declining.
- Q: An unattended run reports what it did with the granted authority — where must that report land? → A: The event log. It is the only destination that cannot fail to be written, and the prose surfaces can be derived from it later.

## User Scenarios & Testing _(mandatory)_

### User Story 1 — a run refuses a notifying action and says so (Priority: P1)

A person starts a feature the ordinary way and grants nothing. The run reaches a
step whose command would create issues on the tracker. It declines, records why,
and reports the decline rather than proceeding or failing silently.

**Why this priority**: This is the default path and the only one every repo
takes. It must work before anything can be relaxed, and it is the half a
grant-shaped feature usually ships without — a test where the grant is always
present has not tested the refusal.

**Independent Test**: Run the step on a branch with no grant. The action does not
happen, the tracker is unchanged, and the output names the missing grant.

**Acceptance Scenarios**:

1. **Given** a feature branch with no grant recorded, **When** `wfctl status`
   runs, **Then** it prints a line saying notifying actions are refused —
   not silence.
2. **Given** the same branch, **When** a step would take a notifying
   action, **Then** the action is not taken and the reason names the absent
   grant.
3. **Given** a wfctl that predates this feature, **When** its status is read,
   **Then** its output is distinguishable from a grant-aware wfctl reporting
   *refused*.

---

### User Story 2 — a person grants authority, and an unattended run uses it (Priority: P1)

A person decides one piece of work can act on its own, grants it in advance, and
leaves. The run takes the notifying actions it needs and reports what it did.

**Why this priority**: The feature exists for this, and #240 is parked on it.
Equal priority to story 1 because a grant with no refusal is unsafe and a refusal
with no grant is useless.

**Independent Test**: Grant on a throwaway branch, run the step unattended,
confirm the tracker changed and the run reported the change without being asked.

**Acceptance Scenarios**:

1. **Given** a person has granted notify authority for a feature,
   **When** the run reaches a notifying action, **Then** it proceeds
   without prompting.
2. **Given** the run took notifying actions, **When** it finishes, **Then**
   it reports what it did with the authority whether or not anyone asked.
3. **Given** a granted feature, **When** `wfctl status` runs, **Then** the
   granted line names the source of the grant, not merely that one exists.

---

### User Story 3 — the agent declines authority it was given (Priority: P2)

A granted run reaches an action it judges it should not take — a delivery plan it
cannot read confidently, a row it cannot key. It narrows its own authority and
says so.

**Why this priority**: Carries #131 principle 2's second half. Lower than P1
because a run that never exercises it is still correct; without it the grant
reads as an instruction to use everything given.

**Independent Test**: Grant authority, present the run with a malformed delivery
plan, confirm it declines and that the decline is distinguishable from a refusal
for want of a grant.

**Acceptance Scenarios**:

1. **Given** a granted feature, **When** the agent declines an action, **Then**
   the report distinguishes *declined* from *refused for want of a grant*.
2. **Given** a granted feature, **When** an action in the irreversible class is
   reached, **Then** it is refused regardless of the grant, and the refusal says
   the class is not grantable rather than that a grant is missing.

---

### Edge Cases

- **The grant is unreadable** — corrupt file, invalid UTF-8, a JSON scalar where
  an object was expected. Reads as refused, and says the value was unreadable
  rather than printing the ordinary refused line. The existing per-feature mode
  sets the precedent for failing closed; it does not set one for failing
  silently.
- **A grant exists for a branch, and the run is on `main`** — refused regardless.
  Authority is bounded by the feature branch and nothing relaxes it on `main`.
- **The tracker is unreachable** when the grant is read. Must resolve to
  refused, never to granted, and must say the read failed rather than reporting
  an absent grant.
- **No tracker is configured at all** — wfctl supports this and the verbs no-op.
  The grant must remain expressible.
- **A second grant is written while one exists** — must not clear the
  neighbouring `auto_approve` value.
- **An agent writes the grant itself.** Out of contract, not prevented. The
  artifact must let a reader see that no person set it.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST record, per feature branch, whether notifying
  actions are granted.
- **FR-002**: The system MUST treat an absent, unreadable, or malformed grant as
  *refused*, never as granted.
- **FR-003**: `wfctl status` MUST print a line in the refused state as well as
  the granted state, so that refusal is distinguishable from a wfctl that has no
  concept of a grant.
- **FR-004**: The status payload MUST carry the grant key present-and-false
  rather than omitting it when refused.
- **FR-005**: The recorded grant MUST carry its source, not only a boolean, so
  the granted line can name where the authority came from.
- **FR-006**: Writing the grant MUST NOT overwrite other values held alongside it.
- **FR-007**: The system MUST record the granting as an event distinct from the
  value, so a grant leaves a trace that the overwritten file cannot hold.
- **FR-008**: A granted authority MUST NOT apply to any branch other than the
  feature branch it was granted for, and MUST NOT apply on `main`.
- **FR-009**: An agent MUST be able to decline or narrow authority it holds.
  It MUST NOT widen it. This half is enforced by rule and not mechanically —
  the local grant command is available in every repo (see Clarifications) — and
  is therefore **deliberately not covered by a test**: a passing test could only
  assert the rule is documented, which would read as protection that does not
  exist. What carries it instead is the decision record and the event log, which
  makes a grant no person made legible after the fact.
- **FR-010**: A run that used granted authority MUST record each notifying
  action it took to the append-only event log, unprompted. The log is the
  required destination: it is written whether or not a change is open, whether
  or not the session ends cleanly, and it is what any prose rendering of the
  report is derived from.
- **FR-011**: The report MUST distinguish an action declined by the agent from an
  action refused for want of a grant.
- **FR-012**: The grant MUST be expressible in a repo with no tracker configured.
- **FR-014**: The grant MUST be read once, when the run begins, and that answer
  MUST hold for every notifying action in the run. A change to the grant
  while a run is in progress is out of scope; stopping a run that is going wrong
  is done by killing it.
- **FR-015**: A failure to read the grant MUST be distinguishable in the record
  from a grant that was read and found absent. Since the read happens once,
  a transient failure decides the whole run and must not be recorded as though a
  person had withheld authority.
- **FR-013**: The irreversible class — merge, close an issue, force-push, delete
  a branch or worktree — MUST remain unreachable by any grant.

## Key Entities

- **Grant** — the per-feature record that notify authority was given.
  Carries whether it is held and where it came from. Bounded to one feature
  branch. Absent by default.
- **Grant event** — the append-only record that a grant was made, and when. The
  grant itself is overwritten and cannot hold this.
- **Notifying action** — an action that tells someone outside the repo and
  cannot un-tell them: push, comment on an issue, open one, add a label. The
  class is defined in `wfctl-classes-the-action-not-the-command`, which still
  calls it *outward-facing*; renaming it there is raised separately on PR #282.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: On a branch with no grant, an unattended run reaching an
  notifying step changes nothing on the tracker and its output names the
  missing grant.
- **SC-002**: On a granted branch, an unattended run completes the same step
  without a prompt, and the tracker reflects it.
- **SC-003**: Reading `wfctl status` on an ungranted branch tells a reader the
  state in one line, with no knowledge of this feature required.
- **SC-004**: A reader of the recorded artifacts can tell, after the fact,
  whether a grant was made and when — without access to the session.
- **SC-005**: The step that is currently blocked on this question needs no
  change beyond reading the grant. If it needs more, the boundary drawn here was
  the wrong one.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`,
  `uv run wfctl doctor` — all green, per `AGENTS.md`.
- `uv run wfctl verify` — the agent does not certify its own completion
  (`wfctl-runs-the-verification`).
- Unit coverage for the refused path specifically: absent grant, malformed
  grant, and unreadable grant each resolve to refused and each render their own
  line.
- A round-trip test that writing the grant leaves a neighbouring `auto_approve`
  value intact (FR-006).
- Any change under `wfctl/agents/` additionally requires `uv run wfctl
  install-skills` and a manual exercise of the changed skill — the suite checks
  that skills ship, not that they read correctly.
- **The exercise must include the ungranted path.** An exercise where the grant
  was always present has not tested the refusal.

## Assumptions

- Pre-specify design context loaded from
  `specs/280-outward-facing-authority/design.md`.
- The classification of actions into three irreversibility rows is settled by
  `wfctl-classes-the-action-not-the-command` (PR #282) and is not re-derived here.
- Who may grant is settled by `a-human-grants-outward-facing-authority` and is
  not re-opened here.
- **Unverified, load-bearing, and deliberately not verified**: that tagging an
  issue notifies the people watching it, and that moving that issue between
  board columns does not. The check was proposed and declined on 2026-09-08 —
  accepted risk, not an oversight. What rides on it: if a label is in fact quiet,
  the label surface loses the property that made it preferable and becomes merely
  convenient; if a board move is in fact loud, then every worktree creation
  already takes a notifying action unprompted and the record's `post_create`
  paragraph is wrong. Neither outcome changes who may grant, which is why it was
  affordable to skip. `design.md` records this and
  asks for it to be checked before `plan`. If either is wrong, FR-005's source
  and the `post_create` exemption both need revisiting.
- Storage shape — a second key beside `auto_approve` against a separate file —
  is left to `plan`. FR-006 constrains it; it does not decide it.
- **Deny is sayable from the terminal only.** The label is present-or-absent;
  removing it returns the issue to silent, which is enough. A deny *label* was
  considered and left out — two ways to say no, on surfaces that can disagree,
  for a state already reachable.
- **The recorded source names which place granted it** — label or local — since
  the two can disagree and a reader resolving a surprise needs to know which one
  answered. This is FR-005 read against the two-surface decision, not a new
  requirement.

## Naming

The branch is `280-outward-facing-authority` and the issue title uses
*outward-facing*; both predate this spec and neither is renamed. The class is
**notifying** from here on, the grant is **notify authority**, the flag is
`--allow-notify/--deny-notify`, and the label is `authority:notify`.

*Outward-facing* named a direction. The class is defined by a consequence — the
people told cannot be un-told — and naming it for that keeps the rule
self-explaining: a new action is classified by asking whether it notifies
anyone. It also puts the three classes on one axis, *what can you take back?*,
where the old set named two for reversibility and one for direction.
