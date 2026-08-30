# Tasks: Architecture Knowledge Lifecycle

**Input**: Design documents from `specs/86-architecture-knowledge-lifecycle/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Resolution order, status parsing, link validation, supersession, and
the in-force projection are critical-path logic and carry automated tests. Skill
content under `wfctl/agents/` cannot be verified by the suite — `AGENTS.md` states
the suite checks skills ship and cross-reference, not that they work — so those
tasks carry named manual verification instead.

**Revision note**: Phases are aligned to stackable PR boundaries. Phase 2 holds
the **complete** `wfctl/_arch.py` module, so later phases consume it without
editing it — that is what lets Phase 3 and Phase 4 run in parallel off the same
base without colliding. Task IDs were renumbered; do not cross-reference an
earlier revision.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US4, mapping to spec.md user stories

## Path Conventions

Single project. Source in `wfctl/`, tests in `tests/`, both at repository root.
Skill source is `wfctl/agents/skills/` — never `.agents/skills/`, which is
gitignored install output.

Verified existing test files: `tests/test_skill_cross_references.py`,
`tests/test_pipeline_commands.py`, `tests/test_promote.py`,
`tests/test_agent_session.py`, `tests/test_remaining_commands.py`. There is no
`test_skills.py` or `test_pipeline.py`.

---

## Phase 1: Setup

- [X] T001 Record the pre-change baseline by running `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/`; all three must be green so any later failure is attributable to this work

---

## Phase 2: Foundational — the complete record module → **PR 1**, base `main`

**Purpose**: Ship `wfctl/_arch.py` finished — parse, validate, supersede,
project — plus root resolution and the retirement of the orphaned promote path.
Nothing consumes it yet.

**Why the whole module lands here**: if later phases extended `_arch.py`, they
would edit the same file and could not run in parallel off this base. Ending this
phase with the module complete is what makes Phase 3 and Phase 4 independent.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Write failing tests for architecture root resolution order in `tests/test_arch_root.py`, covering `WFCTL_ARCH_DIR`, this repo's manifest, the main checkout's manifest, the `docs/architecture` default, a root outside the working tree, and a root that does not yet exist
- [X] T003 Implement `arch_root()` and `arch_root_declaration()` in `wfctl/_paths.py`, mirroring `spec_root()` at lines 233-264 including its rule that resolution neither checks existence nor creates the directory; verify with `tests/test_arch_root.py`
- [X] T004 [P] Write failing tests for record parsing in `tests/test_arch_records.py`, covering each of the five status values, an absent `status`, an unrecognised `status`, a missing frontmatter delimiter, and `supersedes` extraction
- [X] T005 Implement record parsing in new module `wfctl/_arch.py` as a frontmatter line scan mirroring `_skill_deployment` (`wfctl/cli.py:786-799`), defaulting an absent or unrecognised status to **excluded**, not to the common case; verify with `tests/test_arch_records.py`
- [X] T006 Write failing tests for record link validation in `tests/test_arch_records.py`: a `supersedes` naming no existing record (VR-003, error), a `superseded` record no successor points at (VR-002, warning), and two records naming the same `supersedes` target (VR-004, error — also a declared spec edge case)
- [X] T007 Implement link validation in `wfctl/_arch.py` per VR-002, VR-003 and VR-004 in `data-model.md`; verify with `tests/test_arch_records.py` (T006)
- [X] T008 Write a failing test asserting supersession changes only `status` and appends one `Log` line, leaving the record body byte-identical, in `tests/test_arch_records.py`
- [X] T009 Implement supersession handling in `wfctl/_arch.py` so a predecessor's body is never rewritten; verify with `tests/test_arch_records.py` (T008)
- [X] T010 Write failing tests for the in-force projection in `tests/test_arch_records.py`: one record per status asserting only `accepted` is projected, an empty root returning an empty set, and an unparseable record excluded and named rather than dropped silently
- [X] T011 Write a failing test asserting projection ordering is stable across runs, in `tests/test_arch_records.py`
- [X] T012 Implement the in-force filter in `wfctl/_arch.py`, projecting `accepted` only and counting the excluded by status; verify with `tests/test_arch_records.py` (T010, T011)
- [X] T013 Add the `arch-root` command to `wfctl/cli.py`, printing the resolved root and warning when it falls outside the working tree per `contracts/cli-commands.md`; verify with `tests/test_arch_root.py`
- [X] T014 [P] Remove the orphaned promotion path: the `promote` command in `wfctl/cli.py`, `promote()` in `wfctl/_session.py`, the `WFCTL_CANDIDATES_FILE` row in `README.md`, all of `tests/test_promote.py`, and the promote cases in `tests/test_agent_session.py`; verify with `grep -rn "memory-candidates\|WFCTL_CANDIDATES_FILE\|promote" wfctl/ tests/ README.md` returning no hits and `uv run pytest -q` green
- [X] T015 Validate Phase 2 with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/ && wfctl doctor` — **PR 1 merge gate**

**Checkpoint**: `_arch.py` is complete and tested. No later phase edits it.

---

## Phase 3: User Story 1 - A decision survives the session (Priority: P1) 🎯 MVP → **PR 2**, base PR 1

**Goal**: The level-2 design gate writes a durable record carrying the ownership
statement, instead of prose that must be copied into one.

**Independent Test**: Run a design session reaching an ownership decision; confirm
a record exists under the resolved root carrying the decision, rejected
alternatives, and a statement of which side owns the truth and why the other
cannot compute it.

**Verification**:

- Automated: `tests/test_skill_cross_references.py` for packaging and cross-references
- Manual: `wfctl install-skills`, then a live design session reaching a level-2 answer
- Evidence: a file under `docs/architecture/` whose `Owns truth` section names both the owning side and why the other cannot compute it

**File isolation**: this phase touches skills and new record files only. It does
not edit `wfctl/_arch.py` or `wfctl/cli.py`, so it runs parallel to Phase 4.

- [X] T016 [P] [US1] Write a failing test asserting the new skill ships in the bundle and its cross-references resolve, in `tests/test_skill_cross_references.py`
- [X] T017 [P] [US1] Create the record template at `wfctl/agents/skills/architecture-decisions/record-template.md`, matching `contracts/record-format.md`; verify by diffing its section list against that contract
- [X] T018 [US1] Create the ADR skill at `wfctl/agents/skills/architecture-decisions/SKILL.md` in MADR-simple form plus the ownership field, with slug-only identity and no sequence number; verify with `tests/test_skill_cross_references.py`
- [X] T019 [US1] Wire the level-2 gate in `wfctl/agents/skills/design-levels/SKILL.md` so its answer writes the record directly rather than a `design.md` section; verify with `tests/test_skill_cross_references.py`
- [X] T020 [US1] Seed exactly two records under `docs/architecture/` for decisions currently contested, including the self-certification decision from #69; verify each carries a non-empty `Owns truth` per VR-006 and parses via `wfctl arch-root` resolution
- [X] T021 [US1] Manually verify the capture path: run `wfctl install-skills`, then a design session reaching an ownership decision, and confirm a record is produced without being asked for
- [X] T022 [US1] Validate Phase 3 with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/ && wfctl doctor` — **PR 2 merge gate**

**Checkpoint**: Decisions are being captured. Nothing reads them yet.

---

## Phase 4: User Stories 2 and 3 - Consumption and enforcement (Priority: P2, P3) → **PR 3**, base PR 1

**Goal**: Accepted records reach the agent at session start, and the design step
refuses to advance without a record or an explicit declaration.

**Independent Test**: With one record in each of the five statuses, confirm
`wfctl arch context` presents exactly the accepted one. Separately, attempt to
advance past design with no record and confirm refusal.

**Verification**:

- Automated: `tests/test_remaining_commands.py` for command rendering; `tests/test_pipeline_commands.py` for the advance check
- Manual: `wfctl install-skills`, then `/start-session` shows the in-force set; a declaration appears in `git diff`
- Evidence: output matching `contracts/cli-commands.md`

**File isolation**: consumes `wfctl/_arch.py` without editing it. Touches
`wfctl/cli.py`, `wfctl/_pipeline.py`, `start-session`, and two existing test
files — all disjoint from Phase 3.

- [X] T023 [P] [US2] Write a failing test for `arch context` rendering in `tests/test_remaining_commands.py`, covering the populated, empty, and unparseable-record cases, pinning `NO_COLOR`
- [X] T024 [US2] Add the `arch context` command to `wfctl/cli.py`, calling the Phase 2 filter and exiting 0 in the empty and unparseable cases per `contracts/cli-commands.md`; verify with `tests/test_remaining_commands.py` (T023)
- [X] T025 [US2] Add a step to `wfctl/agents/skills/start-session/SKILL.md` loading the in-force set alongside the existing `wfctl start` and `wfctl doctor` calls; verify with `tests/test_skill_cross_references.py`
- [X] T026 [US2] Manually verify delivery: `wfctl install-skills`, then `/start-session`, confirming the in-force set appears in the session report
- [X] T027 [P] [US3] Write failing tests in `tests/test_pipeline_commands.py` for the design-step check: refusal when no record and no declaration, advance when a record exists, and advance when a declaration exists
- [X] T028 [US3] Implement the design-step advance check in `wfctl/_pipeline.py`, keeping it out of `doctor`, which explicitly refuses checks describing what the user has not done; verify with `tests/test_pipeline_commands.py` (T027)
- [X] T029 [US3] Add `arch none --reason` to `wfctl/cli.py`, persisting the declaration where it lands in the change under review and recording it without verifying it per FR-010a; verify with `tests/test_pipeline_commands.py`
- [X] T030 [US3] Manually verify the declaration is reviewable: make a trivial change, declare no boundary, and confirm the declaration appears in `git diff` rather than only in state
- [X] T031 Record the `arch context` falsification test from `plan.md` in the command's docstring in `wfctl/cli.py`, in the style of `doctor`'s scope statement, so a later reader can retire the command rather than inherit it; verify with `wfctl arch context --help`
- [X] T032 Validate Phase 4 with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/ && wfctl doctor` — **PR 3 merge gate**

**Checkpoint**: Agents read the in-force set. Relocation in Phase 5 is now safe.

---

## Phase 5: User Story 4 - Knowledge lives in exactly one place (Priority: P3) → **PR 4**, base PR 3

**Goal**: Content misplaced in `AGENTS.md` moves to where the placement rule puts
it, and the placement rule itself becomes durable.

**⚠️ Depends on PR 3 being merged.** `AGENTS.md` is loaded automatically every
session; `docs/architecture/` is loaded by nobody until the projection ships.

**Independent Test**: In a fresh session, ask an agent to fix a typo in a skill.
It must edit `wfctl/agents/skills/…`, not `.agents/skills/…`.

**Verification**:

- Automated: `tests/test_arch_records.py` asserting the relocated records parse and project
- Manual: SC-004 — three of three fresh-session trials edit the source tree
- Evidence: `grep` finds relocated content absent from `AGENTS.md` and present in `wfctl arch context`

- [X] T033 [P] [US4] Write the layer-model record to `docs/architecture/layer-model.md` per `contracts/record-format.md`; verify it appears in `wfctl arch context`
- [X] T034 [P] [US4] Write the managed-mirror-vs-seed-once record to `docs/architecture/install-modes.md`; verify it appears in `wfctl arch context`
- [X] T035 [P] [US4] Write the committed-config constraint record to `docs/architecture/no-hardcoded-agent.md`; verify it appears in `wfctl arch context`
- [X] T036 [P] [US4] Write the vendor-rather-than-fork record to `docs/architecture/vendor-upstream-skills.md`, naming which skills are vendored — `i-have-adhd` is the only one today. The per-file fact lives here rather than in the skill because `AGENTS.md:83` forbids editing a vendored file and an upstream pull would overwrite it; verify it appears in `wfctl arch context` and that no vendored file was modified
- [X] T037 [P] [US4] Write the placement-rule record to `docs/architecture/knowledge-placement.md`, stating the rule and its exception: a fact about one file belongs to that file **when the project controls that file's contents**; when it does not, the fact belongs to the record governing its class. Satisfies FR-012's requirement that the rule be *stated*, not merely applied; verify it appears in `wfctl arch context`
- [X] T038 [US4] Remove the relocated content from `AGENTS.md` and keep `CLAUDE.md` in step; verify with `grep -n "layer model\|managed mirror\|seed-once\|i-have-adhd" AGENTS.md CLAUDE.md` returning no hits
- [X] T039 [US4] Manually verify SC-004: in three fresh sessions, ask for a typo fix in a skill and confirm all three edit `wfctl/agents/skills/…` rather than the gitignored `.agents/skills/…`
- [X] T040 [P] Document `arch-root` and `arch context` in `README.md`, including a `WFCTL_ARCH_DIR` row alongside the existing `WFCTL_SPEC_DIR` entry; verify by reading the rendered section
- [X] T041 Run every `quickstart.md` scenario end to end, and verify SC-005 by opening one seed record and confirming its rationale is complete without consulting `git log`; verify each scenario produces the output shown in `quickstart.md`
- [X] T042 Validate the whole feature with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/ && wfctl doctor` — **PR 4 final gate**

**Checkpoint**: All four stories functional. No duplication left to keep in sync.

---

## Dependencies & Execution Order

### PR stack

```
main
 └── PR1  Phase 1–2   T001–T015   complete _arch.py, arch-root, delete promote
      ├── PR2  Phase 3   T016–T022   ADR skill, level-2 gate, 2 seed records
      └── PR3  Phase 4   T023–T032   arch context, arch none, advance check
           └── PR4  Phase 5   T033–T042   relocation, placement record, docs
```

PR 2 and PR 3 both base on PR 1 and touch **disjoint file sets**, so they run in
parallel without conflict. That is why Phase 2 ships `_arch.py` complete rather
than letting later phases extend it.

### The one dependency that is not negotiable

```
PR3 (projection)  ──must merge before──►  PR4 (relocation)
```

Relocating the layer model before anything reads records means an agent asked to
fix a typo edits `.agents/skills/…` — which reads correctly, passes the suite, and
ships nothing, because `.agents/` is gitignored install output. Nothing errors.

### Sequencing note on US3

US3 sits in PR 3 rather than waiting on US1. Its tests build their own record
fixtures, so it has no code dependency on PR 2. The product-level observation —
that there is nothing to check for until records are being written — is a
measurement concern, tracked by SC-001, not a build order.

### Parallel Opportunities

- T002 ‖ T004 ‖ T014 — different files, and T014 only deletes
- T016 ‖ T017 within PR 2
- T023 ‖ T027 within PR 3
- T033 ‖ T034 ‖ T035 ‖ T036 ‖ T037 — five independent new record files
- **PR 2 ‖ PR 3** — the whole of Phase 3 alongside the whole of Phase 4

### Within Phase 2

Tests before implementation, and `_arch.py` grows in one direction: parse (T005)
→ validate (T007) → supersede (T009) → project (T012). Each step's tests are
written first and must fail.

---

## Implementation Strategy

### MVP (through PR 2)

1. PR 1 — the record module, complete
2. PR 2 — capture wired to the design gate
3. **Stop and measure against SC-001**: do the next three features produce a
   record or an explicit no-boundary declaration? Baseline is zero of eleven.
4. That measurement decides whether the advance check in PR 3 is worth keeping.

### Incremental Delivery

1. PR 1 → records can be located, read, validated, superseded, projected
2. PR 2 → decisions are captured (MVP)
3. PR 3 → agents read them; enforcement lands; PR 4 becomes safe
4. PR 4 → duplication removed, placement rule made durable

---

## Notes

- Skill source is `wfctl/agents/skills/`. Editing `.agents/skills/` changes
  nothing that ships and is the failure US4 exists to prevent.
- `i-have-adhd` is vendored and must not be edited (`AGENTS.md:83`). The fact
  that it is vendored lives in the vendoring record, not in the file.
- Tests asserting on console output must pin `NO_COLOR`; rich colorizes by
  terminal otherwise and assertions become machine-dependent.
- Do not widen the ruff rule set as a drive-by. Annotate new functions for
  `disallow_untyped_defs`.
- Do not bump `version` in `pyproject.toml` — that ships a release on `main`.
