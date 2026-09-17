# The record leads with a drawing

## Problem Statement

How might we make an architecture record readable at a glance by a human,
without weakening the exact projection an agent already reads from the same
file?

## Recommended Direction

A record declares what kind of drawing it carries, carries one, and cannot be
accepted without it.

Three things had to be settled before any template changes, and the corpus
settled two of them. When #109 was written there were 7 records, 429 lines and
no diagrams at all, and its "cheap now, expensive later" argument rested on
there being nothing to migrate. Twelve days later there are 38 records and 18
level-3 design records, and **22 of the 38 already draw** — in ASCII, inside
`## Context` and `## Decision`, because the template offered nowhere else to put
it. The practice arrived before the slot. What is missing is not the habit but
a name for what a drawing is *of*, and anything that says a record is missing
one.

The second thing the corpus settled is where the requirement can bind. Five
accepted records carry no drawing, and `architecture-decisions` freezes an
accepted body in its own words — *"a missing section in an accepted record is a
date, not a defect."* A requirement that binds every record on disk contradicts
an accepted rule in the skill that would carry it. So it binds on one edge: the
`proposed` → `accepted` transition, which is the only place where the body is
still editable and a human is present to judge whether the drawing is any good.

The third is traceability, and it is the one this design deliberately shrinks.
#109 asks that a diagram element, a record, an agent constraint and a code
boundary name the same concept. Three of those four live inside the record file
and can be compared there. The fourth means resolving a label to a module, and
this repository has done that exactly once — `views/current-state.md`, whose
boxes are literally module names, held honest by
`tests/test_architecture_view.py`. A record's drawing names states and roles.
Resolution against code is a different feature, and pretending otherwise would
buy a check that rejects most records or a per-record map that drifts.

## Behavior — what each state renders

The five reachable states of `wfctl arch accept`, read as the strings they
print:

```
proposed · drawing present · kind declared
  ✓ the-author-declares-the-diagram-kind is accepted — agreed on #351

proposed · no ## Boundary block
  ✗ the-author-declares-the-diagram-kind carries no drawing.
    A record is accepted with the sketch it came out of. Add a `## Boundary`
    block. Nothing was accepted.

proposed · drawing present · no `diagram:` key
  ✗ the-author-declares-the-diagram-kind draws, but declares no kind.
    Add `diagram: data-flow | component | state` to the frontmatter.

proposed · drawing present · a label appears in no other section
  ⚠ the-drawing-is-required-at-acceptance draws `refused`, which appears in
    neither `## Decision` nor `## Owns truth`.
  ✓ …is accepted — agreed on #351

accepted · no drawing
  (nothing — never checked, and `wfctl arch context` projects it unchanged)
```

Read each in its state and ask whether it tells the truth. The fourth is the one
that had to be a warning rather than a refusal: a lifecycle diagram legitimately
introduces state names that no prose sentence needs to repeat, so a refusal
there would fire hardest on exactly the diagrams #109 asked for.

The fifth is the state this design exists to protect. It renders nothing, and
that silence is the answer to the five frozen records.

**The level-3 consequence each of these generates:** the check reads
`Record.body`, which `parse_record` already carries, so no reader opens a record
file twice; and `Record` gains a `diagram` field that is `""` for every file on
disk, which forces absent to read as "not declared" rather than as a default
kind.

## Boundaries and Ownership

The author owns *what kind of diagram this decision needs*. wfctl cannot compute
it — it would have to classify English to decide that "who may assert a verdict"
is ownership and "what a payload carries" is not, across records that share a
vocabulary and differ only in subject.

wfctl owns *may this record be accepted*, which is not a new claim: `acceptable`
already answers it from the status and the presence of a `## Log` section. The
drawing is a third fact of the same kind.

Both are recorded under `wfctl arch-root`, and `wfctl arch context` is unchanged
by either — it projects the first paragraph of `## Decision` and nothing else, so
no drawing in any format reaches the terminal through the projection.

## Software design decisions

- docs/architecture/design/109-traceability-is-label-agreement.md — traceability
  is checked as agreement between the drawing's labels and the record's own
  prose, not by resolving labels against the code.

Level 2 was answered with two records rather than none, and they are not listed
above because they are level-2 records and binding:
`the-author-declares-the-diagram-kind` and
`the-drawing-is-required-at-acceptance`, both under `docs/architecture/`. Level 4
answered nothing yet; the mechanism is chosen in the plan.

## Key Assumptions to Validate

- [ ] A label shared between the drawing and the prose means a shared concept,
      not a shared word. Test: run the label check over all 22 drawing records
      and read every finding. More than a couple of false positives means the
      check is wrong and the baseline was right.
- [ ] Authors draw with the words they already use in prose. Test: the same run
      — a record whose drawing says `svc` for what the prose calls "the tracker
      backend" is the falsifying case.
- [ ] Three kinds are enough. Test: classify the 22 existing drawings into
      data-flow, component and state. A drawing that fits none is the signal.
- [ ] Mermaid renders on GitHub in this repository's records. Test: open one of
      the two records that already carry a mermaid `## Boundary` on github.com —
      the test suite cannot see this and never will.

## MVP Scope

In: the `diagram` frontmatter key and its three values; `## Boundary` promoted
from optional to required in `record-template.md`; the drawing check in
`acceptable` and `accept`; the label-agreement warning; constants in wfctl held
against the shipped template by a test, following `required-sections-are-wfctls`.

Out: touching any record already on disk. The eleven proposed records with no
drawing gain one when someone accepts them, which is where the cost belongs.

## Not Doing (and Why)

- **Resolving diagram labels to code symbols** — a record's boxes name states
  and roles, not modules. The one drawing in this repo whose boxes are module
  names already has a test; a second mechanism for records would reject most of
  them or need a per-record map that drifts.
- **A `traces:` frontmatter list naming the code a record binds** — a new claim
  about which code a decision governs is a level-2 question, and answering it
  inside this feature would draw a boundary nobody asked for.
- **Backfilling the five accepted records** — forbidden by an accepted rule, and
  the counting it would make tidy is not worth rewriting finished history for.
- **Inferring the diagram kind from prose** — every available mechanism is a
  keyword heuristic, and one wrong in ten produces a refusal the author cannot
  argue with.
- **Amending #86's principles in this change** — the issue suggests wording for
  the epic. That is the epic's edit, made once the three records here are
  accepted rather than while they are proposed.

## Open Questions

- Does the label check belong in `validate` alongside the link-integrity
  findings, or beside `acceptable`? `validate` returns `Finding`s with a
  warning level already, which is the shape this needs; `acceptable` is where
  the refusals live. The two answers put the warning in different commands.
- Whether `component` and `data-flow` are distinguishable enough in practice to
  be separate values, or whether the 22 existing drawings collapse into two
  kinds rather than three.
