# Clarify scan for #648

## Session 2026-10-25

- Verdict: satisfied
- Scanned: spec.md
- Asked: 1 · Answered: 1 · Outstanding: 0 · Deferred: 1
- Detail: /Users/andremarin/Development/wfctl-specs/648-design-gate/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Resolved |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Clear |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Deferred |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Interaction & UX Flow** — the spec didn't say who may write the "no" claim
  when brainstorm runs with auto-approve on and nobody is watching.
  Q: May the agent run `wfctl step none brainstorm.software-design` itself? →
  A: Yes, and the PR review is the human sign-off, since the claim is a
  committed file with its reason and a person merges every PR.
  Basis: the user answered, and asked whether an existing human sign-off could
  cover it. The PR review is the one `wfctl arch none` already relies on.
  Decided against **Always a person**: it's stricter than the architecture pass,
  and it stops every autonomous run on a change with no structural choice.
  Decided against **Agent can't say no**: it forces an empty design record on
  those changes, which is what the claim exists to avoid.

### Deferred

- **Terminology & Consistency** — the spec calls the "no" answer a claim, which
  is the name on `main`. #635 renames claims to design exceptions. The spec
  follows whichever name is on `main` when this branch rebases, so the rename
  belongs to that rebase, not to this scan.
