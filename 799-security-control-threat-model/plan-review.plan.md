# Implementation Plan: Security control threat model

**Branch**: `799-security-control-threat-model` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/799-security-control-threat-model/spec.md`

## Summary

A change that adds, removes, loosens, or tightens a security control writes a
threat model before code, as a `## Threat model` section in its level-2 record.
The security reviewers find that section, judge findings against it, and name
the record. The guard's accept-check threat model moves from R-013 into
`accept-check-threat-model.md`, which this branch already committed.

The work is five skill edits, one new reference file, two tests, and a release
note. No wfctl code changes. The design records are
`security-change-needs-threat-model.md` and `accept-check-threat-model.md`
(level 2) and `design/799-threat-model-in-the-record.md` (level 3).

## Technical Context

**Language/Version**: Python 3.11+ for the tests. The rest is Markdown skills.
**Primary Dependencies**: none new. The tests use pytest and read files.
**Storage**: N/A
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`,
`uv run wfctl doctor`, and a walkthrough of the installed skills after
`uv run wfctl install-skills`.
**Target Platform**: the agents that run wfctl's skills, and wfctl's own CI.
**Project Type**: CLI with packaged skills.
**Performance Goals**: N/A. The two tests run 28 guard reads and two file reads.
**Constraints**: no edit to a vendored skill (`security-and-hardening`,
`speckit-*`), per `vendor-upstream-skills.md`, and minimal-complexity bias.
**Scale/Scope**: five skills, one reference, two tests.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repository has no `.specify/memory/constitution.md`. The gates below come
from `AGENTS.md` and the accepted records, and Complexity Tracking records the
substitution.

- [x] Validation plan exists: `pytest`, `ruff`, `mypy`, and `doctor`, plus the
      two new tests, a mutation check of each, and the installed-skills
      walkthrough that `AGENTS.md` requires for any change under
      `wfctl/agents/`.
- [x] Complexity is justified: one new file, the reference, and the level-3
      record says why one file beats two copies.
- [x] Ownership is stated: the user sets the bar by accepting the record, the
      author writes it before code, and the reviewer reads it. The coordinator
      doesn't, since a bar written for each run is what caused the #792 loop
      (`security-change-needs-threat-model.md`, Owns truth).
- [x] No vendored skill is edited: `security-and-hardening` stays as shipped,
      and `reviewing-security` is wfctl's own layer over it.
- [x] Every change commits a release note (`change-carries-release-note.md`).
- [x] A rule is a check where a violation shows in an artifact
      (`a-rule-is-expressed-as-a-check.md`): the heading agreement and the
      guard's lists are tests. Whether a change loosens a control isn't in any
      artifact, so the reviewers report it instead.

## Project Structure

### Documentation (this feature)

```text
specs/799-security-control-threat-model/
├── design.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── threat-model-section.md
├── scans/
│   └── clarify.md
└── tasks.md             # /speckit.tasks
```

### Source Code (repository root)

```text
wfctl/agents/skills/
├── architecture-decisions/
│   ├── SKILL.md                        # one paragraph pointing at the reference
│   └── references/threat-model.md      # new: the section's four parts
├── design-levels/SKILL.md              # level 2: send a control change to the reference
├── design-passes/SKILL.md              # step 1: a control change answers question 2 yes
├── reviewing-security/SKILL.md         # find, judge against, and name the threat model
└── fanning-out-code-review/SKILL.md    # the brief states no bar and names no record

tests/
├── test_threat_model_skills.py         # new: the reference and reviewer name the same headings
└── test_accept_check_threat_model.py   # new: each listed form through the guard

docs/architecture/                      # committed in brainstorm
├── security-change-needs-threat-model.md
├── accept-check-threat-model.md
└── design/799-threat-model-in-the-record.md

changes/799.change.md                   # release note
```

**Structure Decision**: the reference goes in `architecture-decisions` because
it defines a section of a record, and that skill owns the record format. The
two tests are separate files because one checks the shipped skills, reading the
bundle through `files("wfctl")`, and the other reads this repository's own
record.

## Ownership

| Value | Who computes it | Why not the other side |
| --- | --- | --- |
| The bar a security change is judged against | The user, by accepting the record | The author would grade their own change, and the coordinator writes a new bar each run |
| Which record holds a control's threat model | The reviewer, by searching for the heading | A coordinator naming one record can leave another out |
| Whether one command runs the accept | The guard's `read` function | Unchanged by this branch |
| Whether the record's lists and the guard agree | The new test | A reviewer reading both by eye missed it on #792 |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| No constitution, gates taken from `AGENTS.md` and accepted records | The template asks for project gates | Inventing a constitution for one branch would be a gate with no source |
| A new reference file | Two skills have to agree on one section's shape | Two inline copies drift, and nothing notices (`design/799-threat-model-in-the-record.md`) |
