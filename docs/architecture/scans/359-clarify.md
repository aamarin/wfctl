# Clarify scan: #359

## Session 2026-10-14

- Verdict: satisfied
- Scanned: spec.md
- Asked: 2 · Answered: 2 · Outstanding: 0 · Deferred: 1
- Detail: /Users/andremarin/Development/wfctl-specs/359-push-specs-to-trunk/spec.md § Clarifications

Andre answered both questions. The first was asked before an automatic session
restart and asked again after it, and nothing was written to the spec in
between.

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Deferred |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Functional Scope & Behavior**: FR-023 had `wfctl check specs` exit 1 for
  any unstored spec dir. Every branch still in the pipeline has one, because
  the store runs only after `implement`, so the command would exit 1 on nearly
  every run and the exit code would stop meaning anything.
  Q: How does `check specs` treat a spec dir whose branch still has a
  worktree? → A: It lists those dirs under a separate "In progress" heading
  that doesn't count toward exit 1.
  Basis: Andre chose B after seeing both outputs rendered. Exit 1 then means a
  spec dir was left behind, and the active ones stay visible.
  Decided against **A, list every unstored dir and exit 1 for any of them**:
  the command would fail whenever any worktree is mid-pipeline, so a person
  would learn to ignore it, which is the same failure the "durable" message
  caused.
  Decided against **C, leave branches with a worktree out entirely**: it hides
  the work in flight, and a branch that has been stuck for weeks with an
  unstored spec dir would never show up.
- **Edge Cases & Failure Handling**: every branch commits into the same spec
  store, and the spec did not say what happens when two stores run at once,
  such as two removals or two unattended runs finishing together. The second
  would hit git's lock and fail.
  Q: What does a store do when another store is already running? → A: It
  waits up to 10 seconds for the other to finish, then fails with a message
  saying another store is running.
  Basis: Andre chose A. A store takes a second or two, so a short wait clears
  almost every collision without anyone seeing it.
  Decided against **B, fail right away with the same message**: the collision
  is almost always over within a second or two, so failing makes a person
  rerun a command that would have succeeded on its own. At removal nobody is
  watching to rerun it.

### Outstanding

None.

### Deferred

- **Integration & External Dependencies**: the exit code `wfctl store specs`
  returns when it committed but could not push. Removal already treats that
  case as a warning (FR-021), and the pass reads `in_progress` either way
  because it asks git rather than the exit code (FR-018). So the exit code only
  changes what the `/store-specs` wrapper and the removal hook check, which is
  mechanism and belongs to the plan.
