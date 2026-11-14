# Clarify scan: #40

## Session 2026-10-15

- Verdict: satisfied
- Scanned: spec.md
- Asked: 3 · Answered: 3 · Outstanding: 0 · Deferred: 1
- Detail: /Users/andremarin/Development/wfctl-specs/40-save-uncommitted-on-remove/spec.md § Clarifications

The run was attended, and Andre answered all three questions. It spanned an
automatic session restart between the second and third question, so the second
was asked twice.

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Resolved |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Deferred |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Edge Cases & Failure Handling**: the spec did not say what removal does
  with a separate git repository inside the worktree, such as a project cloned
  there for reference. The worktree's own git reports it as one untracked
  folder.
  Q: What should removal do with it? → A: Copy it whole, history included, to
  `unsaved/` like any other untracked folder (FR-019a).
  Basis: Andre chose it. Local commits in the clone exist nowhere else, and
  copying the folder keeps them.
  Decided against **skip it with a warning**: the clone's local commits would
  be deleted with the worktree, which is the loss this feature exists to
  prevent.
  Decided against **stop the removal**: you would have to move the clone out
  by hand, even though a plain copy saves it just as well.
- **Interaction & UX Flow**: FR-023 said removal prints how many files it saved
  and where, with no list of names. A file you didn't expect to be saved would
  go unnoticed.
  Q: What should removal print about the files it saves? → A: The count, the
  `unsaved/` folder path, and the first 20 relative paths, then how many more
  there are (FR-023).
  Basis: Andre chose it "for now". The copy stays on his own machine and
  nothing is uploaded, so the risk the list guards against is small, and 20
  lines is enough to spot something like an un-ignored `.env`.
  Decided against **count and folder only**: an unexpected file shows up only
  if you open the folder, which nobody does after a clean removal.
  Decided against **every file**: a large untracked tree, such as a cloned
  repository, would flood the removal output.
- **Edge Cases & Failure Handling**: FR-019 said an untracked symlink is copied
  as a link, and `design.md` never decided that.
  Q: Should removal copy the link or what it points to? → A: Copy the link
  itself (FR-019).
  Basis: Andre agreed with the recommendation. The link's target is not deleted
  with the worktree, so the link is the only thing at risk.
  Decided against **follow the link**: a link to a large folder, or to one
  outside the worktree, would pull that folder into the state dir.
  Decided against **skip it with a warning**: the link is deleted with the
  worktree, and copying it costs nothing.

### Outstanding

None.

### Deferred

- **Integration & External Dependencies**: whether workmux 0.1.268 still runs
  `pre_remove` under `--force`, and whether the hook can see `--force` or
  `--keep-branch`. These are facts about workmux rather than gaps in the spec,
  which already states both as assumptions. The manual removal test in the
  Validation Strategy checks them, and Andre has to run it, because a session
  inside one worktree is refused when it removes another.
