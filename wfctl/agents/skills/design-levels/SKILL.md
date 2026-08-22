---
name: design-levels
description: 'Runs design as four separate passes — behavior, architecture, design, implementation — each with its own gate, so decisions that are expensive to reverse get made deliberately rather than buried in code. Use when designing a feature, screen, or schema change, before writing a spec or any code. Use when a question asks what changes for the user, what moves, or who owns a piece of truth. Use when a design conversation has jumped from a wireframe straight to an implementation.'
deployment: skill
---

# Design levels

## Overview

Design conversations collapse four levels into two: a wireframe, then code. The
two skipped in between are where the expensive-to-reverse decisions live. This
skill runs each level as its own pass with its own gate.

## When to Use

- Designing a feature, screen, schema change, or CLI surface — anything that
  introduces new state or new user-visible behavior.
- A question was asked about behavior or ownership and the answer forming in
  your head is code.
- The reader says "I need just a high-level description of this."

Not for: bug fixes, copy edits and other trivial changes that introduce no new
state, or work whose behavior and boundaries are already settled in an existing
spec.

## The four levels

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

Use the `verification-before-completion` skill and the `code-review` skill.
Nothing new here.

## Rendering the gate's answer

The *Form* column above names an artifact per level. That is what the gate's
answer is written as — not a paragraph, and not a table by default. A table is
one form among several, and reaching for it first is the most common way a
rendered answer still arrives unreadable.

Pick by the shape of the thing:

```
what shape is the thing?
 ├ two versions of one output ───► side-by-side code block
 ├ one input, several outcomes ──► ASCII fan-out
 ├ a line with sides ────────────► boundary sketch
 ├ N conditions × M outcomes ────► table
 └ one thing ────────────────────► render the string
```

ASCII, not mermaid: a skill is read in a terminal, where mermaid renders as its
own source.

**Level 1 — the literal string each state renders**, stacked one per state, each
judged true or false in that state. A table only when the states are a real
cross product of independent conditions.

```
implement    ▶  12/12 done  ← current
                unverified — run `wfctl verify`

implement    ▶  12/12 done  ← current
                stale — verified at a1b2c3d, tree dirty
```

**Level 2 — a boundary sketch**: one column per side, phases down the page,
arrows only where something actually crosses. Read a phase label, read left,
follow the arrow, drop down.

```
agent                          │  wfctl
───────────────────────────────┼──────────────────────────
config time                    │
  writes .agents/verify.json ──┼─►  reads argv
                               │
implement                      │
  edits code, ticks boxes      │
  runs `wfctl verify`       ───┼─►  runs argv
                               │    records exit + sha + dirty
                               │
status                         │
  (nothing)                    │    reads record + live git
                               │    decides ● or ▶
                               │
  "it passed"  ────────────────┼──✗ never accepted from the left
```

The line down the middle is the decision, and the bottom row is the one the
feature exists for. A table would file both under a column header.

Two parallel lists sharing vertical space is not a sketch. Rows that read as
pairs but are not aligned on purpose are worse than prose, because the reader
infers a relationship the diagram never claimed.

**Level 3 — two columns, `checked` and `assumed`.** The asymmetry is the
finding; a reader sees it before reading a word.

## The decisions ledger

Design spans turns and the reader loses what is already settled. Carry a ledger
and restate it when it changes — number, level, decision, one line each.

| # | Level | Decision |
|---|---|---|
| 1 | behavior | not run green → implement ▶, gated |
| 2 | behavior | record binds sha + dirty; any drift → stale |
| 3 | architecture | wfctl runs the check — tamper-evident, not unforgeable |

Three columns of short values is what a table is for.

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

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Showing the code *is* the answer — it's concrete." | It buries the decision under detail and makes editing feel expensive. A level-2 question answered in code has its decision made silently, inside the code. |
| "Level 1 is obvious, we already know what the user sees." | Then state its level-3 consequence. If you can't, level 1 isn't finished — that's the test. |
| "Ownership will be clear once I see the schema." | Backwards. The schema encodes the ownership decision; writing it first makes the decision by accident. |
| "The client can just compute that." | The answer that is fast is the wrong one roughly every time here. Name what the client would need and check it actually has it. |
| "That's an edge case, not a state." | Empty, first-load, and permission-denied are reachable states. Every one of them renders a string that is either true or a lie. |
| "Going back up now would waste the design we already have." | Revising a boundary costs a paragraph. Working around it costs a contract, and it is permanent. |
| "The user is in a hurry." | Urgency is a reason to not build the wrong thing twice. |

## Red Flags

Each of these means a level got collapsed. Stop and go back to the level the
question was asked at.

- A file path, line number, or function name appears before the decision it
  implements has been stated.
- The reader asks "what does that look like?" or "I need just a high level
  description" — the level they wanted led, and it didn't.
- A design section describes *how* something is stored before saying *who*
  computes it.
- A claim about existing code ("the index covers this", "pagination is already
  there") appears in the design and was never opened and checked.
- `design.md` reaches `speckit.specify` with no Boundaries and Ownership
  content, or with schemas sitting in that section.
- A gate's answer is a paragraph, or a table whose rows are not a cross product
  — the decision is in there somewhere, and the reader has to extract it.

```
✗  Q: "Where should the manifest record which commit skills came from?"
   A: a _bundled_hash() implementation, with line numbers and test blast radius
      — the question was about where authority lives; the answer was code
```

This skill governs **which level you answer at**, not how the answer is worded.

## Verification

Before `design.md` is written:

- [ ] Every reachable state was named, and its copy read *in that state* and
      judged true or false.
- [ ] Each level-1 decision has a stated level-3 consequence.
- [ ] Every piece of state or derived value the feature introduces names the
      side that computes it **and** why the other side cannot.
- [ ] Every claim about existing code is marked verified or assumed, and the
      verified ones were checked against the code, not from memory.
- [ ] Any boundary a lower level invalidated was revised upward, not worked
      around.
- [ ] `design.md` has a Boundaries and Ownership section holding ownership
      decisions, not schemas — and no level-4 code.
- [ ] Each gate's answer was rendered in its form — literal strings for level 1,
      a boundary sketch for level 2, a two-column split for level 3 — not a
      paragraph, and not a table chosen by default.
