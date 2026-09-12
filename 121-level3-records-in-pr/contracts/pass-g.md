# Contract — pass G, design-record contradiction

The seventh detection pass in `/speckit.analyze`, beside the six that exist. It
reads the same artifacts they do, plus the record list the record-list contract
resolves.

## What it asks

For each task in `tasks.md`, and each record in the resolved set: does the task
do the opposite of what the record binds?

**Two sections bind: `Decision` and `Consequences`.** Never `Considered`,
`Direct baseline`, or the baseline half of `Diagram` — those describe what was
rejected, so a task implementing the shape that won reads as contradicting them.

Not *is the task unrelated to the record* — most are. Not *does the task fail to
mention the record* — a record is not a checklist. The question is reversal: the
record says the strategy is chosen at the call site, the task says inject it.

## Severity

Read from the record's frontmatter `status`:

| `status` | A task reversing it |
| --- | --- |
| `approved` | CRITICAL |
| `proposed` | warning |
| `superseded` | no finding |
| `rejected` | no finding |

`approved` means a human ratified the decision, so reversing it is a defect
rather than a change of mind. `proposed` means the decision was put and not
ratified, so a task reversing it may be the design moving — worth reporting,
not worth blocking.

Gating on `approved` alone was the literal reading of epic #121 item 6, and it is
rejected on evidence: every record in this repository is `proposed`, and an
unattended run approves none, so the pass would ship correct and never fire.

A `superseded` or `rejected` record produces no finding because a retired
decision is not one a task can violate. No record here carries either status yet;
this row is written from the template's stated lifecycle and recorded in the
spec's Assumptions as such.

## What a finding carries

```markdown
- **G · Design-record contradiction, CRITICAL** — T014 reverses an approved
  decision.
  Record: `docs/architecture/design/326-contradiction-is-a-seventh-pass.md`
  Decision: "Contradiction detection is a seventh pass beside the six that
  already exist, reading the record list as one more input to the same read."
  Task: "T014 Add `wfctl design check-tasks` comparing declared invariants"
```

The record by path and the task quoted, both, per FR-008. That is what makes a
finding disputable: pass G is a model's judgment rather than a mechanical check,
so two runs over the same tasks can disagree, and a reader who thinks the pass
misread the record needs both halves in front of them to say so.

## The coverage row

Written on every run, including runs that read no records. Between
`F · Inconsistency` and `Requirement-to-task coverage`, which stays the only row
carrying a percentage.

```
| G · Design-record contradiction | Clear (2 records read) |
| G · Design-record contradiction | 1 CRITICAL             |
| G · Design-record contradiction | 1 warning              |
| G · Design-record contradiction | None listed            |
| G · Design-record contradiction | No design.md           |
```

The row and not a findings line, for the reason the whole scan file exists: a
findings list renders identically for a thorough pass over clean artifacts and
for a pass that never ran.

## What pass G does not do

**It does not edit anything.** `speckit-analyze` is read-only of `spec.md`,
`plan.md` and `tasks.md`, and the wrapper's existing override covers exactly one
new file the step writes about its own work. Pass G adds a row to that file and
nothing else.

**It does not gate the pipeline.** A CRITICAL finding is reported, and step 8's
offer of remediation is still an offer. Nothing in this feature refuses a
transition.

**It does not read a record outside the resolved list**, and it does not fall
back to globbing `<arch-root>/design/` when the list is empty. `None listed` is
an answer.
