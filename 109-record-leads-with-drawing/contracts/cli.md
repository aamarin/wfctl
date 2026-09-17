# Contract — command output

**Feature**: `109-record-leads-with-drawing`

Three commands change what they print. Every other command is byte-identical
(SC-006).

## `wfctl arch accept <slug> --agreed "…"`

Refuses a record with no drawing. The refusal is the feature, and SC-005 is its
bar: a reader shown only this can produce a conforming record without opening
the skill.

```
✗ the-drawing-is-required-at-acceptance cannot be accepted yet.
    no drawing: add a fenced block under '## Boundary'
    no declared kind: add 'diagram: data-flow | component | state' to the frontmatter

  data-flow  a value moving between two sides
  component  a line between components
  state      a sequence one thing passes through

  docs/architecture/the-drawing-is-required-at-acceptance.md
```

Refuses a record whose declared kind is not one of the three:

```
✗ some-record cannot be accepted yet.
    'dataflow' is not a diagram kind — use data-flow, component or state

  docs/architecture/some-record.md
```

Exit 1. Nothing is written (FR-004). The three status refusals
(`_not_promotable`) and the citation refusals are unchanged and still print
first — a record that is already accepted says so, rather than being asked for a
drawing it will never need.

Success is unchanged:

```
✓ some-record is accepted — agreed in review of #109
  Logged: - 2026-09-16  accepted    — agreed in review of #109
```

## `wfctl arch accept` with no slug, and the promotable listing

The listing already exists and already claims that what it lists can be
accepted. It now excludes a record acceptance would refuse (FR-007), because
`acceptable` and `accept` read one definition (R-002).

```
✗ Name the record to accept.

  Proposed, and promotable:
    a-record-that-carries-a-drawing

  wfctl arch accept <slug> --agreed "<where the human agreed>"
```

A proposed record with no drawing does not appear. It is not an error and
nothing names it here — the record findings below are where a record's own gaps
are reported.

## `wfctl doctor`

Two findings join the record findings it already prints. Neither reaches the
exit code unless it is an error.

```
✗ some-record: declares diagram 'dataflow', which is not a diagram kind
⚠ session-state-is-re-derived: drawing label 'we are at plan now' appears nowhere else in the record
    records: docs/architecture/
```

`✗` is VR-006 and contributes to exit 1, like every other record error. `⚠` is
VR-007 and does not (FR-008 — a warning stays a warning). The `records:` line is
the existing one; the repair for both is editing the file, and the root is
configurable so it cannot be guessed from the slug.

A record whose drawing has no readable labels — an ASCII sketch, a fence of
prose — produces no VR-007 finding. The check compared nothing and says nothing;
this is the limit R-004 states rather than coverage it implies.
