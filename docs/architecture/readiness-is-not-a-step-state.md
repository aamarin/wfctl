---
status: proposed
---

# A step state says whether the pipeline may advance; readiness is four facts, each read from its own owner

## Context

`pipeline-state-is-one-payload` (accepted) fixes what inference produces: a
step's name, its state as one of `done`, `in_progress`, `pending`, `skipped`, an
annotation, and which step is current. Every view renders that and computes
nothing of its own.

Four separate questions are being answered through that one value, and they have
four different owners:

| The question | Owned by |
|---|---|
| were this step's artifacts written? | the spec dir |
| did the definition of done pass on this tree? | `wfctl.json` + the verify record |
| is the architecture binding, or still proposed? | the record's `status` field |
| may this branch be integrated? | a human's grant |

Only the first two reach the payload, and the second reaches it folded into the
first: `implement` is `in_progress` both when tasks are open and when
`verification_block` names a failure. The third is read nowhere — `design_block`
counts a record under the arch root *whatever its status*, and says so in its own
docstring, so a branch whose record is `proposed` and one whose record is
`accepted` produce byte-identical payloads. The fourth is present as `notify` and
`notify_source` but says whether this run may tell people something, not whether
anyone agreed the branch may land.

The rung comment in `_predicates.py` already names the missing two — "6 a
decision has authority; 7 integration was approved" — and its own per-predicate
list shows no step reaching either.

So a branch that is blocked cannot say which question is unanswered, and the
reader supplies the answer from context. That is the state #100 scope item 4 was
filed against.

## Direct baseline

Widen `implement`'s reason string. It is the one step whose annotation already
names why it is held, so appending the record status and the notify grant to it
costs one predicate and no new shape:

```
implement    ▶  12/12 done  architecture proposed; integration not authorized
```

It fixes the reported symptom for the reader looking at that row, and it is
genuinely smaller than what is decided below.

What it does not produce is four facts. It produces a longer sentence about one
step, and the sentence is composed from three sources by a predicate that owns
none of them — so `implement` would report on a record it does not read and a
grant resolved before the pipeline started. The next reader adding a fifth
condition appends to the same string, because that is where the last four went.
It also answers only for branches that reach `implement`: a branch held at
`specify` has the same unanswered architecture question and no row to carry it.

## Decision

The payload carries the four facts alongside the steps, never inside them. Each
is derived from its own owner, and none is derived from another or from any step
state. A step state goes on answering exactly one question — may the pipeline
advance past this step — and gains nothing.

Each fact is scoped to *this branch*, not to the repository. A fact whose
question does not arise on this branch says so, and is not reported as unmet.

## Owns truth

Four owners, one question each, and the payload reads all four rather than
computing any:

- The spec dir owns "were this step's artifacts written?". Nothing else can:
  the artifact on disk is the only evidence that a step ran.
- `wfctl.json` and the verify record own "did the definition of done pass, and
  against which tree?". `wfctl-runs-the-verification` already settled this and
  the reason stands unchanged — an agent's self-report is unfalsifiable.
- A record's `status` field owns "is this decision binding?". The pipeline
  cannot compute it: a record's existence is a fact about the filesystem, and
  its bindingness is a fact about whether a human agreed. `a-human-accepts-a-decision`
  makes that transition a person's, so the only honest read is the field they set.
- A human's grant owns "may this branch be integrated?". The pipeline cannot
  compute it for the reason #280 gives for the grant existing at all: the
  consequences reach people outside the repository, and no artifact in the repo
  can stand in for someone agreeing to that.

**What the payload owns is that these are four answers and not one.** A view may
render them in any arrangement; it may not fold two of them into a single value,
because the value it would produce has no owner to be wrong about.

## Considered

- Widen `implement`'s reason string, per **Direct baseline** — smaller, and it
  answers on one row for branches that reach it. The four facts stay collapsed,
  one step ends up reporting on three sources it does not read, and a branch held
  before `implement` gets no answer at all.
- A fifth step state — `blocked`, or `ready` — rejected by #299 scope item 3, and
  the reason is not arbitrary. The four facts are independently true or false, so
  a single value covering them is 16 states wearing one name; the collapse this
  record undoes would return under a new spelling.
- Four columns across the eight step rows — puts every fact on every row, and
  three of the four are facts about the branch rather than about a step, so
  seven rows would carry a repeated value and the eighth would carry it too.
  Where the facts *render* is level 3 and is settled in
  `design/299-facts-render-as-a-block.md`; what is rejected here is the shape
  that would make three branch facts into step facts.
- Read "architecture accepted" from the whole projection rather than from this
  branch's records — the reading is cheaper and needs no git. It answers a
  different question: this repository currently holds 15 proposed records, so
  every branch would report `no` forever, including branches that touched no
  architecture and have nothing to accept. A permanently false value is not a
  fact about the branch.
- Derive "integration authorized" from the other three — that is the collapse,
  arriving as a convenience. Whether the work is finished and whether anyone
  agreed it may land are different questions with different owners, and #280
  exists because the second one had none.

## Consequences

The three branch-scoped facts are answerable with no spec dir. That is new: a
branch whose feature directory has not been created still has a definition of
done, a record set and a grant, and today's payload can say nothing about any of
them.

"Architecture accepted" needs the branch's own record set, which means resolving
the arch root and asking git what this branch changed under it during inference.
`records_on_this_branch` already does exactly that, for `status`'s auto-approve
listing, so the read exists and is not new work.

Three values per fact, not two: met, unmet, and *does not arise here*. A repo
that declares no definition of done, a branch that wrote no record, and the trunk
itself each have a question that was never asked, and reporting those as unmet
would send a reader to satisfy something that does not exist. This is not the
fifth status this record rejects — it is one fact's own value, and it never
crosses back into the step table.

`blocks(verdict, source)` is untouched. That rule answers what it means for
evidence to be *unavailable*, and it goes on answering it inside the gates that
call it; these facts answer which *question* the evidence was about. A fact whose
evidence cannot be read reports unmet with the reason naming why, which is what
the rule already says for a promised source.

## Log

- 2026-09-10  proposed    — #299, #100 scope item 4. Four questions, four owners,
  one value carrying all of them.
