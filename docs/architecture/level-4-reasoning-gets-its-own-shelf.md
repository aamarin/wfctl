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
its own. It informs a choice, and routes to neither `architecture-decisions` nor
`software-design-decisions`."* That was the right call against
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

**The test against `design/` is whether the alternative was weighed, not what the
thing is.** Both shelves can claim the same artifact otherwise — a Repository
wrapper over an ORM session is a structural choice *and* a mechanism choice, and
naming the subject settles nothing:

```
a Repository wrapper went in
      │
      ├─ two approaches were compared, and one won on a stated criterion
      │     └─► design/, with software-design-decisions. The record carries
      │         the loser and why it lost.
      │
      └─ a constraint said the session transaction was the cheaper shape,
         and a pressure overrode it
            └─► implementation/. There is no loser to carry — the cheaper
                shape was the default, not a candidate someone argued for.
```

A weighed choice has a losing alternative to write down; a departure has a
default it walked away from. That is the discriminator, and it is what makes
`software-design-decisions`' *Not for* clause — "a choice with no credible
alternative" — the same line both records turn on.

**A note is indexed by naming the file and symbol it explains**, in its first
line. The shelf loses the baseline's one advantage otherwise: `git blame` reaches
a commit message in one hop from the code, and reaches `implementation/370-foo.md`
only for a reader who already knows the shelf exists. Naming the code in the note
makes `grep` the hop back, which is what the baseline has and a bare filename
does not.

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
targets of its own. It informs a choice, and routes to neither
`architecture-decisions` nor `software-design-decisions`."* — narrows. The skill
still mints no verdict and routes to neither of those two; what changes is that a
departure from a constraint now has a destination that is neither of them.

The narrowing is stated here and not there. An accepted record's body is never
edited, and a forward reference from an in-force record to this one would make
`wfctl arch context` carry a conclusion nobody has ruled on.

No reader of the arch root needs a code change, and that is worth stating because
`SCANS_DIR` exists for the opposite case. There are five readers, and the shelf
was checked against each:

- `load_records` globs one level, so a fourth subdirectory stays out of the
  `wfctl arch context` projection the way `design/`, `declarations/` and `views/`
  already do.
- `fact_architecture_accepted` intersects `records_on_this_branch` with
  `load_records`, and the one-level glob drops the shelf — so the fact answers
  `n/a  no level-2 record on this branch`, which is the right answer.
- `records_on_this_branch` asks git about the whole root recursively and lists an
  implementation note as `record: <stem>` in the auto-approve listing. The
  `<issue>-<slug>.md` convention is what keeps it clear of a stem collision with
  a top-level record, which carries no issue prefix by `architecture-decisions`'
  naming rule. That convention is load-bearing, and this is where it says so.
- `_observe` counts the shelf, so a note under it flips `boundary` to `answered`.
  That is not defended as correct. It is the same open question `cli._observe`'s
  own comment already names one directory over — whether a level-3 record under
  `design/` should count — extended one level further down, where the argument
  for excluding it is stronger rather than weaker: level 4 is further from a
  boundary than level 3. Left where it was found, deliberately, because moving it
  moves `design/` too and that is a separate decision.
- `design_block` excludes `design/` and nothing else, so an implementation note
  would satisfy the level-2 design gate. What makes this unreachable is the
  `spec.md` guard above it: a note under this shelf is written during `implement`,
  by which point `spec.md` has existed for four steps and the gate has already
  returned. The guard is the reason, not the exclusion list — stated here because
  a later change that moves the guard removes the protection with nothing to
  notice.

## Log

- 2026-09-13  proposed    — Andre's framing in the #370 working session:
  deliberate decisions belong at the level they were made at, because "the
  choices are tied to the level and the detail needed for its level", and mixing
  implementation reasoning with architectural reasoning costs both. The
  deciding evidence is that `design-levels`' own argument for the `design/`
  shelf — `specs/` is gitignored and resolves outside the tree — applies to
  level 4 unchanged and was never carried over.
