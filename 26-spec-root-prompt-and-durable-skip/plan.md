# Implementation Plan: spec-root prompt and durable-spec skip

**Branch**: `26-spec-root-prompt-and-durable-skip` | **Date**: 2026-08-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `spec.md`; design context from [design.md](./design.md)

## Summary

Teardown currently destroys gitignored design artifacts without a sound, and
duplicates them for repos that moved their specs somewhere durable. One predicate
— *is this artifact inside the worktree being removed* — fixes both, and its
answer also decides whether a failed preservation refuses the removal. Alongside
it, first-run setup gains the question that makes the durable location reachable
at all, since the setting has existed since #25 with nothing pointing anyone at
it.

Phase 0 confirmed the mechanism by experiment rather than argument: a failing
pre-remove hook aborts the removal even under `--force`, and a worktree holding
only gitignored specs reads clean to every version-control check, so nothing but
this hook can protect it.

## Technical Context

**Language/Version**: Python ≥ 3.11
**Primary Dependencies**: typer ≥ 0.12, rich ≥ 13 — both already present; the
prompt's panels use rich, which the codebase already renders with
**Storage**: JSON manifest per checkout (`.wf-skills-manifest.json`); artifacts
copied into the XDG state directory. No database, no migration
**Testing**: `uv run pytest -q`; lint `uv run ruff check .`; types `uv run mypy`.
Feature-specific: containment cases and prompt gating in
`tests/test_archive_specs.py` (renamed) and `tests/test_install_skills.py`
**Target Platform**: developer workstations, macOS and Linux; invoked
interactively and from a `workmux` pre-remove hook
**Project Type**: single-package CLI
**Performance Goals**: no regression in `feature-paths`, which runs on every
speckit script invocation. The containment predicate is a path comparison on a
list already assembled; it adds no filesystem calls and no subprocesses
**Constraints**: the pre-remove hook is on the teardown path — a defect here
either destroys artifacts or strands worktrees. Minimal-complexity bias
**Scale/Scope**: ~12 spec artifacts per branch, tens of branches per project.
Two source files (`_archive.py`, `cli.py`), one config file, two test modules

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. Gates below are
substituted from its own documented conventions — `pyproject.toml` rationale
comments, `.workmux.yaml` hook comments, and the existing module docstrings — and
the substitution is recorded in Complexity Tracking as the template requires.

- [x] **Complexity is justified.** The change adds one predicate, one manifest
      key, one hidden alias, and one drift check. No new dependency, no new
      module, no new abstraction. The rejected alternative that would have added
      one — tagging plan entries copy-vs-reference — is recorded in
      `data-model.md`.
- [x] **No new dependency.** typer and rich are already required.
- [x] **Deliberate simplifications are marked.** The alias and the drift check are
      transitional; both carry a stated end condition, and their collective
      removal is tracked as separate work (#36).
- [x] **Behaviour changes are argued in the code, not only in the commit.** Two
      docstrings currently argue the opposite of this design and are rewritten as
      part of it (FR-021), rather than left to contradict the shipped behaviour.
- [x] **Teardown safety over convenience.** Established by the module's existing
      docstring. This change tightens it: refusing a removal is now preferred to
      completing one that loses artifacts.
- [x] **Assumptions about external tools are verified, not inferred.** Satisfied
      by Phase 0 — every claim about `workmux` in this plan is observed
      behaviour, recorded with its transcript in `research.md`.

**Post-Phase 1 re-check**: passes unchanged. Phase 1 removed a candidate
abstraction (the copy-vs-reference tag) and added none.

## Project Structure

### Documentation (this feature)

```text
~/Development/wfctl-specs/26-spec-root-prompt-and-durable-skip/
├── design.md            # brainstorming output
├── spec.md              # /speckit.specify output
├── plan.md              # this file
├── research.md          # Phase 0 — three experiments, all resolved
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1 — manual verification
├── contracts/
│   └── cli.md           # Phase 1 — command surface and exit statuses
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit.tasks output — NOT created here
```

Specs live outside the repository: this project has `spec_root` recorded, which
is the configuration the feature is about. Paths resolve through
`wfctl feature-paths`, never a literal `specs/<branch>`.

### Source Code (repository root)

```text
wfctl/
├── _archive.py          # containment predicate in _plan; docstring rewritten
├── cli.py               # archive-specs + hidden alias; exit status;
│                        # install prompt; _NON_LAYER_KEYS; doctor drift check
└── _paths.py            # unchanged — the asked-marker read reuses
                         # spec_root_declaration

.workmux.yaml            # pre_remove rewritten; `|| true` removed

tests/
├── test_archive_specs.py    # renamed from test_archive_story.py
└── test_install_skills.py   # prompt gating and manifest writes
```

**Structure Decision**: single-package CLI, unchanged. The feature touches two
existing modules and adds no files outside tests. `_paths.py` is deliberately
untouched — reusing `spec_root_declaration` for the asked-marker read is what
keeps one resolution rule instead of two that can drift.

## Implementation Sequence

Ordered by risk, and by what unblocks what. Each step is independently
verifiable.

1. **Rename with the alias, first.** `archive-story` → `archive-specs`, old name
   hidden but working; tests renamed. Landing this before the exit-status change
   means the alias is proven while a failing hook still cannot abort anything.
   Reversed, a missing alias plus a blocking hook makes worktrees unremovable in
   every repo with an older configuration.
2. **Containment predicate in `_plan`.** Pure filter, no signature change. The
   regression test for the default layout is written before the predicate, since
   it is what proves the common case is untouched.
3. **Exit status and messages.** Only after step 2, because "at-risk artifacts
   existed and failed" is not expressible until the plan distinguishes them.
4. **`.workmux.yaml` hook.** Only after step 3 — the hook is what turns a non-zero
   status into a refused removal, and it must not be armed before the status it
   consumes is correct.
5. **Manifest key and `_NON_LAYER_KEYS`, together, in one commit.** Adding the key
   without the set membership crashes `doctor` and `install-skills` immediately.
6. **Install prompt**, reading the marker via `spec_root_declaration`, writing to
   the primary checkout.
7. **Doctor drift check** for configurations still naming the old command.
8. **Docstrings** — `_archive.py` module docstring and the command's, plus the
   FR-013 reconciliation. Last, so they describe what shipped.

Steps 1–4 and 5–7 are independent of each other and could be split into two pull
requests. Recommendation: keep them together. They are the setup and the
consequence of one setting, and separating them ships the skip behaviour to a
population that has no way to opt into it.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution substituted from repo conventions | No `.specify/memory/constitution.md` exists; the template requires recording the substitution rather than borrowing another project's gates | Inventing gates would make them decorative; copying another project's would make them false |
| Hidden command alias (FR-019) | Project configuration files are repo-local and copies predating the rename persist indefinitely. Combined with the now-blocking hook, an unknown command name makes worktrees unremovable | No alias plus reliance on reinstallation — nothing forces reinstallation, and the failure is severe and delayed |
| Fifth transitional drift check (FR-020) | Gives the alias an observable end condition instead of making it permanent | Shipping the alias with no removal criterion; rejected because that is how transitional code becomes load-bearing. Mitigated by #36, which tracks removing all five together |
| Separate `spec_root_asked` key | FR-012 requires the default answer to be indistinguishable from never having been asked, so the answer cannot be recorded in `spec_root` itself | Recording `spec_root: null` — `_manifest_spec_root` already treats empty as undeclared, so the key would be bookkeeping under a name implying behaviour |

## Phase Status

- [x] Phase 0 — research complete; all three open questions resolved by
      experiment, zero unverified assumptions remain
- [x] Phase 1 — `data-model.md`, `contracts/cli.md`, `quickstart.md` written
- [x] Constitution check — passes before and after Phase 1
- [ ] Phase 2 — `/speckit.tasks`
