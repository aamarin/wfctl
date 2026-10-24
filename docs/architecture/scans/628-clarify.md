# Clarify scans for #628

## Session 2026-10-22

- Verdict: satisfied
- Scanned: spec.md
- Asked: 2 · Answered: 2 · Outstanding: 0 · Deferred: 1
- Detail: /Users/andremarin/Development/wfctl-specs/628-design-passes-every-change/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Deferred |
| Edge Cases & Failure Handling | Clear |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Resolved |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Functional Scope & Behavior** — the first draft said `design-passes` runs
  on every change, while the design-passes record says the handoff still picks
  the route and only the route that bypasses Spec Kit points to the skill. The
  two readings differ on whether a branch routed to Spec Kit from the start
  carries a `Needs-spec:` trailer.
  Q: Which changes run `design-passes`? → A: Only changes a handoff doesn't
  send to Spec Kit. A branch routed to Spec Kit skips the skill, carries no
  trailer, and answers "Yes" in its PR section (User Story 1, Edge Cases, Key
  Entities).
  Basis: Andre chose A, after confirming that the pipeline already runs the
  passes: brainstorm runs levels 2 and 3, and `/speckit.implement` runs test
  tasks first and `clean-code` after the last task.
  Decided against **every handoff points to `design-passes`**: on a Spec Kit
  branch the skill would repeat the passes brainstorm already runs, and make
  the branch answer a spec question the handoff session already answered.
  Decided against **brainstorm writes a `Needs-spec: yes` trailer**: it adds a
  step to the Spec Kit route for an answer the PR section already carries.
- **Terminology & Consistency** — `design.md` left the name of the `wfctl.json`
  key for required PR sections open, and the first draft used `pr_sections` as
  a placeholder.
  Q: What's the key called? → A: `change_sections` (FR-006, User Story 2).
  Basis: Andre chose B.
  Decided against **`pr_sections`**: it assumes GitHub, while wfctl calls a PR,
  a merge request, or a patchset a "change" across every backend.
  Decided against **`required_sections`**: it says the sections are required
  but not what they're sections of.

### Deferred

- **Integration & External Dependencies** — how `wfctl check config` finds a
  repo's PR template, and what it reports for a backend with no template file.
  The spec requires a finding when a listed section is missing from the
  template, and where the template lives is a plan question.
