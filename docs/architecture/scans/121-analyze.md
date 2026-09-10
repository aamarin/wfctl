# Analyze scans — #121

## Session 2026-09-10

- Verdict: satisfied
- Scanned: `spec.md`, `plan.md`, `tasks.md` — all three present and read
- Findings: 5 · Critical: 1 · Acted on: 5 · Accepted: 0
- Detail: `<FEATURE_DIR>/checklists/analysis-report.md`

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Clear |
| C · Underspecification | Resolved |
| D · Constitution alignment | Clear |
| E · Coverage gaps | Resolved |
| F · Inconsistency | Resolved |
| G · Design-record contradiction | Clear (1 record read) |
| Requirement-to-task coverage | 100% |

**Pass G ran after the other six, and after the change that created it.** The
first pass of this session had no pass G, because the feature that adds it had
not been implemented — so the row above was written by re-running G alone against
this feature's `tasks.md` once `speckit.analyze.md` carried it. Extending this
session rather than opening a second: the sessions a reviewer distinguishes are
separated by the pipeline advancing, not by the clock, and nothing advanced.

Its input was the one record `design.md` lists,
`docs/architecture/design/326-contradiction-is-a-seventh-pass.md`
(`status: proposed`). Its `Decision` is that contradiction detection is a model
pass beside the other six rather than a `wfctl` command comparing declared
invariants. No task reverses it — T012 through T016 implement exactly that shape,
and no task adds a command. Hence `Clear`, and the record count is stated so that
a reader can tell this from a run that had nothing to read.

Pass D reads Clear against substituted gates rather than a constitution: this
repository ships no `.specify/memory/constitution.md`, so `plan.md`'s Constitution
Check draws its gates from `AGENTS.md` and the ten records `wfctl arch context`
projects, and records the substitution in Complexity Tracking as the template
requires. Checked against `vendor-upstream-skills`, `layer-model`,
`knowledge-placement` and `a-rule-is-expressed-as-a-check` specifically; no
requirement conflicts with any of them.

### Findings

- **F · Inconsistency, CRITICAL** — SC-005 said the change touches only
  `wfctl/agents/commands/` and its tests. The branch already carried three files
  under `docs/architecture/` — the two design records and the clarify scan — so
  the criterion was false about its own change before any wrapper was edited.
  FR-012 was always the narrower and correct statement: no file under `wfctl/`
  *outside* `wfctl/agents/commands/`.
  → Fixed: SC-005 now measures FR-012, names `docs/architecture/` and `tests/` as
  expected, and specifies `git diff --name-only origin/main...HEAD`.
  → Decided against widening FR-012 to match: it would forbid the records this
  feature exists to make routine, in the change that introduces them.
  → Decided against deleting SC-005: the violation *is* visible in an artifact
  the work produces, which is the case `a-rule-is-expressed-as-a-check` says to
  express as a check rather than as prose.

- **C · Underspecification, MEDIUM** — FR-005 gave pass G the same three
  artifacts the other six read, while FR-008 and the contract scoped the
  comparison to tasks. Whether a `plan.md` element contradicting a record is a
  finding was left to whoever implemented it.
  → Fixed: FR-005a, tasks only, added to T013.
  → Decided against including plan elements: it catches a contradiction one step
  earlier and pays a duplicate finding for every real one, since tasks are
  derived from the plan.

- **E · Coverage gaps, MEDIUM** — FR-002a, the bullet-only parse rule, had an
  implementation task and no test. It is the requirement with the most
  consequence and the smallest surface: without it, prose naming a level-2 record
  loads that record as level-3.
  → Fixed: T009a asserts all four wrappers state the rule.
  → Decided against relying on T009: that test asserts three other strings, and a
  test that passes while the rule is missing is worse than no test.

- **E · Coverage gaps, MEDIUM** — the spec described what a step does with a
  listed path that does not exist or sits outside the repository, and no
  requirement demanded it. The behaviour existed only in
  `contracts/record-list.md`.
  → Fixed: FR-013, with T009b and T013a. The fix also answered a question the
  contract had not: pass G produces no finding for an unreadable record, because
  a record nobody could open is not one a task can be shown to contradict.
  → Decided against leaving it in the contract alone: a contract with no
  requirement behind it is implemented by whoever happens to read it.

- **F · Inconsistency, LOW** — "record set", "record list" and "applicable set"
  named one thing across five documents.
  → Fixed: standardised on "record list", the term Key Entities defines.
  → Decided against defining the synonyms instead: cheaper to write and it leaves
  a reader deciding whether two names mean two things.

### Deferred

- **FR-007 has no verifying exercise.** No record in this repository carries
  `superseded` or `rejected`, so nothing can demonstrate that a task
  contradicting one produces no finding. Left in the spec's Assumptions rather
  than fixtured: a record created solely to exercise a lifecycle transition is a
  record nobody decided, in a directory whose premise is that every file in it
  records a real decision.
- **The pass G reliability assumption.** That a model can see a prose
  contradiction at all is the bet `326-contradiction-is-a-seventh-pass` records
  as the one everything rests on. T017 is its test, and a clean verdict there
  reopens the decision rather than producing a bug fix. Not a finding — a
  dependency on a run that has not happened yet.
