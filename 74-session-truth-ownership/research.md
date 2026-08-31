# Phase 0: Research — session truth ownership

No `NEEDS CLARIFICATION` remained in Technical Context: the language, the two
runtime dependencies, the test commands and the target platform are all fixed by
the existing project and none of them changes here. What follows is the research
that did happen — decisions taken during the design pass and at
`/speckit.clarify`, each recorded with what it rejected.

## Decision: session existence comes from the event log

**Decision**: delete `current.json` along with `current.md`. Whether a session
was started for this branch is read from the `start` event already appended to
`events.jsonl`.

**Rationale**: every other field on `current.json` is derived elsewhere —
verified, not assumed: issue, branch and repo in `_resolve_context`
(`cli.py:82-86`), the step by `_infer_steps` on every read, the next command by
`next_step_content`, `updated` by the last event's timestamp, and `status` has no
reader at all. That leaves one fact, and the event log already records it as it
happens rather than caching a conclusion about it.

**Alternatives considered**:
- Keep the file with the derivable fields stripped — two files asserting one
  fact, which is the shape `session-state-is-re-derived` exists to forbid.
- Keep it unchanged apart from dropping `status` — smallest diff, but
  `workflow_step` survives as a cache nothing should trust, and the next reader
  cannot tell that from a value that is maintained.

## Decision: not-started and skipped are different states

**Decision**: a step reads as skipped only when its own artifact is absent *and*
a later step's artifact exists. Absence with nothing after it is not-started.

**Rationale**: the design gate fires only when `design.md` is present
(`_pipeline.py:267-273`) — "a change that never drew a design has nothing to
advance past". So the dash already means "passed by", and the defect is that
inference spends it on "nothing has happened yet". Two situations that need
opposite advice currently render one way or the other depending on whether a
directory exists.

**Alternatives considered**:
- Render both as skipped and route to `specify` — consistent with the gate, but
  a brand-new feature is never pointed at the first step of the pipeline.
- Drop the skipped state entirely — makes "we moved past this without one"
  inexpressible, and that is a real and legitimate history.

## Decision: state names now, machine surface later

**Decision**: `_PipelineStep` carries `done` / `in_progress` / `pending` /
`skipped`; `cli` maps names to `● ▶ ○ –` when printing. No serialized view ships
in this feature.

**Rationale**: `pipeline-state-is-one-payload` is proposed, not accepted. Code
that depends on a decision makes it binding by fact rather than by agreement,
and the record is the thing an implementation is written against. Removing the
glyph from inference is the half that this feature's other requirements need
anyway, because `cli.py` and `_pipeline.py` are already open for the next-command
line and the not-started fix.

**Alternatives considered**:
- Ship the whole payload with a serialized view — makes an unaccepted record
  binding, and puts a flag, a schema and annotation structure into a PR whose
  actual defects live in `_session.py`.
- Defer all of it — leaves the agent reading a drawing at exactly the moment
  the drawing becomes its only read.

## Decision: fossils are removed on first touch

**Decision**: any command that touches a state directory unlinks `current.md`
and `current.json` if present.

**Rationale**: they are inert to the new code but readable by an older
`start-session` elsewhere on the machine, which would produce precisely the stale
answer this feature removes. There are tens of state directories on a developer
machine, and none of them is hand-edited — `current.md`'s prose sections have
never been filled in by anything.

**Alternatives considered**:
- Leave them — costs nothing to build and keeps the stale-read window open for
  as long as any un-upgraded skill copy exists.
- Report them from `doctor` — visible, but the file stays readable until someone
  acts on the report.

## Verified against the code

| Claim | Evidence |
| --- | --- |
| `current.md` is written only at `start` | `_session.py:104-118`, `cli.py:145-153` |
| `end` hardcodes a completion | `_session.py:41` |
| `status` has no reader | only `_session.py:21,81,101` touch it |
| an empty file and a missing file are one state | `_file_exists`, `_pipeline.py:70` |
| `steps_display` returns a glyph in a dict | `_pipeline.py:357` |
| `load_agentconfig` has zero callers | `_io.py:58` |
| `status` cannot name the next command | `cli.py:121-153` — `next_step_content` is not imported |
| an empty feature dir is reachable | `setup-plan.sh:37` |
| a finished pipeline renders no cursor and no line | observed on a scratch repo with no definition of done |
