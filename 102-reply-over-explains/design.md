# conversation-response-shape: register, and the shape of a reply

## Problem Statement

A reply can satisfy every rule in `conversation-response-shape` and still be
unreadable.

The skill governs **order** (answer first) and **depth** (scale to the question).
It says nothing about **register** — how much a piece of material is worth
saying at all. So a reply reports five finished records, then spends two hundred
words under a heading of "two judgment calls worth naming" explaining decisions
that were already made, already verified, and required nothing from the reader.
The reader's response was *"I don't get what you are getting at."*

A second failure sits beside it. The skill says to render a shape rather than
describe it, but never says what a reply is *made of*. So the drawing, when it
appears at all, appears as a table — and the same content that reads well in a
pull request arrives in conversation as prose.

A third sits under both. Neither rule set requires the reply to establish
*what it is talking about* before it argues about it. So a reply can be
answer-first, plain-language and forty words long, and still leave the reader
asking "what are we talking about again" — because the subject was assumed, not
named.

The three share a cause: the skill describes properties a reply should have, and
never a shape a reply should take.

## Evidence

Fourteen agent runs, six variants of the skill, five real issues as fixed tasks.
Agents received the variant by path and were told not to read the installed
skill, so rule text was the only variable.

### The register failure reproduces

Variant A — the current skill, verbatim — volunteered a bolded *"Why a marker
and not a smarter detector"* paragraph justifying a decision nobody had
contested. Prose words per reply on the same task, code and tables excluded:

```
A  current skill            203   ← reproduced the failure
B  + new rules, conflicts left  103
C  + new rules, conflicts cut   120
D  + new rules, carve-outs       91
E  hybrid                       152
```

Every variant carrying a register rule killed it. The rule works in any of the
forms tested.

**The metric is narrower than it looks.** Prose word count measures compression,
not whether the reply answered. A later exchange (below) produced a forty-word,
answer-first, recommendation-led reply that scores as a win on this table and
still failed the reader. Word count stays as *a* measure here; it is not the
measure.

### The drawing rules produce tables, and only tables

Variant F is C with every form instruction removed — the control for *did the
rules cause this*:

| | C (rules present) | F (rules stripped) |
|---|---|---|
| #88 | config + warning + **state table** | prose only |
| #90 | branching as prose in a bullet | branching **drawn as a trace** |
| #76 | two literal `✓` lines | two literal `✓` lines |
| #85 | **two tables** | bullets + a CLI session block |
| #61 | **2-cell table** (unwarranted) | no table |
| | tables **3/5** · literal output 4/5 | tables **0/5** · literal output 4/5 |

Three findings follow:

1. **"Render the literal output" earns nothing.** It fires at the same rate with
   the rule absent. When the subject *is* a CLI line, it gets rendered anyway.
2. **The table habit is entirely rule-caused, including where it is wrong.** #61
   had no shape worth drawing. C drew a two-cell table around twenty words; F
   did not. The rules do not distinguish a warranted table from an unwarranted
   one.
3. **Zero boundary sketches in fourteen runs.** The form is not in this skill —
   only in `design-levels`. Verified against the file, not assumed.

### Stating a rule does not make it fire

The fan-out form is already a rule in this skill *and* carries a worked example.
On #90 the material was a three-branch path resolution. C, with that rule
present, wrote it as one sentence joined by "so". F, without it, drew it.

An earlier draft read this as *stated rules do not fire*, and concluded that
adding checkable triggers for the decision tree and the boundary sketch would
change nothing. That reading does not survive the control. F is C with **every**
form instruction removed — not only the fan-out rule but the table rule with it.
So #90 shows two rules changing together, and cannot separate *the fan-out rule
failed to fire* from *the table rule fired instead*.

Finding 2 above already says the table habit is entirely rule-caused. The
simpler reading of #90 is that it is rule-caused here too: C had a form to reach
for, reached for the wrong one, and F — with nothing to reach for — was left
drawing what the material actually was.

### A live session reproduces the preemption

Not an experiment run. A real exchange in this project, on #99.

The question was which frontmatter key controls skill invocation. The material
is a fan-out — one installer, two destinations — over a partition, 5 of 28
skills mirrored. The first reply rendered a 2x2 table of key against behaviour,
then carried the fan-out and the partition entirely in prose. The reader's
response was *"i need a diagram here of what's mirror and what's not, too much
context for my brain to parse text wise."*

The second reply, written to that instruction, used three drawings — a fan-out
for where files land, a two-column partition for set membership, a per-item
trace for what the state means — and was readable at a glance.

Three things follow.

**The table fired where a table was wrong, and the fan-out did not fire at all.**
The same pattern as #90, in a fresh case, with a human confirming the failure.
The 2x2 was not a bad table. It was a correct table answering a smaller question
than the one that was asked.

**The forms are available without a trigger.** The second reply needed no new
rule; it needed the reader to say *draw this*. A fan-out, a partition and a
consequence trace appeared on demand, and none of the three has a stated trigger
in the skill. What is missing is not the form. It is the step that picks between
forms before any of them fires.

**The register tell reproduced verbatim.** The first reply carried a bolded
*"Two smaller things, not questions — just flagging:"* — the same shape this
design names as the tell, written before this exchange happened.

### Compressing a reply does not make it answer

A second live exchange, on #556, and the one that limits what this design can
claim.

The question was whether a set of pieces belonged in `wfctl` or in the consumer
repo. The first reply gave a placement table, a shell command counting
committers, three placement options with costs as prose bullets, a recommendation
in the second-to-last paragraph, and a closing *"Worth noting…"* — the register
tell, third instance.

The reader said: *"too much verbosity, get to the point with recommendations."*

The second reply was two numbered recommendations and a closing question. Forty
words. Answer first, recommendation led, no volunteered justification — every
property this design asks for.

The reader's next message was ***"what hook are we talking about again"***.

```
what the reader needed          what the reply argued about
──────────────────────          ───────────────────────────
what IS this hook          →    where it should live
                                three placement options
                                how many people commit to the repo
                                which issue owns which piece
```

**Compression was not the fix, because verbosity was not the defect.** The reply
was one level past where the reader was standing. Everything in it was true and
none of it was reachable without knowing what the hook was. Shortening it removed the
symptom and preserved the cause — which is why the "what are we talking about"
question arrived *after* the compression, not before it.

The third reply is the shape the first one needed: what the hook is, when it
fires, the literal `matcher`/`inject` block, one line on why it exists at all.
Four lines to establish the thing. Only then is placement a question with an
answer.

This is not rule 1 restated. The second reply led with its answer. It is not
rule 2 restated either — the second reply used no jargon. It is a third
obligation: a reply must establish its subject before it argues about its
subject.

### The rules decay within a session

The clearest instance is this session. *"Tabular content goes in a table.
Columns aligned by hand inside a code block read as jumbled the moment one cell
outgrows its header"* is in the file, correctly worded. Around forty turns in,
the assistant hand-aligned a five-row comparison inside a code block; the
columns collapsed exactly as the rule predicts, and the user had to paste a
screenshot back.

The rule was not missing, not ambiguous, and not disagreed with. It was gone.

## Recommended Direction

Four changes, one commit. Three are additions; the fourth is a decision to add
nothing, recorded so it is not re-proposed.

### 1. Add the register rule, and resolve what it contradicts

> **Nothing that needs no decision gets a paragraph.** Work that is finished and
> verified is reported as finished. Judgment calls made along the way get one
> line each, or none. If the reader has nothing to decide, they have nothing to
> read.

A heading like "two things worth naming" is the tell — material inflated to
justify its own presence. Rule 1 governs justification *of the answer*; this
governs volunteered side-notes attached to completed work, which is the harder
case because the reasoning behind them is usually real.

Four contradictions resolve, per variant C — two by deletion, two by
replacement:

| # | Contradicted text | Resolution |
|---|---|---|
| 1 | *"Reach for it when the description is getting long"* | replace — draw when the reader has to hold a set, a location, a count or a branch to follow the sentence |
| 2 | *"the artifact does not replace the explanation"* | replace — the drawing carries the argument, the line under it is a caption |
| 3 | *"Terseness is the default, not a ceiling"* | delete |
| 4 | `.github/pull_request_template.md`: *"if a diagram takes longer to read than the prose it replaced, delete it"* | replace with the same test as #1 |

Conflict 3 was contested and settled by experiment. C deleted the ceiling
sentence and E restored it; the files are otherwise byte-identical. C produced a
four-row state table enumerating every reachable case. E did not. The sentence
was originally kept as a guard against over-compression — but D, which also kept
it, produced the shortest and least informative reply in the set. It does not do
the job it was kept for.

### 2. Give the reply a shape, and a rule for picking the form

The skill lists forms without saying what a reply is composed of, and without
saying which form the material calls for. Both halves are needed. The first is a
template; the second is what the #99 exchange shows is actually missing.

**The composition depends on what the reply is doing.** The template below came
from five merged pull requests, and a pull request reports a change. A reply
answering a question about current state is a different genre and does not fit
it — the #99 reply has no *what changed*, because nothing changed. One opening
per genre, then a shared body:

```
   reporting a change            answering a question
   ──────────────────            ────────────────────
   What / Why / Impact           the claim, with the numbers in it
   one sentence each             "only 5 of 28 are invocable"
   no hedging
           │                              │
           └──────────────┬───────────────┘
                          ▼
        ┌─────────────────────────────────────────┐
        │  one drawing per question the reader    │
        │  has — not one drawing per reply        │
        └─────────────────────────────────────────┘
                          │
                          ▼
        the line under each drawing names what to
        look at in it, and says nothing the drawing
        already says
```

**One drawing per question, not one per reply.** The #99 reply carried three,
because the reader had three questions — where the files land, who is in each
set, what the state means — and each has a different shape. A single drawing
would have had to answer all three or drop two. An earlier draft of this design
said *one visual*; that is a floor being mistaken for a ceiling.

**Draw when the reader has to hold something to follow the sentence** — a set, a
location, a count, a branch. This is the replacement for conflict 1's *"reach for
it when the description is getting long"*, and it is checkable against the
material rather than against the prose. Length was never the signal: the first
#99 reply was not long, and it failed anyway.

**Pick the form from what the material is.** This step does not exist in the
skill today, and its absence is what lets the table rule win uncontested:

| The material is | Draw |
|---|---|
| a set split in two | two columns, counts in the headers |
| one source, several destinations | a fan-out, annotations hanging right |
| a value and what it causes | the value, then `└─►` the consequence |
| a sequence with exits | a flow, exits hanging off the step that takes them |
| rows against columns | a table |

Two-column is the most frequent row, but *before / after* is one filling of it
and not the privileged one. #99's was a membership partition, and the counts in
the headers did most of the work. An earlier draft of this design named
BEFORE / AFTER as *the* default form; on this evidence the default is
**two columns**, with the split chosen from the material.

### 3. Establish the subject before deciding about it

> **Name the thing before arguing about the thing.** If a reply decides where
> something should live, whether to keep it, or which of two options wins, it
> first says what that something *is* — in one or two lines, with its literal
> surface if it has one. A reader who cannot identify the subject cannot use the
> answer.

This is the rule the #556 exchange exposes, and it is the one rule here that
compression makes *worse* rather than better: the shorter the reply, the more
tempting it is to drop the establishing lines as overhead, and they are the part
the reader could not proceed without.

It is a third obligation, not a restatement:

| Rule | Governs | #556 reply 2 |
|---|---|---|
| 1. Answer first | where the answer sits | passed — answer on line 1 |
| 2. Frame in plain language | what vocabulary it uses | passed — no jargon |
| **3. Establish the subject** | **whether the reader can tell what the reply is about** | **failed** |

The check is the reader's follow-up. *"What hook are we talking about again"*,
*"which file?"*, *"wait, what is X"* — a clarifying question about the **subject**
rather than the answer means the subject was never established. It is checkable after the
fact, unlike most of this skill, which makes it worth stating.

Placement in the skill: beside rules 1 and 2 in the precedence list, not in the
drawing section. It governs order and content, not form.

### 4. Still no per-form trigger — but the reason has changed

The conclusion holds. The reason recorded in the earlier draft does not, and is
replaced here so the wrong one is not cited later.

**Was:** stated rules do not fire, so a boundary-sketch rule would be lost the
way the fan-out rule was on #90.

**Is:** a trigger treats the wrong cause. #90 cannot support the old claim — its
control moved two rules at once — and #99 shows three untriggered forms
appearing on demand, so availability is not the constraint. Adding *"draw a
boundary sketch when X"* would put a sixth rule into a set where one rule
already wins every contest. The selection table in change 2 is what a per-form
trigger was reaching for, and it gets there without a rule per form: it makes
the forms already in the skill addressable by the shape of the material.

If the selection table ships and boundary sketches still never appear, *that* is
when a trigger is the right instrument. Not before.

One observation to preserve, unchanged: the section that produced a decision
trace on #90 was `Untangling compressed explanations` — "name and separate the
fused things, then render the consequence as a trace." F's reply opens its trace
with *"The two questions, now separate:"*. If a decision tree needs a home, that
section is where it already lives. **n=1**, and still the one cell where noise
would look like signal.

## Boundaries and Ownership

**Who owns the rules a reply follows.**

```
upstream                    │  wfctl                    │  the individual
────────────────────────────┼───────────────────────────┼──────────────────────
i-have-adhd                 │  conversation-response-   │  personal taste
  brevity, next action      │  shape                    │
  vendored, never edited ───┼─► layers on top:          │
                            │    order, depth, register │
                            │                           │
                            │  ships to every repo   ───┼─► examples stay domain-
                            │  that runs install-skills │   agnostic (#80)
                            │                           │
                            │  defaults are the owner's │  consumer's exit ──► #106
                            │  approach, deliberately   │
```

Three ownership decisions this makes explicit:

**The register rule is wfctl's, not personal.** A reply that explains a settled
decision at length is worse for any reader in any project. It is a defect, not a
taste, so it ships in the base layer.

**The reply template is also wfctl's.** *What / Why / Impact, one visual, one
caption* is not a preference about tone — it is a composition that survives
being read in a terminal by anyone. The author's own pull requests are the
evidence it works, but the shape is not specific to them.

**The author's preferences are the default, deliberately.** wfctl is not a
neutral utility that happens to ship skills — it is the harness that makes this
development approach reproducible, and the skills are the approach. A default
that did not encode the author's way of working would leave the tool with no
position at all. So the reply template ships as the default because it is how
the owner of this repo wants replies to read, and that is a sufficient reason.

What #106 changes is the *consumer's* exit, not what ships. Today
`install-skills` has two kinds of layer — `base`, always installed, and an agent
layer derived from `--agent` — so a downstream repo takes the defaults or edits
files wfctl will overwrite. Optional layers give it a way to decline. That is a
courtesy to consumers, not a precondition for the default existing.

**Why `i-have-adhd` cannot absorb or be absorbed.** It carries `license:` in its
frontmatter and is the single vendored skill; `vendor-upstream-skills` states
that upstream owns its contents and the project owns only the layer above.
Copying its rules into `conversation-response-shape` would give those rules two
homes, which `knowledge-placement` names as the condition with no owner. The
layering stays.

**One owner for the figure rule, three pointers.** The instruction *lead with a
figure* is about to exist on four surfaces: this skill, the pull request
template, `speckit-delivery-plan`'s completion checklist, and
`finishing-a-development-branch`'s push-and-create-PR option. The last two are
#556's change, not this one — but they are only safe if they **point** rather
than restate.

```
conversation-response-shape          owns: when to draw, which form
   the draw test + selection table    (changes 2 and 3)
          │
          ├──► .github/pull_request_template.md
          ├──► speckit-delivery-plan          ─┐  #556's change,
          └──► finishing-a-development-branch ─┘  not #102's scope
```

The selection table is the thing that must not be copied. It is the part most
likely to change, and a restatement anywhere is a stale copy the moment it does.
Each pointer states the obligation — a body leads with a figure — and defers the
choice of form to the owner. `knowledge-placement` names the alternative, one
rule with four homes, as the condition with no owner.

Both downstream skills are wfctl's own (`wfctl/agents/skills/`), neither carries
`license:`, so neither raises the vendoring problem that keeps `i-have-adhd`
separate. Checked, not assumed.

**Why examples cannot be wfctl's own output.** This skill installs into every
downstream repo. #80 already records that its `wfctl end` example is a defect for
exactly this reason. The five pull requests that motivated the template are
`wfctl` and `pfms` specific and must be abstracted before they land in the file.

## Key Assumptions to Validate

| Checked | Assumed |
|---|---|
| `i-have-adhd` is the only vendored skill — `license:` in frontmatter, named in `vendor-upstream-skills` | The reply template survives contact with a non-wfctl repo. It was derived from five pull requests in two repos, both the author's. |
| The #99 exchange happened as described — both replies read from the reader's own terminal | That the two-genre split is the right cut. *Reporting a change* and *answering a question* are the two seen; a third genre may need its own opening. |
| The #556 exchange happened as described — three consecutive replies, the reader's two interventions quoted verbatim | That stating the subject rule makes it fire. It is checkable *after* the fact, from the reader's follow-up, which no other rule here is — but nothing tested whether it fires unprompted. |
| No boundary-sketch glyphs anywhere in `conversation-response-shape` | That the register rule holds past the point in a session where other rules decay. Every variant run was a fresh context. |
| wfctl's defaults are intended to encode this author's approach — stated by the owner, 2026-08-29 | |
| `_BASE_LAYER = "base"`, `_layer_keys()`, per-layer drift checks — the layer mechanism exists, optional selection does not | That deleting the ceiling sentence does not cause over-compression elsewhere. D kept it and over-compressed anyway, but no variant tested deletion against a question that genuinely asked for depth. |
| `.github/pull_request_template.md` contains the contradicted line, in the `Before / After` comment | The #90 result — one run, and the cell where noise most resembles signal. It is now load-bearing for *nothing*: the conclusion it supported has been re-derived from #99. |
| The five two-column kinds in the selection table are each already producible — four appear across the runs and the #99 replies | That a selection table fires where a per-form trigger would not. It is a different instrument, but it is still rule text, and rule text is what decays. |
| Fourteen runs, six variants, five issues — all replies preserved | |

## MVP Scope

One commit, three files:

1. `wfctl/agents/skills/conversation-response-shape/SKILL.md`
   - register rule folded in beside rule 3, per #102's own framing
   - the subject rule added to the precedence list beside rules 1 and 2
   - four contradicted passages resolved — two deleted, two replaced
   - the reply template added, with both genre openings
   - the *draw when the reader has to hold something* test, replacing length
   - the form-selection table, so the material picks the form
   - examples abstracted out of wfctl vocabulary (#80 closes with this)
2. `.github/pull_request_template.md` — the *time to read* line replaced
3. Whatever test in `tests/` asserts skill cross-references still passes

No new skill, no new frontmatter key, no CLI change.

## Not Doing (and Why)

| | Why not |
|---|---|
| A per-form trigger for the decision tree or the boundary sketch | Availability is not the constraint — #99 produced three untriggered forms on demand. The form-selection table addresses the same gap without a rule per form. Revisit only if sketches still never appear once it ships. |
| Deleting *"render the literal output"* | The control says it earns nothing, but removing a working rule on one run of evidence is a worse bet than leaving it. Revisit with more runs. |
| Merging `i-have-adhd` into this skill | Vendored. Would give its rules two homes. |
| Waiting for #106 before setting a default | wfctl is the author's harness; its defaults are the author's approach. #106 gives consumers an exit, it does not gate what ships. |
| A per-turn hook to stop the decay | That is #85, and it is the real fix for the failure this design cannot solve. Separate issue, separate worktree, already created. |
| ASCII-rendering tooling (`graph-easy`, `diagon`) | None installed; a reply is text either way. Overcomplicates a problem that is about what to draw, not how. |

## Open Questions

1. **Does any of this survive session decay?** This design's own evidence says
   rules are lost mid-session — the table rule was lost in the session that
   produced this document. Every variant run had a fresh context and therefore
   cannot measure it. Without #85's per-turn hook, the honest claim is that these
   rules work *when loaded*, which is not the same as working.

   Partially answered for one class of surface. A rule stated inside a skill that
   is invoked *at the moment the artifact is written* — `speckit-delivery-plan` at
   issue creation, `finishing-a-development-branch` at PR creation — is loaded
   when it is needed and has no forty turns to decay across. That is why #556
   resolves to two skill lines rather than a settings hook. It does nothing for
   conversation, which has no point of use: `conversation-response-shape` loads at
   turn 0 and competes with everything after it. Conversation remains #85's
   problem.

2. **Is prose word count still worth measuring?** It was this design's headline
   metric and #556 shows it scoring a failed reply as a win. It is kept as one
   measure among several, but any future variant run needs a second axis —
   whether the reader's next message is a clarifying question about the subject.

3. **Was the #90 trace caused by `Untangling`, or is it noise?** n=1. Cheap to
   settle: three more runs of C and F on the same task. Lower stakes than it was
   — no decision in this design now rests on it.

4. **Does the form-selection table actually beat the table rule?** The whole of
   change 2 rests on the claim that the table habit wins because nothing else is
   addressable. That is inferred from two cases, #90 and #99, and has not been
   run. The check is direct: the same fixed tasks, with and without the selection
   table, counting warranted against unwarranted tables.

5. **Settled: the template ships as the default.** It was asked whether a shape
   derived from one committer's pull requests should reach every repo. It should
   — wfctl is this author's harness and its defaults are deliberately theirs.
   #106 gives a consumer a way to decline; it is not a gate on the default.
   Recorded here because the question is a reasonable one to ask again, and this
   is the answer.
