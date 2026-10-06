---
description: Review the feature's plan.md against its spec and design records before tasks, or revise plan.md against the BLOCKER findings the last review left open, and record each review in a committed scan file.
allowed-tools: Read Glob Write Edit Bash(wfctl status*) Bash(wfctl feature-paths*) Bash(wfctl arch-root*) Bash(wfctl arch check*) Bash(git hash-object*) Bash(git diff --no-index*) Bash(cp*) Bash(mkdir*) Bash(date -u*) Bash(git add*) Bash(git commit*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

This command runs in one of two modes, and section 1 chooses which:

1. A **review** reads the plan with the `plan-review` method and writes three
   things: the report, a byte copy of the plan it read, and one section of the
   scan file.
2. A **revision** edits `plan.md` against the BLOCKER findings the last review
   left open, and writes nothing else.

The method lives in the `plan-review` skill and names no pipeline. Everything
below is what this pipeline adds to it: which mode a run is in, where the files
go, and the scan file. The split is `plan-review-boundaries`.

**Finish section 1 before reading anything else.** Do not open the skill, even
alongside this file, until section 1 has chosen the review mode. A revise run
never reads it.

## 1. Which run this is

Run `wfctl feature-paths` and read `REPO_ROOT` and `FEATURE_DIR` from its
output. Do not build the feature directory from the branch name, since it can
resolve outside the working tree.

Run `wfctl status --json`. Take the entry in `steps` whose `name` is `plan`, then
the entry in its `sub_steps` whose `name` is `plan-review`, and read that entry's
`state` and `annotation`. Choose the mode from this table:

| The pass reads | Mode |
| --- | --- |
| `in_progress`, annotation `N BLOCKER findings open`, and every checked input row matches its file now | revise |
| `in_progress`, annotation `N BLOCKER findings open`, and a checked input row does not match its file now | review |
| `in_progress` with no annotation, or with `no review recorded`, `the review records no plan.md identity`, `stale; plan.md changed since the review`, or `the review records no BLOCKER count` | review |
| `done` | review of the same plan, which the method runs as a re-review when the plan copy matches and in full otherwise |
| `skipped`, `pending`, or no `plan-review` entry at all | review |

`no review recorded` means `tasks.md` was written before any review of the
plan, and the review runs as for any other `in_progress` reading. A feature
planned before this pass existed reads the same way. For one of those, a person
can decide the review is not wanted and run `wfctl step none plan.plan-review
--reason "…"` instead; that is their call to make, so say the option and do not
take it.

Only the first row revises. A person runs this command on a `done` pass to have
the plan reviewed again, most often after `spec.md` changed, and on a `pending`
one only by hand, since the pipeline names `/plan-review` only once `plan` has
run. Neither is a reason to write nothing. A `pending` run most often finds
`spec.md` or `plan.md` missing, and section 5 says what it writes then.

### The input check, before revising

A BLOCKER whose cause sits in `spec.md` or a design record is fixed there, and
`plan.md` stays as the review read it, so the pass still reads its BLOCKER
count. Without this check, the person who fixed that input and ran this command
to have the fix reviewed would get an agent edit to `plan.md` instead.

So on the first two rows, read `FEATURE_DIR/plan-review.md` and its
`## Reviewed inputs` table before choosing. The checked rows are every row except
three:

1. `plan.md`. The pass has already compared it, and it matches, or the pass
   would read stale.
2. `plan-review.plan.md`. A re-review records the copy it read as its base and
   then overwrites the copy with the plan it read, so this row never matches
   after a re-review.
3. `plan-review.md`. A report records no row for itself, and a row naming the
   file it sits in can never match. Skip one if an older report carries it.

For each checked row, run `git hash-object --no-filters <path>` with the path in
its first cell resolved against `FEATURE_DIR`, and, when that exits non-zero
because no file is there, resolved against `REPO_ROOT`. A non-zero exit at both
is how a gone or still-absent file shows itself, not an error. The row does not
match when any of these is true:

1. The hash differs from the row's second cell.
2. The row recorded an identity, and the file is now gone.
3. The second cell says `absent`, and the file now exists.
4. The second cell is neither 40 lowercase hex characters nor `absent`.

One row that does not match means review. Carry the paths of the inputs that did
not match into the review, which names them in its review scope, re-reads each
one in full, and reviews the whole of `plan.md` against it, since the plan diff
may be empty.

A check that misfires only ever chooses review, and a review costs one more run
where a revision was due. The check needs no grant beyond `git hash-object`, and
runs the same way attended or not.

## 2. The method, for the review mode only

Read `.agents/skills/plan-review/SKILL.md` (or `../skills/plan-review/SKILL.md`
relative to this file, if `.agents/skills` isn't present) for the complete
review method, and follow it with the names and paths sections 4 and 5 give.

A revise run does not read the skill. The method never edits what it reviews,
never iterates until its findings clear, and never hands control on, and a
revision does all three. Keeping the revision out of the method is what keeps
those three rules true.

## 3. The revise mode

Reached only when section 1 chose it.

1. Read `FEATURE_DIR/plan-review.md`, and take each finding under `## Findings`
   whose priority is BLOCKER and whose status is `open`.
2. Edit `FEATURE_DIR/plan.md` so that each such finding's evidence no longer
   holds, following its suggested response where it gives one.
3. Edit `plan.md` and nothing else. Reading an input a finding cites, such as
   the requirement in `spec.md`, is fine. Leave the report, the plan copy, the scan
   file, `spec.md`, `design.md`, the design records, and every other planning
   artifact exactly as they are.
4. Do not run `setup-plan.sh`, and do not run `/speckit.plan`. `setup-plan.sh`
   copies the plan template over `plan.md`, which deletes the plan this run is
   revising.
5. A finding whose cause is outside `plan.md`, such as a requirement in
   `spec.md` that contradicts a design record, is one this run cannot fix. Leave
   it, and say which finding it is, where its fix belongs, and that a person
   fixes it there and runs `/plan-review` again, which then reviews because an
   input changed.
6. Do not review the edit. The pass now reads stale, and the next run reviews it
   with the method, in a fresh context where the host allows one (section 6).
7. Go to section 8.

A revise run that could not change `plan.md` at all still hands back. The pass
then reads the same BLOCKER count, and the pipeline's stall count is what stops
a run that repeats a pass which changes nothing.

Nothing checks that a revise run left the report alone. The rule is prose, and
a revise run that rewrote the report would change the report's hash, which the
review cap counts as a review.

## 4. What this pipeline names that the method does not

The method names no pipeline, so the review run supplies these to it:

1. The review sits after `plan` and before `tasks`, and runs late when tasks
   were written without it. `analyze` runs later, over
   `tasks.md`, and checks consistency across the three artifacts. This review
   does not do that job, and `analyze` does not do this one.
2. `spec.md` marks an unresolved question with `[NEEDS CLARIFICATION`. A marker
   still standing is a finding in the `Missing Information` category, graded by
   what it blocks like any other finding.
3. The constitution lives at `.specify/memory/constitution.md` under
   `REPO_ROOT`. When it is not there, the report records the row
   `| .specify/memory/constitution.md | absent | constitution |`, and the review
   goes on. A missing constitution does not make the review inconclusive.
4. The design records are the ones `design.md` lists. Resolve them with
   `.agents/skills/reading-design-records/SKILL.md` (or
   `../skills/reading-design-records/SKILL.md` relative to this file, if
   `.agents/skills` isn't present).
5. The inputs section 1 found changed, when it found any.

## 5. Where the review writes

1. The report is `FEATURE_DIR/plan-review.md`, replaced whole on every review.
   The method reads the earlier one first, since a re-review starts from it.
2. The plan copy is `FEATURE_DIR/plan-review.plan.md`. Make it with
   `cp "FEATURE_DIR/plan.md" "FEATURE_DIR/plan-review.plan.md"`, with the real
   directory in place of `FEATURE_DIR`, and never by reading `plan.md` and
   writing it back out, which does not reliably reproduce CRLF line endings,
   trailing whitespace, or a long file byte for byte. Copy only after the method
   has finished reading the earlier copy as its base.
3. After copying, run `git hash-object --no-filters` on the copy and check that
   it equals the identity the report records for `plan.md`. On a mismatch, copy
   once more. If the second copy also differs, add a line to the report's
   `## Review scope` saying that the plan copy does not match the plan the
   review read, and leave the copy in place. The next run treats a copy whose
   identity differs from the report's `plan.md` row as missing, and reviews in
   full.
4. A re-review diffs the copy against the plan with
   `git diff --no-index "FEATURE_DIR/plan-review.plan.md" "FEATURE_DIR/plan.md"`.
   It exits 1 when the files differ, and that is the diff, not an error.
5. When `spec.md` or `plan.md` is missing, the review cannot run. The method
   still writes its report for a review that could not run, and this command
   makes no plan copy. Write the scan file section with the verdict
   `inconclusive`, naming the missing input, commit it, and stop. This is the
   one exit that does not hand back.

## 6. Independence

Where the host can start a reviewer with a fresh context, such as a subagent,
run the review in one. Give it sections 2, 4, and 5 of this file and the inputs
section 1 found changed, have it write the report and the plan copy, and write
the scan file here from the report it leaves.

This matters most after a revise run, when the conversation now reviewing has
just written the changes the review is about to judge. Where the host cannot
start one, run the review here.

## 7. Write the scan file

Follow `.agents/skills/writing-a-scan-file/SKILL.md` (or
`../skills/writing-a-scan-file/SKILL.md` relative to this file, if
`.agents/skills` isn't present). It owns the destination, the commit, and the
check. What it does not own is what this pass reviewed, which is below.

**The scan file is written on every exit path of the review mode, including a
run that stops because `spec.md` or `plan.md` is missing.** A review that could
not run and a review nobody started must not look the same to the pull request
reviewer. A revise run writes no section, since it reviewed nothing.

**File**: `<arch-root>/scans/<issue>-plan-review.md`, with `<issue>` the `issue`
field of `wfctl status --json`.
**Detail**: `FEATURE_DIR/plan-review.md`.

**One section per run, headed `## Review <UTC timestamp>`.** Take the timestamp
from `date -u +%Y-%m-%dT%H:%MZ`. This overrides `writing-a-scan-file`'s rule that
a second run on the same day extends that day's section. Each review binds a
different plan identity, and two runs merged under one heading would put two
identities, and possibly two verdicts, under one section. Append the new section
at the end of the file, and never edit or remove an earlier `## Review` or
`## Sign-off` section. When the file is new, start it with
`# Plan review scan for #<issue>`.

**Coverage rows**, every one on every run, in this order:

```
Deterministic checks
Requirements and traceability
Architecture and boundaries
Adversarial implementation and verification
Security and reliability
```

A row with any finding still open is `Outstanding`, and one whose findings are
all fixed is `Resolved`. The rubric's other lenses report under these rows:
verification and risk under `Adversarial implementation and verification`,
dependency and scope under `Architecture and boundaries`. The first four always
ran on a review that ran. `Security and reliability` is
`Deferred` with its reason when the lens did not apply. On a review that could
not run, every row is `Deferred (spec.md missing)` or `Deferred (plan.md
missing)`.

**Verdict, for this pass**: `unsatisfied` while any BLOCKER finding is open.
`inconclusive` when `spec.md` or `plan.md` is missing. `satisfied` otherwise,
however many MAJOR and MINOR findings are open.

The verdict reads open BLOCKER findings and nothing else. The skill grades every
finding with one of the three priorities the rule above names, and the two lists
are held together by a test, so a new priority added to one of them fails there.

**A finding carries no rejected alternatives.** A review reaches a finding from
evidence rather than by choosing among options, so there is no option set to
report. An open finding says why it stands, which is its evidence, and a fixed
one says what fixed it.

**Section shape**:

```markdown
## Review 2026-09-28T14:02Z

- Verdict: unsatisfied
- Reviewed: plan.md 9f2c1e0d4b6a8c2e1f3a5b7d9e0c2a4f6b8d0e1c, spec.md 3b7e0a9c1d5f2e8a4c6b0d2f9e1a3c5b7d9f0e2a, .specify/memory/constitution.md absent
- Review type: re-review
- Open: BLOCKER 1 · MAJOR 2 · MINOR 5 · Fixed since the earlier review: 1
- Detail: <FEATURE_DIR>/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Outstanding (PR-003) |
| Architecture and boundaries | Clear |
| Adversarial implementation and verification | Resolved (PR-001 fixed) |
| Security and reliability | Deferred (no trust boundary is touched) |

### Findings

- **PR-003, BLOCKER, open.** `spec.md §FR-009` requires X, and `plan.md §Reader`
  does Y. Stands because the plan has no state for Z.
- **PR-001, BLOCKER, fixed.** Fixed by `plan.md §Reader`, which now lists Z.
```

`Reviewed` lists every row of the report's `## Reviewed inputs`, identity and
all, with the plan copy's row, which only a re-review records, marked `(base)`,
since the copy on disk has since been replaced. `Fixed since the earlier review`
counts the findings this run marked `fixed` that the earlier report carried as
`open`. `Detail` carries the real feature directory, not the placeholder. On a
review that could not run, `Review type` is `not run (<input> missing)`, `Open`
is `no count; the review did not run`, and the findings line names the missing
input. On a full review, `Review type` gives the method's reason, such as
`full (no plan copy from the earlier review)`. A run that found nothing still
writes every coverage row and a findings line saying so, such as "No finding;
every check and lens above ran and found nothing to report."

Commit and check exactly as `writing-a-scan-file` says, with the subject
`docs(scans): plan review for #<issue>`.

## 8. Hand back

Invoke `speckit-orchestrate` once the scan file section is committed, or, in the
revise mode, once `plan.md` is edited. Whether the pipeline stops before `tasks`
is the payload's answer, not this command's.

## What this command does not say

It never says the plan is approved, rejected, or ready to implement, and it
never decides whether `tasks` may run. It does not restate the lenses, the
priority definitions, or the report's shape, which are the method's.
