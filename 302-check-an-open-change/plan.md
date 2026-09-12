# Implementation Plan: check an open change

**Branch**: `302-check-an-open-change` | **Date**: 2026-09-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from this feature directory's `spec.md`

## Summary

`wfctl change check <id>` reads an open change's fields and the branch's issue
fields through the tracker, and reports the fields that carry an expectation and
are unset. Expectation comes from two places and nowhere else: the repository's
committed `change_check` list in `wfctl.json`, and whatever the issue itself
carries.

The technical approach follows the split `check-body` already uses. A pure module
holds the comparison and knows nothing about git, subprocesses or trackers; the
tracker module grows a capture helper generalising the one #301 added; and the
command in `cli.py` composes the three, which is where the state lives.

Not in this change: #306, found during this feature's design pass, goes to its own
branch off `main`. `speckit-delivery-plan` holds that one PR closes exactly one
issue, and the two share no code, so nothing is bought by pairing them.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer`, `rich`. No new runtime dependency — the JSON
payload is `json.loads`, the tracker call is `subprocess.run`, both already used
in `wfctl/_tracker.py`.
**Storage**: None. `wfctl.json` is read, never written. No state is persisted by
this feature; every value is re-derived per invocation, per
`session-state-is-re-derived`.
**Testing**: `uv run pytest -q`, with `NO_COLOR` pinned by `conftest.py` for
anything asserting on console output. Comparison states are unit-tested by handing
the pure function a payload directly, so no test needs a tracker. Contract
validation goes through `wfctl tracker-check`.
**Target Platform**: developer machines and CI, wherever `wfctl` is installed.
**Project Type**: single project — a CLI.
**Performance Goals**: each tracker read bounded at 15 seconds (FR-016). No other
target; the command reads two records and compares string sets.
**Constraints**: no tracker-specific field name may appear in wfctl's own source
(FR-004, SC-004). ruff limited to `E4`, `E7`, `E9`, `F` — do not widen it here
(#14). mypy runs with `disallow_untyped_defs`; annotate every new function.
**Scale/Scope**: one change and one issue per invocation.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. The gates below are
substituted from its accepted architecture records and `AGENTS.md`; the
substitution is recorded in Complexity Tracking.

- [x] **Validation plan exists** — `spec.md`'s Validation Strategy names the four
      definition-of-done commands, the unit coverage per reachable state, the
      contract validation, and the live exercise no unit test substitutes for.
- [x] **Complexity is justified** — one new module, one new tracker verb, one new
      config key, one new command verb. The simpler path (shell to `gh` from
      `cli.py`) is rejected in a committed record with the reason.
- [x] **Ownership is stated** — `docs/architecture/the-repo-names-the-fields-a-
      change-must-carry.md` names the owning side for every value this feature
      introduces, and why the other side cannot compute it.
- [x] **A rule ships as a check when its violation is visible in an artifact the
      work produces** (`a-rule-is-expressed-as-a-check`) — this feature is that
      record applied to an open change.
- [x] **Source is committed package data; dotted directories are generated**
      (`layer-model`) — the skill edit lands in `wfctl/agents/skills/`, never in
      `.agents/`.
- [x] **wfctl runs the verification, not the agent** (`wfctl-runs-the-
      verification`) — untouched. This check judges a change's attributes and
      records no verdict about the branch.

Re-check after Phase 1: unchanged. Phase 1 added no boundary the level-2 record
does not already draw.

## Project Structure

### Documentation (this feature)

```text
specs/302-check-an-open-change/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── fields-verb.md
│   └── change-check-config.md
├── design.md            # From /speckit.brainstorm
├── spec.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
wfctl/
├── _change.py       # NEW — the comparison, and the wfctl.json read for its key
├── _tracker.py      # read_fields(), generalising read_issue_labels; ALLOWED
│                    #   and ALLOWED_CHANGES gain "fields"
├── cli.py           # `change check` composes the three
└── agents/
    ├── skills/opening-a-change/SKILL.md    # Step 6 invokes the check
    ├── skills/scaffold-tracker/SKILL.md    # the verb table gains `fields`
    └── configs/github/... trackers/github.json  # declares the fields verbs

tests/
├── test_change_check.py     # NEW — the comparison, one test per reachable state
├── test_change_cli.py       # NEW — rendering, exit codes, every degrade path
├── test_change_config.py    # NEW — wfctl.json reading and its malformed shapes
└── test_tracker.py          # extended — the verb table, and read_fields
```

`test_tracker.py` is extended rather than duplicated: it already covers
`change list`/`view`, the verb table and its rejections. New files are created
only for the new module and the new command.

**Structure Decision**: single project, existing layout, no new directories. The
new module sits beside `_body.py` and `_shape.py`, which are the two other pure
modules a check command composes. `wfctl/agents/` is source; `.agents/` is
generated and is never edited (`layer-model`).

## Phase 0 — Research

See [research.md](./research.md). No `NEEDS CLARIFICATION` entered this plan:
`/speckit.clarify` resolved the two open questions (read bound, partial read) and
the design pass resolved the five shape questions issue #302 raised.

## Phase 1 — Design artifacts

- [data-model.md](./data-model.md) — the field payload, the expectation, the
  finding, and the three-way marker set.
- [contracts/fields-verb.md](./contracts/fields-verb.md) — what a tracker's
  `fields` verb must return, and what wfctl does with a payload that breaks it.
- [contracts/change-check-config.md](./contracts/change-check-config.md) — the
  `change_check` key in `wfctl.json`.
- [quickstart.md](./quickstart.md) — configuring and running the check.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from architecture records rather than read from `.specify/memory/constitution.md` | The repository has no constitution file; its binding decisions live in `docs/architecture/` and are projected by `wfctl arch context` | Borrowing another project's constitution would make the gate false, and leaving the section empty would make it decorative — the template names both outcomes |
| A second reader of `wfctl.json` (`_change.py` alongside `_verify.py`) | Each reader owns one key and its schema; `_verify.py`'s stated subject is the definition of done, and `change_check` is not that | Putting `change_check` into `_verify.load_config` makes that module's first line false. Sharing `_verify.CONFIG_PATH` keeps the *path* defined once, which is the part that would drift |
