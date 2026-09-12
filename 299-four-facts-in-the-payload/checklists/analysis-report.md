# Analysis report: four facts in the payload

**Feature**: #299 | **Date**: 2026-09-10
**Artifacts**: `spec.md`, `plan.md`, `tasks.md` — all three present and read.
Supporting: `data-model.md`, `contracts/facts-payload.md`, `research.md`,
`design.md`, and the two committed records.

## Verdict

Satisfied. Seven findings, none CRITICAL. Six fixed, one accepted.

## Requirement-to-task coverage

Before: 11 of 15 functional requirements had a task naming them — **73%**. The
four uncovered were all prohibitions (FR-005, FR-008, FR-014, FR-015), which is
the shape that goes uncovered because nothing fails when a prohibition is merely
believed.

After T024: **100%**.

## Findings

- **F · Inconsistency, MEDIUM** — `spec.md` § Key Entities called the second
  fact "definition of done verified" while `data-model.md` and
  `contracts/facts-payload.md` name it `definition of done`. FR-007 has a
  consumer keying on `name`, so two spellings across the artifacts is a defect
  and not a style question.
  → Fixed. Key Entities now names the four wire spellings and says why they are
  shorter than the questions they ask. Decided against renaming the field to the
  longer form: it is the column width in the console block, and 29 characters of
  left-justification for one row is what pushed the details past 80 columns.

- **B · Ambiguity, MEDIUM** — FR-004 described the three values in prose ("met,
  unmet, or does not arise") and never gave the literals, while the
  Clarifications section three screens below settled them as `met` / `unmet` /
  `n/a`. An implementer reading the requirements section alone would have
  invented a third spelling.
  → Fixed. FR-004 now carries the literals.

- **C · Underspecification, MEDIUM** — `data-model.md` said the first derivation
  reads `Evidence`, and `_infer_steps` never builds an `Evidence` when no spec
  dir resolves. The signature was underspecified at exactly the input the spec's
  own edge case names.
  → Fixed. The derivation takes `Evidence | None`. Decided against constructing
  an empty `Evidence` for that case: three empty strings would be
  indistinguishable from a feature directory holding three empty files, which is
  a different state with a different answer.

- **D · Constitution alignment, MEDIUM** — `plan.md`'s Performance Goals
  described the cost as landing on `wfctl status`. T003 moves the trunk
  correction into `build_report`, which has five call sites, so `next`, `resume`
  and `end` each gain two local git calls they do not pay today. The complexity
  gate was passed against a cost statement that was smaller than the change.
  → Fixed. Performance Goals now names all five call sites. The gate still
  passes — the calls are local and `research.md` already listed the sites — but
  it now passes against what is actually being spent.

- **E · Coverage gaps, MEDIUM** — four functional requirements had no task.
  FR-005 (every detail is actionable), FR-008 (no new step state), FR-014
  (`blocks` untouched) and FR-015 (no view composes a fact) are the four
  prohibitions, and prohibitions are the requirements that quietly become
  intentions.
  → Fixed. T024 states each as an assertion. Decided against folding them into
  the existing tests: a prohibition asserted as a side effect of a feature test
  disappears the moment that test is rewritten, and these four outlive the
  feature.

- **F · Inconsistency, LOW** — `design.md`'s level-1 mock rendered the second
  fact's detail as `verified at 47e3e9c`; the contract says `passed at <sha7>`.
  → Fixed in `design.md`. Decided against changing the contract to match the
  mock: `passed` is the word `verification_block` and `wfctl verify` already use
  for this outcome, and the mock was written before the contract existed.

- **A · Duplication, LOW** — the four facts and their owners are written out in
  the level-2 record, `design.md`, `spec.md`, `data-model.md` and
  `tasks.md`. Five copies of one table.
  → Accepted. Four of the five are gitignored and are closed when the feature
  ships; the fifth is the record, which is the copy a reviewer opens and the only
  one that outlives the branch. The copies serve different readers at different
  moments — the record states ownership, the data model states derivation, the
  tasks state order — and collapsing them to one pointer would send a reader
  writing a test off to read an ownership argument. This is the same trade #307's
  own analysis made in the other direction, and it went the other way there
  because the three copies were of *assumptions*, which have no per-reader form.

## Deferred

- **Non-Functional** — the measurement behind the performance assumption. It
  needs a real repository and a timing run, and it belongs to implementation:
  `research.md` names the five call sites, and the level-3 record names what
  would falsify the assumption.
