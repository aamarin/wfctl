# Implementation Plan: plan-walkthrough

**Branch**: `500-plan-defense` | **Date**: 2026-09-27 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/Users/andremarin/Development/wfctl-specs/500-plan-defense/spec.md`

## Summary

wfctl ships a `plan-walkthrough` skill and a `/plan-walkthrough` command. A person runs
it to find out, in private, whether they can explain their own plan or change.
The answers go to the branch's state directory, and the feature directory gets
a marker with no answers in it.

A repository places the pass itself in `wfctl.json` `steps`. The one change to
wfctl's core is a `needs_person` flag on a declared pass: while auto-approve is
on and the marker is absent, wfctl reads the pass as `skipped` with a reason,
and writes nothing. The skill refuses to run while auto-approve is on, whoever
invoked it.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)  
**Primary Dependencies**: `typer`, `rich`; no new dependency  
**Storage**: files only; the answers file in `$(wfctl state-dir)/walkthrough/`, the
marker in the feature directory, the declaration in `wfctl.json`  
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`,
`uv run mypy wfctl/`, `uv run wfctl check config`, `uv run wfctl doctor`, and
the manual runs in `quickstart.md`  
**Target Platform**: macOS and Linux shells, under any agent host wfctl
installs into  
**Project Type**: CLI with a shipped skills tree  
**Performance Goals**: none new; `wfctl status` reads the approval mode once
per report, as it already does  
**Constraints**: the answers never enter the feature directory or a committed
file (SC-001); the skip writes nothing (SC-003); minimal-complexity bias  
**Scale/Scope**: one new field on a declared pass, one new payload key, one
skill with five references, one command wrapper, one docs section, and this
repository's own declaration

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. The gates below come
from `AGENTS.md` and the in-force architecture records, and the substitution is
recorded in Complexity Tracking.

- [x] Validation plan exists: the three definition-of-done commands, new tests
      in `tests/test_declared.py`, `tests/test_cli_status.py`, and
      `tests/test_status_contract.py` plus a new pass-reading test,
      `wfctl check config` on this repository's `wfctl.json`,
      `install-skills` and `doctor` through `uv run`, and the manual runs in
      `quickstart.md` for the skill's behavior.
- [x] Complexity is justified: one boolean field and one branch in
      `_pass_states`. The simpler path, a claim the skill writes, is rejected
      in `autonomous-agent-skips-human-checks` for committing a file per run that
      outlives the mode.
- [x] Ownership is stated: the repository owns whether a pass needs a person
      (the declaration), wfctl owns whether it is skipped right now (read from
      the stored approval mode), and the person owns who sees the answers
      (`plan-walkthrough-is-private`). See `data-model.md`.
- [x] `layer-model`: the skill lives under `wfctl/agents/skills/plan-walkthrough/`
      and the wrapper under `wfctl/agents/commands/`. Nothing under a dotted
      directory is edited by hand, and `agents/openai.yaml` is dropped.
- [x] `pipeline-state-is-one-payload`: the four state names do not change; the
      new key is additive and the contract version bumps a minor.
- [x] `session-state-is-re-derived`: the skip is computed on every read and
      never written.
- [x] `vendor-upstream-skills`: the skill is wfctl's own. Its `source-map.md`
      cites ideas and copies no upstream text, and the record gains a line
      saying so (FR-019).
- [x] `a-rule-is-expressed-as-a-check`: the two `needs_person` rules are
      `check config` findings. "The answers never enter the feature directory"
      is visible in an artifact, so it is covered by the manual check in
      `quickstart.md`; the skill's behavior has no automated test, as
      `AGENTS.md` says of every skill.

Re-check after Phase 1: all gates still hold. The design added no field beyond
`needs_person` and no state beyond the four.

## Project Structure

### Documentation (this feature)

```text
/Users/andremarin/Development/wfctl-specs/500-plan-defense/
├── spec.md
├── design.md
├── plan.md                 # this file
├── research.md             # R1 - R9
├── data-model.md           # declaration, pass reading, payload, answers, marker
├── quickstart.md           # manual runs for Stories 1 - 5
├── contracts/
│   ├── declaration-and-payload.md
│   └── plan-walkthrough-command.md
├── checklists/requirements.md
└── tasks.md                # /speckit.tasks, not created here
```

### Source Code (repository root)

```text
wfctl/
├── _pipeline.py            # SubStep.needs_person, _PipelineSubStep.needs_person,
│                           #   _pass_states row 5, auto_approve threaded from
│                           #   build_report, payload key
├── _declared.py            # parse needs_person, two check config findings
├── contracts/
│   └── status-payload.json # new path, version 1.1
└── agents/
    ├── commands/
    │   └── plan-walkthrough.md # new wrapper
    └── skills/
        └── plan-walkthrough/   # new, from docs/plan-defense/ in the main checkout
            ├── SKILL.md
            └── references/
                ├── artifact-contract.md     # split into answers file and marker
                ├── interrogation-lenses.md  # lenses 2, 3, 4, 7 pruned; 11 leads
                ├── question-quality.md
                ├── examples.md
                └── source-map.md

docs/
├── reference.md            # new section on declaring your own passes
└── architecture/
    ├── vendor-upstream-skills.md          # plan-walkthrough is wfctl's own
    └── (the three #500 records were rewritten and renamed in f456a2c and 634dccb)

wfctl.json                  # declares plan.plan-walkthrough with needs_person

tests/
├── test_declared.py        # needs_person parsing, both findings
├── test_cli_status.py      # check config output for both findings
├── test_status_contract.py # fixture covering needs_person
├── test_pipeline_needs_person.py  # the pass reading rows 4 - 6 in both modes
└── test_plan_walkthrough_skill.py # the skill and command ship, with no agents/ directory
```

**Structure Decision**: The existing single-project layout. Core changes stay
in `_pipeline.py` and `_declared.py`, where declared passes are already parsed
and read. The skill and wrapper go where every shipped skill goes, and ship
through `graft wfctl/agents` in `MANIFEST.in` with no packaging change.

## Notes carried to tasks

- Build order: the `needs_person` field and reading first, with tests; then
  the payload key and contract bump; then the skill and wrapper; then the
  docs section, the declaration in `wfctl.json`, and the provenance line. The
  declaration fails `check config` until the wrapper is installed.
- The skill is copied from `/Users/andremarin/Development/wfctl/docs/plan-defense/`
  in the main checkout. Read it there; do not edit or run anything in that
  worktree.
- `speckit-plan`'s setup script rewrites `plan.md` from the template on every
  run, so a second `/speckit.plan` on this branch loses this file.
- The spec was corrected during planning: an absent marker reads
  `in_progress`, the outstanding pass, not `pending`, because
  `build_file_exists_reader` returns `in_progress` (`_evidence.py:245`). The
  level-2 record was corrected in f456a2c.
- `design.md` still says the README carries the snippet and that the skill
  refuses only when orchestrate invokes it. The spec's Clarifications supersede
  both.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| No constitution; gates taken from `AGENTS.md` and the in-force records | This repository has no `.specify/memory/constitution.md` | Leaving the gates empty would pass every plan, and borrowing another project's gates would be false |
