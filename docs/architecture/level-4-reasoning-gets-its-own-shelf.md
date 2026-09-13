---
status: proposed
---

# Level-4 reasoning lands on its own shelf under the arch root, not in the level-3 one and not only in a commit message

## Context

`design-levels` says where each level's answer lands. Level 2 goes to one record
per ownership decision directly under `wfctl arch-root`. Level 3 goes to
`design.md` and, when it weighed credible alternatives, to one record under
`<arch-root>/design/`. Level 4 *"belongs to the plan and to `speckit.tasks`, not
to the design."*

That last routing is the gap. `tasks.md` lives in `specs/`, which is gitignored
and whose `spec_root` resolves outside the working tree — the exact condition
that gave level 3 a shelf of its own, stated in `design-levels` as *"a reviewer
reading the PR never sees `design.md`."* The same sentence is true of `tasks.md`
and nothing was done about it.

`level-4-owns-pattern-selection` then added a skill that fires at the moment an
implementer picks a mechanism, and closed with *"It gets no hand-off targets of
its own. It informs a choice; it records none."* That was the right call against
the destinations that existed — routing mechanism reasoning to
`architecture-decisions` or `software-design-decisions` would file it where
`wfctl arch context` treats it as binding, or where a reader looking for a
structural decision finds an implementation note. It leaves the reasoning behind
a deliberate mechanism choice with nowhere to go.

## Direct baseline

Add no directory. A departure from a pattern-selection constraint is written in
the commit message, which is where the draft skill already sends it: *"the
departure is what gets written down — in a commit message, or in a level-3 record
if an alternative was really weighed."*

The baseline is not nothing: a commit message is durable, in-tree, and reaches
the PR reader. It loses on retrieval rather than on durability. A constraint is
consulted by someone standing in front of the code months later asking *why is
this wrapper here*, and `git log -S` over a file's history is a search, not a
shelf. The level-2 and level-3 records exist for the same reason and neither was
satisfied by a commit message either.

## Decision

Implementation-level reasoning gets one shelf under the arch root —
`<arch-root>/implementation/`, a sibling of `design/` — holding one file per
deliberate mechanism choice, named `<issue>-<slug>.md` as `design/` and
`declarations/` already are. The shelf is chosen by the level the reasoning was
produced at, not by the change that produced it.

`implementation` rather than a word about patterns, because the shelf is the
level's and not one skill's: `design-levels` calls level 4 implementation, and a
second level-4 skill added later files here without the directory reading as a
misnomer.

## Owns truth

The shelf a piece of reasoning lands on owns *"at what level of detail is this
argument pitched, and therefore who is its reader?"*

The change cannot own it. A single change routinely produces reasoning at three
levels — who owns a value, how it is structured, which mechanism expresses it —
and filing all three together forces every later reader to re-sort them. The
level is a property of the argument and is known at the moment it is written;
the change is a property of the delivery and says nothing about who needs the
argument later.

## Considered

- **The commit message alone** — the direct baseline. Durable and in-tree, and
  it loses only on retrieval. Kept as the right home for a mechanism choice
  nobody would look up: the shelf is for the deliberate one, not for every
  application of a default.
- **A reference under `software-design-decisions`** — its own *Not for* excludes
  "a choice with no credible alternative", which is most mechanism choices. A
  level-4 argument filed there is also read as a structural decision by anyone
  scanning that directory, which is the mixing this record exists to prevent.
- **A new `wfctl` verb, on the `arch none` model** — sound, and premature.
  `wfctl arch none` exists because a *declaration of absence* is easy to skip and
  needs a prompt; an engineer who decided something against a stated default is
  already motivated to write it. The convention earns the verb by being used, not
  before.
- **Reusing `declarations/`** — that subtree holds the claim that a change needed
  no decision at a level. A decision someone did make is its inverse, and filing
  both under one name costs the reader the distinction the directory was created
  to draw.

## Consequences

`level-4-owns-pattern-selection`'s third consequence — *"It gets no hand-off
targets of its own. It informs a choice; it records none."* — narrows. The skill
still mints no verdict and routes to neither `architecture-decisions` nor
`software-design-decisions`; what changes is that a departure from a constraint
now has a destination that is neither of those.

No reader of the arch root needs a code change, and that is worth stating because
`SCANS_DIR` exists for the opposite case. `load_records` globs one level, so a
fourth subdirectory stays out of the `wfctl arch context` projection the way
`design/`, `declarations/` and `views/` already do. `records_on_this_branch` and
`_observe` ask git about the whole root recursively and will count the new shelf
as decided work on the branch — which is correct here and is why it takes no
`:(exclude)`, unlike `scans/`, whose contents decided nothing.

## Log

- 2026-09-13  proposed    — Andre's framing in the #370 working session:
  deliberate decisions belong at the level they were made at, because "the
  choices are tied to the level and the detail needed for its level", and mixing
  implementation reasoning with architectural reasoning costs both. The
  deciding evidence is that `design-levels`' own argument for the `design/`
  shelf — `specs/` is gitignored and resolves outside the tree — applies to
  level 4 unchanged and was never carried over.
