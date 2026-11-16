---
status: accepted
governs: architecture-records
---

# One reader turns a fence or an SVG into the same drawing summary

## Context

`record-drawing-can-be-svg.md` lets a record's drawing be a mermaid fence or an
SVG file. wfctl runs four checks on a drawing:

1. Whether the record has a drawing at all, for each declared kind.
2. Whether every label appears in the record's prose.
3. Whether a sequence shows its failing step.
4. Whether a label runs past the drawing's edge, which is new with SVG.

Currently, each check reads the fence's text and parses mermaid syntax where it
needs to. With SVG, every check has to read a second format, and a third format
would mean changing all four again.

## Verified

- `wfctl/arch/_records.py:427` `_drawing` returns "the text inside the first
  fenced block under `## Boundary`", and `:471` `_drawings` returns the same for
  each `### <kind>` heading. Both return a string.
- `_labels` (`:778`) and `_draws_a_failure` (`:416`) take that string and parse
  mermaid syntax with regular expressions.
- The callers are all in `_records.py`: `validate` (`:360`, `:362`, `:375`,
  `:393`), `_sequence_drawing` (`:538`, `:540`), `_drawing_refusals` (`:584`),
  and `accept_blockers` (`:665`, `:677`). No other module calls them.
  `_evidence.py:1591` reaches them only through `accept_problems`.
- `Record` carries `path` (`_records.py:70`), so an image link can be resolved
  against the record's own folder.
- The bundled expat is 2.6.3 under Python 3.11.14 (`pyexpat.version_info`).

## Assumed

- Python's `xml.etree.ElementTree` is safe enough for SVG files committed to
  the repository. Expat 2.4.1 and later limit entity expansion, and wfctl
  requires Python 3.11. A supported Python whose bundled expat is older than
  2.4.1 would falsify this.
- A label's width can be estimated from its character count and font size
  well enough to catch text running off the edge. On the drawings the skills
  teach, a label that visibly overflows while the estimate says it fits, or the
  reverse, would falsify this.

## Direct baseline

Keep `_drawing` and `_drawings` returning a string, and teach each check both
formats. `_drawing` returns either the fence text or the SVG file's text.
If the text is an SVG, `_labels` and `_draws_a_failure` each parse it with
ElementTree, and otherwise they run the mermaid regular expressions. The new
edge check reads SVG only. It adds no new type, and no new function besides
the edge check.

## Decision

A drawing reader turns the drawing under each heading into one summary: the
drawing's labels, whether it shows a failing step, and any labels running past
its edge. A fence goes to the mermaid reader, which holds the existing
regular expressions. An image link goes to the SVG reader, which parses the
file. The four checks read only the summary and never see either format.

If the SVG file is missing, the SVG reader reports no drawing, and the summary
names the path so the refusal can show it.

## Diagram

```
          baseline                                  decision

stable    ┌──────────────┐                          ┌──────────────┐
          │ four checks  │                          │ four checks  │
          └──────────────┘                          └──────────────┘
           │          │                                    │ reads
           │ parses   │ parses                             ▼
           │          │                             ┌──────────────┐
           │          │                             │ summary (new)│
           │          │                             └──────────────┘
           │          │                               ▲          ▲
           │          │                       builds  │          │ builds
volatile   ▼          ▼                      ┌────────┴─┐  ┌─────┴──────┐
   ┌───────────┐ ┌──────────┐                │ mermaid  │  │ SVG reader │
   │ mermaid   │ │ SVG file │                │ reader   │  │   (new)    │
   │ fence     │ │          │                └──────────┘  └────────────┘
   └───────────┘ └──────────┘
```

In the baseline, each of the four checks parses each format, so there are
eight parse arrows. A third format adds four more, one per check. In the
decision, the checks read one summary, and each format has one reader that
builds it, so there are three arrows. A third format adds one reader and one
arrow. A fifth check reads the summary and adds one arrow in the decision,
where the baseline needs one arrow per format.

## Considered

- **The baseline, with each check handling both formats.** It's smaller
  today, with no new type. We didn't choose it because the format knowledge
  ends up spread across four checks, so a third format, or a fix to how one
  format is read, means finding and changing every one of them.
- **Convert an SVG into mermaid text and keep the checks as they are.** The
  checks wouldn't change at all. We didn't choose it because the conversion
  would have to invent mermaid syntax for a failing step (`alt` or `-x`) from a
  class name, and an error in that translation would show up as a check result
  that matches neither the SVG nor the record.
- **A `Drawing` class hierarchy with one subclass per format.** It would work
  equally well. We didn't choose it because the summary is three read-only
  values computed once, so a frozen dataclass built by two plain functions
  covers it without the indirection (`python-pattern-selection`: a function before a Strategy
  hierarchy).

## Consequences

The mermaid regular expressions move into the mermaid reader unchanged, so
records that pass today keep passing.

Each check now reads a summary built once per drawing, instead of parsing the
text again. A record with several kinds builds one summary per kind.

A bug in a reader shows up in every check at once. That's easier to notice
than a bug in one check's copy of the parsing, but it breaks more checks.

## Verification

- The existing tests for mermaid labels and failing steps pass unchanged
  against the mermaid reader.
- Each check is tested once with an SVG summary and once with a mermaid
  summary, with no format-specific code in the check.
- `grep -n "ElementTree\|<text" wfctl/arch/_records.py` finds SVG parsing only
  inside the SVG reader.
- A label that overflows on a rendered drawing triggers the edge warning, and
  one that fits doesn't.

## Log

- 2026-11-13  proposed  — the level-3 gate for #740
- 2026-11-15  accepted  — Andre, in the #740 implement session on 2026-11-15
