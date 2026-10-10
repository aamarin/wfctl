# Clarify scan: #264

## Session 2026-10-09

- Verdict: satisfied
- Scanned: spec.md
- Asked: 2 · Answered: 2 · Outstanding: 0 · Deferred: 1
- Detail: /Users/andremarin/Development/wfctl-specs/264-sentinel-goes-stale/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Resolved |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Deferred |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Domain & Data Model**: the spec matched tasks by description but left
  open whether spec-kit's `[P]` and `[USn]` tags are part of it.
  Q: Do the `[P]` and `[USn]` tags count as part of a task's description? →
  A: No. The checkbox, the ID, and both tags are removed, and whitespace is
  collapsed, before descriptions are compared.
  Basis: Andre chose this option in the session. A re-run of `/speckit.tasks`
  rewrites the whole file, so a story added to the spec renumbers `[USn]` and
  a plan change can add or drop `[P]`, the same way it renumbers task IDs.
  Decided against **Keep the tags**: a re-run that only moves a tag would
  reopen the step with no new work behind it, and the argument that set IDs
  aside applies to the tags unchanged.
- **Edge Cases & Failure Handling**: nothing stopped `wfctl step complete
  implement` from running before implementation started. A record written
  then saves every task as incomplete, so no task ever counts as new work, and
  with no definition of done the story reads complete with nothing built.
  Q: Should the command refuse unless `implement` is the current step? →
  A: It refuses while a step before `implement` is current, and runs when
  `implement` is current or already finished.
  Basis: Andre chose "refuse unless current". The rule was then widened to
  accept a pipeline already past `implement`, because the implement
  instructions run the command on every finish. With every box ticked and no
  definition of done, the pipeline has already moved past `implement` by
  then, and "only when current" would refuse a normal finish. Andre was told
  of the change in the session.
  Decided against **No position check**: an early run would reach the same
  false "complete" this issue fixes, by a different route.

### Deferred

- **Integration & External Dependencies**: a sub-issue branch claimed by an
  epic reads the epic's `tasks.md` and its single completion record, so two
  sub-issues finishing in turn write the same record. That is how the record
  behaves today, and this feature does not change it. The plan should confirm
  the epic case reads the same before and after, and nothing more.
