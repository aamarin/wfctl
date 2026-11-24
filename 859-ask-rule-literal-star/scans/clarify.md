## Session 2026-11-23

- Verdict: satisfied
- Scanned: spec.md
- Asked: 0 · Answered: 0 · Outstanding: 0 · Deferred: 1
- Detail: /Users/andremarin/Development/wfctl-specs/859-ask-rule-literal-star/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Deferred |
| Edge Cases & Failure Handling | Clear |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- No question met the bar; every category above was read. The decisions a question would have asked were settled with the user in the design session on 2026-11-22 and 2026-11-23 and are recorded in `settings-edit-asks-first.md` (accepted) and `design/settings-changes-ask-once.md`:
  - `--yes` doesn't answer the settings question (FR-002), since the worktree hook and `/start-session` pass it unattended.
  - One question per file, all or nothing (FR-003), rather than one per change.
  - A missing file is created without asking (FR-006), so a new worktree gets the guard's hook.
  - Doctor warns rather than failing (FR-011), since `/start-session` can't apply the change.
  - The unattended warning gives a count, and the question lists each change with its existing cost line (FR-004, FR-008).
  - The agent applying changes after a prompt is out of scope, in #860.
- Security & privacy was read against the threat model in `settings-edit-asks-first.md`. SC-001 and SC-002 map one test to each of its 6 "Must keep catching" and 4 "Must let through" items.

### Outstanding

- None.

### Deferred

- **Integration & External Dependencies** — whether Claude Code's `!` prefix gives install a terminal on desktop. It doesn't change any requirement, since the design holds either way, and it's checked by hand during implementation (spec Assumptions).
