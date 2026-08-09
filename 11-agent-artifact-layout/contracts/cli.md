# Contract: paths and CLI surface

**Branch**: `11-agent-artifact-layout` | **Date**: 2026-08-05

This feature's external interface is a set of filesystem paths shared between two
repositories, plus one CLI behaviour change. Both are contracts because a
consumer repo observes them directly.

## Path contract

Producers and consumers agree on these locations. Anything reading or writing
outside this table is a defect.

| Path | Producer | Consumers | Status |
| --- | --- | --- | --- |
| `specs/<branch>/design.md` | `/brainstorm` | `speckit-specify`, `_pipeline.py`, `_archive.py` | **new** |
| `specs/<branch>/brief.md` | `/speckit.brief` | scoped agent | **moved** |
| `specs/<branch>/escalation.md` | scoped agent | human | **moved + renamed** |
| `AGENTS.md` | repository maintainer | `/brainstorm` | **new** |
| `.agent/**` | — | — | **removed** |

### Invariants

1. **One writer per path.** Verifiable by search; FR-009.
2. **`specs/<branch>/` is created on demand.** `/brainstorm` runs before any
   other pipeline step and must `mkdir -p` rather than assume; FR-012.
3. **`AGENTS.md` is read-if-present.** Absence is legal and silent; FR-005. No
   component creates it.
4. **No component reads `.agent/`.** Not as a fallback, not for migration;
   FR-013.

### Breaking change

Consumer repos that have installed one component but not the other observe a
stalled pipeline: the step inference cannot see a design document written to the
path it does not read. This is deliberate — see the CLI contract below and
research R1.

## CLI contract

### `wfctl doctor` — new diagnostic

**Given** a repository containing a `.agent/` directory,
**When** `wfctl doctor` runs,
**Then** it reports that a component writing the superseded path is installed,
and names the action that resolves it.

Presence of `.agent/` is the trigger, not a version comparison. It is positive
evidence that some installed component still writes there, it needs no manifest
schema change, and it self-clears permanently once every component is current.

Severity is `⚠` (yellow) — the repository still functions, but its pipeline
state will be wrong. It joins the existing freshness lines rather than replacing
them; `_check_wfctl_version` and the manifest-commit check both already report
skew and name their own corrective actions (research R1).

### `wfctl archive-story` — unchanged surface, changed mapping

Arguments, exit codes, and output format are unchanged. The design document
moves from a special-cased worktree-relative constant into the ordinary spec-dir
map, so it is discovered the same way as every other artifact.

**Given** a branch archived at any pipeline stage,
**When** the archive is produced,
**Then** the numbered sequence is contiguous from `1-design.md` and no file
appears under `extra/` that the map should have named.

### `wfctl start` / `wfctl status` — unchanged surface, corrected inference

**Given** a branch whose design document exists at the new path,
**When** step inference runs,
**Then** brainstorm reports complete.

This also repairs a latent defect: `_infer_steps` returns all-incomplete when the
spec directory is absent (`_pipeline.py:55-56`), so the old check against
`.agent/spec.md` was unreachable during exactly the phase it existed to serve.
Moving the design document inside the spec directory makes it reachable —
conditional on invariant 2 above.

## Out of contract

- The internal layout of the archive's `extra/` directory.
- Whether `AGENTS.md` carries a fenced managed region. This feature neither
  creates nor requires one; a later mechanism may add it and must then handle a
  file that has none.
- The session state directory's contents, which this feature does not touch.
