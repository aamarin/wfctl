# Implementation Plan: Vendor wf-skills into wfctl's package

**Branch**: `43-vendor-wf-skills` | **Date**: 2026-08-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `wfctl-specs/43-vendor-wf-skills/spec.md`

## Summary

`install-skills` and `install-config` clone `aamarin/wf-skills@main` at run time.
`main` is a moving target, so the same wfctl version installs different content on
different days, and `doctor` needs the network to say anything at all. Ship the
skills inside the wheel instead: one tool version, one result.

The approach: copy the wf-skills tree into `wfctl/agents/` and `wfctl/specify/`
(dots stripped — `setuptools` silently drops dot-prefixed directories from
`build_py`), declare it as `package-data`, and repoint the `src` half of the
existing `(src, dst)` target lists at it. Both clones, `--repo`, `--ref` and the
resolved-commit pin go away. The manifest swaps `repo`/`ref`/`commit` for
`wfctl_version` plus a whole-tree `content_hash`, and `doctor`'s per-layer
network block becomes a dictionary comparison over those two fields.

Everything a repo receives — destination paths, per-kind counts, backups,
uninstall — is unchanged. The user-visible delta is that installs are instant and
offline, and the provenance line names a wfctl version instead of a URL.

**Merge order is constrained.** spec.md frames four stories; three of them are not
independently deliverable. Deleting `--repo`/`--ref` removes the variables the
manifest write consumes, so the write lands with US1, and US2 reads the
`content_hash` it produces, and US3 migrates records written in that shape — the
chain is **US1 → US2 → US3**. US4 (packaging checks) is genuinely independent and
can proceed in parallel from Phase 1. Merging US2 before US1 leaves `doctor`
comparing a field nothing writes; the ordering is enforced in
[tasks.md](./tasks.md) and repeated here so it is visible without reading it.

## Technical Context

**Language/Version**: Python, floor 3.11 (`requires-python = ">=3.11"`), CI matrix 3.11 + 3.13
**Primary Dependencies**: typer >=0.12, rich >=13. This feature adds none — it uses
`importlib.resources`, `hashlib`, `shutil` and `importlib.metadata` from the stdlib,
and *removes* the `subprocess`/`tempfile` usage that served the clones.
**Storage**: two on-disk artifacts — read-only package data under `wfctl/agents/`
and `wfctl/specify/`, and the per-repo `.wf-skills-manifest.json` (name unchanged).
**Testing**: `uv run pytest -q`, `uv run ruff check .`, `uv run mypy`. This feature
adds a CI job that builds a wheel, installs it clean into a scratch repo, and asserts
both bundled-content presence and the `.sh` executable bit — the one property the
source-tree suite structurally cannot check.
**Target Platform**: macOS and Linux developer machines; installed via `uv tool install`
or `pip install` from a git URL.
**Project Type**: single-package CLI.
**Performance Goals**: `install-skills` completes without a network round-trip
(today ~15s of clone); `doctor`'s skills verdict is a local hash comparison rather
than an `ls-remote` plus a clone per layer.
**Constraints**: no new runtime dependency; destination paths byte-identical to the
current release; manifests written by earlier versions must not crash `doctor`; and
minimal-complexity bias.
**Scale/Scope**: one bundled tree (25 skills, 23 commands, 2 runtime dirs, 1 tracker,
1 config), 4 layers, ~4 commands touched in a ~1900-line `cli.py`.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repo has no `.specify/memory/constitution.md`. The gates below are substituted
from its own documented conventions — the rationale comments in `pyproject.toml`
and the checks CI actually runs. The substitution is recorded in Complexity Tracking.

- [x] **Validation plan exists**: `pytest` + `ruff check` + `mypy` all run, plus a
      new wheel-build job asserting bundled content and the `.sh` exec bit
      (FR-005). Named per surface in [quickstart.md](./quickstart.md) §2, §3, §6.
- [x] **Complexity is justified**: one new module, `wfctl/_bundle.py`, for two call
      sites — justified in [research.md](./research.md) §3 and logged below. No new
      dependency, no new abstraction over the target lists, no config surface.
- [x] **Lint scope unchanged**: no new ruff rules enabled; the pin stays
      `>=0.15,<0.16`. Import sorting stays deferred to #14 rather than riding along
      with a diff that moves imports.
- [x] **Typed at the boundary**: new functions carry annotations
      (`disallow_untyped_defs = true`, `files = ["wfctl"]`). No `strict` opt-in,
      no `Any`-shaped manifest work beyond what already exists.
- [x] **The suite does not reach the network**: this feature removes the last
      unstubbed call (`test_install_skills_bad_repo_exits_one`) and the
      `GIT_TERMINAL_PROMPT: "0"` guard at `ci.yml:70-71` that existed for it.
- [x] **No user-reachable override is introduced**: the bundle root is a
      monkeypatched module constant, deliberately not a `WFCTL_BUNDLE_ROOT`
      environment variable ([research.md](./research.md) §4) — an override would
      reintroduce the second source of truth this feature exists to remove.

**Post-Phase-1 re-check**: still passing. Phase 1 added no entity, no dependency
and no configuration; the manifest gained two scalar fields and lost three.

## Project Structure

### Documentation (this feature)

Spec artifacts live outside the repo, resolved via `wfctl feature-paths`:

```text
wfctl-specs/43-vendor-wf-skills/
├── spec.md              # /speckit.specify output, + /speckit.clarify record
├── design.md            # brainstorm record (pre-existing)
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli.md           # Phase 1 output — the command surface is the contract
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
wfctl/
├── cli.py               # target lists (630-682), install-skills, install-config, doctor
├── _bundle.py           # NEW — BUNDLE_ROOT + content_hash(root)
├── _manifest.py         # docstring line 9 updated: layers no longer pin a commit
├── agents/              # NEW — vendored, committed
│   ├── skills/          # 25 dirs
│   ├── commands/        # 23 files
│   ├── trackers/github.json
│   └── configs/workmux/
└── specify/             # NEW — vendored, committed
    ├── scripts/bash/    # mode 755, load-bearing
    └── templates/

tests/
├── test_install_skills.py   # _make_wf_skills_repo → plain-dir builder
├── test_install_config.py   # _make_wf_skills_repo_with_config → same
├── test_tracker.py          # _make_wf_skills_repo_with_tracker → same
└── test_bundle.py           # NEW — content_hash properties

pyproject.toml           # + [tool.setuptools.package-data]
.github/workflows/ci.yml # + wheel job; − GIT_TERMINAL_PROMPT env block
README.md                # 11 lines describing clone-and-pin provenance
```

**Documentation debt** — `README.md` describes the mechanism being removed, so
it goes stale silently (no test covers prose). The specific lines:

| Lines | Now says | Becomes |
| --- | --- | --- |
| 115 | manifest is "pinned commit + backups" | version + content hash + backups |
| 144, 146, 148 | command table: "Clone wf-skills…", "…from wf-skills", "against upstream for drift" | bundled source, local drift check |
| 187, 197, 202 | `✓ Installed from …wf-skills@main`, "Defaults to `aamarin/wf-skills@main`" | `✓ Installed from wfctl 0.15.0`; no default to state |
| 246-248, 255-256 | doctor "pinned commit vs upstream tip" + a SHA-to-SHA example with a diff stat | version/hash comparison + the four new states |
| 260-264 | "pins the resolved commit SHA (not just the `--ref` name)" | pins the wfctl version and content hash; drop "or a repo is unreachable" from the exit-code sentence |
| 268-269, 275 | install-config "sourced from the same wf-skills repo" + its provenance line | sourced from the wheel |

**Structure Decision**: single package, no `src/` layout — matching what exists.
The bundled trees are package data *inside* `wfctl/`, which is what makes
`package-data` able to see them and `importlib.resources.files("wfctl")` able to
resolve them. `.agents/` and `.specify/` at the repo root stay gitignored: after
this change they are this repo's own `install-skills` output, a copy of the
committed bundle rather than its source ([research.md](./research.md) §7).

The dot-strip is load-bearing twice over. `.gitignore:12-14` lists `.agents/` and
`.specify/` unanchored, so those patterns match at *any* depth — a vendored
`wfctl/.agents/` would have been silently untracked, and T002's exec-bit staging
would have had nothing to stage. `wfctl/agents/` is unaffected. setuptools was
the reason to strip the dots; git independently requires it.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from repo conventions | `.specify/memory/constitution.md` does not exist; the template requires the substitution be recorded rather than left implicit | Leaving the two generic gates alone would make the check decorative; copying another project's constitution would make it false |
| New module `wfctl/_bundle.py` | Two call sites (`install-skills`, `doctor`) plus a hash worth testing without importing typer, rich and every command — the same argument `_manifest.py` documents for itself | Inlining in `cli.py` is the smaller diff but drags the whole CLI into the one unit test with real logic in it |
| Whole-tree hash accepts over-reporting | `.agents/trackers/github.json` is copied inline (`cli.py:1196-1210`) and belongs to no target list, so per-layer hashing has a silent-miss mode | Per-layer hashing is more precise but its failure is invisible; whole-tree's failure is noise carrying a correct remedy (`wfctl install-skills`) |
| New CI job that builds and installs a wheel | The suite runs against the source tree, where the bundle and the exec bit are present whether or not the wheel ships them — a green suite proves nothing about the shipped artifact | Trusting `package-data` globs and the [research.md](./research.md) §1 mode finding leaves both failures undetectable until a user hits `Permission denied` |
