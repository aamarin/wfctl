# Phase 1: Rule Inventory

There is no data layer. The "entities" this feature manipulates are rules in a
shipped skill file, and the thing that matters about each is **who owns it** and
**what it governs** — because `knowledge-placement` makes a rule with two homes a
rule with no owner.

## The rule set after this change

| # | Rule | Governs | Status |
| --- | --- | --- | --- |
| 1 | Answer first | where the answer sits in the reply | unchanged |
| 2 | Frame in plain language | what vocabulary the answer uses | unchanged |
| 3 | Scale depth to what was asked | how far the reply goes | one line deleted |
| 4 | Establish the subject | whether the reader can tell what the reply is about | **new** |
| 5 | Nothing that needs no decision gets a paragraph | whether material is said at all | **new** |

Rules 4 and 5 are appended, not inserted — see `research.md` §2 for the
cross-reference count that forces this.

**Why 4 precedes 5.** Establishing the subject is a precondition for judging
whether material needs a decision: you cannot tell that a side-note is
volunteered until you know what it is about.

**Why 4 is not a special case of 1 or 2.** This is the distinction the whole
#556 evidence exists to hold open:

| | Rule 1 | Rule 2 | Rule 4 |
| --- | --- | --- | --- |
| Asks | is the answer first? | is it in plain words? | can the reader tell what it is about? |
| #556 reply 2 | passed | passed | **failed** |

## Form instructions

Not rules in the precedence list — they live in the drawing section and govern
the shape of what gets rendered.

| Instruction | Governs | Status |
| --- | --- | --- |
| The draw test — hold a set, a location, a count, a branch | *whether* to draw | replaces the deleted length test |
| Form selection | *which* drawing the material calls for | **new** |
| Reply composition, two genres | what a whole reply is made of | **new** |
| Tabular content goes in a table | one form's placement | unchanged |
| Render the literal output | one form's fidelity | unchanged — **budget lever**, see `plan.md` |

### Form selection

The mapping the skill has never had. Its absence is what lets the table
instruction fire by default.

| The material is | Draw |
| --- | --- |
| a set split in two | two columns, counts in the headers |
| one source, several destinations | a fan-out, annotations hanging right |
| a value and what it causes | the value, then the consequence on a branch |
| a sequence with exits | a flow, exits hanging off the step that takes them |
| rows against columns | a table |

*Before / after* is one filling of the first row, not a privileged default.

### Reply composition

```
   reporting a change            answering a question
   ──────────────────            ────────────────────
   What / Why / Impact           the claim, with the numbers in it
           │                              │
           └──────────────┬───────────────┘
                          ▼
           one drawing per question the reader has
                    (not one per reply)
                          │
                          ▼
           one line under each, naming what to look at
```

## Ownership

The constraint that makes this a design artifact rather than a list.

```
i-have-adhd                    conversation-response-shape
  brevity, next action           rules 1-5, the draw test,
  VENDORED — never edited        form selection, composition
        ▲                                  │
        │ layered over, nothing copied     │  single owner
        └──────────────────────────────────┤
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                      ▼                      ▼
    .github/pull_request_    speckit-delivery-plan   finishing-a-development-
    template.md              (#556, not here)        branch (#556, not here)
         │                        │                        │
         └────────────────────────┴────────────────────────┘
              each states the obligation only:
              "a body leads with a figure"
              — and defers which figure to the owner
```

**The form-selection table is the thing that must never be copied.** It is the
part most likely to change, so any restatement is a stale copy the moment it
does.

## State transitions

One, and it is the observable check for rule 4:

```
reply sent
    │
    ├─► reader's next message is about the ANSWER      → rule 4 held
    │
    └─► reader's next message asks what the reply is   → rule 4 failed
        about ("what hook", "which file", "wait, what     (SC-011)
        is X")
```

This is the only rule in the skill checkable from outside the reply itself.
