---
name: architecture-decisions
description: 'Write an architecture decision as a durable record — one file per decision, naming which side owns a piece of truth and why the other side cannot compute it. Use when a design answers who owns a value, who computes it, or where authority for a question lives. Use when a boundary between two components is being drawn or moved. Use when a decision that is expensive to reverse has just been made in conversation and nothing has written it down.'
---

# Architecture decisions

## Overview

A record is one file holding one decision. It is not documentation of the code;
the code documents itself. It holds what the code cannot answer: what else was
considered, and which side owns the truth.

## When to Use

Write a record when a decision draws or moves a boundary:

- A piece of state or a derived value gets an owner — one side computes it, the
  other asks.
- Authority for a question moves from one component to another.
- A format, protocol or contract between two sides is fixed.
- An alternative was seriously considered and rejected for a reason that is not
  visible in the resulting code.

This is the `.agents/skills/design-levels` level-2 gate's answer in durable
form. That skill decides *which level you answer at*; this one is where a
level-2 answer lands.

**Not for**: bug fixes, refactors that move no boundary, naming, style, library
version bumps, or anything a code comment already carries. A record per change
is a changelog, and nobody reads a changelog to find a constraint.

## Where records live

```bash
wfctl arch-root     # prints the directory; defaults to <repo>/docs/architecture
```

Ask rather than assuming: a repo can declare `arch_root` in its manifest, and
the default is not the truth. The command neither creates the directory nor
requires it to exist — a repo has no records until it writes its first one.

## Identity is the slug, and the slug is the filename

`wfctl-runs-the-check.md` is the record `wfctl-runs-the-check`. There is no
sequence number, for two reasons that both bite in this repo's workflow:

- Monotonic numbering collides. Two worktrees writing `0007-…` on the same
  afternoon both believe they took the number.
- Renumbering breaks every inbound `supersedes`, which names a slug.

For the same reason, **a record is never renamed.** A slug that turned out to be
wrong is cheaper to live with than a link that silently resolves to nothing.

Name it for the decision, not the feature or the issue: `wfctl-runs-the-check`,
not `verification-work` or `issue-69`.

## Writing one

Copy `record-template.md` from this skill's directory and fill it in. The
sections are fixed — `Context`, `Direct baseline`, `Decision`, `Owns truth`,
`Considered` and `Log` are required, `Consequences` is optional. Add
`supersedes` to the frontmatter only when this record replaces one.

## The field that is not in MADR

`Owns truth` is the reason this format exists. Every other section appears in
MADR and in every ADR template on the market; this one does not, and it is the
single thing a level-2 design pass is run to extract.

**Both halves are required:**

```
which side owns the question   →  wfctl owns "did the check pass?"
why the other cannot compute it →  the agent cannot: a self-report is
                                   unfalsifiable
```

The second half is the one that gets dropped, and it is the one that carries the
argument. Without it the section is a role assignment, which the code already
shows, rather than a constraint, which the code cannot.

Phrase the owned thing **as the question it answers**, in quotes. "wfctl owns
verification" names a component. `wfctl owns "did the check pass, and against
which tree?"` names a question, and a question is what a later reader checks a
proposed change against.

A record reaching `accepted` without a non-empty `Owns truth` is not a lighter
record. It is the failure this feature exists to correct, wearing a new
filename.

## Status

| Value | Meaning | In force |
|---|---|---|
| `proposed` | Written, not yet agreed | no |
| `accepted` | Currently binding | **yes** |
| `superseded` | Replaced by a named successor | no |
| `rejected` | Considered and not adopted | no |
| `retired` | Governed the work, then ended with no successor | no |

Absent, empty or unrecognised reads as **not in force**, never as the common
case: presenting an unreviewed decision as binding is what the field prevents.
Write `proposed` while a human still has to agree.

## An accepted record is immutable

Once a record is `accepted`, exactly two things ever change:

```
status:  accepted → superseded | retired
Log:     one line appended
```

The body is never edited. Not to fix the reasoning, not to add a consideration
that came up later, not to soften a claim. **A changed decision is a new
record**, and the old one becomes `superseded` with the new one naming it:

```
old record:  status: superseded
             Log: - 2026-08-11  superseded  — unfalsifiable; moves to wfctl

new record:  supersedes: agent-runs-the-check
```

Git holds the edit history. The file holds only what git cannot answer — and a
body edited after the fact makes the record agree with the present, which is
exactly the thing it was written to prevent.

That rule outranks the section list, so **an accepted record written before a
section existed does not carry it, and is not backfilled.** Retrofitting a
heading across every accepted record is the "agree with the present" failure at
the only scale where it looks like tidying. A missing section in an accepted
record is a date, not a defect.

The exemption stops there. A `proposed` body is not frozen, so a proposed record
gains a section the format has since added like any other edit — and it has to
before it can be accepted. Nothing in the list below is waived by a record
having been written first; the exemption is for records already past the point
where anything can be added.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll write the record once it's implemented." | The record is what the implementation is written against. Afterwards it is a description, and it will describe whatever got built. |
| "This decision is too small for a record." | Size is not the test. Did it draw a boundary? Then it is expensive to reverse, whatever its size. |

## Verification

- [ ] The filename is a slug naming the decision, with no sequence number.
- [ ] `Owns truth` names the owning side **and** why the other side cannot
      compute it — both halves, the second one in full.
- [ ] The owned thing is written as a question in quotes, not as a component name.
- [ ] `Direct baseline` describes the no-new-structure option concretely enough
      to compare the decision against.
- [ ] `Considered` carries at least one real alternative with the true reason it
      was not chosen. Losing on fit is a reason; a weakness the alternative does
      not have is never one.
- [ ] `Log` has a dated line for the status the record currently carries.
- [ ] If this supersedes a record, that record's `status` was changed to
      `superseded` and got its own `Log` line — and nothing else in it was edited.
