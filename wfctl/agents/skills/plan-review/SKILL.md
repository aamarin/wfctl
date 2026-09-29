---
name: plan-review
description: 'Review the technical plan of a feature against its specification, its accepted design records, and the constitution of the repository, after the plan is written and before it is broken into tasks. Use when a plan needs an independent, read-only critique of requirement coverage, architecture and decision compliance, hidden assumptions, failure modes, dependencies, feasibility, and verification readiness. Writes an evidence report and a byte copy of the plan it read, at the paths the invoking command names, and edits nothing it reviews.'
---

# Plan review

## Purpose

This skill reviews a feature's planning artifacts as an independent critic,
after the technical plan exists and before it is broken into tasks. A mistake
in the plan is cheapest to fix at this point, since no task, test, or code has
been built on it yet. The skill keeps review, revision, and workflow authority
apart: it reviews, and someone else revises and decides what happens next.

This is a review method. It is not a planning method, and it does not approve
anything.

## Boundaries

These hold on every run.

1. The review is read-only toward what it reviews. It does not edit `spec.md`,
   `plan.md`, `design.md`, research, data models, contracts, design records,
   the constitution, or source code.
2. The review writes two files and nothing else: the report and the plan copy,
   each at the path the invoking command names.
3. The review does not approve or reject the work. It reports findings and
   their evidence, and the person or workflow that invoked it owns what
   happens next.
4. The review does not create implementation tasks, start implementation,
   commit changes, or open a pull request.
5. The review does not repair a finding, even a small one. A review that
   changes its subject is no longer independent of it.
6. The review does not hand control to a workflow orchestrator at its end. It
   writes the report, summarizes it, and stops, so that whoever invoked it can
   decide whether to revise, review again, or continue.

## What the invoking command supplies

This skill names no path of its own. The command that invokes it names these:

1. The feature directory, which holds `spec.md`, `plan.md`, and the planning
   artifacts.
2. The repository root, which other inputs are read relative to.
3. The report path.
4. The plan copy path.
5. Where the repository keeps its constitution, when it has one.
6. Any conventions its pipeline uses in these artifacts, such as a marker for
   an unresolved clarification, which the deterministic checks then surface.

It may also name inputs it found changed since the earlier report. Treat each
one as step 3 below says.

## Workflow

### 1. Assemble bounded context

Read in this order.

1. Intent and constraints: `spec.md`, then the constitution at the path the
   command names.
2. Technical strategy: `plan.md`, then the planning artifacts it actually relies
   on, such as `research.md`, `data-model.md`, `contracts/`, `quickstart.md`,
   or their equivalents.
3. Accepted design context: `design.md` when present, then the design records
   it lists, following the repository's `reading-design-records` rules when they
   exist. Read other architecture records only when the plan or a listed record
   makes them relevant.
4. Existing implementation, narrowly. Inspect source only to verify a concrete
   claim the plan makes about an existing boundary, API, schema, dependency, or
   behavior. Do not scan the whole repository to appear thorough.

Do not use conversation history as authoritative context when durable artifacts
exist. The point is to test whether another agent could implement the feature
correctly from the repository's durable knowledge alone.

When the repository has no constitution, the review goes on without one. Record
the path the command named, with the identity `absent`, so a later run can tell
that one has since appeared.

When `spec.md` or `plan.md` is absent, the review cannot run. Look for both, and
for the constitution, and read nothing further. Write the report anyway, as
`references/report-format.md` § A review that could not run shows, with a row
for each of those three and the missing one marked `absent`, and stop. Do not
infer the missing artifact from prose elsewhere.

### 2. Bind the review to the exact inputs

Before judging content, record the path and content identity of every input the
review reads. The identity is the output of:

```bash
git hash-object --no-filters <path>
```

`--no-filters` hashes the bytes on disk. Plain `git hash-object` applies a
repository's line-ending rules and clean filters first, so it can report a
different value for a file nobody edited, and the review would then describe a
plan other than the one it read.

Record the identities in the report's `## Reviewed inputs` table, one row per
input:

1. The first cell is the path, relative to the feature directory for a file in
   it and relative to the repository root otherwise.
2. The second cell is the identity, or `absent` for an input the review looked
   for and did not find. Never write `missing`, `none`, or a placeholder there.
3. `plan.md`, `spec.md`, and the constitution each get a row on every run, and
   so do `design.md`, each design record, and each planning artifact the review
   used.
4. On a re-review, the plan copy the review read as its base gets a row too.
5. The report records no row for itself.

### 3. Start from the earlier report, or review in full

Look for an earlier report at the report path and a plan copy at the copy path,
and read the earlier report before anything overwrites it.

Run a re-review when all three of these hold:

1. An earlier report exists.
2. The plan copy exists.
3. The copy's identity equals the identity the earlier report recorded for
   `plan.md`.

A re-review works from the earlier report and the copy:

1. Diff the copy against `plan.md`, using the tool the invoking command names.
2. Review the parts of `plan.md` that changed together with the parts that
   refer to them, such as a section that names a changed field, a test that
   exercises a changed path, or a requirement trace row that points into a
   changed section. Do not limit the review to the changed lines alone, since a
   change is most often wrong where something else still assumes the old text.
3. Compare every other input row of the earlier report with its file now, using
   the same identity command. Leave out three rows: `plan.md`, whose change the
   diff already shows; the plan copy, whose row never matches after a re-review,
   because the same run then overwrites the copy; and a row for the report
   itself, if an older report carried one. A row does not match when its
   identity differs, when its file is gone, or when it says `absent` and the
   file now exists.
4. For each input that does not match, and for each input the command named as
   changed, re-read that input in full and review the whole of `plan.md` against
   it. The plan diff may be empty, since a fix made in `spec.md` or a design
   record leaves `plan.md` as it was, and a review of the diff alone would then
   review nothing.
5. Carry every earlier finding forward under its earlier ID, and mark it `fixed`
   when its evidence no longer holds or `open` when it still does. Give a new
   finding the next unused ID.

Run a full review of the whole of `spec.md` and `plan.md` in every other case,
and say in the report's review scope why: no earlier report, no plan copy, or a
copy whose identity does not match the earlier report's `plan.md` row. A copy
that does not match is treated as missing, because a diff against it would
describe changes the review never saw. When an earlier report exists, still
carry its findings forward and mark each one `fixed` or `open`.

### 4. Run the deterministic checks first

Before any subjective critique, check the facts that need no reviewer opinion.

1. The required artifacts exist and are readable.
2. The plan addresses every in-scope requirement and success criterion in
   `spec.md`, or says why a requirement needs no technical action.
3. The plan introduces no material behavior absent from the spec unless it
   labels that behavior as an assumption, a constraint, or a requested scope
   change.
4. The plan does not silently contradict a decision in a listed design record
   or the constitution.
5. The interfaces, schemas, migrations, external dependencies, and state
   transitions named in one planning artifact agree with the others.
6. Every unresolved clarification marker, TODO, placeholder, or equivalent that
   affects implementation is surfaced as a finding.
7. The verification the plan describes can observe the behavior the spec
   requires, including the important negative paths.

These checks are the factual spine of the review. A reviewer's preference
cannot override a direct contradiction in the artifacts.

### 5. Review through independent lenses

Apply the lenses in `references/review-rubric.md`. Every review uses at least
these three:

1. **Requirements and traceability.** Can every important intent be traced into
   a concrete technical approach without invented scope?
2. **Architecture and boundaries.** Does the plan respect accepted decisions,
   ownership, dependency direction, data boundaries, and the project's actual
   architecture?
3. **Adversarial implementation and verification.** Where would a competent
   implementer still have to guess, and how could the design fail or become
   unverifiable?

Add the security and reliability lens when the feature touches trust
boundaries, authorization, secrets, sensitive data, destructive operations,
concurrency, distributed state, or irreversible migrations. When it touches
none of those, the report says the lens did not apply and why.

When the host can run isolated reviewers or different models, the lenses may run
independently and be synthesized afterwards. When it cannot, run them one after
another in the current agent. Voting across models is optional and is never a
source of truth.

### 6. Form findings from evidence, not taste

Every finding carries these fields:

1. A stable ID, `PR-001`, `PR-002`, and so on, kept across re-reviews of one
   feature.
2. A priority.
3. A category.
4. A status, `open` or `fixed`. A first review has only `open` findings.
5. The exact evidence locations.
6. The concrete gap or contradiction.
7. Why it matters to implementation, correctness, or verification.
8. The smallest useful response to consider.
9. Corroboration, when independent reviewers or lenses found the same issue.

Grade every finding with exactly one of these three priorities:

1. **BLOCKER** means the plan cannot be broken into tasks safely until the issue
   is resolved. Examples are contradictory requirements, an undefined mandatory
   state transition, a violation of an accepted invariant, and a required
   behavior with no testable interpretation.
2. **MAJOR** means implementation can start only by taking a consequential
   unstated assumption or by accepting substantial avoidable risk.
3. **MINOR** means a bounded improvement that forces no architectural or
   behavioral guess.

The tests for each priority are in `references/review-rubric.md` § Priority
tests.

File each finding under one of these categories:

1. Missing Information
2. Requirement / Plan Mismatch
3. Architecture / Decision Conflict
4. Boundary / Ownership Concern
5. Risk / Failure Mode
6. Verification Gap
7. Dependency / Feasibility
8. Assumption Challenge
9. Scope Expansion
10. Enhancement Suggestion

A question the artifacts leave unanswered is a finding in the `Missing
Information` category, and it is graded by what it holds up like any other
finding. A missing answer that stops the plan from being broken into tasks is a
BLOCKER, and one that barely matters is MINOR. Do not answer the question
yourself to make the plan complete.

Do not raise a priority because several reviewers repeat the same opinion. A
single reviewer may still find a BLOCKER when the cited evidence makes the
contradiction objective.

### 7. Synthesize without erasing disagreement

When more than one reviewer or lens ran:

1. Merge findings only when they describe the same underlying issue and cite
   compatible evidence.
2. Record which reviewer or lens corroborated each finding.
3. Keep materially different alternatives or disagreements in their own section
   of the report.
4. Do not turn vote counts into a numeric confidence score.
5. Do not let the synthesis introduce a BLOCKER that no reviewer's evidence
   supports.

The synthesis makes the report shorter and more useful. It does not turn a
range of views into false certainty.

### 8. Write the report and the plan copy

Write the report to the report path the command names, in the structure
`references/report-format.md` gives, replacing any earlier report whole. Then
copy `plan.md` byte for byte to the plan copy path, in the way the command says,
after the review has finished reading the earlier copy as its base.

The report is complete even when it finds no BLOCKER. In that case it says so
and still records the reviewed inputs, the lenses, and every MAJOR and MINOR
finding.

The report never says that the plan is approved, rejected, or ready to
implement, and never states an equivalent verdict on the plan. Keep those three
words and phrases out of the report entirely, quotations of the artifacts
included, so a reader searching the report for a verdict finds none. It may say
`No BLOCKER findings identified in this review.`

### 9. Summarize and stop

Summarize these for whoever invoked the review:

1. The report path.
2. The number of open BLOCKER, MAJOR, and MINOR findings, and on a re-review
   how many earlier findings are now fixed.
3. The highest-impact open themes.
4. Whether any reviewer disagreement remains.
5. That no reviewed artifact was changed.

Then stop. Do not run the next step of any workflow from inside the review.

## What to challenge explicitly

A good review is not a generic best-practices checklist. Challenge a claim when
the feature makes it consequential:

1. A design that covers only the happy path and leaves failure or recovery
   undefined.
2. Ownership split across layers with no single source of truth.
3. State transitions with no concurrency or idempotency semantics where a retry
   is plausible.
4. A migration with no compatibility, rollback, or recovery story where a
   failure would strand data.
5. A new abstraction whose only rationale is hypothetical future flexibility.
6. A requirement whose acceptance language no test or operator can observe.
7. A plan that depends on an API, permission, schema field, or tool nobody has
   verified.
8. A security boundary that relies on hiding something in the interface or on
   caller discipline rather than on enforcement.
9. A "simple" change that quietly crosses a module, service, persistence, or
   public-contract boundary.
10. Generated planning artifacts that disagree with the main plan.

Not every feature has to discuss every concern. An absence is a finding only
when the concern is relevant to the change proposed.

## Requirements-language diagnostic

Use EARS-style event, state, and unwanted-behavior patterns (Easy Approach to
Requirements Syntax, EARS) as a diagnostic aid, not as a mandatory authoring
syntax. When a requirement is ambiguous, ask whether its trigger, state,
response, and observable result are clear enough to implement and verify. Do
not rewrite the specification into EARS, and do not flag ordinary prose for not
using its grammar.

## Feasibility without fake precision

Judge feasibility through concrete dependencies, environment constraints,
unknown integration behavior, migration risk, and required capabilities. Do not
invent hour estimates, and do not treat a model-generated schedule as evidence
unless the repository has a validated estimating method the plan is required to
follow.

## Where this review sits beside other reviews

Three reviews look at a feature's planning, and each keeps its own job:

1. A requirements-quality checklist tests the requirements in a chosen domain.
   It can run earlier, and its results are useful input here when one exists.
2. This review reads the specification, the plan, and the durable design
   context before tasks exist, and emphasizes strategy, assumptions,
   architecture, failure modes, and implementability.
3. A cross-artifact consistency analysis runs after tasks exist, and checks
   coverage and consistency across the specification, the plan, and the tasks.

Keep the three apart rather than growing one reviewer that does all of them.

## References

Read these when the step that names them is reached:

1. `references/review-rubric.md` holds the reviewer lenses, their prompts, and
   the priority tests.
2. `references/report-format.md` holds the report structure and an example.
3. `references/open-source-notes.md` holds where the method came from, and which
   ideas it adopted, adapted, or rejected.
