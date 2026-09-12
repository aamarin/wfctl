# Delivery Plan: four facts in the payload (299)

**Feature**: `299-four-facts-in-the-payload` | **Date**: 2026-09-10
**Source**: `specs/299-four-facts-in-the-payload/tasks.md` (24 tasks)
**Parent issue**: #100

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| one PR, #299 | T001–T024 | `wfctl/_predicates.py` (modified), `wfctl/_pipeline.py` (modified), `wfctl/cli.py` (modified), `tests/test_four_facts.py` (created), `tests/test_pipeline_state_names.py` (modified), `docs/architecture/readiness-is-not-a-step-state.md` (created), `docs/architecture/design/299-facts-render-as-a-block.md` (created), `docs/architecture/scans/299-clarify.md` (created), `docs/architecture/scans/299-analyze.md` (created) | M | The four definition-of-done commands green, and the two situations in `quickstart.md` read differently in the console |

**Rationale**: Single PR. The payload field, its four derivations and its two
renderings are mutually dependent — a payload field nothing renders is the state
the issue was filed about, and a console block with no payload behind it is a
view computing a fact, which `pipeline-state-is-one-payload` forbids. Nine files,
three of them source; M by the sizing table and below the L threshold that would
call for a discussion.

**PR closes**: `Closes #299`

#100 is the parent epic and this is its last open child, but the parent close is
**not** added here. Five of #100's six scope items have shipped and the sixth is
this one; whether the epic itself closes is a judgment about the epic, and the PR
body says this is its last child rather than closing it by keyword.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #299 | T001–T024 | `[299] Four facts in the payload, each read from its own owner` | half a day | PR for #299 |

**Grouping pattern**: Single issue
**Rationale**: The issue already exists and already scopes exactly this work; no
issue is created, so nothing here reaches the tracker or anyone outside the repo.

---

## Parallelization Waves

| Wave | Tasks | Parallel | Gate |
|------|-------|----------|------|
| 0 | T001 | — | Baseline green before any edit |
| 1 | T002, T003 | no | T002 defines the type the four derivations return; T003 is what makes fact 4 answerable from the payload. Both block everything after them. |
| 2 | T004–T006 | yes | Three console tests in one new file, no shared state |
| 3 | T007 → T008 → T009 → T010 | no | A chain through `_predicates.py` into `_pipeline.py` into `cli.py`; each reads the one before |
| 4 | T011, T012, T013, T014, T015 | T014 ‖ T015 | T014 and T015 each add one new function and touch nothing the other does |
| 5 | T016–T019 | yes | Four independent tests in the file created in wave 2 |
| 6 | T020, T021, T024 | yes | Three separate surfaces — a comment, a structural check, four assertions |
| 7 | T022, T023 | no | The definition of done, then the hand walk the suite cannot do |

---

## Agent Fanning Instructions

Not fanned. One PR, one issue, one worktree — this one. Waves 2, 5 and 6 are
parallel within a single session's editing, not across agents: every parallel
task in them writes to `tests/test_four_facts.py`, and three sessions writing one
file is a merge conflict dressed as concurrency.

The one thing that must not be done here: flipping `clarify` or `analyze` to
automatic. That is #325, queued behind this feature, and its own body says why it
waits — the flip asserts those steps proved enough to pass unattended, which is a
separate judgment with a separate owner.
