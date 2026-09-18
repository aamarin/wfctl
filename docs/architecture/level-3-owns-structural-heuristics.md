---
status: proposed
---

# Level 3 owns structural heuristics, and a skill that writes nothing is what may own them

## Context

`design-levels` routes level 2 to `architecture-design` → `architecture-decisions`
and level 3 to `software-design-decisions`. Level 3's own gate asks *"which of
these claims did I verify, and which am I still betting on?"* — a verification
question. Nothing in the tree helps an agent **make** the structural choice the
gate then checks: whether a module owns one coherent reason to change, whether a
decision sits with the knowledge it needs, whether failure is part of the API.

Level 4 has the same shape one level down and it was answered:
`level-4-owns-pattern-selection` put mechanism guidance in a new
implementation-facing skill rather than as a reference under an existing one.
Its route is conditional on purpose — `design-levels` §4 says *"There is no
equivalent skill for another language yet"* — so a Go or TypeScript implementer
reaching level 4 gets only the two verification skills, both of which fire after
the code exists.

#412 proposes a `clean-code` skill whose references load per the unit of code
under work, routed at levels 3 and 4 and into `code-review`. Two of its
references — `classes-and-modules.md` and `boundaries.md` — carry guidance about
module cohesion and vendor edges, which is close enough to `architecture-design`'s
subject that an agent loading both could run a design loop twice. Where that
guidance may live, and what bounds it, is an ownership question rather than a
packaging one.

## Direct baseline

Ship `clean-code` as a description-triggered skill and route nothing. The eleven
references exist, `design-levels` and `code-review` are untouched, and the skill
fires when an agent's own description match happens to pull it in.

The baseline is not empty: a description trigger does reach an attended session
where someone says "clean this up". What it does not reach is an unattended
pipeline run, which is where `design-levels` is walked step by step and no
description ever matches. That is the failure already on record for
`fanning-out-code-review` (#124) and the reason `_MIRRORED_SKILLS` exists.

## Decision

Structural-expression guidance lands at level 3, in the `clean-code` skill, and
the skill is bounded by producing no artifact. `design-levels` names it by path
at level 3 and again at level 4; `code-review` names its `review-catalog`
reference as a source for the readability lens.

A method that ends in a record is a design loop and belongs to
`architecture-design`. Heuristics that end in nothing are guidance and may sit
beside it at a lower level. That property — **does the skill write anything** —
is what separates the two, not the subject either one talks about.

## Owns truth

`clean-code` owns *"how should this unit of code be expressed, given its
boundary is already settled?"* — at level 3 for structure and at level 4 for
mechanism in any language.

`architecture-design` cannot own it. Its method ends in a proposed boundary
record or in `wfctl arch none`, and most expression choices draw no boundary at
all. Running the driver-ranking loop over "does this module have one reason to
change" either manufactures a boundary to complete the method — which the
skill's own text forbids — or spends an iteration to reach its no-record exit.

`software-design-decisions` cannot own it, for `level-4-owns-pattern-selection`'s
reason one level up: its **Not for** excludes "a choice with no credible
alternative", so guidance placed there is read only by an implementer who had
already stopped to weigh alternatives — the implementer who least needs it.

`code-review` cannot own it. It fires after the code exists, which converts a
choice into rework. It is a consumer of the catalog, not its owner.

```
design-levels                    │  the skill that answers
─────────────────────────────────┼──────────────────────────────────
level 2 — who owns this truth?   │
  boundary in play            ───┼─►  architecture-design
                                 │      └─► architecture-decisions
                                 │            writes a record
  no boundary                 ───┼─►  wfctl arch none
                                 │            writes a declaration
                                 │
level 3 — how is it structured?  │
  alternatives were weighed   ───┼─►  software-design-decisions
                                 │            writes a record
  expression of the structure ───┼─►  clean-code            ◄── new
                                 │      classes-and-modules, boundaries,
                                 │      errors, tests
                                 │            writes nothing
                                 │
level 4 — which mechanism?       │
  Python                      ───┼─►  python-pattern-selection
                                 │            writes nothing
  any language                ───┼─►  clean-code            ◄── new
                                 │      naming, functions,
                                 │      comments-and-formatting
                                 │            writes nothing
                                 │
review                           │
  readability lens            ───┼─►  code-review, sourced from
                                 │      clean-code/review-catalog  ◄── new
                                 │
  "clean-code says this fails" ──┼──✗  no verdict ever crosses
```

The bottom row is what the decision is for. Every arrow above it carries
guidance in one direction; nothing comes back the other way, because a skill
that writes nothing has nothing to send.

## Considered

- **The direct baseline, routing nothing** — correct about the risk and wrong
  about the cost. It cannot collide with `architecture-design` because it never
  fires beside it, and it never fires beside it in an unattended run either.
  It buys eleven files and no reach.
- **Route at level 4 only, moving the four design-half references there** —
  cheaper, one edit site, and no level-3 collision at all. It loses on timing
  rather than on correctness: level 4 is the mechanism *given the boundary is
  settled*, so cohesion and error-model guidance arriving there lands after the
  structure it was meant to shape. It would also leave a level-4 skill whose
  contents are level-3 material, which is the disagreement
  `level-4-owns-pattern-selection` avoided by asking where guidance is **read**
  rather than what it is **about**.
- **A `references/` directory under `software-design-decisions`** — adds no new
  description-triggered skill, and sound for the subset of guidance that does
  weigh alternatives. Rejected for the reason in *Owns truth*: that skill's
  trigger is a choice already weighed.
- **A second design loop inside `clean-code`, ranking drivers at level 3** —
  rejected before it was drafted. `architecture-design` already owns that
  method, and two of them means an agent loading both does the work twice or
  picks one arbitrarily. This is #370's finding, restated one level down.
- **A seventh `code-review` lens** — symmetrical with the six and wrong for the
  panel: `fanning-out-code-review` states that *"every reviewer runs the whole
  `code-review` rubric"* and rejects a panel split by axis. A seventh lens either
  joins that rubric, in which case it is not a lens but a source, or it splits
  the panel, which contradicts a skill this project ships.

Asked once, as step 3 requires: **a known solution already fits.**
`python-pattern-selection` is a level-N skill that informs a choice, produces no
artifact, and is bounded by an explicit *Authority* section. It was accepted for
this class of gap one level down. Reusing its shape is the cheaper answer, and a
structure invented beside it would be the more expensive kind of wrong.

The published-interface claim was examined rather than inherited. It does not
hold here: `install-skills` mirrors the skills tree into projects wfctl cannot
reach, so a skill's `name` and `description` **are** a published interface —
renaming one is not a mechanical refactor. The conservative reading wins on the
record: get the description right on the first publish, and carry the exclusion
in it rather than relying on a later edit.

## Consequences

Four constraints follow, and none is optional.

- **`clean-code` mints no verdict vocabulary and grants no waiver.** No pass, no
  fail, no outcome class. `design-levels` owns every gate. This is
  `python-pattern-selection`'s first inherited constraint, and it binds harder
  here: level 3's gate is itself a judgment, so a skill that produced one would
  be taking the gate rather than informing it.
- **It runs no design loop and routes to neither record skill.** A choice that
  draws a boundary is `architecture-decisions`; one that weighed credible
  alternatives and drew none is `software-design-decisions`. Neither routing is
  `clean-code`'s to make.
- **Its `description` must sit inside `architecture-design`'s pre-drawn
  exclusion** — *"Not for diff review, implementation verification, local pattern
  selection, or work whose boundaries are already settled"* — by scoping itself
  to a settled boundary, exactly as `python-pattern-selection`'s does. The draft
  description this skill is built from names "module design" and "dependency
  boundaries" with no such scope, and would sit beside the exclusion rather than
  inside it.
- **It joins `_MIRRORED_SKILLS`.** `design-levels` names it by path at two
  levels, and an agent that read the pointer and reached for `Skill(clean-code)`
  is refused without membership. That is `architecture-design`'s own entry
  rationale, and `python-pattern-selection`'s: the mirror does not make a refused
  route work, it removes the fork so the outcome stops depending on which way the
  agent reached. `speckit.implement`'s ceiling already grants `Read`, `Glob` and
  `Bash(wfctl arch context*)`, which is everything the *Authority* section needs,
  so no grant widens.

Two costs are accepted rather than avoided.

`design-levels` gains two routing paragraphs in a skill whose density is already
a filed problem (#290). That is a reason to keep the additions to a sentence
each, not a reason to restructure the skill in this change.

Two skills are reachable at level 3 from here on, and an agent tells them apart
by their descriptions alone. The exclusion clause above is the whole of what
makes that work, which is why it is a constraint and not a style note.

No attribution is owed, and that is a positive claim rather than an omission.
The draft `clean-code` was generated by an agent: no upstream project, no
repository, no licence, no copyright holder, so there is nothing to name on a
last line and no entry owed in `NOTICES.md`. It synthesizes public, unowned
engineering guidance and reproduces no sample program. This is
`python-pattern-selection`'s case exactly, and `vendor-upstream-skills` says so
positively there because a reader who saw "generated from a third-party draft"
in a commit message went looking for a row owed to nobody (#370). That record is
amended in the same change, not after it.

## Log

- 2026-09-17  proposed    — #412's placement question, answered by one
  `architecture-design` iteration. The deciding evidence is that
  `architecture-design`'s method ends in a record and `clean-code`'s references
  end in nothing, not the level-3 framing the issue opened with.
