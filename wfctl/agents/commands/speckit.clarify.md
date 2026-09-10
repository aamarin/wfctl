---
disable-model-invocation: true
description: Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec.
handoffs:
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
allowed-tools: Read Glob Write Edit Bash(.specify/scripts/bash/check-prerequisites.sh*) Bash(wfctl status*) Bash(wfctl arch-root*) Bash(wfctl arch check*) Bash(mkdir*) Bash(git add*) Bash(git commit*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-clarify/SKILL.md` (or `../skills/speckit-clarify/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete clarification workflow.

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
order, every one of them present:

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
  Decided against **<option B>**: <why it lost>.
  Decided against **<option C>**: <why it lost>.
- **<category>** — what was ambiguous.
  Q: <the question> → A: <the answer>.
  No options offered — short answer.

### Deferred

- **<category>** — <what was not asked, and why it belongs to a later step>.
```

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
mode. That is the one respect this layer differs from `speckit.brainstorm.md`'s,
whose layer is conditional on `auto_approve` and moves where an approval happens.
