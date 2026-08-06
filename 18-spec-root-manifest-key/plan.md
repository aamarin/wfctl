# Implementation Plan: spec-root-manifest-key

**Branch**: `18-spec-root-manifest-key` | **Date**: 2026-08-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/18-spec-root-manifest-key/spec.md`

## Summary

Make one function decide where a repository's specs live, and let a repository
record that location. Today `resolve_spec_dir` honors `WFCTL_SPEC_DIR` while
`feature_paths_cmd` hardcodes `repo_root / "specs" / branch` when nothing exists
yet, so reads are redirectable and creates are not.

The approach: a `spec_root(repo_root)` resolver in `wfctl/_paths.py`
(`WFCTL_SPEC_DIR` → `spec_root` in `.wf-skills-manifest.json`, current repo then
main checkout → `repo_root / "specs"`), consumed by both call sites; `spec_root`
registered as a non-layer manifest key so the installer does not choke on it; a
`wfctl spec-root` command that writes the main checkout; and a `doctor` check
that reports in-repo spec directories left behind after a root is recorded.

## Technical Context

**Language/Version**: Python ≥3.11 (`pyproject.toml: requires-python`)
**Primary Dependencies**: typer ≥0.12, rich ≥13. No new dependency — the feature
uses `os.environ`, `pathlib`, `json`, and `subprocess`, all already imported by
the modules being changed.
**Storage**: `.wf-skills-manifest.json` at the repo root — the existing per-repo
config file, already read by `_load_manifest` and already carrying the non-layer
`tracker` key.
**Testing**: pytest ≥8. `tests/test_paths.py` and `tests/test_install_skills.py`
are the homes for the new cases; `tests/conftest.py` already builds real git
repos in `tmp_path`, and `tests/test_paths.py` already builds real linked
worktrees (`test_resolve_agent_dir_keys_on_main_checkout_not_worktree`,
`test_project_name_from_a_worktree`) — the worktree-inheritance test reuses that
pattern rather than mocking git.
**Target Platform**: Local developer machines (macOS, Linux); no runtime service.
**Project Type**: Single Python package (`wfctl/`) with a CLI entry point
(`wfctl = "wfctl.cli:app"`).
**Performance Goals**: None applicable. The added work is at most one extra file
read and one `git rev-parse` per invocation, on a command that already runs
several subprocesses.
**Constraints**: `wfctl/cli.py` imports `wfctl/_paths.py` at module level
(`cli.py:13`), so `_paths` must not import `cli` at module scope — the existing
lazy in-function import (`_tracker.py:129`) is the established pattern.
`feature-paths` output is `eval`'d by the shell, so nothing may be added to
stdout; diagnostics belong on stderr or in `doctor`.
**Scale/Scope**: Two production modules (`_paths.py`, `cli.py`), plus `README.md`.
Roughly 60 lines of implementation and 10 new tests.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

**No `.specify/memory/constitution.md` exists in this repository.** The installed
`plan-template.md` ships gates written for the pfms application (workspace
isolation, ZenStack policies, `.zmodel` tiers, `pnpm type-check`); none of those
surfaces exist in a standalone Python CLI. Gates below are derived from this
repository's own recorded conventions — `pyproject.toml`'s pinned-lint and
`disallow_untyped_defs` rationale, and the `ponytail:` comment convention for
deliberate simplifications.

- [x] **No new dependency**: uses stdlib plus what the touched modules already
      import.
- [x] **No new abstraction without a second caller**: one function,
      `spec_root()`, created precisely because two call sites must agree; the
      whole defect is that they currently disagree.
- [x] **Import graph unchanged**: no new module-level import into `_paths`; the
      manifest read uses the lazy in-function import already used by `_tracker`.
- [x] **Typed**: every added function carries annotations (`disallow_untyped_defs`
      is on for `wfctl/`).
- [x] **Validation named**: `pytest`, `ruff check`, `mypy` — plus the specific new
      cases listed under Validation Strategy in the spec.
- [x] **Backwards compatible by default**: a repo recording nothing resolves
      byte-identical paths (SC-004), pinned by a test.
- [x] **Deliberate shortcuts marked**: the `.git`-name guard and the
      no-existence-check decision each get a `ponytail:` comment naming the
      ceiling and the upgrade path.

Post-Phase-1 re-check: unchanged — the design added no module, no dependency, and
no abstraction beyond the single shared resolver.

## Project Structure

### Documentation (this feature)

```text
specs/18-spec-root-manifest-key/
├── plan.md              # This file
├── spec.md              # /speckit.specify + /speckit.clarify output
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli.md           # Phase 1 output — command + resolver contract
├── checklists/
│   └── requirements.md  # /speckit.specify output
└── tasks.md             # /speckit.tasks output — NOT created here
```

### Source Code (repository root)

```text
wfctl/
├── _paths.py     # + spec_root(); resolve_spec_dir() consumes it
├── cli.py        # feature_paths_cmd fallback; _NON_LAYER_KEYS;
│                 #   spec-root command; doctor co-existence check
├── _tracker.py   # unchanged — reference for the lazy-import pattern
└── _archive.py   # unchanged — follows resolve_spec_dir automatically

tests/
├── test_paths.py           # + resolver, worktree inheritance, guard, path forms
└── test_install_skills.py  # + manifest key survives install; doctor runs clean

README.md         # + the spec_root key and the spec-root command
```

**Structure Decision**: Single package, no new modules. `spec_root()` belongs in
`_paths.py` because that is where every other path decision already lives
(`get_repo_root`, `resolve_branch`, `resolve_spec_dir`, `resolve_agent_dir`), and
because `resolve_spec_dir` — its first consumer — is there. `cli.py` keeps
manifest ownership (`_load_manifest`, `_save_manifest`, `_NON_LAYER_KEYS`) since
it already has it; `_paths` reaches for it the way `_tracker` does.

## Implementation Order

Sequenced so each stage is independently verifiable, matching the spec's story
priorities.

1. **P1 — the defect** (`_paths.py`, `cli.py:352`): add `spec_root()` with the
   env → manifest(current repo) → default chain; point `resolve_spec_dir` and
   `feature_paths_cmd` at it; add `spec_root` to `_NON_LAYER_KEYS` in the same
   change, since a manifest carrying the key breaks `install-skills` without it.
   Verifiable alone: a repo with the key set writes new specs to it.
2. **P2 — worktree inheritance** (`_paths.py`): extend the manifest lookup to the
   main checkout, guarded on the git common dir being named exactly `.git`.
   Verifiable alone against a real linked worktree.
3. **P3 — the command and the diagnostic** (`cli.py`): `wfctl spec-root
   [PATH] [--unset]` writing the main checkout and reporting the file it wrote;
   `doctor` reporting recorded-root-plus-in-repo-specs co-existence (FR-014).
4. **Docs** (`README.md`): the key, the command, the precedence chain, and the
   statement that recording a root does not migrate existing specs.

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified

No violations. No new dependency, module, or abstraction; the one added function
exists to remove a duplicated decision rather than to introduce one.
