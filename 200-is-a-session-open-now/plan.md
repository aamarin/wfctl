# Implementation Plan: is a session open now?

**Branch**: `200-is-a-session-open-now` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/200-is-a-session-open-now/spec.md`

## Summary

`session_started` answers "has `wfctl start` ever run on this branch" and six
speckit skills read it as "is a session open now". This feature adds the second
answer without disturbing the first: `wfctl start` accepts an opaque session id
from its caller, records it on the `start` event it already appends, and every
later command compares the id the caller presents against the last one recorded.
A caller presenting no id sees today's behaviour exactly.

The approach is the one the design pass settled: no new file in the state dir, no
new runtime dependency, and the comparison in `_session.py` beside the predicate
it supplements. `start` already appends an event on the already-initialized path
when a sitting opens, so the id rides on a line that is written anyway, the
append-only log stays the single source, and `session-state-is-re-derived` holds
— the id is the one value re-derivation cannot reach, the same carve-out
`auto_approve` already occupies.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer`, `rich` — both already present. This feature
adds none, and the "no other runtime dependencies" line in `AGENTS.md` is a
constraint it must not spend.
**Storage**: the branch's append-only `events.jsonl` in the XDG state dir
(`wfctl state-dir`). No new file and no migration — an event gains an optional
key, and a reader that does not know the key is unaffected.
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`,
`uv run mypy wfctl/` — all three green is the repository's whole bar. Plus
`uv run wfctl doctor` with no standing finding, and `uv run wfctl install-skills`
followed by hand-exercising any changed skill, because the suite checks that
skills ship and cross-reference, not that they read well.
**Target Platform**: developer machines (macOS, Linux) and CI. No server, and no
network call on any path this feature touches.
**Project Type**: single Python package that is both a CLI and the carrier for a
skills tree shipped as package data.
**Performance Goals**: `wfctl status` stays a pure disk read. No path this
feature adds may make a network call — the notify grant is already resolved once
by `start` and read back from the log precisely so `status` does not spend a
round-trip per call, and this must not reintroduce one.
**Constraints**: no new runtime dependency; no new file in the state dir; no
host-specific variable named in any committed hook (`no-hardcoded-agent`); skills
reach this answer through wfctl rather than reading `events.jsonl`
(`pipeline-state-is-one-payload`); minimal-complexity bias.
**Scale/Scope**: three modules (`_session.py`, `_pipeline.py`, `cli.py`) and two
shipped skills (`start-session`, `speckit-orchestrate`). One new CLI option, two
new status fields, one changed gate. A branch's log is a few dozen lines; nothing
here is sensitive to its size.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository ships no `.specify/memory/constitution.md`. The gates below are
substituted from its own documented conventions — the accepted records
`wfctl arch context` prints, and the definition of done in `AGENTS.md` — and the
substitution is recorded in Complexity Tracking, per the template's own
instruction that a gate with no source is decorative.

**Project-independent gates**

- [x] Validation plan exists: `uv run pytest -q`, `uv run ruff check wfctl/
      tests/`, `uv run mypy wfctl/`, `uv run wfctl doctor`, plus the per-requirement
      unit coverage named in the spec's Validation Strategy and the manual
      two-conversation exercise that no test run can cover.
- [x] Complexity is justified: nothing is added. No dependency, no module, no file
      in the state dir — the id rides on an event already written, which is what
      `design/200-session-id-rides-on-the-start-event.md` weighed a `session.json`
      against and won on crash behaviour.
- [x] Ownership is stated: the **caller** owns the session id; wfctl records it
      verbatim. wfctl cannot compute it — its process is not the conversation, and
      a sub-agent's process is not its parent's, which is why
      `session-identity-comes-from-the-caller` forbids deriving it from the
      process tree.

**Substituted from this repository's accepted records**

- [x] `session-identity-comes-from-the-caller` — the id is opaque, taken from
      `--session-id` falling back to `WFCTL_SESSION_ID`, never parsed, never
      derived, and no host's variable name appears in wfctl's source.
- [x] `session-state-is-re-derived` — the id is stored because it is the one value
      re-derivation cannot reach. Every answer built on it is computed from the
      log at read time and cached nowhere.
- [x] `pipeline-state-is-one-payload` — the new answers join the existing
      `PipelineReport` and reach every view through it. No skill reads
      `events.jsonl`, and no second inference path appears.
- [x] `no-hardcoded-agent` — the shipped skill takes the id from the environment
      in the `${VAR:+--flag "$VAR"}` shape already used for `--agent`, so no host
      is named in committed config.
- [x] `a-rule-is-expressed-as-a-check` — "the id is never derived" is visible in
      wfctl's own source, so a test asserts it rather than prose asking for it.
- [x] `wfctl-runs-the-verification` — unchanged; this feature adds no
      self-certification path.

**Post-Phase 1 re-check**: passes unchanged. Phase 1 introduced no entity that
owns a derived value, no contract requiring a network call, and no file in the
state dir. The one surface it grew is `status --json`, which is the payload the
one-payload record already designates as the place for it.

## Project Structure

### Documentation (this feature)

```text
specs/200-is-a-session-open-now/
├── spec.md              # /speckit.specify output
├── design.md            # /speckit.brainstorm output
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli.md           # Phase 1 output
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit.tasks output — not created here
```

### Source Code (repository root)

```text
wfctl/
├── _session.py          # session_started stays as it is; last_session_id()
│                        #   and session_open_for() join it, beside it
├── _pipeline.py         # PipelineReport gains session_open and session_holder;
│                        #   build_report fills them from the caller's id
├── cli.py               # start gains --session-id; resume and end compare
│                        #   rather than only checking existence; status renders
│                        #   the new state and the takeover line
├── _io.py               # unchanged — append_event already takes **kwargs
└── agents/
    ├── skills/
    │   ├── start-session/SKILL.md        # presents the host's id (FR-013)
    │   └── speckit-orchestrate/SKILL.md  # step 0 reads the new answer
    └── commands/                          # unchanged

tests/
├── test_agent_session.py        # the identity comparison, all four states
├── test_pipeline.py             # the payload carries both answers
├── test_cli_status.py           # the two refusals are distinct strings
├── test_cli_start.py            # --session-id, its fallback, the takeover line
├── test_cli_resume.py           # resume refuses a caller that does not hold it
├── test_cli_end.py              # end refuses rather than taking over
├── test_skills_ship.py          # the shipped skill names no host variable
├── test_architecture.py         # wfctl's source names no host variable
└── test_no_regression_unwired.py  # the gate surface, unchanged with no id

docs/architecture/
├── session-identity-comes-from-the-caller.md          # accepted, committed
├── design/200-session-id-rides-on-the-start-event.md  # proposed, committed
└── scans/200-clarify.md                               # committed
```

**Structure Decision**: the existing single-package layout, with no new module.
The comparison belongs in `wfctl/_session.py` because `session_started` lives
there and the new answer is the same question asked with one more input; splitting
them across two modules would make a reader chase the second half of one concept.
`_stall.opens_a_new_sitting` is deliberately left alone — it answers "did the
previous sitting run anything", a different question that happens to read the same
events, and folding the two would give one function two reasons to change.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from repository conventions rather than read from `.specify/memory/constitution.md` | The file does not exist here; the template instructs substitution and requires it be recorded in this table | Shipping only the two project-independent gates was rejected: this repository has eleven accepted architecture records, six of which bind this feature directly, and a Constitution Check that ignored them would pass a plan that violates them |
| `status --json` grows fields rather than repurposing `session_started` | Clarify Q4 — state A ("the branch has never had a session") must stay answerable, and a repurposed field cannot answer it | Repurposing was rejected because state A and state C then render identically, which is this issue's defect with the two states swapped |
| `start` writes an event on a path that is otherwise idempotent | A takeover must leave a trace, and `start` is the only command that learns of one | Writing nothing was rejected by FR-014: the displaced conversation would have no signal but a refusal that does not mention the takeover. Appending unconditionally was rejected because `/start-session` runs `start` on every handoff, and two tests pin that a repeat `start` leaves the log byte-identical |
