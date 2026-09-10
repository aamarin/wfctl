---
status: proposed
---

# Contradiction detection is a seventh pass inside analyze, not a check outside it

## Context

#326 requires `speckit-analyze` to report a task that contradicts a level-3
design record. The comparison is between two pieces of prose: a record's
`Decision` section, written in the present tense during brainstorm, and a task
line in `tasks.md`, written by `speckit-tasks` days later.

The pressure is that "contradicts" has no mechanical form. A record saying *the
summary strategy is chosen at the call site, not injected* and a task saying
*inject a SummaryStrategy into the renderer* disagree, and no comparison of
strings, paths or symbols finds it. Any check that runs outside the model has to
be given a machine-readable claim to compare against, which the record does not
carry and would have to be invented for.

`a-rule-is-expressed-as-a-check` asks the question that settles this, and asks it
of the rule rather than the tooling: is a violation of it visible in an artifact
the work already produces? Here the artifacts exist — the record and `tasks.md`
are both on disk — and the violation is visible in them only to a reader.

## Verified

- `wfctl/agents/commands/speckit.analyze.md:52` lists six detection passes,
  `A · Duplication` through `F · Inconsistency`, and step 4 of the skill runs
  them over `spec.md`, `plan.md` and `tasks.md` in one read.
- `wfctl/agents/commands/speckit.analyze.md:41` — the scan file is
  `<arch-root>/scans/<issue>-analyze.md`, and its coverage table already carries
  one row per pass plus `| Requirement-to-task coverage | N% |`.
- All seven records under `docs/architecture/design/` carry `status: proposed`.
  `head -4 docs/architecture/design/*.md` returns `status: proposed` seven times
  and `approved` zero times.
- `wfctl/agents/skills/software-design-decisions/design-record-template.md:16`
  — "`status` runs proposed -> approved -> superseded | rejected. Only a human
  moves it past proposed."
- `wfctl/_arch.py` contains no reference to `design`; `load_records` reads
  `root.glob("*.md")`, non-recursive, so nothing in `wfctl` parses a level-3
  record today.
- `wfctl/agents/commands/speckit.analyze.md:24` states the override to the
  skill's read-only rule out loud — the precedent for adding an instruction in a
  wrapper rather than in the spec-kit-derived skill.

## Assumed

- That a model reliably detects a prose contradiction between a `Decision`
  section and a task description. Falsified by running `/speckit.analyze` against
  a task deliberately written to reverse an approved record and getting a clean
  verdict. This is the bet the whole decision rests on, and #326's definition of
  done tests exactly it.
- That the record's `Decision` section is where a contradiction is detectable.
  Falsified by a record whose binding content lives in `Consequences` or
  `Diagram` and whose `Decision` reads as a summary — in which case the pass has
  to take the whole record, not one section.

## Direct baseline

Add pass `G · Design-record contradiction` to the list of detection passes in
`speckit.analyze.md`, with the record set as an input alongside `spec.md`,
`plan.md` and `tasks.md`. One row in the coverage table, one severity rule. No
new file, no new command, no new field on the record.

## Decision

The baseline. Contradiction detection is a seventh pass beside the six that
already exist, reading the record set as one more input to the same read.

Severity is taken from the record's frontmatter `status`: contradicting an
`approved` record is CRITICAL, contradicting a `proposed` one is a warning. The
pass emits its coverage row on every run, including the run that found no
records.

## Diagram

The two graphs share the same components. The divider is the one
`downstream-asks-the-record-store` already drew and is not new here.

```
              baseline                          strongest alternative

stable   ┌──────────────────┐              ┌──────────────────┐
         │ design/<issue>-  │              │ design/<issue>-  │
         │   *.md  record   │              │   *.md  record   │
         └──────────────────┘              │  + invariant:    │
                    ▲                      └──────────────────┘
                    │ reads                          ▲
                    │                                │ parses
═══ the record store owns which ════════════╪════════╪══════════════
    records apply (level 2)                          │
                    │                                │
volatile  ┌─────────┴────────┐            ┌──────────┴───────┐
          │ analyze — passes │            │ wfctl design     │
          │   A B C D E F G  │            │   check-tasks    │
          └──────────────────┘            └──────────────────┘
                    │ reads                          │ reads
                    ▼                                ▼
             ┌────────────┐                   ┌────────────┐
             │ tasks.md   │                   │ tasks.md   │
             └────────────┘                   └────────────┘
```

The two differ by where the judgment happens and what the record must carry to
support it. On the left the record stays prose and the judgment is the model's,
made in the same read that already answers six other questions. On the right the
judgment moves into `wfctl`, which buys a verdict that is reproducible and does
not vary between runs — and pays for it with a field on every record whose
vocabulary nobody has yet had to write one of, and a second reader of a schema
`_arch.py` does not parse today.

## Considered

- **A `wfctl design check-tasks` command comparing declared invariants** (the
  right-hand graph) — genuinely better on the axis a check is usually judged on:
  same input, same verdict, every time, and it would put the rule where
  `a-rule-is-expressed-as-a-check` prefers rules to live. It loses on the
  question that record actually asks. The violation is not visible in an
  artifact the work already produces; making it visible means inventing an
  `invariant:` vocabulary and writing it into seven existing records before the
  first one has been contradicted. #121's out-of-scope section refuses the
  command for the same reason one level up.
- **A standalone pass run separately from analyze's six** — sound, and it would
  keep the record set out of a read that is already large. It loses on fit: the
  scan file exists so that a thorough analysis and a skipped one are
  distinguishable in the PR, and a seventh pass reported outside that table is
  the one whose absence nobody notices.
- **Gating the pass on `approved` only** — the literal reading of #121 item 6.
  Rejected on evidence rather than on principle: zero of seven records are
  approved, and an unattended run approves none, so the pass would ship correct
  and dead.
- **Strategy, for the severity split** — one comparison with two outcomes, read
  from a frontmatter field. Named and rejected: a second caller would be the
  reason to have one, and there is no second caller.

## Consequences

Gained: the pass costs one row in a table a reader already reads, and the record
format is unchanged — the seven records that exist are inputs to it today,
without migration.

Harder: the verdict is a model's judgment, so two runs over the same tasks can
disagree. The scan file is what makes that visible rather than acceptable — a run
that reports `Clear` is on record as having looked, and a reader comparing two
sessions can see the disagreement.

The failure mode this introduces: a pass that reports `Clear` because it did not
understand the record, which is indistinguishable in the coverage table from one
that read it and found nothing. That is the same shape as the risk the six
existing passes already carry, and it is the reason the row names the records it
read rather than only its status.

## Verification

- `/speckit.analyze` on a feature whose `tasks.md` contains a task deliberately
  reversing an `approved` record reports a CRITICAL finding naming that record.
  The same task against a `proposed` record reports a warning.
- `/speckit.analyze` on a feature with no records under `<arch-root>/design/`
  emits the pass G row saying so, rather than omitting the row.
- The scan file written by that run carries pass G between `F · Inconsistency`
  and the coverage percentage.

## Log

- 2026-09-10  proposed  — written at #326's level-3 gate, deciding whether
  contradiction detection is a model pass or a command, while the alternative
  was still being argued rather than after the wrapper was edited.
