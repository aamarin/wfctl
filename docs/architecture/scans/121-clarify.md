# Clarify scans — #121

## Session 2026-09-10

- Verdict: satisfied
- Scanned: `spec.md` for #326 (level3 downstream), all ten taxonomy categories
- Questions asked: 1 · Resolved: 1 · Deferred: 2 · Outstanding: 0
- Detail: `<FEATURE_DIR>/spec.md` § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Deferred |
| Domain & Data Model | Resolved |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Deferred |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Clear |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

Two rows read `Deferred` and the header counts two, which it did not when this
was first written: `Functional Scope & Behavior` said `Clear` while the Deferred
section below deferred a corner of that same category. A review panel found the
row and its own file disagreeing — which is the one thing a coverage table exists
to make impossible.

### Findings

- **Domain & Data Model, resolved** — the spec said a step takes "the paths
  listed under `## Software design decisions`" without saying what counts as a
  listing. The `/speckit.brainstorm` wrapper specifies bullet entries, and also
  requires that a level answered with no record says so in one line rather than
  deleting the section — so the section legitimately carries prose as well as
  entries. This feature's own `design.md` carries both, and its prose names a
  **level-2** record; a step taking every path in the section would load that
  record as a level-3 one.

  → Fixed: FR-002a. A path counts only as a list item `- <path> — <text>`; prose
  contributes none.

  → Decided against **filtering every path in the section to those under
  `<arch-root>/design/`**: it tolerates prose, and it silently drops a record in
  a repository that declares `arch_root` elsewhere — trading a visible parse rule
  for an invisible path assumption, which is the class of failure #121 exists to
  remove.

  → Decided against **tightening the section's format in the brainstorm
  wrapper** so prose paths are forbidden: cleanest rule of the three, and it
  edits a shipped item-5 wrapper for a consumer that does not exist yet. Out of
  #326's scope, and the bullet-only rule needs no change to any artifact already
  written.

### Deferred

- **Non-Functional Quality Attributes** — whether reading a feature's records
  exhausts the context available to `/speckit.implement`. No feature in this
  repository carries more than one record, so there is nothing here to measure.
  Recorded in the spec's Assumptions rather than asked as a question: a question
  whose answer would be a guess is not a clarification.
- **Functional Scope & Behavior, one corner** — what separates a task that
  *contradicts* a record from one that merely overlaps it. Inherent to pass G
  being a model pass rather than a mechanical check, and bounded rather than
  resolved: FR-008 requires a finding to name the record and quote the task, so a
  false positive is disputable by a reader. Argued in
  `docs/architecture/design/326-contradiction-is-a-seventh-pass.md`, which
  records it as the assumption the whole approach rests on.
