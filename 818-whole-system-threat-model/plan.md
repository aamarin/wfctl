# Implementation Plan: Whole-system threat model

**Branch**: `818-whole-system-threat-model` | **Date**: 2026-11-21 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from the feature's spec folder, `spec.md`

## Summary

wfctl ships Anthropic's `threat-model` skill and its `_lib/checkpoint.py` helper, unedited except for the attribution line, plus a wfctl skill called `threat-baseline` that layers over them. A new brainstorm pass, `threat-baseline`, pauses a branch that adds or edits a level-2 record with a `## Threat model` section until `THREAT_MODEL.md` is committed at the repository root, or until the user records that the pass doesn't apply. The branch ends by running `/threat-baseline` on wfctl and committing wfctl's own baseline.

The technical approach follows the code that already exists:

1. The pass is one more `SubStep` with one evidence reader. The reader asks `touched_on_this_branch` before `branch_records`, so a failed git read holds the branch instead of skipping the pass, and reads `HEAD` with `git ls-tree`, which tells a missing file apart from git failing (research R4 to R6).
2. The `threat-baseline` skill reads `auto_approve` from `wfctl status --json`, ends by committing `THREAT_MODEL.md`, and tells the agent that declaring the pass doesn't apply is the user's call. `design-levels` sends the agent to `/threat-baseline` before it writes a control's threat model, and the pass catches a run that skips that (research R1, FR-015).
3. Installation reuses `_MIRRORED_SKILLS` and the base layer's copy of `agents/skills`, so the helper lands beside the skill for every agent, and `threat-baseline` points the agent at it (research R2).
4. Attribution follows `vendor-upstream-skills.md`: a line in `SKILL.md`, rows in both tables, and a `NOTICES.md` section with the Apache-2.0 text. The attribution test learns a licence per notice section, since today it assumes every upstream is MIT (research R8).

Design records: 1 listed in design.md
  docs/architecture/design/818-threat-baseline-layers-over-upstream.md

The level-2 record `docs/architecture/security-record-needs-baseline.md` decides that wfctl checks for the file, and that the agent shouldn't answer whether it exists.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13). The vendored helper is a standalone Python 3 script.  
**Primary Dependencies**: `typer` and `rich`, unchanged. No new runtime dependency. The helper uses only the standard library.  
**Storage**: N/A. The pass re-derives everything from files and git on each read.  
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `uv run wfctl doctor`, `uv run wfctl verify`. A design-time prompt against an installed tree checks the trigger separation by hand.  
**Target Platform**: macOS and Linux, wherever wfctl runs.  
**Project Type**: CLI, plus the skills and commands it installs into a project.  
**Performance Goals**: The pass adds one `git ls-tree` call to `wfctl status`, and only on a branch whose records carry a threat model. The record listing it asks for is the one `fact_architecture_accepted` already builds.  
**Constraints**: Upstream's files stay unedited except for the attribution line (`vendor-upstream-skills`). The pass checks existence only, never content. Minimal-complexity bias.  
**Scale/Scope**: One new skill, one vendored skill and helper, one pass, and wfctl's own `THREAT_MODEL.md`. Existing tests change in five files: three fixes for the vendored files (R10), four changes to the attribution test (R8), and the pass-order assertions in `test_declared.py` and `pipeline_payload_snapshot.json`.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repository has no `.specify/memory/constitution.md`, so the gates below come from `AGENTS.md` and the accepted records. The substitution is recorded under Complexity Tracking.

- [x] Validation plan exists: the suite, ruff, and mypy, plus the pass's state tests, the test changes written to fail first, the installed-helper check, and the design-time prompt.
- [x] Complexity is justified: the only new abstraction is one skill, and the level-3 record argues it against a note in `design-levels`.
- [x] Ownership is stated: wfctl computes whether the baseline is committed, from git. The agent shouldn't, because it would be grading its own work. The user decides when the pass doesn't apply, and the remedy, the skill, and the wrapper all say so, since `step none` has no check on who runs it (FR-007b).
- [x] Release note: the branch commits `changes/818.addition.md` (`change-carries-release-note`).
- [x] Imports respect the Context Map: the new reader sits in `wfctl/_evidence.py` beside its siblings and imports nothing new across contexts (`contexts-are-packages`).
- [x] Upstream stays layered, not edited: every wfctl addition lives in `threat-baseline` or in tests (`vendor-upstream-skills`).
- [x] A rule ships as a check where its violation is visible: the pass is that check (`a-rule-is-expressed-as-a-check`).
- [x] Agent-facing changes are exercised: `uv run wfctl install-skills` runs, and `/threat-baseline` builds wfctl's own baseline from the installed tree (`AGENTS.md`, Definition of done).

Re-checked after Phase 1: no gate changed.

## Project Structure

### Documentation (this feature)

```text
<spec folder>/818-whole-system-threat-model/
├── design.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/threat-baseline-pass.md
├── checklists/requirements.md
├── scans/clarify.md
└── tasks.md             # /speckit.tasks output, not created here
```

### Source Code (repository root)

```text
wfctl/
├── _pipeline.py                       # new SubStep "threat-baseline" between architecture and software-design
├── _evidence.py                       # new reader brainstorm_threat_baseline, BASELINE_UNANSWERED_REASON,
│                                      # its reason and remedy constants
├── cli.py                             # _MIRRORED_SKILLS gains threat-model, threat-baseline, _lib;
│                                      # install-skills ignores .threat-model-state/
└── agents/
    ├── commands/threat-baseline.md    # wrapper for layers other than Claude; says step none is the user's
    └── skills/
        ├── NOTICES.md                 # new Apache-2.0 section; a licence line on every section
        ├── LICENSE-Apache-2.0         # upstream's license text
        ├── _lib/checkpoint.py         # vendored, unedited
        ├── threat-model/              # vendored, attribution line appended to SKILL.md
        ├── threat-baseline/SKILL.md   # wfctl's layer: reads auto_approve, commits THREAT_MODEL.md,
        │                              # re-reads the record's threat model, never runs step none
        └── design-levels/SKILL.md     # security part names threat-baseline and runs it first

docs/architecture/vendor-upstream-skills.md   # one row in each table

tests/
├── test_skill_frontmatter.py          # ALLOWED_KEYS gains argument-hint
├── test_skill_cross_references.py     # _OWN_FILE matches "in this directory"; new .claude/skills path test
├── test_skill_attribution.py          # _ROW accepts "_"; licence per section; Apache block checked
│                                      # against LICENSE-Apache-2.0; claim check for _lib/ paths
├── test_declared.py                   # brainstorm pass lists at 25, 399, 406 gain threat-baseline
├── pipeline_payload_snapshot.json     # brainstorm passes gain threat-baseline
├── test_install_skills.py             # mirrors and ignore entry
└── test_pipeline_threat_baseline.py   # every row of R6, the git-failure and no-trunk rows included,
                                       # and a fenced "## Threat model" that doesn't count

changes/818.addition.md
THREAT_MODEL.md                        # last step, built by /threat-baseline
```

**Structure Decision**: The single-project layout wfctl already has. The new reader goes in `_evidence.py` beside the three brainstorm readers it sits between, and the pass tests get their own file because the existing pipeline tests are organized by feature.

### Order of work

1. Vendor upstream's files, attribution, notices, the three vendored-file test fixes, and the attribution test's four changes, each test failing first.
2. Mirror entries and the ignore entry, with install tests.
3. The reader and the `SubStep`, with the state tests and the pass-order fixes in `test_declared.py` and the payload snapshot.
4. The `threat-baseline` skill and wrapper, and the `design-levels` paragraph that runs `/threat-baseline` before a control's threat model.
5. `uv run wfctl install-skills --agent claude`, the helper check, and the design-time prompt.
6. `/threat-baseline` on wfctl, then commit `THREAT_MODEL.md`.

Steps 1 and 3 don't depend on each other. Step 4 needs step 1's files to name, and steps 5 and 6 need everything before them installed.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| No constitution, so gates come from `AGENTS.md` and accepted records | The template asks for gates derived from a constitution, and this repository keeps its rules in `AGENTS.md` and `docs/architecture/` | Leaving the gates empty would make the check decorative, and borrowing another project's constitution would be false |
| A skill folder with no `SKILL.md` (`_lib/`) | Upstream calls its helper at `_lib/` beside the skill folder | Moving the helper inside `threat-model/` edits upstream's paths, which the next pull reverts |
