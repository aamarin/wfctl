# Tasks: notify authority

**Input**: Design documents from `specs/280-outward-facing-authority/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: `AGENTS.md` sets the bar — `uv run pytest -q`, `uv run ruff check
wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl doctor`, all green, plus
`uv run wfctl verify`. Console assertions pin `NO_COLOR`; `conftest.py` explains
the presence-only semantics. A change under `wfctl/agents/` is additionally not
covered by the suite and needs `install-skills` plus a manual exercise.

**Organization**: Grouped by user story. Phases 3 and 4 are both P1 and both
have to land before this is safe — a grant with no refusal is unsafe, a refusal
with no grant is useless — but they are separately reviewable and Phase 3 alone
is a coherent PR.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable — different files, no dependency on an incomplete task
- Paths are repository-relative, from `plan.md`'s structure decision

---

## Phase 1: Setup

No project initialization needed — this is an existing package with a resolved
environment. One naming task, because the vocabulary changed during `clarify`
and the rest of the work reads better once it has landed.

- [ ] T001 Rename the middle authority class from *outward-facing* to
      *notifying* in `docs/architecture/wfctl-classes-the-action-not-the-command.md`,
      leaving `local and reversible` → `reversible` so all three sit on one axis.
      Verify: `uv run pytest tests/test_skill_cross_references.py -q` and
      `uv run wfctl arch context` still parses the record.
- [ ] T002 [P] Update the comment near `_unkeyed_issues` in `wfctl/_pipeline.py`
      that reads *"creating them is outward-facing and waits for a human"* to the
      new term. Verify: `uv run pytest -q` (comment-only, so the suite is the
      regression check, not the proof).

**Checkpoint**: vocabulary is consistent across the record and its one code
citation. Reviewable as its own slice.

---

## Phase 2: Foundational (blocks every story below)

The resolver and its storage. Nothing in Phases 3–5 can be written before this
exists, and it is the only phase with no user-visible surface.

- [ ] T003 (FR-001, FR-002) Add `NotifyGrant` NamedTuple and
      `notify_grant(agent_dir, issue)` to `wfctl/_session.py`, per
      `contracts/notify-grant.md`. Resolves label against local file, returns
      `(granted, source, detail)`. Never raises. Verify: T006.
- [ ] T004 (FR-001, FR-006, FR-007) Add `grant_notify(agent_dir, state)` to
      `wfctl/_session.py` — writes `notify.json` via `write_json_atomic` and
      appends a `notify-grant` event. Two writes for two questions, mirroring
      `grant_auto_approve`. Verify: T007.
- [ ] T005 (FR-010, FR-015) Add `record_notify_action(agent_dir, action, count)`
      and `record_notify_unread(agent_dir, detail)` to `wfctl/_session.py` —
      appending `notify-action` and `notify-unread` to `events.jsonl`. The second
      is where the tracker's stderr goes, since the console line carries a fixed
      string. Verify: T008.
- [ ] T006 (FR-002, FR-015) Unit tests in `tests/test_session.py` for the
      resolver: all four verdicts from `data-model.md`'s grid, plus the three
      unreadable shapes
      `auto_approve` already guards (missing file, invalid UTF-8, JSON scalar
      where an object was expected). Each must return `granted=False` with a
      distinct `source`.
- [ ] T007 [P] Unit test that `grant_notify` writes both the file and the event,
      and that writing it leaves a neighbouring `mode.json` untouched — the
      round-trip FR-006 demands, which is the whole argument for the second file.
- [ ] T008 [P] Unit test that `record_notify_action` appends without rewriting
      prior lines, and that a malformed pre-existing line does not break the append.
- [ ] T008a Enforce FR-008: a grant read on the trunk branch returns refused
      regardless of any stored value or label, in `wfctl/_session.py`. Verify: T008b.
- [ ] T008b [P] Test FR-008 from the *granted* side — write `notify.json` with
      `state: granted`, read it on the trunk branch, assert refused. Asserted
      against an ungranted fixture this passes vacuously and proves nothing.
      The behaviour is probably correct today by construction, since the state
      dir is per-branch; this is what keeps it correct when that changes.

**Checkpoint**: the resolver answers correctly and is proven to. No CLI surface
yet — nothing calls it.

---

## Phase 3: User Story 1 — a run refuses and says so (Priority: P1)

**Goal**: the default path. No grant, so the action does not happen and the
output names why.

**Independent Test**: on a branch with no grant and no label, run the step that
would create issues. The tracker is unchanged, the output names the missing
grant, and the run continues rather than erroring.

- [ ] T009 [US1] Carry `notify` and `notify_source` into `build_report` in
      `wfctl/_pipeline.py`, **present and false** when refused, never omitted
      (FR-004). Verify: T012.
- [ ] T010 [US1] Print the refused console lines in `wfctl status`
      (`wfctl/cli.py`) — the three distinct refusals from
      `contracts/notify-grant.md`: no grant, denied locally, tracker unreadable.
      Never silence. The unreadable line carries the **fixed string**, never the
      tracker's stderr — `status` is glanced at and must stay one line. The
      stderr goes to the event log, where someone debugging will look for it.
      Verify: T013, and a test that a multi-line stderr does not reach the
      console.
- [ ] T011 [US1] Gate the notifying action in **both** skills that take one:
      `wfctl/agents/skills/speckit-delivery-plan/SKILL.md` (creates issues) and
      `wfctl/agents/skills/end-session/SKILL.md` (commits, tracker writes, and
      the push it currently omits entirely). Each declines and states the
      missing grant. Verify: T014 — **not** the suite, which cannot see skill
      prose.
- [ ] T012 [US1] [P] Test in `tests/` that `--json` carries both keys in every
      refused state, and that a consumer can tell refusal from a wfctl too old
      to know (FR-003's whole point).
- [ ] T013 [US1] [P] Console test with `NO_COLOR` pinned: each refusal renders
      its own line, and the three are distinguishable from each other.
- [ ] T014 [US1] (SC-001) Manual exercise: `uv run wfctl install-skills`, then
      run the gated step **with the grant absent**. Confirm the tracker is unchanged and
      the decline is reported. An exercise where the grant was present has not
      tested this story.

**Verification**: T012, T013 automated; T014 manual and mandatory. Then
`uv run pytest -q`, `ruff`, `mypy`, `doctor`.

**Checkpoint**: refusal works and is legible. Shippable alone — this is the MVP.

---

## Phase 4: User Story 2 — a person grants, an unattended run uses it (Priority: P1)

**Goal**: the feature's reason for existing.

**Independent Test**: grant on a throwaway branch, run the step unattended, and
confirm the tracker changed and the run reported the change without being asked.

- [ ] T015 [US2] Add `--allow-notify/--deny-notify` to `start_cmd` in
      `wfctl/cli.py` as a tri-state defaulting to `None`, matching
      `--auto-approve`'s shape and its documented reason — a plain bool would
      revoke on every later `wfctl start`. **The help text must name the flag
      alongside the plain-language phrasing**: the pinned console wording says
      "may notify people" and no longer contains the token `notify` as a flag
      name, so `--help` is the only place a reader can connect the line they saw
      to the command that sets it. Verify: T019.
- [ ] T016 [US2] Read the `authority:notify` label through the existing tracker
      `view` verb, once per run (FR-014). Skip the read where no tracker is
      configured (FR-012). Verify: T020.
- [ ] T017 [US2] Print the granted console lines, naming the source — label or
      local (FR-005). Verify: T021.
- [ ] T018 [US2] Call `record_notify_action` from each notifying action so the
      run reports what it did, unprompted (FR-010). Verify: T022.
- [ ] T019 [US2] [P] Test the tri-state: `--allow-notify` grants,
      `--deny-notify` denies, neither leaves the stored value alone.
- [ ] T020 [US2] [P] Test the resolution grid end to end, including that an
      explicit local deny beats a present label and that a missing label is not
      a deny.
- [ ] T021 [US2] [P] Console test that the granted line names its source, and
      that label-granted and locally-granted render differently.
- [ ] T022 [US2] (SC-002, SC-004) Manual exercise with the grant present:
      confirm the action happens and a `notify-action` event lands in
      `events.jsonl`, readable without access to the session.

**Verification**: T019–T021 automated; T022 manual. Full gate after.

**Checkpoint**: both halves work. This is where #240 becomes unblockable.

---

## Phase 5: User Story 3 — the agent declines what it was given (Priority: P2)

**Goal**: authority can be narrowed by its holder, never widened.

**Independent Test**: grant authority, hand the run a delivery plan it cannot
key, confirm it declines and that the decline reads differently from a refusal
for want of a grant.

- [ ] T023 [US3] Distinguish *declined by the agent* from *refused for want of a
      grant* in the reported output (FR-011). Verify: T025.
- [ ] T024 [US3] Ensure the irreversible class is refused regardless of the
      grant, and that its refusal says the class is not grantable rather than
      that a grant is missing (FR-013). Verify: T026.
- [ ] T025 [US3] [P] Test that the two refusal reasons render distinctly.
- [ ] T026 [US3] [P] Test that no grant value makes an irreversible action
      reachable — the negative test that must not pass vacuously. Assert against
      a *granted* fixture, not the default, or it proves nothing.

**FR-009's second half is deliberately untested.** *An agent MUST NOT widen its
own authority* has no mechanical enforcement: `clarify` put the local grant
command in every repo, so an agent that wants authority can run it. A test could
only assert the rule is written down, which looks like protection and is not —
and a green test named `test_agent_cannot_widen_authority` would be actively
misleading to the next reader. The rule is carried by the decision record and by
the event log making a self-grant legible after the fact. Recorded here so its
absence reads as a decision rather than an oversight.

**Checkpoint**: the asymmetry holds and is tested from the granted side.

---

## Phase 6: Polish

- [ ] T027 [P] Update `AGENTS.md` if the grant changes anything an agent
      working on wfctl itself must know.
- [ ] T028 Move `docs/architecture/a-human-grants-outward-facing-authority.md`
      from `proposed` to `accepted`, or state why it stays proposed. While
      proposed, `wfctl arch context` does not project it and the rule reaches
      readers only through the file.
- [ ] T029 Run the review panel unattended before opening the PR — it is
      description-triggered, so an unattended run skips it silently.
- [ ] T030 `uv run wfctl verify`, then open the PR against
      `.github/PULL_REQUEST_TEMPLATE.md` with `--body-file`.

---

## Dependencies

```
Phase 1 (naming)          ──┐
                            ├─► Phase 2 (resolver) ──┬─► Phase 3 (US1, refusal)
Phase 1 is independent    ──┘                        └─► Phase 4 (US2, grant)
                                                              │
                                          Phase 5 (US3) ◄─────┘
                                                              │
                                          Phase 6 ◄───────────┘
```

Phase 3 and Phase 4 both depend on Phase 2 and on nothing else, so they can be
built in either order — but **Phase 3 first**, because a grant shipped before its
refusal is a feature that has only been exercised in the state that cannot fail.
Phase 5 needs Phase 4's granted path to test against.

## Parallel opportunities

- T001 and T002 — different files, no shared state.
- T006, T007, T008 — three test files, one per Phase 2 function.
- T012, T013 — JSON and console, different assertions.
- T019, T020, T021 — flag, resolution, console.
- T025, T026 — different refusal paths.

Nothing in Phase 2's implementation tasks is parallel: T003, T004 and T005 all
edit `wfctl/_session.py`.

## Implementation strategy

**MVP is Phase 1 + 2 + 3.** That delivers a wfctl that refuses notifying actions
and says so clearly — strictly better than today, where the refusal is hardcoded
and silent, and it ships without granting anything to anyone.

Phase 4 is the second PR and the one that carries risk, because it is the first
time an unattended run can act on the tracker. Phase 5 and 6 follow.

**SC-005 is not a task here.** "The blocked step needs no change beyond reading
the grant" can only be checked after this merges and #240 rebases onto it. It is
a post-merge check, not uncovered work.

**Counts**: 32 tasks — 2 setup, 8 foundational, 6 US1, 8 US2, 4 US3, 4 polish.
Two are manual exercises (T014, T022) and neither is optional; the suite cannot
see skill prose, and `.agents/` is gitignored so a green suite is evidence about
this repo, not about what installs.
