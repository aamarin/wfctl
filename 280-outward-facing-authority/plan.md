# Implementation Plan: notify authority

**Branch**: `280-outward-facing-authority` | **Date**: 2026-09-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/280-outward-facing-authority/spec.md`

## Summary

A per-feature grant saying whether a run may take actions that notify people
outside the repo — push, comment, open an issue, add a label. Granted in advance
by a person, from either an issue label or a local command; declined or narrowed
by the agent, never widened by it. Refused by default, and the refusal says so
out loud rather than staying silent.

Stored as its own file in the per-branch state dir, resolved once at run start
against the label, and recorded to the event log both when granted and each time
it is used.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer`, `rich`. No new runtime dependency — the
tracker read goes through the existing `wfctl issue view` verb and `gh`.
**Storage**: `notify.json` in the XDG state dir, per branch. JSON, one writer,
one reader. Not in the repo; `specs/` and the state dir both sit outside the
working tree.
**Testing**: `uv run pytest -q`; console assertions pin `NO_COLOR` per
`conftest.py`. New coverage is unit-level around the resolver plus console
output.
**Target Platform**: local developer machines, macOS and Linux, through the CLI.
**Project Type**: single Python package, CLI.
**Performance Goals**: one tracker round-trip per run, not per action (FR-014).
No other budget applies.
**Constraints**: ruff limited to `E4`, `E7`, `E9`, `F` — do not widen as a
drive-by (#14). mypy with `disallow_untyped_defs`, not `--strict`; annotate new
functions. Minimal-complexity bias.
**Scale/Scope**: one grant per feature branch. Two surfaces. Four verdicts.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

**This repo has no `.specify/memory/constitution.md`.** The gates below are
substituted from its own documented conventions — `AGENTS.md`, the accepted
records that `wfctl arch context` projects, and `pyproject.toml`. The
substitution is recorded in Complexity Tracking, as the template requires.

- [x] **Validation plan exists.** `uv run pytest -q`, `uv run ruff check
      wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl doctor` — AGENTS.md's
      stated bar, and what CI runs. Plus `uv run wfctl verify`, and for any
      change under `wfctl/agents/`, `install-skills` and a manual exercise
      including the ungranted path.
- [x] **Complexity is justified.** One new file, one new reader, one new writer,
      two new event kinds, one new flag. The second file over a second key on
      `mode.json` is argued in `research.md` from what the code says about
      itself. No new dependency, no new abstraction.
- [x] **Ownership is stated.** Four pieces of state, each with the side that
      computes it and why the other cannot — `research.md`, *Ownership*. Summary:
      the agent cannot own it because an actor authorizing its own action makes
      the claim the authorization exists to check; the harness cannot, because
      permission rules match command strings and cannot express "notifies
      someone."

**Re-checked after Phase 1**: still passing. Phase 1 added no abstraction and no
dependency; the contract is three functions and a NamedTuple.

## Project Structure

### Documentation (this feature)

```text
specs/280-outward-facing-authority/
├── plan.md              # This file
├── research.md          # Phase 0 — the storage decision
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── notify-grant.md  # Phase 1
├── design.md            # from brainstorm (levels 1 and 3)
├── spec.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit.tasks — not created here
```

### Source Code (repository root)

```text
wfctl/
├── _session.py          # notify_grant(), grant_notify(), record_notify_action()
│                        #   beside auto_approve() / grant_auto_approve()
├── _pipeline.py         # build_report carries notify + notify_source
├── cli.py               # --allow-notify/--deny-notify on `start`
│                        #   status console lines, --json keys
└── agents/skills/       # the skills that gate on the grant and report use

tests/
├── test_session.py      # resolver: four verdicts, three unreadable shapes
├── test_cli_status.py   # console line in every state, NO_COLOR pinned
└── test_hook_*.py       # unchanged
```

**Structure Decision**: single package, existing modules. The grant is a session
concern and `_session.py` already owns the only other per-feature setting, so it
takes this one rather than a new module. `docs/architecture/` gains nothing —
the decision record is already committed at `61f8979`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from repo conventions | No `.specify/memory/constitution.md` exists; the template requires the substitution be recorded rather than the gates invented or borrowed | Borrowing another project's constitution would make the gate false; skipping it would make it decorative |
| A second state file rather than a second key on `mode.json` | `mode.json` documents one-writer-one-reader as the property it copies from `verify.json`; a second key forces read-merge-write and a decision about what a partially-corrupt file means | Argued at length in `research.md`. The second key saves ~12 lines and spends them on merge logic plus a new failure mode |
| Four verdicts where the spec's headline is a boolean | `unset`, `denied` and `unreadable` all resolve to refused but are different events — FR-015 exists because a failed read decides the whole run | A boolean cannot distinguish "nobody granted" from "the tracker was down", and filing the second as the first misreports a person's intent |

## Carried risk

The two notification assumptions — that tagging an issue notifies watchers and
that a board column move does not — remain unverified. Declined on 2026-09-08 as
accepted risk. Neither outcome changes who may grant, where it is stored, or any
contract in Phase 1, which is what made skipping affordable. `spec.md`
Assumptions records what rides on each.

## Also in this branch's PR

The `notify` rename reaches `wfctl-classes-the-action-not-the-command.md`, which
merged to `main` as PR #282 on 2026-09-07. It is a plain file on `main` now, not
another branch's open PR, and folds into this change rather than needing its own.
`wfctl/_pipeline.py` spends the old term in a comment near `_unkeyed_issues` and
moves with it.
