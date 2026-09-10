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

**Before step 4's detection passes**, because one of them consumes the result.

```bash
wfctl feature-paths      # read FEATURE_DIR from the output
```

Read `<FEATURE_DIR>/design.md` and take the section headed
`## Software design decisions`. Every **list item** of the form
`- <path> — <text>` names a record; read each one.

**Prose in that section names no records.** The section carries prose by design —
`/speckit.brainstorm` requires a level answered with no record to say so in one
line rather than delete the heading — and that prose may name a *level-2* record.
A level-2 record read as level-3 binds nothing while looking like it does.

**Do not glob `<arch-root>/design/` by issue number instead.** That was the first
mechanism and it is silently wrong on any branch cut from an epic: the worktree
carries the epic's number, the record carries the child issue's, so the glob
loads another feature's record and misses this one. Neither failure raises
anything. `docs/architecture/design-md-indexes-the-records.md` carries the
argument.

**Report what was read, always** — including when there was nothing:

```
Design records: 2 listed in design.md
  <path>
  <path>

Design records: none — design.md records no level-3 decision

Design records: unknown — no design.md at <FEATURE_DIR>
```

The last two are different facts and are never collapsed. One says a design pass
ran and recorded no structural decision; the other says no design pass ran. A
step that reports neither reproduces #307's defect one directory over.

A listed path that will not read — missing, or outside the working tree — gets
its own line, `<path> — listed, not found`, and does not stop the step. Pass G
produces **no finding** for such a record: one nobody could open is not one a
task can be shown to contradict.

Report paths, never a summary. A digest of a record is a second copy of it, and
the copy is what drifts.

**Here rather than in `speckit-analyze/SKILL.md`**: that skill is
`github/spec-kit`-derived (`vendor-upstream-skills`), so an in-place edit is
reverted by the next upstream pull with no conflict to notice, and the behaviour
then regresses at a moment whose diff mentions neither the skill nor this file.
Same layer, and the same reason, as the scan-file instruction below.

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
| `proposed` | warning |
| `superseded` | no finding |
| `rejected` | no finding |

`approved` means a human ratified the decision, so reversing it is a defect
rather than a change of mind. `proposed` means the decision was put and not
ratified, so a task reversing it may be the design moving — worth reporting, not
worth blocking. A retired decision is not one a task can violate.

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

**Pass G's row is written on every run, including one that read no records.**
Its two empty values are distinct — `None listed` and `No design.md` — for the
reason the whole file exists: a run that found nothing, a run whose input was
missing, and a run nobody started must not render identically. That is #307's
argument met one directory over, and it is why this is a coverage row rather
than a findings line.

```
| G · Design-record contradiction | Clear (N records read) |
| G · Design-record contradiction | N CRITICAL             |
| G · Design-record contradiction | N warning              |
| G · Design-record contradiction | None listed            |
| G · Design-record contradiction | No design.md           |
```

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
