---
disable-model-invocation: true
description: Perform a cross-artifact consistency and quality analysis across spec.md, plan.md, and tasks.md after task generation, then write a scan file into the repository recording what it covered.
allowed-tools: Read Glob Write Edit Bash(.specify/scripts/bash/check-prerequisites.sh*) Bash(wfctl status*) Bash(wfctl arch-root*) Bash(wfctl arch check*) Bash(git add*) Bash(git commit*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-analyze/SKILL.md` (or `../skills/speckit-analyze/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete analysis workflow.

## Write the scan file

Follow `.agents/skills/writing-a-scan-file/SKILL.md` (or
`../skills/writing-a-scan-file/SKILL.md` relative to this file, if
`.agents/skills` isn't present). It owns the destination, the session rule, the
commit and the check. What it does not own is what *this* step scanned, which is
below.

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

**Coverage rows** — the six detection passes of step 4, in its order, plus one
measurement:

```
A · Duplication          D · Constitution alignment
B · Ambiguity            E · Coverage gaps
C · Underspecification   F · Inconsistency
```

Then a final row `| Requirement-to-task coverage | N% |`. **That row carries a
percentage rather than one of the four statuses**, and it is the only row that
does — the metric step 6 already computes, kept beside the passes because a
reader comparing thoroughness reads them together.

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
| Requirement-to-task coverage | N% |

### Findings

- **<pass>, <severity>** — what was wrong.
  → Fixed: <what changed>. Decided against <the alternative>: <why>.
  → Accepted: <why this stands rather than being fixed>.

### Deferred

- **<pass>** — <what was left, and why it belongs to a later step>.
```
