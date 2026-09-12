# Tasks: Session Stopped, Not Finished

**Input**: Design documents from `/Users/andremarin/Development/wfctl-specs/352-session-stopped-not-finished/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

**Tests**: Not optional here. The event shape, the flag's default, and step 9's
table rows are all critical-path — a wrong verdict on the last row starts an
unattended run on a branch a person deliberately wrapped up. Every task below
names its verification path.

**Organization**: By user story. The three are independent by construction —
User Story 1 reads a mark that can be written by hand, User Story 2 writes one
nothing has to read. Either ships alone.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3
- Exact file paths in every description

## Path Conventions

Single project. `wfctl/` and `tests/` at the repository root; the skills tree is
package data under `wfctl/agents/`. `FEATURE_DIR` resolves **outside** the
working tree — `wfctl feature-paths` prints it.

---

## Phase 1: Setup

**Purpose**: Establish the baseline, so a failure later in the run is
attributable to this change rather than inherited.

- [X] T001 Record the pre-change baseline from the repository root: run all four definition-of-done commands in `quickstart.md` and note the passing test count; verify with `uv run --frozen --extra dev pytest -q` reporting zero failures — merge gate

---

## Phase 2: Foundational

**No foundational task, and that is a finding rather than an empty heading.**

`_io.append_event` at `wfctl/_io.py:71` already forwards arbitrary keyword
arguments into the JSON record (`{"ts": ts, "event": event, **kwargs}`), so the
new field needs no plumbing beneath it. The two shipping stories touch disjoint
files — `wfctl/agents/skills/start-session/SKILL.md` for US1, `wfctl/_session.py`
and `wfctl/cli.py` for US2 — so neither blocks the other.

The one shared prerequisite is a decision, not code:
`docs/architecture/stop-kind-is-a-field-not-an-event.md` is already written and
committed at `51c8392`. It is `proposed`; `a-human-accepts-a-decision` puts that
transition on a human at the pull request, and no task here performs it.

---

## Phase 3: User Story 1 — A cut-off run comes back and carries on (P1) 🎯 MVP

**Goal**: A session starting on a branch whose most recent stop is marked
continued, with a quotable first action in the handoff, begins that action and
asks nobody.

**Independent Test**: Put `"continued": true` on the last `end` line of a
branch's `events.jsonl` by hand and a handoff naming a first action beside it.
Start a session — it must begin, quoting the sentence. Flip the mark to
`false` and start again — it must ask.

**Verification**: `tests/test_start_session_asks_conditionally.py`, which asserts
against individual table rows rather than substrings anywhere in the step. Its
docstring records why: a review panel showed three earlier assertions all passing
on a copy with two cells swapped. T002 extends it downward *and upward* — every
helper there slices from step 9's heading, so step 4 needs a slice of its own
before T003 has anything checking it. Plus `quickstart.md` halves 1, 2 and 3,
which are the only thing that reaches the rendered skill.

- [X] T002 [US1] Extend `tests/test_start_session_asks_conditionally.py` with four things, all bound to a table cell rather than to a substring of the step: (a) a last `end` line carrying `"continued": true` plus a quotable handoff selects the do-not-ask row, and the same handoff with `"continued": false` selects the ask row; (b) **re-anchor the two existing row assertions** — `_row()` selects on the condition column's *prefix* and calls `pytest.fail` when none matches, so `test_a_handoff_on_a_branch_nobody_has_worked_on_starts_without_a_reply` and `test_a_branch_that_has_ended_a_session_before_is_still_asked` both go red the moment T003 and T004 land, with T007's gate as the first thing that says so; (c) a `_step_four()` slice and an assertion on step 4's stated `grep … | tail -1` command and its three-outcome table — every helper in that module slices from step 9's heading downward, so step 4 is unreachable today and T003 would ship unverified; (d) row three still selects an ask and row one's condition still requires a named first action, which is the only automated reach on FR-006 and SC-003. Verify with `uv run --frozen --extra dev pytest -q tests/test_start_session_asks_conditionally.py` failing before T003
- [X] T003 [US1] Rewrite step 4's `events.jsonl` read in `wfctl/agents/skills/start-session/SKILL.md` from "whether any line carries `"event": "end"`" to the stated command `grep '"event": "end"' "$(wfctl state-dir)/events.jsonl" | tail -1` and its three-outcome table, per `contracts/start-session-step-9.md`; verify with T002's step-4 assertion (c) — not with its row assertions, which slice below step 9's heading and cannot see this edit
- [X] T004 [US1] Rewrite step 9's **first two** table rows in the same file, per the table in `contracts/start-session-step-9.md`: row one to "a summary naming a first action, and no stop — or a stop marked continued", and row two from "a summary, and an `end` event — a session has finished here before" to "a summary, and a stop that was wrapped up". Row two is not optional — its present condition is true of a continued stop as well, so leaving it makes rows one and two both match the exact case this feature exists to fix. Row three stands; verify with T002's assertions (a), (b) and (d)
- [X] T005 [US1] Update step 8's "which row this session took" reporting line in the same file so it still distinguishes the rows now that row one carries two conditions; verify with `uv run --frozen --extra dev pytest -q tests/test_start_session_asks_conditionally.py::test_step_eight_reports_which_row_step_nine_took`
- [X] T006 [US1] Reconcile the skill's own prose against the new rows — the paragraph beginning "**The `end` event is what keeps an attended session safe**" argues from a fact T003 replaces; verify by reading `wfctl/agents/skills/start-session/SKILL.md` step 9 end to end and confirming no sentence still claims the mere presence of an `end` event decides the row
- [X] T007 [US1] Validate Phase 3 with `uv run --frozen --extra dev pytest -q tests/test_start_session_asks_conditionally.py` — merge gate

---

## Phase 4: User Story 2 — Stopping without finishing is something you can record (P2)

**Goal**: `wfctl end --continued` records a stop distinguishable from a finished
one, produces the handoff under identical rules, and warns when the handoff names
no first action.

**Independent Test**: End a session declaring it continued. The handoff must be
written by the same template at the same path under the same write-once rule, and
the event line must carry `"continued": true`.

**Verification**: a new `tests/test_session_stopped_not_finished.py`, plus
`tests/test_end_reports_observations.py` unchanged and still green — SC-005's
check that no existing reader changes its verdict.

- [X] T008 [US2] Create `tests/test_session_stopped_not_finished.py` with failing tests for the four observables in `contracts/wfctl-end.md`: the flag writes `"continued": true`, omitting it writes `"continued": false`, the closing console line differs in its first clause only, and the handoff write-once rule plus kept-file report are identical under both; pin `NO_COLOR` per `conftest.py`'s convention and verify with `uv run --frozen --extra dev pytest -q tests/test_session_stopped_not_finished.py` failing before T009
- [X] T009 [US2] Extend `_session.end()` at `wfctl/_session.py:462` to take the stop's kind and pass it through as `append_event(agent_dir, "end", step=observed.step, continued=<bool>)`; annotate the new parameter under `disallow_untyped_defs`, and extend the docstring with why the caller declares the kind rather than `end` concluding it (#70); verify with T008
- [X] T010 [US2] Add `--continued` to `end_cmd` at `wfctl/cli.py:754` as a boolean flag defaulting off, with no `--finished` counterpart per `contracts/wfctl-end.md`, and branch the closing line to `✓ Session stopped, not finished — {step}, boundary {boundary}, tree {tree}.` keeping `escape()` on the step; verify with T008
- [X] T011 [US2] Add the FR-013 warning to `wfctl/cli.py`: printed only with `--continued`, and only when the handoff's `## Next Session TODO` section is absent, empty, or holds just the template placeholder — read from a shared constant beside `_render_session_summary` in `wfctl/_session.py:458`, never a second copy of `- [ ] (fill in)` written into `cli.py`, because a change to the template would then kill this warning with nothing going red. The warning reads `⚠ the handoff names no first action — the next session will ask.`; the stop is still recorded either way; verify with a case in `tests/test_session_stopped_not_finished.py` covering all three unfilled shapes and one filled one
- [X] T012 [US2] [P] Assert the no-session refusal is byte-identical with and without the flag and still exits 1 (Story 2 scenario 3) in `tests/test_session_stopped_not_finished.py`; verify with `uv run --frozen --extra dev pytest -q tests/test_session_stopped_not_finished.py`
- [X] T013 [US2] [P] Assert `tests/test_end_reports_observations.py::test_the_end_event_records_the_position_not_a_status` still passes unchanged — the new key must not read as the `status` spelling #70 removed; verify with `uv run --frozen --extra dev pytest -q tests/test_end_reports_observations.py`
- [X] T014 [US2] Validate Phase 4 with `uv run --frozen --extra dev pytest -q tests/test_session_stopped_not_finished.py tests/test_end_reports_observations.py` — merge gate

---

## Phase 5: User Story 3 — An interrupted run is visible afterwards (P3)

**Goal**: A branch interrupted N times reports N, in order, with nothing removed.

**Independent Test**: Record three continued stops on a branch. Its history shows
three, each carrying its kind, in the order they happened.

**Verification**: tests in `tests/test_session_stopped_not_finished.py`. No
production change is expected in this phase — append-only already holds, and
these tests pin it against a future change that would erase a stop instead of
recording it, which is the alternative `spec.md` rejects.

- [X] T015 [US3] Add a test recording three continued stops and one finished stop on one branch, asserting four `end` lines survive in file order with their kinds intact (FR-008, SC-004); verify with `uv run --frozen --extra dev pytest -q tests/test_session_stopped_not_finished.py`
- [X] T016 [US3] Add a test asserting that a mixed history survives in file order with each stop's kind intact — a continued stop after a finished one, and the reverse — so `grep … | tail -1` finds the newer one (`spec.md`'s first edge case). **This does not verify FR-007.** The rule is `tail -1` inside `start-session/SKILL.md`, there is no wfctl function to call, and Phase 5 adds none; FR-007's routing half is pinned by T002's step-4 assertion (c) and by `quickstart.md` half 2. Verify with the same command
- [X] T017 [US3] In `tests/test_session_stopped_not_finished.py`, assert `wfctl log` renders a continued stop as an existing `end` row in the existing colour with the kind inside the detail string, and that no new event kind appears in `_STYLES`; verify with `uv run --frozen --extra dev pytest -q -k log`
- [X] T018 [US3] Validate Phase 5 with `uv run --frozen --extra dev pytest -q tests/test_session_stopped_not_finished.py` — merge gate

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T019 In `tests/test_session_stopped_not_finished.py`, assert `wfctl status` and `wfctl status --json` produce output identical to a branch with no stop recorded, on a branch carrying a continued stop (FR-015, and the clarification behind it); verify with `uv run --frozen --extra dev pytest -q -k status`
- [X] T020 In `tests/test_session_stopped_not_finished.py`, assert all three spellings of the payload — absent, `false` and `true` — are indistinguishable to the three existing readers of the stop mark, which is the stronger form of "today's verdict on a line carrying no key" and the architecture record's central claim — `_stall._passes_this_sitting`, `_stall.opens_a_new_sitting`, `_session.session_started` (SC-005); verify with `uv run --frozen --extra dev pytest -q tests/test_stall.py tests/test_session_existence.py tests/test_agent_session.py` — `test_stall.py` is not optional here: it is the only module that exercises the two sitting readers, and without it the command covers `session_started` alone
- [X] T021 Install the skills from the working tree with `uv run wfctl install-skills`, never a bare `wfctl` — without it the skill exercised is whatever the release put on disk and the change is nowhere in it
- [ ] T022 Run all four manual halves in `quickstart.md` against the installed tree (**CLI halves done** — the flag, the plain form, both stops on disk, the placeholder warning, the filled handoff's silence, and `status`/`log` unmoved, all exercised in an isolated state dir against a tree installed by `uv run wfctl install-skills`. **Open**: the two halves that run `/start-session` and watch whether it asks — they need a session that did not write the table): a continued stop carries on, a wrapped-up stop still asks, the quote is still the gate, and nothing else moved. **Half 2 is not optional** — a run that exercised only half 1 has not tested the protection FR-005 exists to provide
- [X] T023 Validate the whole change with the four definition-of-done commands — `uv run --frozen --extra dev pytest -q`, `ruff check wfctl/ tests/`, `mypy wfctl/`, and `uv run wfctl doctor` — merge gate

---

---

## Phase 7: The branch is the first column (FR-004 widened, FR-005 narrowed, FR-016)

**Why this phase exists rather than an edit to Phase 3.** Phases 1-6 shipped a
rule that branched on the stop's kind alone, and it left an issue branch asking
"what are we working on today?" after a deliberate wrap-up — on a branch named
for the one thing it is for. The question belongs to trunk branches, which carry
no answer in their name and accumulate a handoff from every session that ever
ended on them. A new phase rather than a rewrite because Phase 3 is already
committed and a reviewer reads the two as a sequence: what was built, and what
was wrong with it.

**Goal**: `/start-session` never asks on a branch that names a tracked issue.
Trunk keeps the question, and a continued stop is what answers it there.

**Independent Test**: the same handoff, the same filled sentence, on an issue
branch and on `main`. The first begins; the second asks.

**Verification**: `tests/test_start_session_asks_conditionally.py`, rows again,
plus `quickstart.md` halves 1, 2 and 3 — which is where the branch axis is
actually exercised, since no test starts a session.

- [X] T024 Rewrite the row assertions in `tests/test_start_session_asks_conditionally.py` onto the new conditions and add three: an issue branch is never asked, a trunk branch whose last stop was not continued still is, and step 4 says where the branch kind comes from; verify with `uv run --frozen --extra dev pytest -q tests/test_start_session_asks_conditionally.py` failing before T025
- [X] T025 Add the `issue` read to step 4 of `wfctl/agents/skills/start-session/SKILL.md` — the key, the `unknown` literal, and why the literal is read rather than the branch name judged — and scope the `events.jsonl` read to a trunk branch's row; verify with T024's step-4 assertion
- [X] T026 Rewrite step 9's first two rows in the same file to `an issue branch, or a stop marked continued …` and `a trunk branch whose last stop was not continued …`, per the rewritten `contracts/start-session-step-9.md`; row three stands; verify with T024's row assertions
- [X] T027 Reconcile step 9's prose and step 8's reporting line in the same file — three paragraphs argued from the stop's kind being the column; verify by reading step 9 end to end and confirming no sentence still claims the stop's kind decides an issue branch
- [X] T028 Carry the change into `spec.md` (a fourth clarification, FR-004, FR-005, FR-007, FR-016, SC-002, User Story 1's scenarios), `contracts/start-session-step-9.md`, `data-model.md` (a Branch kind entity and a three-column routing table), `quickstart.md` (five halves) and `plan.md`'s Summary; verify by reading each for a claim still resting on the stop's kind alone
- [ ] T029 Run `quickstart.md` halves 1, 2 and 3 against the installed tree — the issue branch begins, trunk after a wrap-up asks, trunk after a continued stop begins. **Half 2 is not optional**: it is the only one that shows the rule did not simply delete the question
- [X] T030 Validate with the four definition-of-done commands — merge gate

## Dependencies

```
Phase 1 (T001)
   │
   ├──► Phase 3 · US1 (T002→T007)  ─┐   independent of US2 — the mark can be
   │                                │   written by hand
   └──► Phase 4 · US2 (T008→T014) ─┤
                    │               │
                    └──► Phase 5 · US3 (T015→T018)
                                    │   needs US2's writer to produce the
                                    │   history it reads
                                    ▼
                            Phase 6 (T019→T023)
```

Within US1, T003 and T004 edit the same file and are sequential. T005 and T006
follow both. Within US2, T009 precedes T010 (the flag has nothing to pass until
`end()` accepts it), and T011 follows T010.

## Parallel opportunities

- **Across stories**: Phase 3 and Phase 4 touch disjoint files and can run at the
  same time once T001 is green.
- **Within US2**: T012 and T013 are marked `[P]` — different test modules, no
  dependency on each other.
- **Within US3**: none. T015, T016 and T017 have no dependency on each other
  and all three write `tests/test_session_stopped_not_finished.py`, which is
  the half of `[P]`'s definition they fail. Free to reorder, not free to fan.
- **Phase 6**: none either, for the same reason — T019 and T020 land in that
  same module. T021 through T023 are sequential and last, because the manual
  halves need the installed tree.

## Implementation strategy

**MVP is User Story 1 alone.** It is the stall, and it is the only part of the
change that removes it — on a branch whose log was marked by hand it already
works. It ships as a skill edit plus its row tests, with no change to any module
under `wfctl/`.

**Increment two is User Story 2**, which is what makes the MVP reachable without
hand-editing durable state. Shipped in the other order it writes a mark nothing
consults.

**Increment three is User Story 3**, which adds no production code — it pins the
append-only property that is the whole reason this change records the
interruption rather than erasing the stop.

Phase boundaries here are review slices, not pull request boundaries.
`/speckit.decompose` decides those.
