---
disable-model-invocation: true
description: Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec.
handoffs:
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
allowed-tools: Read Glob Write Bash(.specify/scripts/bash/check-prerequisites.sh*) Bash(wfctl status*) Bash(wfctl arch-root*) Bash(wfctl arch check*) Bash(git add*) Bash(git commit*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-clarify/SKILL.md` (or `../skills/speckit-clarify/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete clarification workflow.

## Write the scan file

The workflow above writes everything it finds into `FEATURE_DIR`, which resolves
outside the working tree in most repos and is gitignored in the rest. A reviewer
opening the change sees none of it, so a thorough scan and one that asked nothing
are the same pull request. Write a second file, into the repository, that says
what this scan reached.

Here rather than in `speckit-clarify/SKILL.md`: that skill is `github/spec-kit`
derived, and `vendor-upstream-skills` prefers a layer over an edit — an in-place
change is reverted by the next upstream pull with no conflict to notice. The
decision is `docs/architecture/the-scan-is-attested-where-the-reviewer-reads.md`;
its shape is `docs/architecture/design/307-the-coverage-map-is-the-evidence.md`.

Ask for the destination rather than writing it in — a repo can declare `arch_root`
anywhere, and `docs/architecture` is the default, not the truth:

```bash
wfctl arch-root      # prints the root; the file is <root>/scans/<issue>-clarify.md
```

`<issue>` is the tracker key `wfctl status` prints, the same key
`<root>/design/` and `<root>/declarations/` are named for.

**The coverage table is the body, and that is the whole point of the file.** A
findings list renders identically for a thorough scan over a clean spec and for a
scan that generated no questions at all — which is the failure this exists to
expose. A coverage table does not: a run that never scanned has no rows to write.
The map is already computed at step 2 of the workflow above and discarded unless
nothing is asked.

One file per step, and **one section per scan session, appended** — the same
`### Session YYYY-MM-DD` shape the workflow above already writes into `spec.md`,
so it is a discipline the step keeps rather than a new one. A re-run never
discards an earlier session: a second scan finding nothing is only meaningful
given what the first one found, and replacing the file would delete the evidence
this file exists to carry. What is not appended across is *steps* — `analyze`
writes its own file and never edits this one.

```markdown
# Clarification scan — #<issue>

## Session YYYY-MM-DD

- Verdict: satisfied | unsatisfied | inconclusive
- Scanned: spec.md
- Asked: N · Answered: N · Outstanding: N · Deferred: N
- Detail: <FEATURE_DIR>/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| … one row per taxonomy category above, ten in all |

### Findings

- **<category>** — what was ambiguous.
  Q: <the question> → A: <the answer>. Decided against <the alternative>: <why>.

### Deferred

- **<category>** — <what was not asked, and why it belongs to a later step>.
```

- **Verdict.** `satisfied` — the scan ran and nothing material is open.
  `unsatisfied` — a category is Outstanding, or a high-impact one is Deferred.
  `inconclusive` — the scan could not run: no `spec.md`, or one still carrying its
  template. Those three words are `_predicates.Verdict`'s, used with its meanings,
  so a later gate can read this file through `blocks(verdict, "repo-declared")`
  without a fourth vocabulary being invented first. Nothing reads it today.
- **Status.** Exactly one of `Clear`, `Resolved`, `Deferred`, `Outstanding` — the
  reporting vocabulary of step 8's coverage summary, not the Clear / Partial /
  Missing the scan uses internally. A reader wants what the scan concluded.
- **Detail is a path, never a copy.** The integrated clarifications live in
  `spec.md` and the pipeline reads them there; a second copy here is the one that
  drifts.
- **A run that found nothing still writes the file**, with every category read and
  a findings section saying so in words a reader can disagree with — "no question
  met the bar; every category above was read and found Clear." An empty section is
  nothing to disagree with, which is the state this file replaces.
- Call it a **scan file**. "Receipt" names a manifest entry in this repo and
  "record" names an architecture record.

Then commit it and confirm a reviewer will actually reach it:

```bash
git add <root>/scans/<issue>-clarify.md
git commit -m "docs(scans): clarification scan for #<issue>"
wfctl arch check <root>/scans/<issue>-clarify.md
```

`arch check` refuses a file that is only staged, and says so — staging is not
committing, and `git push` moves commits. So the commit comes first; checking
before it would fail every time and teach nothing.
