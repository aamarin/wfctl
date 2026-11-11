# Clarify scan: #598

## Session 2026-11-11

- Verdict: satisfied
- Scanned: spec.md
- Asked: 2 · Answered: 2 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/598-scans-in-spec-folder/spec.md § Clarifications

Written to the spec folder rather than `docs/architecture/scans/`, since this
branch is the change that moves it.

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Resolved |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Domain & Data Model**: the spec didn't say which part of the scan file the
  check reads.
  Q: Whole file or last section? → A: The whole file.
  Basis: a plan review scan ends with a `## Sign-off` section, which has no
  `Verdict` line or coverage table (`_plan_review.append_sign_off`).
  Decided against the last-section check: it would hold every signed-off plan.
- **Edge Cases & Failure Handling**: the spec claimed a sign-off section carries
  its own verdict line. It doesn't.
  Q: Does a file holding only sign-off sections pass? → A: No.
  Basis: the sign-off refuses without a review report, so a review ran and had
  to write a section first.
  Decided against letting the sign-off event skip the scan check: it would hide
  a review that skipped its scan.
