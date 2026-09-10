# Scan files — clarify and analyze report where the reviewer reads

## Problem Statement

How might we make a thorough clarification or analysis run distinguishable from
a skipped one, for the person opening the pull request?

`clarify` and `analyze` are the two steps whose whole job is to find problems.
Both write what they find into `FEATURE_DIR`, which resolves outside the working
tree in this repo and is gitignored under the default `<repo>/specs`. Neither
reaches the change under review, so the reviewer cannot check either step's work
and cannot tell whether it happened.

## Recommended Direction

Each of the two steps writes one file per change into the repository, at
`<arch-root>/scans/<issue>-<step>.md`, committed on the branch. The
`FEATURE_DIR` artifacts stay exactly as they are, and so do the predicates that
read them: the repository gets the attestation, the spec store keeps the detail.

The file's body is the **coverage map** — one row per category the scan
examined, with the status it assigned. The findings are reported beneath it.
This is the part that does the work, and it comes from reading the skill rather
than from the issue: a findings list renders identically for a thorough scan over
a clean spec and for a scan that generated no questions at all, which is the
motivating symptom. A coverage table does not. `speckit-clarify` already computes
that map on every run (step 2) and discards it unless nothing is asked.

Both files are written by the **command wrappers**, not by the derived
`SKILL.md` files. `speckit-clarify` and `speckit-analyze` are `github/spec-kit`
derivatives and `vendor-upstream-skills` says to prefer layering to editing;
`speckit.brainstorm.md` is the worked example of a wrapper layering behaviour
over a derived skill in this tree.

## Behavior — what the reviewer sees

Three reachable states, each read as the literal file a reviewer meets in the
diff.

**A scan that found something.**

```markdown
# Clarification scan — #307

- Verdict: unsatisfied
- Scanned: spec.md
- Asked: 3 · Answered: 3 · Outstanding: 1
- Detail: <spec-root>/307-clarify-findings-in-repo/spec.md § Clarifications

## Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Clear |
| … |
| Non-Functional Quality Attributes | Outstanding |

## Findings

- Q: Does the receipt replace the FEATURE_DIR artifact? → A: No — it sits beside it
- Outstanding: no latency or size bound stated for the scan file. Deferred to plan.
```

True in that state: something was asked, something is still open, and the
reviewer can see which category is open without opening anything else.

**A scan that found nothing — the state this exists for.**

```markdown
# Clarification scan — #307

- Verdict: satisfied
- Scanned: spec.md
- Asked: 0 · Answered: 0 · Outstanding: 0
- Detail: <spec-root>/307-clarify-findings-in-repo/spec.md § Clarifications

## Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| … ten rows, every one read |

## Findings

No question met the bar. Every category above was read and found Clear.
```

True in that state: it says it looked, and it says what it looked at. The
sentence "no question met the bar" is a claim about ten rows the reader can
disagree with.

**A scan that never ran.**

```markdown
# Clarification scan — #307

- Verdict: satisfied
- Asked: 0

## Findings

None.
```

False in that state, and visibly so — the file claims a verdict over a coverage
table it does not have. This is the state the whole design is chosen against, and
the reason the coverage map is the body rather than a footnote.

**Level-3 consequence generated here:** the verdict line cannot be the file's
only load-bearing content, because `satisfied` is what states two and three both
write. The coverage table has to be structurally required, which is what
`307-the-coverage-map-is-the-evidence` decides.

`analyze` renders the same three states over its own categories — the six
detection passes it already runs (duplication, ambiguity, underspecification,
constitution alignment, coverage gaps, inconsistency) plus its requirement-to-task
coverage percentage.

## Boundaries and Ownership

**The repository owns "was this change scanned, and what did the scan cover?"**
The spec store cannot: `spec_root` resolves outside the working tree and
`<repo>/specs` is gitignored, so nothing it holds is part of the change under
review, and an agent's own report that the scan ran is unfalsifiable.

**The spec store keeps "what exactly did the scan say?"** — the integrated
clarifications in `spec.md`, the full findings table in
`checklists/analysis-report.md`. The repository takes no second copy. These are
two facts and not one fact with two homes, in the same way `vendor-upstream-skills`
holds an attribution line and its table row to be two facts.

**`blocks` keeps "what does it mean that this evidence is unavailable?"** The
scan file states its verdict in `_predicates.Verdict`'s own three values so a
later gate reads it through `blocks(verdict, "repo-declared")`. This change
writes no such gate — that is #100's call.

```
spec store (FEATURE_DIR, gitignored)   │  repository (the PR diff)
───────────────────────────────────────┼─────────────────────────────────────
clarify runs                           │
  spec.md § Clarifications         ────┼─►  scans/<issue>-clarify.md
  (pipeline sentinel: _predicates      │    (coverage map + verdict + findings)
   reads the heading, nothing under it)│
                                       │
analyze runs                           │
  checklists/analysis-report.md    ────┼─►  scans/<issue>-analyze.md
  (pipeline sentinel: existence only)  │
                                       │
reviewer opens the PR                  │
  (no path to any of it)               │    reads both files in the diff
                                       │
  "the scan ran"  ─────────────────────┼──✗ never inferred from the left
```

## Checked

- `speckit-clarify` step 2 computes a taxonomy coverage map every run and emits
  it only when no question will be asked.
- `speckit-clarify`'s Behavior rules already argue this issue's principle for the
  section it writes into `spec.md`: *"a clean scan that writes nothing is
  indistinguishable from never having run"*.
- `_predicates.py:719` reads `^##[ \t]+Clarifications\b` from `spec.md`;
  `_predicates.py:792` asks only whether `checklists/analysis-report.md` exists.
  Neither is touched by this change.
- `cli.py:1233` — `wfctl arch check` takes an arbitrary path and never tests that
  it is under the arch root, so the visibility check works on a scan file with no
  new wfctl code.
- `_arch.py:146` — `load_records` globs `<root>/*.md` one level, so
  `<arch-root>/scans/` stays out of `wfctl arch context`. `wfctl arch none`'s own
  help states this as the reason declarations live in a subdirectory.
- `_predicates.py:520` — `design_block` returns `None` once `spec.md` exists, and
  both steps run after `specify`, so a scan file under the arch root can never
  spuriously answer the boundary question.
- `_predicates.py:34-45,96` — `Verdict`, `Source`, `_PROMISED` and `blocks` exist
  and are the vocabulary to reuse.
- `wfctl/agents/commands/speckit.brainstorm.md` layers behaviour over two derived
  skills without editing either.

## Assumed

- A reviewer opens a new file in the diff. `121-level3-records-in-pr` already
  rests on this; both fail together and this change does not strengthen it.
- An agent told to fill a coverage table fills it from a document it read.
  Falsified by ten fabricated `Clear` rows, which is a lie rather than an
  absence — a worse artifact and a better signal, and the remedy would be a
  wfctl-owned taxonomy constant, not built here.
- `speckit-clarify`'s ten categories are stable enough to be a table's rows.
  Falsified by an upstream rename, which nothing would report today.

## Software design decisions

- `docs/architecture/the-scan-is-attested-where-the-reviewer-reads.md` — the
  repository owns the attestation, the spec store keeps the detail (level 2).
- `docs/architecture/design/307-the-coverage-map-is-the-evidence.md` — the scan
  file's body is the coverage map, not the findings list (level 3).

## Questions answered without asking

Run under `auto_approve`, so each was decided from the repository rather than put
to a person. Each answer carries what it was decided from.

- **Does the scan file replace the `FEATURE_DIR` artifact or sit beside it?**
  Beside it. `_predicates.clarify` and `_predicates.analyze` read those two paths
  as the pipeline's sentinels; replacing either changes what the steps prove,
  which is #100's contract and `240-flip-decompose`'s file.
- **One file per step, or one per change with a section each?** One per step.
  A shared file needs a rule that analyze replaces its own section rather than
  appending, nothing can check that rule, and an agent following prose is the
  reader that gets merge rules wrong.
- **Under the arch root, or a new tree beside it?** Under the arch root.
  `arch_root` is overridable and `arch check` resolves any path, so a
  subdirectory moves with a repo that relocates its records while a second
  top-level tree would stay behind and the skills would name both.
- **Does this change any step's review flag?** No. Both stay
  `_REVIEW_REQUIRED`. Flipping one because it now has a visible artifact would
  answer #100 by side effect.

## MVP Scope

**In:** the `scans/` destination; the file format for both steps; the writing
instruction in `speckit.clarify.md` and `speckit.analyze.md`; tests that the two
wrappers ship and carry the instruction; `AGENTS.md` and the architecture records.

**Out:** any predicate change, any `_STEPS` change, any gate that refuses a step
for a missing or `unsatisfied` scan file, and any wfctl-side generation or
validation of the table's rows.

## Not Doing (and Why)

- **Building the extension-hook executor** (`hooks.after_clarify`,
  `.specify/extensions.yml`) — recorded as considered and rejected on #307 and
  #204: nothing in `wfctl/` parses that file, and an `after_clarify` hook would
  write into the same invisible column. It changes how the note is written, not
  where it lands.
- **Making `clarify` or `analyze` automatic** — the payoff this enables and not
  this change's to take. Both wait on #100's evidence contract.
- **Committing `specs/`** — reverses `spec_root` resolving outside the tree and
  the `specs-trunk` orphan branch, for a problem two files solve.
- **Editing the derived `SKILL.md` files** — `vendor-upstream-skills` prefers
  layering, and an in-place edit is reverted by the next upstream pull with no
  conflict to notice.
- **A machine-readable body** — better for a gate that does not exist yet, worse
  for the reviewer who does.

## Open Questions

- Should `analyze`'s scan file carry its full findings table or a count plus the
  CRITICAL rows? The full table is up to 50 rows and the report it duplicates is
  the pipeline's sentinel. Settle at `/speckit.plan`.
- #286 asks whether clarify's *rejected options* belong in an extended bullet or
  a file of their own. This design answers the destination — the scan file's
  Findings section, where a rejected option is what the answer was decided
  against — and leaves the content question to #286.
