---
status: proposed
---

# An action is named by the verb that takes it, so taking it lifts its own hold

## Context

`wfctl-records-outward-actions-and-never-gates-them` (proposed, level 2) decides
that for each action the latest event decides whether a hold stands, and that
the name is fixed once. Three writers put that name into the log, and today they
disagree:

```
skill files a block:     report-block issue-create     → action "issue-create"
retry succeeds:          wfctl issue create            → action "create"
close succeeds:          wfctl issue close             → nothing
```

So a retry that worked has never lifted its hold. `blocked --clear` was the only
exit and hid the mismatch, and level 2 removes `--clear`. Left alone, a hold
filed against `issue-create` or `issue-close` would have nothing to lift it but
`report-action` typed by hand, for an action wfctl itself had just performed.

## Verified

- `_tracker.py:358` calls `record_notify_action(agent_dir, verb)`: the bare verb,
  `create`.
- `_tracker.py:74` records only `{"comment", "create", "label"}`. `close` is left
  out, and the comment above it says the reason is the grant.
- `speckit-delivery-plan/SKILL.md:148` and `speckit.analyze.md:249` file
  `issue-create`; `end-session/SKILL.md:231` files `issue-close`.
- `_session.py:657`: `standing_blocks` matches events on `action` alone, with
  `blocked`, `block-cleared` and `notify-action` sharing one timeline.
- `_restart.py:313` folds `notify-action` events into the summary by `action`,
  so the name also reaches the handoff a person reads.
- `wfctl/agents/trackers/github.json`: the `verbs` section also carries `start`
  and `stop` (board moves run from `post_create` and `pre_remove`), plus the read
  verbs `list`, `view`, `labels` and `fields`.
- `grep -rn "action=" wfctl/*.py`: every event carrying an `action` is written in
  `_session.py:543-613`, reached from `_tracker.py` and the two CLI verbs only.

## Assumed

- **No log in use holds a block that only a bare name would lift.** Every block
  filed so far comes from skill prose that already said `issue-…`, so a bare
  `create` never matched one anyway. Falsified by a hand-filed `blocked create`.

## Direct baseline

Normalize on read. `standing_blocks` treats `create` and `issue-create` as one
action, and `_tracker.py` adds `close` to the verbs it records. No writer changes
names, and old logs read identically.

## Decision

The writer names the action. `_tracker.py` records every write verb in the
`verbs` section it ran successfully as `issue-<verb>` — `issue-comment`,
`issue-create`, `issue-label`, `issue-close` — and the skills file blocks under
those names. The set is one constant beside the dispatch, renamed from
`_NOTIFYING_VERBS` because it no longer means "notifying".

`start` and `stop` stay out. They run from worktree hooks rather than from a
session's turn, nothing files a block against them, and recording them would put
a board move into every restarted session's handoff.

## Diagram

```
          baseline                                decision

wfctl     ┌───────────┐  writes "create"          ┌───────────┐  writes "issue-create"
          │ _tracker  │──────────┐                │ _tracker  │──────────┐
          └───────────┘          ▼                └───────────┘          ▼
                            ┌─────────┐                             ┌─────────┐
                            │ events  │                             │ events  │
                            └─────────┘                             └─────────┘
                             ▲       ▲                               ▲       ▲
                        reads│       │reads                     reads│       │reads
          ┌────────────────┐ │  ┌────┴─────┐          ┌────────────────┐ │  ┌────┴─────┐
          │standing_blocks │─┘  │ _restart │          │standing_blocks │─┘  │ _restart │
          │ + "create" ≡   │    │ prints   │          │ matches names  │    │ prints   │
          │ "issue-create" │    │ "create" │          │ as written     │    │ issue-…  │
          └────────────────┘    └──────────┘          └────────────────┘    └──────────┘
```

The graphs differ in where tracker vocabulary lives. In the baseline the reader
of holds has to know that `create` is an issue verb, and `_restart`, the second
reader, prints a name that does not match what the skills call the action. Every
future reader would need the same mapping. In the decision the name is right
when it is written, so both readers stay ignorant of trackers.

## Considered

- **The baseline: normalize on read.** Sound, and it keeps old logs untouched.
  It loses on the second reader: `_restart` would print `create` beside a
  summary that names the action `issue-create`, and each future reader would
  have to repeat the mapping or disagree.
- **A closed vocabulary that `report-block` validates.** It would catch a
  mistyped action at the moment of filing rather than as a hold that never
  lifts. Rejected because it makes wfctl own the list of every outward action an
  agent might take — the list the grant claimed to own and never did.
  `the-agent-reports-the-block-wfctl-never-saw` kept `action` as free text for
  that reason.
- **Record `start` and `stop` as well**, for uniformity. It adds entries that no
  block names and puts board moves into the restart handoff, for no reader that
  asked for them.

## Consequences

A successful `wfctl issue create` or `close` lifts a matching hold, and nobody
types anything. Holds the agent files by hand still need the name spelled right,
and a typo still produces a hold that never lifts. `status` prints the held
action's name, which is where a person sees a mismatch.

**The name carries the verb and not the issue, so a hold is lifted by the next
success at that verb rather than by the one it was filed for.** A refused
comment on #384 followed by a successful comment on #300 leaves no hold, and the
refused comment is never made. Scoping the name to an issue would fix that and
break the thing this record is for: the skills file `report-block issue-comment`
with no issue in it, so an id-scoped reader would stop matching the holds that
are actually written. The block is an agent's report of what its host refused,
and the agent is working one issue at a time — a second issue inside one held
step is the case this trades away.

Branch is the one scope that *is* carried, because `standing_blocks` already
reads it on the block side: `record_outward_action` writes it too, so a success
in one worktree cannot lift another worktree's hold under a shared
`WFCTL_STATE_DIR`.

Logs written before this change keep their bare `create` entries. Nothing reads
those as holds, and `wfctl log` prints them as they are.

## Verification

- A test files `report-block issue-create`, runs a stubbed `wfctl issue create`
  that exits 0, and asserts that `status` no longer holds the step. The same test
  for `issue-close`.
- A test runs `wfctl issue start` and asserts that no `notify-action` event is
  written.
- A test asserts that every `report-block issue-<x>` in `wfctl/agents/` names a
  verb in `_RECORDED_VERBS`
  (`test_every_issue_action_a_skill_files_names_a_verb_wfctl_records`). A name
  nothing records is a hold nothing can lift, and the six files agree by hand.
- A test files a block on one branch, records the same action on another, and
  asserts the first branch's hold still stands
  (`test_a_success_on_one_branch_does_not_lift_a_hold_on_another`).

## Log

- 2026-09-15  proposed  — #384 level 3; removing `--clear` exposed that a
  successful retry never lifted its own hold
