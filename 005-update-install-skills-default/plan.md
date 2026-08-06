# Implementation Plan: update-install-skills-default

**Branch**: `005-update-install-skills-default` | **Date**: 2026-07-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-update-install-skills-default/spec.md`

## Summary

Split `install-skills` into a base layer that always installs (`.agents/skills` + `.agents/commands`) and optional per-agent layers that own unique roots (`.claude/`, `.bob/`, `.github/`). The default becomes base-only, `--agent copilot` is added as a plain directory copy into `.github/skills`, and `--agent codex` informs rather than errors.

Because base and agent layers no longer share a destination, the backup cross-attribution at `cli.py:395` becomes unreachable instead of patched. One deliberate exception to that reasoning: foreign-file detection must union all manifest entries, because ownership of `.agents/skills` *moves* from the `claude` entry to the `base` entry across this version — without it, every existing repo's first upgrade prompts to overwrite 25 files it installed itself.

The tracker-consent work is already implemented on this branch (`b636356`) and is carried in this plan only as documentation and verification scope.

## Technical Context

**Language/Version**: Python 3.11+, `from __future__ import annotations` throughout
**Primary Dependencies**: typer (CLI), rich (console output); stdlib `subprocess`, `shutil`, `json`, `tempfile`, `pathlib`. No new dependency is required by this feature.
**Storage**: `.wf-skills-manifest.json` at the repo root — a single JSON file recording what was installed, per agent, with backup pointers. Gitignored.
**Testing**: `uv run pytest`; `typer.testing.CliRunner` for command invocation; `tests/conftest.py` fixtures provide a real git repo in `tmp_path` with `WFCTL_STATE_DIR` / `WFCTL_REPO_ROOT` overridden.
**Target Platform**: macOS and Linux developer machines; a `git` binary on PATH is assumed and already required.
**Project Type**: Single Python package (`wfctl/`) with a flat test suite (`tests/`).
**Performance Goals**: None beyond current behavior. The install is network-bound on one shallow clone of wf-skills; this feature does not add a second clone or a second pass over the tree.
**Constraints**: Destinations across all layers must be provably disjoint. Existing manifests must upgrade without user action. `--agent none` must keep resolving. No change to `_RUNTIME_TARGETS` (`.specify/*`), which is repo-level by design.
**Scale/Scope**: ~57 installed items per repo at the base layer, +25 to +48 per agent layer. One file changes materially (`wfctl/cli.py`), plus its test module.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. The template's gates
(workspace isolation, ZenStack policies, `.zmodel` tiers, `pnpm type-check`)
describe a different project. Substituted with gates derived from this
repository's evident conventions and the spec's own constraints — see
Complexity Tracking for the record of that substitution.

- [x] **Behavior change is bounded and stated**: the breaking change is the bare-install default. Documented in the spec (FR-016), the README, and a minor version bump. No silent behavior change ships unannounced.
- [x] **Upgrade path is silent**: no user-run migration command. FR-005 makes the first upgrade after this change indistinguishable from any other install.
- [x] **Invariants are enforced by tests, not comments**: the disjoint-destination property is what removes the cross-attribution bug, so it gets an assertion (SC-006), not a docstring. The existing `cli.py:395` comment is deleted rather than reworded.
- [x] **No new dependency**: the feature is a data-structure change plus copy targets. Nothing is added to `pyproject.toml`.
- [x] **No new abstraction without a second caller**: `_AGENT_SKILL_EXTRAS` already exists as the per-agent hook; Copilot does not need it and does not get one. No transform layer is introduced for a transform that isn't needed.
- [x] **Validation plan names its commands**: `uv run pytest` for the suite, plus the manual scratch-repo checks in `quickstart.md` for the one assumption tests cannot cover.

## Project Structure

### Documentation (this feature)

```text
specs/005-update-install-skills-default/
├── spec.md              # /speckit.specify output
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output — manifest shape
├── quickstart.md        # Phase 1 output — terminal walkthrough
├── contracts/
│   └── cli.md           # Phase 1 output — command surface contract
├── checklists/
│   └── requirements.md  # /speckit.specify output
└── tasks.md             # /speckit.tasks output — NOT created here
```

### Source Code (repository root)

```text
wfctl/
├── cli.py               # install_skills_cmd, uninstall_skills_cmd, _AGENT_TARGETS,
│                        #   _AGENT_SKILL_EXTRAS, _RUNTIME_TARGETS, manifest helpers
├── _paths.py            # unchanged by this feature
├── _tracker.py          # unchanged by this feature
├── _session.py          # unchanged by this feature
└── _pipeline.py         # unchanged by this feature

tests/
├── conftest.py          # repo_root / agent_dir fixtures
└── test_install_skills.py   # 32 cases today; the module this feature grows
```

**Structure Decision**: Single Python package, unchanged. This feature is
contained in `wfctl/cli.py` and `tests/test_install_skills.py`. No new module is
warranted: the layer split is a change to two module-level dicts and the loop
that consumes them, and extracting an installer module for that would add
indirection without a second caller.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --------- | ---------- | ------------------------------------ |
| Union of all manifest entries for foreign-file detection, despite layers being disjoint | Ownership of `.agents/skills` moves from the `claude` entry to the `base` entry in this version. Reading an old manifest with only the current entry's items makes wfctl's own files look foreign. | Per-entry detection is simpler and correct going forward, but produces an overwrite prompt listing ~25 files plus a backup directory of wfctl's own content on every existing repo's first upgrade. A one-line union avoids a migration command. |
| Constitution gates authored here rather than read from `.specify/memory/constitution.md` | No constitution file exists in this repo; the template's gates belong to another project. | Leaving the gates unchecked would make the section decorative. Filling in another project's gates would make it false. Tracked upstream as aamarin/wf-skills#3. |
