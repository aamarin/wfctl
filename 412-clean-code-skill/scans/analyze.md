# Analyze scans — #412

## Session 2026-09-17

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 5 · Critical: 0 · Acted on: 5 · Accepted: 0
- Detail: /Users/andremarin/Development/wfctl-specs/412-clean-code-skill/checklists/analysis-report.md

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Resolved |
| C · Underspecification | Resolved |
| D · Constitution alignment | Clear |
| E · Coverage gaps | Resolved |
| F · Inconsistency | Resolved |
| G · Design-record contradiction | Clear (2 records read) |
| Requirement-to-task coverage | 100% |

### Findings

- **E · Coverage gaps, HIGH** — FR-012 forbids reproducing or translating a
  sample program from any source, and no task verified it. It is one of the two
  provenance claims this change makes and it was the only requirement with zero
  coverage; the other, FR-011, had T032.
  → Fixed: added T033 to Phase 7, beside T032 — read every reference's code
  blocks against the draft's, where a block that appeared during the split is
  what to find. Decided against adding a check per reference in Phase 2: the
  question is one judgment over eleven files, and eleven copies of it would each
  be answered without the others in view.

- **B · Ambiguity, MEDIUM** — SC-005 read *"Measured by reading the shipped text
  for outcome vocabulary"* and named no vocabulary. A measurement that names no
  terms cannot fail, so the criterion was decorative.
  → Fixed: SC-005 now lists eight terms — *pass*, *fail*, *waiver*, *verdict*,
  *blocker*, *approved*, *rejected*, *outcome class* — and T020 carries the
  search beside the `method` search it already had. Decided against a test: the
  judgment is whether a hit is ordinary prose or a value the skill emits, and a
  grep that fails on the word "pass" appearing in a sentence would be worse than
  the ambiguity it replaced.

- **E · Coverage gaps, MEDIUM** — SC-004 is measured against a named baseline —
  the draft's single entry naming seven subjects — and no task recorded the
  measurement, so the criterion had a method and no occasion.
  → Fixed: folded into T034, the routing exercise, which already walks one real
  unit of work from task to reference. Decided against a task of its own: the
  count is a by-product of the exercise, and a separate task would either repeat
  the exercise or report a number nobody derived.

- **C · Underspecification, MEDIUM** — four verify commands in tasks.md (T005,
  T014, T015, T016) wrote `references/<file>.md`, which resolves from no
  directory the reader would be standing in. A verify command that errors on
  paste teaches the reader that the verify commands are decorative, which is the
  one habit this template's verification rule exists to prevent.
  → Fixed: `SKILL` and `REF` bound once under Path Conventions, and the four
  commands rewritten against them. Decided against spelling the full path into
  each: `wfctl/agents/skills/clean-code/references/` is 43 characters and
  wrapping it inside a checklist line is what made the abbreviation attractive
  in the first place.

- **F · Inconsistency, LOW** — the parallel execution example labelled its first
  wave "8 in parallel" and listed ten tasks.
  → Fixed: corrected to 10. No alternative to decide against.

### Filing

Nothing filed. All five findings met both in-scope conditions — each is confined
to `spec.md` and `tasks.md`, and each makes one artifact say what the others
already said rather than deciding anything new. E1 and E2 are the coverage-gap
case the policy settles explicitly: `spec.md` set the scope when it stated
FR-012 and SC-004, and `tasks.md` failing to cover them was the defect rather
than the boundary.

Pass G found nothing, so the `proposed`-record exception did not arise. Had it,
the finding would have been filed rather than applied: only a human moves a
record past `proposed`, and an unattended run that rewrote `tasks.md` to conform
would have ratified the record by acting on it.
