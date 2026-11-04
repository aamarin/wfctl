# Implementation Plan: Drop unloaded skills

**Branch**: `698-drop-unloaded-skills` | **Date**: 2026-11-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/698-drop-unloaded-skills/spec.md`

## Summary

wfctl stops shipping three skills no session needs, `using-superpowers`,
`verification-before-completion`, and `brainstorm`, along with their command
wrappers. It also takes `speckit-brainstorm` out of the Claude mirror, so the
brainstorm step appears once in the listing, as `/speckit.brainstorm`. That
follows the level-3 record `698-brainstorm-listed-once`.

The two skills that pointed at `verification-before-completion` point at `wfctl
verify` instead. An existing project loses the dropped paths through the orphan
rule the installer already has, and a new test pins that for a mirrored skill.

Design records read before this plan (via `reading-design-records`):

- `docs/architecture/design/698-brainstorm-listed-once.md`: found, `proposed`.
  Its Decision is what Phase 1 below implements for `speckit-brainstorm`, and its
  Verification list becomes three of the tests.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `typer`, `rich`; no new dependency  
**Storage**: package data under `wfctl/agents/`; the project's
`.wf-skills-manifest.json`, unchanged in shape  
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`,
then `uv run wfctl install-skills --agent claude --prune --yes` and `uv run wfctl
doctor` in this worktree  
**Target Platform**: any project that installs wfctl's skills, through the base
layer and the Claude layer  
**Project Type**: CLI with a shipped skills bundle  
**Performance Goals**: the one-word session in a clone with this branch installed
loads fewer tokens than 39,789, the same session on `main` on 2026-11-03  
**Constraints**: don't edit `start-session` (#700 is changing it); keep
`python-pattern-selection`, `python-package-layout`, and `model-the-domain`; leave
derived skills unedited except to delete them (`vendor-upstream-skills`); and
minimal-complexity bias  
**Scale/Scope**: 3 skills and 3 wrappers deleted, 1 mirror entry removed, 2
skills' prose repointed, 1 wrapper description widened, 1 record table and the
notices file edited, and about 8 tests updated or added

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repo has no `.specify/memory/constitution.md`. These gates come from
`AGENTS.md` and the accepted records instead, and Complexity Tracking records
that substitution.

- [x] Validation plan exists: the three `uv run` commands from `AGENTS.md`'s
      definition of done, the install and `doctor` run, the scratch-repo upgrade,
      and the before and after "hi" measurement are each named under Phase 2.
- [x] Complexity is justified: nothing is added. The plan deletes files and one
      list entry, and the one new test reuses the existing install fixtures.
- [x] Ownership is stated: the feature adds no state. Removal follows
      `deletion-follows-recorded-files` and the orphan rule in `cli.py`: wfctl
      removes a path only when its own manifest recorded it.
- [x] `vendor-upstream-skills`: `using-superpowers` and
      `verification-before-completion` are derived from `obra/superpowers`.
      Deleting them is not an in-place edit, and their rows leave the record's
      table and `NOTICES.md` together, since `test_skill_attribution.py` checks
      the two against each other.
- [x] `layer-model`: every edit is under `wfctl/agents/` or `wfctl/cli.py`. The
      installed `.agents/` and `.claude/` trees are regenerated with `install-skills`,
      never edited by hand.
- [x] `a-rule-is-expressed-as-a-check`: "the brainstorm step is listed once" is
      visible in the bundle, so it becomes a test rather than a comment.

## Project Structure

### Documentation (this feature)

```text
specs/698-drop-unloaded-skills/
├── design.md            # brainstorm output
├── spec.md              # specify and clarify output
├── plan.md              # this file
├── research.md          # Phase 0
├── quickstart.md        # Phase 1
└── tasks.md             # /speckit.tasks output
```

No `data-model.md` or `contracts/`: the feature adds no entity and no interface.
The one interface it touches is the set of names the bundle ships, and the spec's
FR-001 to FR-003 already state it.

### Source Code (repository root)

```text
wfctl/
├── cli.py                                   # _MIRRORED_SKILLS and its comments
└── agents/
    ├── commands/
    │   ├── brainstorm.md                    # deleted
    │   ├── using-superpowers.md             # deleted
    │   ├── verification-before-completion.md  # deleted
    │   └── speckit.brainstorm.md            # description widened
    └── skills/
        ├── NOTICES.md                       # superpowers list loses two names
        ├── brainstorm/                      # deleted
        ├── using-superpowers/               # deleted
        ├── verification-before-completion/  # deleted
        ├── design-levels/SKILL.md           # §4 names wfctl verify
        └── python-pattern-selection/SKILL.md  # overview and diagram name wfctl verify
docs/architecture/
└── vendor-upstream-skills.md                # two table rows removed, Log line added
tests/
├── test_install_skills.py                   # suppressed-wrapper pin, new upgrade test
├── test_skill_cross_references.py           # brainstorm mirror pin replaced
└── test_architecture_design_skill.py        # comment names wfctl verify
changes/
└── 698.change.md                            # release note
```

## Phase 0: Research

Written to `research.md`. Four questions, each settled by reading the repo:

1. Which brainstorm entry point stays. `/speckit.brainstorm`, per the record.
2. How an existing project loses a dropped skill. The orphan rule and `--prune`,
   checked end to end in a scratch repo on 2026-11-03.
3. What replaces `verification-before-completion` at level 4. `wfctl verify`.
4. Which tests pin the names. Listed under Phase 2.

## Phase 1: Design

### 1. Delete the three skills and their wrappers

Delete `wfctl/agents/skills/{using-superpowers,verification-before-completion,brainstorm}/`
and `wfctl/agents/commands/{using-superpowers,verification-before-completion,brainstorm}.md`.

### 2. Shrink `_MIRRORED_SKILLS`

Remove `brainstorm`, `speckit-brainstorm`, `using-superpowers`, and
`verification-before-completion` from the set in `cli.py`. Each removed name
loses the comment that defended it. The `brainstorm` comment goes with its entry.
The `speckit-brainstorm` comment is replaced by nothing in the set, since a name
that isn't in the set needs no defense there. The record carries why it left.

Two other comments mention the dropped names and need a fix:

- `_mirror_supersedes_wrapper`'s docstring uses "a pass naming `/brainstorm`" as
  its example of `check config` reading `.agents/commands/`. Change the example
  to `/design-levels`, which still ships a suppressed wrapper.
- The `speckit-orchestrate` entry's comment is unaffected, but read it once to
  confirm nothing in it leans on `speckit-brainstorm` being mirrored.

### 3. Repoint level 4 at `wfctl verify`

`design-levels/SKILL.md` §4 currently says:

```
Then `verification-before-completion` and `code-review`, unchanged — in every
language, Python included.
```

It becomes:

```
Then `wfctl verify`, which runs the checks the repo declares and records the
verdict, and `code-review` — in every language, Python included.
```

`python-pattern-selection/SKILL.md` changes the same name in its overview
sentence and in its diagram's `claim complete ──►` line. `design-levels` and
`python-pattern-selection` are wfctl's own, not derived, so editing them is
allowed.

### 4. Widen `/speckit.brainstorm`'s description

The current description starts "Start a brainstorming session." The new one adds
the moment the dropped `brainstorm` skill fired on: starting a new feature or
major change that needs design thinking before code. It keeps naming the
`speckit-brainstorm` skill and `design.md`, since
`test_skill_cross_references.py` reads the step's route from it.

### 5. Attribution

`NOTICES.md` drops `using-superpowers` and `verification-before-completion` from
the `obra/superpowers` list. `vendor-upstream-skills.md` drops both table rows
and gets a Log line: `2026-11-03  amended  — #698 stopped shipping
using-superpowers and verification-before-completion`.

### 6. Existing installs

No code change. The installer already diffs each layer's previous items against
this run's. A dropped path becomes an orphan: reported on a bare run, kept on
record, and removed by `--prune` with any backup restored. The new test in Phase
2 pins that for a mirrored skill dropped from the bundle.

## Phase 2: Tests and verification

Tests change in three files.

1. `test_install_skills.py`: remove `brainstorm`, `using-superpowers`, and
   `verification-before-completion` from `_SUPPRESSED_ON_A_MIRRORING_LAYER`. The
   two tests that compare it with the bundle then pass against the new tree.
2. `test_install_skills.py`, new: install a bundle carrying a mirrored skill,
   add a hand-authored `.claude/skills/my-own` and select the github tracker,
   then install a bundle without that skill. Assert that the bare run reports
   both layers' paths and removes nothing, that `--prune --agent claude` removes
   the paths from `.agents/skills/`, `.agents/commands/` and `.claude/skills/`,
   and that `my-own` and `.agents/trackers/github.json` remain.
3. `test_skill_cross_references.py`: replace
   `test_brainstorm_is_mirrored_onto_the_native_discovery_path` with a test that
   `speckit-brainstorm` is not in `_MIRRORED_SKILLS` and that
   `speckit.brainstorm.md` carries no `disable-model-invocation`. The docstring
   says why: #473 made the wrapper the route, and a mirror beside it is a second
   listing entry.
4. `test_skill_cross_references.py`, new: no file under `wfctl/agents/` names
   `using-superpowers`, `verification-before-completion`, or the bare
   `brainstorm` skill. This catches a pointer the cross-reference test would read
   as prose.
5. `test_architecture_design_skill.py`: its comment names
   `verification-before-completion` as a source of PASS/FAIL. Name
   `speckit-implement` alone.

Then:

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`.
- `uv run wfctl install-skills --agent claude --prune --yes` and `uv run wfctl
  doctor` in this worktree.
- The scratch-repo upgrade from `quickstart.md`, using this branch's bundle.
- The "hi" measurement in a fresh clone of this branch with the Claude layer
  installed, compared with 39,789.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Gates come from `AGENTS.md` and the accepted records, not a constitution | the repo has no `.specify/memory/constitution.md` | inventing a constitution would put gates in the plan with no source |
