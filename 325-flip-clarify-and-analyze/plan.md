# Implementation Plan: flip clarify and analyze

**Branch**: `325-flip-clarify-and-analyze` | **Date**: 2026-09-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `spec.md` in this directory

## Summary

Move `clarify` and `analyze` from `_REVIEW_REQUIRED` to `_AUTOMATIC` in `_STEPS`,
and cover the change with assertions in the two test modules that already own the
table and the function reading it.

The technical approach is the absence of one. `auto` is computed at a single site
and every view derives from it, so the feature is two values and no new mechanism.
The work that made this defensible landed elsewhere: both steps commit a scan file
a reviewer can read (#307/#320), `clarify` records the options it rejected
(#286/#322), and the payload can say which of four facts a step answered (#299).

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: none beyond the existing `typer` + `rich`; this feature
adds none
**Storage**: N/A — the change is a constant in a module-level table
**Testing**: `uv run pytest -q`; assertions added to `tests/test_pipeline_sections.py`
(the table) and `tests/test_pipeline_commands.py` (the reported flag per state)
**Target Platform**: CLI, wherever wfctl is installed
**Project Type**: single project — a CLI with a package under `wfctl/`
**Performance Goals**: N/A — a dict lookup on a table of eight rows
**Constraints**: `pipeline-state-is-one-payload` forbids a second site computing
`auto`; minimal-complexity bias, which here means the change adds no branch
**Scale/Scope**: two table values, one renamed test, three new assertions

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository ships no `.specify/memory/constitution.md`. The gates below are
the two project-independent ones the template carries, plus three drawn from this
repository's own accepted architecture records and `AGENTS.md`. The substitution
is recorded in Complexity Tracking, as the template requires.

- [x] **Validation plan exists**: the four commands in `AGENTS.md` are named in
      the spec's Validation Strategy, together with the three story-specific
      assertions and what each covers.
- [x] **Complexity is justified**: no abstraction, infrastructure or dependency is
      added. The feature is two values in a table that already exists, and the one
      alternative that would have added a branch is ruled out by FR-006.
- [x] **Ownership is stated**: the feature introduces no state and no derived
      value. `_STEPS` owns the continuation value before and after;
      `next_step_content` remains its only reader. Declared as an absence with
      `wfctl arch none`, whose reason is on the branch.
- [x] **`pipeline-state-is-one-payload`**: no view computes a fact of its own. The
      change is upstream of every view, in the table the one inference reads.
- [x] **`a-rule-is-expressed-as-a-check`**: the rule this change asserts — that
      these two steps may run unattended — is expressed as the table value a test
      pins, not as prose. FR-008 keeps that tripwire in one place.

## Project Structure

### Documentation (this feature)

```text
specs/325-flip-clarify-and-analyze/
├── plan.md              # This file
├── spec.md              # Written by /speckit.specify, clarified in place
├── design.md            # Written before speckit ran
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # /speckit.tasks output — not created here
```

No `research.md`, `data-model.md`, `quickstart.md` or `contracts/`. Phase 0 has
nothing to research: every factual claim the design rests on was checked against
the code before `design.md` was written, and its *assumed* column is empty. Phase
1 has no data model and no contract, because the feature introduces no entity and
no interface — the one it touches is an internal table whose shape is unchanged.
Writing four files that say "not applicable" would make a reviewer read four files
to learn nothing.

### Source Code (repository root)

```text
wfctl/
└── _pipeline.py                    # _STEPS: two values change

tests/
├── test_pipeline_sections.py       # the table's own test — renamed, dict updated
└── test_pipeline_commands.py       # the reported flag, per reachable state
```

**Structure Decision**: The existing layout, unchanged. `wfctl/_pipeline.py` holds
the step table, the walk over it, and the one payload every view renders;
`_predicates.py` holds what each step reads and is not touched. The two test
modules are named for what they test, which is why the change's assertions split
across them rather than gathering in a new file — settled in the spec's
Clarifications.

## Complexity Tracking

> Filled because the Constitution Check substituted gates from a source other than
> a constitution, which the template requires be recorded here.

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution Check gates are not derived from `.specify/memory/constitution.md` | The repository ships no constitution file | Leaving the section with the template's two generic gates would make the check decorative. The three added gates are this repository's own accepted records and `AGENTS.md` conventions, which is the source the template names as the substitute |
| Two test modules touched rather than one | The table and the function that reads it have separate existing test modules, each named for its subject | Gathering both in one module puts `next_step_content` assertions away from the other tests of `next_step_content`; a new module puts that function's coverage in three places. Recorded in the spec's Clarifications |

## Phase 0 — Research

None required. Every claim the design rests on was verified against the source
before the design document was written; the *assumed* column of its level-3 split
is empty. The five checked claims are listed there with how each was checked.

## Phase 1 — Design

Complete before speckit ran. `design.md` carries the three levels in their
rendered forms — literal strings per reachable state for level 1, a boundary
sketch for level 2, the checked/assumed split for level 3 — and the level-2 gate
was answered as a declared absence rather than a record.

No entity is introduced, so there is no `data-model.md`. No interface is
introduced or changed, so there is no `contracts/`. The step table's shape,
`Step(command, continuation, predicate)`, is untouched.

## Phase 2 — Implementation approach

One commit, because the evidence that earns each flip is already on `main` in the
scan files rather than in this diff. Splitting would show a reviewer two halves of
one judgment and no additional evidence.

Order within it:

1. Change the two table values.
2. Rename the pinning test and update its dict and docstring, so the tripwire
   fails loudly if step 1 were ever partially applied.
3. Add the per-state assertions for the reported flag.
4. Run the four commands.

Step 2 before step 3 deliberately: the pinning test is what proves the table
changed, and the per-state assertions prove the change reaches a reader. A run
where 3 passes and 2 was forgotten would report the feature working with its
tripwire silently stale.
