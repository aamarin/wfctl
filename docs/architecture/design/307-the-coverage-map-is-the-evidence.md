---
status: proposed
---

# The coverage map is the evidence; the findings list is its consequence

## Context

`the-scan-is-attested-where-the-reviewer-reads` decides that `clarify` and
`analyze` each write a file into the repository. It does not decide what that
file has to carry, and the obvious answer — the verdict and the findings — is
the one that cannot do the job the file exists for.

The pressure is the motivating symptom, not the artifact. Told to auto-choose,
an agent stops generating clarification questions at all. So *no findings* is the
output of a thorough scan over a clean spec and of a scan that never ran, and a
file carrying only findings renders identically in both. Moving that file into
the repository puts the same ambiguity in front of a reviewer instead of hiding
it from one.

What separates the two runs is not what was found. It is **how far the scan
reached** — and `speckit-clarify` already computes exactly that, on every run,
and throws it away.

## Verified

- `wfctl/agents/skills/speckit-clarify/SKILL.md` step 2: *"Produce an internal
  coverage map used for prioritization (do not output raw map unless no questions
  will be asked)"* — computed every run, surfaced only when nothing is asked.
- Same file, step 8: the completion report lists *"each taxonomy category with
  Status: Resolved … Deferred … Clear … Outstanding"* — to the console, and to no
  file.
- Same file, Behavior rules: a clean scan still writes `- No critical ambiguities
  detected.` into `## Clarifications`, because *"a clean scan that writes nothing
  is indistinguishable from never having run"*. The principle is already this
  repo's; the section it writes into is unreachable.
- `wfctl/agents/skills/speckit-analyze/SKILL.md` step 6 emits a findings table, a
  Coverage Summary Table and a Metrics block; step 6b writes the whole report to
  `{FEATURE_DIR}/checklists/analysis-report.md`.
- `_predicates.py:719` reads `^##[ \t]+Clarifications\b` out of `spec.md`;
  `_predicates.py:792` asks only whether `checklists/analysis-report.md` exists.
  Neither reads a coverage map, and neither is changed here.
- `_predicates.py:34-45` defines `Verdict` as `satisfied | unsatisfied |
  inconclusive` and `Source` as `repo-declared | accepted-record | human |
  ambient`; `blocks` at `:96` keys on `_PROMISED`.
- `cli.py:1233` — `arch check` takes a `Path` argument and resolves it, with no
  test that it sits under the arch root. It works on a scan file unchanged.
- `_arch.py:146` — `sorted(root.glob("*.md"))`, one level, so
  `<arch-root>/scans/` stays out of `wfctl arch context`.
- `wfctl/agents/commands/speckit.brainstorm.md` layers auto-approve behaviour
  over `brainstorming` and `idea-refine` without editing either, and says so.
  That is the wrapper-as-layer pattern `vendor-upstream-skills` asks for, already
  working in this tree.

## Assumed

- A reviewer opens a new file in the diff. This change does not strengthen that
  bet; `121-level3-records-in-pr` already rests on it, and both fail together.
- An agent instructed to fill a coverage table fills it from a spec it read,
  rather than fabricating rows. Falsified by a run producing ten `Clear` rows
  over a document it never opened — in which case the artifact is a lie rather
  than an absence, which is a different and worse failure. The remedy would be a
  check comparing the table's rows against a taxonomy constant wfctl owns, in the
  shape `required-sections-are-wfctls` already uses; this change does not build
  it, and the row count is chosen to make the fabrication tedious rather than
  impossible.
- `speckit-clarify`'s ten taxonomy categories are stable enough to be a
  table's rows. Falsified by an upstream pull that renames them; the cost is a
  scan file whose rows no longer match the skill's, which nothing would report.

## Direct baseline

The scan file carries the verdict, a pointer to the full artifact, and the list
of findings — the smallest document that answers *what did it find*, and one an
agent can write from what it already reports to the console.

```markdown
# Clarification scan — #307

- Verdict: satisfied
- Detail: <spec-root>/307-…/spec.md § Clarifications

## Findings

None.
```

Concretely: three lines and a heading, no new content computed, and the reviewer
learns the scan's outcome. What they cannot learn is whether there was a scan.
The document above is what a thorough pass over a clean spec produces and what
an agent that generated no questions produces, and they are the same bytes.

## Decision

The scan file's body is the coverage map — one row per taxonomy category, with
the status the scan assigned it — and the findings are reported beneath it as
what that coverage turned up.

A run that found nothing renders a full table and an empty findings section. A
run that never scanned has no rows to write.

```markdown
# Clarification scan — #307

## Session 2026-09-09

- Verdict: satisfied
- Scanned: spec.md
- Asked: 0 · Answered: 0 · Outstanding: 0
- Detail: <spec-root>/307-…/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Clear |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

No question met the bar. Every category above was read and found Clear.
```

The `## Session` heading arrived after this record was first written, from running
the step rather than reading it: a re-scan of a spec whose questions were already
answered would, under a write-it-whole rule, have deleted the session that
answered them. A second run on a date already present extends that section rather
than opening another.

The verdict is `satisfied` when the scan ran and nothing is outstanding,
`unsatisfied` when a category is left Outstanding or a high-impact one Deferred,
and `inconclusive` when the scan could not run — no `spec.md`, or one still
carrying its template. Those are `_predicates.Verdict`'s three values, used with
their meanings, so a later gate reads this file through `blocks(verdict,
"repo-declared")` rather than through a fourth vocabulary. This change writes no
such gate.

## Diagram

```
              baseline                              decision

stable        ┌──────────────┐                      ┌──────────────┐
              │  scan file   │                      │  scan file   │
              └──────────────┘                      └──────────────┘
                     ▲                                ▲          ▲
                     │ writes                  writes │          │ writes
══════════════ arch-root ═════════════════════════════╪══════════╪═════════
                     │                                │          │
volatile      ┌──────┴───────┐                 ┌──────┴───┐  ┌───┴─────────┐
              │   findings   │                 │ findings │  │coverage map │
              └──────────────┘                 └──────────┘  └─────────────┘
                     ▲                                ▲          ▲
                     │ produces                       │ produces │ produces
              ┌──────┴───────────────┐         ┌──────┴──────────┴─────────┐
              │     clarify scan     │         │       clarify scan        │
              └──────────────────────┘         └───────────────────────────┘
                     │ produces
                     ▼
              ┌──────────────┐
              │ coverage map │   discarded — never crosses
              └──────────────┘
```

Both graphs hold the same three things the scan produces. They differ by one
arrow: whether the coverage map crosses the arch-root boundary. That arrow is the
whole decision, because it is the only one of the three whose absence a reviewer
can see.

## Considered

- **Verdict and findings only**, per *Direct baseline* — the smallest file that
  answers the question the issue's title asks, and it cannot answer the question
  the issue's body asks.
- **The verdict alone, as a one-line receipt** — cheapest of all, and it is the
  baseline's defect concentrated: `satisfied` is what both runs write.
- **Copying the full `FEATURE_DIR` artifact into the repository** — no second
  computation, and the reviewer gets everything. It is a second copy of a
  document the pipeline reads, so the two drift and the predicates keep reading
  the one the reviewer does not; `design-levels` names the digest-that-drifts
  failure and this is its inverse, the original that drifts from its copy.
- **A machine-readable body — JSON, or counts in frontmatter** — better for the
  gate #100 may later write, worse for the reader who exists today, and premature
  while nothing consumes it. A markdown table is what renders in a diff.
- **Recording the taxonomy in wfctl and generating the rows** — the shape
  `required-sections-are-wfctls` uses, and it would close the fabrication hole in
  *Assumed*. It moves a list out of an upstream-derived skill into wfctl's
  constants, which is a boundary this record has no mandate to draw; filed as the
  answer if a fabricated table is ever observed.

## Consequences

An agent writing this file does work it currently discards rather than new work:
the coverage map exists at step 2 of the clarify skill and the coverage summary
is already in its step-8 report.

A wrong-but-complete table is now the cheapest way to fake a scan, where before
the cheapest way was an empty section. That is a worse artifact and a better
signal — ten fabricated rows are a claim a reviewer can disagree with, and an
absent section was nothing to disagree with.

Both steps' files are written by their command wrappers, not by the derived
`SKILL.md` files, so `vendor-upstream-skills`' *"prefer layering to editing"*
holds and an upstream pull cannot revert the behaviour silently.

## Verification

- `/speckit.clarify` on a spec with a real ambiguity: the scan file names it, the
  category's row reads `Resolved` or `Outstanding`, and the verdict is
  `unsatisfied` where anything is left open.
- `/speckit.clarify` on a spec with nothing ambiguous: the file carries every
  taxonomy row, the findings section says the scan asked nothing, and the verdict
  is `satisfied`. This is the case the suite cannot see and the one #307 was
  filed over.
- `wfctl arch check docs/architecture/scans/<issue>-clarify.md` exits 0 once the
  file is committed and exits 1 while it is only written.
- `wfctl arch context` is unchanged by the presence of `scans/`.

## Log

- 2026-09-09  proposed  — #307. The findings list cannot distinguish the two runs
  it has to distinguish; the coverage map already could and was being thrown away.
