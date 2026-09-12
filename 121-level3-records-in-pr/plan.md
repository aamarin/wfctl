# Implementation Plan: level3 downstream

**Branch**: `121-level3-downstream` | **Date**: 2026-09-10 | **Spec**: [spec.md](./spec.md)
**Issue**: #326 (child of epic #121, scope item 6)
**Input**: Feature specification from this feature's `spec.md` — reached through
`wfctl feature-paths`, not `specs/<branch>/`, because this repository records a
`spec_root` outside the working tree.

## Summary

Four `/speckit.*` command wrappers gain an instruction to read the level-3 design
records a feature's `design.md` lists, and `/speckit.analyze` gains a seventh
detection pass that reports a task contradicting one. No Python changes, no new
command, no change to the record format.

The technical approach is entirely prose: the deliverable is four edited Markdown
files under `wfctl/agents/commands/` plus tests asserting they ship and
cross-reference. That is not a shortcut — it is what
`vendor-upstream-skills` and `a-rule-is-expressed-as-a-check` jointly require
here. The four `speckit-*` skills are `github/spec-kit`-derived, so an in-place
edit is reverted by the next upstream pull with no conflict to notice; the
wrapper is the layer. And a contradiction between a record's prose `Decision` and
a prose task description is not visible in any artifact mechanically, which is
the case `a-rule-is-expressed-as-a-check` leaves as prose delivered at the moment
it binds.

## Technical Context

**Language/Version**: Python 3.11+ for the test additions; the deliverable itself
is Markdown under `wfctl/agents/commands/`
**Primary Dependencies**: none added. `typer` + `rich` already carry the CLI, and
this feature adds no runtime code
**Storage**: the filesystem — `design.md` under `FEATURE_DIR`, records under
`<arch-root>/design/`, the scan file under `<arch-root>/scans/`
**Testing**: `uv run pytest -q`, plus the four exercises in the spec's Validation
Strategy, which the suite cannot perform — it checks that skills ship and
cross-reference, not that they read well
**Target Platform**: any repository wfctl installs into; the wrappers ship as
package data in the wheel
**Project Type**: CLI tool plus the agent-instruction bundle it installs
**Performance Goals**: none stated. The one quantity that could matter — records
read into `/speckit.implement`'s context — is unmeasured and recorded as an
assumption rather than a target
**Constraints**: FR-011 and FR-012 bound the change to
`wfctl/agents/commands/` and its tests. Ruff's rule set stays `E4, E7, E9, F`;
mypy runs with `disallow_untyped_defs` and not `strict`
**Scale/Scope**: four wrapper files, one new detection pass, one new scan-file
row. No feature in this repository currently lists more than one record

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository ships no `.specify/memory/constitution.md`. The gates below are
substituted from its documented conventions — `AGENTS.md` and the ten accepted
records `wfctl arch context` projects — and the substitution is recorded in
Complexity Tracking, as the template requires.

- [x] **Validation plan exists.** `uv run pytest -q`, `uv run ruff check
      wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl doctor`, plus
      `uv run wfctl install-skills` and the four named exercises. All four
      commands through `uv run`, which is the only thing that answers "does the
      installed tree match the source I am editing" in a repo carrying two wfctls
      on PATH.
- [x] **Complexity is justified.** The feature adds no abstraction. Every
      alternative that would have — a `wfctl design context` command, an
      `invariant:` field on the record format, a propagated `spec.md` section —
      is rejected in `design.md` and in the two records, each with the reason.
      The direct baseline won at level 3 and is recorded as the decision.
- [x] **Ownership is stated.** Two pieces of derived state, each with a record:
      *which records apply to this feature's work* is owned by `design.md`
      (`design-md-indexes-the-records`), and *how severe a contradiction is* is
      owned by the record's own frontmatter `status`
      (`326-contradiction-is-a-seventh-pass`).
- [x] **`vendor-upstream-skills`.** No `speckit-*` skill is edited. Every
      instruction lands in the wrapper, which is the layer that survives an
      upstream pull. FR-011 states this and SC-005 measures it from the diff.
- [x] **`a-rule-is-expressed-as-a-check`.** Asked of the rule: is a violation
      visible in an artifact the work already produces? For the wrapper contents,
      no — a prose contradiction is not mechanically visible, so the rule stays
      prose delivered at the moment it binds. For the file's own existence, yes —
      the scan file's pass G row is the artifact, and `wfctl arch check` already
      enforces that it reaches a reviewer.
- [x] **`knowledge-placement`.** A constraint on the system goes to
      `docs/architecture/`, which is where both records are. Guidance for the
      worker goes to the wrappers. Nothing about this feature belongs in
      `AGENTS.md`.
- [x] **`layer-model`.** Source is committed package data under
      `wfctl/agents/`; `.agents/` and `.claude/` are generated and never edited
      by hand. The four edits are to `wfctl/agents/commands/`, and
      `install-skills` is what puts them in a tree that can be exercised.

**Post-Phase 1 re-check**: unchanged. Phase 1 produced no new abstraction and no
new ownership question — its artifacts describe formats that already exist
(`design.md`'s section, the record's frontmatter, the scan file's table) rather
than introducing any.

## Project Structure

### Documentation (this feature)

```text
<FEATURE_DIR>/                        # outside the working tree; ask wfctl feature-paths
├── design.md                         # the brainstorm one-pager, and the record index
├── spec.md                           # /speckit.specify output, with § Clarifications
├── plan.md                           # this file
├── research.md                       # Phase 0
├── data-model.md                     # Phase 1
├── quickstart.md                     # Phase 1
├── contracts/                        # Phase 1
│   ├── record-list.md
│   ├── step-report.md
│   └── pass-g.md
├── checklists/
│   └── requirements.md               # written by /speckit.specify
└── tasks.md                          # /speckit.tasks — not created here
```

### Source Code (repository root)

```text
wfctl/agents/commands/
├── speckit.plan.md                   # + read the record list, report it
├── speckit.tasks.md                  # + read the record list, report it
├── speckit.implement.md              # + read the record list, report it
└── speckit.analyze.md                # + pass G, severity split, scan-file row

docs/architecture/
├── design-md-indexes-the-records.md  # level 2 — written, committed
├── design/
│   └── 326-contradiction-is-a-seventh-pass.md   # level 3 — written, committed
└── scans/
    ├── 121-clarify.md                # written, committed
    └── 121-analyze.md                # written by /speckit.analyze

tests/
└── <the existing skill-shipping suite>          # + assertions for the four wrappers
```

**Structure Decision**: The change is confined to `wfctl/agents/commands/` and
`tests/`. Nothing under `wfctl/` outside that directory is touched — no
predicate, no constant, no CLI verb — which is FR-012 and is measurable from the
branch diff (SC-005). The three `docs/architecture/` files listed are already
written and committed; they are shown because they are what the wrappers point
at, not because this plan creates them.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from `AGENTS.md` and `wfctl arch context` rather than from `.specify/memory/constitution.md` | The repository ships no constitution file. The template requires a substitution to be recorded rather than left implicit, since "a gate with no source is decorative, and one borrowed from another project is false" | Writing a constitution for this feature would put a repo-wide artifact inside a change whose subject is four command wrappers. The conventions already exist and are already in force — ten accepted records and a maintained `AGENTS.md` — so a new file would restate them and then drift |

No other row. The feature adds no abstraction, dependency, or infrastructure, and
the alternatives that would have are rejected in the two design records rather
than justified here.
