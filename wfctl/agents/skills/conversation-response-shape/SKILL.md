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

Three rules, each governing the one below it. When two conflict, the lower
number wins.

1. Answer first.
2. Frame in plain language before mechanics.
3. Scale depth to the question.

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

## 3. Scale depth to the question

| Question shape | Response |
|---|---|
| Status, tool result, "did it work?", progress | Short. The default. |
| "explain", "walk me through", "why" | Full reasoning, headers to skim back |
| "should we X or Y", "what's the proposal", tradeoffs | Recommendation first, then options with costs |
| Architecture, design, product strategy | Structured and complete; tables over prose |
| Reporting your own error | What is true now, then plain-language cause, then blast radius |

Terseness is the default, not a ceiling. Compressing a question that asks for
understanding deletes the answer being asked for.

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

## Show, to simplify the description

When the subject has a shape — a layout, a structure, a before/after, a flow —
render it: wireframe, diagram, prototype, worked example. The artifact does not
replace the explanation; it *carries the structure so the words don't have to*.
Prose describing a layout in sentences is long, imprecise, and hard to hold.
The same layout drawn takes ten lines and needs one sentence beside it.

Reach for it when the description is getting long because it is doing spatial
or structural work. If the reader asks "what does that look like?", the artifact
should have led and the prose should have been shorter.

**Render the literal output, not a description of it.** Anything with a surface
— a CLI line, an error, a field in a file — is written as the exact string the
reader would see. A sentence describing the string is longer than the string and
less certain.

```
✗  "the command should report where the pipeline actually is instead of
    claiming the session ended"

✓  $ wfctl end
   ✓ Session closed — implement 3/8.  Summary: <path>
```

**Tabular content goes in a table.** Columns aligned by hand inside a code block
read as jumbled the moment one cell outgrows its header. Reserve ASCII for flows
and timelines, where the arrows carry meaning that a table cannot.

**A two-column split is often the whole answer.** *Can observe / cannot
observe*, *checked / assumed*, *before / after* — the shape does the arguing, and
the reader sees the asymmetry before reading a word.

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
✗  "The design only changed how wfctl reads completion — the agent still
    runs the old write instruction too, so the file gets written but
    nothing consults it anymore."
    — one sentence carrying two facts, joined by "so"; the reader has to
      unfuse it themselves before either fact is usable

✓  **The write** — an instruction telling the agent: "when you finish,
   create this file."
   **The read** — code that checks: "does that file exist?"

   The design changed the read. It never touched the write. So:

   agent finishes implement
     → still writes implement-complete.md   (untouched instruction)
     → also runs wfctl verify                (the new step)

   wfctl status
     → reads the verify record only
     → the file exists, ignored completely
```

Signal to catch while drafting, before sending: a sentence joining two nouns
that are not the same kind of thing — an instruction and a check, a claim and
an observed fact, a config value and a runtime value — with "so" or "which
means" is usually two facts wearing one sentence. Split it there; don't wait
for the reader to ask.

## Two surfaces that are not prose

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

1. Reasoning first, recommendation last. Reads as verbose even when correct.
2. Opening at the level of identifiers, so the reader cannot judge relevance.
3. Answering a short question with its justification pre-attached.
4. Treating terseness as a ceiling rather than a default.
5. Inventing shorthand and using it before demonstrating it.

## Pre-send check

Three questions, in order:

1. Is the answer in the first line? If it is in the last paragraph, move it.
2. Does the first line use a word the reader would have to look up — an
   identifier, a path, a requirement number, coined shorthand? Frame it first,
   in one sentence.
3. Did the question ask for understanding, a tradeoff, or a correction? If so,
   three bullets are not an answer.
