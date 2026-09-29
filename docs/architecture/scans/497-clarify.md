# Clarify scans — #497

## Session 2026-09-27

- Verdict: satisfied
- Scanned: spec.md
- Asked: 4 · Answered: 4 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/497-start-refuses-untracked-branch/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Resolved |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Resolved |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Functional Scope & Behavior** — the spec said the issue question is asked
  only where a tracker is configured, and that a worktree with no install is
  refused. A worktree with no install has no tracker config of its own, so both
  rules matched it, and whichever ran first decided; checked tracker-first, the
  install refusal could never fire.
  Q: In a worktree with no wfctl install, which check comes first? → A: The
  install. The tracker question is asked only after it, from this worktree's
  own config.
  Basis: Andre accepted the recommendation. design.md gives the install refusal
  the reason that this worktree's tracker config is absent, which is only true
  if the install is settled first.
  Decided against **tracker first, read from the main checkout**: it answers the
  tracker question from a checkout other than the one being started, and still
  needs the install refusal after it to cover the missing skills.
  Decided against **tracker first, drop the install refusal**: it leaves a
  worktree made by bare `git worktree add` ungated, which is the route the
  refusal exists for.

- **Edge Cases & Failure Handling** — the spec refused a detached HEAD "as
  naming no issue", but wfctl substitutes the short commit hash for a missing
  branch name, and the key is parsed from that hash.
  Q: How is a worktree on a detached HEAD handled? → A: Ask git directly whether
  HEAD is detached, and refuse with its own remedy; switch to the worktree's
  branch.
  Basis: Andre accepted after asking for it to be verified first. The test
  corrected the question's premise: a hash with a leading digit and a letter
  (`60761f0`) reads as no issue, because the key must be followed by `-`, `_`,
  or the end, while an all-digit hash (`5611469`) reads as issue 5611469, which
  is about 1 in 27 hashes. The state directory is already keyed on the hash
  (`…/wfctl/60761f0`).
  Decided against **parse the substituted name**: most hashes would get the
  `git branch -m` remedy, which fails on a detached HEAD, and an all-digit hash
  would be checked against the tracker as an issue.
  Decided against **exempt a detached HEAD**: it contradicts the rule that every
  worktree works against an issue, and a detached session already loses its
  branch's state directory.

- **Integration & External Dependencies** — in a bare-repository layout there is
  no main checkout, and `main_checkout()` returns None for its worktrees, tested
  on a bare clone of this repository. The install check compares against the
  main checkout, so it could never fire there.
  Q: In a bare layout, what happens to a worktree with no install? → A: It is
  refused; a missing install in a linked worktree is enough when there is no
  main checkout to compare against.
  Basis: Andre chose it, after asking what a bare layout is.
  Decided against **accept the gap and document it**: Andre chose closing the
  gap over leaving bare-layout worktrees ungated, although `main_checkout`'s
  docstring had declined a bare-layout fallback for spec-root resolution.
  Decided against **infer from sibling worktrees**: Andre chose the outright
  refusal over it; it was not discussed further.

- **Functional Scope & Behavior** — the exemption was written as "the main
  checkout proceeds", and a bare layout has no main checkout, so its `main`
  worktree would be refused as naming no issue. This surfaced from Andre's
  question whether `main` is usually its own worktree in an orchestrated setup;
  it is not in this repository, where `main` is the main checkout.
  Q: How does trunk keep its exemption, and how is trunk found? → A: A linked
  worktree on trunk proceeds, in any layout. Trunk is read from `origin/HEAD`,
  then the bare repository's own `HEAD`, then the first of `main`, `master`, and
  `dev`. A trunk key declared in `wfctl.json` is a separate issue.
  Basis: Andre accepted the recommendation, after asking whether trunk is
  configurable per repository (a repository he named works under `dev`). It is
  discovered, not configured, and it was tested against a source whose default
  was `dev` and which also had `main`. A bare clone records no `origin/HEAD`, so
  today's detection returned `main`; the bare `HEAD` returned `dev`. The bare
  `HEAD` did not follow a later change of the source's default. From inside the
  worktree, `git rev-parse --is-bare-repository` reports `false` and
  `git config --bool core.bare` reports `true`.
  Decided against **declare a trunk key on this branch**: it changes both
  existing callers of trunk detection, which is its own change, and the
  discovered source covers the layout the exemption is for.
  Decided against **keep today's detection**: it returns `main` for a bare layout
  that has both branches, and refuses the `dev` worktree it was meant to exempt.
  The question was first put without the detection half, offering the exemption
  in any layout, in a bare layout only, or not at all. The answer takes the
  first; a bare-only exemption lost because in a normal layout git will not
  check trunk out in a second worktree, so the wider rule costs nothing, and no
  exemption lost because it breaks orchestration from trunk, which Andre
  confirmed at brainstorm must keep working.

One consequence was written without a question, since it follows from the
answers: the exemptions are settled before the install check (FR-001a).
Otherwise a bare layout's trunk worktree with no install is refused, which undoes
the fourth answer.

### Outstanding

None.

### Deferred

None. The declared trunk key is out of scope by the fourth answer, not a
deferred question.
