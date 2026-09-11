---
disable-model-invocation: true
description: Perform a cross-artifact consistency and quality analysis across spec.md, plan.md, and tasks.md after task generation, then write a scan file into the repository recording what it covered.
allowed-tools: Read Glob Write Edit Bash(.specify/scripts/bash/check-prerequisites.sh*) Bash(wfctl status*) Bash(wfctl arch-root*) Bash(wfctl arch check*) Bash(wfctl feature-paths*) Bash(wfctl issue create*) Bash(mkdir*) Bash(git add*) Bash(git commit*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-analyze/SKILL.md` (or `../skills/speckit-analyze/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete analysis workflow.

## Read this feature's design records

Follow `.agents/skills/reading-design-records/SKILL.md` (or
`../skills/reading-design-records/SKILL.md` relative to this file, if
`.agents/skills` isn't present). It owns how the list is resolved, the four
states, and how they are reported. What it does not own is when this step reads
them, which is below.

**Before step 4's detection passes**, because pass G below consumes the result.
A record that will not read produces no pass G finding: one nobody could open is
not one a task can be shown to contradict.

## Pass G — design-record contradiction

A seventh detection pass, run beside step 4's six and reported with them.

**What it asks**: for each task in `tasks.md`, and each record in the list above,
does the task do the opposite of what the record binds?

Not *is the task unrelated to the record* — most are. Not *does the task fail to
cite the record* — a record is not a checklist. The question is reversal: the
record says the strategy is chosen at the call site, the task says inject it.

**Two sections bind, and the rest of the record does not.** Compare against
`Decision` and `Consequences`. A decision's constraints do not all fit in its
first paragraph — "this is now harder", "the failure mode this introduces" — and
a task reversing one of those reverses the decision as surely as one contradicting
its summary.

Never compare against `Considered`, `Direct baseline`, or the baseline half of
`Diagram`. Those describe what was **rejected**, so a task implementing the shape
that won reads as contradicting them — which turns every correctly-implemented
record into a finding. This is why pass G reads two named sections rather than
the whole record: more text is not more signal when half of it is the road not
taken.

**Tasks, and not `plan.md`.** The plan is what the tasks were derived from, so a
contradiction there surfaces as the tasks that carry it; reporting both would
double every finding.

**Severity comes from the record's frontmatter `status`:**

| `status` | A task reversing it |
| --- | --- |
| `approved` | CRITICAL |
| `proposed` | HIGH |
| `superseded` | no finding |
| `rejected` | no finding |
| absent or unrecognised | HIGH, and say the status was unreadable |

Both severities are step 5's own — the scale is CRITICAL / HIGH / MEDIUM / LOW
and pass G invents nothing. `approved` means a human ratified the decision, so
reversing it is a defect rather than a change of mind, and it reaches CRITICAL by
step 5's first clause. `proposed` means the decision was put and not ratified, so
a task reversing it may be the design moving: HIGH, which is where step 5 already
files a conflicting requirement. A retired decision is not one a task can
violate.

A record whose `status` is missing or is not one of the four is read as
`proposed` for severity and reported as unreadable, rather than skipped. A record
nobody can classify is the one most likely to have been hand-written outside the
template.

**Do not gate on `approved` alone.** It is the literal reading of #121 item 6 and
it ships the pass dead: only a human moves a record past `proposed`, an
unattended run moves none, and every record in this repository is `proposed`
today.

**A finding carries the record by path and the task quoted, both:**

```markdown
- **G · Design-record contradiction, CRITICAL** — T014 reverses an approved
  decision.
  Record: `<arch-root>/design/<issue>-<decision>.md`
  Decision: "<the record's Decision section, quoted>"
  Task: "<the task, quoted>"
```

Both halves, because this pass is a model's judgment rather than a mechanical
check — two runs over the same tasks can disagree — and a reader who thinks the
pass misread the record needs both to say so.

**Pass G reports; it never gates.** What step 8 does about a finding is settled
by *When nobody answers* below and by nothing here, and nothing here refuses a
transition. A CRITICAL finding is a CRITICAL finding, not a stop.

That is not in tension with the verdict rule below, which reads `unsatisfied`
while a CRITICAL stands. A verdict is a *statement about this scan*, written into
the scan file for a reviewer; a gate is a refusal to advance the pipeline.
`unsatisfied` records that a CRITICAL is open and lets the run continue — which
is what makes it worth writing down rather than worth arguing with.

**Here rather than in `speckit-analyze/SKILL.md`**: that skill is
`github/spec-kit`-derived (`vendor-upstream-skills`), so an in-place edit is
reverted by the next upstream pull with no conflict to notice. Same layer, and
the same reason, as the scan-file instruction below.

## When nobody answers

**Step 8 offers remediation and waits, and since #325 this step is automatic.**
`speckit-orchestrate` enters the command rather than printing it and stopping, so
a run with nobody watching reaches the offer and has to settle it. The #299 run
already did: it got past this pause by an agent judging that acting was fine. The
judgment was right and it was nobody's rule, which is what the rest of this
section is.

| Where it pauses | When no answer arrives |
|---|---|
| Step 8, *"Would you like me to suggest concrete remediation edits for the top N issues?"* | Settle it against the policy below rather than waiting on it. Every finding is applied or filed, and the counts in the scan file say which each one was. |
| Step 8's *"(Do NOT apply them automatically.)"*, and the skill's *"Do **not** modify any files"* | Overridden for an in-scope fix, and for nothing else. This is the second stated override in this file — the scan file below is the first — and it is stated for that one's reason: a wrapper that silently contradicts the skill it points at teaches the reader to discount both. The skill's rule is unscoped, so both overrides are real overrides rather than readings of it; its own step 6b mandates writing `analysis-report.md` and is the third, which nothing reconciles. |
| Step 7's Next Actions, *"Recommend resolving before `/speckit.implement`"* | Still written, and computed against what stands *after* remediation. A Next Actions block derived from the pre-fix report tells the reviewer to resolve findings this run already resolved, which reads as the fixes not having happened. Step 7's three outcomes do not cover what that ordering leaves most often — remediation is what clears CRITICALs, so a standing HIGH with no CRITICAL above it is the normal end state. Say so in its own line: what stands, at what severity, and that it was filed rather than fixed. *"only LOW/MEDIUM"* is false there, and reporting it as proceed-with-suggestions is the one wrong answer. |

**Deliberately not conditional on `auto_approve`.** That grant moves approval
authority for design gates, and only a human hands it over; nothing here moves
any. An in-scope fix stays inside three artifacts the pipeline regenerates and
lands in the branch diff the reviewer reads, and the one outward-facing action in
this policy — filing — is gated already and is deferred to rather than routed
around. Reading the grant would also leave ungoverned the exact run that has no
rule today: #299 was an unattended pass nobody granted anything to.

### In scope, and what it means

**A finding whose fix is in scope is applied. Every other finding is filed.**
There is no third door. A finding left neither fixed nor filed is one this step
found and then lost, and the counts below are what make that visible.

In scope is two conditions, and a fix meets both or it is out:

1. The fix is confined to `spec.md`, `plan.md` and `tasks.md` — the three
   artifacts this step reads, taken as a set. A terminology drift is corrected in
   every file carrying it, because a rename applied to one of two files creates
   the drift it was called to remove.
2. It decides nothing those three, and this feature's design records, have not
   already decided.

Making one artifact say what the others already say satisfies the second
condition rather than bending it. Choosing a number the artifacts never chose,
adding a requirement, or picking between approaches the plan deliberately left
open fails it, however small the edit that would carry the choice.

**A coverage gap is in scope, and it is the case this definition exists to
settle.** Pass E finds a requirement with zero tasks; the fix adds a task, so
`tasks.md` gains a line it did not have. It still decides nothing: `spec.md` set
the scope when it stated the requirement, and `tasks.md` failing to cover it is
the defect rather than the boundary. Filing it instead sends the feature into
`implement` without the requirement and books the omission as separate work,
which inverts what this step sits before `implement` to do.

**Materially larger is a third route out of scope.** A fix that cannot be written
as an edit to named sections of those artifacts — because it restructures the plan,
or cascades through every task the plan derives — is filed whatever it decides,
and the finding gives its size as the reason.

### Filing, and the gate it meets

**A filed finding is an issue, and `wfctl issue create` refuses by default.**
Nothing on a fresh branch has allowed an outward-facing action
(`a-human-grants-outward-facing-authority`), so an unattended run that was
granted nothing cannot file — and must not look for a way around the refusal,
which is the gate working rather than a tracker misconfigured.

Where filing is refused the finding is still `Accepted`, and its reason carries
both halves — why it stands, and that nobody was told:

```markdown
→ Accepted: out of scope — quantifying "responsive" is a product decision.
  Not filed: outward actions are not authorized on this branch.
```

That is not the finding being lost. The scan file is committed to the branch and
the reviewer reads it at the PR, which is where an unattended run's decisions are
reviewed anyway. What the second line buys is that a finding already filed and a
finding somebody still has to file stop reading identically.

**One issue per cause, not per finding.** Three findings that are one ambiguity
seen from three passes get one issue, cited by all three. The alternative turns a
thorough analysis into tracker debt, which is the failure the apply half of this
policy exists opposite. It also puts `Accepted: 4` and *three issues* on the same
run, so the count alone does not say how much tracker work is outstanding — the
`### Filing` block below is what does.

**A filing that was refused keeps its title and body, in `### Filing`.** The
reason line says somebody still has to file it; without the text it also says
they have to write it again, from a report that by then is one of several in the
same file. Record the command that would have run, verbatim — an unattended run
that had the grant and one that did not then differ by whether the command was
executed, rather than by what survives of it.

### The counts say what happened

The section below reports `Findings: N · Critical: N · Acted on: N · Accepted:
N`, and **`Acted on` plus `Accepted` equals `Findings`**. That is what "no third
door" looks like once it is written as arithmetic. Every `Accepted` carries a
reason — `writing-a-scan-file` already asks for one, and this policy is what
makes it load-bearing, because a finding fixed and a finding nobody touched are
the same row in a table until the reason separates them.

**A check could see this, and one is planned.** The counts, the arithmetic
between them, and a reason on every `Accepted` row all land in the scan file,
which is an artifact this work already produces — the yes side of
`a-rule-is-expressed-as-a-check`. Prose here states the rule; #335 is the
mechanism that would observe it.

## Write the scan file

Follow `.agents/skills/writing-a-scan-file/SKILL.md` (or
`../skills/writing-a-scan-file/SKILL.md` relative to this file, if
`.agents/skills` isn't present). It owns the destination, the session rule, the
commit and the check. What it does not own is what *this* step scanned, which is
below.

**The scan file is written on every exit path, including an abort.** Step 1 above
halts when `spec.md`, `plan.md` or `tasks.md` is missing. That is exactly the
`inconclusive` case below, and reaching the abort without writing the file leaves
an analysis that *could not run* looking identical to one nobody started — which
is the defect #307 is about, met on the failure path instead of the success one.
Write the section with `Verdict: inconclusive` naming which artifact was missing,
then stop.

**This overrides the skill's read-only rule, and it is the narrower of this
file's two overrides of it.** `speckit-analyze` states the rule twice —
**STRICTLY READ-ONLY** under Operating Constraints, *"NEVER modify files"* under
Analysis Guidelines — and neither is scoped to the artifacts it analyses. *When
nobody answers* above lifts it for a remediation edit and bounds which edits
qualify; what this section adds is
independent of that and holds on a run that remediates nothing — one new file the
step writes about its own work, outside `FEATURE_DIR`, and one commit of that
path. Both are stated rather than left for a reader to reconcile, because a
wrapper that silently contradicts the skill it points at teaches the reader to
discount both.

**File**: `<arch-root>/scans/<issue>-analyze.md`.
**Detail**: `FEATURE_DIR/checklists/analysis-report.md`.

**Write it after step 8, and never leave the step without having written it.**
Not after step 6b: `Acted on` and `Accepted` are not knowable until remediation
has been settled, and a scan file written between the report and that
conversation commits counts that are already stale.

**The two halves of that sentence used to be the same instruction and are not
since #325.** Step 8 asks the user whether to apply remediation. With nobody
there to answer, a run that treats it as a stop leaves `analysis-report.md`
written — which is the whole of what `_predicates.analyze` reads, so the step
reports `done` — and no scan file at all. That is #307's defect restored on the
one step whose scan file is cited as earning the flip, and it is reachable only
now: before #325 the pause happened *outside* this command, with nothing yet
written.

So where step 8 cannot be answered, settle it rather than waiting on it, and
write the section with the counts that settlement produced. `Accepted` is the
honest value for a finding nobody acted on, and it takes a reason — a finding
fixed and a finding nobody touched read identically as a row in a table, which
`writing-a-scan-file` already says is the difference a reviewer needs. The policy
for settling is *When nobody answers* above (#331); what this paragraph holds is
the narrower thing it cannot, that no settlement ends with an unwritten scan
file.

**Coverage rows** — the six detection passes of step 4, in its order, then pass G,
plus one measurement. Read down the left column and then the right; across the
rows gives A, D, B, E, C, F, which is not step 4's order:

```
A · Duplication          D · Constitution alignment
B · Ambiguity            E · Coverage gaps
C · Underspecification   F · Inconsistency
                         G · Design-record contradiction
```

Then a final row `| Requirement-to-task coverage | N% |`. **That row carries a
percentage rather than one of the four statuses**, and it is the only row that
does — the metric step 6 already computes, kept beside the passes because a
reader comparing thoroughness reads them together. Pass G sits between
`F · Inconsistency` and that row, so the statuses stay contiguous and the one
measurement stays last.

**Pass G's row is written on every run, including one that read no records** —
`Deferred` with its reason when the pass could not run, never absent, which is
the shared skill's rule and not a new one. A run that found nothing, a run whose
input was missing and a run nobody started must not render identically; that is
#307's argument one directory over, and it is why this is a coverage row rather
than a findings line.

Its status is one of the same four every other row carries. The count goes in a
parenthetical, because the row above about `Requirement-to-task coverage` being
the only one carrying a measurement stays true:

```
| G · Design-record contradiction | Clear (2 records read)        |
| G · Design-record contradiction | Outstanding (1 CRITICAL)      |
| G · Design-record contradiction | Outstanding (2 HIGH)          |
| G · Design-record contradiction | Resolved (1 HIGH, task fixed) |
| G · Design-record contradiction | Clear (design.md lists none)  |
| G · Design-record contradiction | Deferred (no design.md)       |
| G · Design-record contradiction | Deferred (no records section) |
```

`Clear` twice, and they are different facts: the pass read N records and found
nothing, or it ran against a `design.md` that lists none. Both mean the pass
reached its answer. The two `Deferred` rows mean it could not — no `design.md`,
or one predating the section — which the shared skill calls `unknown`.

**A pass with one finding applied and another accepted takes `Outstanding`, and
its parenthetical carries both.** One row per pass and one status per row, so the
status answers the only question a status can: is anything from this pass still
open. `Resolved` there would be false and `Outstanding` alone erases the fix,
which is why the count beside it is two numbers rather than one:

```
| E · Coverage gaps | Outstanding (1 MEDIUM; 1 CRITICAL resolved) |
```

**Verdict, for this step**: `satisfied` — all three artifacts were read and no
CRITICAL finding stands. `unsatisfied` — at least one CRITICAL finding is open.
`inconclusive` — an artifact was missing or unreadable, so coverage could not be
computed; name which one.

**A CRITICAL this run fixed does not stand; one it filed does.** The verdict is
read after remediation, not from the report step 6 produced, so a pass that found
three CRITICALs and applied all three is `satisfied` and says so honestly. An
`Accepted` CRITICAL keeps the verdict `unsatisfied` however good its reason —
filing it moves who finishes it, not whether it is open.

**`Critical: N` counts what was found, not what stands.** It sits beside
`Findings: N`, which counts the same way, and the verdict two lines above is
already the statement about what stands. Read the other way, a run that found a
CRITICAL and fixed it reports `Critical: 0 · Verdict: satisfied` — a clean row
for the run that did the most work, and the one finding a reviewer would most
want to see.

**`Requirement-to-task coverage` is also post-remediation.** It is the metric
step 6 computes, recomputed after step 8 for the reason the Next Actions row
above gives: a pre-fix percentage on the same row as a `Resolved` coverage-gap
status says the gap was both closed and not.

**Section shape**:

```markdown
## Session YYYY-MM-DD

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: N · Critical: N · Acted on: N · Accepted: N
- Detail: <FEATURE_DIR>/checklists/analysis-report.md

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| … the five others |
| G · Design-record contradiction | Clear (N records read) |
| Requirement-to-task coverage | N% |

### Findings

- **<pass>, <severity>** — what was wrong.
  → Fixed: <what changed>. Decided against <the alternative>: <why>.
  → Accepted: <why this stands rather than being fixed>.
    Not filed: <why nobody was told>.

### Filing

- **<cause>** — <the findings it covers>.
  `wfctl issue create --title "<title>" --body "<body>"`

### Deferred

- **<pass>** — <what was left, and why it belongs to a later step>.
```
