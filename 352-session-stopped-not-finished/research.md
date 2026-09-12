# Research: Session Stopped, Not Finished

**Branch**: `352-session-stopped-not-finished` | **Date**: 2026-09-11
**Input**: `spec.md`, issue #352, the branch handoff in the state dir.

The spec leaves three things open and marks two of them as gate work. Each is
resolved below. Nothing in `plan.md`'s Technical Context is left as NEEDS
CLARIFICATION.

## R1 — How the record distinguishes a finished stop from a continued one

**Decision**: a `continued` boolean on the existing `end` event. One event kind,
the kind answering *did a session stop here* and the payload answering *did it
finish*. Absent key reads as finished.

**Rationale**: the full argument is the level-2 record
`docs/architecture/stop-kind-is-a-field-not-an-event.md`, written at this gate
and `proposed` pending a human. In short: four readers match on
`event == "end"` today and all four ask the same question. A second event kind
turns *a session stopped* into a set of two names with nothing enforcing
membership, and the reader written next year fails by under-counting rather than
by crashing. A payload key leaves those four untouched and charges the cost to
the one reader that asks the new question.

**Alternatives considered**: a distinct `continued` event (the handoff's
recommendation, and sound — it loses on fit); deleting the `end` line so the
next session routes past it (rejected in #352: races concurrent writes and
erases what User Story 3 exists to keep); a separate `stops.jsonl`; a `status`
key (the spelling `test_end_reports_observations` forbids, for #70's reason).
Each is carried in the record with its true reason.

## R2 — The surface an operator uses to declare a continued stop

**Decision**: a flag on the existing command — `wfctl end --continued`. No new
verb.

**Rationale**: FR-002 requires a continued stop to produce the handoff under the
same template, same location, same write-once rule, and the same kept-file
report as a finished one; FR-002 plus Story 2 scenario 3 (refused identically
when no session has started) means a second verb would be `end_cmd`'s body
verbatim with one argument changed. The duplication is the whole of its cost,
and it is the kind that drifts — the refusal path, the observation call, the
kept-file mtime line and its two comments would have to stay in step by hand.

The flag also matches the record decided in R1: one command with a kind
argument, writing one event with a kind field. A reader who knows the flag knows
the field, and the surface stops being a second thing to learn.

**Alternatives considered**:
- `wfctl continue` / `wfctl pause` as its own verb — a clearer name at the call
  site, and genuinely easier for a hook to reach without knowing `end`'s other
  flags. Rejected on the duplication above, not on the naming, which is better.
- `wfctl end --kind continued|finished` — an enum leaves room for a third kind
  later. Rejected as speculative: nothing names a third kind, and FR-011's
  default is a boolean's default for free.

## R3 — How step 9 reads the stop, and what it reads it with

**Decision**: `start-session` reads `events.jsonl` directly, as it does today,
with one stated command:

```bash
grep '"event": "end"' "$(wfctl state-dir)/events.jsonl" | tail -1
```

Three observable outcomes, which are exactly the rows: no output (no stop
recorded), a line containing `"continued": true` (continued), any other line
(finished).

**Rationale**: step 4 already sends the agent to `events.jsonl` for this fact,
so this is a change of what it looks for rather than a change of where. Stating
the literal command matters more than it looks: the current step names the fact
in prose — *whether any line carries `"event": "end"`* — and the new rule is
*the most recent `end` line's kind*, which an agent improvising a grep gets
wrong in the direction that starts work on a branch a person wrapped up.

**Alternatives considered**:
- A field on `wfctl status --json`. Rejected by FR-015 and by the clarification
  behind it: the status view is unchanged by this feature, and a status row
  would be a second reader of the record.
- Parsing `wfctl log`'s rendered output. It works — the kind lands in the detail
  string as `continued=True` — but it reads a human-facing rendering whose
  colour markup and column widths are not a contract, to recover a fact the
  JSONL states literally.

## R4 — Where the routing rule is written so it reaches every repository

**Decision**: `wfctl/agents/skills/start-session/SKILL.md`, the committed
package-data source. Not `.agents/`, and not any consuming repo's copy.

**Rationale**: FR-012. `layer-model` makes every dotted directory at the repo
root generated and gitignored, so a rule written into `.agents/` survives one
session and is overwritten by the next `install-skills` with no error. The
committed source ships in the wheel and reaches every repo the tool installs
into, which is the requirement.

**Consequence for validation**: the pytest suite does not cover
`wfctl/agents/`. `tests/test_start_session_asks_conditionally.py` is the
exception and it asserts against step 9's *table rows*, binding each cell to the
condition that selects it — its own docstring records a panel showing three
earlier assertions passing with the two cells swapped. The new row goes in that
file the same way, and the manual exercise in `quickstart.md` covers what no
test reaches.

## R5 — What `end` can observe about the handoff, for FR-013

**Decision**: `end --continued` warns when the handoff on disk is an *unfilled
template* — the `## Next Session TODO` section absent, empty, or carrying only
the `- [ ] (fill in)` placeholder the template writes. It says what it observed
and that the next session will therefore ask. It does not judge filled prose.

**Rationale**: FR-013 requires the operator to be told the handoff names no
first action, and #70 is the standing reason `end` reports observations rather
than conclusions — `**Status**: complete` was written on every run including one
that closed with half the tasks open. Whether a filled sentence *names a usable
first action* is step 9's judgment and is not computable here; whether the
template was ever filled in is. The observable case is also the specified one:
the spec's edge case is a scaffold "whose next action is still a placeholder".

This fires on the common path by construction. A continued stop on a branch with
no handoff writes a fresh template and then warns about it — correct, and the
most useful moment to say so, because the operator is still there.

**Alternatives considered**: warning whenever the summary was newly written by
this run. Rejected as the wrong fact — a handoff copied in by
`worktree-handoff` is not written by `end` and may be complete, and #239 says
provenance is not recoverable from the file. The placeholder is recoverable.
