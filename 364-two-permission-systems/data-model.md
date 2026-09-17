# Data model: two permission systems

**Feature**: `364-two-permission-systems` | **Date**: 2026-09-13
**Phase**: 1

One new event kind, one derived value, and no new storage. Everything here lives
in the branch's existing `events.jsonl` under the XDG state dir, written by
`append_event` (`wfctl/_io.py:71`), which stamps `ts` and `event` and passes every
other field through — so a new kind costs no change there.

## Entity: block event

One line in `events.jsonl`. Written by `wfctl blocked <action> --reason "…"`.

| Field | Type | Source | Notes |
|---|---|---|---|
| `ts` | ISO-8601 UTC string | `append_event` | stamped, not supplied |
| `event` | `"blocked"` | the writer | the kind; distinct from `notify-refused`, which is wfctl's *own* refusal |
| `action` | free-text string | the agent | positional; matched against clearings and successes by exact string |
| `reason` | free-text string | the agent | what the host said; required, FR-007 |
| `step` | step name, or `null` | inference at call time | the step current when the report was made (FR-010); `null` on a branch with no feature |

**The agent supplies two fields and infers none.** It names the action and quotes
the reason — the two facts it alone witnessed — and the step comes from
`build_report` at call time. That is the level-2 ownership line drawn as a record
shape: the agent hands facts up, wfctl decides what they mean.

**`step` is stored, not recomputed on read.** A block reports the step that was
current *when the refusal happened*; re-deriving it later would move the hold
onto whatever step is current at read time, which is a different claim and a
wrong one — the pipeline may have advanced since.

## Entity: clearing event

One line in `events.jsonl`. Written by `wfctl blocked <action> --clear`.

| Field | Type | Notes |
|---|---|---|
| `ts` | ISO-8601 UTC string | stamped |
| `event` | `"block-cleared"` | |
| `action` | free-text string | the string the block carried |

No reason, no step. It asserts one thing — a person took the action — and the
step it releases is whatever the superseded block named.

## Derived value: the standing block

Not stored. Computed on every read, as `session-state-is-re-derived` requires.

```
read events.jsonl for this branch
  → keep the LAST event per `action` among:
        blocked          (a block was reported)
        block-cleared    (a person cleared it)
        notify-action    (the action later succeeded through wfctl)
  → for each surviving `blocked`, the step it names is held
```

`notify-action` is in the set because a run that retried and succeeded already
writes it, and because `wfctl issue comment|create|label` writes it for itself on
a successful call (FR-020). It is the cheap release; `--clear` is the reachable
one.

**Three kinds, one keyspace.** They are matched on `action` alone, and `action`
is free text on all three. A block reported as `issue-comment` and a success
recorded as `comment` do not match, and nothing detects that — it is the failure
mode the level-3 record names as where this breaks first, and `--clear` is the
escape a person can spell to match.

## Derived value: the held step

| | |
|---|---|
| Signature | `block_reason(agent_dir, branch, step) -> str \| None` |
| Shaped after | `verification_block(repo_root)` at `wfctl/_predicates.py:506` |
| Returns | the `reason` of the standing block naming that step, else `None` |

Applied in `build_report` after `_infer_steps` returns, never inside the
per-step loop — `_infer_steps` cascades on the first `pending` step, and a hold
injected mid-loop would force later steps that are legitimately `done` to
`pending`.

## State transitions

```
no event for this action
  │
  │ wfctl blocked <action> --reason "…"
  ▼
HELD ──── wfctl blocked <action> --clear ────────► released
  │
  └────── notify-action for the same action ─────► released
  │
  └────── wfctl blocked <action> --reason "…" ───► HELD, later reason stands
```

A held step whose block is released reports from its own artifacts again, with
nothing carried over. Two blocks of one action collapse to the later; the earlier
reason is not separately recoverable from the step, though both lines stay in
`events.jsonl`.

## What this feature adds nowhere

- No new step state (FR-018). A held step is `in_progress` with the reason on its
  annotation — the shape `verification_block` already uses.
- No new fact row in the authority report (FR-018).
- No new top-level key in the `--json` payload (FR-018). The hold reaches the
  payload through the `state`, `reason` and `remedy` fields each step already
  carries.
- No change to `notify`'s three event kinds or its gate (FR-019).
