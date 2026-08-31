# Phase 1: Data model — session truth ownership

Three entities. Two of them are computed on every read and stored nowhere; the
third is the only thing a session file still holds.

## PipelineStep

One per step in the pipeline, in pipeline order. Produced by `_infer_steps` from
artifacts on disk; consumed by the console renderer.

| Field | Type | Notes |
| --- | --- | --- |
| `name` | str | `brainstorm` … `implement`; the table in `_pipeline.py` is the order |
| `state` | str | `done` · `in_progress` · `pending` · `skipped` — replaces `symbol` |
| `annotation` | str \| None | e.g. `3/8 done`, and the reason implement is blocked |

**Validation**: `state` is one of the four names. Nothing outside `cli` maps it
to a symbol, and nothing stores a symbol.

**State transitions**: none held. A step's state is recomputed from artifacts on
every read; there is no transition to record because there is no prior value to
transition from.

**The distinction that matters**: `skipped` and `done` both mean "does not
block" and only one of them ran. `pending` and `skipped` are both "no artifact
here" and mean opposite things — pending is where the reader is sent, skipped is
already behind them.

## PipelineReport

What a caller gets when it asks where the feature stands. One structure carrying
the steps and the facts that used to require a second file.

| Field | Type | Notes |
| --- | --- | --- |
| `steps` | list[PipelineStep] | in pipeline order |
| `current` | str \| None | the step a reader is sent to; None when every step is behind them |
| `next_command` | str \| None | the command that advances `current`; None when the story is complete |
| `session_started` | bool | whether a `start` event exists in this branch's event log |

**Validation**: `current` is None exactly when `next_command` is None. A report
with a current step and no command is the failure `_STEPS` was collapsed into one
table to prevent (`_pipeline.py`), and must not be constructible.

**Ownership**: computed by wfctl on every read, from spec artifacts, git, and the
event log. Never read from a session file. Per `session-state-is-re-derived`.

## SessionHandoff

The prose a session leaves for the next one. The only session content that
survives, because nothing on disk can reconstruct it.

| Field | Type | Notes |
| --- | --- | --- |
| accomplishments | prose | written by the agent or human |
| decisions | prose | why, which no diff shows |
| next session TODO | prose | intent, not position |
| observed position | derived | pipeline position, boundary answered, tree dirty — written at end from the report above |

**Validation**: honest standing alone. A handoff whose prose was never filled in
reads as empty; nothing in it asserts a completion, because completion is not
observable (`#70`).

## Naming

The spec says "resume-point file" and "session state file" because it avoids
implementation names. They are `current.md` and `current.json` in the state
directory (`wfctl state-dir`), and every artifact below this one uses those
names.

## Removed

| Thing | Why it goes |
| --- | --- |
| `current.md` | every field re-derivable but the prose, and the prose was never filled |
| `current.json` | same, minus one fact the event log already holds |
| `status` field | no reader; work status is the pipeline |
| `symbol` on a step | a rendering stored as state |
| `load_agentconfig` | zero callers, including tests |
