# Clarify scan for #698

## Session 2026-11-03

- Verdict: satisfied
- Scanned: spec.md
- Asked: 3 · Answered: 3 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/698-drop-unloaded-skills/spec.md § Clarifications

The session ran unattended, so each answer is the recommendation step 4
computed, with the basis it was derived from.

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Resolved |
| Edge Cases & Failure Handling | Clear |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Resolved |
| Misc / Placeholders | Clear |

### Findings

- **Functional Scope & Behavior**: the spec said an existing project loses a
  dropped skill, but not whether a bare install does it.
  Q: Should a bare `install-skills` remove a dropped skill without `--prune`? → A: No, the existing orphan rule stands.
  Basis: the manifest records paths and backups but no content, so a bare removal would delete a copy the project edited (`install-modes`, the orphan comment in `cli.py`), and `/start-session` already runs `--prune --yes`.
  Decided against **Remove on every bare install**: it deletes a hand-edited copy with no backup to restore.
  Decided against **Remove only when the content is unchanged**: the manifest stores no per-file hash, so this needs a new manifest field and a migration, which is more than the issue asks for.
- **Integration & External Dependencies**: agents that read `.agents/commands/` also got the `brainstorm` wrapper.
  Q: Should the `brainstorm` command wrapper keep shipping for those agents? → A: No, it is dropped with its skill.
  Basis: `/speckit.brainstorm` ships to the same directory and leads to the same step, and nothing in `wfctl/` or this repo's `wfctl.json` names `/brainstorm`.
  Decided against **Keep the wrapper and point it at speckit-brainstorm**: it keeps a second name for the step in every non-Claude install, which is the duplication scope item 2 removes.
- **Completion Signals**: SC-001 could be read against the issue's 38.8k or against `main` today.
  Q: What is SC-001 measured against? → A: A clone of `main` measured the same day with the same command, 39,789 tokens on 2026-11-03.
  Basis: the harness grew about 1k since the issue's measurement, so the absolute number would measure changes this branch didn't make.
  Decided against **The issue's 38.8k**: a miss there would say nothing about this branch.

### Outstanding

None.

### Deferred

None.
