---
status: proposed
---

# A pipeline step asks the record store which design records apply to it, never the feature's documents

## Context

Level-3 records are written during `/speckit.brainstorm` and land at
`<arch-root>/design/<issue>-<decision>.md`. `idea-refine` then lists them in
`design.md` under `## Software design decisions` — paths, never blocks (#121
item 5, shipped).

Nothing downstream reads that list. `speckit-plan`, `speckit-tasks` and
`speckit-implement` plan and build against a decision none of them has seen, and
`speckit-analyze` cannot say whether a task contradicts one. Connecting them
requires deciding where a step asks the question "which records apply to the work
I am doing?", and there are two candidate owners because the list already exists
in two places at once — as a section in `design.md`, and as the set of files
whose names begin with this feature's issue number.

The pressure is that the two disagree in reachable states. `design.md` is absent
for a feature that skipped brainstorm; `spec.md` — which is what `speckit-plan`
actually reads — carries no such section at all.

## Direct baseline

Leave authority with `design.md`: each of the four steps resolves `FEATURE_DIR`,
opens `design.md`, parses the `## Software design decisions` section, and reads
the paths it names. No new constant, no new convention — the section written by
item 5 becomes the index item 6 consumes.

## Decision

The record store owns it. Each downstream step resolves `wfctl arch-root`, reads
this feature's issue number from `wfctl status --json`, and globs
`<arch-root>/design/<issue>-*.md`. No step opens `design.md`, and no new section
is added to `spec.md` or `plan.md`.

`design.md`'s list stays exactly as item 5 wrote it. It is the human's index into
the one-pager, not the pipeline's.

## Owns truth

The record store owns "which design records apply to this feature's work?" — the
question is answered by the filenames under `<arch-root>/design/`, which encode
the issue the record was written for.

`design.md` cannot compute it, for three reasons that each hold alone:

```
   the question asked                design.md's answer
   ────────────────────────────      ─────────────────────────────────
   at plan time                      not read — speckit-plan/SKILL.md
                                     Outline step 2 loads FEATURE_SPEC
                                     and constitution.md, not design.md

   from a fresh checkout             resolves outside the working tree
                                     (FEATURE_DIR → ../wfctl-specs) and
                                     `specs/` is gitignored

   for a feature with no             absent — and records written by hand
   brainstorm pass                   are still records
```

`spec.md` cannot be made to carry it either, and that is a cost rather than an
impossibility: `required-sections-are-wfctls` makes the section list a constant
in `_predicates.py` checked against the shipped template, so a new section is a
constant, a template edit and a test — paid by every repo wfctl installs into, to
serve the minority of features that write any record at all.

## Considered

- **`design.md` owns the list, and the four steps read it** (the baseline) —
  equally coherent, and it reuses a section that already exists. It loses on the
  first row of the table above: `speckit-plan` does not read `design.md`, so
  adopting this means four steps newly depending on a gitignored file that
  resolves outside the repository. That dependency is the failure #121 exists to
  route around, reintroduced one step downstream of the fix.
- **`spec.md` carries a propagated list, written by `speckit-specify`** — sound,
  and it puts the answer where `speckit-plan` already looks. It loses on price:
  `required-sections-are-wfctls` means every repo's spec template grows a section
  that most features leave empty, to serve a case only some repos have.
- **A `wfctl design context` command that prints the applicable records** — the
  shape the level-2 records already use, and the one a fourth reader would find
  most discoverable. Ruled out by #121's own out-of-scope section, and for its
  stated reason: a command written against a record schema that has survived no
  real use is a migration waiting to be paid for.

## Consequences

The issue number becomes load-bearing in a filename. A record written under an
issue number other than the one `wfctl status` reports for the branch is
invisible to every downstream step, silently. The record template already says
records are "numbered for the issue being implemented, not its epic", so this
consequence gives that line a second reason to exist rather than adding a new
rule.

Cross-feature reference — a task in feature B that must respect a record written
for feature A — is not reached by the glob and is out of scope here. It has no
instance yet; the glob answers the question that does.

`_observe` in `cli.py:655` and the `record:` listing in `cli.py:450` exclude
`<arch-root>/scans/` and not `<arch-root>/design/`. The comment at `cli.py:648`
names this as a pre-existing open question and leaves it. This decision changes
its weight rather than its answer: making downstream consumption real is what
makes level-3 records routine on a branch, which is what turns `boundary` into a
constant-true observation — the #307 failure the comment cites, one directory
over. Tracked separately; not resolved here.

## Log

- 2026-09-10  proposed    — written at #121's level-2 gate while deciding how
  `speckit-plan`, `speckit-tasks`, `speckit-implement` and `speckit-analyze`
  reach the records item 5 already writes down.
