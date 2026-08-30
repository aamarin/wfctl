# Implementation Plan: reply over-explains

**Branch**: `102-reply-over-explains` | **Date**: 2026-08-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `<spec root>/102-reply-over-explains/spec.md`

## Summary

Add two governors to `conversation-response-shape` that it currently lacks —
**register** (whether material is worth saying) and **subject** (whether the
reader can tell what the reply is about) — plus a **form-selection** step that
maps what the material is onto which drawing to use. Resolve the four passages
that contradict them, abstract the wfctl-specific examples out (#80), and make
the repo's pull request template point at the skill instead of restating its
rule (FR-007).

Technically this is a prose edit to one shipped skill file and one repo
template. The engineering risk is not in the diff; it is that the change grows a
388-line file whose documented failure mode is that its rules get lost partway
through a session.

## Technical Context

**Language/Version**: Markdown (skill content); Python 3.11+ for the surrounding suite
**Primary Dependencies**: none added. `typer` + `rich` unchanged; no runtime code touched
**Storage**: N/A
**Testing**: `uv run pytest -q`; `tests/test_skill_cross_references.py` is the file covering this skill
**Target Platform**: any repo that runs `wfctl install-skills` — the skill is base-layer, installed everywhere
**Project Type**: CLI + shipped skill bundle (package data under `wfctl/agents/`)
**Performance Goals**: N/A. The measurable targets are reply-quality criteria SC-001 … SC-012, not machine performance
**Constraints**: net file growth is the binding one — see Complexity Tracking. Also: source edits go in `wfctl/agents/`, never `.agents/` (`layer-model`); every rule has exactly one home (`knowledge-placement`); `i-have-adhd` is vendored and must not be edited or absorbed (`vendor-upstream-skills`)
**Scale/Scope**: two files changed, one test file possibly extended. No new skill, no frontmatter key, no CLI change (FR-009)

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repo has no `.specify/memory/constitution.md`. Gates below are substituted
from its own documented conventions — `CLAUDE.md`'s definition of done and the
accepted records in `docs/architecture/`. The substitution is recorded in
Complexity Tracking, per the template.

- [x] **Validation plan exists.** `uv run pytest -q`, `uv run ruff check wfctl/ tests/`,
      `uv run mypy wfctl/`, then `wfctl doctor`. Plus the two checks the suite
      cannot make: `wfctl install-skills` and exercising the changed skill
      (`CLAUDE.md`: "A change to anything under `wfctl/agents/` is not verified by
      the test suite alone"), and the reply-quality benchmark for SC-001/009/011.
- [x] **Complexity is justified.** No abstraction, infrastructure or dependency is
      added. The one thing that grows is the skill's own length, and it is
      budgeted below rather than left implicit.
- [x] **Ownership is stated.** The skill owns the draw test and the form-selection
      table; the pull request template and (later, under #556)
      `speckit-delivery-plan` and `finishing-a-development-branch` state only the
      obligation and point at the skill (FR-007). `i-have-adhd` keeps ownership of
      brevity and next-action; this skill layers over it and copies nothing
      (`vendor-upstream-skills` names this skill as that record's worked example).

**Post-Phase-1 re-check**: still passing. Phase 1 added no new surface — the
artifacts describe the rule set that already existed in the spec.

## Project Structure

### Documentation (this feature)

```text
<spec root>/102-reply-over-explains/
├── design.md            # brainstorm output, approved
├── spec.md              # /speckit.specify output
├── plan.md              # this file
├── research.md          # Phase 0
├── data-model.md        # Phase 1 — the rule inventory
├── quickstart.md        # Phase 1 — how to verify
├── contracts/
│   └── skill-structure.md   # Phase 1 — the skill's structural contract
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit.tasks, not created here
```

### Source Code (repository root)

```text
wfctl/agents/skills/conversation-response-shape/SKILL.md   # the change (388 lines today)
wfctl/agents/commands/conversation-response-shape.md       # wrapper — read, likely untouched
.github/pull_request_template.md                           # FR-007 pointer
tests/test_skill_cross_references.py                       # FR-010 — must stay green
tests/test_response_shape_invariants.py                    # FR-012 — new
```

**Three files change, one is added.** The new test file is the answer to "is the
contract enforced or decorative": `contracts/skill-structure.md` marks seven
invariants assertable, and today **none** of them is asserted anywhere — the two
existing skill test files cover cross-references and the ADR record template
only. Checked, not assumed.

| Invariant | Enforced by | Home |
| --- | --- | --- |
| C-3 rule numbers 1-3 don't move | new test | #102 |
| C-5 selection table has exactly one home | new test | #102 |
| C-6 no wfctl inside examples | new test | #102 — closes #80 verifiably |
| C-7 line ceiling | new test | #102 |
| C-1 frontmatter key set | — | **#60**, deliberately not here |
| C-2 precedence list contiguous | — | **#60**, deliberately not here |
| C-4 no verbatim `i-have-adhd` text | — | weak assertion, not worth the test |

C-5 is the load-bearing one. It is the invariant #556 will stress by adding two
more pointers to a rule this feature makes single-owner, and nothing today would
catch a restatement.

**Structure Decision**: no new directories. Edits land in the committed source
tree under `wfctl/agents/`. The installed copies at
`.agents/skills/conversation-response-shape/` and any `.claude/` mirror are
gitignored output and are never edited — `layer-model` records that editing them
is a silent failure that passes the suite and ships nothing.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Gates substituted from `CLAUDE.md` + `docs/architecture/` rather than a constitution | The repo has no `.specify/memory/constitution.md`, and the plan template requires the substitution be recorded rather than silently skipped | Borrowing another project's constitution would produce gates with no source, which the template calls decorative or false |
| The skill grows — net **+50 to +60 lines** on a 388-line file (~14%) | Two new rules, a draw test, a form-selection table and a two-genre template cannot be stated in zero lines | Stating them shorter loses the worked examples, and this skill's own evidence is that a rule without an example does not fire |

**The growth is the risk this plan tracks.** The skill's documented failure mode
(design.md, *"The rules decay within a session"*) is that its rules get lost
partway through a long session. This change adds rule surface to the file whose
rules already decay, and nothing here makes decay better — #85 owns that.

Budget and lever:

```
today                        388 lines
  − deletions (conflicts 1-3)  ~8
  + register rule              ~6
  + subject rule + table      ~15
  + draw test                  ~5
  + form-selection table      ~10
  + two-genre template        ~25
  ────────────────────────────────
target                       ~440 lines   (+13%)
ceiling                       450 lines
```

If the edit exceeds the ceiling, the named lever is **"Render the literal output,
not a description of it"** (SKILL.md:202-214, ~13 lines). design.md's control
found it fires at the same rate when absent — it earns nothing measurable — and
declined to cut it only because removing a working rule on one run of evidence
was the worse bet. Under budget pressure that calculus flips. Do not invent a
different cut; this one is already argued.

## Phase 0 — Research

Output: `research.md`. Three unknowns carried from the spec, all resolved there:

1. How SC-001 / SC-009 / SC-011 get measured, given the original experiment's
   replies were in an ephemeral scratchpad.
2. Where each new rule goes in the file, and what the resulting section order is.
3. Whether the two skills #556 will touch need anything from this feature beyond
   FR-007's pointer rule.

## Phase 1 — Design

Outputs: `data-model.md` (the rule inventory and each rule's home),
`contracts/skill-structure.md` (the structural invariants a test could assert),
`quickstart.md` (the verification runbook).

There is no data layer and no external API. The "contract" here is the skill's
section structure, which is what other files and tests reference.
