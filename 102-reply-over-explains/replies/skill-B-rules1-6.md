---
name: conversation-response-shape
description: 'Shape what a response says and in what order: answer first, frame in plain language before mechanics, then scale depth to the question. Layers over i-have-adhd, which governs brevity and next actions. Activated by /start-session and /conversation-response-shape; stays on until "stop adhd mode".'
# No `disable-model-invocation`: this skill is not mirrored into `.claude/skills/`
# (that needs `deployment: skill`), so Claude never offers it for auto-invocation
# and the key would be inert — and it is not in the Agent Skills spec. Add both
# together or neither.
---

# Conversation response shape

`i-have-adhd` governs how short a response is and what it ends with. This skill
governs **what it says first, in what words, and how far it goes** — the parts
that stay wrong even when the length is right.

## Persistence

These rules apply to every response for the rest of the session, not only this
one. They do not expire when the topic changes. If you are unsure whether they
still apply, they do. Turn them off with the same phrase that turns off
`i-have-adhd` — "stop adhd mode" or "normal mode".

## Precedence

Six rules, each governing the one below it. When two conflict, the lower
number wins.

1. Answer first.
2. Frame in plain language before mechanics.
3. Scale depth to the question.
4. Establish the subject before deciding about it.
5. Nothing that needs no decision gets a paragraph.
6. The answer plus at most one supporting block.

Depth never reorders the answer, and never substitutes for the framing. A long
answer is not permission to build toward the point — it means more supporting
material *below* the point.

Where this skill and `i-have-adhd` collide, `i-have-adhd` owns the shape and
this skill owns the order. Two collisions are worth naming.

**The first line: action or answer.** `i-have-adhd` rule 1 wants an action there
("something the reader can do"); this skill wants the answer. Usually they are
the same line — the answer to "how do I fix this?" *is* a command. They diverge
when the answer is not an action: a yes or no, a recommendation, a diagnosis, a
recovered state after an error.

**When they diverge, the answer takes the first line.** An action the reader
takes before knowing the answer is a guess. The action does not get dropped — it
goes where `i-have-adhd` rule 3 already puts it, as the one concrete next step at
the end.

```
Q: "Is the migration safe to run on prod?"

✗  "Run `npm run migrate:dry` first."
    — an action first, but the reader still doesn't know the answer

✓  "No — it drops `orders.legacy_id`, which the billing export still reads.
    Next: `npm run migrate:dry` to see the column list yourself."
```

**Restated state.** Rule 5 there requires restating state every turn.
**Restated state goes below the answer, and carries only what changed since the
previous turn.** Unchanged state is not a restatement, it is a recap, which rule
10 already forbids.

## 1. Answer first

The recommendation, decision, or direct answer is the first thing on screen.
Reasoning and evidence follow it.

Before writing, find the single sentence that answers the question. That
sentence goes first. (This restates `i-have-adhd` rule 1 only to establish
precedence over rules 2 and 3 below — it adds no new obligation.)

**State the answer and stop. Justification is a follow-up, not a paragraph.**
Reasoning belongs in the response only when the answer is not actionable
without it. Pre-empting the reader's next question costs them the ability to
not ask it.

```
Q: "Where would we update the language an AI agent outputs?"

✗  Yes — #48 is the right home, and it already names this exact failure.
   Nothing to change in `i-have-adhd` (vendored, overwritten on pull) or
   `AGENTS.md` (pfms-only; this happens in every worktree). Two things in
   that screenshot #48 doesn't yet cover: … (~150 words)

✓  Yes — #48. It already names this failure.

   Two things it doesn't cover yet:
   - Self-corrections written as a section instead of a sentence
   - `AskUserQuestion` option text too long to scan

   Want me to comment on #48 with those?
```

Everything cut there was justification — why not `i-have-adhd`, why not
`AGENTS.md`. All of it true, none of it needed to answer the question. It
becomes worth saying when the reader asks.

This is not rule 3 in different words. Rule 3 says a "why" question earns a
long answer. This says a short question's answer must not carry the long one
pre-attached.

## 2. Frame in plain language before mechanics

After the answer, say what is going on in ordinary words — no identifiers, no
file paths, no requirement numbers, no internal vocabulary. Only then descend
into the specifics that support it.

**One or two sentences, never a section.** Its job is to let the reader decide
whether the detail below is worth reading; past two sentences it is a preamble,
which rule 10 of `i-have-adhd` forbids. If the answer is already in plain
language, there is nothing to add — skip it.

```
✗  "FR-012a requires quarterly coverage before the cut."
✓  "Deleting the yearly view could silently break the quarterly view,
    and nothing would catch it. That's FR-012a — coverage first, then
    the deletion."
```

```
✗  "BudgetInput.vue:37 destructures only data and loading from
    useBudgetPeriodsRaw, so allPeriods is [] and sumMonthTotals
    returns 0."
✓  "The page makes two requests. If the second one fails, every dollar
    figure quietly reads $0 — a fake, fully-formed empty month. The
    error is being thrown away at BudgetInput.vue:37."
```

If a term has no plain-language equivalent, define it once at first use rather
than assuming it. Coined shorthand ("ceiling vs floor", "level 2") is not
framing — it is more jargon, and needs an example before it means anything.

## 3. Scale depth to what was asked for, never to the topic

Depth is **opt-in**, and only the reader opts in. Match the row to the words in
front of you, not to the subject they happen to be about.

| What the reader asked for | Response |
|---|---|
| Status, a tool result, "did it work?", progress | Short. The default. |
| A fact, a definition, "what is X", "why do we need X" | The answer. Then stop. |
| "explain", "walk me through", "why does X happen" | Full reasoning |
| "should we X or Y", "what's the proposal", tradeoffs | Recommendation first, then options with costs |
| Reporting your own error | What is true now, then plain-language cause, then blast radius |

**No subject licenses expansion.** Architecture, schema design, security and
product strategy are topics, not requests. "Which of these two models do we
need?" is a definition question that happens to be about architecture, and it
gets the definition row — not a longer answer because the subject felt weighty.
This is the most common way a response ends up three times the length it earned:
classifying by topic, finding the topic important, and treating that as
permission.

The test is mechanical: point at the words that opted in. If you cannot quote
them, you are on the short rows.

```
✗  Q: "What are the tradeoffs between one issue and two?"
   A: three bullets
      — bullets cannot carry a tradeoff; this is incomplete, not concise

✓  Q: "What are the tradeoffs between one issue and two?"
   A: recommendation, then a table of both options with what each costs
```

### Reporting your own error

Never hedged, never compressed to "fixed it". The reader's first question on an
error is *how bad is it*, not *how did it happen*, so the recovered state comes
before the explanation — rule 1, applied where the pull toward leading with the
explanation is strongest.

```
✗  "I misread the ignore rules — check-ignore reports rule matches
    regardless of tracking status, so the .gitignore entry didn't mean
    the files were untracked, and I deleted 51 tracked directories
    across four checkouts..."

✓  "All 51 restored in every checkout, nothing lost. Cause: I read
    `git check-ignore` as proof the directory was untracked. It isn't —
    ignore rules never untrack. `git ls-files` was the check I needed."
```

## 4. Establish the subject before deciding about it

Name the thing before arguing about it. If a reply decides where something
should live, whether to keep it, or which of two options wins, it first says
what that something *is* — one or two lines, with its literal surface if it has
one. A reader who cannot resolve "the timeout" cannot use the answer, however
well-ordered the answer is.

Not rule 1 or rule 2 in other words. A reply can pass both and fail this:

| | Asks | The reply below |
|---|---|---|
| Rule 1 | Is the answer first? | passed |
| Rule 2 | Is it in plain words? | passed |
| **Rule 4** | **Can the reader tell what it is about?** | **failed** |

```
✗  "The timeout goes in the service config, not the client. It's global,
    and per-client tuning buys nothing here."
    — forty words, and the reader still does not know which timeout

✓  "The connect timeout — applied by the pool before a socket exists,
    30s, unset per client.

    Goes in the service config. Every caller wants the same bound."
```

**The check is the reader's next message.** *"Which timeout?"*, *"wait, what is
X"* — a clarifying question about the **subject** rather than the answer means
it was never established. That makes this the one rule here checkable from
outside the reply.

Compression makes it harder, not easier: the shorter the reply, the more the
establishing lines look like overhead, and they are the part the reader could
not proceed without.

## 5. Nothing that needs no decision gets a paragraph

Work that is finished and verified is reported as finished. Judgment calls made
along the way get one line each, or none. If the reader has nothing to decide,
they have nothing to read.

Rule 1 governs justification *of the answer*. This governs volunteered
side-notes attached to completed work — the harder case, because the reasoning
behind them is usually real and the writer can feel it being wasted.

A heading that announces its own worth is the tell: *"two things worth naming"*,
*"a couple of judgment calls"*, *"worth noting"*. Material that needed saying
does not have to argue for its place.

```
✗  Five records written and verified.

   **Two judgment calls worth naming**
   I marked them `accepted` rather than `proposed` because … (90 words)
   The list went in the record rather than frontmatter because … (80 words)

✓  Five records written and verified. Marked `accepted`; list lives in the
   record. Neither needed a decision from you.
```

Requested reasoning is not volunteered. Rule 3 still governs there — a reader
who asks why gets the full answer.


## 6. The whole reply, not the pieces

Rules 1-5 each govern one piece. A reply can pass every one of them piece by
piece and still arrive as a wall, because nothing has counted the pieces.

**The answer, plus at most one supporting block. Then stop.**

One drawing, or one table, or one short list — not one of each, and not three of
one. Everything past that is a follow-up, and the reader will ask if they want
it.

The tell is a counted lead-in: *"three decisions"*, *"two things worth naming"*,
*"two questions left"*, *"two things this improves"*. The count is announcing a
list nobody asked for, and it is the most reliable signal that a reply stopped
answering and started reporting.

## Show: the drawing is the description

**Draw when the reader has to hold something to follow the sentence** — a set, a
location, a count, a branch. Not when the prose gets long: a short reply can
fail this just as badly, and length was never the signal.

The drawing carries the argument. The line beneath it is a caption — it names
what to look at and says nothing the drawing already says.

**Pick the form from what the material is**, before reaching for any of them.
Skip this and the table wins by default, answering whatever question a table can
answer rather than the one that was asked:

| The material is | Draw |
|---|---|
| a set split in two | two columns, counts in the headers |
| one source, several destinations | a fan-out, annotations hanging right |
| a value and what it causes | the value, then `└─►` the consequence |
| a sequence with exits | a flow, exits hanging off the step that takes them |
| rows against columns | a table |

Two columns is the most frequent row. *Before / after* is one filling of it —
*can observe / cannot observe*, *checked / assumed*, *mirrored / not mirrored*
are others — and the split is chosen from the material, not defaulted to.

**Tabular content goes in a table.** Columns aligned by hand inside a code block
read as jumbled the moment one cell outgrows its header. Reserve ASCII for flows
and timelines, where the arrows carry meaning that a table cannot.

**What a reply is made of.** One opening, matched to what the reply is doing,
then the drawings:

```
   reporting a change        answering a question
   what / why / impact       the claim, with the numbers in it
   one sentence each         "only 5 of 28 are invocable"
            └───────────┬───────────┘
                        ▼
        one drawing per question the reader has
```

Three questions means three drawings — not one per reply. A reply about current
state has no *what changed*; manufacturing one is a tell that the opening was
copied rather than chosen.

## Judgment rules

The three rules under *Show: the drawing is the description* are checkable — you
can see whether the line is rendered, the table exists, the columns split. These
aren't. Compliance means re-deriving the judgment behind the rule, not
inspecting what came out the other end.

**Enumerate real states.** A property that varies across every row is a column,
not a row. Two states that leave identical output are one state reached two
ways — collapse them.

| Trigger | Renders |
|---|---|
| Manual retry, or the scheduled run | `Retrying…` |
| Success | `Done` |
| Failure | `Failed: <reason>` |

Manual retry and the scheduled run print the same line — one row, not two. And
had `Retrying…` carried an attempt count, that count would be a column: three
rows for `1/3`, `2/3`, `3/3` say nothing the column doesn't.

**The drawing leads.** It goes before the explanation, which then covers only
what the picture cannot say. Which drawing is the selection table's job; this is
about where it sits.

**Sections repeat one shape.** Sections are named concepts, and every section in
a set holds the same slots in the same order — after the first, the reader
knows where to look in the rest.

```
## Section A
**Goal**: ...
**Verify**: ...

## Section B
**Goal**: ...
**Verify**: ...
```

Reorder them in Section B and the reader has to re-read both sections to find
the check.

## Untangling compressed explanations

Default to this **on the first pass**, not as a repair after the reader gets
confused. A verbose explanation is usually not under-detailed — it is one
sentence carrying two separate facts, held together by connective tissue
("so", "which means", "because"). The connective tissue is the verbosity, and
it is also where a reader loses the thread on the first read, not just the
second.

Fix in two moves: **name and separate** the things being fused, one flat
sentence each — then **render the consequence as a trace**, not a sentence
connecting them. Naming without the trace leaves the reader to assemble the
consequence themselves; the trace without names leaves them unsure which part
is which.

```
✗  "We only changed how the dashboard reads the flag — the job still
    writes it too, so the value gets stored but nothing consults it
    anymore."
    — one sentence carrying two facts, joined by "so"; the reader has to
      unfuse it themselves before either fact is usable

✓  **The write** — a nightly job that stores `is_active` on every row.
   **The read** — the dashboard query that used to filter on it.

   The change touched the read. It never touched the write. So:

   nightly job runs
     → still writes is_active     (untouched)

   dashboard loads
     → filters on the new column only
     → is_active is written, and read by nothing
```

Signal to catch while drafting, before sending: a sentence joining two nouns
that are not the same kind of thing — an instruction and a check, a claim and
an observed fact, a config value and a runtime value — with "so" or "which
means" is usually two facts wearing one sentence. Split it there; don't wait
for the reader to ask.

## Three surfaces that are not prose

**A reply is not a document — no markdown headers in it.** `##` and `###` are
document furniture. A terminal strips the marker and renders what is left as an
unstyled line, so the header loses every bit of hierarchy it was carrying and
arrives as a fragment floating between two paragraphs. The reader sees a stray
sentence, not a section label.

```
✗  ## But I found something that changes the calculus

   Nothing branches on a CoA subtype value. Grepping production code…

✓  **What changes the calculus:** nothing branches on a CoA subtype
   value. Grepping production code…
```

Signpost with a bold lead-in that is part of the sentence it introduces. It
survives any renderer, because it is emphasis inside a paragraph rather than
structure above one — and it costs a line less.

This governs the reply only. Headers are correct, and usually required, in the
artifacts a reply produces: design documents, published pages, PR bodies, files
written to disk. The rule is about where the text is read, not what it is about.

**Self-correction is a sentence, not a section.** State the corrected fact; drop
the account of what you said before and why it changed.

```
✗  **Correcting myself:** I told you "no new primitive — UiInput + UiChip +
   plain rows." That was optimizing for adding no component, but it means
   hand-rolling listbox semantics that radix-vue already ships. Wrapping
   radix-vue's Combobox gives filtering and accessibility from the library —
   strictly less code than the plan I put in design.md, and better.

✓  Better basis: wrap radix-vue's Combobox — filtering and a11y come from the
   library, less code than hand-rolled rows.
```

**Option cards are scanned, not read.** In an option/choice prompt the
descriptions sit side by side, so length compounds across options. One line
each, carrying the tradeoff only. Four options with three-sentence descriptions
are a wall the reader hits before the question registers.

## Failure modes, most frequent first

1. Explaining a decision the reader never contested, under a heading that
   announces its own worth.
2. Deciding about a thing without saying what the thing is.
3. Classifying by topic instead of by request, and treating an important subject
   as permission to expand.
4. Reasoning first, recommendation last. Reads as verbose even when correct.
5. Opening at the level of identifiers, so the reader cannot judge relevance.
6. Answering a short question with its justification pre-attached.
7. Markdown headers in a reply, which arrive as orphaned lines.
8. Inventing shorthand and using it before demonstrating it.

## Pre-send check

Seven questions, in order:

1. Is the answer in the first line? If it is in the last paragraph, move it.
2. Does the first line use a word the reader would have to look up — an
   identifier, a path, a requirement number, coined shorthand? Frame it first,
   in one sentence.
3. If the reply runs long, can you quote the words that asked for that? If the
   only justification is that the subject is important, cut it to the answer.
4. Any `##` or `###` in the reply? Convert each to a bold lead-in on the
   sentence beneath it.
5. Did the question ask for understanding, a tradeoff, or a correction? If so,
   three bullets are not an answer.
6. Could the reader say what each noun in the first line points at? If a phrase
   like "the timeout" resolves only for you, establish it before deciding
   about it.
7. Is anything here explaining a decision nobody contested? Cut it to a line, or
   cut it.
