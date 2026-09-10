---
disable-model-invocation: true
description: Perform a cross-artifact consistency and quality analysis across spec.md, plan.md, and tasks.md after task generation, then write a scan file into the repository recording what it covered.
allowed-tools: Read Glob Write Edit Bash(.specify/scripts/bash/check-prerequisites.sh*) Bash(wfctl status*) Bash(wfctl arch-root*) Bash(wfctl arch check*) Bash(wfctl feature-paths*) Bash(mkdir*) Bash(git add*) Bash(git commit*)
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
does the task do the opposite of what the record's `Decision` section says?

Not *is the task unrelated to the record* — most are. Not *does the task fail to
cite the record* — a record is not a checklist. The question is reversal: the
record says the strategy is chosen at the call site, the task says inject it.

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

**Pass G reports; it never gates.** Step 8's remediation stays an offer, and
nothing here refuses a transition. A CRITICAL finding is a CRITICAL finding, not
a stop.

That is not in tension with the verdict rule below, which reads `unsatisfied`
while a CRITICAL stands. A verdict is a *statement about this scan*, written into
the scan file for a reviewer; a gate is a refusal to advance the pipeline.
`unsatisfied` records that a CRITICAL is open and lets the run continue — which
is what makes it worth writing down rather than worth arguing with.

**Here rather than in `speckit-analyze/SKILL.md`**: that skill is
`github/spec-kit`-derived (`vendor-upstream-skills`), so an in-place edit is
reverted by the next upstream pull with no conflict to notice. Same layer, and
the same reason, as the scan-file instruction below.

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

**This overrides the skill's read-only rule, and only here.** `speckit-analyze`
says **STRICTLY READ-ONLY** twice — of the artifacts it analyses, which stays
true: nothing below edits `spec.md`, `plan.md` or `tasks.md`, and the offer of
remediation at step 8 is still an offer. What is added is one new file the step
writes about its own work, outside `FEATURE_DIR`, and one commit of that path.
Stated here rather than left for a reader to reconcile, because a wrapper that
silently contradicts the skill it points at teaches the reader to discount both.

**File**: `<arch-root>/scans/<issue>-analyze.md`.
**Detail**: `FEATURE_DIR/checklists/analysis-report.md`.

**Write it after step 8**, not after step 6b. `Acted on` and `Accepted` are not
knowable until remediation has been settled, and a scan file written between the
report and that conversation commits counts that are already stale.

**Coverage rows** — the six detection passes of step 4, in its order, then pass G,
plus one measurement:

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

**Verdict, for this step**: `satisfied` — all three artifacts were read and no
CRITICAL finding stands. `unsatisfied` — at least one CRITICAL finding is open.
`inconclusive` — an artifact was missing or unreadable, so coverage could not be
computed; name which one.

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

### Deferred

- **<pass>** — <what was left, and why it belongs to a later step>.
```
