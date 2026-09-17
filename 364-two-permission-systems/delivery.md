# Delivery Plan: two permission systems (364)

**Feature**: `364-two-permission-systems` | **Date**: 2026-09-14
**Source**: `specs/364-two-permission-systems/tasks.md` (39 tasks)
**Parent issue**: #364

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| #TBD | T001–T039 | `wfctl/cli.py` (modified), `wfctl/_session.py` (modified), `wfctl/_predicates.py` (modified), `wfctl/_pipeline.py` (modified), `wfctl/agents/skills/` (modified), `tests/test_blocked_events.py` (created), `tests/test_blocked_cli.py` (created), `tests/test_blocked_holds_step.py` (created), `tests/test_notify_status.py` (modified), `tests/test_console_plaintext.py` (modified), `docs/architecture/the-agent-reports-the-block-wfctl-never-saw.md` (modified — status), `docs/architecture/design/364-the-block-report-is-its-own-verb.md` (modified — status) | L | T038 green (`pytest`, `ruff`, `mypy`), T039 `doctor` green **from this working tree**, and T037 both records moved to `accepted` |

**Rationale**: Single PR, chosen by the user over the two-PR split this analysis
recommended. The split signal did fire and is recorded below rather than
discarded, because a reviewer arriving at an L-sized PR is owed the reason it is
one.

**PR closes**: `Closes #364`

### The split that was considered and declined

Two of the four boundary signals pointed at a split, and they pointed at
different cuts:

- **Signal 2, reviewability — bundles US1 with US2.** A reviewer seeing the hold
  without the release cannot judge whether the release semantics are right. This
  signal is honoured either way; no option separated them.
- **Signal 4, story independence — splits US3 off.** US3 shares no file *region*
  with US1 and US2, has its own acceptance criteria and its own runtime path, and
  is what #364 asks for in its own words. `tasks.md` § Parallel opportunities says
  the same thing unprompted.

The recommendation was therefore two PRs: #364 carrying US3 (two strings and a
test file), and a new issue carrying the `blocked` verb, the event pair and the
hold — a mechanism #364 never requested. **The user chose one PR.** The cost of
that choice is the thing to watch in review: the words #364 asked for and the
mechanism it did not are landing under one `Closes`, so a revert of either is a
revert of both.

Signals 1 and 3 did not fire. All three slices touch `wfctl/cli.py`, but in
regions that do not overlap — `_IRREVERSIBLE_NOTICE` at `cli.py:197` and the
print site at `cli.py:478` for US3, a new `@app.command` for US1 — and the phases
are sequenced, so no two agents edit the same region concurrently.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #364 | T001–T039 | `[364] An orchestrating agent answers to two permission systems and wfctl reports only its own` | L — 39 tasks, 12 files | PR #TBD |

**Grouping pattern**: Single issue
**Rationale**: One PR closes exactly one issue, and #364 already exists as that
issue — the branch is named for it and the spec dir resolves from it.

**No issue was created by this step, and none was declined.** The map's only row
was already keyed before decompose ran, so there was nothing for
`wfctl issue create` to do. This is not the refusal step 6 of
`speckit-delivery-plan` guards against — `wfctl status` reports `notify: true`
(`notify_source: local`) on this branch, so the run *was* permitted to create an
issue and simply had none to create. Recorded here because an empty tracker
write can mean three different things and only one of them is a reason to widen a
grant.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | Baseline green and its count written down, before any file is edited |
| 1 | Parallel | T002 ‖ T003 ‖ T029 ‖ T030 ‖ T031 | Openers of both tracks. Two same-file pairs **coordinate rather than fan**: T002/T003 both add a function to `_session.py`, T029/T030 both add a test to `test_notify_status.py` |
| 2 | Parallel | (T004 → T005 → T006) ‖ (T032 → T033) | Event-layer track and US3 track share no file. Each is internally sequential — T005 scopes the function T004 writes; T032 sits beside the constant T031 reworded |
| 3 | Parallel | T007 ‖ T034 | Two merge gates, one per track. Fan-in before Wave 4 |
| 4 | Parallel | T008 ‖ T009 ‖ T010a ‖ T010 | Tests written and confirmed failing before T011. T008/T009/T010a share `test_blocked_cli.py`; T010 is alone in `test_blocked_holds_step.py` |
| 5 | Sequential | T011 → T012 → T013 → T014 | One new command in `cli.py`, built up argument by argument |
| 6 | Sequential | T015 → T016 → T017 | Predicate before the hold. T016 applies it **after** `_infer_steps` returns, never inside its loop |
| 7 | Parallel | T018 ‖ T019 | Payload-snapshot assertion ‖ the skill instruction under `wfctl/agents/skills/` |
| 8 | Sequential | T020 | US1 merge gate |
| 9 | Parallel | T021 ‖ T022 | Different test files |
| 10 | Sequential | T023 → T024 → T025 → T026 → T027 | `--clear` mode, then the remedy, then the console rendering that shows it |
| 11 | Sequential | T028 | US2 merge gate |
| 12 | Parallel | T035 ‖ T036 ‖ T037 | Walkthrough ‖ help-text read ‖ record acceptance. **T037 is the human's to run** — the citation is a person's agreement |
| 13 | Sequential | T038 → T039 | Definition of done, then `doctor` from this working tree |

**Single-agent order** (the realistic path for one PR):
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T010a →
T011 → T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020 → T021 →
T022 → T023 → T024 → T025 → T026 → T027 → T028 → T029 → T030 → T031 → T032 →
T033 → T034 → T035 → T036 → T037 → T038 → T039

A single agent should run US3 (T029–T034) **first**, not in `tasks.md` order.
It is six tasks in one file, it is independently revertible, and `tasks.md`
§ Implementation strategy names it as what ships if the change has to ship
something today.

---

## Agent Fanning Instructions

Real parallelism exists only in Waves 1–3, where the event layer and US3 share no
file. Everything after Wave 3 is one dependency chain, and fanning it buys
nothing.

**Waves 1–3 fanning (2 agents):**

**Agent A — the event layer (Phase 2):**
```
Implement T002 through T007 from
specs/364-two-permission-systems/tasks.md.

Scope: wfctl/_session.py and tests/test_blocked_events.py only. Do not
touch wfctl/cli.py — another agent is editing it concurrently in a
different region.

T002 and T003 both add a function to _session.py: write them in one
pass, placed beside the three notify-* writers they match.
T004 then adds standing_blocks, T005 scopes it to the branch, T006
writes the test file covering all four including a truncated final
line that must be skipped rather than crash the reader.

Stop at T007 and report: uv run pytest -q tests/test_blocked_events.py
&& uv run mypy wfctl/
```

**Agent B — the two authority lines (Phase 5 / US3):**
```
Implement T029 through T034 from
specs/364-two-permission-systems/tasks.md.

Scope: wfctl/cli.py (only _IRREVERSIBLE_NOTICE at :197 and the print
site at :478), tests/test_notify_status.py, tests/test_four_facts.py.
Do not touch wfctl/_session.py — another agent is editing it
concurrently.

T029 and T030 both add a test to test_notify_status.py: write them in
one pass. The loop covers eight renderings, not seven — research.md
establishes that the `label` rendering is built by _notify_line rather
than looked up in _NOTIFY_LINES.

T031 rewords the irreversible line to name all four actions in its
class; T032 adds the new constant beside it and prints it
unconditionally, keyed on nothing.

Stop at T034 and report: uv run pytest -q tests/test_notify_status.py
tests/test_four_facts.py && uv run ruff check wfctl/ tests/
```

**Fan-in gate after Wave 3:** `uv run pytest -q && uv run mypy wfctl/`

---

## Notes carried out of decomposition

- **`tasks.md` § Parallel opportunities miscounts one line.** It lists
  "T008, T009, T010, T010a — three test files, no shared fixture". Those four
  tasks write **two** files: T008, T009 and T010a all land in
  `tests/test_blocked_cli.py`, and only T010 is in
  `tests/test_blocked_holds_step.py`. The parallelism claim survives — no shared
  fixture, and three tasks appending independent tests to one file is still safe
  for a single agent — but an agent fanning on the stated file count would spawn
  one worker too many. Wave 4 above states the real grouping.
- **T037 is not the implementing agent's task.** Moving both records from
  `proposed` to `accepted` takes `--agreed "<where the human agreed>"`, and the
  citation belongs to whoever agreed. An agent running it invents the citation.
