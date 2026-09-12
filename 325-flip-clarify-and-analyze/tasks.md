# Tasks: flip clarify and analyze

**Input**: Design documents from `specs/325-flip-clarify-and-analyze/`
**Prerequisites**: plan.md, spec.md

**Tests**: Every task below either changes a test or is paired with one in the
same phase. The feature is a table value, so the only thing that can prove it
moved is an assertion against the table and against what a reader is told.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel — different files, no dependency
- **[Story]**: US1 (an unattended run reaches the end), US2 (a blocked step still
  holds the run), US3 (a reviewer can see what each step covered)

## Path Conventions

Single project. `wfctl/` and `tests/` at the repository root, per plan.md.

---

## Phase 1 — US1: an unattended run reaches the end of the pipeline (P1)

- [ ] **T001** [US1] In `wfctl/_pipeline.py`, change the `clarify` row of `_STEPS`
      from `_REVIEW_REQUIRED` to `_AUTOMATIC`. Keep the column alignment the table
      is written in — the rows are aligned so a reader scans the flag column, and
      a misaligned row is the one that gets skipped. Covers FR-001.
- [ ] **T002** [US1] In the same table, change the `analyze` row from
      `_REVIEW_REQUIRED` to `_AUTOMATIC`. Covers FR-002.
- [ ] **T003** [US1] In `tests/test_pipeline_sections.py`, rename
      `test_no_step_changed_the_flag_that_says_it_may_run_unattended` to
      `test_the_table_pins_every_steps_unattended_flag`, update its expected dict
      so `clarify` and `analyze` read `"automatic"`, and extend its docstring to
      name #325 beside #309 — what moved, why, and that the six other rows are
      what it still guards. One test over one dict; do not split it. Covers
      FR-008 and FR-009.
- [ ] **T004** [US1] In `tests/test_pipeline_commands.py`, add a test asserting
      that `next_step_content("clarify", None)` returns `("/speckit.clarify",
      True)`, and that the same holds when `clarify` is current with clarification
      markers still standing — the state where its predicate reads `in_progress`
      and sets no reason. The docstring names why that second state is the
      interesting one: it is the state a reader would expect to block, and the
      reason it does not is that re-entering the step is what resolves a marker.
      Covers FR-003 and acceptance scenarios 1 and 2.
- [ ] **T005** [P] [US1] In `tests/test_pipeline_commands.py`, add a test
      asserting `next_step_content("analyze", None)` returns
      `("/speckit.analyze", True)`. Covers FR-004 and acceptance scenario 3.
- [ ] **T006** [US1] In `tests/test_pipeline_commands.py`, assert the property
      the two prohibitions describe, over the whole table rather than per step:
      for every name in `_STEPS`, `next_step_content(name, None)[1]` equals
      `_STEPS[name].continuation == "automatic"`, and `next_step_content(name,
      "any reason")[1]` is `False`. A per-step arm for `clarify` or `analyze`
      breaks the first assertion; a flip made conditional on branch state, a
      grant, or one of the payload's four facts breaks it too, because the
      property holds with no argument but the step's own name. Covers FR-006 and
      FR-007, which are prohibitions — the shape that goes uncovered because
      nothing fails when a prohibition is only believed.

- [ ] **T006a** [P] [US1] In `tests/test_pipeline_sections.py`, assert that no
      step's continuation value is `"review_required"` — the count is zero, not
      "two fewer than before". SC-001 states the outcome as a count falling from
      two to zero, and a test asserting the new dict proves the table changed
      without proving the pipeline has no waiting steps left. Covers SC-001.
- [ ] **T006b** [US1] Add the acceptance path SC-002 names — an unattended run
      executing both steps with no prompt — to the PR body as a stated gap rather
      than to the suite. It cannot be asserted here: it needs a real
      `/speckit.orchestrate` run, and that run is blocked on #331, where `analyze`
      step 8 still stops to ask whether to apply remediation. Covers SC-002 by
      recording why it is uncovered, which is the honest answer and the one a
      reviewer can disagree with.

### Verification

```bash
NO_COLOR=1 uv run pytest -q tests/test_pipeline_sections.py tests/test_pipeline_commands.py
```

T003 must fail before T001 and T002 are applied and pass after — if it passes
against the unflipped table, the tripwire is not pinning what it claims to.

T004 and T005 together cover SC-003: the three reachable current-states of the
two steps are `clarify` pending, `clarify` with markers standing, and `analyze`
pending, and each is asserted once.

---

## Phase 2 — US2: a blocked step still holds the run (P1)

- [ ] **T007** [US2] Run the existing
      `test_a_blocked_design_step_is_never_automatic` in
      `tests/test_pipeline_commands.py` and confirm it is green after the flip.
      It asserts that a blocked `brainstorm` reports `auto: False` despite being
      `automatic` in the table, which is the property that makes Phase 1 safe.
      No new test: this one already covers it, and a second assertion of the same
      property is a second thing to update. Covers FR-005 and acceptance
      scenario 1 of US2.
- [ ] **T008** [US2] Confirm `test_a_blocked_design_step_is_never_automatic`'s
      sibling assertion — a blocked `implement` routing to `wfctl verify` with
      `auto: False` — is unaffected. Covers acceptance scenario 2 of US2.

### Verification

```bash
NO_COLOR=1 uv run pytest -q tests/test_pipeline_commands.py -k blocked
```

Both must pass without modification. A blocked-step test that needed editing to
stay green would mean this change reached the guard, which it must not.

---

## Phase 3 — US3: a reviewer can see what each step covered (P2)

- [ ] **T009** [US3] Confirm `docs/architecture/scans/325-clarify.md` is committed
      and that `uv run wfctl arch check` on it reports the change adds it. Already
      done during `/speckit.clarify`; listed so the story has a verification path
      rather than being assumed.
- [ ] **T010** [US3] After `/speckit.analyze` runs, confirm
      `docs/architecture/scans/325-analyze.md` exists, is committed, and carries
      every coverage row plus the requirement-to-task percentage.

### Verification

```bash
uv run wfctl arch check docs/architecture/scans/325-clarify.md
uv run wfctl arch check docs/architecture/scans/325-analyze.md
```

---

## Phase 4 — whole-change verification

- [ ] **T010a** Assert the two edge cases the spec names that are cheap to state
      and would otherwise be believed: a `skipped` `clarify` is never the current
      step, so its continuation value never reaches a reader; and `analyze` with
      `tasks.md` complete and no analysis report reads `pending` and becomes
      current. The third — both steps reached in one unattended pass — needs no
      assertion, because each is evaluated from the same table with no shared
      state, which T006's property already covers for every step at once.
- [ ] **T011** Confirm `tests/pipeline_payload_snapshot.json` is unchanged. It
      pins `_infer_steps` across 41 feature shapes and carries no `auto` key, so
      this change should not touch it. If it does, that is a finding to explain in
      the PR rather than a file to regenerate. Covers SC-005.
- [ ] **T012** Run the repository's four commands, all four green:

      ```bash
      uv run pytest -q
      uv run ruff check wfctl/ tests/
      uv run mypy wfctl/
      uv run wfctl doctor
      ```

- [ ] **T013** Confirm the change touches exactly `wfctl/_pipeline.py`,
      `tests/test_pipeline_sections.py` and `tests/test_pipeline_commands.py`,
      plus the two scan files. Covers SC-004.
- [ ] **T014** Confirm FR-009 — no step other than `clarify` and `analyze`
      changed its continuation value — is carried by T003's dict, which lists all
      eight. FR-006 and FR-007 are carried by T006's property assertion. No task
      here restates them: three tasks asserting one prohibition is the duplication
      this list was rewritten to remove.

### Verification

```bash
uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/ && uv run wfctl doctor
```

---

## Dependencies

```
T001, T002  ─┬─►  T003  ──►  T004, T005  ──►  T006
             │
             └─►  T007, T008        (must stay green, not change)

T009  (done)      T010  (after /speckit.analyze)

T006a, T006b  ──►  with Phase 1
T010a … T014  ──►  after every phase above
```

Numeric order is execution order. T003 is written after T001 and T002 and is
expected to fail if run against the unflipped table — that is what the Phase 1
verification note asks to be demonstrated, not an instruction to reorder.

## Out of scope

Named here because each was considered and rejected with a reason, and a task
list that is silent about them reads as a list that never thought of them.

- A loop bound in `speckit-orchestrate` — filed as #332.
- A remediation policy for `analyze` step 8 — filed as #331.
- A structural check on the scan file — filed as #330.
- Any per-step arm in `next_step_content`, any runtime condition on the flip.
