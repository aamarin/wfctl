---
disable-model-invocation: true
description: Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec.
handoffs:
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
allowed-tools: Read Glob Write Edit Bash(.specify/scripts/bash/check-prerequisites.sh*) Bash(wfctl status*) Bash(wfctl issue view*) Bash(wfctl arch-root*) Bash(wfctl arch check*) Bash(mkdir*) Bash(git add*) Bash(git commit*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-clarify/SKILL.md` (or `../skills/speckit-clarify/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete clarification workflow.

## When nobody answers

**Step 4 is a questioning loop written for a person, and since #325 this step is
automatic.** `speckit-orchestrate` enters the command rather than printing it and
stopping, so a run with nobody watching reaches the loop and has to get out of
it. Below is what each of its pauses resolves to. `speckit-clarify/SKILL.md` is
spec-kit-derived and stays unedited (`vendor-upstream-skills`), so this file is
the layer above it.

| Where it pauses | When no answer arrives |
|---|---|
| Step 4, *"Present EXACTLY ONE question at a time"* and *"After the user answers"* | Take the answer the step has already computed — the `**Recommended:** Option X` it renders above a multiple-choice table, the `**Suggested:** …` it renders for a short answer — and record it together with the reasoning it was rendered with. That reasoning is the basis. A recommendation recorded without it is a question decided silently, which is the failure this step exists to prevent, and nobody being there to ask does not make it acceptable. |
| Step 4's stop conditions, *"User signals completion"*, and the behaviour rule *"Respect user early termination signals"* | None arrives, and none is inferred from the absence of one. Two of the loop's own conditions remain — every critical ambiguity resolved, or five questions asked — and the withdrawal rule below adds a third: an empty queue with neither of those met. |
| Step 8, *"recommend whether to proceed to `/speckit.plan` or run `/speckit.clarify` again later"* | Still written, and still a recommendation. What the pipeline does next is `wfctl status`' answer rather than this line's, and the two are allowed to differ — this one is addressed to the reviewer. |

**The trigger is a pause reached with no answer, not a mode read.** Ask each
question as step 4 renders it, recommendation and all — including the ones the
withdrawal rule below covers, which are the questions a person is the only
authoritative source for. Where an answer comes back it is the answer, and
nothing in this section changed the run.

**A question the withdrawal rule covers is rendered without the
`**Recommended:**` line,** carrying in its place one sentence saying the
repository does not settle it and a person has to. Step 4's format mandates that
line on every multiple-choice question, so this is an override and is stated as
one: inventing a recommendation to satisfy the format is the silent decision the
rule below forbids, reached through the format instead of through the reasoning.

**That also settles which rule fires when such a question reaches a pause with no
answer.** The first row above takes the recommendation step 4 computed; a
question that rendered none leaves it nothing to take, and the withdrawal rule
below is what covers the pause. No question is reached by both.

**Deliberately not conditional on `auto_approve`,** which is one of two respects
in which this layer differs from `speckit.brainstorm.md`'s — the rejected-options
rule at the end of this file is the other. That table is conditional
because what it moves is approval authority, and only a human can hand that over.
This one moves none: an answer derived from the repository is information, carried
with the basis that produced it, and a reviewer who disagrees overrules it at the
PR exactly as they would overrule an answer a person gave. Reading the grant
would also leave ungoverned the run that has no rule today — an unattended pass
nobody granted anything to, which is how the #299 run got past `analyze`'s pause
by an agent deciding rather than by a rule.

### A question the repository cannot settle

**Do not invent a recommendation in order to have one.** Step 4 grounds its
recommendation in best practice and in what `spec.md` already says; unattended,
widen that to the branch's issue (`wfctl issue view`) and to this feature's
design records, both of which carry decisions the spec was written from. That is
an instruction rather than a description of step 4 — the frontmatter grants the
read for it — and `plan.md` is deliberately not on the list, because on a first
clarify run there is none.

A question none of those reach is a question about what somebody wants, and
deriving an answer to it is the silent decision the first row above rules out,
reached by a longer route.

Such a question is put like any other and withdrawn only when no answer arrives.
Withdrawn, it never counts against the five, and its slot is refilled by
re-running step 3's ranking over what is left of step 2's coverage map.

**Not counting it is an override of *"Never exceed 5 total asked questions"*,
stated rather than left to be reconciled.** The cap bounds what a person is asked
to answer, and a withdrawn question is one nobody answered — the skill carves out
the same shape already, in the retries it declines to count as new questions. The
attended run is what shows the override is narrow: an answer that comes back is
an answer, the question is never withdrawn, and five is five. Step 3 keeps only
five candidates and holds no sixth, so there is nothing waiting to be promoted,
and a withdrawal that spent a slot would narrow coverage by exactly the amount
this rule was supposed to protect. Its category takes an `Outstanding` row in
the coverage table, and the question and what made it underivable go under
`### Outstanding` in the scan file, in the same terms the findings use. The
marker rule below already requires any `[NEEDS CLARIFICATION` marker to go with
it, so the spec reads the same whether the question was declined by the scan or
withdrawn by this rule.

**`Outstanding` rather than `Deferred`, and the verdict is the reason.**
`Deferred` says a later step is the better place to answer it; no later step
answers this one either, and only a person closes it. This widens the status —
the workflow's own definition is *still Partial or Missing but low impact*, and a
question the repository cannot settle can be the highest-impact thing the scan
found. Widened deliberately: the alternative is a high-impact row reported as
`Deferred`, which leaves the verdict `satisfied`. `Outstanding` is also what
makes this step's verdict read `unsatisfied` — the true statement about a scan
that reached a question it could not settle, and the one a `Deferred` row would
have hidden.

**One `### Outstanding` block, not one per rule.** `| Category | Status |` is two
columns wide and one of them is a single word, which is why the question goes to
the block rather than the row. The marker rule below sends a declined
`[NEEDS CLARIFICATION` marker to the same block, and the two arrive with
different things to say — a withdrawn question has no answer to give, a declined
marker has one nobody judged worth asking for. Say which it is.

**A run that withdrew every candidate did not find a clean spec.** The workflow's
behaviour rule writes `- No critical ambiguities detected.` whenever no question
was asked, which is true of a scan that found nothing and false of one that found
only questions it could not settle. Write the `## Clarifications` section either
way — it is what marks the step done — carrying a bullet that names what was
withdrawn and points at the scan file, never that one.

**A standing `Outstanding` row makes this verdict permanent, and that matters
once something reads it.** Nothing does today; `writing-a-scan-file` says the
verdict is there for a later gate to read through `blocks(verdict,
"repo-declared")`. A gate that blocks on `unsatisfied` is not cleared by
re-running unattended, because no unattended pass can settle a question the
repository does not contain — an attended one can, which is the whole reason the
question is still put. Since #332
`speckit-orchestrate` counts passes and stalls rather than looping, so what it
produces is a stall reported against `clarify` — a pipeline stopped by the step
correctly saying it did its job. Whichever change wires that gate has to exempt
this row, and this paragraph is where it finds out.

**A check could see this, and the planned one does not yet.** Every answer this
section produces lands in `spec.md`'s `## Clarifications` bullet and in the scan
file's finding beside it, so *recorded with its basis* is visible in an artifact
the work already produces — the yes side of `a-rule-is-expressed-as-a-check`.
#335's `clarify_block` is scoped to #334's postconditions, standing markers and
the `## Clarifications` section, and reads no `Basis:` line. Whichever change
ships that block has to widen it or say why not; until then this rule is prose on
the checkable side of the test, which the record calls the rule's absence rather
than a partial implementation of it.

## No marker survives the scan

**Every `[NEEDS CLARIFICATION` marker left in `spec.md` is removed before this
step ends** — either by the answer that resolved it, or by rewriting it as an
`Outstanding` row in the coverage summary the workflow already produces. A marker
the scan read and declined to ask about is a decision, and it is recorded as one
rather than left in the text.

Stated here because the workflow above never mentions the marker syntax — it
scans a taxonomy, not a token — and its own behaviour rule sends a low-impact
marker down the "no critical ambiguities detected" path, which writes the
`## Clarifications` section and suggests advancing. That is the correct judgment
and the wrong artifact: `wfctl` reads a standing marker as the scan being
unfinished, so the step reports `in_progress` and the pipeline routes straight
back here.

Before #325 that cost a stop a human could see. Since the flip it does not stop:
`clarify` is automatic, a successful pass provably cannot change what the
predicate reads, and `speckit-orchestrate` re-enters with identical inputs and no
iteration bound (#332). One rule in this file converges it, where a guard in the
pipeline would be a second mechanism for a judgment this step already made.

**An `Outstanding` row is not a lesser answer.** The workflow's own reporting
vocabulary carries it for exactly this — *still Partial or Missing but low
impact* — and a row a reviewer can disagree with beats a marker that only a
re-run can find. Say which category it fell under and why it was declined, in the
same terms the scan file's findings use.

Not in `speckit-clarify/SKILL.md`, which is spec-kit-derived: an in-place edit
there is reverted by the next upstream pull with no conflict to notice
(`vendor-upstream-skills`).

## Write the scan file

Follow `.agents/skills/writing-a-scan-file/SKILL.md` (or
`../skills/writing-a-scan-file/SKILL.md` relative to this file, if
`.agents/skills` isn't present). It owns the destination, the session rule, the
commit and the check. What it does not own is what *this* step scanned, which is
below.

**The scan file is written on every exit path, including an abort.** The workflow
above stops early when `spec.md` is missing or `check-prerequisites.sh` cannot be
parsed, and tells the reader to run `/speckit.specify`. That is exactly the
`inconclusive` case below, and reaching the abort without writing the file leaves
a scan that *could not run* looking identical to one nobody started — which is the
defect #307 is about, met on the failure path instead of the success one. Write
the section with `Verdict: inconclusive` naming what was missing, then stop.

**File**: `<arch-root>/scans/<issue>-clarify.md`.
**Detail**: `FEATURE_DIR/spec.md` § Clarifications.

**Coverage rows** — the ten taxonomy categories the workflow above scans, in its
order, every one of them present. Read down the left column and then the right;
across the rows gives an order the workflow never uses:

```
Functional Scope & Behavior          Edge Cases & Failure Handling
Domain & Data Model                  Constraints & Tradeoffs
Interaction & UX Flow                Terminology & Consistency
Non-Functional Quality Attributes    Completion Signals
Integration & External Dependencies  Misc / Placeholders
```

The map behind them already exists: step 2 above builds it on every run and
discards it unless no question is asked. Writing it down is what this step stops
throwing away.

Its scanning vocabulary is Clear / Partial / Missing and its reporting vocabulary
is Clear / Resolved / Deferred / Outstanding. **The reported one is what goes in
the file** — a reader wants what the scan concluded, not what it saw first.

**Verdict, for this step**: `satisfied` — the scan ran and nothing material is
open. `unsatisfied` — a category is Outstanding, or a high-impact one is
Deferred. `inconclusive` — the scan could not run: no `spec.md`, or one still
carrying its template.

**Section shape**:

```markdown
## Session YYYY-MM-DD

- Verdict: satisfied
- Scanned: spec.md
- Asked: N · Answered: N · Outstanding: N · Deferred: N
- Detail: <FEATURE_DIR>/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| … the nine others |

### Findings

- **<category>** — what was ambiguous.
  Q: <the question> → A: <the answer>.
  Basis: <what the answer was derived from, or who gave it>.
  Decided against **<option B>**: <why it lost>.
  Decided against **<option C>**: <why it lost>.
- **<category>** — what was ambiguous.
  Q: <the question> → A: <the answer>.
  Basis: <what the answer was derived from, or who gave it>.
  No options offered — short answer.

### Outstanding

- **<category>** — withdrawn: <the question, and what made it underivable>.
- **<category>** — declined: <the marker, and why it was not worth asking>.

### Deferred

- **<category>** — <what was not asked, and why it belongs to a later step>.
```

**`Basis` is where *When nobody answers* lands, and it is one line on every
finding rather than only on a derived one.** An answer a person gave has a basis
too — *"the reviewer chose B in the PR thread"* is one — and a field present only
when nobody was watching tells a reader which runs to trust by its own absence.
`Decided against` cannot carry it: those lines are the reasoning for the options
*not* taken, which is the opposite question.

### The options the answer was chosen over

**One `Decided against` line per lettered option the question offered and the
answer did not take.** Step 4 above renders each multiple-choice question as 2–5
lettered options and takes one; the others are what the step considered, and
nothing but this file carries them past the run. So keep each question's option
table until the file is written — the workflow records only the answer, and the
table is gone from every later step.

*Lettered* is the whole of what counts. The rendered table can carry a trailing
`Short` row, which is an escape hatch from the options rather than one of them —
a `Decided against **Short**` line has no true reason to give, and the rule below
then forces one to be invented.

A single line naming one representative alternative reports a two-option question
and a five-option one identically, and *what else was on the table, and why not
that* is the only question a reviewer can ask of a resolved ambiguity (#286).
**Do not narrow a question to shorten this section.** Step 4 chooses the options
and this step reports them, and an option dropped before the question is asked is
the one loss no reader of this file can see.

**The reason an option lost is the reason it actually lost.** Losing on fit is a
reason; a weakness the option does not have is never one — the standard
`architecture-decisions` holds its own `Considered` to. An option invented to be
knocked down is worse than no record, because a reviewer cannot tell it from one
that was really on the table.

**Only a question that rendered no option table writes `No options offered —
short answer.`** — on its own line under the finding, in place of the `Decided
against` lines. Step 4's short-answer branch renders no table, so there is
nothing rejected to name and inventing a set to reject is the straw the paragraph
above rules out.

**A multiple-choice question is not that case, however it was answered.** Step 4
lets an A/B/C question be answered in free-form words instead of by letter, and
the options it offered were still offered. *Which* of them lost is what the
wording hides, and Step 4 has already settled it — it accepts a free-form answer
only once that answer maps to one of the offered options or stands as a short
answer of its own:

- **It mapped to an option.** That option is the answer, whatever words carried
  it, so it gets no line and the rest do. `Decided against` naming the option the
  answer chose contradicts the `A:` recorded two lines above it, and a reader has
  nothing left to settle which of the two is the decision.
- **It stood on its own.** No lettered option was taken, so every one of them
  gets a line, and the finding records what the free-form answer was.

Neither branch is the short-answer exemption. This is the one path on which both
rules above look like they apply, and taking the exemption here destroys exactly
the evidence this section exists to keep.

**This holds however the answer was chosen.** A human picking option B destroys A
and C exactly as thoroughly as an unattended run does, and the reviewer reading
the change is equally unable to see them — so the rule is not conditional on the
mode. That is the other of the two respects in which this layer differs from
`speckit.brainstorm.md`'s — *When nobody answers* above is the first, and both
turn on the same property: nothing in this file moves an approval, and
`speckit.brainstorm.md`'s layer is conditional precisely because its does.
