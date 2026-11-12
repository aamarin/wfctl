---
name: 'writing-a-scan-file'
description: 'Write the scan file a review step leaves beside the files it reviewed — what it covered, what it found, and that a run which found nothing looked. Use when /speckit.clarify, /plan-review or /speckit.analyze has finished its own workflow, since wfctl holds the step until the scan is in the spec folder. Use when a branch that ran no pipeline step produced a finding a reviewer must see — an evaluation, a spike, an experiment whose result is the deliverable.'
---

# Writing a scan file

`/speckit.clarify`, `/plan-review` and `/speckit.analyze` are the steps whose
whole job is finding problems. A run told to choose its own answers can finish
any of them having asked nothing, and its own artifact then looks the same as a
thorough run's. The scan file is what tells them apart: a run that never scanned
has no coverage rows to write.

This skill owns what the steps share about that. What it does not own is *what
each step scanned*: the categories, their meanings, and what each verdict means
for that step stay in the command wrapper that invoked this, because they are the
one part the steps do not share.

The decision is `docs/architecture/scans-live-in-spec-folder.md`. Its shape is
`docs/architecture/design/307-the-coverage-map-is-the-evidence.md`.

**Here rather than in `speckit-clarify/SKILL.md` or `speckit-analyze/SKILL.md`.**
Both are `github/spec-kit`-derived, and `vendor-upstream-skills` prefers a layer
over an edit: an in-place change is reverted by the next upstream pull with no
conflict to notice, and the behaviour then regresses at a moment whose diff
mentions neither step.

## Where it goes

A pipeline step writes its scan into the feature's spec folder, beside the
`spec.md`, `plan.md` and `tasks.md` it reviewed. Ask for the folder rather than
building it from the branch name, since it can resolve outside the working tree:

```bash
wfctl feature-paths      # prints FEATURE_DIR; the file is FEATURE_DIR/scans/<step>.md
mkdir -p "FEATURE_DIR/scans"
```

`<step>` is `clarify`, `plan-review` or `analyze`. The folder already names the
issue, so the file name doesn't. Substitute the real directory for `FEATURE_DIR`.

**Don't commit it, and don't run `wfctl arch check` on it.** The scan reviews
files the pull request doesn't carry, so it isn't evidence about the code, and
the spec folder doesn't have to be a Git repository. `wfctl store specs` saves it
with the rest of the folder, and wfctl reads it in place of the PR reviewer: the
step stays current in `wfctl status`, and an unattended run goes back to it,
until the file is there in the shape below.

**`evaluation` is the kind with no step behind it, and it still goes in the
code repository.** A spike, an experiment, or a tool evaluation runs no pipeline
step. Its result is the branch's deliverable, so the PR reviewer is the scan's
reader, and the branch may have no spec folder. The section *An evaluation scan*
below says where it goes and how it is committed. Everything else in this skill
applies to it unchanged except the two things a wrapper would have supplied, and
both are called out where they arise: the coverage rows, and how many rejected
alternatives a finding carries. An evaluation names its own, before it starts,
and says in its opening that it did.

## The coverage table is the body

This is the whole point of the file, and the part an instruction most easily
loses. A findings list renders identically for a thorough scan over clean
artifacts and for a scan that generated nothing at all — which is the failure
this exists to expose. A coverage table does not: a run that never scanned has no
rows to write.

The wrapper that sent you here names the rows. Every one of them appears, with
the status the scan assigned it. A row you did not reach is `Deferred` with a
reason, never absent.

**An `evaluation` has no wrapper, so it names its own rows — before it runs, not
after.** Rows written afterwards are a list of what happened, which is the
findings list again and carries none of the information a coverage table exists
to carry. The passes an evaluation did not reach are the ones a reader most needs
named, and they only exist as rows if they were named while they were still
expected.

## One section per session, appended

The file carries a `## Session YYYY-MM-DD` heading per scan session, and a re-run
**never discards an earlier session**: a second scan finding nothing is only
meaningful given what the first one found, and replacing the file deletes the
evidence it exists to carry.

**A second run on a date already present extends that section rather than opening
a new one.** The sessions a reviewer distinguishes are separated by the pipeline
advancing, not by the clock, and `/speckit.clarify` already merges same-day runs
into one `### Session YYYY-MM-DD` in `spec.md` — a second convention here would
make the two documents disagree about what a session is.

What is never merged is two *steps* into one file. Each step owns its own, and
neither ever edits the other's.

## What every section carries

- **Verdict** — exactly one of `satisfied`, `unsatisfied`, `inconclusive`, on a
  line written exactly `- Verdict: <value>`. Those are `_evidence.Verdict`'s three
  values, used with its meanings. wfctl matches that line form to see that a
  scan ran, and never reads the value to decide the step, so an `unsatisfied`
  scan still lets the step finish. What each value means for your step is in
  the wrapper that sent you here.
- **Status**, per coverage row — a table row whose last cell starts with exactly
  one of `Clear`, `Resolved`, `Deferred`, `Outstanding`. wfctl needs at least one
  such row to see that a scan ran. A row carrying a measurement rather than a
  status is the wrapper's to declare, and it says so on the row.
- **Detail** — the path of the full artifact in `FEATURE_DIR`, never a copy of
  it. The pipeline reads that artifact; a second copy here is the one that drifts.
- **Findings** — what was found, and for each, the alternative the answer was
  decided against. A finding you did not act on says why it stands: a finding
  fixed and a finding nobody touched read identically as a row in a table, and the
  difference is the only thing a reviewer can disagree with. **How many
  alternatives that is belongs to the wrapper that sent you here**, for the same
  reason the coverage rows do: `clarify` decides each finding by picking one of a
  set of options it generated, and every option it did not pick lost for a reason
  a reader would ask about, while `analyze` reaches a finding without an option
  set to discard. One line here would understate the first step or invent a
  requirement for the second.
- **A run that found nothing still writes the section**, with every row read and a
  findings line saying so in words a reader can dispute — "no question met the
  bar; every category above was read and found Clear." An empty section is nothing
  to disagree with, which is the state this file replaces.

Call it a **scan file**. "Receipt" names a manifest entry in this repo
(`136-the-receipt-is-a-sibling-of-merged`) and "record" names an architecture
record.

## Ask whether the file is really there

```bash
wfctl status
```

The step's line no longer reads `no scan file`, `scan file has no verdict`, or
`scan file has no coverage rows`. Any of the three means the file is missing,
has no `- Verdict:` line, or has no coverage row with a status, and the step
stays current until it is fixed. That is the check, so a step that skips this
file is sent back to write it.

## An evaluation scan

An evaluation is read by the PR reviewer, so it is the one scan that still goes
in the code repository. Ask for the root rather than writing the path in, since
a repo can declare `arch_root` anywhere:

```bash
wfctl arch-root      # prints the root; the file is <root>/scans/<issue>-evaluation.md
```

`<issue>` is the tracker key `wfctl status` prints. `#unknown` means the branch
carries no issue key, and there is no fallback: the file has no name, so write
none and say so in one line rather than inventing one. A scan file under a
made-up key claims a change nobody can match it to.

`arch-root` warning that the root is outside the working tree is the same
answer. It exits 0 and prints the warning, but a file written there is one
`git add` refuses and no reviewer reaches. Say so in one line and write nothing.
Don't fall back to a repository-local path, since `arch_root` is the single
authority for where records live.

Write it, then commit that path and nothing else, then check it:

```bash
mkdir -p <root>/scans
git add <root>/scans/<issue>-evaluation.md
git commit -m "docs(scans): evaluation for #<issue>" -- <root>/scans/<issue>-evaluation.md
wfctl arch check <root>/scans/<issue>-evaluation.md
```

`mkdir -p` comes first because nothing seeds `scans/`, and the run that needs it
is the one where nobody is watching. The pathspec on `commit` keeps whatever else
is staged out of a commit whose subject says it holds a scan file. The commit
comes before the check, because `arch check` refuses a file that is only staged.

Exit 0 means a reviewer opening the change reads the scan beside the code. Exit
1 says which way it failed: outside this working tree, never committed, or
written to since its commit. Move the file or repeat the commit before reporting
the evaluation done.
