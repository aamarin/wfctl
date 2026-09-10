# Analysis scan — #325

## Session 2026-09-10

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 7 · Critical: 0 · Acted on: 6 · Accepted: 1
- Detail: `<spec-root>/325-flip-clarify-and-analyze/checklists/analysis-report.md`

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Accepted |
| B · Ambiguity | Clear |
| C · Underspecification | Resolved |
| D · Constitution alignment | Clear |
| E · Coverage gaps | Resolved |
| F · Inconsistency | Resolved |
| Requirement-to-task coverage | 79% before, 93% after |

### Findings

- **F · Inconsistency, HIGH** — T006 and T014 both claimed FR-006 and FR-007, and
  disagreed about how. T006 called itself "a review task with no diff of its own";
  T014 said to state each "as an assertion … rather than as a comment". A reader
  following the list would have done one and believed the other was done.
  → Fixed. T006 became a single property assertion over the whole table — for
  every step, the reported flag equals the table's value, and is `False` whenever
  a reason is present. T014 keeps only FR-009. Decided against keeping both and
  making them agree: two tasks asserting one property is the duplication that
  produced the contradiction.

- **E · Coverage gaps, MEDIUM** — three of five success criteria had no traceable
  task. SC-003 was covered in substance by T004 and T005 and named in neither.
  → Fixed. T006a asserts SC-001 as a count of zero rather than as a decrease, so
  it proves the pipeline has no waiting steps left rather than proving the table
  changed. T006b records SC-002 as uncoverable here and says why. The Phase 1
  verification block names SC-003 against the two tasks that carry it.

- **E · Coverage gaps, MEDIUM** — three of the spec's four edge cases had no task.
  → Fixed. T010a asserts two of them. The third — both steps reached in one
  unattended pass — is subsumed by T006's property, which holds for every step
  from the same table with no shared state, and a task restating it would be a
  third assertion of one fact.

- **C · Underspecification, MEDIUM** — T014 asked for an assertion that "no branch
  reads a fact, a grant, or branch state". That is a negative over code nobody has
  written, and it names no shape a test could take.
  → Fixed by the same rewrite as F1. T006's property takes no argument but the
  step's own name, so any dependence on a fact, a grant or branch state breaks it.
  Decided against a source-inspection test asserting the absence of a branch: it
  passes or fails on formatting, and it would break on a refactor that changed
  nothing about the property.

- **F · Inconsistency, MEDIUM** — Phase 1 numbered T003 after T001 and T002, and
  the Dependencies section said to write it first "if that ordering is easier".
  Two orderings, no rule saying which governed.
  → Fixed. Numeric order is execution order, stated as such, and the failing-first
  demonstration is written as a check on T003 rather than as a reordering.

- **F · Inconsistency, MEDIUM** — four names for one thing across four documents:
  *continuation value*, *continuation flag*, *unattended flag*, and `auto`.
  → Fixed by declaring rather than by normalising. Key Entities now names the
  three that are correct and says which surface each belongs to — the table calls
  it the continuation value, the wire calls it `auto`, and prose written for a
  reader calls it the unattended flag. *Continuation flag* was the fourth and is
  normalised out. Decided against collapsing to one name: `auto` is what a
  consumer reads and cannot be renamed here, and a test named for the wire field
  rather than for what it means is the naming this repository's own conventions
  reject.

- **A · Duplication, LOW** — FR-006 and FR-007 overlap enough to read as one
  requirement.
  → Accepted, not fixed. They constrain different things and a branch can satisfy
  either while breaking the other: a single-site computation that reads one of the
  payload's four facts satisfies FR-006 and breaks FR-007, and a per-step arm
  returning an unconditional `True` does the reverse. One assertion now carries
  both, which is the right economy — the property is one property. That is not a
  reason to make them one requirement.

### Deferred

None. All six passes ran against all three artifacts.

One verification gap stands and is stated rather than closed: SC-002, an
unattended run executing both steps with no prompt, needs a real
`/speckit.orchestrate` run and is blocked on #331, where `analyze` step 8 still
stops to ask whether to apply remediation. Recorded in the task list and carried
to the pull request rather than left to be discovered there.
