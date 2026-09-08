# Delivery Plan: notify authority (280)

**Feature**: `280-outward-facing-authority` | **Date**: 2026-09-08
**Source**: `specs/280-outward-facing-authority/tasks.md` (32 tasks)
**Parent issue**: #280

---

## File-touch matrix

| Task | File | Op |
|---|---|---|
| T001 | `docs/architecture/wfctl-classes-the-action-not-the-command.md` | MODIFY |
| T002 | `wfctl/_pipeline.py` (comment near `_unkeyed_issues`) | MODIFY |
| T003–T005, T008a | `wfctl/_session.py` | MODIFY |
| T006–T008, T008b | `tests/test_session.py` | CREATE/MODIFY |
| T009 | `wfctl/_pipeline.py` (`build_report`) | MODIFY |
| T010, T015, T017, T023, T024 | `wfctl/cli.py` | MODIFY |
| T011, T018 | `wfctl/agents/skills/speckit-delivery-plan/SKILL.md`, `wfctl/agents/skills/end-session/SKILL.md` | MODIFY |
| T012, T013, T019–T021, T025, T026 | `tests/test_cli_status.py`, `tests/test_session.py` | MODIFY |
| T016 | `wfctl/_session.py`, `wfctl/cli.py` | MODIFY |
| T014, T022 | — | MANUAL |
| T027 | `AGENTS.md` | MODIFY |
| T028 | `docs/architecture/a-human-grants-outward-facing-authority.md` | MODIFY |
| T029, T030 | — | PROCESS |

**Distinct files: 10.** Size **L** by the sizing table (8–12 files), which the
skill routes to *flag for discussion, do not auto-split*.

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| #1 | T001–T032 | `wfctl-classes-the-action-not-the-command.md` (M), `a-human-grants-outward-facing-authority.md` (M), `wfctl/_session.py` (M), `wfctl/_pipeline.py` (M), `wfctl/cli.py` (M), `speckit-delivery-plan/SKILL.md` (M), `end-session/SKILL.md` (M), `tests/test_session.py` (C/M), `tests/test_cli_status.py` (C/M), `AGENTS.md` (M) | L | Four gates green, `wfctl verify` recorded, **both** manual exercises done — T014 with the grant absent and T022 with it present |

**Rationale**: One PR. Decided 2026-09-08 after the boundary question below was
put to the owner.

The two signals that favoured splitting both turned on *reviewability under
risk* — that a reviewer could assess the refusal path without holding the
question of an agent writing to a tracker. Weighed against a ten-file feature
whose two halves are not independent, that was not worth a second review cycle
over the same files. The split's benefit is real and small; its cost is a
rebase, a second issue, and the same reviewer reading `_session.py` and `cli.py`
twice.

**The ordering argument survives the decision.** Building refusal before grant
still holds inside the single PR — Phase 3 lands before Phase 4, and T014
exercises the ungranted path before T015 exists to grant anything. What was
dropped is a review boundary, not a construction one.

**PR #1 closes**: `Closes #280`

**Consequence worth stating**: an L PR is the size this repo's own guideline
routes to discussion rather than to a default, so the review carries more than
usual. `tasks.md`'s phase checkpoints are the reviewable slices inside it, and
the commit sequence should follow them rather than arriving as one diff.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #280 | T001–T032 | `[280] notify authority: grant, refuse, report` | L | PR #1 |

**Grouping pattern**: Single issue.
**Rationale**: One PR closes exactly one issue, and #280 is that issue. The
sub-feature split proposed earlier was declined — see *PR Decomposition*.

**No issues were created, and none are needed.** The single-issue grouping closes
#280 directly, so `decompose` has no tracker write left to make. The row above
carries a real key rather than `_(TBD)_`, which is what moves this step from
in-progress to done.

That is worth naming rather than celebrating: this feature exists because
`decompose` cannot create issues unattended, and the reason this run got past it
is that the chosen grouping needed no issues created — not that the problem was
solved. A two-issue split would have stopped here exactly as it did before.

---

## Parallelization waves

| Wave | Tasks | Parallel? | Gate |
|---|---|---|---|
| 0 | T001, T002 | [P] — different files | Vocabulary consistent before anything reads it |
| 1 | T003, T004, T005, T008a | Sequential — all edit `wfctl/_session.py` | Resolver exists |
| 2 | T006, T007, T008, T008b | [P] — independent assertions | Resolver proven, including FR-008 from the granted side |
| 3 | T009, T010, T011 | [P] — `_pipeline.py`, `cli.py`, skills | Refusal renders |
| 4 | T012, T013 | [P] | Automated coverage of the refusal |
| 5 | T014 | Manual, blocking | **Grant absent.** The half a grant feature usually ships without |
| 6 | T015, T016, T017, T018 | Sequential — `cli.py` then callers | Grant settable and readable |
| 7 | T019, T020, T021 | [P] | Automated coverage of the grant |
| 8 | T022 | Manual, blocking | Grant present; `notify-action` lands in the log |
| 9 | T023, T024 | Sequential — same file | Decline and ceiling |
| 10 | T025, T026 | [P] | T026 asserts from a **granted** fixture or proves nothing |
| 11 | T027–T030 | Sequential | Review panel, then the PR |

All eleven waves are PR #1. The wave boundaries are the commit
boundaries inside it, and `tasks.md`'s phase checkpoints are what a reviewer
reads it in.

---

## Issue creation — none required

The single-issue grouping closes #280, which already exists. Nothing here needed
a tracker write, so nothing was refused.

The earlier two-issue proposal did need two, and stopped: `_unkeyed_issues` read
the `_(TBD)_` cells and reported `decompose ▶ 2 issue rows without a key`. That
is the wall #240 is parked against, and it was reached from the inside before the
grouping decision removed it.
