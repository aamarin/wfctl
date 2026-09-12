# Analysis Report — level3 downstream (#326)

**Date**: 2026-09-10
**Artifacts**: `spec.md`, `plan.md`, `tasks.md` — all three present and read
**Also read**: `research.md`, `data-model.md`, `contracts/record-list.md`,
`contracts/step-report.md`, `contracts/pass-g.md`, `design.md`

## Findings

| ID | Pass | Severity | Summary | Disposition |
| --- | --- | --- | --- | --- |
| A1 | F · Inconsistency | CRITICAL | SC-005 was already false on this branch | Fixed |
| A2 | C · Underspecification | MEDIUM | Pass G's comparison scope left open between tasks and plan | Fixed |
| A3 | E · Coverage gaps | MEDIUM | FR-002a had an implementation task and no test | Fixed |
| A4 | E · Coverage gaps | MEDIUM | An edge case had no requirement and no task | Fixed |
| A5 | F · Inconsistency | LOW | "record set" and "record list" used for one thing | Fixed |

### A1 — SC-005 contradicted the branch it measures (CRITICAL)

**Was**: *"The change touches only files under `wfctl/agents/commands/` and their
tests, verifiable from the branch diff."*

**Observed**: `git diff --stat origin/main...HEAD` on this branch returns three
files, none of them under `wfctl/`:

```
docs/architecture/design-md-indexes-the-records.md              | 118 ++
docs/architecture/design/326-contradiction-is-a-seventh-pass.md | 171 ++
docs/architecture/scans/121-clarify.md                          |  64 ++
```

A success criterion that its own change already fails is worse than an absent
one: it either blocks a correct change or gets waived, and waiving one teaches
the next reader to waive the rest. FR-012 was always the narrower and correct
statement — it forbids touching `wfctl/` *outside* `wfctl/agents/commands/`, and
says nothing about `docs/`. SC-005 had generalised it into something FR-012 never
claimed.

→ **Fixed**: SC-005 now measures what FR-012 states, names `docs/architecture/`
and `tests/` as expected, and specifies `git diff --name-only origin/main...HEAD`
as the command.

→ **Decided against widening FR-012 to match SC-005**: that would forbid the
records this feature exists to make routine, in the change that introduces them.

→ **Decided against dropping SC-005**: FR-012 is the constraint that keeps a
predicate change out of a PR whose subject is skill prose, and a constraint with
no measurement is the shape `a-rule-is-expressed-as-a-check` refuses when the
violation *is* visible in an artifact the work produces. Here it is — the diff.

### A2 — Pass G's comparison scope (MEDIUM)

FR-005 said pass G reads "the same artifacts its existing six passes read", which
is `spec.md`, `plan.md` and `tasks.md`. FR-008 and `contracts/pass-g.md` scope
the comparison to tasks. Whether a `plan.md` element contradicting a record is a
finding was left to the implementer.

→ **Fixed**: FR-005a. Tasks only, with the reason — the plan is what the tasks
were derived from, so a contradiction there surfaces as the tasks carrying it,
and reporting both doubles every finding. Added to T013.

→ **Decided against including plan elements**: it would catch a contradiction one
step earlier, and pay with a duplicate finding for every real one. Epic #121
item 6's own wording is "no task silently contradicts an approved record".

### A3 — FR-002a had no test (MEDIUM)

The bullet-only parse rule is the requirement with the most consequence and the
smallest surface: without it, prose naming a level-2 record loads that record as
level-3, which binds nothing while looking like it does. T003 settles the wording;
no test asserted it survived into the four wrappers. T009 asserts three other
strings and T022 asserts the three states.

→ **Fixed**: T009a, asserting all four wrappers state the rule, with a docstring
naming the failure rather than restating the assertion.

### A4 — The unreadable-path edge case had no requirement (MEDIUM)

The spec's Edge Cases described what a step does with a listed path that does not
exist, or one outside the repository. `contracts/record-list.md` specified the
behaviour. No functional requirement demanded it and no task built it, so it
would have been implemented by whoever happened to read the contract.

→ **Fixed**: FR-013, plus T009b for the three steps and T013a for analyze —
including what pass G does with such a record, which the contract had not said: no
finding, because a record nobody could open is not one a task can be shown to
contradict.

### A5 — Terminology drift (LOW)

"record set" in `spec.md` and `contracts/pass-g.md`; "record list" in
`data-model.md`, `contracts/record-list.md` and Key Entities; "applicable set" in
`design.md`.

→ **Fixed**: standardised on "record list", which is the term Key Entities
defines. Six occurrences replaced.

## Coverage

Requirement-to-task coverage: **14 of 14** functional requirements have at least
one task. Success criteria: **6 of 6**.

| Requirement | Tasks |
| --- | --- |
| FR-001 | T003, T005–T007, T012 |
| FR-002 | T003 |
| FR-002a | T003, T009a |
| FR-003 | T004, T005–T007 |
| FR-004 | T004, T020 |
| FR-005 | T013 |
| FR-005a | T013 |
| FR-006 | T013, T017, T018 |
| FR-007 | T013 |
| FR-008 | T013, T017 |
| FR-009 | T014, T020, T025 |
| FR-010 | T014, T019 |
| FR-011 | T008 |
| FR-012 | T026 |
| FR-013 | T009b, T013a |

## Not fixed

**FR-007 has no verifying exercise.** No record in this repository carries
`superseded` or `rejected`, so nothing can demonstrate that a task contradicting
one produces no finding. Recorded in the spec's Assumptions and left there: a
fixture record created solely to test a lifecycle transition would be a record
nobody decided, in a directory whose whole premise is that every file in it
records a real decision.

**The pass G reliability assumption stands unresolved by design.** That a model
detects a prose contradiction at all is the bet `326-contradiction-is-a-seventh-pass`
records. T017 is the test; a clean verdict there reopens the decision rather than
producing a bug fix, which the task says out loud.
