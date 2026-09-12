# Tasks: orchestrate loop bound

**Branch**: `332-orchestrate-loop-bound` · **Issue**: #332
**Plan**: `<FEATURE_DIR>/plan.md` · **Data model**: `<FEATURE_DIR>/data-model.md`

`[P]` marks tasks that touch no file another unfinished task touches.

## Phase 1 — the counting, on its own

- [x] **T001** Add `wfctl/_stall.py` with a digest over an `Evidence`'s
      `spec_text`, `plan_text` and `tasks_text`, in that order, separated so a
      byte moving between files changes the result. Short hex, fixed width.
      *Done when*: two Evidences differing in any one artifact produce different
      digests, and identical ones produce the same digest.

- [x] **T002** In `wfctl/_stall.py`, read `resume` lines from the end of a
      branch's `events.jsonl` and return the run of consecutive lines sharing both
      `step` and `digest`. Skip a line that will not parse. Collapse two lines
      sharing a timestamp into one pass, for the legacy shape.
      *Done when*: the function returns the step and the count, or nothing when
      fewer than three passes match.

- [x] **T003** [P] Add `tests/test_stall.py` covering T001 and T002: a clean run,
      a stalled run, a legacy double-written log, an unparseable line mid-log, and
      a log whose passes carry no digest at all.
      *Done when*: every case asserts on the returned count, and each test's
      docstring names the failure it exists to catch.

## Phase 2 — into the one payload

- [x] **T004** Add the verdict field to `PipelineReport` in `wfctl/_pipeline.py`
      — the repeated step, the number of passes, and what the digest covered.
      Absent when the run is progressing.
      *Done when*: `mypy wfctl/` passes with the field annotated.

- [x] **T005** Call `_stall` once from `build_report`, which already receives the
      state dir. Keep the edit to the import, the call and the field — this file
      belongs to #325 for now, and the plan's Complexity Tracking says why the
      change cannot be avoided.
      *Done when*: `wfctl status --json` carries the field on a stalled branch and
      omits it otherwise.

- [x] **T006** In `wfctl/cli.py`, have `resume` record the digest in the event it
      already appends.
      *Done when*: a fresh `wfctl resume` writes a line carrying `digest`, and a
      branch with no feature directory writes one without it rather than failing.

- [x] **T007** Render the verdict in `wfctl status`, naming the step that
      repeated and what did not change. Follow the existing blocked-reason
      rendering rather than inventing a second shape.
      *Done when*: a stalled branch prints the step and the unchanged evidence,
      and `NO_COLOR` is pinned in the test that asserts it.

## Phase 3 — the agent stops

- [x] **T008** Add the branch to step 5 of
      `wfctl/agents/skills/speckit-orchestrate/SKILL.md`: a stalled run stops and
      reports instead of emitting `EXECUTE_COMMAND`. This skill is wfctl's own,
      not spec-kit-derived, so the edit belongs in place.
      *Done when*: the step reads the verdict off the same payload it already
      takes `next_command` and `auto` from, with no second command run.

- [x] **T009** Run `uv run wfctl install-skills` and read the installed copy of
      that skill.
      *Done when*: the installed tree carries the new branch. The suite checks
      that skills ship and cross-reference, not that this one reads correctly.

## Phase 4 — proof

- [x] **T010** Add the spec's Validation Strategy tests: three passes each
      advancing the work does not stop; three advancing nothing stops and names
      the step; a legacy-shaped history counts correctly.
      *Done when*: all three fail against `main` and pass against this branch.

- [x] **T011** Drive a real repeating step to a stop and watch it. Re-entry that
      changes nothing, three times, unattended.
      *Done when*: the run halted on its own and named the step. A test asserting
      the bound fires, with no run that watched it fire, does not close this task.

- [x] **T012** The repo's definition of done: `uv run --frozen --extra dev pytest
      -q`, `ruff check wfctl/ tests/`, `mypy wfctl/`, then `uv run wfctl doctor`.
      *Done when*: all four are green and the output is in hand, not assumed.
