---
name: design-levels
description: 'Use before writing a spec or code for any feature, screen, or schema change. Runs design as four separate passes — behavior, architecture, design, implementation — each with its own gate, so the decisions that are expensive to reverse get made deliberately instead of being skipped on the way to code.'
deployment: skill
---

# Design levels

Design descends through four levels. Each is a separate pass with its own
approval. Don't skip, don't collapse.

| Level | Question | Form | Reversal cost |
|---|---|---|---|
| **1. Behavior** | What changes for the user? | Before/after wireframes, real output | Cheap |
| **2. Architecture** | What moves, and who owns truth? | Boundary sketch, data flow | Expensive after spec |
| **3. Design** | How is it structured? | Schemas, contracts, named alternatives + why | Moderate |
| **4. Implementation** | What's the code? | Real code to scan, not narrate | Cheap, mechanical |

Levels 2 and 3 are where the decisions with lasting consequence live, and they
are the ones most often skipped — level 1 feels like enough and level 4 feels
like progress.

A question asked at level 2 is answered at level 2, not with code.

## The gate at each level

An unnamed gate is an intention, and intentions are what momentum skips. Each
level has one question that has to be answered out loud before descending.

### 1. Behavior — the walkthrough

Enumerate the reachable states. Read each string **in that state**, and ask
whether it is true.

The question is not *does each state exist* but *does each state tell the
truth*. States that render fine and lie are the ones that get shipped:

- A failed first load that says it is showing cached results.
- Empty-state copy telling the user to relax a filter they never applied.

**Test for whether level 1 is finished:** if a level-1 decision has no level-3
consequence you can state, you probably haven't finished level 1. Level 1 is not
the easy pass on the way down — it is what generates the level-3 requirements.

Worked example: deciding that summary cards describe the *date window* rather
than the filtered rows sounds like pure behavior. It isn't — filtering to
`PENDING` means the completed rows never come back, so the client cannot compute
those cards, and the response has to carry a window aggregate computed before
the filters apply. That is a level-3 requirement generated at level 1.

### 2. Architecture — who owns this truth, and can they actually compute it?

The tell is usually a **state**, not a data flow. You find the ownership
question by walking an empty screen, not by staring at the data model.

Worked example: an empty *filter window* and an empty *workspace* render
identically and need opposite advice — one says relax a filter, the other says
there is nothing to filter yet. The client cannot tell them apart, because the
list opens on a 30-day default, so a brand-new workspace lands in the narrowed
branch and gets told to widen a range with nothing on either side of it. The fix
is an explicit `hasAny` flag on the response: authority for "is this workspace
empty?" moves to the server.

Answer for every piece of state or derived value the feature introduces: which
side computes it, and why the other side cannot. "The client can just work it
out" is the wrong answer roughly every time it is also the fast one.

### 3. Design — which of these claims did I verify, and which am I still betting on?

Split the design's factual claims into checked and assumed, then go check the
assumed ones against the code. This is where the gate pays most: claims that
read as settled fact are routinely wrong.

- "The index covers this query" — it did not.
- "Pagination already exists somewhere" — it did not.

Both would otherwise have surfaced during implementation, after the contracts
were written against them.

### 4. Implementation — covered by the existing verification skills

`verification-before-completion` and `code-review` own this level. Nothing new
here.

## The descent is not one-directional

A finding at a lower level can invalidate a boundary drawn higher up. When that
happens, go back up and revise — do not work around it in the spec.

Worked example: pagination was scoped **out** at level 1 as a separate
cross-cutting concern. At level 3 it turned out the window aggregate already
computes pagination's expensive half — the total count without fetching
everything — so pagination came back **in**, and search had to move server-side
with it or silently degrade to "find on this page."

## Where the levels land

Everything through level 3 lands in `specs/<branch>/design.md` before speckit
runs. The spec should be derivable from the recorded decisions, not re-invented.

- Level 1 → the behavior sections of `design.md`, gated by `speckit.clarify`.
- Level 2 → the **Boundaries and Ownership** section of `design.md`. It has no
  other home: `speckit.plan`'s Technical Context is a stack inventory and its
  Project Structure is directory layout — neither asks who owns truth.
- Level 3 → `design.md`, then expanded by `speckit.plan` Phase 1 into
  `data-model.md` and `contracts/`.
- Level 4 → belongs to the plan and to `speckit.tasks`, not to the design.

`plan-template.md`'s Constitution Check re-checks that ownership is stated. It
**verifies** the answer; it does not derive it. Arriving at `speckit.plan`
without one means going back to level 2, not filling the gate in from memory.

## Failure mode

Answering a level-1 or level-2 question with level-4 content. It buries the
decision under detail and makes editing feel expensive.

```
✗  Q: "Where should the manifest record which commit skills came from?"
   A: a _bundled_hash() implementation, with line numbers and test blast radius
      — the question was about where authority lives; the answer was code
```

The reader's signal that this happened: "I need just a high-level description of
this." By then the level-2 decision has already been made silently, inside the
code you showed.

This skill governs **which level you answer at**, not how the answer is worded.

## When not to use it

Bug fixes, trivial changes with no new state (button label, copy edit), and work
whose behavior and boundaries are both already settled in an existing spec.
