# Phase 0 Research — record leads with drawing

**Feature**: `109-record-leads-with-drawing` | **Date**: 2026-09-16

Every unknown the Technical Context marked NEEDS CLARIFICATION, resolved. Three
of them were resolved by measurement over this repository's own corpus rather
than by argument, and the measurements are reproduced here because one of them
falsifies an assumption a level-3 record was written on.

---

## R-001 — Where the declared kind lives, and what reads it

**Decision**: a `diagram:` key in the record's frontmatter, carrying one of
`data-flow`, `component`, `state`. `parse_record` lifts it onto `Record.diagram`
the way it already lifts `status` and `supersedes`. Absent parses to `""`.

**Rationale**: settled at level 2 by `the-author-declares-the-diagram-kind`, and
the code confirms the cost that record claimed. `_frontmatter` already returns
the whole block as a dict (`wfctl/_arch.py:92`), and `parse_record` already
selects two keys off it (`wfctl/_arch.py:114`). A third key is one line in the
constructor and no new parsing.

An unrecognised value parses to `""` *and* produces a finding, which is where
`diagram` differs from `status`. `status` may silently become `""` because an
unrecognised status excludes the record from the projection — a safe direction.
An unrecognised `diagram` has no safe direction: dropping it silently means a
record declaring `dataflow` is refused at accept with "declares no kind", which
is a true sentence about a file whose author wrote the key. FR-003 is that
difference.

**Alternatives considered**: a `## Data flow` / `## Component` / `## State`
heading in place of `## Boundary` plus a key — rejected at level 2, and the
narrow reason holds up in the code: `_log_bounds` and `_unfenced` are written
against one literal heading each, so a variable heading means the scanner learns
three names and every reader has to agree about all three.

---

## R-002 — How `acceptable` and `accept` share the drawing rule

**Decision**: one exported function, `accept_blockers(record) -> list[str]`,
returning every reason acceptance would refuse, in reading order.
`acceptable(record)` becomes `record.status == "proposed" and not
accept_blockers(record)`. `accept` raises when the list is non-empty. The CLI
calls `accept_blockers` itself to choose its wording.

**Rationale**: `acceptable`'s own docstring already names the failure a second
copy produces — "a listing built from status alone names a record whose own
suggested command then fails". FR-007 is that sentence as a requirement, and a
drawing check written twice reintroduces it one release later.

The split between module and console follows the shape already in this file.
`_set_status` raises for a missing `## Log` and `accept`'s docstring says why the
guard lives there — "that guard is the invariant, every caller gets it" — while
the CLI picks the sentence, because "three statuses need three different
sentences and only the console knows what they are". Blockers are the same
division: the module owns *whether*, the console owns *how it reads*.

Strings rather than an enum, because the console prints them and there is one
console. A `Finding`-like type would be a second vocabulary for the same facts
and neither caller needs to branch on which blocker fired.

**Alternatives considered**:

- **`accept` raises a new exception type carrying the blockers** — the CLI already
  catches `ValueError` from `_set_status` and rewrites its path
  (`wfctl/cli.py:1632`). A second exception type means two catch arms for one
  refusal path, and the wording still cannot live in the module.
- **`acceptable` gains an `explain` flag returning either a bool or a list** — a
  function with two return types for one question, which is what the list form
  already collapses: emptiness *is* the bool.

---

## R-003 — Reading one section out of a record

**Decision**: generalise `_log_bounds` into `_section_bounds(lines, heading)`,
with `_log_bounds` becoming a call to it. A new `_drawing(record) -> str`
returns the text inside the first fenced block in the `## Boundary` section, or
`""`.

**Rationale**: `_log_bounds` is already the section scanner; only its heading is
hard-coded. Both of the reasons its docstring gives for its shape apply
unchanged to `## Boundary`: fenced examples must be skipped (a record
documenting the record format carries a fenced `## Boundary`), and the section
ends at the next `## ` rather than at end of file.

`_drawing` needs fence *interiors*, which `_unfenced` deliberately does not
yield. `_md.walk_lines` already reports `inside` and `fence` per line
(`wfctl/_md.py:57`), so the interior is the complement of what `_unfenced`
selects — the same walk, the opposite predicate, and no second definition of
what opens a fence.

**Alternatives considered**: a regex over the whole body for
`## Boundary\n+```...```` — rejected for the reason `_unfenced` exists. A record
that quotes a `## Boundary` example inside a fence is matched by the regex and
not by the walk, and `contracts/record-format.md` is exactly such a document.

---

## R-004 — What the label-agreement check compares (measured)

**Decision**: a **node label** is reported when **none of its content words
appears anywhere else in the record**. A node label is the text inside `"…"`,
`[…]`, `{…}`, or after `:` on a transition line; `<br/>` is whitespace. Content
words are alphanumeric tokens longer than two characters that are not closed-class
English.

**Rationale**: three mechanisms were run over every record in this repository
that carries a `## Boundary` block. SC-004 allows no more than two findings a
reader judges wrong.

| Mechanism | Unit compared | Findings over 4 records |
|---|---|---|
| Whole label, exact match against `Owns truth` + `Decision` | phrase | **43** (every label) |
| Every word of the drawing, stemmed, against the whole record | word | **18** |
| Node label reported when *no* content word appears elsewhere | phrase | **1** |

The first two are not close to the gate and neither is repairable by a better
stopword list. They fail for the reason the level-3 record wrote down as an
assumption: authors draw in phrases — `"start · status · resume reads git + spec
artifacts on every call"` — and prose does not repeat a phrase. Matching whole
phrases reports every label; matching every word reports every inflection, and
tightening that needs English morphology, which is the dependency
`109-traceability-is-label-agreement` rejects by name.

The third fires only when the drawing introduces a concept the record never
writes about, which is the finding FR-008 describes. Its one hit is
`'we are at plan now'` in `session-state-is-re-derived` — a quoted example of
remembered state, the one label in the corpus whose words appear nowhere else.
Whether that finding is right is a judgment; either way it is one, and the gate
is two.

**Known limit, stated rather than implied**: the check reads labels in bracketed
or quoted form. An ASCII box drawing yields none, so such a record passes with
the check having compared nothing. All four `## Boundary` blocks on disk today
are mermaid; the limit binds the first record that draws in ASCII, and the
report says "no labels read" rather than "agreed".

---

## R-005 — Which records the label check reads

**Decision**: `proposed` only.

**Rationale**: FR-006 excludes `accepted`, and the three remaining statuses
exclude themselves on the check's purpose. `superseded` and `retired` records
were accepted once, so their bodies are frozen by the same rule
(`architecture-decisions`: "exactly two things ever change"). `rejected` records
are never accepted, so a finding against one names work nobody will do.

`proposed` is also the set the level-3 record's own Verification names — "every
`proposed` record with a `## Boundary` block passes the check" — so this is the
scope the calibration in R-004 was measured against.

---

## R-006 — SC-004's corpus is 4 records, not 22

**Finding**: 40 records sit under `docs/architecture/`. Four carry a
`## Boundary` section, all four in mermaid:

|  | `## Boundary` | none |
|---|---|---|
| accepted | 2 | 10 |
| proposed | 2 | 24 |
| rejected | 0 | 2 |

SC-004 says the label report is run "over the 22 records that already carry
drawings". Those 22 carry fenced blocks under `## Context` and `## Decision` —
`109-traceability-is-label-agreement` measured that and wrote it into its own
`Verified` section — and the Drawing entity scopes a drawing to `## Boundary`.
So the calibration corpus available to this feature is 4 records, and 2 of them
are `proposed`.

**Decision**: SC-004's threshold is kept and its denominator is corrected to the
records in range. The number that was measured against it is in R-004.

**Why this is not a reason to widen the check**: reading any fenced block
anywhere in a record as a drawing would make `Owns truth`'s prose examples and
`Considered`'s code samples into drawings, and the clarification session already
settled that content is never classified. A check that cannot tell a picture
from a code sample must be told where to look, and `## Boundary` is where.

---

## R-007 — Where a label finding surfaces

**Decision**: `_arch.validate` returns it as a `Finding` at `warning` level.
`doctor` already prints every finding `validate` returns and contributes only
`error` to its exit code (`wfctl/cli.py:5652`).

**Rationale**: the clarification session chose the findings path over the accept
output, and the code makes that free. `validate` takes the record set and
`Finding` already carries `level`, `slug` and `message`; the printer already maps
`warning` to `⚠` and already prints the records directory afterwards, which is
the one repair.

FR-008's "without refusing" and FR-011's "the projection is unchanged" are both
satisfied by placement alone: `validate` feeds `doctor`, `in_force` feeds
`arch context`, and they share no code.

**Alternatives considered**: print it from `arch accept` alongside the success
line — rejected in clarification. It would make a warning arrive only to whoever
accepts, which is the one moment the record is about to become unfixable.

---

## R-008 — Whether three kinds survive contact with the corpus

**Decision**: three kinds ship, and the assumption stays open rather than being
validated here.

**Rationale**: `design.md` lists "three kinds are enough" as an assumption whose
test is classifying the 22 existing drawings into `data-flow`, `component` and
`state`. R-006 is why that test cannot run: those drawings are not under
`## Boundary`, so they are not drawings under this feature's own definition, and
classifying them would validate the vocabulary against a corpus the vocabulary
does not govern.

The four in range classify cleanly — two data-flow, one state, one state — which
is evidence of nothing at n=4. The honest position is that `component` versus
`data-flow` is unvalidated, and the record that would change is
`the-author-declares-the-diagram-kind`, whose own Consequences already say a
fourth kind is a change to both the constant and the template.

---

## R-009 — Holding the kinds against the shipped template

**Decision**: `DIAGRAM_KINDS` is a module constant in `wfctl/_arch.py`. A test
asserts every value in it appears in the `record-template.md` the same wheel
ships, and that the template names no kind the constant lacks.

**Rationale**: `required-sections-are-wfctls` settles the shape, and
`_predicates.py:221` plus `tests/test_pipeline_sections.py` are the worked
example — constants beside the predicate that reads them, a test that loads the
template through `importlib.resources.files` so it reads the packaged copy
rather than the working tree's.

FR-010 is that test. Without it the template is guidance and the constant is the
rule, and the first divergence is a refusal naming three kinds the author's
template never mentioned.
