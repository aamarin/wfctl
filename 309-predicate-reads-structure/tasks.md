# Tasks: predicate reads structure

**Input**: Design documents from this feature directory
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: US1 specify · US2 plan · US3 clarify annotation

---

## Phase 1 — Foundation (blocks every story)

- [x] T001 Add `_REQUIRED_SPEC_SECTIONS` and `_REQUIRED_PLAN_SECTIONS` to
      `wfctl/_pipeline.py`, beside `_file_exists`. Ordered tuples of heading
      stems, in template order, with a comment saying why the list is wfctl's
      and not read from the template — point at
      `docs/architecture/required-sections-are-wfctls.md` rather than restating
      it.
- [x] T002 Add `_missing_sections(text, required) -> tuple[str, ...]` to
      `wfctl/_pipeline.py`. Matches `^##[ \t]+<stem>\b` per required stem,
      MULTILINE, against already-blanked text; returns the absent stems in the
      given order. The idiom is `clarify`'s existing `Clarifications` regex —
      `[ \t]` not `\s` so a bare `##` line followed by the name is not a match,
      `\b` so `## RequirementsTODO` is not one either.
- [x] T003 Read `plan.md` as text once, beside the existing `spec_md` read, and
      blank fenced and inline spans the same way. `plan-template.md` carries
      fenced blocks with `#` lines inside them, so an unblanked read is wrong
      for the same reason `spec_text` is blanked today.

**Verification**: `uv run mypy wfctl/` and `uv run ruff check wfctl/ tests/`
pass. No behaviour change yet — T001–T003 add unused symbols and one read.

---

## Phase 2 — US1, specify reads structure (P1)

- [x] T004 [US1] In the `specify` arm, compute the missing sections and set
      `state = "in_progress"` when any are absent. Marker handling is unchanged
      and keeps priority: a marked spec is clarify's business.
- [x] T005 [US1] Set `specify`'s annotation to `missing: <names>` and its
      `reason` to the same, joining the `reason` dict at the foot of the loop.
      `specify` sets `in_progress` from evidence, which is that field's stated
      contract.
- [x] T006 [US1] Tests in `tests/test_pipeline_sections.py`: a `spec.md` of the
      single character `x` leaves `specify` not `done` and names all four
      sections; a spec carrying all four reads `done`; a spec carrying two names
      exactly the two it lacks; a heading inside a fenced block does not count;
      `## Functional Requirements` does not satisfy `Requirements`;
      `## Requirements _(mandatory)_` does. The state assertion is `in_progress`
      exactly, never merely not-`done` — `pending` also satisfies not-`done`,
      and the difference between the two is the whole of FR-003.

**Verification**: `uv run pytest -q tests/test_pipeline_sections.py`. SC-001's
spec half and SC-003 are proved here.

---

## Phase 3 — US2, plan reads structure (P1)

- [x] T007 [US2] In the `plan` arm, replace `_file_exists(spec_dir / "plan.md")`
      with the text read from T003 plus the section check. Leave `clarify`'s
      `skipped` branch reading `plan.md` by existence — it asks whether planning
      already passed through, which a thin plan still answers, and tightening it
      would send an in-flight old spec back to clarify.
- [x] T008 [US2] Annotation and `reason` for `plan`, as T005.
- [x] T009 [US2] Tests: a `plan.md` of `x` leaves `plan` exactly `in_progress`
      — not merely not-`done`, per T006's note; one carrying all five reads
      `done`; `clarify`'s `skipped` branch still fires for a thin `plan.md`,
      which is the regression T007 is most likely to cause.

**Verification**: `uv run pytest -q tests/test_pipeline_sections.py`. SC-001's
plan half.

---

## Phase 4 — US3, clarify says why it passed (P2)

- [x] T010 [US3] Set `clarify`'s annotation to `scan never ran` in the `skipped`
      branch. **Annotation only** — not `reason`. A `skipped` step is never
      `_current_step_name`, so a reason set there reaches no consumer, and the
      field's contract is arms that set `in_progress` from evidence
      (`research.md`).
- [x] T011 [US3] Test: the skipped branch carries the annotation and still reads
      `skipped`; the `done` branch carries none.

**Verification**: `uv run pytest -q`. The state must be unchanged — a test that
only asserts the annotation has not checked the thing most at risk.

---

## Phase 5 — Drift, docs, and the whole-corpus exercise

- [x] T012 Drift test: both constant tuples equal the mandatory sets of
      `wfctl/specify/templates/spec-template.md` and `plan-template.md`. Equality
      in both directions — a renamed section and an added one both fail
      (spec.md Clarifications). The plan template marks nothing `_(mandatory)_`,
      so its side asserts against that file's `##` headings, and the test says
      in its docstring why the two halves are asserted differently.
- [x] T013 The positive exercise a negative-only run does not cover: inference
      against a real spec directory from `~/Development/wfctl-specs/` still
      reads `specify` and `plan` as `done`. Skipped, not failed, where that root
      is absent — the corpus is not in the repo and CI has no copy.
- [x] T014 Update the rung comment at the head of `wfctl/_pipeline.py`:
      `specify` becomes `1 + 2 + 3`, `plan` becomes `1 + 2`, `clarify` gains its
      annotation clause, and the two `#309` lines in the "filed, not fixed"
      paragraph are settled. Leave #308's lines exactly as they are.
- [ ] T015 Flip `docs/architecture/required-sections-are-wfctls.md` to
      `accepted` **only if the maintainer says so** — an agent never writes
      `accepted` (`architecture-decisions`). Otherwise leave it `proposed` and
      say so in the PR body.

**Verification**: all four of `uv run pytest -q`, `uv run ruff check wfctl/
tests/`, `uv run mypy wfctl/`, `uv run wfctl doctor`.

- [x] T016 Test that inference reads the spec directory and nothing else
      (FR-006, SC-005): run `_infer_steps` against a spec dir under a repo root
      with no `.specify/` reachable, and assert every step's state matches the
      run where the templates are present. This is the level-2 record's
      load-bearing claim and the one thing no other task touches — if it fails,
      the record is wrong, not the test.
- [x] T017 Test pinning the eight entries of `_STEPS` — name, command and
      continuation (FR-009). The flags are a property of the table, not of a
      run, so nothing else can observe that this change left them alone. Its
      docstring names #309 as the change it was written to constrain.

---

## Dependencies

```
T001 ─┬─► T004 ─► T005 ─► T006      (US1)
T002 ─┤
T003 ─┴─► T007 ─► T008 ─► T009      (US2)

T010 ─► T011                         (US3, independent of US1/US2)

T012, T013, T014, T016 after US1 and US2
T017 independent of everything — it constrains the table, not the arms
T015 last, and only on the maintainer's word
```

`[P]`: T006, T009 and T011 touch one new test file and are written together
rather than in parallel. T012 and T013 are independent of each other.

## Verification

The suite passes against the defect today, so a green run is not the check. The
two exercises that fail if the fix did not work are T006/T009 (the `x` case) and
T013 (the real corpus). A run that exercised only the negative case has not
tested this.
