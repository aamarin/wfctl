# Implementation Plan: two permission systems

**Branch**: `364-two-permission-systems` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/364-two-permission-systems/spec.md`

## Summary

Two permission systems decide whether an agent may take an outward action, and
wfctl can see only one of them. When the agent's own host refuses a tracker write,
wfctl's process never starts — no exit code, no stderr, no invocation to record
one — and the step that owned the write reports exactly as it would have had the
write succeeded.

The approach: a new ungated command, `wfctl blocked <action> --reason "…"`, lets
the agent report the one fact it alone witnessed. A predicate shaped after
`verification_block` reads the event back and holds the step that was current when
the report was made, at `in_progress` with the reason on its annotation. A person
releases it with `wfctl blocked <action> --clear`, and a later success for the same
action releases it for free. Two lines in the authority report stop overstating
what wfctl knows.

No new step state, no new fact row, no new payload key, and `wfctl notify` is
untouched.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer`, `rich` — both already present; this feature adds none
**Storage**: `events.jsonl` in the XDG state dir, append-only JSONL via `wfctl/_io.py:71`. No schema, no migration
**Testing**: `uv run pytest -q`; unit coverage for the two verbs, pipeline coverage asserted on the `--json` payload, rendering coverage with `NO_COLOR` pinned as `conftest.py` requires
**Target Platform**: CLI on macOS and Linux
**Project Type**: single project — a CLI with its skills tree as package data
**Performance Goals**: the new predicate adds one read of `events.jsonl`, which `build_report` already opens. No network call, no git call. `status` runs on every session start, so this is the bar it must not cross
**Constraints**: `pipeline-state-is-one-payload`, `session-state-is-re-derived`, `wfctl-runs-the-verification` (all accepted) bind this work; `the-agent-reports-the-block-wfctl-never-saw` and `364-the-block-report-is-its-own-verb` (both proposed) are its design. Minimal-complexity bias
**Scale/Scope**: one new command with two mutually exclusive modes, one new event kind pair, one new predicate, two changed strings, one skill instruction

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. The gates below are
substituted from its own documented conventions — `AGENTS.md` § Definition of
done, § Testing conventions, § Code style, and the accepted records `wfctl arch
context` prints. The substitution is recorded in Complexity Tracking, as the
template requires.

- [x] **Validation plan exists.** `uv run pytest -q`, `uv run ruff check wfctl/
      tests/`, `uv run mypy wfctl/`, then `uv run wfctl doctor` — the repository's
      whole bar. Per-surface tests are named in Phase 2 below, and the skill
      change carries the `install-skills`-and-read-it step `AGENTS.md` requires
      for anything under `wfctl/agents/`.
- [x] **Complexity is justified.** One new command, argued at level 3 against the
      cheaper `--blocked` flag it lost to on the gate rather than on cost. One
      new predicate, needed whichever verb writes the event because nothing reads
      any `notify-*` event back today (verified in `research.md`). Nothing else is
      added: no new state name, no new payload key, no new storage.
- [x] **Ownership is stated.** wfctl owns *may the pipeline advance past this
      step, and why not* — the agent cannot, because a step state an actor sets
      for itself is the claim the state exists to check. The agent owns *was an
      outward action refused, and which one* — wfctl cannot, because the host
      refuses the command before the process exists and no host offers a way to
      ask. Both halves are the level-2 record, in force as `proposed`.

**Post-Phase-1 re-check**: all three still hold. Phase 1 added no abstraction:
`data-model.md` introduces one event kind pair and one derived value, and
`contracts/cli.md` adds one verb with the two modes level 3 already settled.

## Project Structure

### Documentation (this feature)

```text
specs/364-two-permission-systems/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli.md           # Phase 1 output — the published surface
├── design.md            # pre-existing, from /speckit.brainstorm
├── spec.md              # pre-existing, from /speckit.specify
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
wfctl/
├── cli.py               # + @app.command("blocked"); _IRREVERSIBLE_NOTICE reworded;
│                        #   the new authority line printed beside it
├── _session.py          # + record_blocked, record_block_cleared, standing_blocks
├── _predicates.py       # + block_reason, shaped after verification_block
├── _pipeline.py         # build_report applies the hold after _infer_steps returns
└── agents/
    └── skills/          # the instruction to report a block (FR-017)

tests/
├── test_blocked_cli.py          # the verb: both modes, exit codes, no-grant, no-feature
├── test_blocked_holds_step.py   # the hold: overrides done, releases both ways, survives a session
└── test_notify_status.py        # extended: the two authority lines in all eight renderings
```

**Structure Decision**: single project, the existing flat `wfctl/` package. This
feature adds no module — the four files it touches are the ones that already own
the event log, the predicates, the inference and the CLI surface. The skills tree
under `wfctl/agents/` is package data and is installed, not imported.

## Phase 2 approach

_What `/speckit.tasks` will break down. Not the task list itself._

Five surfaces, in dependency order. Each is independently testable, and the first
two deliver User Story 1 on their own.

**1. The event writers** — `_session.py`. `record_blocked(agent_dir, action,
reason, step)` and `record_block_cleared(agent_dir, action)`, each a single
`append_event` call, matching the three `notify-*` writers beside them.

**2. The verb** — `cli.py`. `@app.command("blocked")` with a positional `action`,
`--reason` and `--clear`. It resolves context the way `notify_cmd` does and
**does not call `action_grant`** — the pinned assertion, not an omission. The step
comes from `build_report` at call time; the agent never names it.

**3. The predicate and the hold** — `_predicates.py` and `_pipeline.py`.
`standing_blocks` keeps the last event per action across `blocked`,
`block-cleared` and `notify-action`; `block_reason` answers for one step;
`build_report` applies it **after** `_infer_steps` returns, never inside the loop
— that loop cascades on the first `pending` step, and a hold injected mid-loop
would force legitimately-`done` later steps to `pending`.

**4. The two authority lines** — `cli.py`. One constant reworded, one added, both
printed unconditionally beside `_notify_line`. FR-003 pins that the new line names
no command.

**5. The skill instruction** — `wfctl/agents/skills/`. An agent that is refused
must know to report it. Per `AGENTS.md`, this is not verified by the suite: run
`uv run wfctl install-skills` from the working tree and read the instruction as an
agent would.

### Tests the design records ask for by name

The level-3 record's Verification section is a list of assertions, not a
suggestion. Carried into Phase 2 verbatim:

| Assertion | Why it exists |
|---|---|
| `wfctl blocked` on a branch with no grant exits 0 and writes the event | the case the rejected baseline fails, stated as a test rather than as an argument |
| `wfctl notify` on that same branch exits 1 | pins that this feature did not widen the gate it declined to reopen |
| `blocked` then `notify-action` for one action → released; the reverse order → held | FR-012, the most-recent-event rule |
| `wfctl blocked <action> --clear` with no grant releases the step | the path `notify-action` cannot reach |
| a `blocked` event holds a step whose own artifacts read `done` | the whole claim of the level-2 record |

The last is the one that fails if the hold is ever wired as a predicate
`implement` alone consults.

### A review question, not a test

Does `wfctl --help` read as though `notify` and `blocked` are alternatives? The
level-3 record names this as a landed consequence rather than a defect: the grant
is the reason there are two, and it is not visible from the verb list. If the help
text reads wrong, it owes the reader the grant.

## Design records

Read per `reading-design-records`, before this plan's structure was drafted.

```
Design records: 1 listed in design.md
  docs/architecture/design/364-the-block-report-is-its-own-verb.md
```

`design.md` also names the level-2 record
`docs/architecture/the-agent-reports-the-block-wfctl-never-saw.md` in prose,
outside the list, and says why: it binds as a level-2 record through `wfctl arch
context`, not as a structural choice for this feature. Both are `proposed` and
are expected to be accepted with this work.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Gates substituted from `AGENTS.md` rather than a constitution | The repo has no `.specify/memory/constitution.md`; the template requires the substitution be recorded rather than left implicit | Borrowing another project's constitution would state gates this repo never agreed to; deleting the section would leave the plan ungated |
| A second verb where a reader expects one flag | `notify`'s grant check covers both its paths deliberately (FR-011 of that feature, pinned in a comment at `cli.py:371`), and a host-blocked run may hold no grant — so the flag refuses exactly the report this feature collects | `--blocked` on `notify` makes that gate conditional, which reopens from underneath a decision recorded and tested. Argued in full at level 3 |
| A permanent published verb that can only report failure | Removing it later is a breaking change; wfctl's CLI is called from outside this repository | The asymmetry is the point: there is no spelling of `wfctl blocked` that reports a success, so *report a failure you alone witnessed, never a success* is enforced by shape rather than by prose |

## Assumptions carried into implementation

- **The agent survives the refusal.** The host returns an error and the run
  continues — observed three times on 2026-09-13, including on the attempt to test
  the claim. A host that kills the run leaves no witness and makes this feature
  unavailable rather than wrong. Re-probe on a second host before relying on it
  unattended.
- **`action` stays free text.** Falsified the first time a consumer wants to
  branch on the value rather than print it, which would want an enum in `notify`
  and `blocked` at once — a change to `notify` that FR-019 forbids.
- **A person who takes the blocked action will record it.** Nothing observes the
  action itself, so an unrecorded release leaves the step held.
