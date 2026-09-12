# Data model — level3 downstream (#326)

Nothing here is new. This feature introduces no entity, no field and no file
format; it makes four steps read three shapes that already exist on disk. The
model is written down anyway because the pass that consumes them has to agree
about their boundaries, and two of the three have a corner that has already
caused a defect.

## The record list

**What it is**: the set of level-3 records applicable to one feature's work.

**Where it lives**: `## Software design decisions` in that feature's `design.md`,
under the directory `wfctl feature-paths` reports as `FEATURE_DIR`. Written by
`idea-refine` at the moment the records were written, per #121 item 5.

**Shape**:

```markdown
## Software design decisions

- <path to a level-3 record> — <the decision in one line>
- <path to a level-3 record> — <the decision in one line>

<free prose: which levels were answered with no record, and anything else>
```

**Parse rule (FR-002a)**: an entry is a list item of the form
`- <path> — <text>`. Prose contributes no paths.

The rule exists because the section legitimately carries both. The
`/speckit.brainstorm` wrapper requires a level answered with no record to say so
in one line rather than delete the section, and this feature's own `design.md`
also names its **level-2** record in that prose. Taking every path in the section
would load a level-2 record as a level-3 one — a level-2 decision read at level 3
binds nothing while looking like it does, which is the failure
`software-design-decisions` names in its own Escalation section.

**Four states**, and they are different truths rather than four spellings of
absence:

| State | Meaning | What the step reports |
| --- | --- | --- |
| N entries | the design pass recorded N decisions | the N paths |
| section present, no entries | the design pass recorded no decision | `none` |
| a `design.md` with no such section | the pass predates the section | `unknown` |
| no `design.md` | no design pass ran | `unknown` |

The third row was the second in the first version of this model, and a reviewer
counted the tree: 19 of 27 `design.md` files under this repo's spec root have no
such heading. Reading it as `none` asserts "the design pass recorded no decision"
about a pass that predates the section — for most existing features, on the first
run. `/speckit.brainstorm` supplies the ruling: the section stays even when a
level was answered with no record, because "a missing section reads as a level
nobody ran", which is `unknown`.

## The design record

**What it is**: one level-3 structural decision. Durable, tracked, in the branch
diff, never binding on another feature.

**Where it lives**: `<arch-root>/design/<issue>-<decision>.md`, where `arch-root`
is what `wfctl arch-root` prints. The filename without `.md` is the slug other
records cite in `supersedes`.

**Fields this feature reads**:

| Field | Source | Used for |
| --- | --- | --- |
| `status` | frontmatter | the severity split, FR-006 and FR-007 |
| `Decision` | body section | the contradiction comparison, FR-005 |
| `Consequences` | body section | the contradiction comparison, FR-005 |
| the path itself | the list entry | the step's report, FR-003 |

**`status` lifecycle**, from the template, with what each means to pass G:

```
proposed ──► approved ──► superseded
    │                 └──► rejected
    │
    └── a task reversing it
        approved                   → CRITICAL    (FR-006)
        proposed                   → HIGH        (FR-006)
        superseded or rejected     → no finding  (FR-007)
        absent or unrecognised     → HIGH, status reported unreadable
```

Only a human moves a record past `proposed`. Every record in this repository is
`proposed` today, which is why FR-006 splits severity rather than gating on
`approved`.

**Fields this feature does not read**: `pattern`, `supersedes`, `Context`,
`Verified`, `Assumed`, `Verification` and `Log` — none of them binds a task.

**Three it must never compare against**: `Direct baseline`, `Considered`, and the
baseline half of `Diagram`. Those describe what was *rejected*, so a task
implementing the shape that won reads as contradicting them, and every correctly
implemented record becomes a finding. That is why the comparison names two
sections rather than taking the whole record: past `Decision` and `Consequences`,
more text is not more signal.

## The scan file's coverage table

**What it is**: the artifact that makes a thorough analyze run distinguishable
from a skipped one, per #307.

**Where it lives**: `<arch-root>/scans/<issue>-analyze.md`, one
`## Session YYYY-MM-DD` section per session, appended and never replaced.

**What this feature adds**: one row, and its position is part of the shape
because the last row is the only one carrying a measurement rather than a status.

```
| A · Duplication                 | <status> |
| B · Ambiguity                   | <status> |
| C · Underspecification          | <status> |
| D · Constitution alignment      | <status> |
| E · Coverage gaps               | <status> |
| F · Inconsistency               | <status> |
| G · Design-record contradiction | <status> |   ← added
| Requirement-to-task coverage    | N%       |
```

**Row values for G** are the same four statuses every other row carries —
`Clear`, `Resolved`, `Deferred`, `Outstanding` — with the count in a
parenthetical: `Clear (2 records read)`, `Outstanding (1 CRITICAL)`,
`Clear (design.md lists none)`, `Deferred (no design.md)`,
`Deferred (no records section)`.

The first version put bare counts in that cell, which three reviewers caught at
once: `writing-a-scan-file` fixes the vocabulary at those four, and this same
wrapper says the coverage-percentage row is the only one carrying anything else.
Both sentences were false at the same time.

The two `Deferred` rows are the states where the pass could not run, and they
stay distinct from `Clear (design.md lists none)` where it ran and found nothing
— which is the difference this file exists to carry.

The row is written on every run, including runs that read no records. That is
what makes it a coverage row rather than a findings line: a findings list renders
identically for a thorough scan over clean artifacts and for a scan that never
ran.
