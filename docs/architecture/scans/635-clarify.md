# Clarify scans for #635

## Session 2026-10-25

- Verdict: satisfied
- Scanned: spec.md
- Asked: 1 · Answered: 1 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/635-arch-folder-per-branch-notes/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
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

- **Functional Scope & Behavior** — when a session ends, `wfctl end` writes a
  "Boundary: answered/unanswered" line into the session summary. The
  `_observe` function in `cli.py` produces it, and it only counts files under
  the architecture folder. After this change, a branch that runs `arch none`
  would read "unanswered" in the summary while the pipeline reads it answered.
  Q: Should the summary count the spec folder's boundary exception too?
  → A: Yes. The summary uses the same rule as the brainstorm gate (FR-014).
  Basis: Andre chose A.
  Decided against **keep counting architecture records only**: the summary and
  `wfctl status` would disagree about the same branch, and the next session
  reads both.
  Decided against **drop the Boundary line**: it's the only place the handoff
  says whether the boundary question was answered, and the fix is one more
  check in a function this change already touches.
- One candidate was dropped without asking: whether the brainstorm gate should
  explain why it ignores an old-style declaration file. No unmerged branch adds
  one, checked across every local and `origin` branch, so the case doesn't
  come up. Every other category was read and found Clear.
