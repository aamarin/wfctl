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

Two of its sections are the reason the format exists, and both are the ones an
agent drops first.

**`Direct baseline` is mandatory and is never "none".** The smallest
implementation that introduces no new abstraction always exists, and the record
is the comparison against it. A baseline written as a sentence of hand-waving
justifies a decision rather than making one. When the baseline won, that is the
decision — record it as one.

**`Diagram` is two graphs, not one.** Baseline and decision, same components in
each, and one paragraph naming what they differ by. That difference is the
argument the rest of the record cites. Two identical graphs say nothing, which
is why a record whose baseline won draws the strongest alternative it beat
rather than drawing itself twice.

## Escalation

A level-3 record draws only dividers already in force. **A divider appearing for
the first time means the decision was level 2** — stop, route it up, and write a
record with `.agents/skills/architecture-decisions` instead.

This is the one check that cannot be deferred to review. A level-2 decision
filed as level 3 reads as settled, is not in force, and is not projected by
`wfctl arch context` — so it binds nothing while looking like it does.

## Status

`proposed` → `approved` → `superseded` | `rejected`. Only a human moves a record
past `proposed`; write `proposed` and leave it there.

An approved record is not renamed and its body is not edited, for
`architecture-decisions`' reason and not a new one: the filename is the slug
inbound `supersedes` fields name, and a body edited afterwards makes the record
agree with the present. A changed decision is a new record naming the old one.

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
