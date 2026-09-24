# After implementation, before review

Use this reference for one bounded pass over the code a finished implementation
just wrote, while its structure is still cheap to change. Before review, a
structural move is part of the change. After review, it is rework on a
reviewed diff. A name or signature that this branch introduced usually has no
caller outside the branch yet, so this is usually the one point where renaming
it needs no compatibility shim. "Usually" is doing work there. A preview
deploy, a published contract or a client generated from the branch reaches
callers that git cannot see, so check for those before renaming without a
shim.

The pass decides which moves are worth making. How to make each one safely is
[refactoring-workflow.md](refactoring-workflow.md), and this file does not
repeat it.

## What the pass is not

It is not a second implementation. The spec, the task list and the accepted
records still decide what the code does. A defect or a missing requirement
found here is a behaviour change: fix it as one, with its own proof, and keep
it distinguishable from the structural moves in the same patch. Don't absorb it
into a refactor where a reviewer cannot tell which line changed behaviour.

It does not declare the work complete. Completion is read from the
verification a repository declares, run after this pass so that its verdict
describes the tree the pass left behind.

A pass may select no moves at all. Code that a fresh implementation left in
good shape is the common case, and the inspection record below is what tells
that result apart from a pass that never looked.

## Find the diff

Compare against the base the branch was cut from, and include staged,
unstaged and untracked files. A summary of what was implemented is a pointer,
not the scope: read the files the diff actually names.

Sort what changed into production code, tests, generated output,
configuration or schema, documentation and migrations. Every changed
production file is in scope. Generated output is not edited directly: change
its source or leave it alone.

Code the diff only reads is context, not a candidate. An awkward caller that
this branch left as it found it can stay awkward. The pass is paid for by the
next change to *this* code, and a move made somewhere else pays nobody.

Where more than one base is plausible, name the ambiguity rather than picking
one silently. A pass over the wrong base inspects someone else's code.

Before the first edit, record the baseline: the checks the repository runs and
what they report now, known failures and flakes included. A move that seems to
break a test which was already failing is noise, and only the baseline tells
the two apart.

## Triage each candidate

Look at the changed code and only as much context as it takes to understand
it. A candidate is worth recording only where all five of these have an
answer:

1. **Evidence:** a concrete branch, call path, duplicated rule, name, state
   transition or dependency you can point at.
2. **Change pressure:** the plausible next change that this structure makes
   harder. A future feature invented to justify an abstraction does not count.
3. **Scope:** a local move inside the boundaries already accepted. Two pieces
   of similar syntax can express different concepts, and merging them couples
   what should vary independently.
4. **Proof:** a check that would tell the moved code apart from the original
   if the move changed behaviour. Where coverage is too weak to do that, the
   first step is characterisation, not the move.
5. **Net gain:** what the move adds in indirection, API churn and diff noise,
   weighed against what it removes.

Duplicated policy and misplaced ownership outrank line counts. Formatter
output and taste are not candidates.

[review-catalog.md](review-catalog.md) is where to look for a candidate. The
questions below decide whether a candidate is worth a move before review:

| Observation | Ask |
| --- | --- |
| Repeated logic | Is it the same rule, changing for the same reason? |
| A long routine | Does it have coherent phases whose names would help a reader? |
| A complex conditional | Does it carry a meaning worth naming, or only syntax? |
| Flags or switches | Distinct responsibilities, or one clear branch? |
| Scattered mutation | Does a shared invariant have one owner? |
| A wrapper layer | Is it protecting a boundary, or only forwarding calls? |
| Parallel fields | Do they form a stable concept with shared invariants? |
| A parameter, option, hook or interface with one implementation | Does anything vary through it today, other than a test? |
| One concept edited in many files by this diff | Is its knowledge scattered, so the next change will scatter too? |
| A routine that reads another module's data more than its own | Does it belong beside that data? |
| A domain value carried as a bare string or number | Does it have rules that a type would hold in one place? |

The row about one implementation deserves a second look in a fresh
implementation. Structure added for a change nobody has asked for is one of
the most common things a first pass leaves behind. Removing it is a move too,
and usually the cheapest one on the list.

The row about many files is the one only this pass can see. The diff itself is
the evidence: it shows how far one change had to travel.

## Record the decision

Give each candidate one line and one decision:

```text
location | evidence | next change made harder | proposed move | behaviour protected | proof | do / defer / skip
```

- **do:** selected for this pass.
- **defer:** worth doing, but out of this pass's scope. Name where it goes.
- **skip:** examined, and not worth doing. Say why in a clause.

Select a small set. The pass ends when the selected moves are made, not when
the code is as clean as it could be, so a short list is the design and not a
compromise.

Keep this record in the report you give at the end. Don't write it to a file.
This skill writes nothing, and a file whose presence meant the pass ran would
be evidence for a pipeline step that nobody declared.

## Make the moves

Take each `do` in turn through [refactoring-workflow.md](refactoring-workflow.md):
one transformation, the narrowest verification that could tell it apart from
the original, a re-read of the call sites, then the next move. Some moves carry
a risk that the generic checks miss. Probe for it before the move is kept:

| Move | Probe |
| --- | --- |
| Rename or move | Indirect callers: strings, configuration, generated consumers, documentation. A name that already existed on the base branch may have callers this repository cannot see |
| A shared helper | The variations the originals had, how many times each input is evaluated, side effects |
| State or ownership | Mutability, aliasing, serialisation, transaction and lifecycle |
| Control flow | When errors are raised, early exits, fallback order, short-circuiting |
| Async or concurrent code | Scheduling, cancellation, retries, locks, idempotency |
| A public or stored shape this branch introduced | Whether a preview deploy, a published contract or stored data has already exposed it; a shape that already existed is a stop, below |
| A hot path | The performance budget, or a representative measurement |

Compilation and lint passing do not show two versions are equivalent. Never
change an expected output to make a test pass. That is a behaviour change, and
it goes back to the paragraph on defects above.

## Stop

Stop on any of the stop conditions in `refactoring-workflow.md`, and on one
more that only this pass meets: **the next move would draw or move a
boundary**, whether that is a public contract, the owner of persisted data or
the direction of a dependency. That question is not this skill's to answer.
Name it as a `defer`, point at `design-levels` for where it belongs, and leave
the code as it is.

## Report

End with a report the reviewer can read without re-running the pass:

```text
scope:        <base, changed paths, callers read>
baseline:     <checks and their results before the first move>
candidates:   <the record above, one line each>
moves:        <each move made, why, and the contract it protected>
verification: <commands or observations, and their results>
unverified:   <the specific risk that remains, or none>
deferred:     <each defer and where it belongs, or none>
```

For a pass that changed nothing, `scope` and `candidates` are the report: what
was read, and why nothing in it earned a move. Leaving them out makes the
report look the same as one from a pass that never ran.
