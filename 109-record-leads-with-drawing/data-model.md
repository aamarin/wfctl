# Data Model — record leads with drawing

**Feature**: `109-record-leads-with-drawing` | **Date**: 2026-09-16

The record is an existing entity with an existing data model; this feature adds
one field to it and two derived values read off its body. Nothing here is a new
store — a record is a markdown file, and everything below is computed from that
file on every read (`session-state-is-re-derived`, applied one directory over).

---

## Record

`wfctl/_arch.py`, `@dataclass(frozen=True)`. Existing fields unchanged.

| Field | Type | Source | Absent reads as |
|---|---|---|---|
| `slug` | `str` | filename stem | — |
| `path` | `Path` | glob | — |
| `status` | `str` | frontmatter `status` | `""` |
| `supersedes` | `str` | frontmatter `supersedes` | `""` |
| `body` | `str` | the file, verbatim | `""` (unreadable) |
| **`diagram`** | **`str`** | **frontmatter `diagram`** | **`""`** |

`diagram` is carried verbatim, including a value outside `DIAGRAM_KINDS`.

**Why verbatim, where `status` is normalised to `""`.** `parse_record` maps an
unrecognised status to `""` because that excludes the record from the projection,
which is the safe direction for a value nobody declared. `diagram` has no safe
direction: normalising `dataflow` to `""` produces a refusal reading "declares no
kind" against a file whose author declared one, and the author cannot see the
difference between their typo and their omission. So the value survives parsing
and FR-003's finding names it.

## Diagram kind

A closed set, held in `wfctl/_arch.py` beside the records that read it:

```python
DIAGRAM_KINDS = ("data-flow", "component", "state")
```

| Value | The decision it suits |
|---|---|
| `data-flow` | a value moving between two sides — who computes it, who may assert it |
| `component` | a line between components — what is inside, what is outside |
| `state` | a sequence one thing passes through — a lifecycle, a transition, a gate |

A tuple rather than a frozenset, because the refusal prints them and the order
they print in is the order the guidance lists them (FR-012). `STATUSES` is a
frozenset for the opposite reason — nothing prints it.

Held against `record-template.md` by a test (FR-010, R-009), following
`_REQUIRED_SPEC_SECTIONS` and `tests/test_pipeline_sections.py`.

## Drawing

Derived, not stored. `_drawing(record) -> str` returns the text inside the first
fenced block under the record's `## Boundary` heading, or `""`.

```
record.body
  └─► _section_bounds(lines, "## boundary")
        ├─ None ─────────────────────► ""        no such section
        └─ (heading, end)
             └─► first fenced block in that range
                   ├─ none ──────────► ""        section present, nothing drawn
                   ├─ empty interior ► ""        fence with no content
                   └─ interior ──────► the text  a drawing
```

Content is never inspected (clarification Q2). A fenced block holding prose is a
drawing to this feature, and that is deliberate: the alternative is a rule that
tells a picture from a code sample, which the corpus does not support.

The first block, not all of them. A second fence under the same heading is a
second drawing of the same boundary and nothing needs to choose between them;
the check that a drawing exists is satisfied by the first, and the label check in
R-004 reads the first because that is the one the reader leads with.

## Label

Derived from a Drawing. The text inside `"…"`, `[…]`, `{…}`, or following `:` on
a transition line. `<br/>` and `<br>` are whitespace. `[*]`, mermaid's start and
end marker, yields no label.

A label's **content words** are its alphanumeric tokens of more than two
characters that are not closed-class English (`the`, `is`, `from`, …).

## Acceptance blockers

Derived. `accept_blockers(record) -> list[str]`, the single definition of what
acceptance refuses (R-002).

| Condition | Blocker |
|---|---|
| no `## Log` section to append to | `no '## Log' section to append to` |
| `_drawing(record) == ""` | `no drawing: add a fenced block under '## Boundary'` |
| `diagram` is `""` | `no declared kind: add 'diagram: <one of …>' to the frontmatter` |
| `diagram` not in `DIAGRAM_KINDS` | `'<value>' is not a diagram kind — use one of …` |

The kind conditions do not test for a drawing. A record missing both reports
both, which is what the ordering sentence below is about — were the kind blocker
gated on a present drawing, such a record would report one blocker and there
would be no order to fix.

Order is reading order, and it is load-bearing for FR-005: a record with no
drawing and no kind reports the drawing first, because adding a kind to a record
with nothing drawn fixes nothing.

Status is **not** a blocker. `acceptable` tests `status == "proposed"` itself and
`accept` raises `ValueError(record.status)` as it does today — the three status
refusals have their own sentences in the CLI chosen from `record.status`
(`wfctl/cli.py:1670`), and folding them in would make one list carry two
vocabularies.

---

## Validation rules

Existing: VR-001 (an illegal status never parses), VR-002 (superseded with no
successor, warning), VR-003 (dangling `supersedes`, error), VR-004 (split
supersession, error), VR-005 (an accepted record's body is never edited).

Added by this feature:

| | Rule | Level | Where |
|---|---|---|---|
| **VR-006** | a record's `diagram` is `""` or a member of `DIAGRAM_KINDS` | error | `validate` |
| **VR-007** | a `proposed` record's drawing labels each share a content word with the rest of the record | warning | `validate` |

VR-006 is an error and runs on every record, accepted ones included — it reads
the frontmatter, which VR-005 does not freeze, and a misspelled kind is wrong
whatever the status. VR-007 is a warning and runs on `proposed` only (R-005).

Neither is a blocker. `accept_blockers` answers "may this be accepted", `validate`
answers "is the record set well-formed", and VR-006 appears in both because a
misspelled kind is both a malformed record and a reason to refuse.

## State transitions

Unchanged, with one edge newly guarded:

```
[*] ──► proposed                       drawing not required to write
         │
         ├─ accept, blockers empty ──► accepted     body frozen
         ├─ accept, blockers ────────► refused ──► back to proposed
         └─ supersede ──────────────► superseded
accepted ──► superseded │ retired
```

The guard sits on one edge. Every record already past it is never re-read
(FR-006, SC-002).
