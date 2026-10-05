# Artifact Contract

A walkthrough writes two files, and they go to different places on purpose. The
answers are about a person, so they stay on that person's machine. The marker
is about the work, so it goes where wfctl reads evidence.

| File | Where | Committed | Holds |
|---|---|---|---|
| Answers | `$(wfctl state-dir)/walkthrough/<mode>-<YYYY-MM-DDTHH-MM-SS>.md` | never, by anyone but the person | every challenge, answer, disposition, and gap |
| Marker | `FEATURE_DIR/plan-walkthrough.md` or `FEATURE_DIR/change-walkthrough.md` | as the repository treats its feature directory | the mode, what was walked through, the date, and nothing else |

Never write an answer, a disposition, a gap, or a count to the feature
directory. A repository that commits its specs would put them in the pull
request, and this one archives feature directories to a pushed branch.

## The answers file

A new file on every run that asks at least one question. `<mode>` is `plan` or
`change`. Create `$(wfctl state-dir)/walkthrough/` if it does not exist. Write
it as the interview goes, so a run the person stops keeps what was answered.

```markdown
# Plan Walkthrough

Mode: plan | change
Status: complete | incomplete
Walked through: sha256:<hex> of plan.md | <commit id>

## Sources
- [artifact or path read as evidence]

## Challenges

### W1 - [short decision name]
Claim: [the plan or code claim being explained]
Question: [the material question]
Why it matters: [why this question was worth asking]
Answer: [the person's answer, in their words]
Evidence: [paths, tests, records, or NONE]
Disposition: SETTLED | REVISION_REQUIRED | DEFERRED | UNRESOLVED
Consequence: [what this means for the plan, the code, or the workflow]

### W2 - ...

## Open challenges
- [only unresolved or deferred items]

## Outcome
Settled: [count]
Revision required: [count]
Deferred: [count]
Unresolved: [count]
Next action: [advance, revise the plan, revise the code, or a person's decision]
```

`Status: incomplete` means the person stopped before the outcome. An incomplete
run writes no marker.

## The marker

Written only when an attended walkthrough reaches its outcome. It is the
evidence a declared pass reads, and it holds nothing about how the person did.

```markdown
Mode: plan
Walked through: sha256:<hex>
Date: YYYY-MM-DD
```

- **Plan mode**: `plan-walkthrough.md`, and `Walked through` is the sha256 of
  `FEATURE_DIR/plan.md`. Compute it with `sha256sum <FEATURE_DIR>/plan.md`, or
  `shasum -a 256 <FEATURE_DIR>/plan.md` where `sha256sum` is missing, with the
  path `wfctl feature-paths` printed in place of `<FEATURE_DIR>`, and record the
  hex digest only. A bare `plan.md` names a file in the working directory, which
  is not the plan: the feature directory usually sits outside the repository.
- **Change mode**: `change-walkthrough.md`, and `Walked through` is the commit id
  of `HEAD` from `git rev-parse HEAD`.

Exactly these three lines. A second run in the same mode overwrites the marker.

## Disposition meanings

### SETTLED

Only when the answer explains the mechanism concretely and, where it matters,
points to evidence or an explicit accepted tradeoff.

### REVISION_REQUIRED

The walkthrough shows the plan or the code has to change. Say exactly what has
to be reconsidered, as a gap in the work. Do not make the change.

### DEFERRED

Postponed on purpose, and the postponement does not invalidate the current
step. Record the owner, trigger, or condition that reopens it. "Later" is not a
deferral.

### UNRESOLVED

A material question has no answer the person can give yet.

## Evidence rules

Good evidence includes:

- accepted architecture or design records;
- repository code that enforces the claimed invariant;
- schemas, constraints, or type contracts;
- tests that show the relevant behavior;
- logs or reproducible observations when debugging existing behavior;
- explicit external contracts or API documentation.

A model's assertion, a reviewer's agreement, a confidence score, or a repeated
paraphrase is not evidence by itself.

## Mutation rule

The answers file may describe changes the work needs. The walkthrough never
makes them: it does not edit the plan, the code, or the architecture records.
The person may carry a gap into the plan afterwards, worded as a gap in the
plan.
