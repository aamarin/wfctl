# Implementation Plan: orchestrate loop bound

**Branch**: `332-orchestrate-loop-bound` · **Issue**: #332
**Spec**: `<FEATURE_DIR>/spec.md` · **Design**: `<FEATURE_DIR>/design.md`

## Summary

Give `speckit-orchestrate`'s loop a bound. `wfctl resume` already appends one
event per pass carrying the step and command; it gains a digest of the artifact
text the same inference already read. `build_report` reads the recent events back
and reports whether the last three passes on the current step share a digest.
`speckit-orchestrate` reads that verdict and stops instead of emitting
`EXECUTE_COMMAND`, naming the step and the evidence that did not move.

The structural choice — fingerprinting artifacts rather than the rendered step
line — is `docs/architecture/design/332-progress-is-measured-in-artifacts.md`.
The ownership choice — wfctl counting rather than the agent —
is `docs/architecture/wfctl-counts-the-passes.md`.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: none new. `hashlib` and `json` are stdlib; `typer` and
`rich` are already present and this feature adds no library.
**Storage**: the branch's `events.jsonl` in the XDG state dir, appended to as it
already is. No new file, no schema migration — a field is added to one event type
and older lines lacking it are read as carrying no digest.
**Testing**: `uv run --frozen --extra dev pytest -q`, plus
`ruff check wfctl/ tests/` and `mypy wfctl/`. Feature-specific: unit tests over
the pass-counting function, and an observed unattended run against a repeating
step.
**Target Platform**: developer machines and CI, wherever wfctl runs.
**Project Type**: CLI, single project.
**Performance Goals**: the digest is taken from text `Evidence` already holds, so
a report costs no additional file read. Reading back the event log is bounded by
scanning only the tail needed to find three passes.
**Constraints**: `wfctl/_pipeline.py` belongs to #325 for the duration of that
branch — see Complexity Tracking. Minimal-complexity bias.
**Scale/Scope**: one pipeline, eight steps, one event log per branch. Logs on
disk today run to tens of lines.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. The gates below are the
two project-independent ones plus this repo's own accepted architecture records,
substituted per the template's instruction; the substitution is recorded in
Complexity Tracking.

- [x] Validation plan exists: `pytest`, `ruff` and `mypy` as the repo's declared
      definition of done, plus the four feature-specific tests named in the spec's
      Validation Strategy, plus one watched unattended run.
- [x] Complexity is justified: one new module and one new event field. The
      simpler path — the agent counting in its own conversation — is insufficient
      for the reason `wfctl-counts-the-passes` records: it loses the tally exactly
      when a run is long enough to need one.
- [x] Ownership is stated: wfctl owns "has this run stopped making progress, and
      on which step?"; the agent cannot, because the count must outlive a cleared
      or compacted conversation and a session boundary.
- [x] `session-state-is-re-derived`: nothing is written to remember an attempt.
      The digest recorded is history — a past pass's evidence cannot be
      re-derived, because the artifacts have moved since — which is what that
      record reserves for a session file.
- [x] `pipeline-state-is-one-payload`: the verdict is a field on the one report
      `build_report` produces, not a second source of pipeline truth. Every view
      renders it from there.
- [x] `a-rule-is-expressed-as-a-check`: the violation is visible in an artifact
      the work already produces — the event log — so the rule ships as a computed
      check rather than as prose in a skill.
- [x] `vendor-upstream-skills`: `speckit-orchestrate` is wfctl's own skill, not
      spec-kit-derived, so editing its `SKILL.md` in place is correct and survives
      an upstream pull.

## Project Structure

### Documentation (this feature)

```
<FEATURE_DIR>/
├── design.md          written by /speckit.brainstorm
├── spec.md            written by /speckit.specify, clarified
├── plan.md            this file
├── data-model.md      Phase 1 — the shapes below
├── tasks.md           written by /speckit.tasks
└── checklists/
    └── requirements.md

docs/architecture/
├── wfctl-counts-the-passes.md                       level 2, proposed
├── design/332-progress-is-measured-in-artifacts.md  level 3, proposed
└── scans/332-clarify.md                             clarify's coverage
```

No `contracts/` directory: this feature crosses no network or process boundary,
so there is no wire format to fix. Its one contract is the event field, which
`data-model.md` carries.

### Source Code (repository root)

```
wfctl/
├── _stall.py          NEW — reads the event log, decides whether the last three
│                      passes on a step share a digest. All of the counting lives
│                      here, so the surface added to files owned elsewhere stays
│                      at a call and a field.
├── _pipeline.py       PipelineReport gains one field; build_report calls _stall
│                      once. See Complexity Tracking — this file is #325's.
├── cli.py             resume records the digest; status renders the verdict;
│                      the --json payload carries it.
└── agents/skills/speckit-orchestrate/SKILL.md
                       step 5 gains a branch: a stalled run stops and reports
                       instead of emitting EXECUTE_COMMAND.

tests/
└── test_stall.py      NEW — the counting function against real log shapes.
```

## Complexity Tracking

| What | Why the simpler path is insufficient |
| --- | --- |
| Gates substituted from `AGENTS.md` and the accepted records rather than a constitution | The repo ships no `.specify/memory/constitution.md`. The template instructs substituting the project's documented conventions and recording it here; gates borrowed from another project would be false. |
| A new module rather than a function inside `_pipeline.py` | `wfctl/_pipeline.py` is #325's for the duration of that branch, and this change cannot avoid it entirely: `pipeline-state-is-one-payload` requires the verdict to be a field on the one report, and that report is built there. Confining the logic to `_stall.py` reduces the edit in the contested file to an import, a call and a field — textually distant from the step-mode constants #325 changes. **This is a deviation from the branch's handoff, which said not to touch that file at all, and it is flagged for the reviewer rather than resolved silently.** |
| A digest rather than storing the artifact text | Storing the text would put a copy of the spec in the event log on every pass. The digest answers the only question asked of it — did this change — at fixed size. |
