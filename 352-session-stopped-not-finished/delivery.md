# Delivery Plan: Session Stopped, Not Finished (352)

**Feature**: `352-session-stopped-not-finished` | **Date**: 2026-09-11
**Source**: `specs/352-session-stopped-not-finished/tasks.md` (23 tasks)
**Parent issue**: #352

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| PR 1 (unopened) | T001–T023 | `wfctl/agents/skills/start-session/SKILL.md` (modified), `wfctl/_session.py` (modified), `wfctl/cli.py` (modified), `tests/test_start_session_asks_conditionally.py` (modified), `tests/test_session_stopped_not_finished.py` (created) | S | T023 green — all four definition-of-done commands — plus `quickstart.md`'s four manual halves run against a tree installed by `uv run wfctl install-skills` |

**Rationale**: Single PR. Two of the four boundary signals say bundle and neither
of the other two says split.

- **File conflict risk — no.** US1 touches only `SKILL.md` and its row tests;
  US2 touches only `_session.py`, `cli.py` and the new test module. Disjoint.
- **Reviewability — bundle.** The feature is a writer and a reader of one
  contract. A reviewer handed the `--continued` flag without step 9's new row
  cannot tell whether the mark is read correctly, and handed the row without the
  flag cannot tell whether anything writes it.
- **Mergeable increment — bundle.** US1 alone is genuinely mergeable and
  `tasks.md` is right that it works on a hand-marked log, but shipping it alone
  leaves a routing rule whose input no command produces. US2 alone writes a mark
  nothing consults. Either half merged on its own is a state someone has to
  remember is half.
- **Story independence — no split.** The three stories are independent to
  *build*, which is why the waves below fan, and dependent to *review*, which is
  what this signal asks.

Two committed files are not in the table because they are already on the branch:
`docs/architecture/stop-kind-is-a-field-not-an-event.md` (`51c8392`) and the two
scan files under `docs/architecture/scans/`. They ride in the same PR and a
reviewer reads them first — the record is `proposed`, and accepting it is a
human's act at this PR under `a-human-accepts-a-decision`.

**PR closes**: `Closes #352`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #352 | T001–T023 | `A session cut off mid-run cannot say so, so the next one stalls on a question nobody is there to answer` | 3–4 h | PR 1 |

**Grouping pattern**: Single issue
**Rationale**: Five files, one PR, one issue — the XS/S row of the sizing table,
and the parent issue is that issue. One PR closes exactly one issue.

**No issue was created, and that is not a decline.** `wfctl status --json`
reports `notify: true` (`notify_source: local`), so this run was permitted to
create one; there was none to create. The map's only row is keyed `#352`, which
existed before the branch did. Nothing is waiting on a key, so `decompose` is
finished rather than parked.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | Baseline, no edits. Everything below is attributable to this change only if this ran first. |
| 1 | Parallel | T002 ‖ T008 | Both are red-first test writes in different modules. Neither may be skipped to "save a step": T002 is the only automated reach on step 4 and on the quote gate. |
| 2 | Parallel | (T003 → T004 → T005) ‖ (T009 → T010 → T011) | Two lanes, sequential *within* each: the left lane is three edits to one `SKILL.md`, the right lane is `end()` before the flag before the warning. |
| 3 | Parallel | T006 ‖ T012 ‖ T013 | T006 reconciles the skill's prose against the rows wave 2 changed; T012 and T013 are the two `[P]` assertions in separate modules. |
| 4 | Sequential | T007, then T014 | Fan-in. US1's gate and US2's gate. A red T007 here is the wave-1 assertions doing their job, not a regression. |
| 5 | Sequential | T015 → T016 → T017 | US3, and it needs US2's writer from wave 2 to produce a history worth reading. Free to reorder, not free to fan: all three write one module. |
| 6 | Sequential | T018 | Fan-in for US3. |
| 7 | Sequential | T019 → T020 | Same module again. T020's command must include `tests/test_stall.py` — without it two of the three readers it names go unchecked. |
| 8 | Sequential | T021 → T022 → T023 | `uv run wfctl install-skills` first, never a bare `wfctl`. Then all four manual halves — **half 2 is not optional**; a run that exercised only half 1 has not tested the protection FR-005 exists to provide. Then the definition of done. |

**Single-agent order** (recommended — this is an S feature):
T001 → T002 → T008 → T003 → T004 → T005 → T009 → T010 → T011 → T006 → T012 →
T013 → T007 → T014 → T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022 →
T023

---

## Agent Fanning Instructions

Single agent recommended. Five files, and the only real fan — wave 2's two lanes
— saves minutes against the cost of two agents holding one contract between them.

**`[P]` in `tasks.md` means "no dependency", and after `/speckit.analyze` it no
longer means "different file" everywhere it appears.** T017, T019 and T020 lost
their markers in that pass: giving them the explicit file path the task list's
own Format section requires put all three in
`tests/test_session_stopped_not_finished.py`, which fails the second half of the
definition. They are still free to reorder. They are not free to fan.

The wave table above is kept for reuse, and for the one thing it says that the
single-agent order does not: **waves 4 and 6 are gates, not steps.** Running past
a red T007 into wave 5 is how a routing defect reaches the manual halves, where
the only thing that catches it is a human reading a session that started work it
should have asked about.
