---
status: proposed
---

# `design.md` owns which design records apply to a feature's work; a filename convention cannot

## Context

Level-3 records are written during `/speckit.brainstorm` and land at
`<arch-root>/design/<issue>-<decision>.md`. `idea-refine` then lists them in
`design.md` under `## Software design decisions` — paths, never blocks (#121
item 5, shipped).

Nothing downstream reads that list. `speckit-plan`, `speckit-tasks` and
`speckit-implement` plan and build against a decision none of them has seen, and
`speckit-analyze` cannot say whether a task contradicts one. Connecting them
means deciding where a step asks "which records apply to the work I am doing?",
and the list already exists in two places — as a section in `design.md`, and as
the set of files whose names begin with an issue number.

The pressure is that the two disagree, and the disagreement is silent.

## Direct baseline

Derive the set from the filesystem: resolve `wfctl arch-root`, read the branch's
issue from `wfctl status --json`, glob `<arch-root>/design/<issue>-*.md`. No new
mechanism, no new section, and the naming convention the record template already
mandates does the work.

## Decision

`design.md` owns it. Each downstream step resolves `FEATURE_DIR` via
`wfctl feature-paths`, reads `design.md`, and takes the paths listed under
`## Software design decisions`. No step derives the set from a filename.

## Owns truth

`design.md` owns "which design records apply to this feature's work?" — the
question is answered by the paths `idea-refine` wrote there at the moment the
records were written, by the pass that wrote them.

The filesystem cannot compute it, because the issue number in a record's
filename and the issue number derivable from the branch are answers to different
questions. The record template says a record is "numbered for the issue being
implemented, not its epic"; a worktree is named for the issue that existed when
it was created; and a child issue is filed *during* the brainstorm pass, after
the worktree exists. Each rule is right and they do not compose.

Observed on this branch, which is the first one the baseline was tried on:

```
   branch            121-level3-downstream    →  status reports issue "121"
   record written    design/326-contradiction-is-a-seventh-pass.md

   glob design/121-*.md
     matches         design/121-visibility-is-asked-of-git.md   ← #122's, months old
     misses          design/326-contradiction-is-a-seventh-pass.md
```

Stale record loaded, current record missed, no error either way.

## Considered

- **The filesystem owns it, via an issue-prefixed glob** (the baseline) — the
  first version of this record chose it, and evidence reversed it within the
  session. It was chosen on an argument that does not survive inspection: that
  `design.md` is gitignored and resolves outside the working tree, so downstream
  steps should not depend on it. That property is about the **reviewer**, who
  reads the PR and never opens `design.md`. The consumers here are pipeline
  steps running locally, where `FEATURE_DIR` resolves and the file is present.
  The reviewer still needs the records themselves, and those are in the diff
  either way — which is what `wfctl arch check` already enforces per record.
- **Ask git what this branch added under `design/`** —
  `_paths.records_on_this_branch` already answers exactly this, independently of
  any naming convention, and it is the same machinery `wfctl arch check` uses.
  Genuinely sound, and it loses on reach rather than on correctness: a skill can
  only get at it through a new `wfctl` verb, which is `wfctl design context`
  under another name and out of scope in #121, or through a raw git line, which
  `software-design-decisions` warns against by name after four near-misses were
  each wrong in their own direction.
- **Keep the glob and renumber records to the branch's issue** — makes the
  baseline correct, and pays for it by contradicting the record template's
  explicit rule. It also loses the property the rule exists for: a record filed
  under an epic tells the next reader nothing about which piece of work made the
  decision.

## Consequences

Gained: correct by construction. The list is written by the pass that wrote the
records, at the moment it wrote them, so it cannot drift from them and cannot be
confused by a numbering coincidence.

Harder: `speckit-plan` gains a read it did not have. Its Outline step 2 loads
`FEATURE_SPEC` and the constitution; `design.md` becomes a third input, reached
through `wfctl feature-paths` rather than assumed at `specs/<branch>/`.

The failure mode this introduces: a feature whose `design.md` is absent, or
predates the section, gets no records. The first case is close to degenerate —
records are written by the brainstorm pass that also writes `design.md` — but the
second is the *majority* state, and this record first said otherwise. A reviewer
counted it: 19 of the 27 `design.md` files under this repo's spec root carry no
`## Software design decisions` heading at all. So the rendering that distinguishes
"recorded nothing" from "nothing is known" is not a nicety for a rare path; it is
what most existing features will hit on the first run.

`## Software design decisions` becomes load-bearing rather than documentary. The
`/speckit.brainstorm` wrapper already requires it and already says a level
answered with no record says so in one line rather than deleting the section,
because "a missing section reads as a level nobody ran" — which is also the
ruling that decides a missing section is `unknown` and not `none`. That rule now
has a second reason to exist and a consumer that depends on it.

`_observe` in `cli.py` and the `record:` listing beside it exclude
`<arch-root>/scans/` and not `<arch-root>/design/`. The comment above the first
names this as a pre-existing open question and leaves it. This decision changes
its weight rather than its answer: making downstream consumption real is what
makes level-3 records routine on a branch, which turns `boundary` into a
constant-true observation — the #307 failure that comment cites, one directory
over. Tracked as **#327**, not resolved here: the two call sites want opposite
answers, and `touched_on_this_branch` takes one `exclude` subtree.

That last paragraph was written into this record, lost when the record was
rewritten during the reversal below, and restored when a reviewer found that
`grep -rn 327` over the tree returned nothing. Its only other home was `spec.md`,
which resolves outside the working tree — so a deferral this change is
responsible for had become invisible to precisely the reader it was written for,
which is the defect this whole epic exists to prevent.

## Log

- 2026-09-10  proposed    — written at #121's level-2 gate while deciding how
  `speckit-plan`, `speckit-tasks`, `speckit-implement` and `speckit-analyze`
  reach the records item 5 already writes down.
- 2026-09-10  revised     — the first version chose the issue-prefixed glob and
  was falsified at the `/speckit.specify` step of the same session, on this
  branch, by the mismatch drawn above. Revised in place rather than superseded:
  nobody had ratified the first version, and a supersession chain for a decision
  that stood for one session is a changelog entry rather than a record. The
  rejected argument is kept in `Considered`, where it now belongs.
