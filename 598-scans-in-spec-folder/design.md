# Scan files live in the spec folder

Contexts: evidence-and-derivation, design-method, architecture-records

Mode: `auto_approve` is on for this branch. Every gate below is answered into
this file or into a record, and the user approves at the PR.

## Problem Statement

Clarify, plan review, and analyze save their scan files in the feature's spec
folder, next to the `spec.md`, `plan.md`, and `tasks.md` they review. The code
repository no longer commits them, and wfctl reads each scan itself, so a
skipped scan still stops the pipeline.

## Background

A scan file records what a review step checked and what it found. Since #307,
each one is committed to the code repository at
`<arch-root>/scans/<issue>-<step>.md`, while the files it reviews stay in the
spec folder. In pfms, that means a PR changing one file of code also carries
three scan commits.

The record that put them there, `the-scan-is-attested-where-the-reviewer-reads`,
made one argument the issue doesn't answer. An agent told to choose answers
itself stops generating clarification questions, so a thorough scan and a
skipped one both leave an empty clarify result. The committed scan was how a PR
reviewer told them apart. Once scans leave the PR, something else has to find a
skipped scan.

## Level 1: behavior

What the user sees in `wfctl status`, one state at a time. Each string is true
in its state.

Clarify ran and wrote its scan file to `FEATURE_DIR/scans/clarify.md`:

```
clarify      ●
```

Clarify wrote `## Clarifications` into `spec.md` but no scan file. This is the
skipped scan the old record worried about, and the step stays current:

```
clarify      ▶  no scan file  ← current
next: /speckit.clarify (auto)
```

The text is a display, not a blocking reason, so the step stays automatic and
an unattended run goes back to clarify. Plan review already holds this way.

The scan file exists but has no `Verdict` line, or its coverage table has no
row with a status:

```
clarify      ▶  scan file has no verdict  ← current
clarify      ▶  scan file has no coverage rows  ← current
```

A feature planned before this change, with clarify's scan committed under the
arch root and `plan.md` already written. The step doesn't send the feature back,
and says why it passed:

```
clarify      ●  no scan file
                run /speckit.clarify
```

Analyze and plan review read the same way, with `scans/analyze.md` and
`scans/plan-review.md`. For analyze, the later artifact that lets an older
feature pass is `delivery.md`, with the fix line `run /speckit.analyze`. For
plan review, it is `tasks.md`, with `run /plan-review`.

Plan review sign-off, before and after:

```
before:  ✓ Signed off plan.md 1a2b3c4 — "typo"
           Written to docs/architecture/scans/598-plan-review.md
           Commit it: git commit -m "docs(scans): sign off plan.md for #598" -- docs/…
after:   ✓ Signed off plan.md 1a2b3c4 — "typo"
           Written to <FEATURE_DIR>/scans/plan-review.md
```

The "Commit it" line goes away, and so does the refusal when the branch doesn't
change the file. `wfctl store specs` saves the file with the rest of the folder.

The PR used to show the sign-off section, which was the only place a person
read an agent's sign-off. Its reason now goes in the PR body, and
`wfctl check-body` reports one the body leaves out, as it does for a design
exception's reason.

A spike's evaluation scan is unchanged. It stays at
`<arch-root>/scans/<issue>-evaluation.md`, committed, and checked with
`wfctl arch check`.

Level-3 consequences of level 1:

1. The clarify, analyze, and plan review readers in `_evidence.py` each read a
   scan file, so they need one shared check for its shape.
2. The check has to tell a missing file from a file with no verdict and from a
   file with no coverage rows, since each has its own reason string.
3. Each reader needs a later artifact that marks a feature as planned before
   this change, so in-flight features aren't sent back.
4. The sign-off needs the spec folder's scan path and no git check.

## Level 2: architecture

The record is
`docs/architecture/scans-live-in-spec-folder.md`. It supersedes
`the-scan-is-attested-where-the-reviewer-reads`.

```
agent (wrapper)               │  spec folder           │  wfctl
──────────────────────────────┼────────────────────────┼──────────────────────────
clarify / plan review /       │                        │
analyze                       │                        │
  writes scans/<step>.md ─────┼─► scans/<step>.md      │
                              │                        │
status, resume, orchestrate   │                        │
                              │   scans/<step>.md ─ ─ ─┼─► step reader checks
                              │                        │   Verdict + coverage rows
                              │   (missing) ─ ─ ─ ─ ─ ─┼─► step stays current
                              │                        │
store specs                   │   folder saved ────────┼─► spec store
                              │                        │
  "the scan ran" ─────────────┼────────────────────────┼──✗ never taken as evidence
```

Who finds a skipped scan, compared:

| Option | Finds it when | Why it wins or loses |
|---|---|---|
| The step reader in `_evidence.py` reads the scan file | before the next step starts | Wins. Every route to the next command (`status`, `resume`, `speckit-orchestrate`) reads it, so an unattended run is sent back to the step it skipped before planning or code builds on it. |
| The worktree guard reads the scan files before `gh pr create`, the way it reads review notes | when the PR opens | Loses. It finds the gap after implement has built on an unscanned spec, and the guard can't import `_evidence` (`arch/_records.py` says so of `RULED_ON`), so the shape check would be written twice. |
| Keep the scans in the PR | when a person reads the diff | Loses. This is what the issue removes, for the user's reason: the PR reviewer is judging the code. |
| Paste the scan into the PR body | when a person reads the body | Loses for the reason the old record gave. Nothing can check a PR body. |
| Nothing replaces it | never | Loses. It drops the old record's argument instead of answering it. |

The step reader checks shape, not the verdict. Whether an `unsatisfied` verdict
should hold the step is a gate on what a scan found, and #100 owns that
question.

Open questions from the issue:

1. **Evaluation scans stay in the code repository.** The user's reason for
   moving scans is that they review the spec, plan, and tasks, which the PR
   doesn't carry. An evaluation reviews no spec. Its result is the branch's
   deliverable, so the PR reviewer is its reader, and a spike may have no spec
   folder.
2. **Committed scans stay as history.** wfctl has 117 under
   `docs/architecture/scans/`, and pfms has its own. Moving them means one
   commit per feature on `specs-trunk` and a change to pfms, and nothing reads
   them. `scans/` stays on `non_record_subtrees`, since committed scans and new
   evaluation scans are still there.

## Level 3: design

| Checked | Assumed |
|---|---|
| Nothing in wfctl reads a scan file's contents today. Only `wfctl arch check` and the sign-off's `touched_on_this_branch` read its location (grep of `wfctl/`). | |
| `Evidence` carries `spec_dir` and no issue key, so a file name with the issue in it needs a new field (`_evidence.py:231`). | |
| A reason on a `done` reading is a warning that holds nothing (`Assessment` docstring, `_evidence.py:70`). | |
| The guard doesn't read pipeline state (`_guard.py`, `_hook.py` import neither `_pipeline` nor `_evidence`). | |
| `wfctl store specs` saves the whole spec folder, so `scans/` goes with it. | Verified when the scan is walked through the new path. |
| Every scan's coverage statuses begin with `Clear`, `Resolved`, `Deferred`, or `Outstanding` (sample: `445-clarify.md`, `445-plan-review.md`). | Analyze has one measurement row; the check needs only one status row, so it passes. |

Structural choices:

1. **File name `scans/<step>.md`, not `scans/<issue>-<step>.md`.** The spec
   folder already names the issue, and `Evidence` has no issue key. The issue
   left the name to the design.
2. **One helper, `scan_reason(spec_dir, step)`, beside the three readers.** It
   returns `None` or the reason string. The three readers call it after their
   own artifact check.
3. **The sign-off keeps its event as the thing that reads the pass done.** It
   writes the scan section to the spec folder and drops the git check, since
   the check's reason was that a PR reviewer had to see the section.

None of these weighed a credible alternative that needs a record. The name
follows from `Evidence`, the helper is the shape the readers already use, and
the sign-off keeps its mechanism. The branch claims the software-design pass
for each context.

## Software design decisions

No level-3 record. Each context carries a `brainstorm.software-design` claim
saying why.

## MVP Scope

1. `writing-a-scan-file` and the three wrappers write to
   `FEATURE_DIR/scans/<step>.md`, with no commit and no `wfctl arch check`.
   Evaluation keeps its old path and steps.
2. The clarify, analyze, and plan review readers hold the step on a missing or
   malformed scan, and warn on an older feature.
3. `wfctl step sign-off plan.plan-review` writes to the spec folder, and
   `wfctl check-body` reports a sign-off reason missing from the PR body.
4. AGENTS.md, the replaced record, and tests follow.

## Not Doing

1. Gating on the verdict. #100 owns that.
2. Moving committed scans.
3. Checking every coverage row a wrapper names.
