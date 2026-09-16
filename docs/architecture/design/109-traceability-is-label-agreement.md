---
status: proposed
---

# Traceability is checked as label agreement inside the record, not as resolution against the code

## Context

#109's third scope item asks that "a diagram element, a record, an agent
constraint, and a code boundary must be able to name the same concept", and that
changing one projection updates the others or surfaces detectable drift.

Four projections, and they are not equally reachable. Three of them live in the
record file: the drawing's node labels, the prose in `Owns truth`, and the text
`wfctl arch context` emits, which is the first paragraph of `Decision`. The
fourth is the code, and reaching it means resolving a label like "the author" or
"the owning side" to a module, a class or a function.

This repository has done the fourth exactly once.
`docs/architecture/views/current-state.md` draws wfctl's modules and
`tests/test_architecture_view.py` parses the drawing and compares it against an
import graph derived by walking the source. It works because every box in that
drawing is a module name — a string that exists in the code — and because there
is one such drawing.

A record's drawing is not that. `the-drawing-is-required-at-acceptance` draws
boxes labelled "record written" and "body frozen from here", which name states in
a lifecycle and resolve to nothing in `wfctl/`.

The two accepted records that constrain this are
`a-rule-is-expressed-as-a-check`, which asks whether a violation is visible in an
artifact the work already produces, and `required-sections-are-wfctls`, which
settles that wfctl pins what an artifact must carry and a test holds the pin
against the shipped template.

## Verified

- `tests/test_architecture_view.py:19` binds `VIEW` to
  `docs/architecture/views/current-state.md`, and its module docstring says the
  drawing is "compared against an import graph derived from" the source — one
  drawing, whose boxes are module names.
- `wfctl/_arch.py:207` `decision_text` projects `## Decision`; the skill states
  it projects "the first paragraph of `Decision`", so no other section reaches
  the terminal through `arch context`.
- `wfctl/_arch.py:114` `parse_record` lifts `status` and `supersedes` off the
  frontmatter onto `Record`, and carries the whole file as `body` — so a section
  scanner needs no second read.
- 22 of 38 records under `docs/architecture/` carry a drawing in a fenced block;
  the box-drawing characters sit under `## Context` (72 lines) and `## Decision`
  (50) far more often than under `## Boundary` (30), measured by walking the
  fences.
- `docs/architecture/pipeline-state-is-one-payload.md` and
  `session-state-is-re-derived.md` carry a `## Boundary` section in mermaid,
  added by `1e7fa41` — written by hand before `record-template.md` had the
  section at all.

## Assumed

- That a label appearing in both the drawing and `Owns truth` is evidence the
  two projections mean the same thing. Falsified by a record that reuses a word
  in two senses — "source" as a data origin in the drawing and as a manifest key
  in the prose would pass a check that means nothing.
- That authors will draw with labels they already use in prose rather than
  inventing diagram-only shorthand. Falsified by the first record whose drawing
  says `svc` for what the prose calls "the tracker backend"; the check then
  fires on a record that is not wrong, and the cost lands as noise.

## Direct baseline

Require nothing. Ship the declared kind and the acceptance gate from the two
level-2 records, and let "traceable projections" be satisfied by the drawing and
the prose sitting in one file where a reader sees both.

Concretely: no parser, no label extraction, no new test. The reader is the check,
and drift surfaces at review when someone notices the picture and the paragraph
disagree.

## Decision

Traceability is checked as agreement between the drawing's labels and the
record's own prose. Every label in the `## Boundary` block must appear somewhere
in `## Owns truth` or `## Decision`; a label that appears nowhere else is the
finding.

Resolution against code is not attempted. The record names concepts; whether a
concept corresponds to a module is a question `views/current-state.md` already
answers for the one drawing whose boxes are module names.

## Diagram

```
              baseline                          decision

stable   ┌──────────────────┐            ┌──────────────────┐
         │  record file     │            │  record file     │
         │  Boundary  Owns  │            │  Boundary  Owns  │
         └──────────────────┘            └────┬────────┬────┘
                                              │ reads  │ reads
═══ wfctl pins what an artifact carries ══════╪════════╪═══════════
        (required-sections-are-wfctls)        │        │
                                              ▼        ▼
volatile        (no reader)                ┌──────────────────┐
                                           │ label agreement  │
                                           │ check            │
                                           └──────────────────┘
                                                    │ names
                                                    ▼
                                           ┌──────────────────┐
                                           │ the record, at   │
                                           │ accept           │
                                           └──────────────────┘
```

The two graphs differ by one reader. The baseline has none — the drawing and the
prose sit in the same file and nothing compares them. The decision adds a reader
that stays inside the file, and the divider is the one already in force: wfctl
pins what an artifact must carry. Nothing in either graph reaches `wfctl/*.py`,
which is the boundary this record deliberately does not draw.

## Considered

- **Resolve labels against the code, as `test_architecture_view.py` does** —
  the strongest reading of #109's "a code boundary must name the same concept",
  and it has working prior art in this repository. It loses on what the labels
  are: a record's drawing names states and roles, not modules, so resolution
  would either reject most records or need a per-record map saying which labels
  are code names. The map is a third projection, and it drifts.
- **A `traces:` frontmatter list naming the code symbols a record binds** —
  makes resolution possible without parsing labels, and gives `arch context` a
  new thing to project. Equally sound and out of scope here: it is a new
  ownership claim about which code a decision governs, which is a level-2
  question, and answering it inside a level-3 record is the escalation
  `software-design-decisions` refuses by name.
- **Check nothing, per the baseline** — genuinely defensible, and it is what
  every record on disk lives under today. It loses to `a-rule-is-expressed-as-a-
  check` on that record's own test: the disagreement is visible in the record,
  which is an artifact the work already produces, so prose alone is the gap that
  record names rather than an acceptable answer.
- **Considered extracting labels with a mermaid parser** — rejected; the block is
  read for node labels only, and a dependency that parses the whole grammar earns
  no property the check needs.

## Consequences

Gained: a drawing that says something the prose does not is caught while the
record can still be edited, and the check costs one pass over two sections of a
file already in memory as `Record.body`.

Harder: a record whose drawing legitimately introduces a label — a state name
like "refused", which no prose sentence needs to repeat — now has to mention it
in prose or carry a finding. That is a real cost and it falls on the author of
exactly the lifecycle diagrams #109 asked for.

The failure mode this introduces is a check that passes on agreement of spelling
rather than of meaning. It cannot tell a shared word from a shared concept, and
the `Assumed` section above is where that is written down rather than discovered.

## Verification

A test over this repository's own corpus: every `proposed` record with a
`## Boundary` block passes the label-agreement check, or the ones that fail are
named and their failures are the noise case above rather than real
disagreements. If more than a couple of the twenty-two drawing records fail on
labels a reader would call fine, the check is wrong and the baseline was right.

## Log

- 2026-09-16  proposed  — the level-3 gate for #109's traceability scope item
