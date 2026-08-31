# Implementation Plan: deployment key metadata

**Branch**: `59-deployment-key-metadata` | **Date**: 2026-08-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from this feature's `spec.md` (`wfctl feature-paths` → `FEATURE_DIR`; this repo records a spec root outside the working tree, so the literal `specs/<branch>` path does not apply — #81)

## Summary

Six shipped skills carry a top-level `deployment:` frontmatter key that the Agent
Skills spec does not allow. Delete the key and the parser that reads it; name the
natively discoverable skills in one constant inside the installer instead.

The issue proposed relocating the key under `metadata`, which the spec permits.
That was rejected during design for two reasons: the project has no YAML parser,
so a nested key costs *more* parsing code than the flat key it replaces; and
`layer-model` already assigns authority over layer contents to `install-skills`,
which a per-file switch was contradicting. Moving the switch into the installer
makes the code match a record that is already accepted.

Because the switch is no longer inside a skill file, a skill wfctl ships but does
not own can join the set — which closes the reachable half of #108.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer`, `rich` at runtime — unchanged; this feature
adds none. Dev: `pytest>=8`, `ruff>=0.15,<0.16`, `mypy>=1.11,<3`.
**Storage**: Files only. Package data under `wfctl/agents/`; installed trees at
`.agents/`, `.claude/`, `.bob/`, `.github/skills/`, `.specify/`; the per-layer
record at `.wf-skills-manifest.json`.
**Testing**: `uv run pytest -q` (521 tests, ~27s), plus `uv run ruff check
wfctl/ tests/` and `uv run mypy wfctl/`. `wfctl doctor` for installed-tree drift.
A manual `install-skills` exercise is required because the suite checks that
skills ship and cross-reference, not that they behave.
**Target Platform**: Developer workstations and CI; the installed output is read
by five agent clients.
**Project Type**: CLI (single package).
**Performance Goals**: None specific. Install is a bounded copy over 28
directories; nothing here changes its cost.
**Constraints**: No new runtime dependency — in particular no YAML parser. The
ruff rule set stays `E4`, `E7`, `E9`, `F` (widening it is its own diff, #14).
`mypy` runs with `disallow_untyped_defs`, so new functions are annotated. No
vendored file is edited. `pyproject.toml`'s `version` is not touched — bumping it
on `main` ships a release.
**Scale/Scope**: 28 shipped skills, 6 discoverable today and 7 after; five agent
layers; one vendored skill.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. `AGENTS.md` states the
substitution explicitly — *"Architectural constraints: Not here. `wfctl arch
context` prints the in-force set"* — so the gates below are the five accepted
records plus the template's three project-independent gates. The substitution is
recorded in Complexity Tracking.

**Project-independent**

- [x] **Validation plan exists** — `uv run pytest -q`, `uv run ruff check wfctl/
      tests/`, `uv run mypy wfctl/`, `wfctl doctor`, plus a new offline
      conformance assertion (FR-010), a new declaration guard (FR-005), and the
      manual install exercise in `quickstart.md`.
- [x] **Complexity is justified** — the change is net-negative in lines. It
      deletes a hand-rolled frontmatter parser and adds a `frozenset` and two
      small tests. The one addition beyond the minimum, the FR-010 conformance
      test, is justified in Complexity Tracking.
- [x] **Ownership is stated** — authority for what lands in `.claude/` belongs to
      `install-skills`. A skill file cannot own it: for a vendored skill upstream
      rewrites the file, so any decision stored there expires on the next pull;
      and for wfctl's own skills, `layer-model` has already assigned that
      authority to the installer. See `design.md`, "Boundaries and Ownership".

**In-force records** (`wfctl arch context`)

- [x] **`layer-model`** — source stays under `wfctl/agents/`; every dotted tree
      remains generated, gitignored and un-hand-edited. Two sentences in this
      record become false and are amended in the same change (FR-009).
- [x] **`vendor-upstream-skills`** — `i-have-adhd` is not edited. Its
      `disable-model-invocation` key stays, which is why it remains the one
      permitted conformance failure and why the discoverable-set membership makes
      it loadable rather than self-invoking.
- [x] **`knowledge-placement`** — one home per fact. The list of discoverable
      skills lives in code; `layer-model` describes the rule and names the
      constant without restating its contents.
- [x] **`install-modes`** — untouched. Install semantics, backup attribution and
      layer disjointness are unchanged.
- [x] **`no-hardcoded-agent`** — untouched. No committed hook names an agent;
      this change does not add or alter hooks.

A `wfctl arch none` declaration was filed during design: the change draws no new
boundary, it stops the code contradicting one an accepted record already drew.

## Project Structure

### Documentation (this feature)

```text
<FEATURE_DIR>/                          # wfctl feature-paths
├── design.md            # /speckit.brainstorm → idea-refine output
├── spec.md              # /speckit.specify output, clarified
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── skill-frontmatter-and-layout.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit.tasks output — not created here
```

### Source Code (repository root)

```text
wfctl/
├── cli.py                              # _skill_deployment() deleted;
│                                       # _MIRRORED_SKILLS added;
│                                       # _claude_native_skill_mirror() rewired
├── _bundle.py                          # unchanged — BUNDLE_ROOT resolution
└── agents/
    └── skills/
        ├── architecture-decisions/SKILL.md          ─┐
        ├── conversation-response-shape/SKILL.md      │ drop `deployment: skill`
        ├── design-levels/SKILL.md                    │ (response-shape also has
        ├── receiving-code-review/SKILL.md            │  a frontmatter comment
        ├── using-superpowers/SKILL.md                │  to rewrite)
        ├── verification-before-completion/SKILL.md  ─┘
        └── i-have-adhd/SKILL.md                      # untouched — vendored

docs/architecture/
└── layer-model.md                      # two sentences amended

tests/
├── test_install_skills.py              # 4 mirror tests refounded on the
│                                       # constant; +1 declaration guard
└── test_skill_frontmatter.py           # new — offline conformance assertion
```

**Structure Decision**: None of the template's options apply. This is an existing
single-package CLI with an established layout, and the feature touches four
places in it: the installer (`wfctl/cli.py`), the shipped skill bundle
(`wfctl/agents/skills/`), one architecture record (`docs/architecture/`), and the
test suite. No new package, module tree or directory is introduced.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from `wfctl arch context` and `AGENTS.md` | This repo has no `.specify/memory/constitution.md`; it keeps its constraints as accepted architecture records instead, and `AGENTS.md` says so explicitly | Leaving the gates empty makes the check decorative; importing another project's constitution would make it false |
| The FR-005 declaration guard (`tests/test_install_skills.py`) | The design replaced six frontmatter blocks with one editable list, which introduces a stale-name failure the previous mechanism could not have. The guard converts a risk this change created into a check | Not writing it leaves the risk uncovered; the frontmatter mechanism it replaces was self-consistent by construction, so the guard restores a property rather than adding one |
| A second new test file (`test_skill_frontmatter.py`, FR-010) beyond the minimum needed to ship the change | Without it the exact defect recurs silently — the next skill to invent a key ships clean until someone runs an external validator by hand. Clarify Q1 chose this over a manual one-off | The offline assertion was itself the simpler alternative: shelling out to the upstream reference validator would put network access and a `uvx` fetch inside `uv run pytest`, and would force #60's vendored-exemption policy to be designed here |

No other gate violations. The change removes more mechanism than it adds.

## Post-Design Constitution Re-Check

Re-run after Phase 1. No gate answer changed, and no new violation appeared.

Two things Phase 1 sharpened rather than reversed:

- **Ownership** gained a stated non-rule, in `data-model.md`: membership in the
  discoverable set decides *placement*, not *invocation policy*. A skill's own
  frontmatter still governs whether the model may reach for it unprompted. This
  is the assumption most likely to be made wrongly downstream, so it is written
  where the entity is defined rather than left implicit.
- **Complexity** was re-measured against the contract, not just the diff. Two
  externally visible contracts change: the frontmatter one narrows (a key is
  removed, none added), and the layout one gains a single entry. Neither adds a
  surface for a consumer to learn.

`contracts/` was written rather than skipped: wfctl installs into other people's
repositories and five agent clients read the result, so the frontmatter and
layout contracts are external, not internal.
