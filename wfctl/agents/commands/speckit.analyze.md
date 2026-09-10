---
disable-model-invocation: true
description: Perform a non-destructive cross-artifact consistency and quality analysis across spec.md, plan.md, and tasks.md after task generation.
allowed-tools: Read Glob Write Bash(.specify/scripts/bash/check-prerequisites.sh*) Bash(wfctl status*) Bash(wfctl arch-root*) Bash(wfctl arch check*) Bash(git add*) Bash(git commit*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-analyze/SKILL.md` (or `../skills/speckit-analyze/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete analysis workflow.

## Write the scan file

The report above is written to `{FEATURE_DIR}/checklists/analysis-report.md`,
which resolves outside the working tree in most repos and is gitignored in the
rest. A reviewer opening the change sees none of it, so an analysis that found six
problems and one that never ran are the same pull request. Write a second file,
into the repository, that says what this analysis reached.

Here rather than in `speckit-analyze/SKILL.md`: that skill is `github/spec-kit`
derived, and `vendor-upstream-skills` prefers a layer over an edit — an in-place
change is reverted by the next upstream pull with no conflict to notice. The
decision is `docs/architecture/the-scan-is-attested-where-the-reviewer-reads.md`;
its shape is `docs/architecture/design/307-the-coverage-map-is-the-evidence.md`,
which was written for `/speckit.clarify` and applies here unchanged.

Ask for the destination rather than writing it in — a repo can declare `arch_root`
anywhere, and `docs/architecture` is the default, not the truth:

```bash
wfctl arch-root      # prints the root; the file is <root>/scans/<issue>-analyze.md
```

`<issue>` is the tracker key `wfctl status` prints, the same key
`<root>/design/` and `<root>/declarations/` are named for.

**The coverage table is the body.** A findings list renders identically for a
thorough pass over consistent artifacts and for a pass that never opened them. A
table of the six detection passes does not: a run that skipped them has no rows to
write.

One file per step, and **one section per analysis session, appended** — the same
shape `/speckit.clarify`'s scan file uses, and the same shape the clarification
workflow already writes into `spec.md`. A re-run never discards an earlier
session: a second pass finding nothing is only meaningful given what the first
one found. What is not appended across is *steps* — `/speckit.clarify` writes its
own file and this one never edits it.

```markdown
# Analysis scan — #<issue>

## Session YYYY-MM-DD

- Verdict: satisfied | unsatisfied | inconclusive
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: N · Critical: N · Acted on: N · Accepted: N
- Detail: <FEATURE_DIR>/checklists/analysis-report.md

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Clear |
| C · Underspecification | Clear |
| D · Constitution alignment | Clear |
| E · Coverage gaps | Clear |
| F · Inconsistency | Clear |
| Requirement-to-task coverage | N% |

### Findings

- **<pass>, <severity>** — what was wrong.
  → Fixed: <what changed>. Decided against <the alternative>: <why>.
  → Accepted: <why this stands rather than being fixed>.

### Deferred

- **<pass>** — <what was left, and why it belongs to a later step>.
```

- **Verdict.** `satisfied` — all three artifacts were read and no CRITICAL finding
  stands. `unsatisfied` — at least one CRITICAL finding is open. `inconclusive` —
  an artifact was missing or unreadable, so coverage could not be computed; name
  which one. Those three words are `_predicates.Verdict`'s, used with its meanings,
  so a later gate can read this file through `blocks(verdict, "repo-declared")`
  without a fourth vocabulary being invented first. Nothing reads it today.
- **Status.** Exactly one of `Clear`, `Resolved`, `Deferred`, `Outstanding`, the
  same four `/speckit.clarify` writes.
- **Detail is a path, never a copy.** The full findings table, the coverage summary
  and the metrics stay in `analysis-report.md`; the scan file carries what was
  concluded, not a second copy that drifts.
- **An accepted finding says why it stands.** A finding fixed and a finding nobody
  acted on read identically as a row in a table, and the difference is the only
  thing a reviewer can disagree with.
- **A run that found nothing still writes the file**, with every pass listed and a
  findings section saying so in words a reader can dispute.
- Call it a **scan file**. "Receipt" names a manifest entry in this repo and
  "record" names an architecture record.

Then commit it and confirm a reviewer will actually reach it:

```bash
git add <root>/scans/<issue>-analyze.md
git commit -m "docs(scans): analysis scan for #<issue>"
wfctl arch check <root>/scans/<issue>-analyze.md
```

`arch check` refuses a file that is only staged, and says so — staging is not
committing, and `git push` moves commits. So the commit comes first; checking
before it would fail every time and teach nothing.
