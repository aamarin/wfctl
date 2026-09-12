# Delivery Plan: level3 downstream (326)

**Feature**: `121-level3-downstream` | **Date**: 2026-09-10
**Source**: this feature's `tasks.md` (33 tasks) — `wfctl feature-paths` prints
the directory; it is not `specs/<branch>/` in this repository
**Parent issue**: #121 (epic — this branch does not close it)

---

## File-touch matrix

| Tasks | File | Action |
|---|---|---|
| T005, T008, T009b, T020, T021 | `wfctl/agents/commands/speckit.plan.md` | modify |
| T006, T008, T009b, T020, T021 | `wfctl/agents/commands/speckit.tasks.md` | modify |
| T007, T008, T009b, T020, T021 | `wfctl/agents/commands/speckit.implement.md` | modify |
| T012–T015, T013a, T020, T021 | `wfctl/agents/commands/speckit.analyze.md` | modify |
| T009, T009a, T009b, T016, T022 | `tests/` — the existing skill-shipping suite | modify |
| T001–T004, T010, T011, T017–T019, T023–T029 | — | read-only, or a decision with no file |

**Five files.** Four wrappers and one test module. Size **M** by the sizing
table, which maps to a single PR and a single issue.

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| one | T001–T029 | the four `wfctl/agents/commands/speckit.*.md` wrappers (modified), `tests/` (modified) | M | The four definition-of-done commands green through `uv run`, the review panel run, and T017 having actually fired |

**Rationale**: Single PR. Signal 2 decides it — a reviewer cannot assess whether
the four wrappers agree about the record list without seeing all four, and the
whole risk of this change is four copies of one instruction drifting into four
subtly different rules. Signal 1 agrees: T020 and T021 touch every wrapper the
story phases also touch, so splitting would put concurrent edits to the same four
files in two PRs for no gain.

Signal 4 is the dissent and it is real — US1 and US2 are independently testable
and independently valuable. It loses to signal 2 here because the files overlap
completely; a split would be two reviews of the same four files rather than two
reviews of two things.

**PR closes**: `Closes #326`

**Do not add `Closes #121`.** The epic has eight scope items and this is item 6.
It outlives this branch, and a comment on #121 saying item 6 landed is the right
shape.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #326 | T001–T029 | `[326] Plan, tasks and implement are written against level-3 records none of them reads` | half a day | PR one |

**Grouping pattern**: Single issue
**Rationale**: Size M with total file overlap between the phases; the sizing
table and both dominant boundary signals point at one issue and one PR.

**Nothing to create.** #326 was filed during this feature's brainstorm pass and
is the row's key. `wfctl status --json` reports `notify: true` and
`notify_source: local`, so this run *is* granted the authority — the map simply
has no unkeyed row for it to exercise. That is a completed decompose, not a
declined one, so no `wfctl notify issue-create --declined` is filed: nothing was
skipped.

#327 exists and is deliberately not in this map. It is a finding this feature
surfaced, not a piece of this feature's work, and no task here delivers it.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Parallel | T001 ‖ T002 | No dependencies. T001 must be green through `uv run`, not a bare `wfctl` |
| 1 | Parallel | T003 ‖ T004 | Wording only, no file. **Blocks everything below** — this is the text the four wrappers copy |
| 2 | Parallel | T005 ‖ T006 ‖ T007 ‖ T012 | Four different files, no shared state. T012 belongs to US2 and can start here |
| 3 | Sequential | T008 → T009b → T013 → T013a → T014 → T015 | T008 describes the three edits from wave 2, so it follows them. T013–T015 all edit `speckit.analyze.md` and must sequence |
| 4 | Parallel | T009 ‖ T009a ‖ T016 ‖ T022 | Tests. Same module, so treat as sequential if the suite file is one file |
| 5 | Sequential | T020 → T021 | Reads all four wrappers as written; verifies wording rather than adding it |
| 6 | Sequential | T010 → T011 → T017 → T018 → T019 → T023 → T024 → T025 | **Gate: `uv run wfctl install-skills` first.** These are the only tasks that verify the feature works rather than that it shipped |
| 7 | Sequential | T026 → T027 → T028 → T029 | T028 is the review panel and it is not optional; T029 opens the PR |

**Single-agent order** (recommended — this is an M feature whose parallelism is
worth little, since every wave-2 branch reconverges at wave 3):

T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T009a → T009b →
T010 → T011 → T012 → T013 → T013a → T014 → T015 → T016 → T017 → T018 → T019 →
T020 → T021 → T022 → T023 → T024 → T025 → T026 → T027 → T028 → T029

---

## Agent Fanning Instructions

Single agent recommended. The wave table above is reference rather than a plan to
execute: wave 2's four branches each take minutes and all four reconverge at wave
3, so fanning costs more in coordination than it returns.

**The one gate worth naming explicitly**, because it is the step that makes every
verification task below it meaningful:

```bash
uv run wfctl install-skills      # before wave 6, and `uv run` is not optional
```

A bare `wfctl install-skills` installs *its own* copy of the wrappers just
edited. The command succeeds, the tree looks installed, and the change is nowhere
in it — so every exercise in wave 6 would test the released wheel and pass.

**Fan-in gate after wave 6:** T017 must have produced a CRITICAL finding on a
real run. If it produced a clean verdict, stop — that falsifies
`326-contradiction-is-a-seventh-pass`, and the next move is that record's `Log`
and a reopened decision, not a fix.
