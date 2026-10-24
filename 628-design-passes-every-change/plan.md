# Implementation Plan: Every change runs the design passes and records whether it needs a spec

**Branch**: `628-design-passes-every-change` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `spec.md` in this feature's spec dir

## Summary

A change that bypasses Spec Kit runs the design passes through a new
`design-passes` skill, and every PR answers whether the change needed a spec.
The work has two halves.

1. **Skills and prose.** A new skill, `design-passes`, and four places
   repointed to it: the `worktree-handoff` route line, the "not for" lines in
   `design-levels` and `architecture-design`, and the paragraph in `AGENTS.md`.
   The "not for" lines in `design-levels`, `architecture-design`,
   `model-the-domain`, and `architecture-decisions` now exclude a change by
   whether it moves a boundary, not by its kind, so a bug fix that
   `design-passes` sends to any of them isn't sent back
   (`contracts/skills.md §Routing between the skills`). `design-levels` level 2
   gains the same first step as the new skill. The review panel's reviewers
   also report any design decision the diff makes that no record or spec on
   the change covers (`contracts/skills.md §fanning-out-code-review Step 2`).
2. **One check.** A new module, `wfctl/_sections.py`, reads a
   `change_sections` list from `wfctl.json`. `check-body` reports a listed
   section that's missing, empty, N/A, or a bare yes or no with no reason, and
   `check config` reports a listed
   section the PR template doesn't have. This repo lists "Needs a spec?" and
   adds it to its PR template.

The spec answer is recorded only in the PR section, which `check-body` checks.
Nothing checks the level-3 answer, test-first, or the refactor.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `typer` and `rich`, already in use. Nothing new.
**Storage**: N/A. `wfctl.json` gains one key, and the spec answer lives in the
PR body.
**Testing**: `uv run pytest -q`, with new tests in `tests/test_sections.py`,
`check-body` CLI cases in `tests/test_shape.py`, `check config` cases in
`tests/test_cli_status.py`, and two cross-reference tests in
`tests/test_skill_cross_references.py`. Plus `uv run ruff check wfctl/ tests/`
and `uv run mypy wfctl/`.
**Target Platform**: macOS and Linux shells where wfctl runs.
**Project Type**: CLI, plus the skills tree it ships as package data.
**Performance Goals**: `check-body` stays a read of one file and `wfctl.json`.
`check config` adds a bounded `find` of three directory levels.
**Constraints**: No edit to `opening-a-change`, which #622 is redesigning. No
edit to Spec Kit-derived skills (`vendor-upstream-skills`). wfctl hardcodes no
section name. Minimal-complexity bias.
**Scale/Scope**: One new module of about 120 lines, one new skill, edits to
four skills, `AGENTS.md`, this repo's PR template, and `wfctl.json`.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repo has no `.specify/memory/constitution.md`. The gates below come from
`AGENTS.md` and the in-force records, as recorded under Complexity Tracking.

- [x] Validation plan exists: the three `uv run` commands, the new tests named
      above, `uv run wfctl check config`, `uv run wfctl install-skills` with a
      real `design-passes` run, and `uv run wfctl doctor`.
- [x] Complexity is justified: one module mirroring `_change.py`'s
      `load_required` shape, and one skill. `628-design-passes-own-skill.md`
      argues the skill against rewriting four places, and
      `628-spec-answer-in-pr-body.md` argues the config key against hardcoding.
- [x] Ownership is stated: the repo owns `change_sections`, since only it knows
      which of its template's sections need a real answer. wfctl computes the
      findings from the body and the list. The agent writes the answer in the
      PR section, and nowhere else.
- [x] `a-rule-is-expressed-as-a-check`: the spec answer is visible in the PR
      body, so it ships as a check. Level 3, test-first, and the refactor
      leave nothing a check can trust beyond the agent's word, so they
      stay prose in `design-passes`.
- [x] `knowledge-placement`: the instructions live in a skill, the decision in
      `docs/architecture/`, and the repo's choice of sections in `wfctl.json`.
- [x] `change-carries-release-note`: `changes/628.addition.md`.
- [x] `layer-model`: edits go to `wfctl/agents/`, never to `.agents/`.

Post-design re-check: still passing. Research R6 adds a template search in
Python that duplicates `opening-a-change` Step 2's `find`, which the PR-body
record named as a cost. It stays in `check config`, and a drift shows up as a
finding there.

## Project Structure

### Documentation (this feature)

```text
628-design-passes-every-change/
├── design.md            # brainstorm output
├── spec.md
├── plan.md              # this file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   └── skills.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
wfctl/
├── _sections.py                         # new: load_required, body_findings, templates, template_problems
├── cli.py                               # check_body_cmd and check_config_cmd call _sections
└── agents/skills/
    ├── design-passes/SKILL.md           # new
    ├── design-levels/SKILL.md           # "Not for" line, level-2 first step, level-2 exit
    ├── architecture-design/SKILL.md     # "Not for" line, keyed on boundary movement
    ├── model-the-domain/SKILL.md        # "Not for" line, keyed on boundary movement
    ├── architecture-decisions/SKILL.md  # "Not for" line, keyed on boundary movement
    ├── fanning-out-code-review/SKILL.md # Step 2: a fifth dispatch bullet
    └── worktree-handoff/SKILL.md        # route section

tests/
├── test_sections.py                     # new: pure findings, load_required, template_problems
├── test_shape.py                        # extended: check-body CLI cases from contracts/cli.md
├── test_cli_status.py                   # extended: check config template gap, bad value
└── test_skill_cross_references.py       # each route section names design-passes; the old phrase is gone

.github/pull_request_template.md         # "## Needs a spec?" section and comment, contracts/cli.md
wfctl.json                               # "change_sections": ["Needs a spec?"]
AGENTS.md                                # pipeline-skip paragraph; change_sections beside change_check
changes/628.addition.md                  # release note
```

**Structure Decision**: The check is a new module beside `_change.py` rather
than code in `cli.py` or `_shape.py`. `_shape.py` stays a pure string module
about drawings, and `_change.py`'s docstring already sets the pattern of each
config key's schema living with the feature that reads it.

### `wfctl/_sections.py`

```python
CONFIG_KEY = "change_sections"

def load_required(repo_root: Path) -> tuple[list[str], list[str]]: ...
def body_findings(body: str, required: list[str]) -> list[str]: ...
def templates(repo_root: Path) -> list[Path]: ...
def template_problems(repo_root: Path, required: list[str]) -> list[str]: ...
```

- `load_required` follows `_change.load_required` line for line, with
  "section heading" for "field name".
- `body_findings` walks the body with `_md.walk`, collects ATX headings outside
  fences, and applies research R4 and R5. It reads no file.
- `templates` mirrors `opening-a-change` Step 2 (research R6).
- `template_problems` runs `body_findings` logic on each template for the
  "missing" state only, since a template's sections are meant to be empty.

### The cross-reference tests

The spec asks for a test that fails when a route section stops pointing to
`design-passes`. A test that searches for "straight to implementation" can't do
that, since the edits remove the phrase and a later edit that drops the pointer
leaves nothing for it to find. So the file gains two tests.

1. `test_every_route_around_spec_kit_names_design_passes` reads four sections,
   each from a start marker to an end marker, and asserts each one contains
   `.agents/skills/design-passes`. A missing start marker fails the test too,
   so renaming a section can't make it pass by finding nothing.

   | File | Start marker | End |
   | --- | --- | --- |
   | `skills/design-levels/SKILL.md` | `Not for:` | the next blank line |
   | `skills/architecture-design/SKILL.md` | `**Not for**:` | the next blank line |
   | `skills/worktree-handoff/SKILL.md` | `3. **Which route this work takes.**` | `4. **` |
   | `AGENTS.md` at the repo root | `Not every change needs the spec pipeline.` | the next blank line |

   `AGENTS.md` isn't shipped, so the test reads it from the checkout next to
   `tests/`. The three skill files are read through `files("wfctl")`, the same
   way the rest of the file reads them.
2. `test_no_shipped_file_sends_a_change_straight_to_implementation` reads every
   `.md` under `wfctl/agents/` and `AGENTS.md`, collapses whitespace, lowercases
   the text, and asserts "straight to implementation" isn't in it. Collapsing
   whitespace catches the phrase wrapped across two lines, which is how
   `architecture-design` has it today, and lowercasing catches
   `worktree-handoff`'s "Straight to implementation".

### Order of work

1. `_sections.py` and `tests/test_sections.py`, test first.
2. `check-body` and `check config` wiring, with their CLI tests.
3. The PR template section with the comment from `contracts/cli.md`, the
   `wfctl.json` key, and `uv run wfctl check config`.
4. The two cross-reference tests, failing. Then `design-passes/SKILL.md`, the
   four pointers, the `model-the-domain` and `architecture-decisions` "Not
   for" lines, the fifth dispatch bullet in `fanning-out-code-review`, and the
   `design-levels` level-2 step and exit, with the wording in
   `contracts/skills.md`.
5. `AGENTS.md`, the release note, `uv run wfctl install-skills --agent claude`,
   the agent runs in `quickstart.md` §2, §4, and §5, and `uv run wfctl doctor`.

## Complexity Tracking

| Item | Why | Note |
| --- | --- | --- |
| No constitution | The repo has none | Gates taken from `AGENTS.md` and the in-force records listed above |
| Template search duplicated in Python | `check config` has to find the template to report a gap | Research R6; confined to `check config` |
