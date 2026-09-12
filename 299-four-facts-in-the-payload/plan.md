# Implementation Plan: four facts in the payload

**Branch**: `299-four-facts-in-the-payload` | **Date**: 2026-09-10 | **Spec**: `spec.md`
**Input**: Feature specification from `<spec-root>/299-four-facts-in-the-payload/spec.md`

## Summary

The pipeline payload gains four facts about the branch, carried beside the step
list and never inside it. Each is derived from its own owner — the spec dir, the
repository's declared definition of done, the status field of the architecture
records this branch touched, and the recorded human grant — and none is derived
from another or from any step state. `wfctl status` renders them as a block
between the step table and the `next:` line; `--json` carries the same four as
structured data.

The two decisions this rests on are recorded and committed on this branch:
`docs/architecture/readiness-is-not-a-step-state.md` (level 2, ownership) and
`docs/architecture/design/299-facts-render-as-a-block.md` (level 3, where a
reader meets them).

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer`, `rich`. No new runtime dependency; every
source this feature reads already has a reader in the tree — `_verify`,
`_arch.load_records`, `_paths.records_on_this_branch`, `_session.resolved_notify`.
**Storage**: files. The spec dir, `wfctl.json`, the verification record in the
XDG state dir, architecture records under the arch root, and `events.jsonl`.
**Testing**: `uv run pytest -q`; console assertions pin `NO_COLOR`. The pinned
payload snapshot (`tests/pipeline_payload_snapshot.json`) must need no
regeneration — it covers `_infer_steps`, and these facts are not per-step.
**Target Platform**: developer machines and CI, wherever `wfctl` runs.
**Project Type**: single project — a CLI with a library core.
**Performance Goals**: no new network call anywhere. The measurement the review
panel took, which this section originally deferred and budgeted wrongly at "two
local git invocations": `build_report` went from 10 to 19 git subprocesses before
the panel's fixes. Hoisting `verification_block` onto `Evidence` removes the
duplicate git and record reads it had reintroduced — the seam `build_report`'s own
comment exists to hold. What remains is the branch's record set and the trunk
question, both local. `wfctl next` is **not** among the callers that pay it: it
calls `_infer_steps` directly, which this section previously got wrong.
**Constraints**: `pipeline-state-is-one-payload` — one inference, and no view
computes a fact of its own. `blocks(verdict, source)` is not to be touched
(FR-014). No new step state (FR-008). ruff rule set stays `E4,E7,E9,F`; mypy runs
with `disallow_untyped_defs` and not `strict`. Minimal-complexity bias.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository ships no `.specify/memory/constitution.md`. The three
project-independent gates below are the template's own and are kept; the
project-specific gates are substituted from this repository's accepted records
and its `AGENTS.md`, and the substitution is recorded in Complexity Tracking as
the template requires.

- [x] Validation plan exists: the project's definition of done is declared in
      `wfctl.json` and named in the spec's Validation Strategy — `pytest`,
      `ruff`, `mypy`, then `wfctl doctor` — plus a test that builds both
      situations #299 names and asserts the console output differs.
- [x] Complexity is justified: the feature adds one named type and one list
      field. The simpler path — widening `implement`'s reason string — is the
      **Direct baseline** in the level-2 record, and the reason it is
      insufficient is written there: it answers on one row, composed from three
      sources that step does not read, and not at all for a branch held earlier.
- [x] Ownership is stated: four owners, one question each, in
      `docs/architecture/readiness-is-not-a-step-state.md` § Owns truth, with
      why the other side cannot compute each.
- [x] One payload, no second inference path (`pipeline-state-is-one-payload`):
      the facts are built in `build_report` and both views render them. The
      console composes no detail string of its own.
- [x] A rule is expressed as a check where a violation is visible in an artifact
      the work already produces (`a-rule-is-expressed-as-a-check`): FR-003's "no
      fact derived from a step state" is visible in the payload — a test builds
      two branches whose step states are identical and whose facts differ.
- [x] Knowledge placement (`knowledge-placement`): the derivations sit beside the
      predicates that already read three of the four sources; the payload shape
      sits beside `PipelineReport`; the glyphs sit in `cli`. Facts about one file
      stay in that file.

**Post-Phase 1 re-check**: unchanged. Phase 1 added no abstraction beyond the
`Fact` type the data model names, and moved one computation — the trunk
correction to the notify grant — out of the console and into the payload, which
tightens the first gate rather than loosening it.

## Project Structure

### Documentation (this feature)

```text
<spec-root>/299-four-facts-in-the-payload/
├── design.md            # /speckit.brainstorm output — levels 1 and 3
├── spec.md              # /speckit.specify output, clarified
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── facts-payload.md # Phase 1 — the console block and the JSON shape
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit.tasks output — not created here
```

The two records are **not** here. They are committed in the working tree, at
`docs/architecture/readiness-is-not-a-step-state.md` and
`docs/architecture/design/299-facts-render-as-a-block.md`, because `specs/` is
gitignored and resolves outside the tree — a reviewer reading the PR never opens
this directory.

### Source Code (repository root)

```text
wfctl/
├── _predicates.py    # + FactValue, Fact, the four derivations, facts()
├── _pipeline.py      # + PipelineReport.facts; build_report fills it
├── _paths.py         # unchanged — records_on_this_branch already answers
├── _arch.py          # unchanged — load_records already carries status
├── _session.py       # unchanged — resolved_notify already reads the grant
└── cli.py            # + _FACT_GLYPH, the console block, "facts" in --json

tests/
├── test_four_facts.py            # new — derivations, values, the two situations
├── test_pipeline_state_names.py  # touched — PipelineReport gains a field
└── pipeline_payload_snapshot.json  # untouched, and that is an assertion
```

**Structure Decision**: single project, the layout already in the repository. The
derivations go in `wfctl/_predicates.py` beside `verification_block` and
`design_block`, which are already public and already read three of the four
sources; that module's own docstring names #299 as one of the four issues it was
split out to serve. The payload field goes on `PipelineReport` in
`wfctl/_pipeline.py`. The glyph table goes in `wfctl/cli.py` beside
`_STATE_GLYPH`. This is the same three-way split `Reading` / `_PipelineStep` /
`_STATE_GLYPH` already uses, and it is why no new module is introduced.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from records and `AGENTS.md` | The repository ships no `.specify/memory/constitution.md`, and the template requires the substitution be recorded rather than left implicit | Borrowing another project's constitution would state gates this repository never agreed to; leaving the section with only the three generic gates would drop the four constraints that actually bind this change |
| A second glyph table in `cli` | The four step states and the three fact values are different closed sets, and the console is the only place either is drawn | Sharing `_STATE_GLYPH` would let a fact render as `▶` — a state it cannot hold — and would assert the two vocabularies are one, which the clarification pass decided they are not |
| The trunk correction moves from `status_cmd` into `build_report` | Fact 4 is part of the payload, and its answer includes the trunk case; computing it in the console would be a view deciding a fact | Leaving the correction in `status_cmd` and computing it a second time for the fact gives two paths to one answer, which is exactly what `pipeline-state-is-one-payload` forbids |
