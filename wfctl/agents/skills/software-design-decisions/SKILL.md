---
name: software-design-decisions
description: 'Write a level-3 design decision as a durable record — one file per structural choice, carrying the direct baseline it beat and the two graphs that show what the choice changed. Use when a design weighed credible alternatives for how something is structured. Use when a pattern was selected, or deliberately rejected. Use when a structural choice was settled in conversation and only the resulting code would record it.'
---

# Software design decisions

## Overview

A level-3 record holds one structural choice. It is not the design document:
`design.md` describes a feature while it is being built and is closed when it
ships. This holds the part still worth reading afterwards — the direct baseline
the choice beat, and the difference between the two.

It exists because `specs/` is gitignored and `spec_root` resolves outside the
tree, so a reviewer reading the PR never sees `design.md`. A structural argument
made only there is made to nobody.

## When to Use

Write a record when a structural choice weighed credible alternatives:

- A pattern was selected — or deliberately rejected, which is the same decision
  and just as worth recording.
- Two shapes of the same code were compared and one won, including when the one
  that won was the baseline.
- A schema or contract took one form where another form would also have worked.

This is the `.agents/skills/design-levels` level-3 gate's answer in durable
form. That skill decides *which level you answer at*; this one is where a
level-3 answer lands.

**Not for**: a choice with no credible alternative. An implementation that only
ever had one shape is not a decision, and saying so is an answer rather than a
missing record.

**Not here**: a choice that draws or moves a boundary. That is level 2, and it
belongs in `.agents/skills/architecture-decisions`. See *Escalation* below —
the tell is in the diagram, not in how large the change feels.

The template's own opening comment reads the other way — "whether or not it
draws a line" — and this skill governs where that conflicts. Read it as lowering
the bar for a level-3 record, not as admitting boundary decisions into one: a
binding decision filed under `design/` is invisible to `wfctl arch context`,
which is the outcome both readings agree is wrong.

## Where records live

```bash
wfctl arch-root     # prints the root; level-3 records go in `design/` under it
```

A record is `<arch-root>/design/<issue>-<decision>.md`. Ask for the root rather
than assuming it: a repo can declare `arch_root` in its manifest, and
`<repo>/docs/architecture` is the default, not the truth.

`design/` is a subdirectory rather than a prefix because the two kinds of record
are read for different reasons. Level-2 records are the constraints in force —
`wfctl arch context` projects them, and a session loads them before touching
code. Level-3 records are durable and never binding. A reader looking for what
constrains them should not have to filter level-3 files out by name.

## Writing one

Copy `design-record-template.md` from this skill's directory and fill it in. The
template carries the field guidance and the placement rule; do not restate them
here or in the record.

`Direct baseline` and `Diagram` are the two an agent drops first, and the two
the format exists for. Fill them from the template rather than from memory.

## Escalation

The template's `Diagram` section carries the tell: a divider appearing there for
the first time means the decision was level 2. Read it before starting, not
while filling the field in — by then the record is written.

Route such a decision up and write it with
`.agents/skills/architecture-decisions` instead. A level-2 decision filed as
level 3 reads as settled, is not in force, and is not projected by `wfctl arch
context` — so it binds nothing while looking like it does, which is worse than
never having written it.

## An approved record is not renamed, and its body is not edited

For `architecture-decisions`' reason and not a new one: the filename is the slug
inbound `supersedes` fields name, and a body edited afterwards makes the record
agree with the present. A changed decision is a new record naming the old one.

The template's frontmatter carries the status values and who may move them.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The baseline is obviously worse — no need to write it out." | Then it costs two lines. The record that skips it is the one where the baseline was never actually considered. |
| "The alternatives are in `design.md`." | `design.md` is gitignored and closes when the feature ships. That is the gap this record fills. |
| "I'll write it once the code settles." | Then it describes whatever got built. The record is what the implementation is written against. |
| "This one is structural *and* draws a boundary, so one record covers both." | It does not. The boundary is level 2 and binding; splitting them is what keeps `wfctl arch context` honest. |

## Verification

- [ ] The record is under `<arch-root>/design/`, named for the issue being
      implemented rather than its epic.
- [ ] `Direct baseline` describes a real no-new-abstraction implementation,
      concretely enough to compare against.
- [ ] `Diagram` carries two graphs with the same components, and a paragraph
      naming what they differ by.
- [ ] No divider in the diagram is new. If one is, this was level 2.
- [ ] `Considered` carries at least one real alternative with the true reason it
      was not chosen. Losing on fit is a reason; a weakness the alternative does
      not have is never one.
- [ ] `status` is `proposed`, and `Log` has a dated line saying why it was
      written.
