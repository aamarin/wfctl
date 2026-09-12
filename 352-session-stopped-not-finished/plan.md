# Implementation Plan: Session Stopped, Not Finished

**Branch**: `352-session-stopped-not-finished` | **Date**: 2026-09-11 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/352-session-stopped-not-finished/spec.md`

## Summary

A session that was cut off mid-run cannot say so, so the next one reads the
single stop mark as *a human wrapped up* and stops to ask a question only the
absent human can answer. The fix records which of the two a stop was, and lets
the next session route on it.

Technically: `wfctl end` gains a `--continued` flag; the `end` event it appends
gains a `continued` boolean; `start-session` steps 4 and 9 branch on the
branch's issue key first and the most recent stop's kind second, instead of
asking whether any stop exists. One new event field, one new flag, no new event
kind, no new command, no change to `wfctl status`.

**The issue key is the first column, and it arrived after the first pass.** The
change as specified branched on the stop's kind alone, which left an issue
branch asking "what are we working on today?" after a deliberate wrap-up — on a
branch named for the one thing it is for. The question survives on trunk
branches only, where the name carries no answer and `main` accumulates a handoff
from every session that ever ended on it. `wfctl status --json` already reports
`issue`, and step 4 already runs it, so the fact costs no command.

The choice of a payload key over a second event kind is this branch's level-2
gate and is recorded at `docs/architecture/stop-kind-is-a-field-not-an-event.md`
(`proposed` — a human accepts). It decides against the handoff's own
recommendation, on the ground that none of the four existing readers of the stop
mark reads its payload, so the objection the handoff raised against a field does
not describe them; the argument is in the record's `Owns truth` and `Considered`
sections.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer`, `rich`. No new runtime dependency; none is needed.
**Storage**: append-only JSONL at `<state-dir>/events.jsonl`, plus
`session-summary.md` beside it. The state dir is XDG, per branch, outside the
repository — `wfctl state-dir` prints it.
**Testing**: `pytest` for the CLI and the event shape; `ruff` and `mypy` per the
repo's definition of done; `tests/test_start_session_asks_conditionally.py` for
the skill's table rows; `quickstart.md`'s five manual halves for what no test
reaches.
**Target Platform**: a terminal on macOS and Linux, invoked by a person or by an
agent harness.
**Project Type**: single project — a CLI whose package data is the skills tree
it installs.
**Performance Goals**: no new work on any hot path. No tracker round-trip is
added (the run's one is resolved by `wfctl start` and unchanged); the event log
is already read whole by `session_started` and `_stall`, and this adds one
key-read to a line already parsed.
**Constraints**: `layer-model` — the skill edit lands in `wfctl/agents/`, never
in the generated `.agents/`. `no-hardcoded-agent` (FR-010) — neither the mark
nor the rule may name an agent. `session-state-is-re-derived` (FR-003) — the
routing answer is recomputed from disk at every session start. FR-008 —
append-only; nothing already recorded is amended. FR-015 — `wfctl status` and
its JSON payload are untouched. And minimal-complexity bias.
**Scale/Scope**: one event log per branch, tens of lines; three source files and
one new test module.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. The gates below are
substituted from its documented conventions — `AGENTS.md` and the accepted
records under `docs/architecture/` — and the substitution is recorded in
Complexity Tracking, as the template requires.

**Project-independent:**

- [x] **Validation plan exists.** The repo's four definition-of-done commands,
      plus the specific tests named in `spec.md`'s Validation Strategy, plus
      `quickstart.md`'s five manual halves for the skill text the suite does not
      cover.
- [x] **Complexity is justified.** Nothing is added that the baseline lacks: one
      boolean field, one boolean flag. The rejected alternative (a second event
      kind) is the *more* structural option, and the record says why it loses.
- [x] **Ownership is stated.** `docs/architecture/stop-kind-is-a-field-not-an-event.md`:
      the `end` event's kind owns *did a session stop here*, its payload owns
      *did that stop finish*, and the kind cannot own the second because every
      reader of the first matches on it.

**This repository's:**

- [x] **`layer-model`** — the skill change is made in `wfctl/agents/skills/`,
      the committed source. `.agents/` is generated and is never edited.
- [x] **`no-hardcoded-agent`** (FR-010) — `continued` names what happens next,
      not a mechanism. The rejected name `recycle` is Claude-specific, and the
      clarification that settled this is in `spec.md`.
- [x] **`session-state-is-re-derived`** (FR-003) — the routing answer is a
      function of the branch name and two artifacts read at session start. Nothing is carried
      forward, and a context reset changes none of it.
- [x] **`a-rule-is-expressed-as-a-check`** — asked of the rule: is a violation
      visible in an artifact the work already produces? For the event shape,
      yes, and pytest checks it. For the routing rule, the artifact is the
      table in `SKILL.md`, and
      `tests/test_start_session_asks_conditionally.py` already binds each cell
      to the condition that selects it. The new row is added there the same way.
      What no check reaches is an agent that reads the table correctly and asks
      anyway; that is prose delivered at the moment it binds, which the record
      says is not a defect.
- [x] **Ruff and mypy unchanged** — the rule set stays `E4`, `E7`, `E9`, `F`
      (#14), and new functions are annotated under `disallow_untyped_defs`.
- [x] **No version bump.** `pyproject.toml`'s `version` ships a release on
      `main` and is not touched by this change.

**Post-design re-check (after Phase 1):** unchanged. The contracts in
`contracts/` add no abstraction, no dependency and no new surface beyond the one
flag; `data-model.md` introduces one field on one existing record. Ownership is
stated in a record that existed before either was written.

## Project Structure

### Documentation (this feature)

```text
specs/352-session-stopped-not-finished/
├── plan.md              # This file
├── research.md          # Phase 0 — R1 record shape, R2 surface, R3 read, R4 placement, R5 FR-013
├── data-model.md        # Phase 1 — the stop record, branch history, handoff, routing table
├── quickstart.md        # Phase 1 — five manual halves
├── contracts/
│   ├── wfctl-end.md          # the CLI surface and what it must not change
│   └── start-session-step-9.md   # the routing rule and its invariants
├── spec.md
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
wfctl/
├── _session.py                 # end() takes the kind; append_event gains `continued`
├── cli.py                      # end_cmd gains --continued, its closing line, the FR-013 warning
└── agents/skills/start-session/
    └── SKILL.md                # step 4's two reads; step 9's first two rows

docs/architecture/
└── stop-kind-is-a-field-not-an-event.md   # the level-2 record (written at this gate)

tests/
├── test_end_reports_observations.py        # existing — the end event's shape
├── test_start_session_asks_conditionally.py # existing — step 9's rows
└── test_session_stopped_not_finished.py    # new — the flag, the field, most-recent-wins, FR-013
```

**Structure Decision**: the existing single-project layout, unchanged. Every
edit lands in a module that already owns the thing being changed —
`_session.py` owns the event write, `cli.py` owns the surface,
`start-session/SKILL.md` owns the routing rule — so no file moves and no module
is added. `the-underscore-is-the-module-contract` is satisfied without a
decision: nothing here crosses a module boundary that is not already crossed.

## Design records

Read before Phase 1, per `reading-design-records`.

```
Design records: unknown — no design.md at
  /Users/andremarin/Development/wfctl-specs/352-session-stopped-not-finished
```

`unknown`, not `none`. `/speckit.brainstorm` was skipped on this branch —
`wfctl status` reports the step as `skipped`, and the spec's own Assumptions
record that no pre-specify design artifact exists. So nothing is known either
way about level-3 decisions taken before the spec; it is not established that
there were none.

**No level-3 record is written by this step, and that is a declared absence
rather than a silence.** The one structural choice this plan made with a
credible alternative — a flag on `end` versus a `wfctl continue` verb — is R2 in
`research.md`, with the alternative and the true reason it lost. It earns no
record under `<arch-root>/design/` because `design-md-indexes-the-records` makes
`design.md` the index a record is found through, and there is no `design.md`
here to index it; a record written outside that index is reachable only by the
glob that record exists to forbid.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from `AGENTS.md` and `docs/architecture/`, not from `.specify/memory/constitution.md` | The file does not exist in this repo. The template requires the substitution be recorded rather than the gates left decorative. | Leaving the two generic template gates alone was the alternative. They would have passed without reaching `layer-model`, `no-hardcoded-agent` or the release rule — all three of which this change can violate silently, and one of which (`layer-model`) is the documented way a skill edit gets installed over and lost. |

No other entry. The Constitution Check above has no violations: this plan adds
one boolean to an existing record and one flag to an existing command, and the
alternative it rejected was the larger of the two.
