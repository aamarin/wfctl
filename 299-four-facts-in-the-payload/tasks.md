# Tasks: four facts in the payload

**Feature**: #299 | **Branch**: `299-four-facts-in-the-payload`
**Input**: `spec.md`, `plan.md`, `data-model.md`, `contracts/facts-payload.md`

## Format: `[ID] [P?] [Story] Description`

`[P]` marks tasks that touch no file another `[P]` task in the same phase
touches. `[US1]`/`[US2]`/`[US3]` name the user story the task serves.

## Path Conventions

Single project. Source under `wfctl/`, tests under `tests/`. Records are already
committed under `docs/architecture/`.

## Phase 1: Setup

- [x] T001 Confirm the baseline is green before touching anything: `uv run pytest
      -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`. A failure here
      belongs to the tree, not to this change, and finding it later costs a
      bisect.

## Phase 2: Foundational (blocking prerequisites)

- [x] T002 Add `FactValue` and `Fact` to `wfctl/_predicates.py`, beside `State`
      and `Verdict`, with the comment saying why the vocabulary is distinct from
      both (`data-model.md` § FactValue).
- [x] T003 Move the trunk correction of the notify grant out of
      `cli.status_cmd` and into `_pipeline.build_report`, so `notify` and
      `notify_source` on the report are already corrected. `status_cmd` renders
      the corrected values rather than computing them. Behaviour of the existing
      notify line is unchanged; `tests/test_notify_status.py` must pass
      untouched, which is the check that it is.

## Phase 3: User Story 1 — a reader can tell which question is unanswered (P1) 🎯 MVP

### Tests for User Story 1

- [x] T004 [US1] `tests/test_four_facts.py`: a branch whose tasks are closed and
      whose definition of done passed, with a `proposed` record on the branch,
      renders `architecture accepted` as unmet in `wfctl status` console output,
      naming the record. `NO_COLOR` pinned.
- [x] T005 [US1] The same fixture after the record's status is `accepted`
      produces different console output, with that fact met. This pair is the
      issue, written as an assertion — a test that reads only `--json` does not
      satisfy it.
- [x] T006 [US1] A branch to which nobody granted outward-facing authority
      renders `outward actions authorized` as unmet, and the detail distinguishes
      "nobody granted it" from "the stored answer could not be read".

### Implementation for User Story 1

- [x] T007 [US1] `_predicates.fact_architecture_accepted(repo_root)` —
      `records_on_this_branch` intersected with `load_records`' one-level glob;
      unmet when any touched record is `proposed` or carries no recognised
      status; `n/a` when the intersection is empty (`data-model.md` § 3, FR-009,
      FR-010).
- [x] T008 [US1] `_predicates.fact_integration_authorized(...)` — reads the
      corrected grant from T003; `n/a` on the trunk, unmet through
      `blocks("inconclusive", "human")` when git cannot say, unmet keyed on
      `notify_source` otherwise (FR-012, FR-013).
- [x] T009 [US1] `_predicates.facts(...)` returning the four in fixed order, and
      `PipelineReport.facts` filled by `build_report` (FR-001, FR-004).
- [x] T010 [US1] `cli._FACT_GLYPH` and the console block between the step table
      and `next:`, rendered in every state, details `escape()`d
      (`contracts/facts-payload.md`, FR-006).

## Phase 4: User Story 2 — a consumer can ask each question precisely (P2)

### Tests for User Story 2

- [x] T011 [US2] `facts` is present in `wfctl status --json` with exactly four
      entries in the fixed order, on every input including no feature directory
      and including the trunk (contract invariants 1 and 2).
- [x] T012 [US2] `tests/pipeline_payload_snapshot.json` needs no regeneration —
      assert the file is unchanged by running the snapshot test as it stands.
      Its passing is the evidence that no step verdict moved (SC-004).

### Implementation for User Story 2

- [x] T013 [US2] Serialize `facts` in `cli.status_cmd`'s `--json` branch beside
      `steps`, as a list of dicts (FR-007).
- [x] T014 [P] [US2] `_predicates.fact_artifacts_written(ev)` from `Evidence`'s
      three texts; unmet with the missing names, and unmet naming the absent spec
      dir when none resolved (`data-model.md` § 1, FR-003).
- [x] T015 [P] [US2] `_predicates.fact_definition_of_done(repo_root)` — `n/a`
      from `load_config` returning no commands and no errors, unmet from
      `verification_block`'s reason unchanged, met with the record's sha
      (FR-011).

## Phase 5: User Story 3 — a question that does not arise is not a blocker (P3)

### Tests for User Story 3

- [x] T016 [P] [US3] A branch that touched no file under the arch root reports
      `architecture accepted` as `n/a`, not unmet (FR-010).
- [x] T017 [P] [US3] A repository whose `wfctl.json` declares no verify commands
      reports `definition of done` as `n/a`, distinguishable in the payload from
      one that ran and passed (FR-011).
- [x] T018 [P] [US3] The trunk reports `outward actions authorized` as `n/a`
      (FR-012).
- [x] T019 [P] [US3] A malformed definition of done reports unmet, not `n/a` —
      the edge case that separates "no question" from "the answer is broken".

## Phase 6: Polish & cross-cutting

- [x] T020 Add the one cross-reference in `_predicates.py`'s rung commentary
      where it names rungs 6 and 7, saying which facts those correspond to and
      that the other five do not map (spec § Clarifications, Q3). Do not rename
      the rungs.
- [x] T021 Structural check that no `Fact` is derived from a `_PipelineStep`:
      the four derivations take `Evidence`, `Path` and the grant, and none takes
      a step or a state (FR-003, contract invariant 5).
- [x] T022 Run the full definition of done: `uv run pytest -q`, `uv run ruff
      check wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl doctor`.
- [x] T024 The four requirements stated as prohibitions, each as an assertion
      rather than as prose nobody checks: every fact's `detail` is non-empty in
      every state (FR-005); the set of pipeline step state names is still exactly
      the four (FR-008); `blocks(verdict, source)` has the same behaviour for all
      eight verdict/source pairs (FR-014); and `cli` composes no fact detail — the
      console renders `f.detail` unchanged (FR-015). Without these the four read
      as intentions, and `a-rule-is-expressed-as-a-check` puts them on the side
      where a violation is visible in an artifact the work already produces.
- [x] T023 Walk `quickstart.md` by hand against this repository: build both
      situations, read both outputs, confirm they differ in the console. The
      suite cannot see this; the handoff names it as the thing that matters.

## Dependencies & Execution Order

### Phase Dependencies

Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6. Phase 2 blocks
everything: T002 defines the type the four derivations return, and T003 is what
makes fact 4 answerable from the payload.

### User Story Dependencies

US1 is the MVP and stands alone — T007 through T010 deliver the reported defect.
US2 adds the machine-readable view over the same derivations. US3 adds the third
value's correctness; its tests would fail against a US1-only tree, which is why
it is a separate story rather than an edge case of the first.

### Within Each User Story

Tests before implementation in each phase. T009 depends on T007 and T008
existing; T010 depends on T009.

### Parallel Opportunities

T014 and T015 touch only their own new functions and can run alongside each
other. T016 through T019 are four independent tests in one new file and can be
written in parallel. Nothing in Phase 3 is parallel: T007 through T010 form a
chain through `_predicates.py` and `_pipeline.py` into `cli.py`.

## Logical PR Boundaries

One PR. The feature is one payload change and its two views, and the level-2
record it implements is already committed on this branch. Splitting the console
view from the payload would land a field nothing renders, which is the state the
issue was filed about.
