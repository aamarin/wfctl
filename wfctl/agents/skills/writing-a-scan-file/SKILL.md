---
name: 'writing-a-scan-file'
description: 'Write the scan file a review step leaves in the repository — what it covered, what it found, and that a run which found nothing looked. Use when /speckit.clarify or /speckit.analyze has finished its own workflow and its findings would otherwise land only in FEATURE_DIR, where no reviewer can reach them.'
---

# Writing a scan file

`/speckit.clarify` and `/speckit.analyze` are the two steps whose whole job is
finding problems, and both write everything they find into `FEATURE_DIR` — which
resolves outside the working tree in most repos and is gitignored in the rest. A
reviewer opening the change sees none of it, so a scan that found six problems
and one that never ran are the same pull request (#307).

This skill owns what both steps do about that. What it does not own is *what
either step scanned*: the categories, their meanings, and what each verdict means
for that step stay in the command wrapper that invoked this, because they are the
one part the two steps do not share.

The decision is `docs/architecture/the-scan-is-attested-where-the-reviewer-reads.md`.
Its shape is `docs/architecture/design/307-the-coverage-map-is-the-evidence.md`.

**Here rather than in `speckit-clarify/SKILL.md` or `speckit-analyze/SKILL.md`.**
Both are `github/spec-kit`-derived, and `vendor-upstream-skills` prefers a layer
over an edit: an in-place change is reverted by the next upstream pull with no
conflict to notice, and the behaviour then regresses at a moment whose diff
mentions neither step. A wfctl-owned skill is the layer — the same shape
`software-design-decisions` already has for its own write-commit-check
discipline.

## Where it goes

Ask, rather than writing the path in. A repo can declare `arch_root` anywhere,
and `docs/architecture` is the default rather than the truth:

```bash
wfctl arch-root      # prints the root; the file is <root>/scans/<issue>-<step>.md
```

`<step>` is `clarify` or `analyze`. `<issue>` is the tracker key `wfctl status`
prints, the same key `<root>/design/` and `<root>/declarations/` are named for.

`wfctl status` printing `#unknown` means the branch carries no issue key, and
there is no fallback: the file has no name, so write none and say so in one line
rather than inventing one. A scan file under a made-up key is worse than none —
it claims a change nobody can match it to.

**`arch-root` warning that the root is outside the working tree is the same
answer.** It exits 0 and prints the warning, so nothing downstream stops on its
own — but a file written there is one `git add` refuses and no reviewer reaches,
which is the state this whole skill exists to leave behind. Say so in one line and
write nothing. Do not fall back to a repository-local path: `arch_root` is the
single authority for where records live, and a second destination invented here
would put scan files somewhere the repo never declared.

**Create the directory before writing into it.** `wfctl arch-root` neither checks
that the root exists nor creates it — deliberately, since a repo has no records
until it writes its first one — and nothing seeds `scans/`. So the first scan in
any project writes into a parent that is not there:

```bash
mkdir -p <root>/scans
```

Cheap and unconditional, rather than a check: `mkdir -p` on an existing directory
is a no-op, and the run that needs it is the one where nobody is watching.

## The coverage table is the body

This is the whole point of the file, and the part an instruction most easily
loses. A findings list renders identically for a thorough scan over clean
artifacts and for a scan that generated nothing at all — which is the failure
this exists to expose. A coverage table does not: a run that never scanned has no
rows to write.

The wrapper that sent you here names the rows. Every one of them appears, with
the status the scan assigned it. A row you did not reach is `Deferred` with a
reason, never absent.

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

- **Verdict** — exactly one of `satisfied`, `unsatisfied`, `inconclusive`. Those
  are `_predicates.Verdict`'s three values, used with its meanings, so a later
  gate can read this file through `blocks(verdict, "repo-declared")` without a
  fourth vocabulary being invented first. Nothing reads it today. What each means
  for your step is in the wrapper that sent you here.
- **Status**, per coverage row — exactly one of `Clear`, `Resolved`, `Deferred`,
  `Outstanding`. A row carrying a measurement rather than a status is the
  wrapper's to declare, and it says so on the row.
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

Write it, then commit that path and nothing else:

```bash
mkdir -p <root>/scans
git add <root>/scans/<issue>-<step>.md
git commit -m "docs(scans): <step> scan for #<issue>" -- <root>/scans/<issue>-<step>.md
wfctl arch check <root>/scans/<issue>-<step>.md
```

The pathspec on `commit` is not the same instruction as the one on `add`. A bare
`git commit` writes the whole index, and both steps run mid-pipeline where an
author's staged code is entirely normal — so whatever is in the index rides along
in a commit whose subject says it holds a scan file. Naming the path makes git
commit that path and leave the rest staged where it was.

The commit comes before the check, and that order is load-bearing: `arch check`
refuses a file that is only staged, and says so — staging is not committing, and
`git push` moves commits. Checking first would fail on every run and teach the
reader that the check is broken rather than that the file is.

Exit 0 and a reviewer opening the change reads the scan beside the code, which is
the whole property. Exit 1 says which way it failed — outside this working tree,
never committed, or written to since its commit — and the file moves, or the
commit is repeated, before the step reports itself done.
