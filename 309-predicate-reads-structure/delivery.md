# Delivery Plan: predicate reads structure (309)

**Feature**: `309-predicate-reads-structure` | **Date**: 2026-09-09
**Source**: `309-predicate-reads-structure/tasks.md` (17 tasks)
**Parent issue**: #309

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| #1 | T001–T017 | `wfctl/_pipeline.py` (modified), `tests/test_pipeline_sections.py` (created), `docs/architecture/required-sections-are-wfctls.md` (created, already committed) | S | all four gates green: `pytest -q`, `ruff check wfctl/ tests/`, `mypy wfctl/`, `wfctl doctor` |

**Rationale**: Single PR. The three stories share one file, one decision and one
argument. #309 holds `specify` and `plan` together on purpose — they resolve the
same way or they contradict each other — so splitting them into two PRs would
duplicate the level-2 record's argument into two reviews that must agree. US3
(clarify's annotation) was folded in on the maintainer's call after being raised
as a candidate for its own issue; it changes no state and is ten lines.

**PR closes**: `Closes #309`

No parent epic closes here. #100 is the epic this sits under (scope item 5) and
it has other scope items open.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #309 (Issue A) | T001–T017 | `[309] specify and plan read structure; clarify says why it skipped` | S | PR #1 |

**Grouping pattern**: Single issue
**Rationale**: One decision, one file, one reviewable argument — the default
pattern, and the one #309's own "why the two are one issue" section requires.

---

## Sequencing

```
T001 T002 T003          foundation, no behaviour change
   │
   ├──► T004 T005 T006  US1  specify
   ├──► T007 T008 T009  US2  plan
   │
T010 T011               US3  clarify annotation, independent
T017                    the flags pin, independent
   │
   └──► T012 T013 T014 T016   drift, corpus, docs, isolation
              │
              └──► T015  record status — maintainer's word only
```

**Parallelization**: none worth taking. Every task but T017 lands in one of two
files, and the phases are minutes apart.

---

## Out of scope for this delivery

- **#308** — `tasks.md` with no checkboxes clearing `tasks` and `implement`.
  Same audit, live branch, different question.
- **#314** — the one-signature predicate restructure. Its handoff says this
  lands independently; if it merges first, this rebases into the shape it left
  and the argument does not change.
- **Flipping any continuation flag.** T017 exists to prove none moved.

---

## Verification before opening the change

- The four gates above.
- The two exercises a green suite does not cover: T006/T009 (the `x` case) and
  T013 (a real spec dir still reading `done`).
- The review panel (`fanning-out-code-review`), whose disposition table goes in
  the PR body — a clean pass and a skipped panel are indistinguishable without
  it.
