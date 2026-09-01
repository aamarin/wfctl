# Delivery Plan: reply over-explains (102)

**Feature**: `102-reply-over-explains` | **Date**: 2026-08-31
**Source**: `<spec root>/102-reply-over-explains/tasks.md` (35 tasks)
**Parent issue**: none — #102 is not under an epic. The three open epics (#100
gates, #74 session truth, #101 durable runs) are all `_pipeline.py` / `_session.py`
work; none owns the skill.

---

## File-touch matrix

Three files. That is the whole change.

```
wfctl/agents/skills/conversation-response-shape/SKILL.md   MODIFY  14 tasks
  T004 T005 · T008 T009 T010 · T012 T013 T014
  T016 T017 T018 T019 · T022 T023

tests/test_response_shape_invariants.py                    CREATE   3 tasks
  T006 (C-3, C-7) · T020 (C-5) · T024 (C-6)

.github/pull_request_template.md                           MODIFY   1 task
  T026

read-only — baselines, gates, judgment reads                       17 tasks
  T001 T002 T003 T007 T011 T015 T021 T025 T027
  T028 T029 T030 T031 T032 T033 T034 T035
```

**Size: S** (3 files). Single PR by the sizing table.

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| PR-1 | T001-T035 | `conversation-response-shape/SKILL.md` (modified), `tests/test_response_shape_invariants.py` (created), `.github/pull_request_template.md` (modified) | S | T035 green: `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/`, plus `wfctl doctor` with no standing finding |

**Rationale**: single PR. Fourteen of the eighteen editing tasks land in one
388-line prose file, and prose has no merge semantics — concurrent edits to it
cannot be resolved mechanically. Signal 1 (file conflict risk) resolves to
*sequence, do not split*. Signals 2 and 3 agree: the C-6 assertion in T024 must
run against every example Phases 3-5 add, so the example rewrites cannot be
reviewed or merged independently of the rule additions.

**PR closes**: `Closes #102`

⚠️ **See "Issue close conflict" below before writing the PR body.**

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #102 | T001-T035 | `[102] conversation-response-shape: register, subject, and form selection` | S | PR-1 |

**Grouping pattern**: Single issue.
**Rationale**: S-size, one PR delivers the whole feature, and #102 already exists
as the branch's issue. Creating a second issue would be noise.

### Issue close conflict — needs a decision

`spec.md` FR-006 and SC-004 close **#80** ("the skill's literal-output example is
wfctl-specific"). Phase 6 does that work. So PR-1 as scoped satisfies two issues,
and this skill's rule is explicit: **never close multiple issues from one PR.**

The four boundary signals split on it:

| Signal | Verdict |
|---|---|
| 1. File conflict risk | **Do not split** — Phase 6 edits the same prose file as Phases 2-5 |
| 2. Reviewability | **Do not split** — T024's C-6 check asserts against examples added in Phases 3-5 |
| 3. Mergeable increment | Split viable — Phases 2-5 land a working feature with #80 still open |
| 4. Story independence | **Split candidate** — US3 has its own acceptance criteria and no shared state |

Per this skill, a split signal means *stop and flag*, not auto-split. Three ways
to resolve, and the choice is the user's:

| | What happens | Cost |
|---|---|---|
| **A. One PR, close #102 only** | PR body says `Closes #102`; #80 closed by hand afterwards with a link to the merged PR | #80's closure is not traceable from a `Closes` line — the thing the rule exists to prevent, at its mildest |
| **B. Two PRs, stacked** | PR-1 = Phases 1-5 + 7 → `Closes #102`. PR-2 = Phase 6 → `Closes #80` | Stacked PRs on this repo need merge commits, not squashes, and the async merge API — real coordination cost for two example rewrites |
| **C. Drop #80 from scope** | FR-006 and SC-004 leave this feature; #80 gets its own branch later | The new examples written in Phases 3-5 would land while the old wfctl-specific ones stay — the file ends up inconsistent with itself |

**Recommendation: A.** The rule protects traceability, and a hand-close carrying
the PR link preserves it. B pays stacked-PR coordination cost for two example
rewrites; C leaves the file internally inconsistent, which is worse than the
bookkeeping it saves.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 → T003 | Baselines recorded, tree green. No edits. |
| 1 | Sequential | T004 → T005 → T006 → T007 | Rule slots 4 and 5 exist; test file created. Blocks every later wave. |
| 1b | **Parallel** | T026 ‖ T027 | `.github/pull_request_template.md` only — no dependency on any wave. Can run from Wave 0 onward. |
| 2 | Sequential | T008 → T009 → T010 → T011 | US5, subject rule. Same file as waves 3-5. |
| 3 | Sequential | T012 → T013 → T014 → T015 | US1, register rule. |
| 4 | Sequential | T016 → T017 → T018 → T019 → T020 → T021 | US2, draw test + selection table. T020 is the test file. |
| 5 | Sequential | T022 → T023 → T024 → T025 | US3, example rewrites. **Must follow 2-4** — C-6 asserts against every example the feature adds. |
| 6 | Mixed | T028 → T029 → T030 → (T031 ‖ T032 ‖ T033) → T034 → T035 | Polish. The three judgment reads touch no files and parallelize. |

**Single-agent order** (recommended for this S feature):

```
T001 → T002 → T003 → T004 → T005 → T006 → T007
  → T008 → T009 → T010 → T011
  → T012 → T013 → T014 → T015
  → T016 → T017 → T018 → T019 → T020 → T021
  → T022 → T023 → T024 → T025
  → T026 → T027
  → T028 → T029 → T030 → T031 → T032 → T033 → T034 → T035
```

**Every task is assigned to exactly one wave.** 3 + 4 + 2 + 4 + 4 + 6 + 4 + 8 = 35.

---

## Agent Fanning Instructions

Single agent recommended. This is an S feature whose editing tasks are 14/18
concentrated in one prose file; fanning agents at it produces conflicts no merge
strategy resolves.

The only genuine fan-out is Wave 1b — `.github/pull_request_template.md` is a
different file with no dependency, and Wave 6's three judgment reads write
nothing. Neither is worth a second agent at this size.

---

## Verification checklist

- [x] `delivery.md` written to the feature dir
- [x] PR count justified — single PR, 4-signal framework applied
- [x] Issue count equals PR count — 1 issue, 1 PR
- [x] Every task assigned to exactly one wave (35/35)
- [ ] GitHub issues created — **none needed**; #102 exists and is the only issue
- [ ] `Closes` line references exactly one issue — **blocked on the #80 decision above**
- [x] Sub-feature issues linked to parent epic — N/A, no split and no epic
