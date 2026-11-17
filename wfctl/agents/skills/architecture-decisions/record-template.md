---
status: proposed
diagram: <data-flow | component | state | sequence>
governs: <names from the domain page's Contexts or Outside parties line, comma-separated>
---

# <the decision, as a statement — "wfctl runs the verification, not the agent">

## Decision

<What was decided, in the present tense. One or two sentences. When the baseline
won, say so here — that is a decision, not an absence of one.>

## Boundary

<Required to accept — `wfctl arch accept` refuses a record with nothing drawn
here. Declare which kind above in `diagram:` and draw that kind: `data-flow`
for a value moving between two sides, `component` for a line between them,
`state` for the states one thing passes through, `sequence` for a request
crossing several actors past a wait.

Draw it as an SVG, saved under the arch root as `drawings/<slug>-<kind>.svg`,
and link it here with an inline markdown image whose alt text is the drawing's
caption:

    ![the decision in one plain sentence](drawings/<slug>-<kind>.svg)

Follow `references/drawing-style.md` in the `design-levels` skill for the grid,
the colors, the classes, and rendering the file to look at it before
committing. A mermaid or ASCII fence here still passes every check.

For `data-flow` or `component`, draw one column of boxes per side, phases down
the page, an arrow only where something actually crosses, and the refusals
too: a red edge (`class="refused-edge"`) for what the owning side never accepts
from the other, because that edge is the decision. Put the refused claim on
that edge as its label, running from one side to the other, and never as a box
inside the side that would make it, since a box for a claim reads as one more
step that side takes. Use a solid arrow for a call the sender waits on and a
dotted arrow for anything read later, such as a file on disk or a payload a
renderer polls. A drawing that reads a file draws the branch where the file is
missing, or holds no part the decision reads, whenever that branch ends
somewhere different. A `sequence` drawing has a row for the step that fails,
and that arrow carries `class="failing-step"`.

When the drawing uses an edge style or a shape the record does not explain in
prose, add a one-line key below the image. Label with the words this record
already uses in prose — a label introducing a concept found nowhere else in the
record is what `wfctl doctor` surfaces as drift. An edge label says what the
edge means to the reader in plain words, such as "import allowed", and the
prose below the image says why it holds. A label written in another drawing's
notation, such as `map draws EV --> WG`, reads as a claim about the boxes it
connects rather than about the edge. The same goes for a box named by a term
the reader may not know, such as "wiring": the prose below the image says what
it is, per `design-levels`' rule that a glyph a reader could doubt gets a key
(Richards and Ford, *Fundamentals of Software Architecture*, p. 321).

In mermaid, the same rules apply: a flowchart with one subgraph per side and
the refused claim on an `--x` edge, a `stateDiagram-v2` for `state`, and a
`sequenceDiagram` for `sequence`, whose failing step is an `alt`, `opt`,
`break` or `critical` block, or a lost message `-x`.>

<If the decision needs more than one kind, declare them as a list, such as
`diagram: [data-flow, sequence]`, and give each kind its own heading here with
its drawing under it:

    ### data-flow

    ![what the value's path shows](drawings/<slug>-data-flow.svg)

    ### sequence

    ![what the order of steps shows](drawings/<slug>-sequence.svg)

`wfctl arch accept` refuses a declared kind with no drawing under its heading,
a kind listed twice, and a heading for a kind the list doesn't declare. A
drawing above the first heading counts for no kind. Other headings, such as
`### Key`, are fine. If the record declares one kind, the drawing can sit
directly under `## Boundary` with no heading.>

## Context

<What made this decision necessary. The situation, not the answer.>

## Direct baseline

<The smallest change that draws no new structure — the boundary left where it
is — described concretely enough to compare the decision against.
`.agents/skills/architecture-design` step 3 produces one in every iteration;
this is where it lands. A baseline that is a sentence of hand-waving justifies a decision rather
than making one.>

## Owns truth

<Which side owns the question, phrased as the question itself:
"wfctl owns 'did the check pass, and against which tree?'.">
<Why the other side cannot compute it: "The agent cannot: a self-report is
unfalsifiable.">

## Considered

- <alternative> — <the reason it was not chosen>
- <alternative> — <the reason it was not chosen>

<Fit and fault are both reasons. An alternative can be sound and lose anyway:
"equally sound — this one puts the answer where the reader already looks" is
truer than a weakness it does not have, and a manufactured criticism reads as
diligence while sending the next reader to reject a sound option twice.>

## Consequences

<Optional. What follows from this — requirements it generates, work it forces.
Delete the section if there is nothing to say.>

## Log

- <YYYY-MM-DD>  proposed    — <why this was written>
