# Implementation Plan: Scan files for clarify and analyze

**Branch**: `307-clarify-findings-in-repo` | **Date**: 2026-09-09 | **Spec**: `<spec-root>/307-clarify-findings-in-repo/spec.md`
**Input**: Feature specification, and the two records this branch already committed.

## Summary

`clarify` and `analyze` each gain an instruction, in their **command wrapper**, to
write one scan file per change at `<arch-root>/scans/<issue>-<step>.md`, commit it,
and check it with `wfctl arch check`. The file's body is a coverage table — one row
per category the step examined — with the findings beneath it and a pointer to the
full artifact in `FEATURE_DIR`.

No Python behaviour changes. No predicate, no `_STEPS` entry, no gate. The work is
two wrapper files, one AGENTS.md paragraph, and tests that assert the wrappers ship
carrying the instruction — because a change under `wfctl/agents/` is otherwise
invisible to the suite.

## Technical Context

**Language/Version**: Python 3.11+ (the tests); markdown (the shipped instruction)
**Primary Dependencies**: none new. `typer` + `rich` already present; the feature
adds no runtime dependency and no import.
**Storage**: files under `<arch-root>/scans/`, committed to the branch. The arch
root is resolved by `wfctl arch-root`, never written in (FR-007).
**Testing**: `uv run pytest -q`; wrapper-content assertions in the shape
`tests/test_skill_attribution.py` and the existing skill-shipping tests use.
**Target Platform**: wherever wfctl installs — the instruction ships as package data
under `wfctl/agents/commands/`.
**Project Type**: single project, CLI + shipped agent instructions.
**Performance Goals**: none. One file write and two git calls per step.
**Constraints**:
- `vendor-upstream-skills` — `speckit-clarify` and `speckit-analyze` are
  `github/spec-kit`-derived; the instruction goes in the wrapper, not the SKILL.md
  (FR-008).
- `the-scan-is-attested-where-the-reviewer-reads` — the repository holds the
  attestation, the spec store keeps the detail; no second copy of the artifact.
- `307-the-coverage-map-is-the-evidence` — the coverage table is the body, not a
  footnote.
- `knowledge-placement` — the AGENTS.md paragraph is guidance for the worker; the
  constraint itself stays in the record.
- `a-rule-is-expressed-as-a-check` — the visibility rule ships as `wfctl arch
  check`, which already exists and already answers this question.
**Scale/Scope**: two wrapper files, one docs paragraph, three or four tests.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repo has no `.specify/memory/constitution.md`. The gates below are the two
project-independent ones the template keeps, plus gates substituted from this
repo's own accepted records and `AGENTS.md`; the substitution is recorded in
Complexity Tracking, as the template requires.

- [x] **Validation plan exists** — `uv run pytest -q`, `uv run ruff check
      wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl doctor`, plus the manual
      exercise `AGENTS.md` requires for any change under `wfctl/agents/`:
      `uv run wfctl install-skills` then run the changed command. Named per story
      in the spec's Validation Strategy.
- [x] **Complexity is justified** — one new directory and no new code path. The
      check the feature depends on (`wfctl arch check`) already exists and takes an
      arbitrary path (`cli.py:1233`), so nothing is built to support it. The
      simpler path — putting the evidence in the PR body — is rejected in the
      level-2 record's `Direct baseline` for being unobservable to any check.
- [x] **Ownership is stated** — the level-2 record names it: the repository owns
      *"was this change scanned, and what did the scan cover?"*, and the spec store
      cannot, because `spec_root` resolves outside the working tree and
      `<repo>/specs` is gitignored, so nothing it holds is part of the change under
      review. The spec store keeps *"what exactly did the scan say?"*.
- [x] **Derived files are layered, not edited** (`vendor-upstream-skills`) — every
      instruction lands in a wrapper. No `SKILL.md` under
      `wfctl/agents/skills/speckit-*` is touched.
- [x] **A rule with a visible violation ships as a check**
      (`a-rule-is-expressed-as-a-check`) — a scan file that no reviewer would read
      is visible to `wfctl arch check`, and FR-013 makes the step run it. The
      *contents* of the coverage table have no objective test and stay prose,
      which that record's own question puts on the prose side.
- [x] **No gate is added** (`promised-evidence-blocks-on-silence`, #100) — nothing
      reads the verdict. The vocabulary is `_predicates.Verdict`'s so a later gate
      can, without a fourth shape being invented first.

Re-checked after Phase 1: unchanged. Phase 1 produced no contract and no new
entity beyond the three the spec already names.

## Project Structure

### Documentation (this feature)

```text
<spec-root>/307-clarify-findings-in-repo/
├── design.md            # brainstorm output
├── spec.md              # /speckit.specify output, with § Clarifications
├── plan.md              # this file
└── tasks.md             # /speckit.tasks output
```

### Source Code (repository root)

```text
wfctl/agents/commands/
├── speckit.clarify.md        # gains the scan-file instruction
└── speckit.analyze.md        # gains the scan-file instruction

docs/architecture/
├── the-scan-is-attested-where-the-reviewer-reads.md   # committed
├── design/307-the-coverage-map-is-the-evidence.md     # committed
└── scans/
    ├── 307-clarify.md        # committed
    └── 307-analyze.md        # written by the analyze step

tests/
└── test_scan_files.py        # wrappers ship, carry the instruction, and
                              # scans/ stays out of `arch context`

AGENTS.md                     # one paragraph: where a scan file goes and why
```

**Structure Decision**: single project. The feature's shipped surface is package
data under `wfctl/agents/commands/`, which `MANIFEST.in` already grafts into the
wheel; the tests live beside the existing suite. No `src/` reorganisation, no new
module — `wfctl/` gains no file.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from records rather than a constitution file | This repo has no `.specify/memory/constitution.md`; the template requires gates from *some* documented source and calls a borrowed one false | Shipping the two generic gates alone would leave `vendor-upstream-skills` and `a-rule-is-expressed-as-a-check` — the two constraints this change actually argues with — ungated |
| A fourth subdirectory under the arch root | The attestation has to be somewhere `wfctl arch check` reaches and `wfctl arch context` does not | A new tree beside `docs/architecture/` does not move with a repo that relocates `arch_root`; `<arch-root>/design/` holds a record shape a clean scan cannot fill |

## Phase 0 — research

No open unknowns. Everything the design rests on was read out of this tree and is
listed in the level-3 record's `Verified` section: `arch check`'s path handling
(`cli.py:1233`), `load_records`' one-level glob (`_arch.py:146`), `design_block`'s
early return (`_predicates.py:520`), the two predicates' reads
(`_predicates.py:719`, `:792`), and clarify's discarded coverage map
(`speckit-clarify/SKILL.md` step 2). `research.md` would restate that list, and a
digest of a record is the copy that drifts.

## Phase 1 — design artifacts

No `data-model.md` and no `contracts/`. The three entities the spec names — scan
file, coverage table, verdict — are a markdown document's sections, not a schema,
and nothing calls anything. The document's shape is fixed by
`307-the-coverage-map-is-the-evidence`, which carries the rendered example; a
second copy in `data-model.md` is the drift this repo keeps naming.

`quickstart.md` is likewise omitted: the feature's quickstart is running
`/speckit.clarify`, which the pipeline already routes to.
