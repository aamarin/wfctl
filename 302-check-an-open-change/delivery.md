# Delivery plan: check an open change

**Branch**: `302-check-an-open-change` | **Date**: 2026-09-09

## File-touch matrix

| Task | Files |
| --- | --- |
| T001, T002 | read-only — git state, baseline suite |
| T003, T004, T005 | MODIFY `wfctl/_tracker.py`, `tests/test_tracker.py` |
| T006 | MODIFY `wfctl/agents/skills/scaffold-tracker/SKILL.md` |
| T007, T008, T015 | CREATE then MODIFY `tests/test_change_check.py` |
| T009, T010, T017, T018, T019 | CREATE then MODIFY `wfctl/_change.py` |
| T011, T012, T020, T021 | MODIFY `wfctl/cli.py` (`change_cmd`), CREATE then MODIFY `tests/test_change_cli.py` |
| T013 | MODIFY `wfctl/agents/configs/github/.agents/trackers/github.json` |
| T014, T016 | CREATE `tests/test_change_config.py`, MODIFY `tests/test_change_cli.py` |
| T022 | MODIFY `wfctl/agents/skills/opening-a-change/SKILL.md` |
| T023 | MODIFY `AGENTS.md` |
| T024, T026, T027 | read-only — grep, live exercise, definition of done |
| T025 | MODIFY `wfctl/cli.py` (help text) |
| T028 | read-only — review panel over the diff |

Nine files modified, four created. That is **M** on the sizing table: single PR,
one issue.

## PR boundary decision

All four signals point the same way.

| Signal | Answer |
| --- | --- |
| File conflict risk | High *within* the feature — `_change.py`, `cli.py` and two test files are touched by both stories. Sequenceable, so one PR |
| Reviewability | A reviewer cannot assess the comparison without the command that composes it, or the command without the config that feeds it |
| Mergeable increment | US1 alone is mergeable and useful, but US2 carries the step that calls the check. Shipping US1 alone leaves a check nothing invokes — the prose problem again |
| Story independence | US1 and US2 share runtime path and state. Not independent |

**One PR, closing #302.**

## Issue grouping map

| Issue | Tasks | Scope |
| --- | --- | --- |
| #302 | T001–T028 | The whole feature — both user stories, foundational work, and polish |

Single-issue pattern, the default for an M-sized feature delivered by one PR.

## What was split out, and why

#306 — a decision record whose `Considered` section can be empty and still pass
every check — was found during this feature's design pass and filed while it was
in front of us. It was originally planned into this PR.

That was wrong twice over. `speckit-delivery-plan` holds that **one PR closes
exactly one issue, always**, and the argument for pairing them priced a *stacked*
PR: merge commits and the async merge API. These two share no code, so they were
never a stack. #306 belongs on its own branch off `main`, running in parallel,
which costs nothing.

Its work is four tasks — a pure section read in `wfctl/_arch.py`, a new
`tests/test_arch_considered.py`, one finding added to `arch_check_cmd`, and a
sweep of the 24 existing records to confirm none newly fails. None of those files
appears in the matrix above.

## Parallelization waves

| Wave | Tasks | Gate |
| --- | --- | --- |
| 1 | T001, T002 | clean tree, green baseline |
| 2 | T003 → T004 → T005, then T006 `[P]` | `tracker-check github` still passes |
| 3 | T007 → T008 → T009 → T010 | comparison tests green |
| 4 | T011 → T012 → T013 | `change check` runs end to end |
| 5 | T014 `[P]`, T015, T016 | config and degrade tests written |
| 6 | T017 → T018 → T019 → T020 → T021 | every state implemented |
| 7 | T022, T023 `[P]` | the check is invoked by something |
| 8 | T024 `[P]`, T025 `[P]` | grep clean, help text updated |
| 9 | T026 → T027 → T028 | live exercise, definition of done, review panel |

Parallelism is thin on purpose. Almost every implementation task lands in
`_change.py` or `cli.py`, and marking more `[P]` than this would be a claim the
file-touch matrix contradicts.

## Issue creation

None needed. Both issues already exist — #302 was filed before this branch, #306
during the design pass. The map's `Issue` column carries real keys, so no
placeholder rows are waiting on a grant.
