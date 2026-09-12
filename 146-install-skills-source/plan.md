# Implementation Plan: install-skills source

**Branch**: `146-install-skills-source` | **Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `<spec_root>/146-install-skills-source/spec.md`

## Summary

`install-skills` gains an optional source location; the manifest records it per
layer; `doctor` compares installed content against the recorded source rather
than against the running wheel. Absence of the recorded value means "the default"
and preserves today's behavior exactly.

The technical approach is small and local. `_bundle` gains one public function
that turns a user-supplied path into a validated bundle root. `install_skills_cmd`
threads that root through the two places it already reads `_bundle.BUNDLE_ROOT`
for content, and writes one extra key in the layer entry it already builds.
`doctor_cmd` replaces its single pre-computed bundle digest with a small
per-source cache and adds three branches inside a loop it already runs per layer.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer`, `rich` — both already present. This feature
adds none.
**Storage**: `.wf-skills-manifest.json`, per repo, gitignored. One new optional
string field per layer entry.
**Testing**: `uv run --frozen --extra dev pytest -q`, plus `ruff` and `mypy` as
recorded in `wfctl.json`. Unit coverage for source resolution, record shape, and
each of `doctor`'s four states; the end-to-end path is `quickstart.md`, which the
suite cannot perform.
**Target Platform**: Local developer machines, macOS and Linux. Windows is a
stated concern for the mirrored skills but not touched here.
**Project Type**: Single-project CLI.
**Performance Goals**: None new. `doctor` may now hash up to one tree per distinct
recorded source instead of exactly one; in practice that is one or two, over a
few hundred small files, at session start.
**Constraints**: No new dependencies. `ruff` rule set stays `E4,E7,E9,F` (#14).
`mypy` with `disallow_untyped_defs`; annotate new functions. Minimal-complexity
bias.
**Scale/Scope**: Two modules (`_bundle.py`, `cli.py`), one shipped skill's prose
(`start-session`), and their tests.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design._

This repo has no `.specify/memory/constitution.md`. Gates below are substituted
from its own documented conventions — `AGENTS.md` and the accepted records under
`docs/architecture/` — and the substitution is recorded in Complexity Tracking.

- [x] **Validation plan exists.** The three recorded `verify` commands, named in
      Technical Context, plus per-state unit coverage and `quickstart.md` for the
      end-to-end path the suite cannot reach.
- [x] **Complexity is justified.** No new dependency, no new module, no new
      abstraction. One public function, one optional field, one optional flag.
      The rejected simpler path — a flag with no recording — is rejected in the
      architecture record for a stated reason, not a preference.
- [x] **Ownership is stated.** The manifest owns *"which bundle produced this
      install, and what did it hash to?"*. `doctor` cannot compute it: two
      installs from different sources can be byte-identical, so nothing in the
      installed files distinguishes them. Recorded at
      `docs/architecture/drift-is-measured-against-the-recorded-source.md`
      (status `proposed`).

**Repo-specific gates:**

- [x] **`layer-model` respected.** Source is committed package data under
      `wfctl/agents/` and `wfctl/specify/`; every dotted root directory is
      generated and gitignored. This feature changes where those trees are *read
      from*, never what is authoritative.
- [x] **`session-state-is-re-derived` respected.** The comparison is computed at
      read time on every `doctor` run. The manifest stores only what
      re-derivation cannot reach — the caller's choice at the moment of copying.
- [x] **`install-modes` respected.** No change to how a layer is chosen or
      merged; the source is orthogonal to the mode.
- [x] **Release discipline.** No `version` bump in `pyproject.toml` — that ships
      a release, and this is not one.
- [x] **`the-underscore-is-the-module-contract`** (proposed, not in force) is
      honored anyway: the new seam is a public name, so acceptance of that record
      would not force a rename.

## Project Structure

### Documentation (this feature)

```text
<spec_root>/146-install-skills-source/
├── plan.md              # This file
├── spec.md              # /speckit.specify + /speckit.clarify output
├── design.md            # /speckit.brainstorm output
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli.md           # Phase 1 output
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit.tasks output — not created here
```

### Source Code (repository root)

```text
wfctl/
├── _bundle.py           # + resolve_root(path) -> Path   (new public seam)
├── cli.py               # install_skills_cmd: --from, threading, record write,
│                        #   FR-015 replacement notice
│                        # doctor_cmd: per-source digest cache, three branches,
│                        #   remedy line carries --from
└── agents/skills/start-session/SKILL.md
                         # prose: the printed command governs over the examples

tests/
├── test_bundle.py       # resolve_root: valid, nested, neither
└── test_install_skills.py
                         # record shape, one-shot semantics, replacement notice
                         #   survives --yes, bad source leaves repo untouched,
                         #   and doctor's four states — this is where doctor's
                         #   skills-drift assertions already live
                         #   (test_doctor_version.py covers only the version check)
```

**Structure Decision**: Single project, existing layout, no new modules. The two
files that change are the two that already own the halves of this question —
`_bundle` owns where the bundle is, `cli` owns what is installed and what is
reported. `docs/architecture/` gains the record already written.

## Phase 0 — Research

Complete. See [research.md](./research.md). Six unknowns resolved:

| | Question | Decision |
|---|---|---|
| R1 | Where the source is recorded | Per-layer, beside `content_hash` |
| R2 | How "the default" is represented | Key absent — unambiguous, no migration |
| R3 | The seam in `_bundle` | Public `resolve_root(path)` |
| R4 | `doctor`'s branching | Per-source digest cache, three branches in the existing loop |
| R5 | Backward compatibility | None needed — see R2 |
| R6 | Path handling | Resolve absolute at install, validate before copying |

Also verified: FR-012 holds with no code, because `--prune` already diffs against
what was just installed.

## Phase 1 — Design & Contracts

Complete.

- [data-model.md](./data-model.md) — the manifest layer entry and its one new
  optional field, with the rules that make absence meaningful.
- [contracts/cli.md](./contracts/cli.md) — the flag, its resolution and failure
  behavior, `doctor`'s four states with exit codes, and the remedy line's
  requirement to carry the source.
- [quickstart.md](./quickstart.md) — the seven-step end-to-end exercise,
  including the two steps that fail if FR-008 or FR-015 are wrong.

### Post-design Constitution re-check

Unchanged. The design added no abstraction, no dependency, and no module. The one
place it could have grown — `doctor` needing a digest per source instead of one —
resolves to a dict keyed on resolved path, not a new type.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from `AGENTS.md` and `docs/architecture/` | The repo has no `.specify/memory/constitution.md`. The template requires recording the substitution rather than leaving gates with no source. | Borrowing another project's constitution would make the gates false; leaving them blank would make them decorative. |
| `drift-is-measured-against-the-recorded-source` is `proposed`, not `accepted` | `wfctl arch context` lists only accepted records, so this plan's ownership gate cites a record that is not yet in force. | Flipping it to `accepted` unilaterally. Acceptance is the human's call, made at PR review; the architecture-decisions skill is explicit that `proposed` is what to write while agreement is outstanding. |
