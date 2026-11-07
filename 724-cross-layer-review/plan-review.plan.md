# Implementation Plan: Reviewers check that each layer accepts the same input

**Branch**: `724-cross-layer-review` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/724-cross-layer-review/spec.md`

## Summary

The `code-review` rubric gets two new passes after its six: an input trace, which follows each value from outside the program through every layer that checks or stores it, and a sibling-path check, which looks for every other place a fix should also apply. Step 5 adds a trail after the findings and a WARNING floor for a layer mismatch. The change is prose in one skill, plus the places that state the pass count and the one test that asserts it. No Python under `wfctl/` changes.

Design record: `docs/architecture/design/724-cross-layer-checks-in-rubric.md`, which chose two passes in the shared rubric over a review group or a different method per reviewer.

## Technical Context

**Language/Version**: Markdown skill files under `wfctl/agents/`, shipped as package data. Python 3.11+ only for the one test that changes.  
**Primary Dependencies**: None added.  
**Storage**: N/A  
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`. The behavior check is a reviewer run over PFMS `7cde6095..996f5e5c` with the saved experiment brief (quickstart.md).  
**Target Platform**: Any agent host that loads wfctl's installed skills.  
**Project Type**: CLI with a shipped skills tree.  
**Performance Goals**: N/A. A review gets longer by the length of the trail, and nothing measures review time today.  
**Constraints**: No edits to `_review*.py` (#725 runs beside this branch). The rubric carries no rule or example that only one repository has (FR-013). Minimal-complexity bias.  
**Scale/Scope**: One skill gains two passes. Three other files restate the pass count. One test asserts it.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repo has no `.specify/memory/constitution.md`. The gates below come from `AGENTS.md` and the in-force records instead, and Complexity Tracking records the substitution.

- [x] Validation plan exists: the three commands, `install-skills` then `doctor`, and the PFMS reviewer run in quickstart.md.
- [x] Complexity is justified: no abstraction, infrastructure, or dependency is added. Two passes join an existing list.
- [x] Ownership is stated: wfctl owns the rubric, as before. The level-2 answer for `design-method` is recorded with `wfctl arch none`.
- [x] `vendor-upstream-skills`: `code-review` is wfctl-owned and edited in place since #47, so an in-place edit is correct. `requesting-code-review` is derived from obra/superpowers, so its edit drops the count rather than changing it, as research.md R3's alternative allows.
- [x] `change-carries-release-note`: `changes/724.change.md`, since every code review now asks more of the reviewer.
- [x] `a-rule-is-expressed-as-a-check`: whether a reviewer ran the passes is visible in its report through the trail, which the coordinator and the PFMS run read. A mechanical check on report contents is out of scope, as research.md R4 explains.

## Project Structure

### Documentation (this feature)

```text
specs/724-cross-layer-review/
├── design.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── review-report.md
└── tasks.md             # written by /speckit.tasks
```

### Source Code (repository root)

```text
wfctl/agents/skills/code-review/SKILL.md             # passes 7 and 8, Step 5 trail and floor, description, red flags
wfctl/agents/commands/code-review.md                 # description lists eight lenses
wfctl/agents/skills/requesting-code-review/SKILL.md  # "the six-pass rubric" → "the rubric"
wfctl/agents/skills/fanning-out-code-review/SKILL.md # example row "six passes" → eight
tests/test_review_fanout_skill.py                    # pass-count assertion 6 → 8
changes/724.change.md                                # release note
```

**Structure Decision**: Edit in place. Every path above already exists, and none is added except the release note.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates taken from `AGENTS.md` and the in-force records | The repo has no constitution file | Leaving the gates out would make the check decorative |
