# Delivery Plan: is a session open now? (200)

**Feature**: `200-is-a-session-open-now` | **Date**: 2026-09-13
**Source**: `specs/200-is-a-session-open-now/tasks.md` (36 tasks)
**Parent issue**: #200

---

## File-Touch Matrix

Seventeen files, four of them production source. Test files dominate the count
because nine of the twelve non-source files are new assertions, six of which
assert that something *did not* change.

| File | Action | Tasks |
|------|--------|-------|
| `wfctl/_session.py` | MODIFY | T003, T004, T005 |
| `wfctl/cli.py` | MODIFY | T006, T009, T010, T012, T013, T014, T018, T019, T020, T021, T022 |
| `wfctl/_pipeline.py` | MODIFY | T007, T008, T024 |
| `wfctl/agents/skills/speckit-orchestrate/SKILL.md` | MODIFY | T015 |
| `wfctl/agents/skills/start-session/SKILL.md` | MODIFY | T016 |
| `README.md` | MODIFY | T029 |
| `docs/architecture/design/200-session-id-rides-on-the-start-event.md` | MODIFY (status) | T030 |
| `docs/architecture/session-identity-comes-from-the-caller.md` | MODIFY | T031 |
| `tests/test_agent_session.py` | MODIFY | T003, T004, T005, T009a, T018, T019, T020, T022, T023, T023a |
| `tests/test_cli_start.py` | CREATE | T006, T021 |
| `tests/test_cli_status.py` | CREATE | T009, T011, T014 |
| `tests/test_cli_resume.py` | CREATE | T012 |
| `tests/test_cli_end.py` | CREATE | T013 |
| `tests/test_pipeline.py` | CREATE | T007, T008, T024, T027 |
| `tests/test_skills_ship.py` | CREATE | T016, T017a |
| `tests/test_architecture.py` | CREATE | T017 |
| `tests/test_no_regression_unwired.py` | CREATE | T025, T026 |

T001, T002, T028, T032 and T033 edit no file — baseline capture, a by-hand
payload diff, doctor, and the review panel.

**One note for the implementing run.** Seven of the eight new test files are
named in a scheme this repository does not use: `tests/` holds
`test_pipeline_commands.py`, `test_pipeline_sections.py`,
`test_remaining_commands.py` and `test_session_existence.py`, and no file is
called `test_cli_*.py` or `test_pipeline.py`. The names in `tasks.md` are not
wrong — nothing forbids a new scheme — but adopting one halfway is how a reader
later greps the wrong prefix. Decide once, at T003, and apply it to all eight.

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| #TBD | T001–T033 (all 36) | 17: `wfctl/cli.py`, `wfctl/_session.py`, `wfctl/_pipeline.py`, `README.md` (modified), 2 skills (modified), 2 records (modified), 9 test files (1 modified, 8 created) | **L** | `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/` green; `uv run wfctl doctor` with no finding standing; quickstart.md's two-conversation sequence exercised by hand |

**Rationale**: Single PR. All four boundary signals point the same way, and the
file count is the only thing that points elsewhere.

1. **File conflict risk — split is worse.** `wfctl/cli.py` is edited by phases
   2, 3 and 4. Splitting on phase boundaries produces three PRs serially
   rewriting one file; the signal's own rule is that tasks which *can* be
   sequenced stay in one PR, and these can.
2. **Reviewability — bundle.** Phase 3's refusal cannot be judged safe without
   phase 4's takeover on the same screen. A reviewer asked whether it is correct
   to refuse a conversation has to see what that conversation does next.
3. **Mergeable increment — bundle.** `tasks.md` states the rough edge outright:
   phase 3 alone leaves "a refused conversation [with] no way back". Merging it
   alone ships a deadlock in place of a wrong answer, which is not obviously an
   improvement on the defect.
4. **Story independence — bundle.** US2 exists only to give US1 an exit
   ("Building US2 alone produces a takeover nobody is displaced by"); US3
   asserts the *absence* of change in the paths US1 adds. Neither has separate
   acceptance criteria or a separate runtime path.

**The L size is flagged, not split.** The sizing table sends 8–12 files to
"flag for discussion — do not auto-split", and this is 17. What inflates it is
the test surface: nine test files, six of whose assertions exist to prove
nothing moved (T009a, T017, T017a, T023, T026, T027). The production diff is
four files. Splitting the tests from the code they assert against would
manufacture a PR that cannot fail.

**PR closes**: `Closes #200`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #200 | T001–T033 (all 36) | `[200] session_started cannot tell a running session from one that ran once` | 6–8h | PR #TBD |

**Grouping pattern**: Single issue
**Rationale**: One PR closes exactly one issue, and #200 already exists and
states this defect — no issue was created by this run because none was needed.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 | Baseline. No edits. T002's payload is what T028 diffs against, so it must be captured before anything lands |
| 1 | Sequential | T003 → T004 → T005 | All three edit `wfctl/_session.py`. T004 reads T003's `last_session_id` |
| 2 | Parallel | T006 ‖ (T007 → T008) ‖ T009a | Different files: `cli.py`, `_pipeline.py`, `test_agent_session.py`. T007 and T008 are sequential within their lane |
| 3 | Sequential | T009 | `cli.py`, and needs the `PipelineReport` fields T007 added. **Fan-in: full bar green before Wave 4** |
| 4a | Parallel lane | T010 → T012 → T013 → T014 | US1 implementation, all in `cli.py`, sequential within the lane |
| 4b | Parallel lane | T015 ‖ T016 | US1 skills — two different `SKILL.md` files |
| 4c | Parallel lane | T011 ‖ T017 ‖ T017a | US1 `[P]` assertions, three files, none depending on 4a |
| 4d | Parallel lane | T024 → (T025 → T026) ‖ T027 | US3 entire. Touches `_pipeline.py` and two test files; shares no file with 4a–4c |
| 5 | Sequential | T018 → T019 → T020 → T021 → T022, then T023 ‖ T023a | US2. All of T018–T022 edit `cli.py`, which lane 4a also edits — this is the wave that must wait |
| 6 | Sequential | T028 | By-hand diff against T002's payload. Needs 4d complete |
| 7 | Parallel | T029 ‖ T031 | README and the record amendment — different files, neither blocks the other |
| 8 | Sequential | T032 → T030 → T033 | `doctor` and the by-hand skill exercise, then the `arch accept` that needs the reader's citation, then the review panel over the finished change |

**Single-agent order** (fine for this feature — the parallel lanes save one
pass, not a day):
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009a → T009 →
T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 → T017a →
T018 → T019 → T020 → T021 → T022 → T023 → T023a →
T024 → T025 → T026 → T027 → T028 → T029 → T031 → T032 → T030 → T033

---

## Agent Fanning Instructions

**Wave 4 fanning (2 agents).** Lanes 4b and 4c are small enough to fold into
4a's agent; the split that earns its overhead is US1 against US3, because they
share no file and US3's whole job is to prove US1 changed nothing.

**Agent A prompt (US1 — lanes 4a, 4b, 4c):**
```
Branch 200-is-a-session-open-now, Wave 4 lane A. Phase 2 is merged and the
bar is green. Implement T010–T017a from
/Users/andremarin/Development/wfctl-specs/200-is-a-session-open-now/tasks.md,
in that order. Read contracts/cli.md for the two refusal strings before
writing either.

Touch only: wfctl/cli.py, wfctl/agents/skills/speckit-orchestrate/SKILL.md,
wfctl/agents/skills/start-session/SKILL.md, and the test files T011/T016/
T017/T017a name. Do NOT touch wfctl/_pipeline.py — another agent owns it
this wave.

T015 and T016 change shipped skills: the suite checks they ship and
cross-reference, not that they read well, so run `uv run wfctl install-skills`
and exercise the gate by hand per quickstart.md.

Done when `uv run pytest -q`, `uv run ruff check wfctl/ tests/` and
`uv run mypy wfctl/` are green.
```

**Agent B prompt (US3 — lane 4d):**
```
Branch 200-is-a-session-open-now, Wave 4 lane D. Phase 2 is merged and the
bar is green. Implement T024–T027 from
/Users/andremarin/Development/wfctl-specs/200-is-a-session-open-now/tasks.md.

Your job is to prove this feature changed nothing for a caller that presents
no identity. T025 comes before T026 and is not paperwork: it writes down the
gate surface — status, resume, end, start, the orchestrate gate — that SC-002
measures against, and which nobody had enumerated.

Touch only: wfctl/_pipeline.py, tests/test_pipeline.py,
tests/test_no_regression_unwired.py. Do NOT touch wfctl/cli.py or either
SKILL.md — another agent owns them this wave.

Leave T028 alone; it is a by-hand diff against a payload captured in T002.

Done when `uv run pytest -q`, `uv run ruff check wfctl/ tests/` and
`uv run mypy wfctl/` are green.
```

**Fan-in gate after Wave 4:** `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/`

---

## Carried Forward

Two MEDIUM findings from `checklists/analysis-report.md` were accepted rather
than fixed, and both are still open at the point implementation starts:

- **C1** — what `wfctl status` prints so a *later* reader learns the branch
  changed hands. `session_holder` is a current-state field, so a third
  conversation reads `"other"` whether or not a takeover happened. FR-014's
  displaced-conversation half is served; the later-reader half is not. A
  contract question, not a missing test.
- **G1** — `design.md` carries no `## Software design decisions` section, so
  every downstream step resolves this feature's design records as `unknown`
  even though `docs/architecture/design/200-session-id-rides-on-the-start-event.md`
  exists. One heading fixes it, outside analyze's edit scope.

Both belong in the change description's Additional Context if they are still
open when it is written.
